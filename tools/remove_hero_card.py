# -*- coding: utf-8 -*-
"""去掉「悲愤交加的勇者」黑场大字卡（用户不需要）。"""
import io

p = 'src/story.js'
s = io.open(p, encoding='utf-8').read()
old = "\n{ t: 'card', line1: '悲愤交加的勇者', line2: '踏上了寻回珍视之人的旅途', frames: 170 },\n"
if old in s:
    s = s.replace(old, '\n', 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('hero card removed')
else:
    # 宽松匹配
    i = s.find("'悲愤交加的勇者'")
    if i > 0:
        start = s.rfind('\n', 0, i)
        end = s.find('\n', s.find('},', i))
        s = s[:start] + s[end:]
        io.open(p, 'w', encoding='utf-8').write(s)
        print('hero card removed (loose)')
    else:
        print('not found')
