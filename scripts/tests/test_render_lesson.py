#!/usr/bin/env python3
"""课件渲染器 `scripts/render_lesson.py` 的回归测试，18 个场景。

渲染器是**唯一**的课件 HTML 产出者：讲解角色只写内容文件（`.md`），出题角色只写按锚点组织的
题库（`.quiz.json`），HTML 由渲染器从 `templates/lesson.html` 的占位符壳 + `curriculum.yaml`
（序号/邻居/标题）一次渲染出来。所以这套测试钉的不是"渲染器没报错"，而是**渲染产物里的真实片段**：

  壳与接线（共享层 4 引用 + 科目组件 2 引用 + 主题开关 + 三个 script）· `&<>` 转义与代码原文
  逐字 · 表格/列表/围栏/行内标记 · 题目按锚点合入且 `data-quiz` 属性值转义正确（单引号包裹、
  值里 `&#39;` / `&lt;` / `&gt;`）· 锚点缺题必须 `empty_reason` · 配图存在性与题注来源 · 导航
  与序号按大纲算 · 未知指令与块语法带行号报错 · `--check` 不写盘 · 渲染产物过闸门 ·
  **一级标题与段落中间的 HTML 都不许静默通过**（前者会连内容一起消失、后者会当字面量显示；
  真标签白名单与 code span 判定都只有一份，落单反引号遮不住标签、`n<m` 也不会被误杀）。

每个场景自造一个临时科目（`fixtures.write_subject` + `write_content` + `write_quiz`），
**不读也不写任何工作区**。用法：python3 scripts/tests/test_render_lesson.py
"""
import html as html_mod
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import fixtures  # noqa: E402
import render_lesson  # noqa: E402  只用来直接验 render_block 的兜底（其余用例都起真子进程）

TMP = tempfile.mkdtemp(prefix='smtest-render-')
_SUBJECT_SEQ = [0]

# 池子索引的表头与一行数据（列序见 check_pool.py：文件/主题标签/说明/来源 URL/许可/尺寸/抓取日期）
POOL_HEADER = '| 文件 | 主题标签 | 一句话说明 | 来源 URL | 许可 | 尺寸 | 抓取日期 |'
POOL_SEP = '| --- | --- | --- | --- | --- | --- | --- |'
POOL_IMAGE = '数组-内存布局-连续存储-cppreference-01.png'
POOL_ROW = (f'| {POOL_IMAGE} | 数组 · 内存布局 | 连续存储的内存布局 | '
            'https://en.cppreference.com/w/cpp/language/array | CC BY-SA 4.0 | 640×360 | 2026-09-19 |')

# 一道题面里同时有 `printf("x")`、`a > 0` 与单引号（';'）：三种转义一次钉住
QUIZ_BOUNDARY = [{
    'q': '这段代码里 printf("x") 在 a > 0 时执行吗？\n\n```cpp\nif (a > 0) printf("x");\n```\n',
    'opts': ['执行', '不执行'],
    'ans': 0,
    'why': 'a > 0 成立才执行；编译器对 \';\' 的报错属于语法错误那一类。',
}]

CASES = []


def case(label):
    """收集一个场景（函数收到一个 Asserts，把失败记进去）。"""
    def wrap(fn):
        CASES.append((label, fn))
        return fn
    return wrap


def new_subject(nodes=None, name='测试科目'):
    """每个场景一个干净的临时科目（互不干扰）。"""
    _SUBJECT_SEQ[0] += 1
    root = os.path.join(TMP, f'case{_SUBJECT_SEQ[0]}')
    os.makedirs(root, exist_ok=True)
    return fixtures.write_subject(root, nodes=nodes, name=name)


def write_pool(subject, files=(POOL_IMAGE,)):
    """造一个图片池子：`assets/img/pool/` 下的文件 + 兄弟索引 pool.md。"""
    pool = os.path.join(subject, 'assets', 'img', 'pool')
    os.makedirs(pool, exist_ok=True)
    for name in files:
        with open(os.path.join(pool, name), 'wb') as handle:
            handle.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 24)
    with open(os.path.join(subject, 'assets', 'img', 'pool.md'), 'w', encoding='utf-8') as handle:
        handle.write(f'{POOL_HEADER}\n{POOL_SEP}\n{POOL_ROW}\n')


class Asserts:
    """断言收集器：一个场景里所有断言都跑完，失败原因一起报，不半路中断。"""

    def __init__(self):
        self.failures = []

    def ok(self, label, passed, detail=''):
        if not passed:
            self.failures.append(label + (f'（{detail}）' if detail else ''))

    def has(self, text, *needles, label=None):
        """产物里必须逐字出现这些片段。"""
        missing = [needle for needle in needles if needle not in text]
        self.ok(label or f'含 {needles[0][:40]!r}', not missing,
                '缺 ' + '、'.join(repr(item) for item in missing))

    def hasnt(self, text, *needles, label=None):
        """产物里不许出现这些片段（例如首课不该有 --prev）。"""
        hit = [needle for needle in needles if needle in text]
        self.ok(label or f'不含 {needles[0][:40]!r}', not hit,
                '却出现 ' + '、'.join(repr(item) for item in hit))

    def equal(self, label, got, want):
        self.ok(label, got == want, f'实际 {got!r}，应为 {want!r}')


