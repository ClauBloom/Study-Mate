# StudyMate

基于 DSH 的长期自学 Agent：多科目各自管理、一份共享学习记忆、可视化课程大纲、人话讲解、四层练习、划词提问。

## 安装

```bash
./install.sh
# 做两件事：① 装"学习模式"预设到 ~/.dsh/.agent-presets/learning/（预设里写入引擎的 skill 目录）
#          ② 建学习工作区（默认 ./workspace/）并写入 ~/.dsh/studymate-config.yaml
```

## 使用

1. **在任意目录**启动 DSH 会话，选择"学习模式"预设（能力装在用户级，与会话目录无关）
2. 第一次：告诉总控你想学什么、当前基础、讲法偏好
3. 之后每次会话：总控读共享记忆、列出科目，你选一门继续或新开一门

## 题目与课型（v2）

**题只有一个 owner**：`practice-evaluator` 出全系统的题——题面、答案、算过标准、`lab/` 实操题（教程／留白任务／断言／`solutions/`）、实验课的验收任务。讲解角色（`learning-coach`）不写题，只把出题人给的题**原样**嵌进课件正文（位置与行文归它）。规范见 `.dsh/skills/layered-practice`（题目唯一规范）。

**四种题型**：

| 题型 | 长什么样 | 判分 |
|------|---------|------|
| 选择题 | 页内 `.quiz`，点选项即时反馈 + 一句解释 | 页内自动判 |
| 开放题 | 页内出题，**参考答案 + 算过标准点击展开**（不贴回会话） | 学生自评 |
| 实操题 | `lab/` 留白任务 + 断言 + `solutions/`，学生亲手写代码 | `npm test` 自动判 |
| 评估题 | 评估时现场出的 1-2 题（开放） | `practice-evaluator` 判 |

数据字段的唯一出处是 `templates/assets/quiz.js` 顶部注释（选择题 `q/opts/ans/why`；开放题 `q/answer/criteria`）。

**三种课型**（写在 `curriculum.yaml` 节点的 `kind` 里）：

| `kind` | 是什么 | 产出 |
|--------|--------|------|
| `概念` | 普通课，只讲不落 lab（题目止于 L3） | 课件（讲解 + 轻量跟做） |
| `实操` | 普通课，学一点练一点 | 课件 + 自己的小 lab |
| `实验` | **里程碑验收课**：与普通课同级插在大纲里，验收"学到目前的知识能做出什么" | 实验说明页（任务书）+ 验收任务 |

- 项目里程碑**就是** `kind: 实验` 的节点，`prerequisites` 列出它验收哪些课；通过后这些节点置「已通过项目验证」。
- `验收点`（原字段名 `evidence`）是节点的过关标准：学完凭什么算做到了。

**质量闸门**（总控在打开页面前跑）：

```bash
python3 scripts/check_lesson.py <页面路径> --subject <科目目录> --node <节点id>
# 阻断项：文件名与编号、共享层与科目组件引用、题目结构（每题 q／选择题 opts+ans+why／开放题 answer+criteria）、
#         题目位标记残留、主题开关；kind 为 实操/实验 时还要求 lab 链接与 lab 产物齐全
# 提示项（不阻断）：选项长度差、实操判定被跳过、概念课却链了 lab
```

## 状态放在哪（学习工作区）

- `workspace/.learning/MEMORY.md`：跨科目共享记忆（现有技能、水平、讲法偏好、学习习惯）
- `workspace/.learning/subjects/<科目>/`：每门科目的大纲（`curriculum.yaml`）、进度（`progress.yaml`）、误解、评估记录（`assessments/`）、会话摘要（`sessions/`）、学习记录（`learning-records/`）
- 每门科目的材料：`lessons/`（课件与实验说明页）、`lab/`（实操与 `solutions/`）、`reference/`（速查页）、`assets/`（组件库）
- `workspace/index.html`：课程总览主页（自动生成）
- 工作区位置记录在 `~/.dsh/studymate-config.yaml`，想换位置改这一个文件
- 换机器时整个项目（含 `workspace/`）拷走 + 跑安装脚本，进度不丢

## 目录结构（三个区域）

| 区域 | 位置 | 职责 |
|------|------|------|
| 引擎项目 | 本目录 | 系统源码：预设源、skill 源、schemas、templates、scripts、examples、docs |
| 用户级安装 | `~/.dsh/` | 学习模式预设（里面记录引擎项目的 skill 目录）、学习工作区配置（install.sh 写入） |
| 学习工作区 | `workspace/`（可配置） | 你的学习数据：共享记忆、科目、课件、实验、主页 |

## 文档

- `docs/设计方案.md`：产品设计（产品经理视角）
- `docs/实施计划.md`：实施任务清单；文末 `## 题目系统重构（v2）` 一节是**题目、课型、验收点、里程碑与闸门规则的当前口径**（覆盖计划里更早的快照）
