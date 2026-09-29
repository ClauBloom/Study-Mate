#!/usr/bin/env python3
"""内容文件语法模块（scripts/lessonfmt.py）的单元测试——第一块：围栏。

为什么单独有这一道：围栏判定原先在三个脚本里各写一遍（渲染器、回填器、主页生成器的
附件编译器），回填器的注释还写着「与 render_lesson.py 同口径」。判定分叉的代价是**静默**：

- `:::` 被当成指令插进代码块（回填器往代码里插行）；
- 代码块整段不上色——`python` 那次 36 个代码块的事故就是白名单两边不一致。

这里钉四件事：marker 的取法与翻转语义、白名单的认法、`:::` 与围栏的关系、
以及**渲染器这个消费者确实用的是同一份判定**（跨模块一致性）。

用法：python3 scripts/tests/test_lessonfmt.py
"""
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parents[1]
sys.path.insert(0, str(REPO / 'scripts'))

import lessonfmt  # noqa: E402
import render_lesson  # noqa: E402

failures = 0
total = 0


def check(label, ok, detail=''):
    global failures, total
    total += 1
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f'  — {detail}' if detail and not ok else ''))
    failures += not ok


class Problems:
    """最小的 problems 桩：render_lesson 的 parse_fence 只调 add(path, line, message)。"""

    def __init__(self):
        self.items = []

    def add(self, path, line, message):
        self.items.append((path, line, message))


def fence_spans(lines):
    """按 lessonfmt 的翻转语义算出围栏区间的行号（1 起，闭区间）。"""
    spans, opened = [], None
    for number, line in enumerate(lines, 1):
        if not lessonfmt.is_fence_line(line):
            continue
        if opened is None:
            opened = number
        else:
            spans.append((opened, number))
            opened = None
    return spans


def test_marker():
    check('裸围栏行的信息串是空串', lessonfmt.marker('```') == '')
    check('带语言的围栏行取到语言', lessonfmt.marker('```python') == 'python')
    check('缩进与尾随空格不影响判定', lessonfmt.marker('   ```py   ') == 'py')
    check('信息串原样保留（多余的部分交给白名单报错）',
          lessonfmt.marker('```python title="x"') == 'python title="x"')
    check('两个反引号不是围栏', lessonfmt.marker('``') is None)
    check('行内反引号不是围栏', lessonfmt.marker('`code`') is None)
    check('不在行首的 ``` 不是围栏（整行 strip 后必须以此开头）',
          lessonfmt.marker('文字 ```python') is None)
    check('空行不是围栏', lessonfmt.marker('') is None)
    check('波浪号围栏不支持（语法里没定义，别偷偷认）', lessonfmt.marker('~~~python') is None)


def test_toggle():
    check('开与关都算围栏行', lessonfmt.is_fence_line('```') and lessonfmt.is_fence_line('```python'))
    check('非围栏行不算', not lessonfmt.is_fence_line('普通文字'))
    lines = ['# 标题', '```python', 'print(1)', '```', '普通段落']
    check('成对出现时区间正确', fence_spans(lines) == [(2, 4)], f'{fence_spans(lines)}')
    check('落单的围栏只开不合（调用方各自报「没有闭合」）', fence_spans(['```python', 'x']) == [])


def test_langs():
    check('空标签算认（前端按内容猜）', lessonfmt.is_known_lang(''))
    check('着色标签认', all(lessonfmt.is_known_lang(lang) for lang in lessonfmt.COLORED_LANGS))
    check('不上色标签认', all(lessonfmt.is_known_lang(lang) for lang in lessonfmt.PLAIN_LANGS))
    check('没登记的语言不认（要带行号报错，不静默）', not lessonfmt.is_known_lang('rust'))
    check('大小写敏感（前端表也是小写键）', not lessonfmt.is_known_lang('Python'))
    check('两张表不重叠',
          not (set(lessonfmt.COLORED_LANGS) & set(lessonfmt.PLAIN_LANGS)),
          f'{sorted(set(lessonfmt.COLORED_LANGS) & set(lessonfmt.PLAIN_LANGS))}')
    check('两张表内部无重复',
          len(set(lessonfmt.COLORED_LANGS)) == len(lessonfmt.COLORED_LANGS)
          and len(set(lessonfmt.PLAIN_LANGS)) == len(lessonfmt.PLAIN_LANGS))
    check('事故里的两个别名都在（python / py）',
          'python' in lessonfmt.COLORED_LANGS and 'py' in lessonfmt.COLORED_LANGS)


