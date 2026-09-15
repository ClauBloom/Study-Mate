/* ═══════════════════════════════════════════════════════════════
   StudyMate · 课件交互组件：选择题即时反馈
   ═══════════════════════════════════════════════════════════════
   用法（与计划约定一致，课件里这样写）：

     <div class="quiz" data-quiz='[
       {"q":"问题文本","opts":["选项A","选项B","选项C"],"ans":1}
     ]'></div>
     <script src="../assets/quiz.js" defer></script>

   data-quiz 是 JSON 数组，每项：
     q    问题（字符串，必填）
     opts 选项数组（必填）
     ans  正确选项的下标，从 0 开始（必填）
     why  可选：答完显示的一句解释（推荐写上，"对/错"之外给个为什么）

   行为：
   - 点选项立刻给反馈：答对/答错 + 解释；选错的选项标红，正确的标绿
   - 允许改选（重讲一遍后可以再点一次），但计分只算第一次作答
   - 一组题全部答完后显示"答对 N / M"，并用 Sayo toast 提示一次
   - 课件没加载 sayo.js 时自动降级为纯内联反馈（不依赖 Sayo）

   出题规范（给写课件的人）：选项尽量等长（同句式、同字数），避免长度泄露答案。
   ═══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  function whenReady(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  /* Sayo toast 是增强项：没有 sayo.js（或调用失败）就静默跳过 */
  function toast(message, type) {
    if (window.Sayo && window.Sayo.toast && typeof window.Sayo.toast.show === 'function') {
      try { window.Sayo.toast.show(message, { type: type }); return true; } catch (e) { /* 忽略 */ }
    }
    return false;
  }

  function buildItem(block, item, index, total, state) {
    var question = document.createElement('p');
    question.className = 'quiz__q';
    question.textContent = (total > 1 ? (index + 1) + '. ' : '') + (item.q || '');
    block.appendChild(question);

    var opts = document.createElement('div');
    opts.className = 'quiz__opts';

    var feedback = document.createElement('p');
    feedback.className = 'feedback';
    feedback.hidden = true;

    var firstAnswer = true;

    (item.opts || []).forEach(function (text, i) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'quiz__opt';
      btn.textContent = text;

      btn.addEventListener('click', function () {
        var ok = i === item.ans;

        Array.prototype.forEach.call(opts.children, function (other) {
          other.classList.toggle('is-picked', other === btn);
          other.classList.toggle('is-correct', other === btn && ok);
          other.classList.toggle('is-wrong', other === btn && !ok);
        });

        feedback.hidden = false;
        feedback.className = 'feedback ' + (ok ? 'correct' : 'wrong');
        feedback.textContent = (ok ? '✓ 对' : '✗ 再想想') + (item.why ? '　' + item.why : '');

        if (firstAnswer) {
          firstAnswer = false;
          state.answered += 1;
          if (ok) state.correct += 1;
          if (state.answered === total && state.scoreEl) {
            state.scoreEl.hidden = false;
            state.scoreEl.textContent = '本题组：答对 ' + state.correct + ' / ' + total;
            toast(
              state.correct === total ? '全部答对（' + total + '/' + total + '）' : '答对 ' + state.correct + ' / ' + total,
              state.correct === total ? 'success' : 'info'
            );
          }
        }
      });

      opts.appendChild(btn);
    });

    block.appendChild(opts);
    block.appendChild(feedback);
  }

  whenReady(function () {
    var blocks = document.querySelectorAll('.quiz[data-quiz]');

    Array.prototype.forEach.call(blocks, function (block) {
      var items;
      try {
        items = JSON.parse(block.getAttribute('data-quiz') || '[]');
      } catch (e) {
        block.textContent = '（题目数据解析失败：data-quiz 不是合法 JSON）';
        return;
      }
      if (!Array.isArray(items) || items.length === 0) {
        block.textContent = '（这组题还没有内容）';
        return;
      }

      var state = { answered: 0, correct: 0 };
      if (items.length > 1) {
        state.scoreEl = document.createElement('p');
        state.scoreEl.className = 'quiz__score';
        state.scoreEl.hidden = true;
      }

      items.forEach(function (item, index) {
        buildItem(block, item, index, items.length, state);
      });

      if (state.scoreEl) block.appendChild(state.scoreEl);
    });
  });
})();
