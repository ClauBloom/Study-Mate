"""StudyMate · 实操 0003-system-elimination 的参考解（做完再对照）

把本文件拷进任务目录（覆盖 ``0003-system-elimination/gauss.py``），再在那个目录里跑
``python3 -m unittest -v``：22 条应当全绿（任务目录里那些 error 就是被它替掉的留白）。

实现要点（与课件第 3 课一一对应）

* ``rref``：逐列找主元 → 换到当前行 → 化成 1 → 用它把**其他所有行**的这一列消成 0。
  内存里全程用 ``Fraction``，不会出现 ``0.9999999`` 这种浮点误差。
* ``solve``：把 b 并到矩阵最右边当最后一列，化成最简行阶梯形后只看两件事——
  有没有 ``[0 … 0 | 非零]`` 的矛盾行；主元有几个。
* 解的结构：特解取「全部自由变量为 0」，零空间的基取「某个自由变量为 1、其余自由变量为 0」，
  每一列（每个未知量）恰好贡献一个方向。
"""

from fractions import Fraction


class InconsistentSystemError(ValueError):
    """方程组无解时由 solve() 抛出（solve 正常返回时不会抛）。"""


def _copy_matrix(A):
    """校验 A 的形状并拷一份，元素一律转成 Fraction（不改调用方的列表）。"""
    if len(A) == 0:
        raise ValueError('矩阵不能为空：至少要有一行')
    width = None
    rows = []
    for index, row in enumerate(A):
        if len(row) == 0:
            raise ValueError(f'第 {index} 行是空的：每一行至少要有一个数')
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError(f'第 {index} 行有 {len(row)} 个数，第一行有 {width} 个：各行长度要一致')
        rows.append([Fraction(value) for value in row])
    return rows


def rref(A):
    """把矩阵化成最简行阶梯形（主元为 1，主元列其余位置为 0）。

    ``rref([])`` 返回 ``[]``；其余情况按行扫描：每一列找一个非零元当主元，换到当前行后
    化成 1，再消掉这一列在别的行里的所有非零元。返回新矩阵，入参不动。
    """
    if len(A) == 0:
        return []
    M = _copy_matrix(A)
    rows, cols = len(M), len(M[0])
    r = 0
    for c in range(cols):
        pivot = next((i for i in range(r, rows) if M[i][c] != 0), None)
        if pivot is None:
            continue
        M[r], M[pivot] = M[pivot], M[r]
        divisor = M[r][c]
        M[r] = [value / divisor for value in M[r]]
        for i in range(rows):
            if i != r and M[i][c] != 0:
                factor = M[i][c]
                M[i] = [a - factor * b for a, b in zip(M[i], M[r])]
        r += 1
        if r == rows:
            break
    return M


def _pivots(M):
    """最简行阶梯形里 (列下标, 行下标) 的列表，按列升序。

    最简行阶梯形里每个非零行的第一个非零元就是主元，且主元逐行右移，所以按行扫一遍
    拿到的列下标天然递增。全零行跳过。
    """
    pivots = []
    for i, row in enumerate(M):
        for j, value in enumerate(row):
            if value != 0:
                pivots.append((j, i))
                break
    return pivots


def pivot_columns(A):
    """主元所在列的下标（从 0 开始，升序）；空矩阵返回 []。"""
    if len(A) == 0:
        return []
    return [column for column, _ in _pivots(rref(A))]


def rank(A):
    """矩阵的秩 = 主元的个数。"""
    return len(pivot_columns(A))


def solve(A, b):
    """解 Ax = b，返回解的结构：unique / none / infinite（约定见 gauss.py 的 docstring）。"""
    if len(A) == 0:
        raise ValueError('系数矩阵 A 不能为空')
    if len(A) != len(b):
        raise ValueError(f'A 有 {len(A)} 行，b 有 {len(b)} 个数，两者必须一样多')
    b = [Fraction(value) for value in b]
    augmented = _copy_matrix(A)
    for row, rhs in zip(augmented, b):
        row.append(rhs)

    reduced = rref(augmented)
    columns = len(A[0])
    pivots = _pivots(reduced)

    for row in reduced:
        if all(value == 0 for value in row[:columns]) and row[columns] != 0:
            return {'kind': 'none'}

    pivot_at = {column: row for column, row in pivots}

    if len(pivots) == columns:
        return {'kind': 'unique', 'solution': [reduced[pivot_at[c]][columns] for c in range(columns)]}

    # 特解：全部自由变量取 0，此时每个主元变量的值就是该行最右边的数
    particular = [Fraction(0)] * columns
    for column, row in pivots:
        particular[column] = reduced[row][columns]

    # 零空间的基：每个自由变量取 1，主元变量随之取该行系数的相反数
    basis = []
    for free in range(columns):
        if free in pivot_at:
            continue
        vector = [Fraction(0)] * columns
        vector[free] = Fraction(1)
        for column, row in pivots:
            vector[column] = -reduced[row][free]
        basis.append(vector)

    return {'kind': 'infinite', 'particular': particular, 'null_basis': basis,
            'free_count': columns - len(pivots)}
