# Claude Code 入門 — 給工程師同仁

一套以網頁呈現的 Claude Code 教學,從第一次在終端機跟 Claude 對話,到讓它讀懂你的 codebase、遵守團隊規範、自動跑流程,把 Claude Code 變成日常開發的一部分。

每一章聚焦一個概念,搭配一個可以馬上動手的小練習。內容對照 [Claude Code 官方文件](https://code.claude.com/docs) 撰寫。

## 怎麼看

純靜態網頁,不需要編譯或安裝套件。兩種方式:

- **直接開**:用瀏覽器打開 `index.html`
- **起本機伺服器**(避免某些瀏覽器對 `file://` 的限制):

  ```bash
  python3 -m http.server 8000
  # 然後開 http://localhost:8000
  ```

## 章節

| # | 章節 | 一句話 |
|---|------|--------|
| 1 | Claude Code 是什麼 | 跑在終端機的 agentic coding 工具,跟純聊天 AI、Copilot 補完的差別 |
| 2 | 安裝設定 | 一行指令裝好、cd 進專案、瀏覽器登入,認識提示列與權限模式 |
| 3 | CLAUDE.md | 給 Claude 的專案常駐指示,每次 session 自動載入 |
| 4 | Hook | 綁在生命週期事件點、到點「一定會跑」的硬性機制 |
| 5 | Skill | 按需載入的「能力包」,平常只有 description 在場 |
| 6 | Slash commands | 打 `/` 主動叫用,內建指令 vs skill,參數 `$ARGUMENTS` |
| 7 | MCP servers | 接上外部工具的開放標準(AI 界的 USB-C) |
| 8 | Subagent | 委派出去的專門角色,在獨立 context 完成後只回報結果 |
| 9 | 權限模式 | 「問你」與「放手」之間的旋鈕,加上 `/permissions` 規則 |

## 專案結構

```
.
├── index.html              # 首頁(章節總覽)
├── 01-claude-code-是什麼.html
├── ...                     # 02 ~ 09 各章
├── 09-permission-modes.html
├── styles.css              # 共用樣式
├── script.js               # 共用腳本
├── img/                    # 各章 demo 截圖
└── .claude/                # 本專案的 Claude Code 設定
    ├── settings.json       #   共享設定(PreToolUse 守門 hook)
    └── hooks/
        └── guard-dangerous-commands.py  # 攔截高風險 Bash 指令的守門腳本
```

> `.claude/settings.local.json`(個人本地設定)與 `practice_data/`(真實練習資料)已列入 `.gitignore`,不會上傳。

## 維護

- 維護者:chris
- 新增章節時,記得同步更新三處:各頁側邊欄連結、上一章的「下一章」導覽、`index.html` 的章節卡片與章數。
- 內容以官方文件為準;改動涉及功能行為時,請先對照 https://code.claude.com/docs 再下筆。
