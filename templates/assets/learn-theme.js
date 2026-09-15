/* ═══════════════════════════════════════════════════════════════
   StudyMate · 主题（亮色/暗色）共享逻辑
   ═══════════════════════════════════════════════════════════════
   根主页、科目主页、课件三个页面共用这一份，不要在页面里各写一套。

   用法（三步）：

     <!-- 1) <head> 里尽早应用主题，避免首帧闪白/闪黑 -->
     <script src="…/learn-theme.js"></script>
     <script>LearnTheme.apply();</script>

     <!-- 2) 页面里放一个 Sayo 主题开关 -->
     <label class="syo-toggle syo-toggle--theme">
       <input type="checkbox" id="theme-checkbox">
       <span class="syo-toggle-track"></span>
       <span class="syo-toggle-knob"> …日/月图标… </span>
     </label>

     // 3) 页面脚本末尾绑定它
     LearnTheme.wire(document.getElementById('theme-checkbox'));

   主题取值规则（apply 时）：
     URL 上的 ?theme=dark|light  →  优先，且不写入偏好（方便预览）
     localStorage['le-theme']    →  其次（学生在任何页面切过都记住）
     都没有                      →  亮色（我们的暖色系；暗色是 Sayo 的 Primer 暗色）

   约定：只用一个 data-theme 属性；**不要**用 Sayo 自带的 data-syo-theme，两套属性会打架。
   ═══════════════════════════════════════════════════════════════ */
(function (global) {
  'use strict';

  var KEY = 'le-theme';
  var root = document.documentElement;

  function readSaved() {
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) { /* file:// 下可能不可用 */ }
    return (saved === 'dark' || saved === 'light') ? saved : null;
  }

  function fromQuery() {
    var q = null;
    try { q = new URLSearchParams(global.location.search).get('theme'); } catch (e) {}
    return (q === 'dark' || q === 'light') ? q : null;
  }

  function current() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  /* 应用主题：可选传 'light'/'dark' 强制指定；不传则按上面的优先级推断 */
  function apply(theme) {
    var next = theme || fromQuery() || readSaved() || 'light';
    root.setAttribute('data-theme', next === 'dark' ? 'dark' : 'light');
    return current();
  }

  /* 切换并记住（persist=false 时只改不记） */
  function set(theme, persist) {
    var next = theme === 'dark' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    if (persist !== false) {
      try { localStorage.setItem(KEY, next); } catch (e) {}
    }
    return next;
  }

  function toggle() {
    return set(current() === 'dark' ? 'light' : 'dark');
  }

  /* 把页面上的 Sayo 主题开关接上：勾选 = 亮色 */
  function wire(checkbox) {
    if (!checkbox) return;
    checkbox.checked = current() === 'light';
    checkbox.addEventListener('change', function () {
      set(checkbox.checked ? 'light' : 'dark');
    });
  }

  global.LearnTheme = {
    KEY: KEY,
    apply: apply,
    set: set,
    toggle: toggle,
    current: current,
    wire: wire
  };
})(window);
