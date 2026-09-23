"""StudyMate · 实操 0003-system-elimination（与课件 0003 对齐）

节点：system.elimination　载体：源码 + 测试（只用 Python 标准库）

怎么用
------
1. 先跑一遍看结果：

       python3 -m unittest -v

   交付状态下是红的：教程那 2 条通过，本文件里四个标了 ``▸ 你的任务`` 的函数抛
   NotImplementedError，测试以非零退出码结束。
2. 逐个实现那四个函数（一次一个），每实现一个就跑一次测试，看对应的那几条从 error 转绿。
3. 卡住了按这个顺序来：先读断言的报错原文 → 再看函数 docstring 里的边界提示 →
   还不行把报错原文贴回会话（我不直接给答案，会先问你哪一行不对）。
4. 参考解在 ``../solutions/0003-system-elimination/gauss.py``，做完再对照。

约定的返回结构（测试就是按它断言的）
------------------------------------
``solve(A, b)`` 返回一个 dict：

* ``kind='unique'``：``{'kind': 'unique', 'solution': [x1, x2, …]}``
* ``kind='none'``：``{'kind': 'none'}``（出现矛盾行，形如 0 = 非零）
* ``kind='infinite'``：``{'kind': 'infinite', 'particular': [...],
  'null_basis': [[...], [...]], 'free_count': 2}``

``particular`` 是取全部自由变量为 0 时得到的那个特解；``null_basis`` 是零空间的一组
基，长度等于自由变量个数。元素用 ``fractions.Fraction`` 表示，避免浮点误差。
"""

from fractions import Fraction


class InconsistentSystemError(ValueError):
    """方程组无解时由 solve() 抛出（solve 正常返回时不会抛）。"""


def rref(A):
    """▸ 你的任务 1：把矩阵化成最简行阶梯形（reduced row echelon form）。

    A 是行列表，例如 ``[[1, 2], [3, 4]]``。返回同形状的新矩阵（不要改到调用方传进来的
    那个列表），每一行都是一个新列表。

    最简行阶梯形的三条要求：

    * 每个非零行的第一个非零元（主元）是 1；
    * 主元所在列的其他位置全是 0；
    * 主元逐行右移：第 i+1 行的主元一定在第 i 行主元的右边。全零行排在最后。

    例：``rref([[2, 4, 2, 8], [1, 2, 3, 9]])`` 应该得到
    ``[[1, 2, 0, Fraction(3, 2)], [0, 0, 1, Fraction(5, 2)]]``。

    边界：``rref([])`` 返回 ``[]``。只允许整除的写法在遇到 ``1/3`` 这类结果时会出错，
    所以元素先转成 ``Fraction`` 再算。

    """
    raise NotImplementedError('▸ 任务 1 未实现：rref')


def pivot_columns(A):
    """▸ 你的任务 2：给出主元所在列的下标（从 0 开始，升序）。

    例：``pivot_columns([[1, 2, 0, 1.5], [0, 0, 1, 2.5]])`` 返回 ``[0, 2]``。
    空矩阵返回 ``[]``。

    提示：主元的个数就是秩，所以这个函数的返回值 ``len()`` 就是 ``rank()``。
    """
    raise NotImplementedError('▸ 任务 2 未实现：pivot_columns')


def rank(A):
    """▸ 你的任务 3：矩阵的秩（主元的个数）。

    秩的三种读法在这一课里是同一件事：非零行的个数、线性无关的列的最多个数、
    变换后空间的维数。用 ``pivot_columns`` 把它数出来。
    """
    raise NotImplementedError('▸ 任务 3 未实现：rank')


def solve(A, b):
    """▸ 你的任务 4：解线性方程组 Ax = b，返回解的结构（见模块 docstring 的约定）。

    三种情形：

    * 出现矛盾行（左边全零、右边非零）→ ``{'kind': 'none'}``；
    * 没有矛盾行且主元个数等于未知量个数 → ``{'kind': 'unique', 'solution': [...]}``；
    * 没有矛盾行且主元少于未知量个数 → ``{'kind': 'infinite', 'particular': [...],
      'null_basis': [...], 'free_count': n}``，其中 ``n = 列数 − 秩``。

    边界：

    * ``A`` 的行数必须等于 ``len(b)``，否则抛 ``ValueError``（信息里写清两个长度）；
    * ``A`` 为空或 ``A`` 的某一行为空时抛 ``ValueError``（没有未知量谈不上解方程组）；
    * 用 ``rref`` 处理增广矩阵，再把结果读出来：主元列对应的未知量由该行右端项直接给出，
      没有主元的列就是自由变量；
    * 系数与结果都用 ``Fraction``，不要用 ``float`` 做相等比较。

    不要修改传进来的 ``A`` 与 ``b``。
    """
    raise NotImplementedError('▸ 任务 4 未实现：solve')