def render(subject, number, node_id, *args):
    """跑渲染器，返回 (exit_code, 输出, 产物文本（没写盘就是空串）, 产物路径)。"""
    code, out = fixtures.run_render(subject, node_id, *args)
    path = fixtures.lesson_html(subject, number, node_id)
    text = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
    return code, out, text, path


def line_of(md_path, needle):
    """needle 在内容文件里的行号（1 起）——报错信息必须指到这里。"""
    with open(md_path, encoding='utf-8') as handle:
        for index, line in enumerate(handle, 1):
            if line.rstrip('\n') == needle:
                return index
    raise AssertionError(f'{md_path} 里找不到 {needle!r}')


def quiz_attr(text):
    """取第一个 .quiz 块的 data-quiz 属性值（按书写原样，不解码实体）。"""
    match = re.search(r"<div class=\"quiz\" data-quiz='(.*?)'></div>", text, re.S)
    return match.group(1) if match else None


# ══════════════════════════════════════════════════════════════════
# ① 壳与接线：共享层 4 引用、科目组件 2 引用、主题开关、三个 script、抬头与页脚
# ══════════════════════════════════════════════════════════════════

@case('壳与接线齐全（共享层/科目组件/主题开关/三个 script/抬头页脚）')
def _(a):
    subject = new_subject()
    goal = '能把 `main.cpp` 编译成可执行文件，并看到程序打印的那一行。'
    fixtures.write_content(subject, 2, 'first-program', body='''## 一笔取款走过几条路

程序拿金额去比两个数，比完决定怎么处理。

::: quiz 理解 锚点：本节校验
:::
''', goal=goal)
    fixtures.write_quiz(subject, 2, 'first-program', {'本节校验': QUIZ_BOUNDARY})
    code, out, text, path = render(subject, 2, 'first-program')
    a.equal('渲染退出码 0', code, 0)
    a.has(text,
          '<!DOCTYPE html>',
          '<html lang="zh-CN" data-theme="light">',
          '<title>编译并跑通 · 测试科目</title>',
          '<link rel="stylesheet" href="../../../assets/sayo/sayo.css">',
          '<link rel="stylesheet" href="../../../assets/learn-theme.css">',
          '<link rel="stylesheet" href="../assets/style.css">',
          '<script src="../../../assets/learn-theme.js"></script>',
          '<script>LearnTheme.apply();</script>',
          '<script src="../../../assets/sayo/sayo.js"></script>',
          '<script src="../assets/quiz.js" defer></script>',
          '<script src="../assets/lesson-toc.js" defer></script>',
          '<input type="checkbox" id="lesson-theme-checkbox" checked>',
          'LearnTheme.wire(document.getElementById(\'lesson-theme-checkbox\'));',
          '<span>测试科目</span>',
          '<span class="lesson-bar__no">0002</span>',
          '<span class="lesson-header__eyebrow">0002 · 编译并跑通</span>',
          '<h1>编译并跑通</h1>',
          '<p class="lesson-goal"><b>本节目标：</b>能把 <code>main.cpp</code> 编译成可执行文件，'
          '并看到程序打印的那一行。</p>',
          '<div class="lesson-ask">',
          '把看不懂的段落（或报错）原样复制回会话',
          'StudyMate · 0002 编译并跑通 · 本地学习工作区')
    a.has(text, '<h2>一笔取款走过几条路</h2>', '<p>程序拿金额去比两个数，比完决定怎么处理。</p>')
    a.ok('交付页面从 <!DOCTYPE html> 起（模板说明注释不随页面出厂）',
         text.startswith('<!DOCTYPE html>\n<html'), repr(text[:60]))
    a.hasnt(text, '课件骨架', '闸门会拦', '不要手工拷贝', '写给维护者', '渲染器只从',
            label='产物里没有写给维护者的说明注释')


# ══════════════════════════════════════════════════════════════════
# ② 转义：正文与代码里的 &<>，且代码原文逐字保留
# ══════════════════════════════════════════════════════════════════

CODE_CPP = '''#include <cstdio>
#include <iostream>

int main() {
    int a = 1, b = 2;
    if (a < b && b > 0) printf("ok\\n");
    return 0;
}'''


