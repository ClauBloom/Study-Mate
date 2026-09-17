# 回归测试

```bash
bash scripts/tests/run_tests.sh              # 5 套快测（纯 Python/Node，约 3 秒）
bash scripts/tests/run_tests.sh --browser    # 再加需要 google-chrome 的高亮那套
```

只依赖 `python3` + `pyyaml`（跑闸门要用）与 `node`（两套 DOM 测试）；没有 node 会自动跳过那两套。
测试自己造临时科目，**不读也不写任何工作区**（`workspace/` 是学生数据，测试不该碰）。

## 快测（默认跑）

| 套件 | 钉住什么 |
|---|---|
| `test_quiz_attr.py` | 闸门对 `data-quiz` 属性值写法的判定：9 例矩阵（单引号/双引号包裹 × 引号怎么写），含「实体引号提前闭合 JSON 字符串」与「裸引号把属性截断」两类 |
| `test_quiz_code.py` | 题面里的 ` ``` ` 代码围栏：成对放行、没闭合即拦（含 `answer` 字段）、行内单个反引号不算围栏（6 例） |
| `test_naming_nav.py` | 闸门检查项 8：文件名与大纲位次一致、上/下节课指针指向大纲邻居、悬空指针只提示、归属查不出即 FAIL（9 个场景） |
| `test_skill_rules.py` | 提示词回归：`.dsh/skills/*/SKILL.md` 里 278 条可执行规则逐条在位（压缩/改写时不许丢规则） |
| `quiz_dom_test.js` | `templates/assets/quiz.js`：选择题判分、开放题展开/收起、坏数据兜底、计分，以及围栏 → `<pre><code>` 的渲染与 `textContent` 语义（26 项） |
| `toc_dom_test.js` | `templates/assets/lesson-toc.js`：侧栏目录、折叠、移动端抽屉、上/下节课指针搬进侧栏（27 项） |

## 浏览器套件（`--browser`）

| 套件 | 用途 |
|---|---|
| `browser/hl_test.mjs` | 在真实 Chrome 里验 `learn-theme.js` 的代码块高亮：语言识别（cpp/sh/term/html/js/json/ts）、手写高亮块不被覆盖、`data-lang` 生效（29 项） |
| `browser/quiz_code_test.mjs` | 题目里的代码块在真实 Chrome 里的样子：等宽、非粗体、**缩进按行保留**（按 Range 量左边界）、自动上色（`syn-*` 类真的出现——它验的是 quiz.js 建块后自己再触发一次扫描）、无围栏的题面不产生代码块（11 项） |
| `browser/measure.mjs` | 主题测量：对比度扫描（含元素 `opacity` 与合成）、指定选择器的计算值、`--hover` 实测某选择器悬停态 |
| `browser/hovers.mjs` | 批量取 hover 前后的计算值（给「悬停不许改底色」这类判断用） |
| `browser/palette.py` | 由主色算一套配色表（纯 Python，不开浏览器） |
| `browser/highlight-fixture.html` | 高亮套件的 fixture（引用仓库内的 `templates/assets/`） |
| `browser/quiz-code-fixture.html` | 题目代码块的 fixture：一道围栏题 + 一道纯散文题（回归用） |

后三个是**手动工具**不是断言套件：`measure.mjs` 与 `hovers.mjs` 要自己给页面 URL
（`node scripts/tests/browser/measure.mjs file:///…/index.html [--hover ".sel"]`）。

## 写新测试

`fixtures.py` 负责造一份**能过闸门**的最小科目（`curriculum.yaml` + 课件 + 正确的上下节课指针），
测试只往里注入自己那一处偏差，断言就不会被无关的 FAIL 污染：

```python
import fixtures
subject = fixtures.write_subject(tmp)                       # 5 个概念节点
path = fixtures.write_lesson(subject, 2, 'first-program',   # 指针自动填对
                             quiz='<div class="quiz" data-quiz=…></div>')
code, out = fixtures.run_gate(path, subject, 'first-program')
```

注意：概念课不要求 lab，所以 fixture 全是 `kind: 概念`；要测 lab 相关的判定得自己造 `lab/` 产物。
