#!/usr/bin/env python3
"""课件质量闸门：校验课件是否满足 lesson-design 规范里可客观判定的六项要素。

用法：
  python3 scripts/check_lesson.py <课件路径> [<课件路径> ...]

输出：每个文件一行 —— 通过 `OK   <path>`，不通过 `FAIL <path>: 问题1；问题2`。
退出码：全部通过 0；任一文件不通过 1；无参数时把本用法打到 stderr 并退出 1。
只用标准库。总控在 xdg-open 打开课件之前跑一次；失败即打回 learning-coach 修。

判定规则（对应 task-5-brief §5.3 六项，口径按 task-5-scope.md R3–R8）：
  1 文件名：匹配 NNNN-dash-case.html（四位数字-小写字母数字短横线）。编号规则：
    被检文件在同目录内是最大编号 → 必须等于其它文件最大编号 + 1（目录内只有它时必须是 0001）；
    否则（复检旧课件）→ 只要求该编号在目录内唯一。
  2 共享层引用：href/src 属性值里齐全 sayo.css、learn-theme.css、learn-theme.js、sayo.js。
  3 科目组件引用：href/src 属性值里齐全 ../assets/style.css、../assets/quiz.js。
  4 交互练习：存在 .quiz[data-quiz]；data-quiz 是合法 JSON 非空数组；每题 opts 是 ≥2 项的数组，
    且 max(len(opt)) - min(len(opt)) <= 4（Python 字符数）；缺 opts 或选项数 < 2 按结构错误报出。
    （这一项用标准库 html.parser 读标签，免得好比 "a > b 成立" 这样的选项文本把标签正则截断。）
  5 要素中可客观判定的三项（词表见文件顶部常量）：
    真实场景开场 = <article class="lesson"> 之后第一个 <h2> 的标题命中场景/问题词表；
    术语来历段   = 存在 <h2>/<h3> 标题命中来历词表（"先问题后定义"的可判定代理，不要求另有"定义"标题）；
    实操引用     = 存在 href 属性值含 lab/ 的链接。
  6 主题开关：存在 id="lesson-theme-checkbox" 的 <input type="checkbox">，
    且有 LearnTheme.wire(...) 引用该 id（骨架里的主题开关不能被改丢）。

已知且预期：templates/lesson.html 骨架本身过不了本闸门（示例 quiz 选项长度差 8/6、无术语来历段、
无指向 lab/ 的链接）——骨架只给结构，要素由 learning-coach 按规范补齐，这不是闸门缺陷。
本脚本只做上面六项，不做计划外的额外检查（不查 lab/ 目录是否存在、不查 quiz 的 ans 越界、
不查 HTML 合法性）。校验前先剥掉 HTML 注释：注释里的示例标记（骨架用法注释里就有一个示例
`data-quiz='[…]'`）不算真标记。
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

# ── 判定口径（要调整只改这里）─────────────────────────────────────────────

# 检查项 5：场景/问题词表与术语来历词表（R3）
SCENE_WORDS = ('场景', '麻烦', '问题', '为什么', '先看', '真实', '需求', '遇到过', '从一个')
ORIGIN_WORDS = ('来历', '由来', '历史', '为什么需要', '解决什么问题', '问题的')

# 检查项 1：课件文件名与同目录编号（R4）
LESSON_NAME_RE = re.compile(r'^(\d{4})-[a-z0-9]+(-[a-z0-9]+)*\.html$')
NUMBERED_NAME_RE = re.compile(r'^(\d{4})-.*\.html$')

# 检查项 2/3：共享层与科目组件引用（按 href/src 属性值比对，不吃注释里的路径）
SHARED_REFS = ('sayo.css', 'learn-theme.css', 'learn-theme.js', 'sayo.js')
SUBJECT_REFS = ('../assets/style.css', '../assets/quiz.js')

# 检查项 4：每题选项最长与最短的长度差上限（R5）
MAX_OPT_LEN_GAP = 4

# 检查项 6：主题开关元素 id
THEME_CHECKBOX_ID = 'lesson-theme-checkbox'

# ── 公共正则 ────────────────────────────────────────────────────────────

REF_ATTR_RE = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']*)["\']', re.I)
COMMENT_RE = re.compile(r'<!--.*?-->', re.S)
ARTICLE_RE = re.compile(r'<article\b[^>]*\bclass\s*=\s*["\'][^"\']*\blesson\b[^"\']*["\'][^>]*>', re.I)
H2_RE = re.compile(r'<h2\b[^>]*>(.*?)</h2>', re.S | re.I)
H23_RE = re.compile(r'<h[23]\b[^>]*>(.*?)</h[23]>', re.S | re.I)
LAB_LINK_RE = re.compile(r'href\s*=\s*["\'][^"\']*lab/', re.I)
INPUT_RE = re.compile(r'<input\b[^>]*>', re.I)


def strip_tags(markup):
    """去掉标签、压平空白，用于标题文本比对。"""
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', '', markup)).strip()


def strip_comments(text):
    """剥掉 HTML 注释，避免把注释里的示例标记当成真标记。"""
    return COMMENT_RE.sub('', text)


def ref_values(text):
    """取出所有 href/src 属性值，供引用类检查比对。"""
    return REF_ATTR_RE.findall(text)


# ── 六个检查项，各返回问题字符串列表 ─────────────────────────────────────


def check_name(path):
    """检查项 1：文件名 NNNN-dash-case.html + 同目录编号规则（R4）。"""
    problems = []
    name = os.path.basename(path)
    match = LESSON_NAME_RE.match(name)
    if not match:
        problems.append(f'文件名 {name!r} 不符合 NNNN-dash-case.html（四位数字 + 小写短横线）')
        return problems

    number = int(match.group(1))
    directory = os.path.dirname(path) or '.'
    try:
        entries = os.listdir(directory)
    except OSError as exc:
        problems.append(f'无法列出所在目录 {directory!r} 以核对编号：{exc.strerror or exc}')
        return problems

    others = []
    for entry in entries:
        if entry == name:
            continue
        other = NUMBERED_NAME_RE.match(entry)
        if other:
            others.append(int(other.group(1)))

    if not others:
        if number != 1:
            problems.append(f'编号 {number:04d} 应为 0001（同目录内这是第一份课件，不能跳号）')
    elif number > max(others):
        expected = max(others) + 1
        if number != expected:
            problems.append(f'编号 {number:04d} 与现有最大编号 {max(others):04d} 不连续，新课件应为 {expected:04d}')
    elif number in others:
        problems.append(f'编号 {number:04d} 在同目录内不唯一（另有 {others.count(number)} 份同编号课件）')
    return problems


def check_shared_refs(text):
    """检查项 2：共享层引用齐全（sayo.css / learn-theme.css / learn-theme.js / sayo.js）。"""
    refs = ref_values(text)
    return [f'共享层引用缺失：{required}' for required in SHARED_REFS
            if not any(required in ref for ref in refs)]


def check_subject_refs(text):
    """检查项 3：科目组件引用齐全（../assets/style.css、../assets/quiz.js）。"""
    refs = ref_values(text)
    return [f'科目组件引用缺失：{required}' for required in SUBJECT_REFS
            if not any(required in ref for ref in refs)]


class QuizScanner(HTMLParser):
    """收集 .quiz 块的 data-quiz 原文，并记下带 .quiz 但缺 data-quiz 的标签数。"""

    def __init__(self):
        super().__init__()
        self.blocks = []
        self.missing = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if 'quiz' not in (attributes.get('class') or '').split():
            return
        data = attributes.get('data-quiz')
        if data is None:
            self.missing += 1
        else:
            self.blocks.append(data)


def check_quiz(text):
    """检查项 4：.quiz[data-quiz] 存在、JSON 合法、每题选项长度差 ≤4（R5）。"""
    problems = []
    scanner = QuizScanner()
    scanner.feed(text)
    if scanner.missing:
        problems.append(f'交互练习块 .quiz 缺少 data-quiz 属性（{scanner.missing} 处）')

    blocks = scanner.blocks
    if not blocks:
        if not problems:
            problems.append('缺少 .quiz[data-quiz] 交互练习块')
        return problems

    for block_index, raw in enumerate(blocks, 1):
        prefix = f'第 {block_index} 个 .quiz 块' if len(blocks) > 1 else '.quiz'
        try:
            items = json.loads(raw)
        except ValueError as exc:
            problems.append(f'{prefix} 的 data-quiz 不是合法 JSON：{exc}')
            continue
        if not isinstance(items, list) or not items:
            problems.append(f'{prefix} 的 data-quiz 应为非空 JSON 数组')
            continue

        for question_index, item in enumerate(items, 1):
            label = f'{prefix} 第 {question_index} 题'
            if not isinstance(item, dict):
                problems.append(f'{label}不是 JSON 对象')
                continue
            opts = item.get('opts')
            if not isinstance(opts, list) or len(opts) < 2:
                problems.append(f'{label}选项结构错误（缺 opts 或选项数 < 2）')
                continue
            lengths = [len(str(opt)) for opt in opts]
            gap = max(lengths) - min(lengths)
            if gap > MAX_OPT_LEN_GAP:
                problems.append(f'{label}选项长度差 {gap} > {MAX_OPT_LEN_GAP}'
                                f'（最长 {max(lengths)} / 最短 {min(lengths)} 字符）')
    return problems


def check_elements(text):
    """检查项 5：真实场景开场、术语来历段、实操引用（R3）。"""
    problems = []

    article = ARTICLE_RE.search(text)
    opening = None
    if article:
        heading = H2_RE.search(text, article.end())
        if heading:
            opening = strip_tags(heading.group(1))
    if opening is None:
        problems.append('找不到 <article class="lesson"> 之后第一个 <h2>，无法判定真实场景开场')
    elif not any(word in opening for word in SCENE_WORDS):
        problems.append(f'真实场景开场缺失：第一个 <h2> 标题 {opening!r} 未命中场景/问题词表')

    titles = [strip_tags(match.group(1)) for match in H23_RE.finditer(text)]
    if not any(any(word in title for word in ORIGIN_WORDS) for title in titles):
        problems.append('术语来历段缺失：没有命中来历词表的 <h2>/<h3> 标题')

    if not LAB_LINK_RE.search(text):
        problems.append('实操引用缺失：没有 href 指向 lab/ 的链接')
    return problems


def check_theme_toggle(text):
    """检查项 6：主题开关元素与接线未丢。"""
    problems = []
    checkbox = None
    for tag in INPUT_RE.findall(text):
        if re.search(r'\bid\s*=\s*["\']' + THEME_CHECKBOX_ID + r'["\']', tag, re.I):
            checkbox = tag
            break
    if checkbox is None:
        problems.append(f'主题开关缺失：找不到 id="{THEME_CHECKBOX_ID}" 的 <input>')
    elif not re.search(r'\btype\s*=\s*["\']checkbox["\']', checkbox, re.I):
        problems.append(f'主题开关损坏：id="{THEME_CHECKBOX_ID}" 的 <input> 不是 type="checkbox"')
    if not re.search(r'LearnTheme\.wire\s*\([^)]*' + THEME_CHECKBOX_ID, text):
        problems.append(f'主题开关接线缺失：没有 LearnTheme.wire(...) 引用 {THEME_CHECKBOX_ID}')
    return problems


def check_file(path):
    """对一个课件跑完六项，返回问题列表（空列表 = 通过）。"""
    try:
        with open(path, encoding='utf-8') as handle:
            text = strip_comments(handle.read())
    except OSError as exc:
        return [f'无法读取文件：{exc.strerror or exc}']

    problems = []
    problems += check_name(path)
    problems += check_shared_refs(text)
    problems += check_subject_refs(text)
    problems += check_quiz(text)
    problems += check_elements(text)
    problems += check_theme_toggle(text)
    return problems


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    failed = False
    for path in argv:
        problems = check_file(path)
        if problems:
            failed = True
            print(f'FAIL {path}: ' + '；'.join(problems))
        else:
            print(f'OK   {path}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
