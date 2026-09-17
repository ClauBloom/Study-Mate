#!/usr/bin/env python3
"""课件质量闸门：只阻断工程/结构缺项；内容风格类问题只提示，不影响放行。

用法：
  python3 scripts/check_lesson.py <课件路径> [<课件路径> ...] [--subject <科目目录>] [--node <节点id>]

`--subject` 与 `--node` 一起给，才能判定"这课该不该有 lab"：节点挂在
`<科目>/progress.yaml` 的 `project.milestones[].nodes` 上就是**实操课**（必须有 lab），
否则是**概念课**（不该有 lab）。不给这两个参数时跳过实操判定并回显一条提示。

输出：每个文件——无阻断项时一行 `OK   <path>`；有阻断项时 `FAIL <path>: 问题1；问题2`；
另有提示项时再补一行 `WARN <path>: 提示1；提示2`（两类可以同时出现）。
退出码：**只看阻断项**——全部文件无阻断项 0；任一文件有阻断项 1；无参数时把本用法打到 stderr 并退出 1。
总控在 xdg-open 打开课件之前跑一次：`FAIL` 的工程/结构缺项打回对应角色修
（题目相关 → practice-evaluator；版式/链接 → learning-coach），`WARN` 只自己心里有数。

判定规则：
  阻断项（失败即打回）——只判工程/结构：
    1 文件名：匹配 NNNN-dash-case.html（四位数字-小写字母数字短横线）。编号规则：
      被检文件在同目录内是最大编号 → 必须等于其它文件最大编号 + 1（目录内只有它时必须是 0001）；
      否则（复检旧课件）→ 只要求该编号在目录内唯一。
    2 共享层引用：href/src 属性值里齐全 sayo.css、learn-theme.css、learn-theme.js、sayo.js。
    3 科目组件引用：href/src 属性值里齐全 ../assets/style.css、../assets/quiz.js。
    4 题目（结构，题型不同要求不同；字段契约见 templates/assets/quiz.js 顶部注释）：
       每个 .quiz[data-quiz] 块是合法 JSON 非空数组；每题：
         · 都有非空 `q`（题面）；
         · 选择题（写了 opts/ans）：`opts` 是 ≥2 项的数组、`ans` 是范围内的整数、`why` 非空；
         · 开放题（写了 answer/criteria）：`answer`（参考答案）与 `criteria`（算过标准）都非空；
         · 两组字段不能同时出现在一题里；都没有则题型不明。
    5 实操（按节点条件判定，需 --subject 与 --node）：
       · 实操课：必须有 href 含 lab/ 的链接，且 `<科目>/lab/<本课编号>-*/` 存在、
         里面有任务文件、`<科目>/lab/solutions/` 非空；
       · 概念课：链接了 lab/ 只提示（规范上概念课不配实操），不阻断。
    6 主题开关：存在 id="lesson-theme-checkbox" 的 <input type="checkbox">，
       且有 LearnTheme.wire(...) 引用该 id（骨架里的主题开关不能被改丢）。
    7 题目位残留：`lessons/` 目录下的课件里不得留着 `<!-- 题目位：… -->` 标记
       （那是讲解角色回合一留下的占位，回合二必须替换掉）。
  提示项（只回显、退出码不受影响）——质量线，值得看一眼：
    · 选项长度差：每题 max(len(opt)) - min(len(opt)) > MAX_OPT_LEN_GAP 时提示。
    · 实操判定被跳过（没给 --subject/--node，或 progress.yaml 读不出来）。

本闸门**不判内容风格**：真实场景开场、术语来历、怎么分节与标题怎么写，都是 lesson-design 的
要素与倾向，由讲解角色按内容与学生偏好现场定；闸门不用关键词词表去替它做判断——那种代理会把
课件逼成套模板。题目**出得好不好**（难度、覆盖、与验收点的对应）也不由闸门判，那是
layered-practice 的规范与 practice-evaluator 的活；闸门只判结构完整。

已知且预期：templates/lesson.html 骨架本身过不了阻断项（组件示例改成注释形式后没有真的
`.quiz[data-quiz]`，也没有指向 lab/ 的链接；校验前会先剥掉注释）——骨架只给工程外壳与组件示例，
正文与题目由各角色按规范补齐，这不是闸门缺陷。

依赖：标准库 + pyyaml（与 gen_home.py 一致）；没装 pyyaml 时实操判定跳过并回显提示。
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

try:
    import yaml
except ImportError:      # pragma: no cover - 环境缺 pyyaml 时降级
    yaml = None

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

# 检查项 7：讲解角色回合一留下的题目位标记（只有课件正文用；骨架注释里是示例，路径不同）
PLACEHOLDER_RE = re.compile(r'^[ \t]*<!--[ \t]*题目位', re.M)
LESSONS_DIR_MARK = '/lessons/'

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


# ── 科目数据：节点是不是实操课（挂没挂项目里程碑）─────────────────────────


class SubjectData:
    """读 <科目>/progress.yaml，记下所有挂在项目里程碑上的节点 id。"""

    def __init__(self, subject_dir):
        self.dir = subject_dir
        self.practice_nodes = set()
        self.error = None
        if yaml is None:
            self.error = '未安装 pyyaml'
            return
        path = os.path.join(subject_dir, 'progress.yaml')
        try:
            with open(path, encoding='utf-8') as handle:
                progress = yaml.safe_load(handle) or {}
        except (OSError, UnicodeDecodeError) as exc:
            self.error = f'读不出 {path}（{exc}）'
            return
        except Exception as exc:                      # yaml.YAMLError 及结构异常
            self.error = f'{path} 不是合法 YAML（{exc}）'
            return
        project = progress.get('project') if isinstance(progress, dict) else None
        milestones = (project or {}).get('milestones') if isinstance(project, dict) else None
        for milestone in milestones or []:
            if not isinstance(milestone, dict):
                continue
            for node in milestone.get('nodes') or []:
                self.practice_nodes.add(str(node))


def lab_number_of(path):
    """课件编号（0002 → 2）；文件名不合格时返回 None，交给检查项 1 报。"""
    match = LESSON_NAME_RE.match(os.path.basename(path))
    return int(match.group(1)) if match else None


def check_lab_artifacts(subject_dir, number):
    """实操课的 lab 产物是否齐全：lab/<编号>-*/ 有任务文件、lab/solutions/ 非空。"""
    problems = []
    lab_dir = os.path.join(subject_dir, 'lab')
    if not os.path.isdir(lab_dir):
        return [f'实操课缺少 lab/ 目录（{lab_dir}）']

    entries = sorted(os.listdir(lab_dir))
    mine = [name for name in entries
            if re.match(rf'^0*{number}(?![0-9])', name) and name != 'solutions']
    if not mine:
        problems.append(f'lab/ 下没有与课件 {number:04d} 对应的 <编号>-主题 目录或文件')
    else:
        target = os.path.join(lab_dir, mine[0])
        if os.path.isdir(target):
            files = [name for name in os.listdir(target)
                     if not name.startswith('.') and name != '__pycache__']
            if not files:
                problems.append(f'{os.path.join("lab", mine[0])}/ 是空的（没有任务文件）')
        elif os.path.getsize(target) == 0:
            problems.append(f'{os.path.join("lab", mine[0])} 是空文件')

    solutions = os.path.join(lab_dir, 'solutions')
    if not os.path.isdir(solutions):
        problems.append('lab/solutions/ 缺失（参考答案要与任务分开放）')
    elif not [name for name in os.listdir(solutions) if not name.startswith('.')]:
        problems.append('lab/solutions/ 是空的（参考答案要与任务分开放）')
    return problems


def check_lab(text, path, subject, node):
    """检查项 5：实操引用与产物——按"这课是不是实操课"条件判定。"""
    problems = []
    notes = []
    has_link = bool(LAB_LINK_RE.search(text))

    if subject is None or node is None:
        notes.append('跳过实操判定：没给 --subject/--node，无法核对这课该不该有 lab')
        return problems, notes
    if subject.error:
        notes.append(f'跳过实操判定：{subject.error}')
        return problems, notes

    if node in subject.practice_nodes:
        if not has_link:
            problems.append(f'实操课缺少实操引用：节点 {node} 挂在项目里程碑上，'
                            '课件里必须有 href 指向 lab/ 的链接')
        else:
            number = lab_number_of(path)
            if number is not None:
                problems += check_lab_artifacts(subject.dir, number)
    elif has_link:
        notes.append(f'概念课却链接了 lab/：节点 {node} 没挂项目里程碑，'
                     '按规范概念课不配实操（只有轻量跟做）')
    return problems, notes


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


def check_placeholder(text, path):
    """检查项 7：课件里不得残留回合一的 `<!-- 题目位：… -->` 标记（看原文，注释未剥）。"""
    if LESSONS_DIR_MARK not in path.replace(os.sep, '/'):
        return []
    if PLACEHOLDER_RE.search(text):
        return ['课件里还留着未替换的题目位标记（回合二的嵌题没做完或标记没删）']
    return []


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
    """检查项 4：题目结构（阻断）＋选项长度差（提示）。字段契约见 quiz.js 顶部注释。

    返回 (problems, notes)。
    """
    problems = []
    notes = []
    scanner = QuizScanner()
    scanner.feed(text)
    if scanner.missing:
        problems.append(f'题目块 .quiz 缺少 data-quiz 属性（{scanner.missing} 处）')

    blocks = scanner.blocks
    if not blocks:
        if not problems:
            problems.append('缺少 .quiz[data-quiz] 题目块（每份课件至少一道题）')
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

            question = item.get('q')
            if not isinstance(question, str) or not question.strip():
                problems.append(f'{label}缺题面（q 必须是非空字符串）')

            is_choice = 'opts' in item or 'ans' in item
            is_open = 'answer' in item or 'criteria' in item
            if is_choice and is_open:
                problems.append(f'{label}题型冲突：选择题字段（opts/ans）与开放题字段（answer/criteria）'
                                '只能二选一')
                continue

            if is_choice:
                opts = item.get('opts')
                if not isinstance(opts, list) or len(opts) < 2:
                    problems.append(f'{label}选择题选项结构错误（缺 opts 或选项数 < 2）')
                    continue
                ans = item.get('ans')
                if isinstance(ans, bool) or not isinstance(ans, int) or not 0 <= ans < len(opts):
                    problems.append(f'{label}选择题的 ans 必须是从 0 开始、落在选项范围内的整数'
                                    f'（ans={ans!r}，选项数 {len(opts)}）')
                why = item.get('why')
                if not isinstance(why, str) or not why.strip():
                    problems.append(f'{label}选择题缺 why（答完要显示一句解释）')
                lengths = [len(str(opt)) for opt in opts]
                gap = max(lengths) - min(lengths)
                if gap > MAX_OPT_LEN_GAP:
                    notes.append(f'{label}选项长度差 {gap} > {MAX_OPT_LEN_GAP}'
                                 f'（最长 {max(lengths)} / 最短 {min(lengths)} 字符）')
            elif is_open:
                answer = item.get('answer')
                criteria = item.get('criteria')
                if not isinstance(answer, str) or not answer.strip():
                    problems.append(f'{label}开放题缺参考答案（answer）')
                if not isinstance(criteria, str) or not criteria.strip():
                    problems.append(f'{label}开放题缺算过标准（criteria，学生据此自评）')
            else:
                problems.append(f'{label}题型不明：选择题要 opts/ans/why，开放题要 answer/criteria')
    return problems, notes


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


def check_file(path, subject=None, node=None):
    """对一个课件跑完所有检查，返回 (problems, notes)：problems 为空 = 无阻断项。"""
    try:
        with open(path, encoding='utf-8') as handle:
            raw = handle.read()
    except UnicodeDecodeError as exc:
        return [f'无法解码文件（需 UTF-8）：{exc.reason}'], []
    except OSError as exc:
        return [f'无法读取文件：{exc.strerror or exc}'], []

    text = strip_comments(raw)
    quiz_problems, notes = check_quiz(text)
    lab_problems, lab_notes = check_lab(text, path, subject, node)
    problems = []
    problems += check_name(path)
    problems += check_shared_refs(text)
    problems += check_subject_refs(text)
    problems += quiz_problems
    problems += lab_problems
    problems += check_theme_toggle(text)
    problems += check_placeholder(raw, path)
    return problems, notes + lab_notes


def parse_args(argv):
    """位置参数是课件路径；`--subject <科目目录>` 与 `--node <节点id>` 用于实操判定。"""
    paths = []
    subject = None
    node = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ('-h', '--help'):
            print(__doc__)
            raise SystemExit(0)
        if arg in ('--subject', '--node'):
            if index + 1 >= len(argv):
                raise SystemExit(f'{arg} 需要一个值\n\n{__doc__}')
            if arg == '--subject':
                subject = argv[index + 1]
            else:
                node = argv[index + 1]
            index += 2
            continue
        if arg.startswith('-'):
            raise SystemExit(f'未知参数 {arg}\n\n{__doc__}')
        paths.append(arg)
        index += 1
    return paths, subject, node


def main(argv):
    paths, subject_dir, node = parse_args(argv)
    if not paths:
        raise SystemExit(__doc__)
    subject = SubjectData(subject_dir) if subject_dir else None
    failed = False
    for path in paths:
        problems, notes = check_file(path, subject, node)
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
