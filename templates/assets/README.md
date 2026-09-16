# templates/assets/ — 前端资源与引用契约

本目录是引擎项目里的**前端资源源**。学习工作区里的资源由 install.sh / gen_home.py / 总控（建科目时）
按下面的规则放置，页面按**固定相对路径**引用（模板里写死，生成器不改）。

## 目录职责

| 路径 | 是什么 | 谁维护 |
|------|--------|--------|
| `sayo/` | **Sayo UI**（自研零依赖 CSS 框架 + 交互引擎），MIT。含 `sayo.css`、`sayo.js`、`icons/`、`LICENSE` | 从 sayo-ui 项目整体拷贝，**不要手改** |
| `learn-theme.css` | 本项目**共享主题层**：亮色=暖纸白+深绿（覆盖 `--syo-*`）、暗色=用 Sayo 默认的 Primer 暗色；修正 Sayo 里为暗色硬编码的紫色光晕；放跨页面组件（进度条、状态徽标、筛选、空状态） | 本项目自研，改色只改这里 |
| `learn-theme.js` | **主题（亮/暗）共享逻辑**：早期应用、切换并持久化、绑定开关（`LearnTheme.apply/set/toggle/current/wire`）。三个页面共用，别各写一份 | 本项目自研 |
| `style.css` | **课件层**（讲解排版 + 练习样式），叠在 Sayo 之上 | 本项目自研；Task 8 拷进每个科目 |
| `quiz.js` | 课件交互组件（选择题即时反馈） | 同上 |

## 在工作区里的落地位置与引用路径

```text
<LEARN_WORKSPACE>/
├── index.html                                  # 根主页（生成产物）
└── .learning/
    ├── assets/                                 # ← 全工作区共享一份
    │   ├── sayo/{sayo.css,sayo.js,icons/,LICENSE}
    │   ├── learn-theme.css
    │   └── learn-theme.js
    └── subjects/<slug>/
        ├── index.html                          # 科目主页（生成产物）
        ├── assets/                             # ← 每个科目一份（Task 8 从 templates/assets/ 拷）
        │   ├── style.css
        │   └── quiz.js
        └── lessons/0001-xxx.html               # 课件
```

各页面**必须**按下面的相对路径引用（路径写死在模板/课件里）：

| 页面 | 引用共享层 | 引用本科目层 |
|------|-----------|-------------|
| 根主页 `<WS>/index.html` | `.learning/assets/sayo/sayo.css`<br>`.learning/assets/learn-theme.css`<br>`.learning/assets/learn-theme.js`<br>`.learning/assets/sayo/sayo.js` | — |
| 科目主页 `<WS>/.learning/subjects/<slug>/index.html` | `../../assets/sayo/sayo.css`<br>`../../assets/learn-theme.css`<br>`../../assets/learn-theme.js`<br>`../../assets/sayo/sayo.js` | `assets/style.css` |
| 课件 `<WS>/.learning/subjects/<slug>/lessons/NNNN-x.html`<br>（从 `templates/lesson.html` 拷起） | `../../../assets/sayo/sayo.css`<br>`../../../assets/learn-theme.css`<br>`../../../assets/learn-theme.js`<br>`../../../assets/sayo/sayo.js` | `../assets/style.css`<br>`../assets/quiz.js` |

> 路径提示：课件在 `.learning/subjects/<slug>/lessons/` 下，向上三层就是 `.learning/`，
> 所以共享层是 `../../../assets/…`（不要再写一层 `.learning`）；科目内组件则是 `../assets/…`。
>
> 为什么共享层只放一份：Sayo 有两个主题、体积 260KB+，每个科目各拷一份纯属浪费；
> 而 `style.css` / `quiz.js` 留在科目内，是因为 learning-coach 会往 `<subject>/assets/` 里
> 追加该科目专用的新组件（新题型、模拟器），科目自带的组件库要跟着科目走。

## 主题约定

- **亮色**：`<html data-theme="light">` → `learn-theme.css` 把 Sayo 令牌映射成暖纸白 + 深绿
- **暗色**：`<html data-theme="dark">` → 用 Sayo 自己的 Primer 暗色 + 紫强调（不覆盖）
- 切换：页面脚本改 `data-theme` 并写 `localStorage['le-theme']`；
  **不要**用 Sayo 的 `data-syo-theme` 属性，两套属性会打架
- 装饰性交互（自定义光标、光晕、拖尾、波纹）**默认不开**：不加 `body[data-syo-*]` 属性即可。
  目前只开：主页抬头的 `data-syo-parallax`、科目页课件目录的 `data-syo-inertia`

## 更新 Sayo UI 的方式

```bash
cp <sayo-ui>/sayo.css <sayo-ui>/sayo.js <sayo-ui>/LICENSE templates/assets/sayo/
cp -r <sayo-ui>/icons templates/assets/sayo/icons
```

`learn-theme.css`、`style.css`、`quiz.js` 是自研文件，**不要**被上游覆盖。

## 新增共享文件时（容易漏）

共享层的清单分散在三处，新增/改名时必须同时改，否则页面会静默少加载一个文件：

1. `templates/assets/README.md`（本文件的表格与目录树）
2. `scripts/preview_templates.py` 里的 `shared_files` / `shared_dirs`
3. `docs/实施计划.md` Global Constraints 的「前端技术选型」与 Task 13 的资源就位要求

## 跨任务提示

- **Task 11（install.sh）/ Task 13（gen_home.py）**：必须保证 `<WS>/.learning/assets/` 存在
  （把 `templates/assets/sayo/` 与 `templates/assets/learn-theme.css` 放进去）。生成器找不到资源时，
  页面会退化成无样式裸 HTML，所以这一步是硬要求，且要幂等。
- **Task 8（总控建科目）**：只拷 `style.css`、`quiz.js` 到 `<subject>/assets/`，
  不要把 `sayo/` 再拷一遍。
- **Task 5（learning-coach 写课件）**：先读 `<subject>/assets/` 与共享层已有的组件，复用而不是内联。