@case('转义：正文 &<> 与代码原文逐字保留（不双重转义）')
def _(a):
    subject = new_subject()
    fixtures.write_content(subject, 1, 'overview-map', body='''## 比较与包含

比较写成 a < b && c > d 就算说清了。

```cpp
''' + CODE_CPP + '''
```

```text
原样的一段：a < b && c > d
```
''')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.equal('渲染退出码 0', code, 0)
    a.has(text,
          '<p>比较写成 a &lt; b &amp;&amp; c &gt; d 就算说清了。</p>',
          '<pre data-lang="cpp"><code>#include &lt;cstdio&gt;',
          'if (a &lt; b &amp;&amp; b &gt; 0) printf("ok\\n");',
          '<pre data-lang="text"><code>原样的一段：a &lt; b &amp;&amp; c &gt; d</code></pre>')
    a.hasnt(text, '&amp;lt;', '&amp;amp;', '&amp;gt;', label='不双重转义')

    match = re.search(r'<pre data-lang="cpp"><code>(.*?)</code></pre>', text, re.S)
    a.ok('代码块在产物里', match is not None)
    if match:
        a.equal('代码原文解码后与内容文件逐字相同', html_mod.unescape(match.group(1)), CODE_CPP)
    # 缺语言 → 不写 data-lang（不上色）
    fixtures.write_content(subject, 1, 'overview-map', body='''## 没语言标签

```
ls -la
```
''')
    code2, out2, text2, path2 = render(subject, 1, 'overview-map')
    a.equal('缺语言的围栏也渲染成功', code2, 0)
    a.has(text2, '<pre><code>ls -la</code></pre>')
    a.hasnt(text2, 'data-lang=""', label='缺语言时不写空的 data-lang')


# ══════════════════════════════════════════════════════════════════
# ③ 块与行内：标题、列表（含嵌套）、表格、行内标记
# ══════════════════════════════════════════════════════════════════

@case('块与行内：h3/列表嵌套/表格/行内 code·粗·斜·链接·上下标/段内换行')
def _(a):
    subject = new_subject()
    fixtures.write_content(subject, 1, 'overview-map', body='''## 写法总览

### 更小的标题

行内：`code`、**粗**、*斜*、[文字](https://example.com/a)、2^31^ 与 a~n~。

第二段从这里开始，
中文换行直接相接。
English words
wrap with a space.

- 项一
- 项二
  - 子项

1. 第一
2. 第二

| 题面里的说法 | 写法 |
| --- | --- |
| 不足 100 元 | `amount < 100` |
''')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.equal('渲染退出码 0', code, 0)
    a.has(text,
          '<h2>写法总览</h2>',
          '<h3>更小的标题</h3>',
          '<code>code</code>',
          '<b>粗</b>',
          '<em>斜</em>',
          '<a href="https://example.com/a">文字</a>',
          '<sup>31</sup>',
          '<sub>n</sub>',
          '<p>第二段从这里开始，中文换行直接相接。 English words wrap with a space.</p>',
          '<li>项一</li>',
          '<li>子项</li>',
          '<li>第一</li>')
    a.has(text, '<ul>', '</ul>', '<ol>', '</ol>', label='有序/无序列表都在')
    a.ok('列表嵌套（子项在最内层 ul 里）',
         re.search(r'<li>项二\s*<ul>\s*<li>子项</li>\s*</ul>\s*</li>', text) is not None,
         '产物的列表结构：' + repr(re.findall(r'<ul>.*?</ul>', text, re.S)[:1]))
    a.has(text, '<table>', '<thead>', '<th>题面里的说法</th>', '<th>写法</th>', '<tbody>',
          '<td>不足 100 元</td>', '<td><code>amount &lt; 100</code></td>')


# ══════════════════════════════════════════════════════════════════
# ④ 题目：按锚点合入 + data-quiz 属性值转义（单引号包裹）
# ══════════════════════════════════════════════════════════════════

@case('题目按锚点合入：data-quiz 单引号包裹、值里 &#39;/&lt;/&gt; 正确')
def _(a):
    subject = new_subject()
    fixtures.write_content(subject, 2, 'first-program', body='''## 边界值该算哪一档

先不编译，按规则判一次它实际走哪条路。

::: quiz 理解 锚点：校对边界
:::
''')
    fixtures.write_quiz(subject, 2, 'first-program', {'校对边界': QUIZ_BOUNDARY})
    code, out, text, path = render(subject, 2, 'first-program')
    a.equal('渲染退出码 0', code, 0)
    a.has(text, '<div class="quiz" data-quiz=\'')
    raw = quiz_attr(text)
    a.ok('能取出 data-quiz 的值', raw is not None)
    if raw is None:
        return
    a.has(raw, '&#39;;&#39;', label='题面里的单引号写成 &#39;')
    a.has(raw, '&gt; 0', label='题面里的 > 写成 &gt;')
    a.has(raw, 'printf(\\"x\\")', label='JSON 字符串里的双引号走 JSON 转义')
    a.hasnt(raw, "';'", label='值里不出现裸的单引号（浏览器会截断属性）')
    a.hasnt(raw, '&quot;', label='单引号包裹时不写实体引号（会提前闭合 JSON 字符串）')
    try:
        got = json.loads(html_mod.unescape(raw))
    except ValueError as exc:
        a.ok('解码实体后是合法 JSON', False, str(exc))
        return
    a.equal('题目内容与题库逐字一致', got, QUIZ_BOUNDARY)


# ══════════════════════════════════════════════════════════════════
# ⑤ 锚点无题：必须 empty_reason，否则带行号报错
# ══════════════════════════════════════════════════════════════════

