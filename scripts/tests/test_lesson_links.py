#!/usr/bin/env python3
"""本地引用可达：检查项 10 的判定（页面里的 href/src 必须落到真实文件）。

为什么单独有这道：`gen_home.py` 的断链自检只管它自己写出的主页（根主页 + 科目主页），
课件页不在它的范围内。检查项 2/3 只核对「引用写没写齐」，不管目标在不在；检查项 9 只管
`<img>`。于是页面可以**同时"通过全部检查"和"点开是白板 / 404"**——示例工作区里真发生过两次：
科目 `assets/` 缺了 `quiz.js` / `style.css`（页面没样式、题点不动），以及正文里那条 lab 链接
指向不存在的 README。

判定口径：
  · 本地目标不存在 → 阻断
  · 外链、锚点、`mailto:`、协议相对 `//` → 跳过
  · HTML 注释里的路径 → 跳过（模板里带一堆给生成器看的示例链接）
  · 上/下节课指针 → 跳过（落空是设计内的，检查项 8 只提示）
  · `?查询串` 与 `#片段` 先剥掉再解析；`%xx` 先解码

用法：python3 scripts/tests/test_lesson_links.py
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixtures  # noqa: E402

EXISTING = '  <p>速查页见 <a href="../reference/cheatsheet.html">这份速查</a>。</p>\n'
MISSING_LAB = '  <p>任务见 <a href="../lab/0001-ghost/README.md">lab 说明</a>。</p>\n'
EXTERNAL = ('  <p><a href="https://example.com/x">外链</a> '
            '<a href="#sec">锚点</a> '
            '<a href="mailto:someone@example.com">邮件</a> '
            '<a href="//cdn.example.com/lib.js">协议相对</a></p>\n')
COMMENTED = '  <!-- <a href="../lab/ghost/README.md">模板里的示例链接</a> -->\n'
WITH_QUERY = '  <p><a href="../reference/cheatsheet.html?v=2#top">带查询串的速查</a></p>\n'

# (说明, extra 里的 HTML, 要不要先删掉某个组件文件, 该不该拦, 输出里要含的片段)
CASES = [
    ('引用齐全（放行）', EXISTING, None, False, None),
    ('正文链接指向不存在的文件（拦）', MISSING_LAB, None, True, '不存在的本地文件'),
    ('正文链接指向存在的文件（放行）', EXISTING, None, False, None),
    ('外链/锚点/mailto/协议相对（放行）', EXTERNAL, None, False, None),
    ('注释里的路径（放行）', COMMENTED, None, False, None),
    ('带 ?查询串 与 #片段（放行）', WITH_QUERY, None, False, None),
    ('科目组件 quiz.js 不在（拦）', '', 'quiz.js', True, 'quiz.js'),
    ('科目组件 lesson-toc.js 不在（拦）', '', 'lesson-toc.js', True, 'lesson-toc.js'),
    ('共享层 learn-theme.css 不在（拦）', '', 'shared:learn-theme.css', True, 'learn-theme.css'),
]


def prepare_reference(subject):
    """造一份真实存在的速查页，给「链接指向存在的文件」这条用。"""
    reference = os.path.join(subject, 'reference')
    os.makedirs(reference, exist_ok=True)
    with open(os.path.join(reference, 'cheatsheet.html'), 'w', encoding='utf-8') as handle:
        handle.write('<!DOCTYPE html><title>速查</title>\n')


def drop_component(subject, which):
    """删掉一个组件文件；`shared:` 前缀表示共享层（`<root>/.learning/assets/`）。"""
    if which.startswith('shared:'):
        learning = os.path.dirname(os.path.dirname(subject))      # <root>/.learning
        target = os.path.join(learning, 'assets', which.split(':', 1)[1])
    else:
        target = os.path.join(subject, 'assets', which)
    os.remove(target)


def main():
    tmp = tempfile.mkdtemp(prefix='smtest-links-')
    subject = fixtures.write_subject(tmp)
    prepare_reference(subject)
    failures = 0
    for label, extra, drop, want_fail, must in CASES:
        fixtures.clear_lessons(subject)
        # 组件每次都重建：上一个用例可能删过它们
        fixtures.write_subject(tmp)
        if drop:
            drop_component(subject, drop)
        path = fixtures.write_lesson(subject, 1, 'overview-map', extra=extra)
        code, out = fixtures.run_gate(path, subject, 'overview-map')
        ok = (code != 0) == want_fail and (not must or must in out)
        failures += not ok
        fixtures.check(label, ok, out if not ok else f'检查={"FAIL" if code else "OK"}')

    # 下节课指针落空：属设计内，只提示不阻断
    fixtures.write_subject(tmp)
    fixtures.clear_lessons(subject)
    path = fixtures.write_lesson(subject, 1, 'overview-map')
    code, out = fixtures.run_gate(path, subject, 'overview-map')
    ok = code == 0 and '悬空指针' in out
    failures += not ok
    fixtures.check('下节课还没产出（放行，只有提示）', ok, out)

    total = len(CASES) + 1
    print(f'\n{total - failures}/{total} 通过')
    shutil.rmtree(tmp, ignore_errors=True)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
