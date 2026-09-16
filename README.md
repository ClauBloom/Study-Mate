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

## 状态放在哪（学习工作区）

- `workspace/.learning/MEMORY.md`：跨科目共享记忆（现有技能、水平、讲法偏好、学习习惯）
- `workspace/.learning/subjects/<科目>/`：每门科目的大纲、进度、误解、会话摘要、课件
- `workspace/index.html`：课程总览主页（自动生成）
- 工作区位置记录在 `~/.dsh/studymate-config.yaml`，想换位置改这一个文件
- 换机器时整个项目（含 `workspace/`）拷走 + 跑安装脚本，进度不丢

## 目录结构（三个区域）

| 区域 | 位置 | 职责 |
|------|------|------|
| 引擎项目 | 本目录 | 系统源码：预设源、skill 源、schemas、templates、scripts、examples、docs |
| 用户级安装 | `~/.dsh/` | 学习模式预设（里面记录引擎项目的 skill 目录）、学习工作区配置（install.sh 写入） |
| 学习工作区 | `workspace/`（可配置） | 你的学习数据：共享记忆、科目、课件、主页 |

## 文档

- `docs/设计方案.md`：产品设计（产品经理视角）
- `docs/实施计划.md`：实施任务清单
