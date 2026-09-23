---
title: 高斯消元与解的结构
goal: 能手写消元把线性方程组解出来，并判断解的存在性与自由度。
---

## 一行报错引出的问题

你在写一个小脚本，要把一次实验里五组测量拟合成三个参数的模型，于是有了三个未知量、五个方程的
超定方程组。标准库里没有 `solve`，你打算自己消元；写到一半，屏幕上跳出一句：

```text
ValueError: 这个方程组没有唯一解：要么无解，要么有无穷多解
```

这句报错就是本课要回答的问题：只看消元的结果，怎么知道它属于哪一种？

## 术语：消元的来历

「高斯消元」这个名字挂在高斯名下，但方法本身比他早两千年：《九章算术》的方程章里就有「遍乘直除」
的算法，用行与行相减来解出未知量；欧洲在 17 世纪由莱布尼茨、18 世纪由高斯在测量数据的最小二乘
计算中系统使用，19 世纪的教科书把它整理成今天的样子，于是用了高斯的名字。

「消元」二字说的是动作：把未知量一个一个消掉，直到某一行只剩一个未知量。手的动作很简单——
**方程两边同乘一个非零数、两个方程相减、交换两个方程的位置**，这三件事都不会改变方程组的解集。
把未知量的名字藏起来，只抄系数，就得到**增广矩阵**（augmented matrix）：系数与等号右边的常数
并排写在同一个数表里，消元时两边一起变，不用每步重抄。

$$
\begin{array}{ccc}
\text{方程} & & \text{增广矩阵} \\[4pt]
\begin{aligned}
2x + y + z &= 9 \\
x + 3y + 2z &= 10 \\
x + y - z &= 2
\end{aligned}
& \quad &
\left[\begin{array}{ccc|c} 2 & 1 & 1 & 9 \\ 1 & 3 & 2 & 10 \\ 1 & 1 & -1 & 2 \end{array}\right]
\end{array}
$$

## 手写一遍消元

拿上面这个方程组走一遍，每一步只做一件事。先交换第 1、3 行，让首位变成 1，再把第一列消干净：

$$
\begin{aligned}
& \xrightarrow{\ \text{第 1、3 行交换}\ } & \left[\begin{array}{ccc|c} 1 & 1 & -1 & 2 \\ 1 & 3 & 2 & 10 \\ 2 & 1 & 1 & 9 \end{array}\right] \\[8pt]
& \xrightarrow{\ \text{第 2 行} - \text{第 1 行}\ } & \left[\begin{array}{ccc|c} 1 & 1 & -1 & 2 \\ 0 & 2 & 3 & 8 \\ 2 & 1 & 1 & 9 \end{array}\right] \\[8pt]
& \xrightarrow{\ \text{第 3 行} - 2 \times \text{第 1 行}\ } & \left[\begin{array}{ccc|c} 1 & 1 & -1 & 2 \\ 0 & 2 & 3 & 8 \\ 0 & -1 & 3 & 5 \end{array}\right]
\end{aligned}
$$

接着处理第二列：把第 2 行化成 1，第 3 行除以 5，再用它们把这一列的 3、1.5 消掉，第三行就只剩
一个未知量了。

$$
\begin{aligned}
& \xrightarrow{\ \text{第 2 行} \div 2\ } & \left[\begin{array}{ccc|c} 1 & 1 & -1 & 2 \\ 0 & 1 & 1.5 & 4 \\ 0 & 0 & 1 & 2 \end{array}\right] \\[8pt]
& \xrightarrow{\ \text{第 3 行} \times 3\ } & \left[\begin{array}{ccc|c} 1 & 1 & -1 & 2 \\ 0 & 1 & 1.5 & 4 \\ 0 & 0 & 1.5 & 3 \end{array}\right] \\[8pt]
& \xrightarrow{\ \text{第 2 行} - \text{第 3 行}\ } & \left[\begin{array}{ccc|c} 1 & 1 & -1 & 2 \\ 0 & 1 & 1 & 3 \\ 0 & 0 & 1.5 & 3 \end{array}\right] \\[8pt]
& \xrightarrow{\ \text{第 3 行} \div 3\ } & \left[\begin{array}{ccc|c} 1 & 1 & -1 & 2 \\ 0 & 1 & 1 & 3 \\ 0 & 0 & 1 & 2 \end{array}\right]
\end{aligned}
$$

最后把上面两行里的 z 也消掉，就得到**最简行阶梯形**（reduced row echelon form，缩写 rref）：

$$
\begin{aligned}
& \xrightarrow{\ \text{第 2 行} - \text{第 3 行}\ } & \left[\begin{array}{ccc|c} 1 & 1 & -1 & 2 \\ 0 & 1 & 1 & 3 \\ 0 & 0 & 1 & 2 \end{array}\right] \\[8pt]
& \xrightarrow{\ \text{第 1 行} + \text{第 3 行}\ } & \left[\begin{array}{ccc|c} 1 & 1 & 0 & 4 \\ 0 & 1 & 0 & 1 \\ 0 & 0 & 1 & 2 \end{array}\right] \\[8pt]
& \xrightarrow{\ \text{第 1 行} - \text{第 2 行}\ } & \left[\begin{array}{ccc|c} 1 & 0 & 0 & 3 \\ 0 & 1 & 0 & 1 \\ 0 & 0 & 1 & 2 \end{array}\right]
\end{aligned}
$$

