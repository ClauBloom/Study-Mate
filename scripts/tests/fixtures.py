#!/usr/bin/env python3
"""回归测试用的**临时科目**：不依赖任何工作区，自己造 curriculum.yaml 与课件。

闸门（`scripts/check_lesson.py`）要判的东西不少（文件名、两类引用、题目块、主题开关、
命名与上下节课指针），所以 fixture 得是一份**能过闸门**的最小课件——测试再往里注入
自己那一处偏差，断言才不会被无关的 FAIL 污染。

用法：
    subject = fixtures.write_subject(tmp)                 # 造科目（5 个概念节点）
    path = fixtures.write_lesson(subject, 2, 'first-program')   # 造第 2 份课件（指针自动填对）
    code, out = fixtures.run_gate(path, subject, 'first-program')
"""
import os
import subprocess
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parents[1]
GATE = REPO / 'scripts' / 'check_lesson.py'
POOL_CHECK = REPO / 'scripts' / 'check_pool.py'

# 默认大纲：全是「概念」课——概念课不要求 lab，fixture 就不用造 lab 产物
DEFAULT_NODES = [
    ('overview-map', '概念', '全景地图'),
    ('first-program', '概念', '编译并跑通'),
    ('io-and-vars', '概念', '读入数据与输出答案'),
    ('branch-and-loop', '概念', '分支与循环'),
    ('func-and-ref', '概念', '函数与引用'),
]

VALID_QUIZ = ('<div class="quiz" data-quiz=\'[{"q":"这是题面？","opts":["A","B"],'
              '"ans":0,"why":"一句解释"}]\'></div>')

# 能过闸门的最小课件：两类引用齐全、有主题开关与接线、有一个合法题目块、没有题目位残留。
# 相对路径按 lessons/<file>.html → 共享层 ../../../assets/、科目组件 ../assets/ 写。
LESSON_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 测试科目</title>
<link rel="stylesheet" href="../../../assets/sayo/sayo.css">
<link rel="stylesheet" href="../../../assets/learn-theme.css">
<link rel="stylesheet" href="../assets/style.css">
<script src="../../../assets/learn-theme.js"></script>
<script>LearnTheme.apply();</script>
</head>
<body class="lesson-body">

<nav class="lesson-bar">
  <a href="../index.html">← 返回课程</a>
  <span>测试科目</span>
  <span class="lesson-bar__no">{number}</span>
  <label class="syo-toggle syo-toggle--theme lesson-bar__toggle" title="切换深浅主题">
    <input type="checkbox" id="lesson-theme-checkbox" checked>
    <span class="syo-toggle-track"></span>
    <span class="syo-toggle-knob"></span>
  </label>
</nav>

<article class="lesson">

  <header class="lesson-header">
    <span class="lesson-header__eyebrow">{number} · {title}</span>
    <h1>{title}</h1>
    <p class="lesson-goal"><b>本节目标：</b>回归测试用的最小课件。</p>
  </header>

  <h2>正文</h2>
  <p>这一节只是让闸门有东西可看。</p>

  {quiz}
{extra}
  <nav class="lesson-nav" aria-label="上一课 / 下一课">
{nav}  </nav>

  <footer class="lesson-footer">
    StudyMate · {number} {title} · 回归测试
  </footer>

</article>

