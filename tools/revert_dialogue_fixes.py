# -*- coding: utf-8 -*-
"""把 GPT 那批台词修订整体回滚（保留后续用户要求的改动：诺登动机/名字揭示/删勇者卡/黑影缓冲）。"""
import io

SRC = 'src/story.js'
DOC = 'docs/design/台词修订建议.md'

s = io.open(SRC, encoding='utf-8').read()
rows = []
for line in io.open(DOC, encoding='utf-8').read().splitlines():
    if not line.startswith('|'):
        continue
    cells = [c.strip() for c in line.strip('|').split('|')]
    if len(cells) < 4 or cells[0] in ('章节', '---') or set(cells[0]) <= set('- '):
        continue
    rows.append((cells[0], cells[1], cells[3]))

reverted, skipped = 0, 0
for chapter, old, new in rows:
    if not new or new == old:
        continue
    # 只回滚「新句存在且唯一」的，避免误伤后来手工改过的句子
    if s.count(new) == 1 and new in s:
        s = s.replace(new, old, 1)
        reverted += 1
    else:
        skipped += 1
        print('SKIP', chapter, '|', new[:20])

io.open(SRC, 'w', encoding='utf-8').write(s)
print('回滚 %d 条，跳过 %d 条' % (reverted, skipped))
