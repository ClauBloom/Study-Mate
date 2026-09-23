/* StudyMate · 课件公式排版（离线 KaTeX，MIT，见 katex/LICENSE）
 *
 * 渲染器把 `$…$` 与 `$$…$$` 写成：
 *   <span class="math-inline">TeX 原文</span>   /   <div class="math-block">TeX 原文</div>
 * 元素里**先放 TeX 原文**——没有 JS、或 KaTeX 没加载成功时，学生读到的还是公式源码（降级可读，
 * 不会白屏）。这个脚本加载后把它们替换成排版结果。
 *
 * 只处理这两个类名，不做全文扫描：代码块里的 `$` 不该被当成公式，扫描式方案（auto-render）
 * 分不清代码与正文，所以这里由渲染器明确标出位置。
 */
(function () {
  'use strict';
  if (typeof katex === 'undefined') return;
  var nodes = document.querySelectorAll('.math-inline, .math-block');
  for (var index = 0; index < nodes.length; index += 1) {
    var node = nodes[index];
    var tex = node.textContent;
    try {
      katex.render(tex, node, {
        displayMode: node.classList.contains('math-block'),
        throwOnError: false,      // TeX 写错时显示成红色原文，不炸整页
        strict: 'ignore'
      });
    } catch (error) {
      node.textContent = tex;     // 兜底：留着原文
    }
  }
})();
