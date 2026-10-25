# -*- coding: utf-8 -*-
"""对话结束后立绘立即消失（走位段不再画残留对话立绘）。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 走位开始时清掉残留立绘
s = s.replace('\tif last_left != "" or last_right != "":\n\t\tportrait_fade = 1.0',
              '\tlast_left = ""\n\tlast_right = ""\n\tportrait_fade = 0.0', 1)

# 2) 删掉走位段残留立绘绘制
old_draw = ('\t# 对话结束后立绘淡出（用户要求：否则会瞬间消失）\n'
            '\tif portrait_fade > 0.0:\n'
            '\t\t_draw_portrait(last_left, Vector2(340, 580), 0.62, false, false, portrait_fade)\n'
            '\t\t_draw_portrait(last_right, Vector2(940, 580), 0.62, false, true, portrait_fade)\n')
if old_draw in s:
    s = s.replace(old_draw, '\t# 走位段不画对话立绘（用户要求：对话结束立即消失）\n', 1)
    print('walk portrait drawing removed')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
