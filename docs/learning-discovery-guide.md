# 学习方向探索：开发分支使用指南

适用于 `learning-direction-exploration` 分支。这个功能帮助你先选学习方向，再接回 StudyMate 原有的建课和上课流程。

源码在 [你的 GitHub fork](https://github.com/lyk05212007/Study-Mate/tree/learning-direction-exploration)。本机已有 `E:\Study-Mate\Study-Mate-src`，可以直接从下一节开始。换一台机器时，先安装 Git、配置 GitHub SSH 密钥，在你选好的父目录克隆：

```powershell
git clone --branch learning-direction-exploration git@github.com:lyk05212007/Study-Mate.git Study-Mate
```

若网络不通 SSH 的 22 端口，可**改用**下面这条；它仅对本次命令使用 SSH 443，不修改全局配置：

```powershell
git -c core.sshCommand='ssh -p 443 -o Hostname=ssh.github.com' clone --branch learning-direction-exploration git@github.com:lyk05212007/Study-Mate.git Study-Mate
```

两条克隆命令任选一条。其他机器执行下文时，把源码目录改成实际克隆位置，试用目录也换成自己的路径。

## 1. 在 Windows 试用当前源码

准备 Node.js 22.19+（22 系列）或 24+、DSH 0.1.5-rc.2 或更新版本、Python 3.9+ 和 PyYAML。DSH 还需要可用的模型配置；使用新版 DSH 时，请按它的要求准备 `pnpm`。先在 PowerShell 检查：

```powershell
node --version
dsh --version
pnpm --version
py -3 -c "import sys, yaml; print(sys.version); print(yaml.__version__)"
```

如果没有 `py`，用本机的 `python` 替代。缺少 PyYAML 时，用对应解释器安装：`py -3 -m pip install PyYAML`。没有 DSH 时，可运行 `npm install -g @deepseek-ai/dsh@latest` 安装提供 `dsh` 命令的[官方 CLI 包](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/package.json)；缺少 `pnpm` 时运行 `npm install -g pnpm`。安装完成后重新检查命令能否运行。模型和界面配置可查 [DSH 官方指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/index.zh.md)，StudyMate 安装背景见 [安装说明](安装.md)。

**本功能尚在开发分支；试用时运行下面的本地安装器。** `npx @yunmiao/studymate@latest install` 和 `dsh plugin add @yunmiao/studymate` 使用已发布的包，不能保证包含这里的修改。若已有原生 StudyMate 插件，它在 DSH 启动时可能重新安装自己的版本，覆盖刚安装的本地技能。因此下面使用独立的 DSH 配置目录和学习工作区，避免与现有学习环境混用。

在一个新的 PowerShell 窗口运行；路径可改成你自己的**独立试用目录**：

```powershell
Set-Location 'E:\Study-Mate\Study-Mate-src'
git branch --show-current
Test-Path '.\.dsh\skills\learning-discovery\SKILL.md'
```

应看到分支 `learning-direction-exploration` 和 `True`。然后运行：

```powershell
$env:DSH_HOME = 'E:\Study-Mate\discovery-dsh'
$env:LEARN_WORKSPACE = 'E:\Study-Mate\discovery-workspace'
node .\bin\studymate.mjs install --profile web --workspace $env:LEARN_WORKSPACE
if ($LASTEXITCODE -ne 0) { throw '安装未完成，请先处理上方错误。' }
dsh web
```

安装器把**当前本地源码**的技能复制到 `E:\Study-Mate\discovery-dsh\studymate\engine`，并生成适合 Windows 的命令与路径。它会创建配置及空学习目录；这属于安装准备，不代表已经建课。这里无需运行 `npm install`，也无需构建 StudyMate。

首次使用这个独立 DSH 环境时，按 DSH 界面提示完成模型配置。打开它给出的网页，新建会话，选择「学习模式」。若另一个 DSH 已占用启动端口，先停止那个服务，再在此窗口重试。

日后启动试用环境，在同一个 PowerShell 窗口先设置上述两个环境变量，再运行 `dsh web`。本地源码更新后，停止试用 DSH，重新执行本地安装命令，然后重启并新建会话。安装器使用源码的副本，单纯修改仓库不会自动更新已安装技能。关闭此窗口后，这两项环境变量设置不会继续影响新开的终端。

## 2. 开始探索

在「学习模式」里直接发送：

> 我不知道学什么，帮我选一个学习方向。

也可以一次告诉它已知条件，减少重复提问：

> 我是零基础，想做一个能整理日常信息的小工具。每周大概有三小时，电脑是 Windows。我喜欢先看例子，但还不知道该学哪个方向，帮我探索一下。

主教练会一次问一个问题，通常围绕目标、兴趣活动、基础、时间和本次讲法偏好。选项没有标准答案，你可以自由补充。它会复用你已经说过的信息，以及当前工作区中允许读取的共享记忆；独立试用工作区不会自动继承旧工作区的记忆。

默认五问后给阶段建议，信息够用时可更早；只有需要区分候选时才补问，每轮最多八个实质问题，追问和跳过的题也计数。信息不足时会保留未知项，不应猜测你的答案。

## 3. 随时调整或停止

| 你可以这样说 | 接下来会怎样 |
|---|---|
| 「不确定」 | 该项保留为未知，继续必要问题 |
| 「跳过本题」 | 本题仍计数，略过它再继续 |
| 「先给建议」 | 立即停止追问，给暂定方向和待确认点 |
| 「跳过整个探索」 | 返回科目选择或已有信息对应的原流程，不替你建课 |
| 「今天到这」或「退出对话」 | 简短收尾，不继续问，也不强行输出报告 |
| 「我想更深入地探索」 | 明确进入追加探索，复用旧答案；追加轮仍有五问阶段建议和八问上限 |
| 「比较这两个方向」或「我想修改刚才的答案」 | 比较或修正现有候选，不自动启动另一轮问卷 |

最好明确说「跳过本题」或「跳过整个探索」，以免还需确认跳过范围。

## 4. 从建议进入第一课

阶段建议通常有二至三个候选，说明能做什么、哪些回答支持这个建议、基础与未知项、必要先修，以及简短学习路径。七个入口可交叉组合：应用开发与自动化、数据分析与数据工程、机器学习与 AI 原理、系统与性能、图形与游戏、嵌入式与机器人、数学。零基础通常意味着补先修，不会因此直接排除你感兴趣的方向。

你可以直接说：

> 我选应用开发与自动化，先做一个自己的小工具。

主教练会明确提示「进入开课准备」，复用探索答案，只补建课需要的目标深度、具体基础、配套项目和实验载体等缺项。开课准备沿用原流程的完成条件，不受探索八问上限代替，也不应继续扩大方向问卷。

这时有两个需要你确认的节点：

1. **确认建课信息。** 选方向只是选择目标，项目、载体等仍可调整；确认之后才建立科目并设计正式课程大纲。
2. **确认开始首课。** 主教练展示第一课安排并问「开始吗」，你同意后才开始教学和相应进度更新。

如果还没决定，可以说「先不建课，我再想想」。探索中的路径只是概览，不是已经生成的正式课程。

## 5. 已知道学什么时

直接发送「我想学 Python」或「继续上次的线性代数」，会进入原有的新科目或恢复学习流程，不必先做方向探索。宽泛的科目名称也不会被当作自动同意探索。

入口在学习对话中；本地 HTML 主页用于查看学习内容，不会因点击某个方向自动启动代理。

## 6. 数据边界与当前限制

确认建课前，探索只维护会话中的答案：不创建科目、不写独立探索档案或 `MEMORY.md`、不改学习进度与掌握度，也不做知识测验。DSH 本身可能保存对话历史，这不等于 StudyMate 建立了学习档案。需要保存到共享记忆的信息，仍按原规则另行确认；自述与暂定建议不自动成为能力证据。

本功能已完成静态规则检查和人工场景走读，也做过一次隔离模型采样；**真实 DSH 的完整多轮对话、确认前运行时无学习写入，以及建课至首课的完整流程仍待验证**。编写本指南时，当前机器的 PATH 中尚未找到可运行的 `dsh`；安装说明基于当前源码核对，尚未实际配置并启动你的试用环境。若发现第九问、退出后继续追问或确认前创建学习文件，请保留对话片段和相关文件变化，用于反馈。

具体检查范围见 [验收记录](learning-discovery-validation.md)，日常学习操作见 [使用说明](使用说明.md)。
