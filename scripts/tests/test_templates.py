#!/usr/bin/env python3
"""模板与规格一致：`templates/` 的分节名与键，必须和提示词/schema 写的一致。

为什么单独有这道：规格是散文（写在 SKILL 与 `docs/` 里），模板是另一份文件，两者之间没有测试
连着。真出过事——`templates/GLOSSARY.md` 一直写 `## Terms`，而 `docs/文件归属.md`、
`learning-system`、`image-scout` 三处都按 `## 待掌握`／`## 已掌握` 两节读词：照模板建出来的术语表，
「采图」查不到主题词、主页也没有那两节可读。这类漂移不会有任何报错，只能靠交叉阅读发现。

所以这道**两边一起钉**：规格里写着的分节，模板里必须真有；模板的键，schema 里必须真有。
规格那边改了名而模板没跟、或者模板自创了键，都会红。

用法：python3 scripts/tests/test_templates.py
"""
import json
import re
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parents[1]
TEMPLATES = REPO / 'templates'

failures = 0
total = 0


def check(label, ok, detail=''):
    global failures, total
    total += 1
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f'  — {detail}' if detail and not ok else ''))
    failures += not ok


def read(path):
    return (REPO / path).read_text(encoding='utf-8')


def has_all(text, needles):
    """返回 (全都在, 缺哪些)。"""
    missing = [needle for needle in needles if needle not in text]
    return not missing, missing


def main():
    # ── 一、规格侧：这些分节名是规格定的（改规格要先改这里，再同步模板）────────
    ok, missing = has_all(read('docs/文件归属.md'), ['## 待掌握', '## 已掌握'])
    check('规格仍要求术语表两节（docs/文件归属.md）', ok, f'缺 {missing}')

    ok, missing = has_all(read('.dsh/skills/learning-system/SKILL.md'),
                          ['## Why', '## Success looks like', '## Constraints'])
    check('规格仍要求使命三节（learning-system 建课顺序）', ok, f'缺 {missing}')

    ok, missing = has_all(read('docs/使用说明.md'),
                          ['我是谁 / 教学偏好 / 学习习惯 / 跨科目观察'])
    check('规格仍列出共享记忆四节（docs/使用说明.md §六）', ok, f'缺 {missing}')

    # ── 二、模板侧：照着上面的规格逐条对 ──────────────────────────────────
    ok, missing = has_all(read('templates/GLOSSARY.md'), ['## 待掌握', '## 已掌握'])
    check('templates/GLOSSARY.md 有「待掌握 / 已掌握」两节', ok, f'缺 {missing}')

    ok, missing = has_all(read('templates/MISSION.md'),
                          ['## Why', '## Success looks like', '## Constraints'])
    check('templates/MISSION.md 有使命三节', ok, f'缺 {missing}')

    ok, missing = has_all(read('templates/MEMORY.md'),
                          ['## 我是谁', '## 教学偏好', '## 学习习惯', '## 跨科目观察'])
    check('templates/MEMORY.md 有共享记忆四节', ok, f'缺 {missing}')

    # 科目档案的键：模板与 schema 必须完全一致（模板自创键 = schema 校验会拦下来，
    # schema 加了键而模板没跟 = 学生新建科目时少写一个必填字段）
    schema = json.loads(read('schemas/subject.schema.json'))
    schema_keys = set(schema.get('properties', {}))
    try:
        import yaml
    except ImportError:      # pragma: no cover - 环境缺 pyyaml 时只跳过这一条
        check('templates/subject.yaml 的键与 subject.schema.json 一致（跳过：没有 pyyaml）', True)
    else:
        template_keys = set(yaml.safe_load(read('templates/subject.yaml')) or {})
        check('templates/subject.yaml 的键与 subject.schema.json 完全一致',
              template_keys == schema_keys,
              f'模板多 {sorted(template_keys - schema_keys)} / 模板缺 {sorted(schema_keys - template_keys)}')

    # status 的取值：模板里那个值必须是 schema enum 里的一员（写错的话建课第一步就过不了校验）
    status = (yaml.safe_load(read('templates/subject.yaml')) or {}).get('status')
    check(f'templates/subject.yaml 的 status 取值合法（{status}）',
          status in (schema['properties']['status'].get('enum') or []),
          f'不在 {schema["properties"]["status"].get("enum")} 里')

    # ── 三、围栏语言：渲染器认可的着色标签必须与前端配色表一一对应 ──────────
    # 真出过事——`python` 在渲染器里畅通无阻（原样写进 data-lang），而 learn-theme.js
    # 的 LANGS 没有这个键：Python 课件的 36 个代码块全部不上色，且没有任何报错。
    source = read('scripts/render_lesson.py')
    match = re.search(r'^COLORED_LANGS = \(([^)]*)\)', source, re.M)
    check('渲染器仍有 COLORED_LANGS 白名单', match is not None)
    colored = re.findall(r"'([a-z][a-z0-9_]*)'", match.group(1)) if match else []

    js = read('templates/assets/learn-theme.js')
    # 用带守卫的 search 取块：锚点漂成 `const LANGS = {` 时给出标签化的 FAIL，而不是 IndexError。
    match_js = re.search(r'var LANGS = \{([\s\S]*?)\n  \};', js)
    check('前端仍有 var LANGS 定义', match_js is not None)
    keys = re.findall(r'^    ([a-z][a-z0-9_]*): function', match_js.group(1), re.M) if match_js else []

    check('前端配色表与渲染器白名单逐个相等',
          sorted(keys) == sorted(colored),
          f'前端={sorted(keys)} 渲染器={sorted(colored)}')
    check('python 两边都有', 'python' in keys and 'python' in colored)

    # ── 四、共享层副本：examples 是产物，副本过期页面就静默不亮（本次事故的活样本）──────
    # 只比 ensure_shared_assets() 点名的四个平铺文件：examples 的 katex/ 下有一个早于本次
    # 改动就未跟踪的 fonts/LICENSE，做整树比对在干净检出里不稳定（那条另记）。
    for name in ('learn-theme.css', 'learn-theme.js', 'learn-mascot.png', 'lesson-math.js'):
        same = ((REPO / 'templates' / 'assets' / name).read_bytes()
                == (REPO / 'examples' / '.learning' / 'assets' / name).read_bytes())
        check(f'examples 共享层副本与模板逐字节一致（{name}）', same,
              f'跑 python3 scripts/gen_home.py examples 重新生成（副本过期会让页面静默不上色）')

    print(f'\n{total - failures}/{total} 通过')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
