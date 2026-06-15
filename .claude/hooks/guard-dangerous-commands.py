#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guard-dangerous-commands.py
===========================
Claude Code 的 PreToolUse 守門 Hook —— 防止 AI 或使用者誤執行高風險指令。

運作方式
--------
Claude Code 在「執行 Bash 工具之前」(PreToolUse 事件) 會把事件 JSON 從 stdin
餵給本腳本。腳本判斷指令的風險等級,並用 stdout 輸出 JSON 決定:

  permissionDecision = "deny"  -> 硬性拒絕,不執行,附上清楚原因 (不可被自動重試繞過)
  permissionDecision = "ask"   -> escalate 給使用者,跳出權限對話框要求確認
  (無輸出 / exit 0)             -> 不干涉,交回正常權限流程

為什麼用 deny / ask 而不是「非 0 exit code」
--------------------------------------------
官方契約:exit 0 + JSON 的 permissionDecision 才是「帶原因的結構化決定」。
若改用 exit 2,Claude Code 會忽略這裡的 JSON、只把 stderr 當錯誤訊息丟回給模型,
反而比較像「可重試的錯誤」。要「不可繞過的硬擋」,deny 才是正解。
PreToolUse hook 是「非互動」的 (stdin 是事件 JSON,不是鍵盤),無法在腳本裡讀
使用者輸入的 "CONFIRM";Claude Code 內建的確認機制就是 "ask" —— 它會跳出
approve / reject 對話框,本腳本把「受影響資源 + 後果」寫進對話框訊息。

設計原則
--------
- 寧可誤擋,不可漏放 (對破壞性指令保守)。
- 用正規表達式吸收常見變形:旗標順序 (-rf / -fr)、合併旗標、多餘空白、大小寫、
  以及用 ; && || | 換行串接的多段指令 (逐段分析,避免跨指令誤判)。
- 規則集中在 DENY_RULES / ASK_RULES,日後新增危險指令只要加一條。
- 只依賴 Python 3 標準庫,相容 macOS / Linux。

