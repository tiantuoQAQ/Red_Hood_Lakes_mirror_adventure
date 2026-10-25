# -*- coding: utf-8 -*-
"""把 GPT 台词修订建议应用到 src/story.js（只替换唯一匹配的句子），再重导 JSON。

用法：python tools/apply_dialogue_fixes.py [--dry]
"""
import io
import re
import sys

SRC = 'src/story.js'
DOC = 'docs/design/台词修订建议.md'
dry = '--dry' in sys.argv


def rows():
    text = io.open(DOC, encoding='utf-8').read().splitlines()
    out = []
    for line in text:
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) < 4:
            continue
        if cells[0] in ('章节', '---') or set(cells[0]) <= set('- '):
            continue
        out.append((cells[0], cells[1], cells[3]))
    return out


def main():
    s = io.open(SRC, encoding='utf-8').read()
    applied, skipped = [], []
    for chapter, old, new in rows():
        if not old or not new or old == new:
            continue
        cnt = s.count(old)
        if cnt == 1:
            s = s.replace(old, new, 1)
            applied.append((chapter, old, new))
        else:
            skipped.append((chapter, old, cnt))
    if not dry:
        io.open(SRC, 'w', encoding='utf-8').write(s)
    print('应用 %d 条，跳过 %d 条（非唯一匹配）' % (len(applied), len(skipped)))
    for c, o, n in applied:
        print('  [%s] %s -> %s' % (c, o[:18], n[:18]))
    for c, o, cnt in skipped[:10]:
        print('  SKIP[%s] x%d %s' % (c, cnt, o[:20]))


if __name__ == '__main__':
    main()
