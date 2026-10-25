# -*- coding: utf-8 -*-
"""诺登动机修正：不是「奉命」（格林当时还不认识她），而是「为了格林大人」自己来的。"""
import io

p = 'src/story.js'
s = io.open(p, encoding='utf-8').read()
orig = s

s = s.replace("{ t: 'say', who: 'norden', show: true, text: '我奉格林大人之命，暂且助您。' },",
              "{ t: 'say', who: 'norden', show: true, text: '我是为了格林大人，才来寻您。' },\n"
              "      { t: 'say', who: 'norden', show: true, text: '……虽然，那位大人还不认识我。' },", 1)

# 让「我救您，是为了格林大人」承接更自然
s = s.replace("{ t: 'say', who: 'norden', show: true, text: '我救您，是为了格林大人。' },",
              "{ t: 'say', who: 'norden', show: true, text: '我救您，也只是为了格林大人。' },", 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
