# 回归测试

```bash
bash scripts/tests/run_tests.sh              # 11 套快测（纯 Python/Node）
bash scripts/tests/run_tests.sh --browser    # 再加需要 google-chrome 的 2 套（共 13 套）
```

只依赖 `python3` + `pyyaml`（跑检查要用）与 `node`（两套 DOM 测试）；没有 node 会自动跳过那两套。
测试自己造临时科目，**不读也不写任何工作区**（`workspace/` 是学生数据，测试不该碰）。

## DSH 实际安装与启动

先在独立目录安装要检查的 DSH，然后指定其包目录：

```sh
npm install --prefix /tmp/studymate-dsh @deepseek-ai/dsh@0.1.7-alpha.2
export STUDYMATE_DSH_PACKAGE=/tmp/studymate-dsh/node_modules/@deepseek-ai/dsh
npm run test:dsh
npm run test:dsh-cli
```

需要 Python 3.9+、PyYAML；CLI 测试另需 `pnpm`。未设置 `STUDYMATE_DSH_PACKAGE` 时跳过，不读取本机默认 DSH 配置。
测试创建临时 HOME、DSH_HOME 和工作区，启动仅监听本机随机端口的 Web，不调用模型。CLI 测试通过临时本地 registry 安装、更新和卸载实际打包的 StudyMate，检查普通模式、学习模式、安装方式切换、缺少 Python 及学习数据保留。

另设 `STUDYMATE_DSH_DOWNGRADE_PACKAGE` 为旧 DSH 包目录，可以检查旧版安装升级后的显式迁移，以及降级和重新安装恢复。两个 DSH 目录只读。CI 覆盖 Windows、macOS、Linux 的旧版和新版，以及 Linux 上的版本切换边界。

## 快测（默认跑）

| 套件 | 钉住什么 |
|---|---|
| `test_install.py` | `install.sh` / `install.ps1`（按平台实跑）：预设装到哪、占位符换成引擎 skills 路径、**委派工具口径（`tool-subagent-fork` 必须 `disabled: true`、`subagent` 的 `maxDepth` 必须 `1`——fork 会把总控已完成的回合注进角色，角色会反过来当总控）**、预设整份能被 YAML 解析（含 `!!js` 行）、工作区写成**绝对路径**（`~` 展开、相对路径落绝对）、重复跑沿用已有工作区、引擎搬走后 `root`/skills 重写、仓库不完整时报错；另验装完能跑 `gen_home` 出空状态主页。另验含单引号、方括号和 `#` 的路径及重复安装；静态检查两版关键动作对齐。全部在沙箱 `HOME` / `USERPROFILE` 里跑（30 项） |
| `test_quiz_attr.py` | 检查对 `data-quiz` 属性值写法的判定：9 例矩阵（单引号/双引号包裹 × 引号怎么写），含「实体引号提前闭合 JSON 字符串」与「裸引号把属性截断」两类 |
| `test_quiz_code.py` | 题面里的 ` ``` ` 代码围栏：成对放行、没闭合即拦（含 `answer` 字段）、行内单个反引号不算围栏（12 例） |
| `test_lesson_figure.py` | 检查项 9（配图）：本地图存在放行、**不存在即拦**（学生看到裂图；`gen_home` 的链接自检只管它写出的主页，课件页不在其范围内）、外链图与缺 `alt` 只提示、内联 SVG 不需要文件（5 例） |
| `test_naming_nav.py` | 检查项 8：文件名与大纲位次一致、上/下节课指针指向大纲邻居、悬空指针只提示、归属查不出即 FAIL（9 个场景） |
| `test_pool.py` | 图片库校验器 `check_pool.py`：表头七列齐全（分隔行跳过）、每行的图真在 `assets/img/pool/` 下、文件名合规（字符集 + ≤60 字符）、`来源 URL`/`许可`/`抓取日期` 非空、单张 ≤500 KB（按文件字节，不读 `尺寸` 列）（6 例） |
| `test_lesson_scripts.py` | 总控的两件机械活做成脚本后的回归：`renumber_lessons.py`（大纲插/删节点后按 `nodes:` 顺序重排 `lessons/` 的文件名序号，三件保持一致、冲突即拒、`--dry-run` 不写盘、`--render` 调渲染器重算指针、认不出的名字不动）与 `apply_empty_reasons.py`（把出题人的 `empty_reason` 按 TSV 打进对应 `::: quiz` 块；锚点找不到／同锚点两块／块里已有理由／TSV 重复或空值一律先校验后写、出错一个文件都不动）（21 例） |
| `test_render_lesson.py` | 课件渲染器 `render_lesson.py`：壳与接线齐全、正文与代码块的 `&<>` 转义且代码原文逐字、表格/列表/围栏/行内标记、题目按锚点合入且 `data-quiz` 单引号包裹与实体正确、锚点无题必须 `empty_reason`（且**只准**出现在 `::: quiz`：写进 `::: practice`／`::: tip` 会被当段落印成 `<p>empty_reason: …</p>`，按错拦下）、锚点**双向**对账（题库里多出来的孤儿键、同一个锚点被两个题目位置引用，都带行号报错）、用法错误退 2 与坏题库三种形态（非 JSON／非对象／值是空数组）、配图存在性与题注来源、导航序号按大纲算、未知指令与手写 HTML（块首与段落中间、HTML 注释、front matter 的 title、`alt:` 与 `caption:`、`script`/`style`/`link`/`meta` 与 `iframe`/`video`/`form`/`main`/`button`/`canvas` 及 11 个 SVG 名）带行号报错、一级标题与行首 `#include` 不许静默消失、运算符/泛型/落单反引号不误伤、真标签名单是完整 HTML 元素表 + SVG 名且与格式文档和测试里的字面集合逐字一致、名单里每个名字都必须被形状正则捕获（连字符名 `<syo-editor>` 捕不到，只能做成 `:::` 指令）、`::: svg` 的收尾按保留换行的文本判（拆成两行不算闭合）、模板占位符报错指向真实行号、`--check` 不写盘、渲染产物过检查（含 `kind: 实验` 的无题库说明页）且不带模板说明注释（26 例） |
| `test_skill_rules.py` | 提示词回归：`.dsh/skills/*/SKILL.md` 里 417 条可执行规则逐条在位（压缩/改写时不许丢规则；`evidence-check` 的「原字段名 `evidence`」那条随提示词精简一并移除，映射仍留在 `docs/使用说明.md`） |
| `quiz_dom_test.js` | `templates/assets/quiz.js`：选择题判分、开放题展开/收起、坏数据兜底、计分，以及围栏 → `<pre><code>` 的渲染与 `textContent` 语义、异常数据隔离和开头围栏（33 项） |
| `toc_dom_test.js` | `templates/assets/lesson-toc.js`：侧栏目录、折叠、移动端抽屉、上/下节课指针搬进侧栏、平板默认折叠与展开状态（33 项） |

