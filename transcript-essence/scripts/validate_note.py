#!/usr/bin/env python3
"""Validate the fixed note hierarchy; not a semantic or UI test. Standard library only."""
import argparse
import re
import sys
from pathlib import Path

SECTIONS = ['1. 内容主线', '2. 核心认知', '3. 关键区分', '4. 自查问题', '5. 原文摘录', '6. 一句提醒']

def validate(text):
    errors, headings = [], []
    fence = None
    previous_line = ''
    visible_lines = []
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r'^\s{0,3}(`{3,}|~{3,})(.*)$', line)
        if match:
            marker, rest = match.groups()
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not rest.strip():
                fence = None
            continue
        if fence:
            previous_line = ''
            continue
        visible_lines.append((number, line))
        match = re.match(r'^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$', line)
        if match:
            headings.append((number, len(match[1]), match[2]))
        elif re.match(r'^ {0,3}(=+|-+)\s*$', line) and previous_line.strip() and not re.match(r'^\s*(?:#{1,6}\s|>|[-*+]\s|`{3,}|~{3,})', previous_line):
            errors.append(f'L{number}: Setext 标题不属于固定 ATX 模板，请转换层级')
        previous_line = line
    if fence:
        errors.append('代码围栏未闭合')
    h1 = [h for h in headings if h[1] == 1]
    if len(h1) != 1 or not headings or headings[0][1] != 1:
        errors.append('需要且仅有一个最前方 H1')
    elif len(h1[0][2]) > 16:
        errors.append('标题超过默认16字符上限（明确用户命名可人工豁免）')
    h2 = [h for h in headings if h[1] == 2]
    if [h[2] for h in h2] != ['原文', '精华笔记']:
        errors.append('H2 必须依次且仅有：原文、精华笔记')
    if len(h2) == 2 and h2[1][2] == '精华笔记':
        boundary = h2[1][0]
        essence = '\n'.join(text.splitlines()[boundary:])
        actual = [h[2] for h in headings if h[0] > boundary and h[1] == 3]
        if actual != SECTIONS:
            errors.append('精华区六个 H3 的名称或顺序不匹配')
        if re.search(r'^\s{0,3}(?:`{3,}|~{3,})\s*mermaid\b|本次只落实三件事|^\s*[-*+] \[[ xX]\]', essence, re.M):
            errors.append('精华区含默认禁止的关系图或任务清单')
        visible_essence = '\n'.join(line for number, line in visible_lines if number > boundary)
        callouts = re.findall(r'^> \[!([^\]]+)\] (.+)$', visible_essence, re.M)
        all_callouts = re.findall(r'^\s*>.*\[![^\]]+\]', visible_essence, re.M)
        preamble = visible_essence.split('### 1.', 1)[0]
        if (callouts != [('abstract', '一句话提炼'), ('info', '阅读边界')]
                or len(all_callouts) != 2
                or len(re.findall(r'^> \[!', preamble, re.M)) != 2):
            errors.append('需要且仅有两个固定 callout，置于六节之前：摘要与阅读边界')
        for index, (number, line) in enumerate(visible_lines):
            if number > boundary and line.startswith('> [!'):
                if index and visible_lines[index-1][1].strip():
                    errors.append(f'L{number}: callout 之前需要空行，避免引用块合并')
        if any(h[1] > 4 for h in headings if h[0] > boundary):
            errors.append('精华区不能使用 H5/H6')
        for i, heading in enumerate(headings):
            if heading[0] <= boundary or heading[1] != 4:
                continue
            prior = [h for h in headings[:i] if h[1] == 3]
            if not prior or prior[-1][2] != '2. 核心认知':
                errors.append(f'L{heading[0]}: 默认模板仅核心认知使用 H4')
                continue
            end = next((h[0]-1 for h in headings[i+1:] if h[1] <= 4), len(text.splitlines()))
            block = '\n'.join(line for number, line in visible_lines if heading[0] < number <= end)
            for field in ['原文要点', '理解', '应用', '边界']:
                if f'**{field}：**' not in block:
                    errors.append(f'L{heading[0]}: 缺少字段 {field}')
        if not any(h[1] == 4 and h[0] > boundary for h in headings):
            core = essence.split('### 2. 核心认知', 1)[-1].split('### 3.', 1)[0]
            if '材料有限：没有足够依据提炼独立观点。' not in core:
                errors.append('核心认知需要有依据的条目，或明确的材料有限声明')
    previous = 0
    for number, level, title in headings:
        if level > previous + 1:
            errors.append(f'L{number}: 标题跳级 H{previous}→H{level}')
        previous = level
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('note', type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.note.read_text(encoding='utf-8'))
    except (OSError, UnicodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    if errors:
        print('\n'.join('FAIL: '+error for error in errors))
        return 1
    print('PASS: fixed note structure (semantic fidelity and client folding require separate checks)')
    return 0

if __name__ == '__main__':
    sys.exit(main())