限制 (務必理解)
--------------
這是「防誤觸」護欄,不是對抗惡意攻擊者的沙箱。高度混淆 (eval、base64、變數展開、
從檔案讀指令) 仍可能繞過。請搭配最小權限與權限模式一起使用。
"""

import json
import re
import sys


# ---------------------------------------------------------------------------
# 文字正規化與指令切分
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """把連續空白 (含 tab / 換行) 壓成單一空白,讓 'rm   -rf' 之類也能命中。"""
    return re.sub(r"\s+", " ", text).strip()


def split_commands(command: str) -> list:
    """
    以常見的指令分隔符 ( && || ; | 換行 ) 切成多段子指令,逐段獨立分析。
    這樣 'ls | grep x' 不會讓 grep 的旗標被算到別的指令上,降低誤判。
    """
    parts = re.split(r"(?:&&|\|\||[;|]|\n)", command)
    return [normalize(p) for p in parts if normalize(p)]


def _has(text: str, pattern: str, flags: int = 0) -> bool:
    """正規表達式是否命中。包成函式只為了讓規則表更好讀。"""
    return re.search(pattern, text, flags) is not None


# ---------------------------------------------------------------------------
# 可重用的比對片段
# ---------------------------------------------------------------------------

# rm 的「遞迴」旗標:-r / -R / -rf / -fr / --recursive (合併旗標也吃得到)
RE_RECURSE = r"(?:(?:^|\s)-{1,2}[a-zA-Z]*[rR][a-zA-Z]*\b|--recursive\b)"

# 災難級刪除目標:根目錄、家目錄、純萬用字元 (前後可為空白或引號,吸收 "rm -rf /" 變形)
RE_CATASTROPHIC = (
    r"(?:^|\s|[\"'])"
    r"(?:/|/\*|~|~/|~/\*|\*|\$HOME|\$\{HOME\})"
    r"(?:\s|$|[\"'])"
)


def is_rm_recursive(c: str) -> bool:
    """這段子指令是否為『遞迴刪除』(rm 且帶遞迴旗標)。"""
    return _has(c, r"\brm\b") and _has(c, RE_RECURSE)


# ---------------------------------------------------------------------------
# 規則表 —— 要新增危險指令,往這兩張表加 (test, 說明) 即可
#   test:  一個 (子指令字串) -> bool 的函式;True 代表命中
#   說明:  給使用者看的原因 / 後果
# ---------------------------------------------------------------------------

# (1) 強制阻擋:直接拒絕,不給執行
DENY_RULES = [
    (
        lambda c: _has(c, r"\bsudo\b(?:\s+-{1,2}\S+)*\s+rm\b"),
        "偵測到 `sudo rm`:以 root 權限刪檔極度危險,已阻擋。",
    ),
    (
        lambda c: _has(c, r"\bgit\s+push\b")
        and _has(c, r"(?:--force\b|--force-with-lease\b|(?:^|\s)-f(?:\s|$))"),
        "偵測到 `git push --force / -f / --force-with-lease`:會覆寫遠端歷史、"
        "可能毀掉他人的提交,已阻擋。請改用一般 push 或先與團隊確認。",
    ),
    (
        lambda c: _has(c, r"\bgit\s+push\b")
        and _has(c, r"(?:--delete\b|(?:^|\s)-d\b|\s:[^\s]+)"),
        "偵測到刪除遠端分支 (`git push --delete` 或 `git push origin :branch`),已阻擋。",
    ),
    (
        lambda c: is_rm_recursive(c) and _has(c, RE_CATASTROPHIC),
        "偵測到對『根目錄 / 家目錄 / 萬用字元』的遞迴刪除 "
        "(如 `rm -rf /`、`rm -rf ~`、`rm -rf *`),已阻擋。這會造成不可逆的大規模刪除。",
    ),
]

# (2) 執行前確認:escalate 給使用者 (ask),核准後才執行
ASK_RULES = [
    (
        # 注意:災難級的遞迴刪除已在 DENY 先攔下,這裡只會剩一般路徑
        lambda c: is_rm_recursive(c),
        "遞迴刪除目錄 (`rm -r` / `rm -rf <path>`):會刪掉該路徑下所有檔案,且無法復原。",
    ),
    (
        lambda c: _has(c, r"\bfind\b") and _has(c, r"(?:^|\s)-delete\b"),
        "`find ... -delete`:會刪除所有符合條件的檔案,範圍可能比預期大。",
    ),
    (
        lambda c: _has(c, r"\bgit\s+reset\b") and _has(c, r"(?:^|\s)--hard\b"),
        "`git reset --hard`:會丟棄所有未提交的變更 (working tree + index)。",
    ),
    (
        lambda c: _has(c, r"\bgit\s+clean\b") and _has(c, r"(?:^|\s)-[a-zA-Z]*f[a-zA-Z]*\b"),
        "`git clean -f...`:會刪除未追蹤的檔案;加上 x 連 .gitignore 忽略的也一起刪。",
    ),
    (
        lambda c: _has(c, r"\bdocker\s+(?:system|volume|image|container|network|builder)\s+prune\b"),
        "`docker ... prune`:會刪除未使用的資源;特別是 `volume prune` 可能刪掉含資料的 volume。",
    ),
    (
        lambda c: _has(c, r"\bDROP\s+DATABASE\b", re.IGNORECASE),
        "`DROP DATABASE`:會永久刪除整個資料庫。",
    ),
    (
        lambda c: _has(c, r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE),
        "`TRUNCATE TABLE`:會清空整張資料表,且通常無法 rollback。",
    ),
]


# ---------------------------------------------------------------------------
# 決策引擎
# ---------------------------------------------------------------------------

def evaluate(subcmds: list):
    """
    對每段子指令套用規則。DENY 優先於 ASK。
    回傳 (decision, reason, matched_subcommand);沒命中則 (None, None, None)。
    """
    for c in subcmds:
        for test, reason in DENY_RULES:
            if test(c):
                return "deny", reason, c
    for c in subcmds:
        for test, reason in ASK_RULES:
            if test(c):
                return "ask", reason, c
    return None, None, None


def emit(decision: str, reason: str) -> None:
    """輸出 PreToolUse 的決定 JSON 到 stdout。"""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output, ensure_ascii=False))


def main() -> None:
    # 解析 hook 輸入。解析失敗時「不阻擋」正常流程 (failing open),但記到 stderr 供除錯。
    try:
        data = json.load(sys.stdin)
    except Exception as exc:  # noqa: BLE001 - 任何解析錯誤都不該讓整個流程崩潰
        print(f"[guard] 無法解析 hook 輸入: {exc}", file=sys.stderr)
        sys.exit(0)

    # 只管 Bash 工具 (matcher 已限定 Bash,這裡再保險一次)
    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = (data.get("tool_input") or {}).get("command") or ""
    if not command.strip():
        sys.exit(0)

    decision, reason, matched = evaluate(split_commands(command))

    if decision == "deny":
        emit("deny", f"🚫 已阻擋高風險指令。\n指令:{matched}\n原因:{reason}")
        sys.exit(0)

    if decision == "ask":
        emit(
            "ask",
            "⚠️ 偵測到高風險指令,需要你確認。\n"
            f"指令:{matched}\n"
            f"可能後果:{reason}\n"
            "確定要執行請於對話框「核准 (approve)」,否則請「拒絕 (reject)」。",
        )
        sys.exit(0)

    # 沒命中任何規則:不輸出 JSON,交回正常權限流程
    sys.exit(0)


if __name__ == "__main__":
    main()