@case('锚点无题：缺 empty_reason 报错带行号；有则跳过不报')
def _(a):
    subject = new_subject()
    fixtures.write_quiz(subject, 2, 'first-program', {'别的锚点': QUIZ_BOUNDARY})
    directive = '::: quiz 理解 锚点：不存在的锚点'
    md = fixtures.write_content(subject, 2, 'first-program', body=f'''## 数次数

数循环次数靠把取值列出来。

{directive}
:::
''')
    code, out, text, path = render(subject, 2, 'first-program')
    a.ok('缺 empty_reason 时非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, directive)}', label='报错指到内容文件的行')
    a.has(out, 'empty_reason', label='报错说清要补什么')
    a.ok('报错时没有写盘', not os.path.exists(path))

    subject2 = new_subject()
    fixtures.write_quiz(subject2, 2, 'first-program', {'别的锚点': QUIZ_BOUNDARY})
    fixtures.write_content(subject2, 2, 'first-program', body=f'''## 数次数

数循环次数靠把取值列出来。

{directive}
empty_reason: 该锚点本轮没有出题
:::
''')
    code2, out2, text2, path2 = render(subject2, 2, 'first-program')
    a.equal('写了 empty_reason 就放行', code2, 0)
    a.ok('产物写出来了', os.path.exists(path2))
    a.hasnt(text2, 'data-quiz', label='无题的锚点不产出题目块')


# ══════════════════════════════════════════════════════════════════
# ⑥ 配图：缺文件报错；池子里的图自动补来源与许可
# ══════════════════════════════════════════════════════════════════

@case('配图：缺文件报错带行号；池子里的图题注自动补来源与许可')
def _(a):
    subject = new_subject()
    missing = '::: figure ../assets/img/pool/不存在的图.png'
    md = fixtures.write_content(subject, 1, 'overview-map', body=f'''## 配图

{missing}
alt: 内存里挨着放
:::
''')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('图片文件不存在时非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, missing)}', label='报错指到内容文件的行')
    a.has(out, '不存在的图.png', label='报错说清是哪个文件')

    subject2 = new_subject()
    write_pool(subject2)
    fixtures.write_content(subject2, 1, 'overview-map', body=f'''## 配图

::: figure ../assets/img/pool/{POOL_IMAGE}
alt: 连续存储
caption: 图 1 · 数组在内存里挨着放
:::
''')
    code2, out2, text2, path2 = render(subject2, 1, 'overview-map')
    a.equal('池子里的图放行', code2, 0)
    a.has(text2,
          '<figure class="lesson-figure">',
          f'<img src="../assets/img/pool/{POOL_IMAGE}" alt="连续存储">',
          '<figcaption>图 1 · 数组在内存里挨着放（来源：'
          'https://en.cppreference.com/w/cpp/language/array，许可：CC BY-SA 4.0）</figcaption>')


# ══════════════════════════════════════════════════════════════════
# ⑦ 导航与序号：按 curriculum.yaml 的 nodes 顺序算
# ══════════════════════════════════════════════════════════════════

@case('导航与序号：首课无 --prev、末课无 --next、中间课两侧都对')
def _(a):
    subject = new_subject()
    body = '## 正文\n\n一段话。\n'
    for number, node in ((1, 'overview-map'), (2, 'first-program'), (5, 'func-and-ref')):
        fixtures.write_content(subject, number, node, body=body, goal='说清这一节要能做到什么。')

    code1, out1, first, path1 = render(subject, 1, 'overview-map')
    a.equal('首课渲染成功', code1, 0)
    a.ok('文件名 = <序号>-<节点id>.html', path1.endswith('0001-overview-map.html'))
    a.hasnt(first, 'lesson-nav__link--prev', label='首课没有 --prev 指针')
    a.has(first, '<a class="lesson-nav__link lesson-nav__link--next" href="0002-first-program.html">',
          '<span class="lesson-nav__dir">下节课</span>',
          '<span class="lesson-nav__title">编译并跑通</span>')

    code5, out5, last, path5 = render(subject, 5, 'func-and-ref')
    a.equal('末课渲染成功', code5, 0)
    a.hasnt(last, 'lesson-nav__link--next', label='末课没有 --next 指针')
    a.has(last, '<a class="lesson-nav__link lesson-nav__link--prev" href="0004-branch-and-loop.html">',
          '<span class="lesson-nav__dir">上节课</span>',
          '<span class="lesson-nav__title">分支与循环</span>')

    code2, out2, middle, path2 = render(subject, 2, 'first-program')
    a.equal('中间课渲染成功', code2, 0)
    a.has(middle,
          '<a class="lesson-nav__link lesson-nav__link--prev" href="0001-overview-map.html">',
          '<span class="lesson-nav__title">全景地图</span>',
          '<a class="lesson-nav__link lesson-nav__link--next" href="0003-io-and-vars.html">',
          '<span class="lesson-nav__title">读入数据与输出答案</span>')


# ══════════════════════════════════════════════════════════════════
# ⑧ 严格模式：未知指令与认不出的块语法都带行号报错
# ══════════════════════════════════════════════════════════════════

