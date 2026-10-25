# -*- coding: utf-8 -*-
"""给「啪嗒」机关加音效：新增 story 命令 sfx，两端支持，并在剧情里插入。"""
import io

# ---------- 1) story.js 插入 sfx 命令 ----------
p = 'src/story.js'
s = io.open(p, encoding='utf-8').read()
old = "{ t: 'say', who: '', text: '「啪嗒。」' },"
new = "{ t: 'sfx', name: 'click' },\n      " + old
if old in s and "t: 'sfx'" not in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('story: sfx click inserted')

# ---------- 2) Web：Sfx.click + cutscene 支持 sfx ----------
p2 = 'src/audio.js'
a = io.open(p2, encoding='utf-8').read()
if 'click: function' not in a:
    a = a.replace('\thurt: function () {',
                  '\t// 机关「啪嗒」：短促木质+金属卡扣\n'
                  '\tclick: function () {\n'
                  '\t\ttone(210, 120, 0.06, \'square\', 0.05);\n'
                  '\t\ttone(2400, 1800, 0.05, \'sine\', 0.04);\n'
                  '\t\tnoise(0.07, 0.02, 5200, 0.6);\n'
                  '\t},\n'
                  '\thurt: function () {', 1)
    io.open(p2, 'w', encoding='utf-8').write(a)
    print('web: Sfx.click added')

p3 = 'src/cutscene.js'
c = io.open(p3, encoding='utf-8').read()
if "case 'sfx':" not in c:
    c = c.replace("      case 'music':",
                  "      case 'sfx':\n"
                  "        if (typeof Sfx !== 'undefined' && c.name && typeof Sfx[c.name] === 'function') {\n"
                  "          Sfx[c.name]();\n"
                  "        }\n"
                  "        break;\n"
                  "      case 'music':", 1)
    io.open(p3, 'w', encoding='utf-8').write(c)
    print('web: sfx command added')

# ---------- 3) Godot：注册 click + 处理 sfx 命令 ----------
p4 = 'godot/sfx_player.gd'
g = io.open(p4, encoding='utf-8').read()
if 'click' not in g:
    g = g.replace('\t_load_sfx("shards", "res://audio/sfx/shards.wav")',
                  '\t_load_sfx("shards", "res://audio/sfx/shards.wav")\n'
                  '\t_load_sfx("click", "res://audio/sfx/click.wav")', 1)
    io.open(p4, 'w', encoding='utf-8').write(g)
    print('godot: click sfx registered')

p5 = 'godot/main.gd'
m = io.open(p5, encoding='utf-8').read()
if '"sfx":' not in m:
    m = m.replace('\t\t\t"reveal":',
                  '\t\t\t"sfx":\n'
                  '\t\t\t\tsfx_player.play(str(command.get("name", "")))\n'
                  '\t\t\t\treturn\n'
                  '\t\t\t"reveal":', 1)
    io.open(p5, 'w', encoding='utf-8').write(m)
    print('godot: sfx command added')
