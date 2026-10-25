# -*- coding: utf-8 -*-
"""1) 修 wake_talk 的走位没有 cam → 镜子在屏幕外看不见（脚本数据补 cam:true）
2) 玛丽苏黑影第一次开口前加一句「……」给玩家缓冲
3) Godot 侧：有交互目标时默认跟随镜头（兜底）
"""
import io
import re

# ---------- 1) story.js：给 wake_talk 的 walk 加 cam ----------
p = 'src/story.js'
s = io.open(p, encoding='utf-8').read()
orig = s

old = "walk', bg: 'void', target: { kind: 'mirror', x: 1040 }"
if old in s:
    s = s.replace(old, "walk', bg: 'void', cam: true, target: { kind: 'mirror', x: 1040 }", 1)
    print('wake_talk walk: cam added')
else:
    # 用更宽松的匹配
    idx = s.find("kind: 'mirror', x: 1040")
    if idx > 0:
        line_start = s.rfind('\n', 0, idx) + 1
        line_end = s.find('\n', idx)
        line = s[line_start:line_end]
        if 'cam' not in line:
            new_line = line.replace("{ t: 'walk', bg: 'void',", "{ t: 'walk', bg: 'void', cam: true,")
            s = s[:line_start] + new_line + s[line_end:]
            print('wake_talk walk: cam added (loose)')
        else:
            print('already has cam')
    else:
        print('mirror walk NOT FOUND')

# ---------- 2) 黑影首次开口前加「……」 ----------
marker = "{ t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '库嘻嘻……' },"
if marker in s and "text: '……' }" not in s.split(marker)[0][-200:]:
    s = s.replace(marker,
                  "{ t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '……' },\n      " + marker, 1)
    print('shadow buffer line inserted')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')

# ---------- 3) Godot 兜底：有 target 就跟随镜头 ----------
p2 = 'godot/main.gd'
g = io.open(p2, encoding='utf-8').read()
g2 = g.replace('\twalk_camera = bool(command.get("cam", false))',
               '\twalk_camera = bool(command.get("cam", walk_target.size() > 0))   # 有交互目标时默认跟随（否则目标可能在屏幕外）', 1)
io.open(p2, 'w', encoding='utf-8').write(g2)
print('godot walk_camera fallback ok' if g2 != g else 'godot unchanged')
