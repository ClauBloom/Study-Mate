#!/usr/bin/env python3
"""StudyMate 亮暗主题审计：找出「只对单一主题成立」的颜色用法。

判据（三类）：
  A. 硬编码颜色字面量（hex / rgb / hsl）出现在「非令牌定义块」里
     → 令牌定义块允许有字面量（那正是它的职责）
  B. 只在 html[data-theme="light"] 下定义的规则里含字面量
     → 暗色下会退回上游/无样式
  C. 通用选择器（无主题前缀）里含暗色专用字面量（深色阴影、深色底）
     → 亮色下不可见或显脏；反之亦然

输出：按文件分组的清单，每条带行号与原文，供人工判断。
"""
import re
import sys
import os

FILES = [
    'workspace/.learning/assets/learn-theme.css',
    'workspace/.learning/subjects/cpp-algorithms/assets/style.css',
    'templates/assets/learn-theme.css',
    'templates/assets/style.css',
    'templates/home-index.html',
    'templates/subject-index.html',
    'templates/lesson.html',
]

HEX = re.compile(r'#[0-9a-fA-F]{3,8}\b')
RGB = re.compile(r'\brgba?\(\s*\d+[^)]*\)')
HSL = re.compile(r'\bhsla?\(\s*\d+[^)]*\)')
NAMED = re.compile(r'(?<![\w-])(white|black|silver|gray|grey)(?![\w-])')

# 令牌定义块：:root { ... } 或 html[data-theme="..."] { ... }（整块都是定义）
TOKEN_BLOCK = re.compile(r'(:root|html\[data-theme="(?:light|dark)"\])\s*\{[^}]*\}', re.S)


def strip_comments(text):
    return re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group(0).count('\n'), text, flags=re.S)


def scan(path):
    raw = open(path, encoding='utf-8').read()
    text = strip_comments(raw)
    # 标记所有「令牌定义块」的区间，这些区间内的字面量是合法的
    token_spans = [(m.start(), m.end()) for m in TOKEN_BLOCK.finditer(text)]

    def in_token_block(pos):
        return any(a <= pos < b for a, b in token_spans)

    findings = []
    # 逐行累加偏移量。**不要**用 text.find(line) 反查位置：完全相同的行（CSS 里很常见）
    # 会一律解析到第一次出现的位置，于是第二次起若在令牌块外也会被误判为「块内」而漏报。
    offset = 0
    for lineno, line in enumerate(text.splitlines(keepends=True), 1):
        for label, rx in (('hex', HEX), ('rgb', RGB), ('hsl', HSL), ('named', NAMED)):
            for m in rx.finditer(line):
                if in_token_block(offset + m.start()):
                    continue
                findings.append((lineno, label, m.group(0), line.strip()))
        offset += len(line)
    return findings


def theme_context(text, lineno):
    """判断某行处于哪种主题上下文：返回 'light-only' / 'dark-only' / 'both'。"""
    lines = text.splitlines()
    # 往上找最近的选择器行（以 { 结尾或含 { ）
    for i in range(lineno - 1, -1, -1):
        s = lines[i].strip()
        if 'html[data-theme="light"]' in s:
            return 'light-only'
        if 'html[data-theme="dark"]' in s:
            return 'dark-only'
        if '{' in s or '}' in s:
            return 'both'
    return 'both'


def main():
    total = 0
    for path in FILES:
        if not os.path.exists(path):
            continue
        raw = open(path, encoding='utf-8').read()
        findings = scan(path)
        if not findings:
            print(f'\n=== {path} ===\n  无非令牌颜色字面量 ✓')
            continue
        print(f'\n=== {path}（{len(findings)} 处）===')
        for lineno, label, value, line in findings:
            ctx = theme_context(strip_comments(raw), lineno)
            tag = {'light-only': '仅亮色', 'dark-only': '仅暗色', 'both': '两主题'}[ctx]
            print(f'  L{lineno:<4} [{tag}] {label}: {value}')
            print(f'         {line[:110]}')
            total += 1
    print(f'\n合计 {total} 处待人工判断')


if __name__ == '__main__':
    main()
