# -*- coding: utf-8 -*-
"""1) 红之惨剧扣 MP + 回血 + 强化 Buff
2) 旋风回归（会移动，中心有伤害，冲刺穿过安全）
3) 雷帝新增招式（三连斩/追踪火球/落雷）
4) 六阶段镜像：分段包裹世界绘制
"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 1) 红之惨剧 ----------
s = s.replace('''	sfx_player.play("skill")
	if skill_red_tragedy:
		bullets.clear()''','''	player_energy -= 2.0          # 消耗 2 MP（用户要求）
	player_hp = mini(PLAYER_MAX_HP, player_hp + 2)   # 回复 2 HP
	tragedy_buff_t = 20.0         # 20 秒强化剑气
	sfx_player.play("skill")
	if skill_red_tragedy:
		bullets.clear()''', 1)

# ---------- 2) 旋风回归（阶段 3/4/5）+ 中心伤害 ----------
s = s.replace('''		2:  # 三：落地追击斩 + 新月剑气''','''		2:  # 三：落地追击斩 + 新月剑气 + 双旋风
			_spawn_two_whirls()''', 1)
s = s.replace('''		3:  # 四：地刺追击 + 火焰弹雨 + 新月剑气''','''		3:  # 四：地刺追击 + 火焰弹雨 + 新月剑气 + 双旋风
			_spawn_two_whirls()''', 1)
s = s.replace('''		4:  # 五：高频追击斩 + 火焰弹幕 + 锁定突刺锋''','''		4:  # 五：高频追击斩 + 火焰弹幕 + 锁定突刺锋 + 双旋风
			_spawn_two_whirls()''', 1)

# 旋风伤害逻辑：中心范围 + 冲刺/光球可穿过
s = s.replace('''		if dx < 70.0 and player_grounded and player_hurt_invuln <= 0 and player_dash_invuln <= 0 and not player_ball:''','''		if dx < 62.0 and player_grounded and player_hurt_invuln <= 0 and player_dash_invuln <= 0 and not player_ball:
			# 中心核心伤害（冲刺有无敌帧，可以穿过去）''', 1)

# ---------- 3) 雷帝新招式 ----------
s = s.replace('''		1:  # 二：落地突刺 + 火焰弹幕''','''		1:  # 二：落地突刺 + 火焰弹幕 + 三连斩
			if frame % 70 == 0:
				for k in range(3):
					var cdir := (player_pos - boss_pos).normalized().rotated((float(k) - 1.0) * 0.22)
					_spawn_bullet(boss_pos, cdir * 560.0, RED, "blade", 2.6, 0.02)
		1_placeholder:  # 占位''', 1)
# 修正占位（把原来的 phase1 内容保留）
s = s.replace('''		1_placeholder:  # 占位''','', 1)

s = s.replace('''		3:  # 四：地刺追击 + 火焰弹雨 + 新月剑气 + 双旋风''','''		3:  # 四：地刺追击 + 火焰弹雨 + 新月剑气 + 双旋风 + 追踪火球
			if frame % 100 == 0:
				for k in range(3):
					_spawn_bullet(boss_pos, Vector2(randf_range(-1, 1), randf_range(-0.4, 0.4)).normalized() * 190.0, RED, "flame", 5.0, 0.5)''', 1)

s = s.replace('''		4:  # 五：高频追击斩 + 火焰弹幕 + 锁定突刺锋 + 双旋风''','''		4:  # 五：高频追击斩 + 火焰弹幕 + 锁定突刺锋 + 双旋风 + 落雷
			if frame % 120 == 0:
				for k in range(2):
					var lxr := clampf(player_pos.x + (float(k) - 0.5) * 280.0, _battle_left() + 80.0, _battle_right() - 80.0)
					_beam_warning_crimson(lxr)''', 1)

if 'func _beam_warning_crimson' not in s:
    s += '''

## 雷帝落雷预警（红色）
func _beam_warning_crimson(x: float) -> void:
	beam_warning_list.append({"x": x, "t": 0.7, "crimson": true})

## 红色落雷（复用 beam 贴图与判定）
func _spawn_beam_crimson(x: float, seconds: float) -> void:
	_spawn_bullet(Vector2(x, (40.0 + GROUND_Y) * 0.5), Vector2.ZERO, RED, "beam", seconds, 0.0)
	_spawn_fx_ring(Vector2(x, GROUND_Y - 30.0), Color(1, 0.25, 0.15, 0.85), 130.0, 0.35, 3.0)
'''
    print('crimson beam helpers added')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
