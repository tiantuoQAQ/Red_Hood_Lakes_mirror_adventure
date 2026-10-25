# -*- coding: utf-8 -*-
"""重写两 Boss 招式：火焰弹幕/追击斩/新月剑气；符纸环/阴阳玉/激光柱 + 粒子流光。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()

start = s.index('func _patterns_crimson() -> void:')
end = s.index('\nfunc _spawn_two_whirls', start)
new_crimson = '''func _patterns_crimson() -> void:
	# 参考用户截图：满屏火焰弹（弱追踪、会自动消散）、落地追击斩、新月剑气
	match boss_phase:
		0:  # 一：火焰弹幕（弱追踪，3 秒后消散）
			if frame % 10 == 0:
				for k in range(2):
					var a := (player_pos - boss_pos).angle() + randf_range(-0.55, 0.55)
					_spawn_bullet(boss_pos + Vector2(randf_range(-16, 16), randf_range(-16, 16)),
						Vector2(cos(a), sin(a)) * randf_range(170.0, 260.0), RED, "flame", 3.0, 0.05)
			if frame % 90 == 0:
				for k in range(10):
					var a2 := TAU * float(k) / 10.0 + elapsed
					_spawn_bullet(boss_pos, Vector2(cos(a2), sin(a2)) * 210.0, RED, "flame", 3.4, 0.03)
		1:  # 二：落地追击斩 + 火焰弹
			_crimson_rush_attack(true)
		2:  # 三：落地追击斩 + 新月剑气
			_crimson_rush_attack(false)
			if boss_skill_state == "" and frame % 26 == 0:
				_crimson_crescent_volley(3)
		3:  # 四：火焰弹雨 + 新月剑气
			_crimson_rush_attack(false)
			if frame % 8 == 0:
				var rx := 150.0 + randf() * 2100.0
				_spawn_bullet(Vector2(rx, 40.0), Vector2(0, 300.0), RED, "flame", 4.0, 0.02)
			if frame % 40 == 0:
				_crimson_crescent_volley(2)
		4:  # 五：高频追击斩 + 火焰弹幕 + 锁定突刺锋
			_crimson_rush_attack(true)
			if frame % 6 == 0:
				for k in range(2):
					var a5 := (player_pos - boss_pos).angle() + randf_range(-0.4, 0.4)
					_spawn_bullet(boss_pos, Vector2(cos(a5), sin(a5)) * 240.0, RED, "flame", 2.8, 0.06)
			if lock_state == "" and lock_cooldown <= 0:
				lock_state = "aim"
				lock_timer = 0.5
				lock_target = player_pos
				lock_cooldown = 120
				sfx_player.play("lock_beep")

func _crimson_crescent_volley(count: int) -> void:
	var dir := (player_pos - boss_pos).normalized()
	for k in range(count):
		var off := (float(k) - float(count - 1) * 0.5) * 0.16
		var d := Vector2(cos(dir.angle() + off), sin(dir.angle() + off))
		_spawn_bullet(boss_pos + d * 40.0, d * 520.0, RED, "crescent", 2.6, 0.0)
	_spawn_fx_ring(boss_pos, Color(1, 0.3, 0.3, 0.8), 120.0, 0.3, 3.0)

## 落地追击斩：先落到地面（带拖尾），再沿地面追击小红帽，落地后放新月剑气
func _crimson_rush_attack(finish_crescent: bool) -> void:
	if boss_skill_state == "":
		boss_skill_state = "leap"
		boss_skill_timer = 22
		boss_rush_side = signf(player_pos.x - boss_pos.x)
		_spawn_fx_ring(boss_pos, Color(1, 0, 0, 0.7), 90.0, 0.25, 3.0)
	elif boss_skill_state == "leap":
		boss_skill_timer -= 1
		boss_pos.y = lerpf(boss_pos.y, 420.0, 0.22)
		if boss_skill_timer <= 0:
			boss_skill_state = "rush"
			boss_skill_timer = 34
			sfx_player.play("skill")
	elif boss_skill_state == "rush":
		boss_skill_timer -= 1
		# 追着小红帽砍：向玩家方向加速冲
		var target_x: float = player_pos.x - boss_rush_side * 60.0
		boss_pos.x = move_toward(boss_pos.x, target_x, 15.0)
		boss_pos.y = 420.0
		# 冲刺拖尾（帅气）
		for k in range(2):
			_spawn_particle(Vector2(boss_pos.x - boss_rush_side * (20.0 + float(k) * 26.0), boss_pos.y - 30.0 + randf_range(-20, 20)),
				Color(1, 0.15, 0.15, 0.85), 0.28, Vector2(-boss_rush_side * 260.0, randf_range(-30, 30)), 7.0)
		if frame % 6 == 0:
			var d := (player_pos - boss_pos).normalized()
			_spawn_bullet(boss_pos + d * 30.0, d * 620.0, RED, "crescent", 2.2, 0.0)
		if boss_skill_timer <= 0:
			boss_skill_state = "land"
			boss_skill_timer = 14
			_spawn_fx_ring(Vector2(boss_pos.x, GROUND_Y - 10.0), Color(1, 0.35, 0.35, 0.9), 200.0, 0.35, 5.0)
			_spawn_burst(Vector2(boss_pos.x, GROUND_Y - 10.0), Color(1, 0.6, 0.4), 14)
			if finish_crescent:
				_crimson_crescent_volley(5)
	elif boss_skill_state == "land":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			boss_pos.y = 226.0

func _patterns_marysue() -> void:
	# 参考用户截图：符纸环、阴阳玉、激光柱、粒子流光
	match boss_phase:
		0:  # 一：符纸环（缓慢外扩，弱追踪）
			if frame % 18 == 0:
				for k in range(10):
					var a := TAU * float(k) / 10.0 + elapsed * 0.6
					_spawn_bullet(boss_pos, Vector2(cos(a), sin(a)) * 170.0, HAZARD, "talisman", 4.5, 0.03)
		1:  # 二：阴阳玉旋转 + 符纸
			if frame % 26 == 0:
				for k in range(6):
					var a2 := -TAU * float(k) / 6.0 + elapsed * 1.1
					_spawn_bullet(boss_pos, Vector2(cos(a2), sin(a2)) * 220.0, HAZARD, "yinyang", 5.0, 0.4)
			if frame % 40 == 0:
				for k in range(6):
					var a3 := TAU * float(k) / 6.0 + elapsed
					_spawn_bullet(boss_pos, Vector2(cos(a3), sin(a3)) * 260.0, HAZARD, "talisman", 4.0, 0.02)
		2:  # 三：激光柱 + 阴阳玉
			if frame % 90 == 0:
				for k in range(3):
					var bx := clampf(player_pos.x + randf_range(-300.0, 300.0), 120.0, WORLD_W - 160.0)
					_spawn_bullet(Vector2(bx, GROUND_Y - 200.0), Vector2.ZERO, HAZARD, "beam", 1.4, 0.0)
					_spawn_fx_ring(Vector2(bx, GROUND_Y - 200.0), Color(0.51, 1, 0, 0.8), 150.0, 0.5, 4.0)
					for k2 in range(8):
						_spawn_particle(Vector2(bx, GROUND_Y - 240.0 + randf_range(-20, 20)),
							Color(0.51, 1, 0, 0.9), 0.6, Vector2(randf_range(-30, 30), randf_range(-120, -40)), 5.0)
			if frame % 30 == 0:
				for k in range(4):
					var a4 := TAU * float(k) / 4.0 + elapsed * 1.4
					_spawn_bullet(boss_pos, Vector2(cos(a4), sin(a4)) * 200.0, HAZARD, "yinyang", 4.5, 0.35)
		3:  # 四：符纸雨 + 阴阳玉环
			if frame % 7 == 0:
				_spawn_bullet(Vector2(120.0 + randf() * 2100.0, 40.0), Vector2(0, 260.0), HAZARD, "talisman", 4.0, 0.02)
			if frame % 60 == 0:
				for k in range(8):
					var a5 := TAU * float(k) / 8.0
					_spawn_bullet(boss_pos, Vector2(cos(a5), sin(a5)) * 180.0, HAZARD, "yinyang", 5.0, 0.45)
		4:  # 五：地面冲刺 + 全屏绿闪 + 粒子
			green_flash_t = 1.2
			if boss_skill_state == "":
				boss_skill_state = "firing"
				boss_skill_timer = 40
				boss_pos.y = 420.0
				boss_pos.x = clampf(player_pos.x + randf_range(-200.0, 200.0), 1250.0, 2180.0)
				_spawn_bullet(boss_pos, Vector2(-1, 0) * 800.0, HAZARD, "beam", 1.0, 0.0)
				for k in range(10):
					_spawn_particle(boss_pos, Color(0.51, 1, 0, 0.9), 0.5, Vector2(randf_range(-200, 200), randf_range(-120, 60)), 6.0)
			elif boss_skill_state == "firing":
				boss_skill_timer -= 1
				if boss_skill_timer <= 0:
					boss_skill_state = ""
					boss_pos.y = 226.0
		5:  # 六：镜像翻转 + 弹幕炼狱（符纸 + 阴阳玉 + 激光柱）
			if not mirror_flip:
				mirror_flip = true
			if frame % 12 == 0:
				for k in range(8):
					var a6 := TAU * float(k) / 8.0 + elapsed * 1.7
					_spawn_bullet(boss_pos, Vector2(cos(a6), sin(a6)) * 190.0, HAZARD, "talisman", 4.0, 0.03)
			if frame % 40 == 0:
				for k in range(8):
					var a7 := -TAU * float(k) / 8.0 + elapsed
					_spawn_bullet(boss_pos, Vector2(cos(a7), sin(a7)) * 140.0, HAZARD, "yinyang", 5.0, 0.4)
			if frame % 70 == 0:
				for k in range(4):
					var bx2 := 150.0 + randf() * 2000.0
					_spawn_bullet(Vector2(bx2, GROUND_Y - 200.0), Vector2.ZERO, HAZARD, "beam", 1.2, 0.0)
'''
s = s[:start] + new_crimson + s[end:]

# boss_rush_side 变量
if 'var boss_rush_side' not in s:
    s = s.replace('var boss_skill_subframe := 0', 'var boss_skill_subframe := 0\nvar boss_rush_side := 1.0', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('patterns rewritten')
