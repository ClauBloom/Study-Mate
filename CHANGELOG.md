# 更新日志

<!-- studymate-release:v0.1.4 -->
## [0.1.4](https://github.com/Miaotofu01/Study-Mate/releases/tag/v0.1.4) - 2026-09-23

### 已合并的 Pull Request

- Fix/dsh old host graceful degrade ([#7](https://github.com/Miaotofu01/Study-Mate/pull/7))

### 所有提交

- Update README to remove studymate commands ([14c44f1](https://github.com/Miaotofu01/Study-Mate/commit/14c44f144738ba83850d6bfa98338dc431a12881))

  > Removed installation and upgrade instructions for studymate.

- fix: let old DSH hosts skip native plugin loading ([fbf7399](https://github.com/Miaotofu01/Study-Mate/commit/fbf7399148d13fb7e9c62f4efcbde1af8dd24b11))
- test: cover graceful fallback on old DSH hosts ([c42e81c](https://github.com/Miaotofu01/Study-Mate/commit/c42e81c2d349c087c34539d6712467d349358406))
- Merge pull request \#7 from GodBlessRen/fix/dsh-old-host-graceful-degrade ([f839b93](https://github.com/Miaotofu01/Study-Mate/commit/f839b9359943b7eaa7115040d48110bfb8d19a24))

  > Fix/dsh old host graceful degrade

- docs(README):新增配图 ([263dd5f](https://github.com/Miaotofu01/Study-Mate/commit/263dd5f3585cd7dd4697a2c75f64faea84ec0e24))
- docs(README):新增配图 ([1f0953a](https://github.com/Miaotofu01/Study-Mate/commit/1f0953a366a665d99755ca44da8677efd504c73e))
- docs(README):新增配图 ([c9667b8](https://github.com/Miaotofu01/Study-Mate/commit/c9667b8dfe4c4343d497b659e9755798d99a9181))
- fix(lesson-design):优化课件提示词 ([7813fb1](https://github.com/Miaotofu01/Study-Mate/commit/7813fb136eee3221ab31d84c030592699a904e05))
- fix(layered-practice):优化课件提示词 ([9da9090](https://github.com/Miaotofu01/Study-Mate/commit/9da909011349f6f9c1ed538d7465995812745887))
- 添加项目交流群 ([dc53a7c](https://github.com/Miaotofu01/Study-Mate/commit/dc53a7c74b7b21ad262d20b6dcbe3c7049288008))
- fix: protect DSH downgrades and make installer migration explicit ([883829f](https://github.com/Miaotofu01/Study-Mate/commit/883829ffcb5a5d77cc08e43a769c8c823fcb06dc))
- 修复：调整 CI 临时目录变量的使用位置 ([ca9bec0](https://github.com/Miaotofu01/Study-Mate/commit/ca9bec070cc452136149a15ae9d474f6f8dbd111))

  > 将 DSH 测试路径从作业级环境变量移到对应测试步骤，避免 runner.temp 在工作流校验阶段不可用，恢复兼容性检查的执行。

- fix：Readme 安装引导 ([261f15f](https://github.com/Miaotofu01/Study-Mate/commit/261f15f9bc8640b6e153e04f9dbb5b0a5faa8aae))

  > Updated installation instructions and added emphasis on npm installation.

- fix(ci)：等待 DSH 预设检查的异步结果 ([8dcc4fa](https://github.com/Miaotofu01/Study-Mate/commit/8dcc4fa82d12930d3638f6010b39312d407c8416))

  > 为两处 inactiveRows 检查补充 await，兼容 DSH 0.1.6 的异步返回值及旧版同步返回值，修复发布流程中的测试失败。
  > 
  > 验证：DSH 0.1.6-alpha.2 的运行时和 CLI 测试 5 项通过；DSH 0.1.5-rc.2 的运行时测试 2 项通过。

- fix(发布)：纠正修复代码后的重试说明 ([d868364](https://github.com/Miaotofu01/Study-Mate/commit/d8683643e328693ab27b6933966506fba766d7b1))

  > 检查失败后若已有修复提交且尚未创建版本 tag，应从最新 main 新建发布；重跑旧任务不会包含新提交。已有版本 commit/tag 的任务仍重跑原任务，保留原版本的恢复机制。


[完整比较](https://github.com/Miaotofu01/Study-Mate/compare/v0.1.3...v0.1.4)
<!-- /studymate-release:v0.1.4 -->

<!-- studymate-release:v0.1.3 -->
## [0.1.3](https://github.com/Miaotofu01/Study-Mate/releases/tag/v0.1.3) - 2026-09-23

### 所有提交

- ci: 等待 npm 完成异步包处理再核验发布 ([0862d57](https://github.com/Miaotofu01/Study-Mate/commit/0862d57178b312026dea69af8146c5923e61b758))
- feat: 支持 DSH 原生插件安装与更新 ([476f566](https://github.com/Miaotofu01/Study-Mate/commit/476f566df5f140c124991edb818aae68d5217535))
- Update README with upgrade instructions and version info ([cf1e2dd](https://github.com/Miaotofu01/Study-Mate/commit/cf1e2ddc7a975d9d87e21ac069bb423f3fad65d3))

  > Added upgrade instructions and updated version information.


[完整比较](https://github.com/Miaotofu01/Study-Mate/compare/v0.1.2...v0.1.3)
<!-- /studymate-release:v0.1.3 -->

<!-- studymate-release:v0.1.2 -->
## [0.1.2](https://github.com/Miaotofu01/Study-Mate/releases/tag/v0.1.2) - 2026-09-23

### 已合并的 Pull Request

- 修复若干问题 ([#3](https://github.com/Miaotofu01/Study-Mate/pull/3))

### 所有提交

- 修复安装路径含单引号、方括号等字符时安装失败或配置损坏的问题。 修复重复安装时无法正确沿用带特殊字符工作区的问题。 修复主页漏扫文件、特殊字符链接失效和空大纲显示旧进度的问题。 修复学习目标悬停提示显示成节点标题的问题。 修复非法大纲导致校验崩溃、重复节点造成编号异常及依赖方向提示错误的问题。 修复题目属性误报、多个题目块漏检和异常题库导致渲染崩溃的问题。 修复图片目录被误放行、编码路径误报和绝对路径漏拦的问题。 修复异常题目中断后续练习、无效题目参与计分的问题。 修复题号和反馈前缀破坏代码围栏，以及 Windows 换行解析失败的问题。 修复代码高亮误判字符串、破坏原文及未知语言触发异常的问题。 修复平板侧栏无法展开，以及切换手机布局后上下课导航消失的问题。 修复无题理由回填破坏换行格式、写入失败可能损坏原文件的问题。 修复课件重编号临时文件冲突、失败回滚不完整及恢复提示错误的问题。 修复技能调用开关判断错误、异常元数据中断批量检查的问题。 修复图片池索引放行错误列数、无效日期及非法文件名的问题。 修复 Windows 无法自动打开预览页面的问题。 修正示例答案路径和错误类型声明，并同步示例前端资源。 ([d3ff025](https://github.com/Miaotofu01/Study-Mate/commit/d3ff025e6d12b49d1d5eb7d01d67ef5ca8c5db21))
- fix:修复 MAC 在运行 install.sh 时将紧邻的中文括号误读为变量名 ([fb6ffd0](https://github.com/Miaotofu01/Study-Mate/commit/fb6ffd0ed628bc1c3e00a6df1c6ea99cf984a26c))
- 增加 npm 安装方式 ([61fc675](https://github.com/Miaotofu01/Study-Mate/commit/61fc6759164fea73ee1123fdfd638e844f954c34))
- Merge pull request \#3 from guoweiyi/main ([c69a768](https://github.com/Miaotofu01/Study-Mate/commit/c69a768597e08a2b83fb6ed672849f9ca75e5e2a))

  > 修复若干问题

- docs: 新增待办清单,方便人工维护 ([c8cb604](https://github.com/Miaotofu01/Study-Mate/commit/c8cb604a9acba16b6762d1c390bda840a61f2faf))
- README:新增前言 ([8af8275](https://github.com/Miaotofu01/Study-Mate/commit/8af8275a6977216923e356abceda03148372cc4c))
- README:修改readme ([b7e662f](https://github.com/Miaotofu01/Study-Mate/commit/b7e662f446a5949028698bb54a287cb3f56d959c))
- fix(提示词): 按 issue \#5 的实测反馈改课件与采图规则 ([a4ecc2c](https://github.com/Miaotofu01/Study-Mate/commit/a4ecc2c82a674979ee18009c567a6ce3c1904ee4))

  > - curriculum-designer：第一个节点改成用具体材料/案例开场，不再先上全景图
  > - lesson-design：术语与配图两条改成可执行的要求
  > - learning-coach：用图前必须先打开图片核对图注；补 SVG 不许写死宽度、字号下限
  > - image-scout：交稿前跑 check\_pool.py 并改到没有为止；主题词以 GLOSSARY.md 为准
  > - learning-system：开课先写 GLOSSARY.md 的「待掌握」，采图与课件共用同一套词
  > 
  > Refs \#5

- 修改:测试文件 ([84f3af7](https://github.com/Miaotofu01/Study-Mate/commit/84f3af7cea35ed83165d449728b196c2468063d6))
- fix(提示词): 第一课禁用学科定义/发展史/本课结构 ([632b441](https://github.com/Miaotofu01/Study-Mate/commit/632b441b28d78102965e93fff4f18919ec4d4d2b))
- feat(校验): check\_curriculum 报依赖位次倒挂 ([93d7923](https://github.com/Miaotofu01/Study-Mate/commit/93d7923182e95e111df3e8d994f8bb0c18fd9ff6))

  > 示例科目 typescript-web-api 现有一处倒挂（exp.pg-and-tests 依赖 test.api），本次未修。

- docs(README): 加 Star 趋势图 ([c79f2cd](https://github.com/Miaotofu01/Study-Mate/commit/c79f2cdd84739f44fc01e49ad68e01c237f61c28))
- fix: 兼容 DSH 新版预设与工作流插件 ([cb9e448](https://github.com/Miaotofu01/Study-Mate/commit/cb9e448d12a4de43cef4cfeef5412ef14ee33a25))

  > 分别适配 0.1.6 工作流更名和 0.1.7 声明式预设，保留旧版安装方式及用户配置。Refs \#4

- ci: 自动生成发布日志并发布 npm 包 ([88be504](https://github.com/Miaotofu01/Study-Mate/commit/88be504a3eb992daf1f1cffbc8851380256aed00))

  > 手动选择版本增量，经三平台检查后整理合并 PR 和全部提交，更新 CHANGELOG、版本标签和 GitHub Release，通过 npm OIDC 发布。

- test: 兼容 Windows 临时目录的短路径表示 ([0da4ca7](https://github.com/Miaotofu01/Study-Mate/commit/0da4ca7a8c5af38daef0d37571e0d7a1fb720b98))
- fix: 绕过 Node 22 在 Windows 复制中文目录时的崩溃 ([c4b2613](https://github.com/Miaotofu01/Study-Mate/commit/c4b2613116a5dc46c9796426749792f15501a42f))

[完整比较](https://github.com/Miaotofu01/Study-Mate/compare/v0.1...v0.1.2)
<!-- /studymate-release:v0.1.2 -->

## v0.1 — 首个可交付版本（2026-09-21）

- **学习模式预设 + 11 个技能**：1 个总控、5 个角色（找资料／采图／课程设计／讲解／出题评估）、5 份规范；配套大纲、进度、评估、会话摘要、科目五份数据结构。
- **三件套页面**：课程总览页、科目主页（大纲路线图）、课件页，共用一套主题（默认暗色，右上角可切）。课件由「内容文件 + 题库」渲染产出，四道校验（大纲／课件／图片库／技能）把关。
- **一条命令安装**：macOS/Linux 跑 `./install.sh`，Windows 跑 `.\install.ps1`——装预设、建学习工作区、写好配置。
- **13 套回归测试**：钉住渲染、题目、命名与上下节课指针、图片库、提示词规则与两个前端组件。
