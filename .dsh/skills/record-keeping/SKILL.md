---
name: record-keeping
description: 档案维护规范：学习状态的读写规则（共享记忆、进度、误解、评估记录、会话摘要、学习记录、主页刷新、新建科目、项目与实验课）。由 learning-system 总控加载并自己执行。
---

# 档案维护规范

学习状态由你（主教练）亲自读写，不派角色。路径都以 `LEARN_WORKSPACE`（开场从 `~/.dsh/studymate-config.yaml` 读到）为前缀：

```
<LEARN_WORKSPACE>/
├── index.html                   # 根主页（生成产物）
└── .learning/
    ├── MEMORY.md                # 跨科目共享记忆
    └── subjects/<slug>/         # 每门科目独立
        ├── subject.yaml  MISSION.md  RESOURCES.md  GLOSSARY.md   # 四份元数据（你维护）
        ├── curriculum.yaml       # 课程设计角色产出
        ├── progress.yaml  misconceptions.yaml
        ├── index.html            # 科目主页（生成产物）
        ├── lessons/ reference/ assets/    # 课件三件（见下）、速查页、科目组件
        ├── lab/                  # 角色落 deliver/、你 cp 搬入：实操 + solutions/ + README.md；概念课没有
        ├── assessments/          # 评估记录（你撰写）
        ├── learning-records/     # 学习记录
        └── sessions/YYYY-MM-DD.md
```

## 共享记忆 MEMORY.md

按模板分节（我是谁 / 教学偏好 / 学习习惯 / 跨科目观察）增补与修正。只记跨科目、跨会话仍成立的东西；知识点细节留给该科目的 misconceptions。

## 科目文件夹

1. **新建**：建 `subjects/<slug>/` 与 `lessons/`、`reference/`、`assets/`、`learning-records/`、`sessions/`、`assessments/`；按 `templates/subject.yaml` 建 `subject.yaml`（`created_at` 填当天）；`assets/` 只从 `<root>/templates/assets/` 拷 `style.css`、`quiz.js`、`lesson-toc.js`（共享层由 `gen_home.py` 负责）。**`lab/` 不预建**——只有 `kind: 实操/实验` 的节点才需要。盘问时定下的**载体**先随派工 prompt 传给 `practice-evaluator`，等**首个实操/实验节点**建 `lab/` 时再落盘进 `lab/README.md`（那之前没有 `lab/` 不是漏了）
2. **列出**：读 `subjects/*/subject.yaml`，汇总"科目名 + 状态 + 上次学习日期 + 当前节点"
3. **切换**：切换即换路径，不复制不搬运
4. **共享组件更新后同步到已有科目**：`<root>/templates/assets/` 里的 `style.css`、`quiz.js`、`lesson-toc.js` 一改，各科目 `assets/` 里的同名副本就旧了（新科目是建课时拷的），要一起覆盖——科目自己新增的组件不动
5. **图片库是科目自己的**：`assets/img/pool/`（图片）与它的索引 `assets/img/pool.md` **不从 `<root>/templates/` 同步**（模板里根本没有），由 `image-scout` 建、由课件消费。**已引用的图不能删**：删之前先 `grep` 一遍 `lessons/` 与 `reference/`，还有页面指着它就留着；补图只增不删。命名与索引格式见 `image-scout`。图片库是**学习产物，随科目整体拷贝或迁移时跟着走**（`.venv` 那类本机工具链不进包，换机器重建）

## 课件三件与归属（`lessons/`）

一个节点的课件是**三件**——`<序号>-<节点id>.md`（内容）+ `<序号>-<节点id>.quiz.json`（题库）+ `<序号>-<节点id>.html`（渲染产物）——各有 owner，**别手改渲染产物**：

| 文件 | 谁写 | 里面是什么 |
|---|---|---|
| `.md`（内容） | 课件正文归 `learning-coach`（它直接写科目目录）；**`kind: 实验` 的说明页由你 `cp` 原样搬入** | 讲解、练习的引入、配图、题目位置（`::: quiz` 的锚点）；出题人交回的 `empty_reason:` 由你跑 `scripts/apply_empty_reasons.py` 打进去 |
| `.quiz.json`（题库） | `practice-evaluator` 出题落 `deliver/`、你 `cp` 搬入（**题面与答案一个字都不改**） | 键与内容文件的锚点逐字对应、对不上渲染器报错（结构见 `docs/课件内容格式.md` 第 4 节） |
| `.html`（渲染产物） | `python3 <root>/scripts/render_lesson.py <subject_path> <节点id>` | 学生看的页面；谁也不手改 |

