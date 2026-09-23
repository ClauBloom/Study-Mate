"""StudyMate · 实操 0003-system-elimination 的自检（python3 -m unittest -v）

跑法：先进入本文件所在目录，再跑

    python3 -m unittest -v

交付状态下是**红的**：教程部分（增广矩阵的拼装与校验）那两条通过，标了「任务」的四个函数
此刻抛 NotImplementedError，整份测试以非零退出码结束。这就是起点——一次实现一个函数，
跑一次测试，看对应的那几条转绿。

四个函数都实现完之后，22 条应当全过（python3 -m unittest 退出码 0）。

断言的形状就是交付要求：解的结构是一个 dict，三种 kind 各带哪些键，见 gauss.py 的模块
docstring。用 Fraction 做相等比较，别用 float。
"""

import unittest
from fractions import Fraction

from gauss import pivot_columns, rank, rref, solve

F = Fraction


def augment(A, b):
    """把系数矩阵 A 与右端项 b 拼成增广矩阵（测试用的夹具，不依赖 gauss.py）。"""
    if len(A) != len(b):
        raise ValueError(f'A 有 {len(A)} 行，b 有 {len(b)} 个数，两者必须一样多')
    return [list(row) + [rhs] for row, rhs in zip(A, b)]


class TestTutorial(unittest.TestCase):
    """教程部分：跑一遍能看见结果的断言（这部分现在就是绿的）。"""

    def test_augment(self):
        self.assertEqual(augment([[1, 2], [3, 4]], [5, 6]), [[1, 2, 5], [3, 4, 6]])

    def test_augment_rejects_length_mismatch(self):
        with self.assertRaises(ValueError):
            augment([[1, 2], [3, 4]], [5])


class TestRref(unittest.TestCase):
    """任务 1：化成最简行阶梯形。"""

    def test_result_is_reduced(self):
        got = rref([[2, 4, 2, 8], [1, 2, 3, 9]])
        want = [[1, 2, 0, F(3, 2)], [0, 0, 1, F(5, 2)]]
        self.assertEqual(got, want)

    def test_pivots_are_one(self):
        got = rref([[2, 1, 1, 9], [1, 3, 2, 10], [1, 1, -1, 2]])
        self.assertEqual(got, [[1, 0, 0, 3], [0, 1, 0, 1], [0, 0, 1, 2]])

    def test_fractions_stay_exact(self):
        got = rref([[3, 1, 0, 1], [1, 1, 0, 1]])
        self.assertEqual(got, [[1, 0, 0, F(0)], [0, 1, 0, F(1)]])

    def test_zero_rows_go_last(self):
        got = rref([[1, 2, 3], [2, 4, 6]])
        self.assertEqual(got, [[1, 2, 3], [0, 0, 0]])

    def test_does_not_touch_the_input(self):
        matrix = [[2, 4], [1, 3]]
        rref(matrix)
        self.assertEqual(matrix, [[2, 4], [1, 3]])

    def test_empty_matrix(self):
        self.assertEqual(rref([]), [])


class TestUniqueSolution(unittest.TestCase):
    """任务 4 的一种情形：唯一解。"""

    def test_three_by_three(self):
        got = solve([[2, 1, 1], [1, 3, 2], [1, 1, -1]], [9, 10, 2])
        self.assertEqual(got['kind'], 'unique')
        self.assertEqual(got['solution'], [3, 1, 2])

    def test_two_by_two_gives_fraction(self):
        got = solve([[2, 1], [1, 3]], [1, 2])
        self.assertEqual(got['kind'], 'unique')
        self.assertEqual(got['solution'], [F(1, 5), F(3, 5)])

    def test_input_is_not_modified(self):
        A, b = [[2, 1], [1, 3]], [1, 2]
        solve(A, b)
        self.assertEqual((A, b), ([[2, 1], [1, 3]], [1, 2]))


class TestNoSolutionAndInfinite(unittest.TestCase):
    """任务 4 的另外两种情形：无解、无穷多解。"""

    def test_no_solution(self):
        got = solve([[1, 2], [2, 4]], [1, 3])
        self.assertEqual(got['kind'], 'none')
        self.assertNotIn('solution', got)

    def test_no_solution_needs_a_contradiction_row(self):
        got = solve([[1, 2], [2, 4]], [1, 2])
        self.assertNotEqual(got['kind'], 'none')

    def test_infinite_with_one_free_variable(self):
        got = solve([[1, 2], [2, 4]], [1, 2])
        self.assertEqual(got['kind'], 'infinite')
        self.assertEqual(got['free_count'], 1)
        self.assertEqual(len(got['null_basis']), 1)
        self.assertEqual(got['particular'], [1, 0])
        self.assertEqual(got['null_basis'][0], [-2, 1])

    def test_infinite_with_two_free_variables(self):
        got = solve([[1, 2, 3], [2, 4, 6]], [6, 12])
        self.assertEqual(got['kind'], 'infinite')
        self.assertEqual(got['free_count'], 2)
        self.assertEqual(len(got['null_basis']), 2)
        self.assertEqual(got['particular'], [6, 0, 0])
        self.assertIn([-2, 1, 0], got['null_basis'])
        self.assertIn([-3, 0, 1], got['null_basis'])

    def test_all_zero_coefficients(self):
        got = solve([[0, 0], [0, 0]], [0, 0])
        self.assertEqual(got['kind'], 'infinite')
        self.assertEqual(got['free_count'], 2)
        self.assertEqual(got['particular'], [0, 0])


class TestHelpersAndErrors(unittest.TestCase):
    """任务 2、3 与错误处理。"""

    def test_pivot_columns(self):
        self.assertEqual(pivot_columns([[1, 2, 0, 1.5], [0, 0, 1, 2.5]]), [0, 2])

    def test_pivot_columns_of_zero_matrix(self):
        self.assertEqual(pivot_columns([[0, 0], [0, 0]]), [])

    def test_rank_matches_pivot_count(self):
        self.assertEqual(rank([[1, 2], [2, 4]]), 1)
        self.assertEqual(rank([[2, 1], [1, 3]]), 2)
        self.assertEqual(rank([[0, 0], [0, 0]]), 0)

    def test_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            solve([[1, 2], [3, 4]], [1, 2, 3])

    def test_empty_input_raises(self):
        with self.assertRaises(ValueError):
            solve([], [])

    def test_empty_row_raises(self):
        with self.assertRaises(ValueError):
            solve([[]], [1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
