# -*- coding: utf-8 -*-
"""Boss 移动粒子特效：魔姬红色余烬、玛丽苏绿色光点（跟随移动、缓缓飘散）。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

if 'var boss_prev_pos' not in s:
    s = s.replace('var boss_hit_flash := 0', 'var boss_hit_flash := 0\nvar boss_prev_pos := Vector2.ZERO\nvar boss_move_particle_tick := 0', 1)
    print('vars added')

# 在 _update_boss 末尾（_update_boss_extras 之前）加入移动粒子
if 'func _boss_move_particles' not in s:
    s = s.replace('\t_update_boss_extras()',
                  '\t_boss_move_particles()\n\t_update_boss_extras()', 1)
    s += '''

## Boss 移动时的粒子特效（小光点）
func _boss_move_particles() -> void:
	var delta := boss_pos - boss_prev_pos
	var speed := delta.length() / maxf(FIXED_DT, 0.0001)
	boss_prev_pos = boss_pos
	boss_move_particle_tick += 1
	if speed < 40.0:
		return
	var dir := delta.normalized()
	var amount := 2 if speed < 200.0 else 3
	if boss_move_particle_tick % 2 != 0:
		return
	for k in range(amount):
		var offset := Vector2(randf_range(-26, 26), randf_range(-46, 46))
		var origin := boss_pos + offset - dir * 18.0
		if boss_id == "crimson":
			# 红色余烬：向后飘散、缓慢下落
			_spawn_particle(origin, Color(1, randf_range(0.1, 0.35), 0.1, 0.9), randf_range(0.35, 0.7),
				Vector2(-dir.x * randf_range(60, 160) + randf_range(-30, 30), randf_range(20, 90)), randf_range(2.5, 5.0))
		else:
			# 绿色光点：向上飘、带轻微旋转感
			_spawn_particle(origin, Color(0.51, 1.0, 0.0, 0.9), randf_range(0.45, 0.85),
				Vector2(-dir.x * randf_range(30, 90) + randf_range(-40, 40), randf_range(-110, -30)), randf_range(2.0, 4.5))
	# 高速时额外一圈细腻光尘
	if speed > 500.0:
		for k in range(3):
			var a := randf() * TAU
			_spawn_particle(boss_pos + Vector2(cos(a), sin(a)) * randf_range(20.0, 60.0),
				Color(1, 1, 1, 0.55) if boss_id == "crimson" else Color(0.51, 1.0, 0.0, 0.7),
				randf_range(0.2, 0.4), Vector2(randf_range(-60, 60), randf_range(-60, 60)), 2.0)
'''
    print('particle fn appended')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
