#!/usr/bin/env python3
"""预览两个主页模板：把模板 + 示例数据渲染成一个「模拟学习工作区」，用浏览器打开看效果。

重要：`templates/*.html` **不是能直接双击打开的页面**——它们引用的是生成后的工作区相对路径
（根主页 `.learning/assets/…`、科目页 `../../assets/…`），仓库里并没有这些目录，直接打开只有裸 HTML。
要看效果就跑这个脚本。

用法：
    python3 scripts/preview_templates.py            # 渲染到 <root>/.preview/
    python3 scripts/preview_templates.py --open     # 渲染完用 xdg-open/open 打开根主页

产出（`.preview/` 已加进 .gitignore，不会进仓库）：
    .preview/index.html                                  根主页（4 门示例科目）
    .preview/index-empty.html                            根主页空状态
    .preview/.learning/assets/…                          共享层（sayo + learn-theme.css）
    .preview/.learning/subjects/typescript-web-api/index.html        科目主页（12 节点 / 7 篇课件）
    .preview/.learning/subjects/typescript-web-api/empty.html        科目主页空状态
    .preview/.learning/subjects/typescript-web-api/lessons/0001-http-basics.html   骨架空壳页（原样渲染 templates/lesson.html，只为验证模板可渲染）

注意：这里渲染用的是**假数据**，只为了看样式与交互；真实生成器是 Task 13 的 scripts/gen_home.py。
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, '.preview')

# ══════════════════════════════════════════════════════════════════
# 示例数据（假数据，只为预览）
# ══════════════════════════════════════════════════════════════════

SUBJECTS = [
    dict(name='TypeScript Web API', slug='typescript-web-api', status='进行中',
         node='路由', date='2026-09-15', done=3, total=8, mastery=0.62),
    dict(name='线性代数', slug='linear-algebra', status='进行中',
         node='特征值与特征向量', date='2026-09-12', done=5, total=9, mastery=0.58),
    dict(name='日语能力考 N3', slug='japanese-n3', status='暂停',
         node='动词て形', date='2026-08-30', done=4, total=10, mastery=0.41),
    dict(name='木工入门', slug='woodworking', status='已完成',
         node='全部完成', date='2026-07-02', done=6, total=6, mastery=0.88),
]

# id, 标题, 目标, 前置, 状态, 掌握度
NODES = [
    ('http.basics', 'HTTP 基础', '能解释请求/响应报文结构与状态码语义', [], '已通过项目验证', 0.95),
    ('web.service', 'Web 服务', '能用 Node 起一个可访问的 HTTP 服务', ['http.basics'], '能独立应用', 0.82),
    ('web.service.routing', '路由', '能独立设计并实现 REST 路由', ['web.service'], '学习中', 0.45),
    ('web.service.validation', '参数校验', '能对入参做结构化校验并返回清晰错误', ['web.service'], '初步理解', 0.30),
    ('web.service.errors', '错误处理', '能统一错误出口并区分可恢复与不可恢复', ['web.service'], '未开始', 0.0),
    ('http.middleware', '中间件', '能写出可复用的请求中间件', ['web.service.routing'], '未开始', 0.0),
    ('db.access', '数据库访问', '能完成增删改查并解释连接池行为', ['web.service.routing', 'web.service.validation'], '未开始', 0.0),
    ('db.migrations', '数据迁移', '能用迁移脚本管理表结构变更', ['db.access'], '未开始', 0.0),
    ('auth.session', '认证：会话', '能实现基于会话的登录态', ['db.access'], '未开始', 0.0),
    ('auth.token', '认证：令牌', '能实现并校验 JWT', ['db.access'], '未开始', 0.0),
    ('testing.api', '接口测试', '能为接口写集成测试并跑通', ['web.service.routing'], '需要复习', 0.35),
    ('project.api', '毕业项目：完整 API', '独立交付一个可部署的 Web API',
     ['auth.session', 'auth.token', 'testing.api', 'db.migrations'], '未开始', 0.0),
]

STATUS_CLASS = {
    '未开始': 'todo', '学习中': 'learning', '初步理解': 'learning',
    '能独立应用': 'done', '需要复习': 'review', '已通过项目验证': 'verified',
}
STATUS_TAG = {'进行中': ('active', 'blue'), '暂停': ('paused', 'yellow'), '已完成': ('done', 'green')}

MISSION = '独立完成一个可部署的全栈 Web API——从 HTTP 基础一路做到认证、测试与部署。'
PROJECT = '''<div class="learn-project__card">
  <span class="learn-project__label">在做的项目</span>
  <p class="learn-project__current">订单 API 的鉴权与限流</p>
  <div class="learn-project__lists">
    <div>
      <span class="learn-project__sub">已完成</span>
      <ul><li>接口骨架与路由表</li><li>订单 CRUD 与分页</li></ul>
    </div>
    <div>
      <span class="learn-project__sub">待推进</span>
      <ul><li>JWT 鉴权中间件</li><li>按用户限流</li><li>接口集成测试补齐</li></ul>
    </div>
  </div>
</div>'''
PROJECT_NONE = ('<p class="learn-project__none">还没有挂项目。告诉 agent 你想做什么，'
                '它会把项目排进路线图，并把里程碑插成实验课。</p>')

# 节点 → 课件（一个节点挂多篇是有意为之：验证补充课件的子树分叉）
LESSONS = [
    ('0001', 'http-basics', 'HTTP 基础：请求、响应与状态码', 'http.basics'),
    ('0002', 'web-service', '用 Node 起一个能访问的 Web 服务', 'web.service'),
    ('0003', 'routing', '路由：把请求交给正确的处理函数', 'web.service.routing'),
    ('0004', 'validation', '参数校验：让脏数据进不来', 'web.service.validation'),
    ('0005', 'api-testing', '接口测试：先写断言再写实现', 'testing.api'),
    ('0006', 'error-handling', '错误处理：统一出口与日志', 'web.service.errors'),
    ('0007', 'routing-supplement', '路由补充：路径参数与查询参数的取舍', 'web.service.routing'),
]
LESSONS_OF = {}
for _no, _slug, _title, _node in LESSONS:
    LESSONS_OF.setdefault(_node, []).append((_no, _slug, _title))

ATTACH_GROUPS = [
    ('参考文档', [
        ('reference/http-status.html', 'HTTP 状态码速查', 'reference/'),
        ('reference/rest-conventions.html', 'REST 约定速查', 'reference/'),
    ]),
    ('术语与资源', [
        ('GLOSSARY.md', '术语表', 'GLOSSARY.md'),
        ('RESOURCES.md', '资源清单', 'RESOURCES.md'),
    ]),
    ('学习记录', [
        ('learning-records/%04d-demo.md' % i, '学习记录 %04d' % i, 'learning-records/') for i in range(1, 9)
    ]),
    ('会话摘要', [
        ('sessions/2026-09-15.md', '2026-09-15 会话摘要', 'sessions/'),
        ('sessions/2026-09-12.md', '2026-09-12 会话摘要', 'sessions/'),
    ]),
]
ATTACH_EMPTY = ('<p class="learn-attachments__empty">还没有附件。速查文档、术语表、'
                '学习记录都会出现在这里。</p>')

GLYPH = ('<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" '
         'stroke-linecap="round" stroke-linejoin="round"><path d="M10 7.2 4.7 12.6M10 7.2l5.3 5.4"/>'
         '<circle cx="10" cy="5.2" r="2"/><circle cx="4.5" cy="14.5" r="2"/><circle cx="15.5" cy="14.5" r="2"/></svg>')

# ══════════════════════════════════════════════════════════════════
# 渲染：根主页卡片
# ══════════════════════════════════════════════════════════════════

CARD = '''<article class="syo-card learn-subject-card" data-status="{status}" data-progress="{progress:.3f}" data-mastery="{mastery}">
  <a class="learn-subject-card__link" href=".learning/subjects/{slug}/index.html">
    <div class="learn-subject-card__head">
      <h3 class="learn-subject-card__name">{name}</h3>
      <span class="syo-tag learn-subject-card__status learn-status--{kind}">{status}<span class="syo-tag-dot syo-tag-dot--{dot}"></span></span>
    </div>
    <p class="learn-subject-card__current">
      <span class="learn-subject-card__label">当前节点</span>
      <span class="learn-subject-card__value">{node}</span>
    </p>
    <p class="learn-subject-card__meta">上次学习 <time>{date}</time></p>
    <div class="learn-progress">
      <div class="learn-progress__track"><div class="learn-progress__bar" style="width:{pct}%"></div></div>
      <div class="learn-progress__meta">
        <span>{done}/{total} 节点 · 掌握度 {mpct}%</span>
        <span class="learn-subject-card__go" aria-hidden="true">→</span>
      </div>
    </div>
  </a>
</article>'''


def render_cards():
    cards = []
    for s in SUBJECTS:
        kind, dot = STATUS_TAG[s['status']]
        progress = s['done'] / s['total']
        cards.append(CARD.format(
            status=s['status'], kind=kind, dot=dot, progress=progress,
            pct=round(progress * 100, 1), mastery=s['mastery'],
            mpct=round(s['mastery'] * 100), slug=s['slug'], name=s['name'],
            node=s['node'], date=s['date'], done=s['done'], total=s['total']))
    return '<div class="learn-subject-list">\n' + '\n'.join(cards) + '\n</div>'


# ══════════════════════════════════════════════════════════════════
# 渲染：科目页（分层路线图 + 课件子树 + 附件）
# ══════════════════════════════════════════════════════════════════

def _levels():
    """按 prerequisites 算最长路径层级（真实实现同理，见模板里的生成器规范）。"""
    prereq = {n[0]: n[3] for n in NODES}
    depth = {}

    def level_of(nid):
        if nid not in depth:
            ps = prereq[nid]
            depth[nid] = 0 if not ps else 1 + max(level_of(p) for p in ps)
        return depth[nid]

    for n in NODES:
        level_of(n[0])

    out = {}
    for nid, d in depth.items():
        out.setdefault(d, []).append(nid)
    return out


def _node_card(nid):
    _, title, obj, prereq, status, mastery = next(n for n in NODES if n[0] == nid)
    cls = STATUS_CLASS[status]
    pct = int(mastery * 100)
    now = '<span class="learn-node__now">当前</span>' if status == '学习中' else ''
    titles = {n[0]: n[1] for n in NODES}
    chips = (''.join('<span class="learn-node__chip">%s</span>' % titles[p] for p in prereq)
             or '<span class="learn-node__chip learn-node__chip--none">无</span>')
    objective = '<span class="learn-node__objective">%s</span>' % obj
    foot = ('<span class="learn-node__foot">'
            '<span class="learn-node__prereq">前置 %s</span>'
            '<span class="learn-node__mastery"><i style="width:%d%%"></i></span>'
            '<span class="learn-node__pct">%d%%</span></span>' % (chips, pct, pct))

    lessons = LESSONS_OF.get(nid)
    if lessons:
        row = ('<span class="learn-node__row"><span class="learn-node__dot"></span>'
               '<span class="learn-node__title">%s</span>%s'
               '<span class="learn-node__status">%s</span>'
               '<span class="learn-node__caret" aria-hidden="true"></span></span>'
               % (title, now, status))
        items = '\n'.join(
            '''        <a class="learn-child" href="lessons/%s-%s.html">
          <span class="learn-child__dot" aria-hidden="true"></span>
          <span class="learn-child__no">%s</span>
          <span class="learn-child__title">%s</span>
        </a>''' % (no, slug, no, ltitle) for no, slug, ltitle in lessons)
        return f'''<details class="learn-slot" data-id="{nid}">
  <summary class="learn-node learn-node--{cls} learn-node--expandable">
    {row}
    {objective}
    {foot}
  </summary>
  <div class="learn-node__children">
{items}
  </div>
</details>'''
    row = ('<span class="learn-node__row"><span class="learn-node__dot"></span>'
           '<span class="learn-node__title">%s</span>%s'
           '<span class="learn-node__nolesson">课件待生成</span></span>' % (title, now))
    return f'''<article class="learn-node learn-node--{cls}">
  {row}
  {objective}
  {foot}
</article>'''


def render_roadmap():
    levels = _levels()
    blocks = []
    for level in sorted(levels):
        cards = '\n'.join(_node_card(nid) for nid in levels[level])
        blocks.append(f'''  <div class="learn-level">
    <div class="learn-level__rail"><span class="learn-level__dot"></span></div>
    <div class="learn-level__body">
      <div class="learn-level__label">第 {level + 1} 层 · {len(levels[level])} 个知识点</div>
      <div class="learn-level__grid">
{cards}
      </div>
    </div>
  </div>''')
    return '<div class="learn-roadmap">\n' + '\n'.join(blocks) + '\n</div>'


def render_attachments():
    groups = []
    for label, items in ATTACH_GROUPS:
        if not items:
            continue
        rows = '\n'.join(
            '''      <a class="learn-attachment" href="%s">
        <span class="learn-attachment__title">%s</span>
        <span class="learn-attachment__meta">%s</span>
      </a>''' % (href, title, meta) for href, title, meta in items)
        groups.append(f'''  <div class="learn-attachments__group">
    <div class="learn-attachments__label">{label}</div>
{rows}
  </div>''')
    return '\n'.join(groups)


def render_subject(template, slug='typescript-web-api', empty=False):
    kind, dot = STATUS_TAG['进行中']
    status = ('<span class="syo-tag learn-status learn-status--%s">进行中'
              '<span class="syo-tag-dot syo-tag-dot--%s"></span></span>' % (kind, dot))
    html = template
    html = html.replace('<!-- @LEARN:TITLE -->', 'TypeScript Web API' if not empty else '新科目')
    html = html.replace('<!-- @LEARN:STATUS -->', status)
    html = html.replace('<!-- @LEARN:MISSION -->', MISSION if not empty else '还没写使命。')
    html = html.replace('<!-- @LEARN:PROJECT -->', PROJECT_NONE if empty else PROJECT)
    html = html.replace('<!-- @LEARN:ROADMAP -->', '' if empty else render_roadmap())
    html = html.replace('<!-- @LEARN:ATTACHMENTS -->', ATTACH_EMPTY if empty else render_attachments())
    return html


# ══════════════════════════════════════════════════════════════════
# 课件页：预览渲染的是骨架空壳页（templates/lesson.html 原样拷贝），只验证模板可渲染。
# 课件层的组件示例（Sayo 编辑区 + 练习 + 提示块 + 资源 + 提问提示）在骨架注释里，不在预览页上。
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)

    assets = os.path.join(OUT, '.learning', 'assets')
    os.makedirs(assets)
    subject = os.path.join(OUT, '.learning', 'subjects', 'typescript-web-api')
    os.makedirs(os.path.join(subject, 'lessons'))
    os.makedirs(os.path.join(subject, 'assets'))

    # 模拟 install/生成流程：共享层放 .learning/assets/（一份）。
    # 清单必须与 templates/assets/README.md 一致——新增共享文件时两处都要加
    src_assets = os.path.join(ROOT, 'templates', 'assets')
    shared_files = ('learn-theme.css', 'learn-theme.js')
    shared_dirs = ('sayo',)
    for name in shared_files:
        shutil.copy(os.path.join(src_assets, name), assets)
    for name in shared_dirs:
        shutil.copytree(os.path.join(src_assets, name), os.path.join(assets, name))

    # 模拟 Task 8 建科目：课件层组件拷进科目 assets/（每科目一份）
    for name in ('style.css', 'quiz.js'):
        shutil.copy(os.path.join(src_assets, name), os.path.join(subject, 'assets', name))

    home = open(os.path.join(ROOT, 'templates', 'home-index.html'), encoding='utf-8').read()
    subj = open(os.path.join(ROOT, 'templates', 'subject-index.html'), encoding='utf-8').read()
    # 课件页直接从骨架拷过来（原样渲染）：预览里看到的是空壳，组件示例在骨架的注释里
    lesson = open(os.path.join(ROOT, 'templates', 'lesson.html'), encoding='utf-8').read()

    outputs = {
        os.path.join(OUT, 'index.html'): home.replace('<!-- @LEARN:SUBJECT_CARDS -->', render_cards(), 1),
        os.path.join(OUT, 'index-empty.html'): home.replace(
            '<!-- @LEARN:SUBJECT_CARDS -->', '<div class="learn-subject-list"></div>', 1),
        os.path.join(subject, 'index.html'): render_subject(subj),
        os.path.join(subject, 'empty.html'): render_subject(subj, empty=True),
        os.path.join(subject, 'lessons', '0001-http-basics.html'): lesson,
    }
    for path, content in outputs.items():
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    print('预览已生成（.preview/ 不进仓库）：')
    for path in outputs:
        print('  ', path)
    print()
    print('打开方式：')
    print('  xdg-open %s   # 或用浏览器打开这个文件' % os.path.join(OUT, 'index.html'))
    print('  切暗色：在地址栏 URL 后加 ?theme=dark')

    if '--open' in sys.argv[1:]:
        opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
        try:
            subprocess.run([opener, os.path.join(OUT, 'index.html')], check=False)
        except FileNotFoundError:
            print('（找不到 %s，请手动打开上面的文件）' % opener)


if __name__ == '__main__':
    main()
