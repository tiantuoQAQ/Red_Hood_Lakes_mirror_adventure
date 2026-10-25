import io, re
p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
# 修复被吞掉的引号
s = s.replace('HAZARD, beam, seconds', 'HAZARD, "beam", seconds')
s = s.replace('Color(0.51, 1, 0, 0.8), 120.0, 0.35, 3.0)', 'Color(0.51, 1, 0, 0.8), 120.0, 0.35, 3.0)')
# 同时检查 _spawn_beam 里的其它字符串
s = s.replace('"kind": "beam", "x": lx, "life": 0.6, "color": HAZARD', '"kind": "beam", "x": lx, "life": 0.6, "color": HAZARD')
io.open(p, 'w', encoding='utf-8').write(s)
print('quotes fixed')