它有两个特征：每个主元都是 1，且主元所在列的其他位置全是 0。答案直接读出来，一行一个：$x = 3$，
$y = 1$，$z = 2$。代回原来的方程组验证：$6 + 1 + 2 = 9$、$3 + 3 + 4 = 10$、$3 + 1 - 2 = 2$，
与右端项一致。

::: svg
alt: 行阶梯形的形状，主元下方全为零
caption: 行阶梯形：主元逐行右移，且主元所在列的下方全是零

<svg viewBox="0 0 300 130" role="img" aria-hidden="true" font-family="sans-serif" font-size="11">
  <g stroke="currentColor" fill="none" opacity="0.5">
    <rect x="35" y="25" width="230" height="24"/><rect x="35" y="49" width="230" height="24"/>
    <rect x="35" y="73" width="230" height="24"/>
    <line x1="215" y1="25" x2="215" y2="97" stroke-dasharray="4 3"/>
  </g>
  <g stroke="currentColor" stroke-width="2" fill="none">
    <rect x="43" y="29" width="26" height="16"/><rect x="103" y="53" width="26" height="16"/>
    <rect x="163" y="77" width="26" height="16"/>
  </g>
  <g fill="currentColor" opacity="0.85">
    <text x="59" y="41">1</text><text x="119" y="65">1</text><text x="179" y="89">1</text>
    <text x="35" y="120">主元：每行第一个非零元，逐行右移</text>
  </g>
</svg>
:::

## 三种解：判据与自由变量

把增广矩阵化成行阶梯形之后，只看两件事：有没有矛盾行、主元够不够。两种判据都要在「没有矛盾行」
的前提下使用，所以顺序是先看矛盾行，再看主元个数。

::: figure ../assets/img/pool/线性代数-消元-三种解的情形对照-本机-03.png
alt: 三种解并列对照：交于一点、平行、同一条线
caption: 三种解的几何对照：交于一点（唯一解）、平行（无解）、同一条线（无穷多解）
:::

落到矩阵上，判据是这样两条：出现 $\left[\begin{array}{cccc|c} 0 & 0 & \dots & 0 & \text{非零} \end{array}\right]$
这样的行（也就是 $0 = \text{非零}$）就是**无解**；没有矛盾行时，主元个数等于未知量个数就是**唯一解**，
少于未知量个数就是**无穷多解**，差几个主元就有几个自由变量。

没有主元的那些未知量叫**自由变量**（free variable）：它可以任取一个值，其余未知量随之被定下来。
自由变量的个数就是解集的维数——一个自由变量，解集是一条直线；两个自由变量，解集是一个平面。

| 情形 | 行阶梯形的特征 | 主元个数 | 自由变量个数 | 解集 |
| --- | --- | --- | --- | --- |
| 唯一解 | 没有矛盾行 | 等于未知量个数 | 0 | 一个点 |
| 无穷多解 | 没有矛盾行 | 少于未知量个数 | 至少 1 个 | 直线、平面或更高维 |
| 无解 | 有 $\left[\begin{array}{ccc\|c} 0 & \dots & 0 & \text{非零} \end{array}\right]$ 行 | 与解无关 | 与解无关 | 空集 |

拿两个例子对照。无解的方程组：

$$
\begin{aligned}
x + 2y &= 1 \\
2x + 4y &= 3
\end{aligned}
$$

消元后第二行变成 $\left[\begin{array}{cc|c} 0 & 0 & 1 \end{array}\right]$，即 $0 = 1$，无解。
把右端项换成 $(1, 2)$，第二行变成全零，只剩一个主元而未知量有两个：$y$ 是自由变量，
解是 $(1 - 2t, t)$，一条直线上的无穷多个点。

::: warn 一整行零不等于无解
$\left[\begin{array}{cc|c} 0 & 0 & 0 \end{array}\right]$ 表示「这一行没提供新信息」，它在说这个方程是前几个方程的
线性组合，解集一点没变。只有右边也非零时才矛盾。看到一整行零就写「无解」，是最常见的误判。
:::

## 解的结构：特解加零空间

无穷多解的情形值得多看一步。$x + 2y = 1$ 的解可以写成

$$
(x, y) = (1, 0) + t \cdot (-2, 1)
$$

右边第一项是取 $t = 0$ 得到的一个**特解**；第二项是齐次方程 $x + 2y = 0$ 的全部解，也就是第 2 课
讲过的**零空间**。这不是巧合：若 $x_p$ 是 $Ax = b$ 的一个解，$v$ 是 $Av = 0$ 的任意解，那么
$A(x_p + v) = Ax_p + Av = b + 0 = b$，所以 $x_p + v$ 也是解；反过来两个解的差必然落在零空间里。

