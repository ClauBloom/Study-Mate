/* ═══════════════════════════════════════════════════════════════
   StudyMate · 课件题目组件（数据契约的唯一出处）
   ═══════════════════════════════════════════════════════════════
   用法（课件里这样写）：

     <div class="quiz" data-quiz='[
       {"q":"选择题题干","opts":["选项A","选项B","选项C"],"ans":1,"why":"一句解释"},
       {"q":"开放题题干","answer":"参考答案","criteria":"算过标准（学生据此自评）"}
     ]'></div>
     <script src="../assets/quiz.js" defer></script>

   属性值的引号（**必读**；写错闸门会拦，浏览器里题目块直接退化成「题目数据解析失败」）：
     属性值里出现**同种**引号是 HTML5 禁止的，浏览器必然在那里把属性截断。所以值里的
     引号一律写成实体——浏览器解码后再交给 JS，拿到的仍是原文：

       单引号 ' → &#39;     双引号 " → &quot;     小于号 < → &lt;     大于号 > → &gt;

     报错原文里引号极常见（`expected ';' before 'return'`、`it's`），照抄进题面必须先转义：

       {"q":"报错 expected &#39;;&#39; before &#39;return&#39; 是什么意思？"}

   data-quiz 是 JSON 数组，每项是一道题，**两种题型二选一**（不能同时写两组字段）：

   题型一 · 选择题（页内自动判）
     q     题干（字符串，必填，两种题型都要）
     opts  选项数组（必填，≥2 项）
     ans   正确选项下标，从 0 开始（必填，必须落在 opts 范围内）
     why   答完显示的一句解释（必填：闸门会拦，见 scripts/check_lesson.py）

   题型二 · 开放题（学生自评，不贴回会话）
     q         题干（字符串，必填）
     answer    参考答案（必填）
     criteria  算过标准：凭什么算答对了（必填；学生点开对照时看到的就是这两段）

   行为：
   - 选择题：点选项立刻给反馈（对/错 + why）；选错的标红、正确的标绿；允许改选，计分只算第一次；
     一组里的选择题全部答完后显示"答对 N / M"，并用 Sayo toast 提示一次（M 只数选择题）
   - 开放题：先只显示题干和"想好了，看参考答案"按钮；点开显示参考答案 + 算过标准；再点一次收起
     （方便隔一会儿重答一遍）。开放题不计分、不判定——它是自测
   - 课件没加载 sayo.js 时自动降级为纯内联反馈（不依赖 Sayo）
   - 题目数据不完整时页面显示提示，不静默吞掉

   出题与判分规范在 <root>/.dsh/skills/layered-practice（题目唯一规范）；
   闸门 scripts/check_lesson.py 按上面这套字段做结构校验。
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

  function questionText(item, index, total) {
    return (total > 1 ? (index + 1) + '. ' : '') + (item.q || '');
  }

  /* ── 选择题：点选项即时反馈 ─────────────────────────────────── */
  function buildChoice(block, item, index, total, state) {
    var question = document.createElement('p');
    question.className = 'quiz__q';
    question.textContent = questionText(item, index, total);
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
          if (state.answered === state.total) {
            if (state.scoreEl) {
              state.scoreEl.hidden = false;
              state.scoreEl.textContent = '本题组：答对 ' + state.correct + ' / ' + state.total;
            }
            toast(
              state.correct === state.total ? '全部答对（' + state.total + '/' + state.total + '）'
                                            : '答对 ' + state.correct + ' / ' + state.total,
              state.correct === state.total ? 'success' : 'info'
            );
          }
        }
      });

      opts.appendChild(btn);
    });

    block.appendChild(opts);
    block.appendChild(feedback);
  }

  /* ── 开放题：自己先答，点开对照参考答案与算过标准（不贴回会话）── */
  function buildOpen(block, item, index, total) {
    var question = document.createElement('p');
    question.className = 'quiz__q';
    question.textContent = questionText(item, index, total);
    block.appendChild(question);

    var wrap = document.createElement('div');
    wrap.className = 'quiz__open';

    var reveal = document.createElement('button');
    reveal.type = 'button';
    reveal.className = 'quiz__reveal';
    reveal.textContent = '想好了，看参考答案';

    var answer = document.createElement('div');
    answer.className = 'quiz__answer';
    answer.hidden = true;

    var answerLabel = document.createElement('p');
    answerLabel.className = 'quiz__answer-label';
    answerLabel.textContent = '参考答案';
    var answerText = document.createElement('p');
    answerText.className = 'quiz__answer-text';
    answerText.textContent = item.answer || '';

    var criteriaLabel = document.createElement('p');
    criteriaLabel.className = 'quiz__answer-label';
    criteriaLabel.textContent = '算过标准';
    var criteriaText = document.createElement('p');
    criteriaText.className = 'quiz__criteria';
    criteriaText.textContent = item.criteria || '';

    answer.appendChild(answerLabel);
    answer.appendChild(answerText);
    answer.appendChild(criteriaLabel);
    answer.appendChild(criteriaText);

    reveal.addEventListener('click', function () {
      answer.hidden = !answer.hidden;
      reveal.textContent = answer.hidden ? '想好了，看参考答案' : '收起，再自己答一遍';
    });

    wrap.appendChild(reveal);
    wrap.appendChild(answer);
    block.appendChild(wrap);
  }

  /* ── 数据不完整时的兜底 ─────────────────────────────────────── */
  function buildBroken(block, item, index, total) {
    var question = document.createElement('p');
    question.className = 'quiz__q';
    question.textContent = questionText(item, index, total);
    block.appendChild(question);

    var hint = document.createElement('p');
    hint.className = 'feedback wrong';
    hint.textContent = '（这道题的数据不完整：选择题要 opts/ans/why，开放题要 answer/criteria）';
    block.appendChild(hint);
  }

  /* ── 题型判定（与闸门、分层规范一致：两组字段只能二选一）──────── */
  function isChoiceItem(item) {
    return !!item && typeof item === 'object' && !Array.isArray(item) &&
           Array.isArray(item.opts) && typeof item.ans === 'number';
  }

  function isOpenItem(item) {
    return !!item && typeof item === 'object' && !Array.isArray(item) &&
           typeof item.answer === 'string' && typeof item.criteria === 'string';
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

      var choiceCount = items.filter(isChoiceItem).length;

      var state = { answered: 0, correct: 0, total: choiceCount };
      if (choiceCount > 1) {
        state.scoreEl = document.createElement('p');
        state.scoreEl.className = 'quiz__score';
        state.scoreEl.hidden = true;
      }

      items.forEach(function (item, index) {
        if (isChoiceItem(item)) buildChoice(block, item, index, items.length, state);
        else if (isOpenItem(item)) buildOpen(block, item, index, items.length);
        else buildBroken(block, item, index, items.length);
      });

      if (state.scoreEl) block.appendChild(state.scoreEl);
    });
  });
})();
