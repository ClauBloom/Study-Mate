#!/usr/bin/env python3
"""课件质量闸门：只阻断工程/结构缺项；内容风格类问题只提示，不影响放行。

用法：
  python3 scripts/check_lesson.py <课件路径> [<课件路径> ...]

输出：每个文件——无阻断项时一行 `OK   <path>`；有阻断项时 `FAIL <path>: 问题1；问题2`；
另有提示项时再补一行 `WARN <path>: 提示1；提示2`（两类可以同时出现）。
退出码：**只看阻断项**——全部文件无阻断项 0；任一文件有阻断项 1；无参数时把本用法打到 stderr 并退出 1。
只用标准库。总控在 xdg-open 打开课件之前跑一次：`FAIL` 的工程/结构缺项打回 learning-coach 修，
`WARN` 只自己心里有数（风格类不阻断、不因此打回）。

判定规则：
  阻断项（失败即打回）——只判工程/结构：
    1 文件名：匹配 NNNN-dash-case.html（四位数字-小写字母数字短横线）。编号规则：
      被检文件在同目录内是最大编号 → 必须等于其它文件最大编号 + 1（目录内只有它时必须是 0001）；
      否则（复检旧课件）→ 只要求该编号在目录内唯一。
    2 共享层引用：href/src 属性值里齐全 sayo.css、learn-theme.css、learn-theme.js、sayo.js。
    3 科目组件引用：href/src 属性值里齐全 ../assets/style.css、../assets/quiz.js。
    4 交互练习：存在 .quiz[data-quiz]；data-quiz 是合法 JSON 非空数组；每题 opts 是 ≥2 项的数组。
      （这一项用标准库 html.parser 读标签，免得好比 "a > b 成立" 这样的选项文本把标签正则截断。）
    5 实操引用：存在 href 属性值含 lab/ 的链接（要素里唯一可客观判定的工程性引用）。
    6 主题开关：存在 id="lesson-theme-checkbox" 的 <input type="checkbox">，
      且有 LearnTheme.wire(...) 引用该 id（骨架里的主题开关不能被改丢）。
  提示项（只回显、退出码不受影响）——质量线，值得看一眼：
    · 选项长度差：每题 max(len(opt)) - min(len(opt)) > MAX_OPT_LEN_GAP 时提示。

本闸门**不判内容风格**：真实场景开场、术语来历、怎么分节与标题怎么写，都是 lesson-design 的
要素与倾向，由讲解角色按内容与学生偏好现场定；闸门不用关键词词表去替它做判断——那种代理会把
课件逼成套模板。

已知且预期：templates/lesson.html 骨架本身过不了阻断项（组件示例改成注释形式后没有真的
`.quiz[data-quiz]`，也没有指向 lab/ 的链接；校验前会先剥掉注释）——骨架只给工程外壳与组件示例，
正文与实操由 learning-coach 按规范补齐，这不是闸门缺陷。

本脚本只做上面这些，不做计划外的额外检查（不查 lab/ 目录是否存在、不查 quiz 的 ans 越界、
不查 HTML 合法性）。校验前先剥掉 HTML 注释：注释里的示例标记不算真标记。
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

# ── 判定口径（要调整只改这里）─────────────────────────────────────────────

# 检查项 1：课件文件名与同目录编号（R4）
LESSON_NAME_RE = re.compile(r'^(\d{4})-[a-z0-9]+(-[a-z0-9]+)*\.html$')
NUMBERED_NAME_RE = re.compile(r'^(\d{4})-.*\.html$')

# 检查项 2/3：共享层与科目组件引用（按 href/src 属性值比对，不吃注释里的路径）
SHARED_REFS = ('sayo.css', 'learn-theme.css', 'learn-theme.js', 'sayo.js')
SUBJECT_REFS = ('../assets/style.css', '../assets/quiz.js')

# 检查项 4：每题选项最长与最短的长度差**提示**阈值（R5）——超过只提示，不阻断
MAX_OPT_LEN_GAP = 4

# 检查项 6：主题开关元素 id
THEME_CHECKBOX_ID = 'lesson-theme-checkbox'

# ── 公共正则 ────────────────────────────────────────────────────────────

REF_ATTR_RE = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']*)["\']', re.I)
COMMENT_RE = re.compile(r'<!--.*?-->', re.S)
LAB_LINK_RE = re.compile(r'href\s*=\s*["\'][^"\']*lab/', re.I)
INPUT_RE = re.compile(r'<input\b[^>]*>', re.I)


def strip_comments(text):
    """剥掉 HTML 注释，避免把注释里的示例标记当成真标记。"""
    return COMMENT_RE.sub('', text)


def ref_values(text):
    """取出所有 href/src 属性值，供引用类检查比对。"""
    return REF_ATTR_RE.findall(text)


# ── 各检查项：阻断项返回问题列表，提示项单独返回 ──────────────────────────


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
    """检查项 4：.quiz[data-quiz] 存在、JSON 合法、opts 结构正确（阻断）；选项长度差只提示。

    返回 (problems, notes)：problems 是阻断项，notes 是提示项（选项长度差超阈值）。
    """
    problems = []
    notes = []
    scanner = QuizScanner()
    scanner.feed(text)
    if scanner.missing:
        problems.append(f'交互练习块 .quiz 缺少 data-quiz 属性（{scanner.missing} 处）')

    blocks = scanner.blocks
    if not blocks:
        if not problems:
            problems.append('缺少 .quiz[data-quiz] 交互练习块')
        return problems, notes

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
                notes.append(f'{label}选项长度差 {gap} > {MAX_OPT_LEN_GAP}'
                             f'（最长 {max(lengths)} / 最短 {min(lengths)} 字符）')
    return problems, notes


def check_practice_link(text):
    """检查项 5：只查实操引用（href 含 lab/）；开场与术语来历属内容风格，不由闸门判定。"""
    if LAB_LINK_RE.search(text):
        return []
    return ['实操引用缺失：没有 href 指向 lab/ 的链接']


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
    """对一个课件跑完所有检查，返回 (problems, notes)：problems 为空 = 无阻断项。"""
    try:
        with open(path, encoding='utf-8') as handle:
            text = strip_comments(handle.read())
    except UnicodeDecodeError as exc:
        return [f'无法解码文件（需 UTF-8）：{exc.reason}'], []
    except OSError as exc:
        return [f'无法读取文件：{exc.strerror or exc}'], []

    quiz_problems, notes = check_quiz(text)
    problems = []
    problems += check_name(path)
    problems += check_shared_refs(text)
    problems += check_subject_refs(text)
    problems += quiz_problems
    problems += check_practice_link(text)
    problems += check_theme_toggle(text)
    return problems, notes


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    failed = False
    for path in argv:
        problems, notes = check_file(path)
        if problems:
            failed = True
            print(f'FAIL {path}: ' + '；'.join(problems))
        else:
            print(f'OK   {path}')
        if notes:
            print(f'WARN {path}: ' + '；'.join(notes))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
