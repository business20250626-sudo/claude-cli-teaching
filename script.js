/* ============================================================
   Claude Code 入門 — 互動腳本
   功能:
   1) 為每一個 .prompt 與 <pre> 代碼區塊產生「複製」按鈕
   ============================================================ */

(function () {
  'use strict';

  function getPromptText(promptEl) {
    // 複製按鈕本身不應被複製進去
    const clone = promptEl.cloneNode(true);
    clone.querySelectorAll('.copy-btn').forEach((b) => b.remove());
    // innerText 會保留 <br> 換成換行,且去除多餘空白
    return clone.innerText.trim();
  }

  function makeCopyButton(promptEl) {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.textContent = '📋 複製';
    btn.setAttribute('aria-label', '複製這段內容');

    btn.addEventListener('click', async function () {
      const text = getPromptText(promptEl);
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(text);
        } else {
          // file:// 開啟時 clipboard API 可能不可用,用 fallback
          const ta = document.createElement('textarea');
          ta.value = text;
          ta.style.position = 'fixed';
          ta.style.opacity = '0';
          document.body.appendChild(ta);
          ta.focus();
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        }
        btn.textContent = '✅ 已複製';
        btn.classList.add('copied');
        setTimeout(function () {
          btn.textContent = '📋 複製';
          btn.classList.remove('copied');
        }, 1500);
      } catch (err) {
        btn.textContent = '❌ 複製失敗';
        setTimeout(function () {
          btn.textContent = '📋 複製';
        }, 2000);
      }
    });

    return btn;
  }

  function init() {
    // .prompt(給 Claude 的指令)與 <pre>(代碼區塊)都加上複製按鈕
    const targets = document.querySelectorAll('.prompt, pre');
    targets.forEach(function (el) {
      if (el.querySelector('.copy-btn')) return; // 防止重複加
      el.appendChild(makeCopyButton(el));
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