于是解集永远长这个样子：

$$
Ax = b \ \text{的全部解} = \text{一个特解} + \text{零空间的任意元素}
$$

这也是「自由变量的个数 = 零空间维数」的来源：两者都是解集维数，只是一个从方程组看、一个从变换看。

## 用 Python 算一遍

下面这段把消元写成代码，用的还是第 1 课的逐行列表运算。它只做一件事：把增广矩阵化成最简行阶梯形。

```python
def rref(M):
    """原地把 M 化成最简行阶梯形（主元为 1，主元列其余位置为 0）。"""
    M = [row[:] for row in M]                 # 拷贝一份，别改到调用方的矩阵
    rows, cols, r = len(M), len(M[0]) - 1, 0  # r 是当前要处理的行的下标
    for c in range(cols):                     # 逐列找主元
        p = next((i for i in range(r, rows) if M[i][c] != 0), None)
        if p is None:                         # 这一列没有可用主元
            continue
        M[r], M[p] = M[p], M[r]               # 把主元换到当前行
        pivot = M[r][c]
        M[r] = [v / pivot for v in M[r]]      # 主元化成 1
        for i in range(rows):                 # 其余各行消掉这一列
            if i != r and M[i][c] != 0:
                f = M[i][c]
                M[i] = [a - f * b for a, b in zip(M[i], M[r])]
        r += 1
    return M
```

```python
A = [[2, 1, 1], [1, 3, 2], [1, 1, -1]]
b = [9, 10, 2]
aug = [row + [rhs] for row, rhs in zip(A, b)]     # 拼成增广矩阵
for row in rref(aug):
    print(row)                    # [1,0,0,3] / [0,1,0,1] / [0,0,1,2] → x=3, y=1, z=2
```

三行打印出来分别是 `[1, 0, 0, 3]`、`[0, 1, 0, 1]`、`[0, 0, 1, 2]`，与手算的结果一致。这里用的是
浮点除法，结果看着干净是因为这些数恰好能整除；把矩阵里的数换成 `fractions.Fraction` 再跑，
遇到 `1/3` 这类结果时就不会有误差。

::: practice 上手做 | 第 1 步 · 用代码核对三种情形

把上面两段存成 `rref_demo.py`，然后分别跑下面三个方程组（只改 `A` 与 `b`）：

```text
① 唯一解：   A = [[2, 1, 1], [1, 3, 2], [1, 1, -1]]      b = [9, 10, 2]
② 无解：     A = [[1, 2], [2, 4]]                        b = [1, 3]
③ 无穷多解： A = [[1, 2], [2, 4]]                        b = [1, 2]
```

每个都先手写出「有没有矛盾行、主元几个、自由变量几个」，再用代码验证。第 ③ 个的最简行阶梯形
第二行会变成 `[0, 0, 0]`，主元只剩一个——这就是自由变量 $y$ 的来历。
:::

::: practice 练习 | 第 2 步 · 进 lab 把它写完整

上面这段代码只负责化简，还不会**判断**解的结构，也还不会把解**回代**出来。剩下的活分给它：

完整任务、环境与跑法见 [lab 说明](../lab/README.md)，里面四个函数要你亲手实现：

- `rref(A)`：化成最简行阶梯形；
- `pivot_columns(A)` 与 `rank(A)`：给出主元所在列、数出秩；
- `solve(A, b)`：用化简结果判断「唯一解 / 无解 / 无穷多解」，并给出自由变量的个数。

```bash
cd ../lab/0003-system-elimination
python3 -m unittest -v      # 现在是红的：20 条报 NotImplementedError，那是待办清单
```

卡住时按这个顺序来：先读断言的报错原文 → 再看函数上方注释里的边界 → 还不行把报错贴回会话。
我不直接给答案，会先问你哪一行不对。参考解在 `../lab/solutions/0003-system-elimination/`，做完再对照。
:::

## 这台机器与后面三课

消元是本课程第一个成型的工具：它把「有没有解、有几个解」变成可以机械执行、也可以写成代码的判定
过程。它的三个副产品后面还要用：主元位置决定哪些变量自由（第 4 课的基就是主元列给出的）；秩是主元
的个数；零空间是所有 $Av = 0$ 的解（第 5 课求特征向量时，解的就是 $(A - \lambda I)v = 0$ 这个齐次方程组）。

::: quiz 理解 锚点：消元得到的最简行阶梯形
:::

::: quiz 排错 锚点：无解与无穷多解的判别
:::

::: quiz 应用 锚点：通解与自由变量
:::

::: resources
- [MIT 18.06 线性代数（Gilbert Strang）](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/) | 公开课 · 第 1~2 讲完整演算消元与回代
- [NumPy 官方文档 · numpy.linalg.solve](https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html) | 官方文档 · 现成库的接口与奇异矩阵的报错，用于对照自己写的版本
- [Python 官方文档 · fractions.Fraction](https://docs.python.org/zh-cn/3/library/fractions.html) | 官方文档 · lab 里做精确消元用到的分数类型
:::
