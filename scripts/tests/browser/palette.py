#!/usr/bin/env python3
"""亮色令牌对比度核算 + 给出达标取值（保留色相，只压明度）。"""
import colorsys


def hex2rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(rgb):
    return '#' + ''.join(f'{max(0, min(255, round(v))):02x}' for v in rgb)


def lum(rgb):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(fg, bg):
    l1, l2 = lum(fg), lum(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def darken_to(fg_hex, bg_hex, target=4.6):
    """保留 H/S，按比例压 L，直到达标；返回 (新 hex, 实际对比度, 明度系数)。"""
    h, l, s = colorsys.rgb_to_hls(*[v / 255 for v in hex2rgb(fg_hex)])
    bg = hex2rgb(bg_hex)
    k = 1.0
    while k > 0.2:
        rgb = tuple(v * 255 for v in colorsys.hls_to_rgb(h, l * k, s))
        if ratio(rgb, bg) >= target:
            return rgb2hex(rgb), round(ratio(rgb, bg), 2), round(k, 3)
        k -= 0.005
    return fg_hex, round(ratio(hex2rgb(fg_hex), bg), 2), 1.0


CASES = [
    # (用途, 令牌, 当前亮色值, 实际背景)
    ('语法·注释 / 编辑器行号', '--syo-syn-comment', '#8a8478', '#ffffff'),
    ('语法·关键字', '--syo-syn-keyword', '#a4462f', '#ffffff'),
    ('语法·字符串', '--syo-syn-string', '#2f6b4f', '#ffffff'),
    ('语法·函数名', '--syo-syn-func', '#6b5b8a', '#ffffff'),
    ('语法·类型', '--syo-syn-type', '#8a5a1f', '#ffffff'),
    ('语法·预处理/宏', '--syo-syn-macro', '#9a7420', '#ffffff'),
    ('语法·运算符', '--syo-syn-operator', '#2c6f8f', '#ffffff'),
    ('语法·数字', '--syo-syn-number', '#2c6f8f', '#ffffff'),
    ('提示卡标签', '--syo-green（.lesson-tip>b）', '#2f7d5f', '#e3e9e2'),
    ('误区卡标签', '--syo-yellow（.lesson-warn>b）', '#9a7420', '#eee4d1'),
    ('状态标签·进行中', '--learn-learning', '#3a7ca5', '#f7f5f0'),
    ('状态标签·待复习', '--learn-review', '#c08a2d', '#f7f5f0'),
    ('状态标签·已完成', '--learn-done', '#2f7d5f', '#f7f5f0'),
    ('状态标签·已验证', '--learn-verified', '#1c5a40', '#f7f5f0'),
    ('状态标签·未开始', '--learn-todo', '#b3ac9d', '#f7f5f0'),
    ('正文次要文字', '--syo-fg-muted', '#6b665c', '#ffffff'),
]

print(f'{"用途":<22}{"令牌":<34}{"现值":<10}{"对比度":<8}{"建议值":<10}{"新对比度"}')
for label, token, cur, bg in CASES:
    r0 = ratio(hex2rgb(cur), hex2rgb(bg))
    new, r1, k = darken_to(cur, bg)
    flag = 'OK ' if r0 >= 4.5 else ' ✗ '
    print(f'{label:<22}{token:<34}{cur:<10}{r0:>5.2f}{flag} {new:<10}{r1:>5.2f}  (L×{k})')
