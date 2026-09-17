---
name: record-keeping
description: 档案维护规范：学习状态的读写规则（共享记忆、进度、误解、评估记录、会话摘要、学习记录、主页刷新、新建科目、项目与实验课）。由 learning-system 总控加载并自己执行。
---

# 档案维护规范

学习状态由你（主教练）亲自读写——信息源就在你上下文里，不派角色。路径都以 `LEARN_WORKSPACE`（开场从 `~/.dsh/studymate-config.yaml` 读到）为前缀：

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
        ├── lessons/ reference/ assets/    # 讲解角色产出（课件/速查/组件）
        ├── lab/                  # 题目角色给内容、你写盘：实操 + solutions/ + README.md；概念课没有
        ├── assessments/          # 评估记录（题目角色给内容、你写盘）
        ├── learning-records/     # 学习记录
        └── sessions/YYYY-MM-DD.md
```

## 共享记忆 MEMORY.md

按模板分节（我是谁 / 教学偏好 / 学习习惯 / 跨科目观察）增补与修正。只记跨科目、跨会话仍成立的东西；知识点细节留给该科目的 misconceptions。

## 科目文件夹

1. **新建**：建 `subjects/<slug>/` 与 `lessons/`、`reference/`、`assets/`、`learning-records/`、`sessions/`、`assessments/`；按 `templates/subject.yaml` 建 `subject.yaml`（`created_at` 填当天）；`assets/` 只从 `<root>/templates/assets/` 拷 `style.css`、`quiz.js`（共享层由 `gen_home.py` 负责）。**`lab/` 不预建**——只有 `kind: 实操/实验` 的节点才需要
2. **列出**：读 `subjects/*/subject.yaml`，汇总"科目名 + 状态 + 上次学习日期 + 当前节点"
3. **切换**：切换即换路径，不复制不搬运

## 学习记录（learning-records/）

记成 `NNNN-dash-case.md`（编号递增），作为下次教什么的依据。**写一条当且仅当出现可观察的证据**：学生正确用出了概念、主动说明已知某知识、误解被纠正。覆盖了但没证据的不记，纯进度日志不记。被更新的理解标 `Status: superseded by LR-NNNN`，不删除。

## 评估记录（assessments/）

`practice-evaluator` 交回题面、作答与结论，**由你写盘**：

1. 命名 `NNNN-<节点id>.md`（编号递增），存 `subjects/<slug>/assessments/`
2. `.md` 文件，**YAML frontmatter 承载 `assessment.schema.json` 的字段**（日期加引号），正文写题面与作答原文
3. 逐题的 `验收点` 要与 `curriculum.yaml` 节点的 `验收点` **逐字对得上**；对不上以节点为准并修正记录
4. 同时双落点记误解（`misconceptions.yaml` + `progress.yaml.misconceptions`）

## 项目与实验课

`progress.yaml` 的 `project` **只有一句"在做的是什么"**：

```yaml
project:
  current: "订单 API（本地可跑，逐步加到可部署）"
nodes:
  exp.crud-routes:            # id 来自 curriculum.yaml 里 kind: 实验 的节点
    status: 未开始
    mastery: 0
```

- 里程碑不在这里——它们就是 `kind: 实验` 的验收课节点，进度就在 `nodes` 里（课型见 `layered-practice` 第四节）
- **实验课通过时（硬规则）**：把该节点与它的 `prerequisites`（被验收节点）都置为「**已通过项目验证**」（mastery 保留或上调），再写一条学习记录（"实验通过：<标题>"）。这是"项目推进"的唯一依据，不要凭印象提前置、也不要漏置
- `current` 变了先跟学生确认；改完过 `schemas/progress.schema.json`

## 主页刷新

主页是生成产物（模板在 `<root>/templates/`，生成器 `<root>/scripts/gen_home.py`）：**刷新 = 跑 `python3 <root>/scripts/gen_home.py`**，覆盖旧文件、不改数据文件。时机：新建科目后、节点状态变化后、材料新增后、会话结束前。

## 读写规则（硬约束）

1. 写前先读现有内容，**增量修改**（不整文件覆盖，`MEMORY.md`/`subject.yaml` 的新建除外）
2. 写后校验：`curriculum.yaml`、`progress.yaml`、`subject.yaml`、评估记录 frontmatter 分别对照 `<root>/schemas/*.json`；会话摘要对照 `session-summary.schema.json`
3. **写入类型化的状态**：结构化事实进 YAML，偏好与观察进 `MEMORY.md`
4. **会话摘要**（会话结束时）：按 session-summary schema 生成，存 `subjects/<slug>/sessions/<YYYY-MM-DD>.md`（同日多段追加）；**YAML frontmatter 承载 schema 字段**（日期加引号），正文写本次要点；同时在对话里给一条 `memory_updates` 建议，学生确认后写进 `MEMORY.md`
5. **恢复视图**（开场自读）：`MEMORY.md` 相关分节 + 当前节点 + 前置节点摘要 + 最近 5 条 misconceptions + 最近 3 条学习记录 + 最近 3 条评估记录 + 实验课节点进度与 `project.current`。只读需要的部分（offset/limit/grep），不把长文件整份读进来

## 边界

- 课程内容归 `curriculum-designer`；课件/参考/组件归 `learning-coach`；**题目、lab 与实验说明页归 `practice-evaluator`（它给内容，你写盘）**。你只读写状态与元数据，发现不一致以文件为准并修正记录
- 档案存结构化摘要，聊天的原始过程留在会话里
- 科目之间隔离：只读当前科目，唯一的跨科目来源是 `MEMORY.md`
- 只在 `<LEARN_WORKSPACE>/` 下写学习文件，绝不写会话目录
