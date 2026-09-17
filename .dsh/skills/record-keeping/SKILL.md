---
name: record-keeping
description: 档案维护规范：学习状态的读写规则（共享记忆、进度、误解、评估记录、会话摘要、学习记录、主页刷新、新建科目、项目里程碑）。由 learning-system 总控加载并自己执行。
---

# 档案维护规范

长期学习状态由你（主教练）亲自读写——这些内容的信息源就在你的上下文里，不派角色。**所有路径都基于学习工作区**（`LEARN_WORKSPACE`，从 `~/.dsh/studymate-config.yaml` 读取；不在会话目录里找学习文件）。状态分两级：

```
<LEARN_WORKSPACE>/
├── index.html                   # 根主页（生成产物）
└── .learning/
    ├── MEMORY.md                # 跨科目共享记忆（弱约束）
    └── subjects/<slug>/         # 每门科目独立
        ├── subject.yaml  MISSION.md  RESOURCES.md  GLOSSARY.md   # 四份元数据（也由你维护）
        ├── curriculum.yaml       # 课程设计角色产出
        ├── progress.yaml
        ├── misconceptions.yaml
        ├── index.html            # 科目主页（生成产物，见"主页刷新"）
        ├── lessons/ reference/ assets/    # 讲解角色产出（课件/速查/组件）
        ├── lab/                  # 题目角色产出（practice-evaluator 给内容、你写盘）：实操 + solutions/ + README.md（环境与验证方式）；概念课没有这个目录
        ├── assessments/          # 评估记录（题目角色给内容、你写盘；见下）
        ├── learning-records/     # 学习记录（见下）
        └── sessions/YYYY-MM-DD.md
```

## 工作区定位（每次操作前）

1. 读 `~/.dsh/studymate-config.yaml` 拿 `workspace` 路径 → 记为 `LEARN_WORKSPACE`
2. 后续所有读写的绝对路径都以它为前缀；`templates/`、`schemas/` 在引擎项目 `<root>/`
3. 配置缺失时提示学生"请先运行 install.sh"，不猜测路径

## 共享记忆 MEMORY.md

- **读**：会话开场读，取与当前任务相关的部分（讲法偏好、水平、卡点）
- **写**：按模板分节（我是谁 / 教学偏好 / 学习习惯 / 跨科目观察）增补与修正
- 只记跨科目、跨会话仍然成立的东西；具体知识点细节留给该科目的 misconceptions

## 科目文件夹操作

1. **新建科目**：建 `<LEARN_WORKSPACE>/.learning/subjects/<slug>/` 与空目录（`lessons/`、`reference/`、`assets/`、`learning-records/`、`sessions/`、`assessments/`）；按 `templates/subject.yaml` 建 `subject.yaml`（`created_at` 填当天）；`assets/` 从 `<root>/templates/assets/` 只拷 `style.css`、`quiz.js` 两个起步组件（共享层由 `gen_home.py` 负责）。**`lab/` 不预建**：只有实操课（挂了项目里程碑的节点）才有 `lab/`
2. **列出科目**：读 `subjects/*/subject.yaml`，汇总"科目名 + 状态 + 上次学习日期 + 当前节点"
3. **切换科目**：切换即换路径，不复制、不搬运内容

## 学习记录（learning-records/）

记成 `NNNN-dash-case.md`（编号递增，扫描现有最大号 +1），作为下次教什么的依据。**写一条当且仅当出现可观察的证据**：学生正确用出了概念、主动说明已知某知识、误解被纠正。覆盖了但没证据的不记；纯进度日志不记。被更新的理解用 `Status: superseded by LR-NNNN` 标记，不删除。

## 评估记录（assessments/）

`practice-evaluator` 交回题面、作答与结论，**由你写盘**（它不写文件）：