@case('严格模式：未知指令 / 四级标题 / 手写 HTML / 指令没闭合 都报错带行号')
def _(a):
    # 未知指令
    subject = new_subject()
    unknown = '::: fancy 一个不存在的指令'
    md = fixtures.write_content(subject, 1, 'overview-map',
                                body=f'## 正文\n\n{unknown}\n:::\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('未知指令非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, unknown)}', label='未知指令报错带行号')
    a.has(out, '未知指令', label='报错说清是未知指令')
    a.ok('未知指令时不写盘', not os.path.exists(path))

    # 词汇表里没有的块语法：四级标题
    subject = new_subject()
    fixture = '#### 四级标题'
    md = fixtures.write_content(subject, 1, 'overview-map', body=f'## 正文\n\n{fixture}\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('四级标题非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, fixture)}', label='四级标题报错带行号')
    a.has(out, '##', label='报错说清只支持 ## 与 ###')

    # 模型手写 HTML：块级标签一律拒收
    subject = new_subject()
    html_line = '<div class="lesson-tip">手写的提示块</div>'
    md = fixtures.write_content(subject, 1, 'overview-map', body=f'## 正文\n\n{html_line}\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('手写 HTML 非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, html_line)}', label='手写 HTML 报错带行号')
    a.has(out, 'HTML', label='报错说清不该写 HTML')

    # 指令没闭合
    subject = new_subject()
    opener = '::: tip 忘了闭合'
    md = fixtures.write_content(subject, 1, 'overview-map',
                                body=f'## 正文\n\n{opener}\n\n正文写到一半就没了。\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('指令没闭合非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, opener)}', label='没闭合报错指到指令那一行')
    a.has(out, '闭合', label='报错说清是没闭合')

    # related 的条目带说明（说明只有 resources 有）
    subject = new_subject()
    item = '- [上节课：浮点与精度](0004-cpp.float.html) | 官方文档'
    md = fixtures.write_content(subject, 1, 'overview-map',
                                body=f'## 正文\n\n::: related\n{item}\n:::\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('related 带说明非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, item)}', label='related 带说明报错带行号')

    # svg 带了参数（说明只能写在块里的 alt:/caption:）
    subject = new_subject()
    opener = '::: svg 双指针收拢'
    md = fixtures.write_content(subject, 1, 'overview-map',
                                body=f'## 正文\n\n{opener}\n<svg viewBox="0 0 4 2"></svg>\n:::\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('svg 带参数非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, opener)}', label='svg 带参数报错带行号')

    # 表格分隔行：格子里不是 --- 语法
    subject = new_subject()
    separator = '| --- | |'
    md = fixtures.write_content(subject, 1, 'overview-map',
                                body=f'## 表格\n\n| a | b |\n{separator}\n| 1 | 2 |\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('分隔行语法不对时非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, separator)}', label='分隔行语法报错带行号')

    # 表格分隔行：格子数与表头不一致
    subject = new_subject()
    separator = '| --- |'
    md = fixtures.write_content(subject, 1, 'overview-map',
                                body=f'## 表格\n\n| a | b |\n{separator}\n| 1 | 2 |\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('分隔行格子数不符时非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, separator)}', label='分隔行格子数报错带行号')
    a.has(out, '表头是 2 格', label='报错说清表头有几格')


# ══════════════════════════════════════════════════════════════════
# ⑨ --check：只解析校验、不写盘
# ══════════════════════════════════════════════════════════════════

@case('--check 只校验不写盘；坏内容 --check 也报错')
def _(a):
    subject = new_subject()
    fixtures.write_content(subject, 2, 'first-program', body='''## 正文

一段话。

::: quiz 理解 锚点：本节校验
:::
''')
    fixtures.write_quiz(subject, 2, 'first-program', {'本节校验': QUIZ_BOUNDARY})
    code, out, text, path = render(subject, 2, 'first-program', '--check')
    a.equal('--check 退出码 0', code, 0)
    a.ok('--check 不写盘', not os.path.exists(path), f'却写出了 {path}')

    code2, out2, text2, path2 = render(subject, 2, 'first-program')
    a.equal('不带 --check 才写盘', code2, 0)
    a.ok('产物存在', os.path.exists(path2))

    fixtures.write_content(subject, 2, 'first-program', body='## 正文\n\n::: nope 一个不存在的指令\n:::\n')
    code3, out3, text3, path3 = render(subject, 2, 'first-program', '--check')
    a.ok('坏内容 --check 非零退出', code3 != 0, f'exit={code3}')
    a.has(out3, '未知指令')


# ══════════════════════════════════════════════════════════════════
# ⑩ 提示卡：tip / warn / note（note 是追加的词汇，见 docs/课件内容格式.md）
# ══════════════════════════════════════════════════════════════════

@case('提示卡：tip / warn / note 的类名与加粗标题')
def _(a):
    subject = new_subject()
    fixtures.write_content(subject, 1, 'overview-map', body='''## 三个提示卡

::: tip 不想建文件也可以
临时试一行输入，可以直接敲 `./main` 回车。
:::

::: warn 两个反过来的写法
把 `-O2` 当成选项名会记串。
:::

::: note 两个名字先记住
`std::` 是标准库的命名空间前缀。
:::
''')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.equal('渲染退出码 0', code, 0)
    a.has(text,
          '<div class="lesson-tip">',
          '<b>不想建文件也可以</b>',
          '<p>临时试一行输入，可以直接敲 <code>./main</code> 回车。</p>',
          '<div class="lesson-warn">',
          '<b>两个反过来的写法</b>',
          '<div class="lesson-note">',
          '<b>两个名字先记住</b>')