<script src="../../../assets/sayo/sayo.js"></script>
<script src="../assets/quiz.js" defer></script>
<script src="../assets/lesson-toc.js" defer></script>
<script>LearnTheme.wire(document.getElementById('lesson-theme-checkbox'));</script>
</body>
</html>
'''


def write_subject(root, nodes=None):
    """在 root 下造一个科目目录（curriculum.yaml + lessons/），返回科目路径。"""
    nodes = nodes or DEFAULT_NODES
    subject = os.path.join(str(root), 'subject')
    os.makedirs(os.path.join(subject, 'lessons'), exist_ok=True)
    lines = ['nodes:']
    for node_id, kind, title in nodes:
        lines += [f'- id: {node_id}', f'  title: {title}', f'  kind: {kind}']
    with open(os.path.join(subject, 'curriculum.yaml'), 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')
    return subject


def clear_lessons(subject):
    """清掉 lessons/ 下所有课件——每个场景都从干净的一份重建。"""
    lessons = os.path.join(subject, 'lessons')
    for name in os.listdir(lessons):
        os.remove(os.path.join(lessons, name))


def auto_nav(subject, number):
    """按大纲顺序给第 number 份课件算出上/下节课指针（含「下节课还没产出」的情况）。"""
    nodes = read_nodes(subject)
    index = number - 1
    links = []
    if index >= 1:
        prev_id, _, prev_title = nodes[index - 1]
        links.append(('prev', f'{index:04d}-{prev_id}.html', prev_title))
    if index + 1 < len(nodes):
        next_id, _, next_title = nodes[index + 1]
        links.append(('next', f'{index + 2:04d}-{next_id}.html', next_title))
    return links


def read_nodes(subject):
    """读回 curriculum.yaml 的 nodes（只要 id/kind/title，手写解析够用）。"""
    nodes = []
    with open(os.path.join(subject, 'curriculum.yaml'), encoding='utf-8') as handle:
        current = {}
        for line in handle:
            line = line.strip()
            if line.startswith('- id:'):
                current = {'id': line.split(':', 1)[1].strip()}
                nodes.append(current)
            elif line.startswith('title:') and current is not None:
                current['title'] = line.split(':', 1)[1].strip()
            elif line.startswith('kind:'):
                current['kind'] = line.split(':', 1)[1].strip()
    return [(n['id'], n.get('kind', '概念'), n.get('title', n['id'])) for n in nodes]


def nav_html(links):
    """把 [(方向, href, 标题)] 拼成 .lesson-nav 的内容。"""
    label = {'prev': '上节课', 'next': '下节课'}
    out = ''
    for direction, href, title in links:
        out += (f'    <a class="lesson-nav__link lesson-nav__link--{direction}" href="{href}">\n'
                f'      <span class="lesson-nav__dir">{label[direction]}</span>\n'
                f'      <span class="lesson-nav__title">{title}</span>\n'
                f'    </a>\n')
    return out


def write_lesson(subject, number, node_id, quiz=None, nav='auto', title=None, extra=''):
    """写一份课件，返回路径。

    number  —— 编号（1 起，等于节点在 nodes 里的位次）
    quiz    —— 题目块的原始 HTML；不给就用一个合法题目块
    nav     —— 'auto'（按大纲自动填对）或 [(方向, href, 标题)]（原样写，用来注入偏差）
    extra   —— 插在题目块与导航之间的原始 HTML（配图、表格等，测别的检查项用）
    """
    if nav == 'auto':
        nav = auto_nav(subject, number)
    titles = {nid: node_title for nid, _, node_title in read_nodes(subject)}
    path = os.path.join(subject, 'lessons', f'{number:04d}-{node_id}.html')
    html = LESSON_TEMPLATE.format(
        number=f'{number:04d}',
        title=title or titles.get(node_id, node_id),
        quiz=quiz if quiz is not None else VALID_QUIZ,
        extra=extra,
        nav=nav_html(nav),
    )
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(html)
    return path


def run_gate(path, subject, node):
    """跑闸门，返回 (exit_code, 输出)。"""
    proc = subprocess.run(['python3', str(GATE), str(path), '--subject', str(subject), '--node', node],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def run_pool(subject):
    """跑池子校验器（`scripts/check_pool.py`），返回 (exit_code, 输出)。"""
    proc = subprocess.run(['python3', str(POOL_CHECK), str(subject)],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def check(label, ok, detail=''):
    """一行断言输出，返回是否通过。"""
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f'  — {detail}' if detail and not ok else ''))
    if not ok and detail:
        print('      ' + detail.strip().replace('\n', '\n      '))
    return ok
