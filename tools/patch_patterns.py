# -*- coding: utf-8 -*-
"""弹幕更绚丽：新增激光招式、扩展每阶段招式组合、玛丽苏缩小一点。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

s = s.replace('const ANIM_BODY_H := {"crimson": 150.0, "marysue": 300.0}',
              'const ANIM_BODY_H := {"crimson": 150.0, "marysue": 360.0}', 1)

# 新增两个激光招式函数
if 'func _crimson_laser_sweep' not in s:
    s += '''

# 魔姬：横向激光扫射（预警 30 帧 → 三束激光）
func _crimson_laser_sweep() -> void:
	if boss_skill_state == "":
		boss_skill_state = "telegraph"
		boss_skill_timer = 30
		var dir := (player_pos - boss_pos).normalized()
		skill_warnings.clear()
		for i in range(3):
			var off := (float(i) - 1.0) * 0.12
			var d2 := Vector2(cos(dir.angle() + off), sin(dir.angle() + off))
			skill_warnings.append({"kind": "line", "pos": boss_pos, "dir": d2, "life": 30.0 / 60.0, "color": RED})
	elif boss_skill_state == "telegraph":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = "firing"
			boss_skill_timer = 26
			for w in skill_warnings:
				_spawn_bullet(boss_pos, w["dir"] * 780.0, RED, "laser")
	elif boss_skill_state == "firing":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			skill_warnings.clear()

# 玛丽苏：翡翠贯射（预警 36 帧 → 5 束绿色激光扇形）
func _marysue_laser_beam() -> void:
	if boss_skill_state == "":
		boss_skill_state = "telegraph"
		boss_skill_timer = 36
		var dir := (player_pos - boss_pos).normalized()
		skill_warnings.clear()
		for i in range(5):
			var off := (float(i) - 2.0) * 0.09
			var d2 := Vector2(cos(dir.angle() + off), sin(dir.angle() + off))
			skill_warnings.append({"kind": "line", "pos": boss_pos, "dir": d2, "life": 36.0 / 60.0, "color": HAZARD})
	elif boss_skill_state == "telegraph":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = "firing"
			boss_skill_timer = 30
			for w in skill_warnings:
				_spawn_bullet(boss_pos, w["dir"] * 700.0, HAZARD, "laser")
	elif boss_skill_state == "firing":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			skill_warnings.clear()
'''
    print('new pattern funcs appended')

# 魔姬阶段招式组合：1/2/3/4 阶段都加料
old = '''		0:  # Stage 1: 赤线突刺 (Telegraph 24 frames → thrust 900px/s)
				_crimson_thrust_lines()
			2:  # Stage 3: 扇形斩击 (5-7 blades, safe gap)
				_crimson_fan_slash()'''
new = '''		0:  # Stage 1: 赤线突刺 + 环形齐射
				_crimson_thrust_lines()
				if boss_skill_state == "" and frame % 3 == 0:
					for i in range(12):
						var a0 := TAU * float(i) / 12.0 + float(frame) * 0.02
						_spawn_bullet(boss_pos, Vector2(cos(a0), sin(a0)) * 230.0, RED, "hazard")
			1:  # Stage 2: 突刺 + 扇形
				_crimson_thrust_lines()
				if boss_skill_state == "":
					_crimson_fan_slash()
			2:  # Stage 3: 扇形斩击 + 双侧刀光
				_crimson_fan_slash()
				if boss_skill_state == "" and frame % 4 == 0:
					for i in range(6):
						var a1 := PI * (0.15 + 0.14 * float(i))
						_spawn_bullet(boss_pos, Vector2(cos(a1), sin(a1)) * 300.0, RED, "blade")
			3:  # Stage 4: 激光 + 突刺
				_crimson_laser_sweep()
				if boss_skill_state == "":
					_crimson_thrust_lines()'''
if old in s:
    s = s.replace(old, new, 1)
    print('crimson phases expanded')
else:
    print('crimson block miss')

old2 = '''		0:  # Stage 1: 法环收束 (12 bullets, 96px gap, 260px/s)
				_marysue_ring_collapse()
			2:  # Stage 3: 光翼裁切 (left/right fan, 6 each, 380px/s)
				_marysue_wing_sweep()'''
new2 = '''		0:  # Stage 1: 法环收束 + 绿色游星
				_marysue_ring_collapse()
				if boss_skill_state == "" and frame % 5 == 0:
					for i in range(8):
						var g0 := TAU * float(i) / 8.0 + elapsed * 0.8
						_spawn_bullet(boss_pos, Vector2(cos(g0), sin(g0)) * 200.0, HAZARD, "hazard")
			1:  # Stage 2: 双环花旋
				if frame % 3 == 0:
					for i in range(10):
						var g1 := TAU * float(i) / 10.0 + elapsed * 1.6
						_spawn_bullet(boss_pos, Vector2(cos(g1), sin(g1)) * 240.0, HAZARD, "hazard")
			2:  # Stage 3: 光翼裁切 + 落雨
				_marysue_wing_sweep()
			3:  # Stage 4: 翡翠贯射
				_marysue_laser_beam()'''
if old2 in s:
    s = s.replace(old2, new2, 1)
    print('marysue phases expanded')
else:
    print('marysue block miss')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
