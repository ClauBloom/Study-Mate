# templates/assets/ — 前端资源与引用契约

本目录是引擎项目里的**前端资源源**。学习工作区里的资源由 install.sh / gen_home.py / 总控（建科目时）
按下面的规则放置，页面按**固定相对路径**引用（模板里写死，生成器不改）。

## 目录职责

| 路径 | 是什么 | 谁维护 |
|------|--------|--------|
| `sayo/` | **Sayo UI**（自研零依赖 CSS 框架 + 交互引擎），MIT。含 `sayo.css`、`sayo.js`、`icons/`、`LICENSE` | 从 sayo-ui 项目整体拷贝，**不要手改** |
| `learn-theme.css` | 本项目**共享主题层**：亮色=暖纸白+深绿（覆盖 `--syo-*`）、暗色=用 Sayo 默认的 Primer 暗色；修正 Sayo 里为暗色硬编码的紫色光晕；放跨页面组件（进度条、状态徽标、筛选、空状态） | 本项目自研，改色只改这里 |
| `learn-theme.js` | **共享行为层**：① 主题（亮/暗）逻辑——早期应用、切换并持久化、绑定开关（`LearnTheme.apply/set/toggle/current/wire`）；② **代码块高亮**——课件里的 `<pre><code>` 与 `.syo-editor` 加载即自动上色（`LearnTheme.highlight`）。三个页面共用，别各写一份 | 本项目自研 |
| `learn-mascot.png` | **抬头看板娘**（640×425，256 色带 alpha，23KB）：透明底 + 底部羽化，给根主页抬头当主视觉（`.learn-hero__mascot`） | 本项目自研；**只有根主页引用它**，科目页与课件不引用 |
| `style.css` | **课件层**（讲解排版 + 练习样式），叠在 Sayo 之上 | 本项目自研；Task 8 拷进每个科目 |
| `quiz.js` | 课件**题目组件**（选择题即时反馈 + 开放题点开对照参考答案与判分要点）。数据契约以它顶部注释为准 | 同上 |
| `lesson-toc.js` | 课件**侧边目录 + 上/下节课入口**：目录按页面 `<h2>` 自动生成；正文里的 `<nav class="lesson-nav">`（**渲染器按 `curriculum.yaml` 算出来的真实链接**）会被搬到目录下面。样式照搬 sayo-ui 文档页的 `.doc-sidebar`（可折叠成 rail、≤768px 变抽屉 + 汉堡），高亮交给 Sayo 的 `data-syo-scrollspy` | 同上 |

## 在工作区里的落地位置与引用路径

```text
<LEARN_WORKSPACE>/
├── index.html                                  # 根主页（生成产物）
└── .learning/
    ├── assets/                                 # ← 全工作区共享一份
    │   ├── sayo/{sayo.css,sayo.js,icons/,LICENSE}
    │   ├── learn-theme.css
    │   ├── learn-theme.js
    │   └── learn-mascot.png
    └── subjects/<slug>/
        ├── index.html                          # 科目主页（生成产物）
        ├── assets/                             # ← 每个科目一份（Task 8 从 templates/assets/ 拷）
        │   ├── style.css
        │   ├── quiz.js
        │   └── lesson-toc.js
        └── lessons/                             # 每课三件：内容 + 题库由模型写，页面由渲染器产出
            ├── <NNNN>-<节点id>.md               # 内容文件（讲解角色写；格式见 docs/课件内容格式.md）
            ├── <NNNN>-<节点id>.quiz.json        # 题库（出题角色写；有 ::: quiz 题目位置时才要）
            └── <NNNN>-<节点id>.html             # 课件页面（render_lesson.py 产出，别手改）
```

各页面**必须**按下面的相对路径引用（路径写死在模板/课件里）；课件文件名的 `NNNN` = 节点在
`<科目>/curriculum.yaml` 的 `nodes:` 里的序号（渲染器按它算，别自己编）：

| 页面 | 引用共享层 | 引用本科目层 |
|------|-----------|-------------|
| 根主页 `<WS>/index.html` | `.learning/assets/sayo/sayo.css`<br>`.learning/assets/learn-theme.css`<br>`.learning/assets/learn-theme.js`<br>`.learning/assets/sayo/sayo.js`<br>`.learning/assets/learn-mascot.png`（抬头看板娘，`<img>`） | — |
| 科目主页 `<WS>/.learning/subjects/<slug>/index.html` | `../../assets/sayo/sayo.css`<br>`../../assets/learn-theme.css`<br>`../../assets/learn-theme.js`<br>`../../assets/sayo/sayo.js` | `assets/style.css` |
| 课件 `<WS>/.learning/subjects/<slug>/lessons/<NNNN>-<节点id>.html`<br>（由 `scripts/render_lesson.py` 从 `<NNNN>-<节点id>.md` + `.quiz.json` 渲染产出；`templates/lesson.html` 是占位符壳，**不要手工拷贝**） | `../../../assets/sayo/sayo.css`<br>`../../../assets/learn-theme.css`<br>`../../../assets/learn-theme.js`<br>`../../../assets/sayo/sayo.js` | `../assets/style.css`<br>`../assets/quiz.js`<br>`../assets/lesson-toc.js` |