# ══════════════════════════════════════════════════════════════════
# ⑪ 资源与相关：resources（ul + 说明）与 related（div + 链接）
# ══════════════════════════════════════════════════════════════════

@case('资源与相关：lesson-resources 的 li 结构、无链接条目、related 的 div')
def _(a):
    subject = new_subject()
    fixtures.write_content(subject, 1, 'overview-map', body='''## 参考资料

::: resources
- [OI Wiki · 分支](https://oi-wiki.org/lang/branch/) | 官方文档 · if 与 else if 的写法
- Competitive Programming 4（Halim 等，第 4 版） | 书 · 当参考书查
:::

::: related
- [上节课：浮点与精度](0004-cpp.float.html)
:::
''')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.equal('渲染退出码 0', code, 0)
    a.has(text, '<ul class="lesson-resources">',
          '<li><a href="https://oi-wiki.org/lang/branch/">'
          'OI Wiki · 分支</a><span class="lesson-resources__meta">官方文档 · if 与 else if 的写法'
          '</span></li>',
          '<li>Competitive Programming 4（Halim 等，第 4 版）'
          '<span class="lesson-resources__meta">书 · 当参考书查</span></li>',
          '</ul>',
          '<div class="lesson-related">',
          '<a href="0004-cpp.float.html">上节课：浮点与精度</a>')


# ══════════════════════════════════════════════════════════════════
# ⑫ 代码 span 逐字：里面的 ~ ^ ** 不当标记
# ══════════════════════════════════════════════════════════════════

@case('代码 span：~ ^ ** 是字面量，但上下标仍解析（语料 0002 的 code 里有 <sup>）')
def _(a):
    subject = new_subject()
    fixtures.write_content(subject, 1, 'overview-map', body='''## 位运算

按位取反写 `~a & ~b`，指针写 `int **p`，异或写 `a ^ b`。

算式写进代码里：`100000 × 100000 = 10^10^`。

区间写成 10 ~ 20 也行，单独的 ^ 与 * 不当标记。
''')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.equal('渲染退出码 0', code, 0)
    a.has(text,
          '<code>~a &amp; ~b</code>',
          '<code>int **p</code>',
          '<code>a ^ b</code>',
          '<code>100000 × 100000 = 10<sup>10</sup></code>',
          '区间写成 10 ~ 20 也行，单独的 ^ 与 * 不当标记。')
    a.hasnt(text, '<sub>', label='落单/带空格的 ~ 不产生下标（code 里也一样）')


# ══════════════════════════════════════════════════════════════════
# ⑬ 内联 SVG：原样透传
# ══════════════════════════════════════════════════════════════════

@case('内联 SVG：figure--inline + 块内 SVG 原样透传（缺 </svg> 报错）')
def _(a):
    subject = new_subject()
    svg = ('<svg viewBox="0 0 40 20" role="img" aria-hidden="true">'
           '<path d="M2 10h36" stroke="currentColor"/></svg>')
    fixtures.write_content(subject, 1, 'overview-map', body=f'''## 画一张

::: svg
alt: 双指针向中间收拢
caption: 图 1 · 收拢过程

{svg}
:::
''')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.equal('渲染退出码 0', code, 0)
    a.has(text,
          '<figure class="lesson-figure lesson-figure--inline" role="img" aria-label="双指针向中间收拢">',
          svg,
          '<figcaption>图 1 · 收拢过程</figcaption>')
    a.ok('SVG 逐字在产物里', text.count(svg) == 1)

    # 缺 </svg>：原样透传会把页面结构从这里断掉，必须报错而不是照发
    subject2 = new_subject()
    broken = '<svg viewBox="0 0 40 20"><path d="M2 10h36"/>'
    md = fixtures.write_content(subject2, 1, 'overview-map',
                                body=f'## 画一张\n\n::: svg\n{broken}\n:::\n')
    code2, out2, text2, path2 = render(subject2, 1, 'overview-map')
    a.ok('缺 </svg> 非零退出', code2 != 0, f'exit={code2}')
    a.has(out2, f'{md}:{line_of(md, "::: svg")}', label='缺 </svg> 报错指到指令那一行')
    a.has(out2, '</svg>', label='报错说清缺什么')

    # 自闭合的根 <svg/> 是合法收尾（退化但合法），不能拦
    subject3 = new_subject()
    fixtures.write_content(subject3, 1, 'overview-map',
                           body='## 画一张\n\n::: svg\n<svg viewBox="0 0 4 2"/>\n:::\n')
    code3, out3, text3, path3 = render(subject3, 1, 'overview-map')
    a.equal('自闭合 <svg/> 放行', code3, 0)
    a.has(text3, '<figure class="lesson-figure lesson-figure--inline">',
          '<svg viewBox="0 0 4 2"/>')


