# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 這是什麼

一套「Claude Code 入門」教學**靜態網站**,給工程師同仁看。純 HTML + 一份共用 CSS + 一份共用 JS,**沒有 build / test / lint / 套件**。內容用台灣繁體中文,技術名詞保留原文。

## 怎麼看

直接用瀏覽器開 `index.html`,或起本機伺服器(避免 `file://` 對 clipboard API 的限制):

```bash
python3 -m http.server 8000   # 開 http://localhost:8000
```

## 結構

- `index.html` — 首頁,含章節總覽卡片
- `NN-名稱.html` — 各章(01~09),每章一個檔
- `styles.css` — 全站共用樣式
- `script.js` — 全站共用腳本
- `img/` — 各章 demo 截圖
- `.claude/` — 本專案的 Claude Code 設定(`settings.json` 的 PreToolUse hook → `hooks/guard-dangerous-commands.py`,攔高風險 Bash 指令)

## ⚠️ 新增 / 改章節時:四處必須同步

這是本專案最容易出錯的地方。每章是獨立 HTML 檔、靠**手動維護的連結**串起來,新增或調整章節順序時,以下四處要一起改,否則導覽會斷:

1. **每一頁的側邊欄** `<aside class="sidebar">` 章節連結清單 — 是**全部頁面**都有一份(含 index 與各章),不是只改一頁
2. 當前頁側邊欄連結要標 `class="sidebar-link active"`,其餘是 `class="sidebar-link"`
3. **上一章的 `.page-nav`「下一章」** 連結(原本指向 `#`、灰底 `規劃中` 的要改成實際連結)
4. **`index.html`** 的章節卡片(`.lesson-card`)與標題的章數(`<span class="duration">N 章 · 持續增加中</span>`)

## 每章的版型骨架

各章 HTML 沿用同一套結構,新增章節時照抄既有章節最快:

- `<h1>` 含 `<span class="chapter-label">Chapter N</span>` + 標題
- 開頭 `<div class="box box-concept">` 💡 一句話講完
- 「為什麼需要它」段(常接續前一章的脈絡)
- 概念段落,搭配 `box-concept`(💡 補充)、`box-warning`(⚠️ 注意)框
- `<hr>` 後一個 `<div class="box box-exercise">` 🛠 小練習(步驟 + 練習目的)
- `<div class="box box-check">` ✅ 走完本章你要能…
- 結尾 `.page-nav` 上一章 / 下一章

可用的 box 類別:`box-concept` / `box-warning` / `box-exercise` / `box-check`。圖片用 `<div class="screenshot"><img><div class="caption">說明</div></div>`。`script.js` 會自動替所有 `.prompt` 和 `<pre>` 加上「複製」按鈕,不需手動加。

## 內容守則(重要)

- **教學內容講的是 Claude Code 的功能,必須對照官方文件 https://code.claude.com/docs 撰寫,不要憑記憶寫功能行為。** 涉及指令、設定、行為的敘述,先查 docs 再下筆;引用官方說法時標明是原話還是推論。
- 維護者很在意「跟官方有無抵觸」與用字,動內容前先確認需求、有疑義先問。

## Git / 上傳

`.claude/settings.local.json`(個人 allow 清單)與 `practice_data/` 已列入 `.gitignore`,不上傳。`img/` 截圖可能含遊戲專案的真實 RTP / 企劃數據,推公開 repo 前需確認可否公開。