- **改课件＝改源文件，再重渲**：内容改 `.md`、题目改 `.quiz.json`，然后重跑渲染器；直接改 `.html` 会在下次渲染时被冲掉，两份文件还会对不上
- **旧的手写课件并存**：`lessons/` 里已交付的 `.html` 不重渲、不搬家，检查照旧判它们（含题目位置残留那条）；新建的节点一律走三件——**`kind: 实验` 的说明页不出题，没有 `.quiz.json`，就是 `.md` + `.html` 两件**
- 渲染报 `<文件>:<行>` 的按归属打回：内容 → `learning-coach`，题库与锚点 → `practice-evaluator`

## 学习记录（learning-records/）

记成 `NNNN-dash-case.md`（编号递增），作为下次教什么的依据。**写一条当且仅当出现可观察的证据**：学生正确用出了概念、主动说明已知某知识、误解被纠正。覆盖了但没证据的不记，纯进度日志不记。被更新的理解标 `Status: superseded by LR-NNNN`，不删除。

## 评估记录（assessments/）

`practice-evaluator` 把评估记录落成 `deliver/assessments/NNNN-<节点id>.md`，**你 `cp` 搬入**（正文含题面与作答原文）：

1. 命名 `NNNN-<节点id>.md`（编号递增），存 `subjects/<slug>/assessments/`
2. `.md` 文件，**YAML frontmatter 承载 `assessment.schema.json` 的字段**（日期加引号），正文写题面与作答原文
3. 逐题的 `过关标准` 要与 `curriculum.yaml` 节点的 `过关标准` **逐字对得上**；对不上以节点为准并修正记录
4. 同时双落点记误解（`misconceptions.yaml` + `progress.yaml.misconceptions`）

## 项目与实验课

`progress.yaml` 的 `project` **只有一句"在做的是什么"**（`current`；schema 只要求这一个键）。**里程碑不在这里**——它们就是 `kind: 实验` 的验收课节点，进度就在 `nodes` 里（课型见 `layered-practice` 第四节）。

- **实验课通过时（硬规则）**：把该节点与它的 `prerequisites`（被验收节点）都置为「**已通过项目验证**」（mastery 保留或上调），再写一条学习记录（"实验通过：<标题>"）。这是"项目推进"的唯一依据，不要凭印象提前置、也不要漏置
- `current` 变了先跟学生确认；改完过 `schemas/progress.schema.json`

## 主页刷新

主页是生成产物（模板在 `<root>/templates/`）：**刷新 = 跑 `python3 <root>/scripts/gen_home.py`**（一次刷新根主页与所有科目主页），覆盖旧文件、不改数据文件。非零退出看 stderr——断链或某个科目数据读不出来，修完重跑。时机：新建科目后、节点状态变化后、材料新增后、会话结束前。

## 读写规则（硬约束）

1. 写前先读现有内容，**增量修改**（不整文件覆盖，`MEMORY.md`/`subject.yaml` 的新建除外）
2. 写后校验：`curriculum.yaml`、`progress.yaml`、`subject.yaml`、评估记录 frontmatter 分别对照 `<root>/schemas/*.json`；会话摘要对照 `session-summary.schema.json`
3. **写入类型化的状态**：结构化事实进 YAML，偏好与观察进 `MEMORY.md`
4. **会话摘要**（会话结束时）：按 session-summary schema 生成，存 `subjects/<slug>/sessions/<YYYY-MM-DD>.md`（同日多段追加）；**YAML frontmatter 承载 schema 字段**（日期加引号），正文写本次要点；同时在对话里给一条 `memory_updates` 建议，学生确认后写进 `MEMORY.md`
5. **恢复视图**（开场自读）：`MEMORY.md` 相关分节 + 当前节点 + 前置节点摘要 + 最近 5 条 misconceptions + 最近 3 条学习记录 + 最近 3 条评估记录 + 实验课节点进度与 `project.current`。只读需要的部分（offset/limit/grep），不把长文件整份读进来
6. **进度只认 `progress.yaml`**：`curriculum.yaml` 的每个节点也带 `status`/`mastery`（schema 要求），那是**建课时的初始快照**，建课后不再回头维护；运行期的状态只写 `progress.yaml`、也只读它——里面**只记有变化的节点**，没写的按大纲里的初始值算（`gen_home.py` 就是这么合并的）。两份文件都改是漂移的源头

## 边界

- 课程内容归 `curriculum-designer`，课件/题库/lab/页面的归属见上表与上面的目录树（题目、lab 与实验说明页由 `practice-evaluator` 落 `deliver/`、你 `cp` 搬入）。你只读写状态与元数据，发现不一致以文件为准并修正记录
- 档案存结构化摘要，聊天的原始过程留在会话里
- 科目之间隔离：只读当前科目，唯一的跨科目来源是 `MEMORY.md`
- 只在 `<LEARN_WORKSPACE>/` 下写学习文件，绝不写会话目录
