#!/usr/bin/env python3
"""课程大纲模块（scripts/curriculum.py）的单元测试。

为什么单独有这一道：位次、课型、层级这条规则原先由五个脚本各写一遍，其中
**坏输入**（节点写坏、id 重复、YAML 坏、`nodes:` 空）在仓库里从来没有固定用例——
渲染与校验硬失败、重排与回填静默跳过、主页生成重复渲染，四套判决谁也不管谁。
口径收进一个模块之后，坏输入的行为才有地方钉住。

用法：python3 scripts/tests/test_curriculum.py
"""
import os
import sys
import tempfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parents[1]
sys.path.insert(0, str(REPO / 'scripts'))

import curriculum  # noqa: E402

failures = 0
total = 0


def check(label, ok, detail=''):
    global failures, total
    total += 1
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f'  — {detail}' if detail and not ok else ''))
    failures += not ok


def write_subject(text):
    """把一段 curriculum.yaml 写进临时科目目录，返回目录。"""
    directory = tempfile.mkdtemp(prefix='studymate-curriculum-')
    Path(directory, 'curriculum.yaml').write_text(text, encoding='utf-8')
    return directory


GOOD = """nodes:
  - id: vector.space
    title: 向量空间
    kind: 概念
    objective: 说清向量空间的三条公理
  - id: numpy.arrays
    title: NumPy 数组
    kind: 实操
    prerequisites: [vector.space]
  - id: numpy.broadcast
    title: 广播机制
    kind: 概念
    prerequisites: [numpy.arrays, 不存在的节点]
"""


def test_happy_path():
    cur, problems = curriculum.load(write_subject(GOOD))
    check('合法大纲：没有问题', problems == [], f'{problems}')
    check('节点数与顺序', cur.ids == ('vector.space', 'numpy.arrays', 'numpy.broadcast'), f'{cur.ids}')
    check('位次从 1 起', cur.index_of('vector.space') == 1 and cur.index_of('numpy.broadcast') == 3)
    check('不在大纲里回 None', cur.index_of('nope') is None)
    check('标题按大纲取', cur.title_of('numpy.arrays') == 'NumPy 数组')
    check('没标题回 id 本身', curriculum.Curriculum('x', [{'id': 'a', 'title': 'a', 'kind': '', 'objective': '', 'prerequisites': [], 'index': 1}]).title_of('a') == 'a')
    check('课型取得到', cur.kind_of('numpy.arrays') == '实操')
    check('课型没写回空串', cur.kind_of('numpy.broadcast') == '' or cur.kind_of('numpy.broadcast') == '概念')
    check('邻居：第一个没有上一课', cur.neighbors(1) == (None, 'numpy.arrays'))
    check('邻居：中间两头都有', cur.neighbors(2) == ('vector.space', 'numpy.broadcast'))
    check('邻居：最后一个没有下一课', cur.neighbors(3) == ('numpy.arrays', None))
    check('邻居：越界回 (None, None)', cur.neighbors(9) == (None, None) and cur.neighbors(None) == (None, None))


def test_levels():
    cur, _ = curriculum.load(write_subject(GOOD))
    levels = cur.levels()
    check('层级：无前置在第 0 层', [n['id'] for n in levels[0]] == ['vector.space'], f'{levels}')
    check('层级：逐级往下', [n['id'] for n in levels[1]] == ['numpy.arrays'])
    check('层级：未知前置忽略（当无前置）', [n['id'] for n in levels[2]] == ['numpy.broadcast'])
    cycle = curriculum.from_data({'nodes': [
        {'id': 'a', 'prerequisites': ['b']}, {'id': 'b', 'prerequisites': ['a']}]})[0]
    check('层级：成环不死循环', sorted(n['id'] for group in cycle.levels().values() for n in group) == ['a', 'b'])