def test_simple_fence_line():
    """校验器（题面/答案里的围栏配对）用的是更严的「简单围栏行」。"""
    check('裸围栏算简单围栏行', lessonfmt.is_simple_fence_line('```'))
    check('带标签算', lessonfmt.is_simple_fence_line('```python'))
    check('缩进与首尾空格不影响', lessonfmt.is_simple_fence_line('  ```py  '))
    check('标签里有空格就不算（渲染器仍认它是围栏，随后按未知语言报错）',
          lessonfmt.is_fence_line('```python extra') and not lessonfmt.is_simple_fence_line('```python extra'))
    check('行内反引号不算', not lessonfmt.is_simple_fence_line('`code`'))
    check('不在行首不算', not lessonfmt.is_simple_fence_line('文字 ```python'))


def test_directives_inside_fences():
    """`:::` 在围栏里是代码原文——三个消费者都靠这条判定。"""
    text = ('## 一\n'
            '\n'
            '```python\n'
            '::: quiz 1 锚点：x\n'
            '```\n'
            '\n'
            '::: tip 提示\n'
            '```\n'
            ':::\n'
            '```\n')
    lines = text.split('\n')
    spans = fence_spans(lines)
    check('三个围栏标记配成两段',
          spans == [(3, 5), (8, 10)], f'{spans}')

    def inside(number):
        return any(start <= number <= end for start, end in spans)

    check('围栏里的 ::: 在区间内（是代码，不是指令边界）', inside(4))
    check('围栏外的 ::: 不在区间内（是真正的指令）', not inside(7))
    check('收尾那个 ::: 也在区间内', inside(9))


def stub_problems():
    return Problems()


def test_renderer_uses_same_table():
    """消费者与模块的一致性：白名单里每个标签渲染器都不该报错，未登记的必须报错。"""
    for lang in lessonfmt.COLORED_LANGS + lessonfmt.PLAIN_LANGS:
        lines = [f'```{lang}', 'code', '```']
        problems = stub_problems()
        block, _ = render_lesson.parse_fence('x.md', lines, 0, len(lines), problems)
        check(f'渲染器接受 {lang}', not problems.items and block is not None,
              f'{problems.items}')
    lines = ['```rust', 'code', '```']
    problems = stub_problems()
    render_lesson.parse_fence('x.md', lines, 0, len(lines), problems)
    check('渲染器对未登记语言带行号报错',
          len(problems.items) == 1 and problems.items[0][1] == 1
          and 'rust' in problems.items[0][2], f'{problems.items}')
    lines = ['```python', 'code']
    problems = stub_problems()
    render_lesson.parse_fence('x.md', lines, 0, len(lines), problems)
    check('渲染器对没闭合的围栏报错',
          any('没有闭合' in message for _, _, message in problems.items), f'{problems.items}')


def test_renderer_toggle_uses_module():
    """渲染器的块解析：带语言的围栏里的 `:::` 是代码，不该被当成指令。"""
    lines = ['::: tip 提示', '```python', '::: 未知指令', '```', '正文', ':::', '']
    problems = stub_problems()
    render_lesson.parse_blocks('x.md', lines, 0, len(lines), problems)
    check('带语言围栏里的 ::: 不被当成指令', not problems.items, f'{problems.items}')


def test_rewriter_uses_same_judgment():
    """回填器（apply_empty_reasons）原先自己实现围栏判定，注释写着「与渲染器同口径」。"""
    import apply_empty_reasons as apply

    text = '::: quiz 1 锚点：x\n内容\n```python\n:::\n```\n:::\n'
    blocks = apply.quiz_blocks(text.split('\n'))
    check('回填器找到题目位置', len(blocks) == 1, f'{blocks}')
    check('回填器认的收尾在下标 5（围栏里的 ::: 不算收尾）',
          blocks and blocks[0]['close'] == 5, f'{blocks}')
    inside = ['开', '```python', ':::', '```', '合', ':::']
    check('回填器的 find_close 跳过围栏里的 :::',
          apply.find_close(inside, 0) == 5, f'{apply.find_close(inside, 0)}')


def main():
    for name, func in sorted(globals().items()):
        if name.startswith('test_') and callable(func):
            func()
    print(f'\n{total - failures}/{total} 通过')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
