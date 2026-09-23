#!/usr/bin/env python3
"""生成线性代数图片库的示意图（本机生成，只用标准库 + Pillow）。

用法（从科目目录运行）：
    python3 assets/img/gen/linear-algebra-diagrams.py

产出三张 PNG 到 assets/img/pool/，索引见 assets/img/pool.md。
配色按浅色底设计，线宽足够在 1x 屏幕上直接看。
"""
import os
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'
OUT = os.path.join('assets', 'img', 'pool')

INK = (28, 32, 38)          # 主线条与文字
ACCENT = (196, 62, 52)      # 强调（结果、目标向量）
MUTED = (150, 156, 164)     # 网格与辅助线


def font(size):
    return ImageFont.truetype(FONT, size)


def canvas(w, h):
    img = Image.new('RGB', (w, h), (252, 252, 250))
    return img, ImageDraw.Draw(img)


def arrow(draw, p, q, color=INK, width=3, head=9):
    """从 p 到 q 画一支带箭头的线。"""
    draw.line([p, q], fill=color, width=width)
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = max((dx * dx + dy * dy) ** 0.5, 1e-6)
    ux, uy = dx / length, dy / length
    left = (q[0] - head * ux - head * 0.5 * uy, q[1] - head * uy + head * 0.5 * ux)
    right = (q[0] - head * ux + head * 0.5 * uy, q[1] - head * uy - head * 0.5 * ux)
    draw.polygon([q, left, right], fill=color)


def diagram_column_combination():
    """列向量的线性组合：x·(2,1) + y·(1,-1) 拼出 (4,-1) 的平行四边形。"""
    img, d = canvas(560, 420)
    origin = (120, 250)
    scale = 55

    def to_px(v):
        return (origin[0] + v[0] * scale, origin[1] - v[1] * scale)

    # 坐标轴
    d.line([(60, origin[1]), (520, origin[1])], fill=MUTED, width=1)
    d.line([(origin[0], 40), (origin[0], 380)], fill=MUTED, width=1)

    a, b, target = (2, 1), (1, -1), (4, -1)
    pa, pb, pt = to_px(a), to_px(b), to_px(target)

    # 平行四边形的辅助边（先画，压在主干线下面）
    arrow(d, origin, pb, MUTED, 2, head=7)
    arrow(d, pb, pt, MUTED, 2, head=7)

    # x·(2,1)：从原点到 pa；y·(1,-1)：从 pa 首尾相接
    arrow(d, origin, pa, INK, 3)
    arrow(d, pa, pt, INK, 3)
    # 结果向量
    arrow(d, origin, pt, ACCENT, 3)

    d.text((152, 200), '1 · (2, 1)', font=font(17), fill=INK)
    d.text((252, 244), '+ 2 · (1, −1)', font=font(17), fill=INK)
    d.text((340, 300), '(4, −1)', font=font(18), fill=ACCENT)
    d.text((150, 348), '2 · (1, −1)', font=font(15), fill=MUTED)

    d.text((70, 20), '解方程组 = 用两个列向量拼出右端向量', font=font(17), fill=INK)
    d.text((70, 396), 'x·(2,1) + y·(1,−1) = (4,−1) 在 x = 1、y = 2 时成立', font=font(15), fill=MUTED)
    return img