def test_bad_nodes():
    text = """nodes:
  - id: good.one
    title: 好节点
  - title: 没有 id
  - id: Bad_ID
    title: id 形态不对
  - id: good.two
    title: 又一个好节点
"""
    cur, problems = curriculum.load(write_subject(text), strict=False)
    codes = [p.code for p in problems]
    check('坏节点：宽松口径逐条报', codes == ['bad_node', 'bad_node'], f'{codes}')
    check('坏节点：坏的两条都点名了第几项',
          problems[0].detail.startswith('nodes 第 2 项') and problems[1].detail.startswith('nodes 第 3 项'),
          f'{[p.detail for p in problems]}')
    check('坏节点：位次按书写位置，不压缩', [n['index'] for n in cur.nodes] == [1, 4], f'{[n["index"] for n in cur.nodes]}')
    strict_cur, strict_problems = curriculum.load(write_subject(text), strict=True)
    check('坏节点：严格口径不给大纲', strict_cur is None and len(strict_problems) == 2, f'{strict_problems}')
    check('坏节点：严格口径也一次报全', len(strict_problems) == 2)


def test_duplicate_ids():
    text = "nodes:\n  - id: dup\n    title: 第一份\n  - id: dup\n    title: 第二份\n  - id: other\n"
    cur, problems = curriculum.load(write_subject(text), strict=False)
    check('重复 id：宽松口径报一条', [p.code for p in problems] == ['duplicate_id'], f'{[p.code for p in problems]}')
    check('重复 id：位次只认第一次出现', cur.index_of('dup') == 1 and cur.title_of('dup') == '第一份')
    check('重复 id：第二次不再占位次', [n['index'] for n in cur.nodes] == [1, 3], f'{[n["index"] for n in cur.nodes]}')
    strict_cur, strict_problems = curriculum.load(write_subject(text), strict=True)
    check('重复 id：严格口径不给大纲', strict_cur is None and strict_problems[0].code == 'duplicate_id')
    check('重复 id：文案带可执行的下一步', 'check_curriculum.py' in strict_problems[0].message, strict_problems[0].message)


def test_broken_files():
    cur, problems = curriculum.load(os.path.join(tempfile.gettempdir(), 'studymate-no-such-subject'))
    check('缺文件：报 missing_file', cur is None and problems[0].code == 'missing_file')
    check('缺文件：文案含「找不到大纲文件」', '找不到大纲文件' in problems[0].message)

    cur, problems = curriculum.load(write_subject('nodes: [\n'))
    check('YAML 坏：报 bad_yaml', cur is None and problems[0].code == 'bad_yaml')
    check('YAML 坏：带行号', problems[0].line >= 1, f'line={problems[0].line}')

    cur, problems = curriculum.load(write_subject('nodes: 不是数组\n'))
    check('nodes 不是数组：报 nodes_shape', cur is None and problems[0].code == 'nodes_shape')

    cur, problems = curriculum.load(write_subject('nodes: []\n'), strict=True)
    check('空 nodes：严格口径不给大纲', cur is None and problems[0].code == 'empty_nodes')
    check('空 nodes：文案含「没有 nodes:」', '没有 nodes:' in problems[0].message)
    cur, problems = curriculum.load(write_subject('nodes: []\n'), strict=False)
    check('空 nodes：宽松口径给空大纲 + 一条问题',
          cur is not None and len(cur) == 0 and [p.code for p in problems] == ['empty_nodes'])

    cur, problems = curriculum.load(write_subject('顶层不是 mapping\n'))
    check('顶层不是 mapping：当作没有 nodes', cur is None and problems[0].code == 'nodes_shape')


def test_from_data():
    cur, problems = curriculum.from_data(None)
    check('from_data(None)：静默回 (None, [])（缺文件由调用方的读取层报）',
          cur is None and problems == [], f'{problems}')
    cur, problems = curriculum.from_data({})
    check('from_data({})：没有 nodes 键也算「没有大纲」，静默',
          cur is None and problems == [], f'{problems}')
    cur, problems = curriculum.from_data({'nodes': 'x'})
    check('from_data：nodes 写成标量才报一条', cur is None and [p.code for p in problems] == ['nodes_shape'],
          f'{[p.code for p in problems]}')
    cur, problems = curriculum.from_data({'nodes': [{'id': 'a'}, {'id': 'a'}]})
    check('from_data：与宽松口径同源（重复 id 只认第一次）',
          cur.index_of('a') == 1 and [p.code for p in problems] == ['duplicate_id'])


def main():
    for name, func in sorted(globals().items()):
        if name.startswith('test_') and callable(func):
            func()
    print(f'\n{total - failures}/{total} 通过')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