1. 命名 `NNNN-<节点id>.md`（编号递增，扫描现有最大号 +1），存 `subjects/<slug>/assessments/`
2. 格式：`.md` 文件，**YAML frontmatter 承载 `assessment.schema.json` 的字段**（日期加引号：`node`／`date`／`layer`／`questions[]`／`mastery`／`verdict`／`next`／`misconceptions`），正文写题面与学生作答原文
3. 逐题的 `验收点` 字段要与 `curriculum.yaml` 节点的 `验收点` **逐字对得上**；对不上就以节点为准并修正记录
4. 与此同时照旧双落点记误解（`misconceptions.yaml` + `progress.yaml.misconceptions`）

## 项目里程碑（progress.yaml 的 `project`）

结构是**对象数组**，不是字符串数组：

```yaml
project:
  current: "订单 API（本地可跑，逐步加到可部署）"
  milestones:
    - text: "能跑通 3 条 CRUD 路由"
      nodes: [http.routing]        # 实现这个路标的节点 id，至少一个
      done: false
```

- **实操归属**：节点出现在某个里程碑的 `nodes` 里 → 该节点是**实操课**（配 `lab/`、题目可到 L4）；否则是概念课（题目止于 L3、没有 lab）
- **翻牌规则（硬）**：某个里程碑的 `nodes` 里的节点**全部**达到"能独立应用"及以上（含"已通过项目验证"）时，把它 `done: true`，并写一条学习记录（"里程碑达成：<text>"）。不要凭印象提前翻，也不要漏翻——`done` 是主页卡片与"要不要调路线"的依据
- `current` 变了要先跟学生确认；每次改完对照 `schemas/progress.schema.json` 校验

## 主页刷新（生成产物）

主页不是手维护的文件，是跑脚本重新生成的产物（模板在 `<root>/templates/`，生成器 `<root>/scripts/gen_home.py`）：

1. **科目主页** `subjects/<slug>/index.html`：数据源 `curriculum.yaml` + `progress.yaml` + `lessons/` + `reference/` 等
2. **根主页** `<LEARN_WORKSPACE>/index.html`：数据源 `subjects/*/subject.yaml` + `progress.yaml`
3. **刷新时机**：新建科目后、节点状态变化后、课件新增后、会话结束前
4. 刷新 = 跑 `python3 <root>/scripts/gen_home.py`（覆盖旧文件），不改动数据文件

## 读写规则（硬约束）

1. 写之前先读现有内容，**做增量修改**（不整文件覆盖，`MEMORY.md`/`subject.yaml` 的新建除外）
2. 写后校验：`curriculum.yaml`、`progress.yaml`、`subject.yaml`、评估记录 frontmatter 分别对照 `<root>/schemas/*.json`；会话摘要对照 `session-summary.schema.json`
3. **写入类型化的状态**：结构化事实进 YAML，偏好与观察进 `MEMORY.md`
4. **会话摘要**（会话结束时写）：按 session-summary schema 生成，存 `subjects/<slug>/sessions/<YYYY-MM-DD>.md`，同日多段追加；格式：`.md` 文件，**YAML frontmatter 承载 `session-summary.schema.json` 的字段**（日期加引号），正文写本次要点；写的同时在对话里给出一条 `memory_updates` 建议（哪些观察值得进共享记忆），学生确认后写进 `MEMORY.md`
5. **恢复视图**（开场时自读）：`MEMORY.md` 相关分节 + 该科目当前节点 + 前置节点摘要 + 最近 5 条 misconceptions + 最近 3 条学习记录 + **最近 3 条评估记录** + 项目里程碑（每个路标的 `done` 与未达成路标）；只读需要的部分（用 offset/limit/grep 取最近条目），不把整份长文件读进上下文

## 边界

- 课程内容归 `curriculum-designer`；课件/参考/组件归 `learning-coach`；**题目与 lab 归 `practice-evaluator`（它给内容，你写盘）**；你只读写状态与元数据，发现不一致时以文件为准并修正记录
- 档案里存结构化摘要，聊天的原始过程留在会话里
- 科目之间保持隔离：只读当前科目，唯一的跨科目来源是 `MEMORY.md`
- 只在 `<LEARN_WORKSPACE>/` 下写学习文件，绝不写会话目录