## 浏览器套件（`--browser`）

| 套件 | 用途 |
|---|---|
| `browser/hl_test.mjs` | 在真实 Chrome 里验 `learn-theme.js` 的代码块高亮：语言识别（cpp/sh/term/html/js/json/ts）、手写高亮块不被覆盖、`data-lang` 生效（29 项） |
| `browser/quiz_code_test.mjs` | 题目里的代码块在真实 Chrome 里的样子：等宽、非粗体、**缩进按行保留**（按 Range 量左边界）、自动上色（`syn-*` 类真的出现——它验的是 quiz.js 建块后自己再触发一次扫描）、无围栏的题面不产生代码块（11 项） |
| `browser/measure.mjs` | 主题测量：对比度扫描（含元素 `opacity` 与合成）、指定选择器的计算值、`--hover` 实测某选择器悬停态 |
| `browser/hovers.mjs` | 批量取 hover 前后的计算值（给「悬停不许改底色」这类判断用） |
| `browser/shot.mjs` | 截图工具：整页截图 + 记录目标元素的框（浅色/深色各一张），供人工验收与文档配图；`node scripts/tests/browser/shot.mjs <file-url> <out-prefix> <css-selector>`，chrome 起不来或选择器没命中就一行报错 + 非零退出 |
| `browser/palette.py` | 由主色算一套配色表（纯 Python，不开浏览器） |
| `browser/highlight-fixture.html` | 高亮套件的 fixture（引用仓库内的 `templates/assets/`） |
| `browser/quiz-code-fixture.html` | 题目代码块的 fixture：一道围栏题 + 一道纯散文题（回归用） |

`measure.mjs`、`hovers.mjs`、`shot.mjs` 与 `palette.py` 是**手动工具**不是断言套件：前三个要自己给页面 URL
（`node scripts/tests/browser/measure.mjs file:///…/index.html [--hover ".sel"]`、
`node scripts/tests/browser/shot.mjs <file-url> <out-prefix> <css-selector>`），`palette.py` 吃主色出配色表。

## 写新测试

`fixtures.py` 负责造一份**能过检查**的最小科目（`curriculum.yaml` + 课件 + 正确的上下节课指针），
测试只往里注入自己那一处偏差，断言就不会被无关的 FAIL 污染：

```python
import fixtures
subject = fixtures.write_subject(tmp)                       # 5 个概念节点
path = fixtures.write_lesson(subject, 2, 'first-program',   # 指针自动填对
                             quiz='<div class="quiz" data-quiz=…></div>')
code, out = fixtures.run_gate(path, subject, 'first-program')
```

课件渲染器那条链路（内容文件 → HTML）用另一组 fixture——内容文件、题库、渲染、再过检查：

```python
subject = fixtures.write_subject(tmp, name='测试科目')       # name 给了才写 subject.yaml
md = fixtures.write_content(subject, 2, 'first-program',    # 默认一份最小正文，body 可换
                            body='## 小节\n\n::: quiz 理解 锚点：本节校验\n:::\n')
fixtures.write_quiz(subject, 2, 'first-program', {'本节校验': [{'q': '…', 'answer': '…', 'criteria': '…'}]})
code, out = fixtures.run_render(subject, 'first-program')   # 第 3 个参数起原样传给渲染器（如 '--check'）
code, out = fixtures.run_gate(fixtures.lesson_html(subject, 2, 'first-program'),
                              subject, 'first-program')
```

注意：概念课不要求 lab，所以 fixture 全是 `kind: 概念`；要测 lab 相关的判定得自己造 `lab/` 产物。
