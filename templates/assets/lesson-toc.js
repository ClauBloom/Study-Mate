/* ═══════════════════════════════════════════════════════════════
   StudyMate · 课件侧边目录（自动生成，写课件的人不用手写）
   ═══════════════════════════════════════════════════════════════
   用法：课件页底部引一次（骨架 templates/lesson.html 里已经带好）：

     <script src="../assets/lesson-toc.js" defer></script>

   它做什么：
   - 从 <article class="lesson"> 里取出全部 <h2>（小节。h3 是节内步骤，不进目录）
   - 给还没有 id 的小节补一个稳定 id，生成 <aside class="lesson-toc"> 与其锚点链接
   - 插在 .lesson-bar 之后；≥1180px 由 style.css 显示为左侧固定目录，窄屏不显示
   - 当前小节的高亮交给 Sayo：容器上带 data-syo-scrollspy，Sayo 自动扫描并切换 .active
     （本脚本是 defer，在 DOMContentLoaded 之前跑完，所以 Sayo 扫得到这些链接）

   少于两节、或页面上没有 .lesson 时不生成——一两节的目录只是噪音。
   ═══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  function build() {
    var lesson = document.querySelector('article.lesson');
    if (!lesson || document.querySelector('.lesson-toc')) return;

    var headings = [];
    Array.prototype.forEach.call(lesson.querySelectorAll('h2'), function (h2) {
      var text = (h2.textContent || '').trim();
      if (!text) return;
      if (!h2.id) h2.id = 'sec-' + (headings.length + 1);
      headings.push({ id: h2.id, text: text });
    });
    if (headings.length < 2) return;

    var aside = document.createElement('aside');
    aside.className = 'lesson-toc';
    aside.setAttribute('data-syo-scrollspy', '88');   // 顶栏高度 + 一点余量

    var title = document.createElement('div');
    title.className = 'lesson-toc__title';
    title.textContent = '本节目录';
    aside.appendChild(title);

    var nav = document.createElement('nav');
    headings.forEach(function (item) {
      var link = document.createElement('a');
      link.href = '#' + item.id;
      link.textContent = item.text;
      nav.appendChild(link);
    });
    aside.appendChild(nav);

    var bar = document.querySelector('.lesson-bar');
    if (bar && bar.parentNode) bar.parentNode.insertBefore(aside, bar.nextSibling);
    else document.body.appendChild(aside);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();
