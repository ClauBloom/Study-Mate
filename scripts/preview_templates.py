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
    .preview/.learning/subjects/typescript-web-api/lessons/0001-http-basics.html   示例课件

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
  <span class="learn-project__label">当前项目里程碑</span>
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
                '它会把里程碑挂到这条路线图上。</p>')

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
# 示例课件（验证课件层：Sayo 编辑区 + 练习 + 提示块 + 资源 + 提问提示）
# ══════════════════════════════════════════════════════════════════

SAMPLE_LESSON = '''<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HTTP 基础：请求、响应与状态码 · TypeScript Web API</title>
<link rel="stylesheet" href="../../../assets/sayo/sayo.css">
<link rel="stylesheet" href="../../../assets/learn-theme.css">
<link rel="stylesheet" href="../assets/style.css">
<script>
  (function () {
    var q = null, saved = null;
    try { q = new URLSearchParams(window.location.search).get('theme'); } catch (e) {}
    try { saved = localStorage.getItem('le-theme'); } catch (e) {}
    if (q === 'dark' || q === 'light') document.documentElement.setAttribute('data-theme', q);
    else if (saved === 'dark' || saved === 'light') document.documentElement.setAttribute('data-theme', saved);
  })();
</script>
</head>
<body class="lesson-body">

<nav class="lesson-bar">
  <a href="../index.html">← 返回课程</a>
  <span>HTTP 基础</span>
  <span class="lesson-bar__no">0001</span>
</nav>

<article class="lesson">
  <header class="lesson-header">
    <span class="lesson-header__eyebrow">0001 · 所属节点：HTTP 基础</span>
    <h1>HTTP 基础：请求、响应与状态码</h1>
    <p class="lesson-goal"><b>本节目标：</b>能说清一次请求从浏览器发出到服务端返回的完整路径，并读懂常见状态码到底在说什么。</p>
  </header>

  <h2>先看一个麻烦</h2>
  <p>你在地址栏敲下回车，页面就出来了。中间发生了什么？如果只会写 <code>app.get('/orders')</code>，那么接口一 404、一 401，你就只能靠猜——因为不知道"请求"和"响应"这两样东西到底长什么样。</p>
  <p>先记住一件事：<strong>浏览器和服务端之间来回传的，是纯文本</strong>。看懂这段文本，排错就有据可依。</p>

  <h2>一次请求长什么样</h2>
  <p>用 <code>curl -v</code> 打开开关，你就能看到原始的请求与响应。请求头部分长这样：</p>

  <div class="syo-editor">
    <div class="syo-editor-titlebar">
      <span class="syo-editor-dots">
        <span class="syo-editor-dot syo-editor-dot--red"></span>
        <span class="syo-editor-dot syo-editor-dot--yellow"></span>
        <span class="syo-editor-dot syo-editor-dot--green"></span>
      </span>
      <span class="syo-editor-filename">request.http</span>
    </div>
    <div class="syo-editor-body">
      <div class="syo-editor-gutter"><span>1</span><span>2</span><span>3</span><span>4</span></div>
      <div class="syo-editor-code">
        <span class="line"><span class="syn-keyword">GET</span> /orders/42 <span class="syn-operator">HTTP/1.1</span></span>
        <span class="line"><span class="syn-type">Host</span>: api.example.com</span>
        <span class="line"><span class="syn-type">Authorization</span>: Bearer eyJhbGciOi...</span>
        <span class="line"><span class="syn-type">Accept</span>: application/json</span>
      </div>
    </div>
  </div>

  <p>三件事值得注意：</p>
  <ul>
    <li><strong>方法 + 路径</strong>（<code>GET /orders/42</code>）决定"要什么"</li>
    <li><strong>请求头</strong>是元信息：我是谁、我要什么格式、我接受什么压缩</li>
    <li>带 body 的方法（POST/PUT/PATCH）才有请求体，GET 通常没有</li>
  </ul>

  <div class="lesson-tip">
    <b>小技巧</b>
    <p>排错时先看请求头和响应头，再怀疑业务代码。绝大多数"接口不通"是头写错了：少了 <code>Content-Type</code>、token 过期、跨域预检没过。</p>
  </div>

  <h2>状态码在说什么</h2>
  <table>
    <thead><tr><th>状态码</th><th>含义</th><th>你该做什么</th></tr></thead>
    <tbody>
      <tr><td><code>200</code></td><td>成功，返回了内容</td><td>解析响应体</td></tr>
      <tr><td><code>201</code></td><td>创建成功</td><td>通常带 <code>Location</code> 头指向新资源</td></tr>
      <tr><td><code>400</code></td><td>请求本身有问题</td><td>检查参数、body 格式</td></tr>
      <tr><td><code>401</code></td><td>没认证 / 认证失败</td><td>检查 token 有没有带上、是否过期</td></tr>
      <tr><td><code>404</code></td><td>资源不存在</td><td>检查路径与资源 id</td></tr>
      <tr><td><code>500</code></td><td>服务端自己炸了</td><td>看服务端日志，不是客户端问题</td></tr>
    </tbody>
  </table>

  <div class="lesson-warn">
    <b>常见误区</b>
    <p>把 401 和 403 混为一谈：<code>401</code> 是"你没证明你是谁"，<code>403</code> 是"我知道你是谁，但你没权限"。前者补凭证，后者找管理员。</p>
  </div>

  <h2>练一下</h2>
  <div class="quiz" data-quiz='[
    {"q":"客户端发来 POST /orders，服务端成功创建订单，最合适的状态码是？","opts":["200 OK","201 Created","204 No Content"],"ans":1,"why":"新建资源用 201，并用 Location 头指向新资源；204 表示成功但没有响应体。"},
    {"q":"浏览器控制台报 401，最可能的原因是？","opts":["路由路径写错了","请求头里的凭证缺失或过期","服务端代码抛了异常"],"ans":1,"why":"401 是认证问题：凭证没带上、格式不对或已过期；路径错通常是 404。"}
  ]'></div>

  <div class="lesson-practice">
    <div class="lesson-practice__head">
      <span class="lesson-practice__level">L2 改造</span>
      <h3 class="lesson-practice__title">把一次 404 改成 200</h3>
    </div>
    <p>在你自己的项目里挑一个返回 404 的接口，用 <code>curl -v</code> 打出原始请求，找出路径或方法哪里不对，改到返回 200。</p>
  </div>

  <h2>参考资料</h2>
  <ul class="lesson-resources">
    <li><a href="https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Messages" target="_blank" rel="noreferrer">MDN · HTTP 消息</a>
      <span class="lesson-resources__meta">官方文档 · 请求与响应报文结构的权威说明</span></li>
    <li><a href="https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status" target="_blank" rel="noreferrer">MDN · HTTP 状态码</a>
      <span class="lesson-resources__meta">官方文档 · 状态码速查，排错时常看</span></li>
  </ul>

  <div class="lesson-ask">
    <b>没看懂？随时问</b>
    把看不懂的段落（或报错）原样复制回会话，前后加 <code>【提问】…【/提问】</code> 标记，我会只解释这一段，不打断你的进度。
  </div>

  <footer class="lesson-footer">Learn-everything · 0001 HTTP 基础 · 本地学习工作区</footer>
</article>

<script src="../../../assets/sayo/sayo.js"></script>
<script src="../assets/quiz.js" defer></script>
</body>
</html>
'''

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

    # 模拟 install/生成流程：共享层放 .learning/assets/（一份）
    src_assets = os.path.join(ROOT, 'templates', 'assets')
    shutil.copytree(os.path.join(src_assets, 'sayo'), os.path.join(assets, 'sayo'))
    shutil.copy(os.path.join(src_assets, 'learn-theme.css'), assets)

    # 模拟 Task 8 建科目：课件层组件拷进科目 assets/（每科目一份）
    for name in ('style.css', 'quiz.js'):
        shutil.copy(os.path.join(src_assets, name), os.path.join(subject, 'assets', name))

    home = open(os.path.join(ROOT, 'templates', 'home-index.html'), encoding='utf-8').read()
    subj = open(os.path.join(ROOT, 'templates', 'subject-index.html'), encoding='utf-8').read()

    outputs = {
        os.path.join(OUT, 'index.html'): home.replace('<!-- @LEARN:SUBJECT_CARDS -->', render_cards(), 1),
        os.path.join(OUT, 'index-empty.html'): home.replace(
            '<!-- @LEARN:SUBJECT_CARDS -->', '<div class="learn-subject-list"></div>', 1),
        os.path.join(subject, 'index.html'): render_subject(subj),
        os.path.join(subject, 'empty.html'): render_subject(subj, empty=True),
        os.path.join(subject, 'lessons', '0001-http-basics.html'): SAMPLE_LESSON,
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