def diagram_shear_grid():
    """斜切变换：单位网格被拉成平行四边形网格，e₁ 不动、e₂ 向右倒。"""
    img, d = canvas(620, 400)
    origin = (110, 265)
    unit = 62
    columns, rows = 6, 4

    def to_px(v):
        return (origin[0] + v[0] * unit, origin[1] - v[1] * unit)

    def shear(v):
        return (v[0] + 0.5 * v[1], v[1])

    # 变换前的网格（淡）
    for i in range(columns + 1):
        d.line([to_px((i, 0)), to_px((i, rows))], fill=(214, 218, 224), width=1)
    for j in range(rows + 1):
        d.line([to_px((0, j)), to_px((columns, j))], fill=(214, 218, 224), width=1)

    # 变换后的网格（被拉斜的实线）
    for i in range(columns + 1):
        d.line([to_px(shear((i, 0))), to_px(shear((i, rows)))], fill=INK, width=2)
    for j in range(rows + 1):
        d.line([to_px(shear((0, j))), to_px(shear((columns, j)))], fill=INK, width=2)

    # 基向量的像
    arrow(d, origin, to_px(shear((1, 0))), ACCENT, 3)
    arrow(d, origin, to_px(shear((0, 1))), (38, 92, 160), 3)
    d.text((to_px(shear((1, 0)))[0] - 8, to_px(shear((1, 0)))[1] + 10),
           'e1 不动', font=font(16), fill=ACCENT)
    d.text((to_px(shear((0, 1)))[0] - 84, to_px(shear((0, 1)))[1] - 6),
           'e2 向右倒', font=font(16), fill=(38, 92, 160))

    d.text((60, 20), '斜切变换：网格被拉斜，直线仍是直线、原点不动', font=font(17), fill=INK)
    d.text((60, 372), '矩阵的列就是 e1、e2 的新落点：网格的每条线仍是直线', font=font(15), fill=MUTED)
    return img


def diagram_three_cases():
    """三种解：交于一点、平行无交点、同一条直线上无穷多点。"""
    img, d = canvas(720, 330)
    unit = 34

    panels = [('唯一解：两条线交于一点', 130), ('无解：两条线平行', 360), ('无穷多解：同一条线', 590)]

    def make_mapper(cx, cy):
        def to_px(v):
            return (cx + v[0] * unit, cy - v[1] * unit)
        return to_px

    for title, cx in panels:
        cy = 175
        to_px = make_mapper(cx, cy)
        d.line([(cx - 105, cy), (cx + 105, cy)], fill=MUTED, width=1)
        d.line([(cx, cy - 110), (cx, cy + 95)], fill=MUTED, width=1)
        d.text((cx - 95, 30), title, font=font(16), fill=INK)

    # 面板一：x + y = 4 与 x − y = 0，交于 (2, 2)
    to_px = make_mapper(130, 175)
    d.line([to_px((-1, 5)), to_px((5, -1))], fill=INK, width=2)
    d.line([to_px((-2.4, -2.4)), to_px((2.4, 2.4))], fill=(38, 92, 160), width=2)
    point = to_px((2, 2))
    d.ellipse([point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5], fill=ACCENT)
    d.text((point[0] + 8, point[1] - 26), '(2, 2)', font=font(15), fill=ACCENT)

    # 面板二：x + 2y = 1 与 x + 2y = 3，平行
    to_px = make_mapper(360, 175)
    d.line([to_px((-2, 1.5)), to_px((3, -1))], fill=INK, width=2)
    d.line([to_px((-2, 2.5)), to_px((3, 0))], fill=(38, 92, 160), width=2)
    d.text((360 - 92, 232), '斜率相同、截距不同', font=font(14), fill=MUTED)

    # 面板三：x + 2y = 1 上的三个点
    to_px = make_mapper(590, 175)
    d.line([to_px((-2, 1.5)), to_px((3, -1))], fill=INK, width=2)
    for t in (0, 0.55, 1):
        point = to_px((1 - 2 * t, t))
        d.ellipse([point[0] - 4, point[1] - 4, point[0] + 4, point[1] + 4], fill=ACCENT)
    d.text((590 - 96, 232), '同一个方向上的所有点', font=font(14), fill=MUTED)

    d.text((40, 296), '消元后只看两件事：有没有矛盾行、主元够不够', font=font(15), fill=MUTED)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    items = {
        '线性代数-向量-列向量拼出右端向量-本机-01.png': diagram_column_combination(),
        '线性代数-矩阵-斜切变换前后网格对比-本机-02.png': diagram_shear_grid(),
        '线性代数-消元-三种解的情形对照-本机-03.png': diagram_three_cases(),
    }
    for name, image in items.items():
        path = os.path.join(OUT, name)
        image.save(path)
        print(f'{path}  {os.path.getsize(path)} B  {image.size[0]}x{image.size[1]}')


if __name__ == '__main__':
    main()