# ══════════════════════════════════════════════════════════════════
# ⑭ 端到端：渲染产物过闸门（check_lesson.py）
# ══════════════════════════════════════════════════════════════════

@case('渲染产物过闸门：check_lesson.py 报 OK')
def _(a):
    subject = new_subject()
    # 闸门按同目录编号判「不能跳号」：把邻居也渲染出来，0002 才是目录里的中间编号
    for number, node in ((1, 'overview-map'), (3, 'io-and-vars')):
        fixtures.write_content(subject, number, node, body='## 正文\n\n一段话。\n',
                               goal='说清这一节要能做到什么。')
        render(subject, number, node)
    fixtures.write_content(subject, 2, 'first-program', body='''## 校对边界

先不编译，按规则判一次它实际走哪条路。

::: quiz 理解 锚点：校对边界
:::

::: resources
- [OI Wiki · 分支](https://oi-wiki.org/lang/branch/) | 官方文档 · if 与 else if 的写法
:::
''')
    fixtures.write_quiz(subject, 2, 'first-program', {'校对边界': QUIZ_BOUNDARY})
    code, out, text, path = render(subject, 2, 'first-program')
    a.equal('渲染退出码 0', code, 0)
    gate_code, gate_out = fixtures.run_gate(path, subject, 'first-program')
    a.equal('闸门退出码 0', gate_code, 0)
    a.has(gate_out, f'OK   {path}', label='闸门回 OK')


# ══════════════════════════════════════════════════════════════════
# ⑮ 一级标题不许静默消失（`# 标题` 与行首 `#include` 都要报错）
# ══════════════════════════════════════════════════════════════════

@case('一级标题与行首 #include 都报错带行号（内容不会静默消失）')
def _(a):
    subject = new_subject()
    heading = '# 这一行连同标题会整块消失'
    include = '#include <cstdio>'
    md = fixtures.write_content(subject, 1, 'overview-map', body=f'''## 正文

这一段还在。

{heading}

再写一行：
{include}
''')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('一级标题非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, heading)}', label='一级标题报错带行号')
    a.has(out, f'{md}:{line_of(md, include)}', label='行首 #include 报错带行号')
    a.has(out, '## 与 ###', '围栏', label='报错给出改法（只有 ##/###，代码放围栏）')
    a.ok('报错时不写盘', not os.path.exists(path))

    # 放进围栏就正常：同一段代码不该再被当成标题
    fixtures.write_content(subject, 1, 'overview-map', body=f'''## 正文

```cpp
{include}
```
''')
    code2, out2, text2, path2 = render(subject, 1, 'overview-map')
    a.equal('围栏里的 #include 放行', code2, 0)
    a.has(text2, '<pre data-lang="cpp"><code>#include &lt;cstdio&gt;</code></pre>')

    # 兜底：渲染器遇到不认识的块要报错，不能安静地丢
    problems = render_lesson.Problems()
    renderer = render_lesson.Renderer('x.md', problems, '.', None, 'x.quiz.json', {})
    output = renderer.render_block({'kind': 'h1', 'text': '一级标题', 'line': 7}, '  ')
    a.equal('不认识的块不产出内容', output, '')
    a.ok('不认识的块记了一条问题', bool(problems) and problems.items[0][1] == 7,
         f'problems={problems.items}')

    # 兜底同理：不认识的指令也要报错（不能静默空输出）
    problems2 = render_lesson.Problems()
    renderer2 = render_lesson.Renderer('x.md', problems2, '.', None, 'x.quiz.json', {})
    output2 = renderer2.render_directive({'kind': 'directive', 'name': 'nope', 'line': 9}, '  ')
    a.equal('不认识的指令不产出内容', output2, '')
    a.ok('不认识的指令记了一条问题', bool(problems2) and problems2.items[0][1] == 9,
         f'problems={problems2.items}')


# ══════════════════════════════════════════════════════════════════
# ⑯ 段落中间的 HTML 标签要拦；运算符/泛型/落单反引号都不误伤
# ══════════════════════════════════════════════════════════════════

