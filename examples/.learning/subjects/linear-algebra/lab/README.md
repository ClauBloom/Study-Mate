# 实操：0003-system-elimination

对应节点 `system.elimination`（课件 0003，`kind: 实操`）。
把第 3 课讲的消元写成能跑的代码：**自己实现「化成最简行阶梯形」与「判断解的结构」**，
不调用任何现成的线性代数库。

项目线索：这是这门课第一个能反复用的小工具——第 4 课数主元求基、第 5 课解 `(A − λI)v = 0`，
用的都是这两个函数。

## 载体

**源码 + 测试**：`0003-system-elimination/` 里是一份 `gauss.py` 加一份 `test_gauss.py`，
用 Python 自带的 unittest 跑，**只用标准库，不装任何第三方包**。

| 文件 | 是什么 |
| --- | --- |
| `0003-system-elimination/gauss.py` | 你要读和写的源码：四处 `▸ 你的任务` 留白，其余是说明与约定 |
| `0003-system-elimination/test_gauss.py` | 自检脚本：2 条教程断言通过，四个任务函数报错——整份测试现在是**红的** |
| `solutions/0003-system-elimination/gauss.py` | 参考解（做完再对照，别提前看） |
| `solutions/0003-system-elimination/test_gauss.py` | 与任务目录同一份自检，在参考解上跑，22 条全绿 |

任务文件与答案分成两个目录：`solutions/` 是一份**完整的对照副本**，拷过去就能直接跑。

## 环境

- Python **3.8 或更高**（本机 3.11 / 3.12 都跑过）：只用 `unittest` 与 `fractions` 两个标准库模块。
- 不需要网络、不需要 `pip install`，也不需要 numpy。这一点是刻意的：先亲手把消元写一遍，
  以后调 `numpy.linalg.solve` 时才知道它在替你做什么。
- 版本差异提示：`_pivots` 这类私有工具函数是本 lab 自己定的，与 SymPy 的 `rref()` 返回值
  （`矩阵, 主元列` 二元组）不是一回事，别混着记。

## 怎么跑

```bash
# 先进入本文件所在的 lab 目录，然后：
cd 0003-system-elimination
python3 -m unittest -v
```

交付状态下应该看到：**2 条通过、20 条报 `NotImplementedError`，`FAILED (errors=20)`（退出码 1）**。
这就是起点：教程那两条让你先看清断言长什么样、要交的结果是什么形状，剩下的红条就是待办清单。

对照参考解（同一份测试，跑在完整实现上）：

```bash
cd ../solutions/0003-system-elimination
python3 -m unittest -v      # 22 条全过，OK（退出码 0）
```

## 要交的东西（结果的结构）

`solve(A, b)` 返回一个 dict，三种解各带哪些键：

| `kind` | 含义 | 还要带什么 |
| --- | --- | --- |
| `unique` | 唯一解 | `solution`：按未知量顺序排的解 |
| `none` | 无解（出现矛盾行） | —（不要带 `solution` 键） |
| `infinite` | 无穷多解 | `particular`（自由变量全取 0 的特解）、`null_basis`（零空间的一组基）、`free_count` |

数字用 `fractions.Fraction`，不要用 `float` 做相等比较——`1/3` 在浮点里是 `0.333...`，
`rref` 里一次除法就会带进误差。

## 教程部分（已完成，跑一遍就能看见结果）

`test_gauss.py` 里的 `TestTutorial` 两条断言演示了夹具怎么拼增广矩阵：`augment(A, b)` 把 b 并到
每一行末尾，行数不一致时抛 `ValueError`。你后面所有调试都会用到这个形状。

## ▸ 你的任务

一次只做一个：实现一个函数 → 跑一次 `python3 -m unittest -v` → 看对应的那几条从 error 转绿。
四个函数全做完之后，22 条应当全过（退出码 0）。

| # | 函数 | 做什么 | 算过的标准（测试转绿） |
| --- | --- | --- | --- |
| 1 | `rref(A)` | 化成最简行阶梯形：主元为 1、主元列其余为 0、主元逐行右移、全零行垫底 | `TestRref` 6 条（含「不改入参」「`rref([])` 返回 `[]`」） |
| 2 | `pivot_columns(A)` | 给出主元所在列的下标（升序） | `TestHelpersAndErrors` 的 2 条 |
| 3 | `rank(A)` | 主元的个数 | `TestHelpersAndErrors` 的 1 条（秩 2 / 1 / 0 各一例） |
| 4 | `solve(A, b)` | 三种解的结构 + 行数不一致、空矩阵、空行三个错误分支 | `TestUniqueSolution` 3 条、`TestNoSolutionAndInfinite` 5 条、`TestHelpersAndErrors` 3 条 |

卡住了按这个顺序来：**先读断言的报错原文**（`AssertionError` 会把期望与实际并排打出来）→
再看函数 docstring 里的「边界」那几行 → 还不行就把报错原文贴回会话。
我不直接给答案，会先问你哪一行不对。

## 做完之后

回课件答那三道题，然后接着上 `space.basis`（基、维数与坐标）——下一课数主元的方式，
就是你这个 `pivot_columns` 已经在做的事。