> 路径提示：课件在 `.learning/subjects/<slug>/lessons/` 下，向上三层就是 `.learning/`，
> 所以共享层是 `../../../assets/…`（不要再写一层 `.learning`）；科目内组件则是 `../assets/…`。
>
> 为什么分两层：共享层体积 260KB+，每个科目各拷一份纯属浪费；`style.css` / `quiz.js` / `lesson-toc.js`
> 留在科目内，是因为它们是**课件层的三个组件**，按「总控建科目」的口径随科目落地，渲染器产出的课件
> 按 `../assets/…` 引用它们（题目内容与字段契约归题目角色，不在这里改）。**讲解角色不往这里追加组件**：
> 页面里的组件 HTML 全部由渲染器产出，要加新组件得给渲染器加 `:::` 指令——流程见
> `docs/课件内容格式.md` 的「已知边界」。

## 代码块高亮约定

课件的代码块**不用手写高亮**：页面加载时 `learn-theme.js` 会给 `<pre><code>` 与 `.syo-editor-code` 里的
代码自动上色（token 类沿用 Sayo 的 `.syn-*`，颜色随亮/暗主题走）。

- 语言按内容猜：`cpp` / `sh` / `term`（终端与编译器输出）/ `html` / `js` / `json`；猜不出来就**保持原样**（程序输出、题面文字不该被染色）
- 要指定就写 `data-lang="cpp|sh|html|js|json|term"`；`data-lang="text"` = 明确不上色
- 一个块里只要手写过 `.syn-*`，整块跳过——手工优先，自动不覆盖
- 猜错的常见场合：整块贴的都是「命令 + 输出」混排时按首行判定，可用 `data-lang` 纠正

## 主题约定

- **默认是暗色**：三个页面的首帧都写 `<html data-theme="dark">`，`LearnTheme.apply()` 的兜底也是 `'dark'`
  （**暗色是保底默认，亮色是覆盖层**）。
  优先级：`?theme=` 查询参数 > `localStorage['le-theme']` > 默认暗色
- **暗色**：`<html data-theme="dark">` → 用 Sayo 自己的 Primer 暗色 + 紫强调（`learn-theme.css` 不覆盖）
- **亮色**：`<html data-theme="light">` → `learn-theme.css` 把 Sayo 令牌映射成暖纸白 + 深绿
- 切换：页面脚本改 `data-theme` 并写 `localStorage['le-theme']`；
  **不要**用 Sayo 的 `data-syo-theme` 属性，两套属性会打架
- 装饰性交互（自定义光标、光晕、拖尾、波纹）**默认不开**：不加 `body[data-syo-*]` 属性即可。
  目前只开：科目页课件目录的 `data-syo-inertia`（根主页抬头的 `data-syo-parallax`
  随星空层一起撤了——抬头主视觉换成看板娘后没有可挂视差的背景层）

## 更新 Sayo UI 的方式

```bash
cp <sayo-ui>/sayo.css <sayo-ui>/sayo.js <sayo-ui>/LICENSE templates/assets/sayo/
cp -r <sayo-ui>/icons templates/assets/sayo/icons
```

`learn-theme.css`、`learn-theme.js`、`style.css`、`quiz.js`、`lesson-toc.js` 是自研文件，**不要**被上游覆盖。

## 新增共享文件时（容易漏）

共享层的清单分散在三处，新增/改名时必须同时改，否则页面会静默少加载一个文件：

1. `templates/assets/README.md`（本文件的表格与目录树）
2. `scripts/preview_templates.py` 里的 `shared_files` / `shared_dirs`
3. `docs/工程约束.md` 的「前端技术选型」与「目录与规则归属」（共享层那份清单）

## 谁在哪里落地

- **总控建科目**：只拷 `style.css`、`quiz.js`、`lesson-toc.js` 到 `<subject>/assets/`，别把 `sayo/` 再拷一遍
- **`gen_home.py`**：负责共享层（`sayo/` + `learn-theme.css/js`）就位，幂等；缺资源页面会退化成裸 HTML