@case('段落中间的 HTML 标签报错；运算符/泛型/落单反引号都不误伤')
def _(a):
    subject = new_subject()
    inline_html = '这段里手写了 <b>粗</b> 标签。'
    md = fixtures.write_content(subject, 1, 'overview-map',
                                body=f'## 正文\n\n{inline_html}\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('段落内标签非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, inline_html)}', label='段落内标签报错带行号')
    a.has(out, '<b>', '**…**', label='报错给出改法（粗体写 **…**）')
    a.ok('报错时不写盘', not os.path.exists(path))

    # 落单的反引号不是 code 区：它不能把后面的标签遮住（code span 判定与 inline() 共用一份）
    subject = new_subject()
    masked = '见 ` 这里 <b>粗</b> 结束。'
    md = fixtures.write_content(subject, 1, 'overview-map',
                                body=f'## 正文\n\n{masked}\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('落单反引号遮不住标签：非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, masked)}', label='落单反引号那一段报错带行号')
    a.has(out, '<b>')

    # 段落中间的 HTML 注释也要拦（手写时代留「题目位」的写法）
    subject = new_subject()
    comment = '前面 <!-- 题目位：L1 ×2 --> 后面。'
    md = fixtures.write_content(subject, 1, 'overview-map',
                                body=f'## 正文\n\n{comment}\n')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('段落中间注释非零退出', code != 0, f'exit={code}')
    a.has(out, f'{md}:{line_of(md, comment)}', label='段落中间注释报错带行号')
    a.has(out, 'HTML 注释', label='报错说清是注释')

    # front matter 的 title 也是散文，同样要查（它是纯文本，不走 inline()）
    subject = new_subject()
    fixtures.write_content(subject, 1, 'overview-map', body='## 正文\n\n一段话。\n',
                           title='<b>粗</b>标题')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.ok('title 里的标签非零退出', code != 0, f'exit={code}')
    a.has(out, 'title', label='报错说清是 front matter 的 title')

    # 运算符、泛型、code span：都必须原样放行
    subject2 = new_subject()
    operators = ('当 n<m 且 m>0 时循环继续，a<b>c 也一样；比较写成 a < b && c > d、2 < n，'
                 '泛型写 <T> 与 `vector<int>` 都没问题。')
    fixtures.write_content(subject2, 1, 'overview-map', body=f'## 运算符\n\n{operators}\n')
    code2, out2, text2, path2 = render(subject2, 1, 'overview-map')
    a.equal('运算符与泛型放行', code2, 0)
    a.has(text2, '<p>当 n&lt;m 且 m&gt;0 时循环继续，a&lt;b&gt;c 也一样；'
                 '比较写成 a &lt; b &amp;&amp; c &gt; d、2 &lt; n，'
                 '泛型写 &lt;T&gt; 与 <code>vector&lt;int&gt;</code> 都没问题。</p>')


# ══════════════════════════════════════════════════════════════════
# ⑰ 指令体里的代码围栏不被当成指令边界
# ══════════════════════════════════════════════════════════════════

@case('指令体里的围栏：里面的 ::: 是代码文本，不当指令边界')
def _(a):
    subject = new_subject()
    fixtures.write_content(subject, 1, 'overview-map', body='''## 写法示例

::: tip 题目位的写法
题目位在正文里长这样：

```markdown
::: quiz 理解 锚点：某个锚点
:::
```

锚点要和题库的键逐字一致。
:::
''')
    code, out, text, path = render(subject, 1, 'overview-map')
    a.equal('渲染退出码 0', code, 0)
    a.ok('没有误报「指令块不能嵌套」', '不能嵌套' not in out, out)
    a.has(text,
          '<div class="lesson-tip">',
          '<b>题目位的写法</b>',
          '<pre data-lang="markdown"><code>::: quiz 理解 锚点：某个锚点\n:::</code></pre>',
          '<p>锚点要和题库的键逐字一致。</p>')


# ══════════════════════════════════════════════════════════════════
# ⑱ 模板占位符报错的行号要指到 templates/lesson.html 的真实行
# ══════════════════════════════════════════════════════════════════

@case('模板占位符报错指到模板文件的真实行号（不被 DOCTYPE 切片平移）')
def _(a):
    template_path = render_lesson.TEMPLATE
    original = open(template_path, encoding='utf-8').read()
    marker = '<!-- @LEARN:TITLE -->'
    a.ok('模板里 TITLE 出现两次（用例前提）', original.count(marker) == 2,
         f'实际 {original.count(marker)} 次')

    # 去掉 <h1> 那一处，只留 <title> 那一处：占位符数不对（1 ≠ 2），报错必须指到留下的那一行
    broken = original.replace(f'<h1>{marker}</h1>', '<h1>标题</h1>', 1)
    tmp_dir = tempfile.mkdtemp(prefix='smtest-tpl-')
    broken_path = os.path.join(tmp_dir, 'lesson.html')
    with open(broken_path, 'w', encoding='utf-8') as handle:
        handle.write(broken)
    true_line = broken[:broken.find(marker)].count('\n') + 1
    problems = render_lesson.Problems()
    a.ok('模板能读进来', render_lesson.load_template(broken_path, problems) is not None)
    a.ok('模板缺占位符时报错', bool(problems), '没有报错')
    if problems:
        path, line, message = problems.items[0]
        a.equal('报错指到模板文件', path, broken_path)
        a.equal('行号 = 模板文件里的真实行号', line, true_line)
        a.has(message, marker)
    shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    failures = 0
    for label, fn in CASES:
        a = Asserts()
        try:
            fn(a)
        except Exception as exc:                                   # 用例自己崩了也要报出来
            a.failures.append(f'用例抛异常：{exc!r}')
        failures += bool(a.failures)
        fixtures.check(label, not a.failures, '；'.join(a.failures))
    total = len(CASES)
    print(f'\n{total - failures}/{total} 通过')
    shutil.rmtree(TMP, ignore_errors=True)
    return 1 if failures else 0

if __name__ == '__main__':
    sys.exit(main())
