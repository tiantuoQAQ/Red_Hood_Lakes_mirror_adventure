# -*- coding: utf-8 -*-
"""大修：玛丽苏战斗重做（公平激光/符纸/阴阳球）、激光有伤害、镜头稳定不抽搐、场地扩大、魔姬追击斩有预警。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()

# ---------- 1) 场地扩大：左右各大半屏 ----------
s = s.replace('const BATTLE_HALF := 700.0', 'const BATTLE_HALF := 980.0', 1)

# ---------- 2) 战斗镜头稳定（围绕 Boss 平滑跟随，不抽搐） ----------
start = s.index('func _update_camera() -> void:')
end = s.index('\nfunc ', start + 10)
new_cam = '''func _update_camera() -> void:
	if mode == Mode.BATTLE:
		# 围绕 Boss 的稳定跟随：目标固定为 Boss 屏幕中心，缓慢插值，不做 min/max 反复钳制
		var half := (BATTLE_HALF + 120.0)
		var want := boss_pos.x - VIEW.x * 0.5
		var lo := _battle_left() - 80.0
		var hi := _battle_right() + 80.0 - VIEW.x
		want = clampf(want, minf(lo, hi), maxf(lo, hi))
		camera_x = lerpf(camera_x, want, 1.0 - pow(0.02, FIXED_DT))
		return
	var target := clampf(player_pos.x - VIEW.x * 0.38, 0.0, WORLD_W - VIEW.x)
	camera_x = lerpf(camera_x, target, 1.0 - pow(0.0004, FIXED_DT))
'''
s = s[:start] + new_cam + s[end:]

# ---------- 3) 激光伤害（柱状判定） ----------
if 'kind == "beam"' not in s.split('func _check_graze_and_hits')[1][:2500]:
    s = s.replace('\tfor bullet in bullets:\n\t\tvar bp: Vector2 = bullet["pos"]',
                  '\tfor bullet in bullets:\n\t\tvar bp: Vector2 = bullet["pos"]\n'
                  '\t\t# 激光柱：竖直范围判定（碰到就扣血）\n'
                  '\t\tif str(bullet.get("kind", "")) == "beam" and player_hurt_invuln <= 0 and player_dash_invuln <= 0 and not player_ball:\n'
                  '\t\t\tif absf(player_pos.x - bp.x) < 22.0:\n'
                  '\t\t\t\t_apply_player_damage()\n'
                  '\t\t\t\tcontinue', 1)
    print('beam damage added')

# 统一扣血函数
if 'func _apply_player_damage' not in s:
    s += '''

## 玩家扣血（统一入口，带无敌帧与红晕）
func _apply_player_damage() -> void:
	if player_hurt_invuln > 0 or player_dash_invuln > 0 or player_ball:
		return
	player_hp -= 1
	player_hurt_invuln = 80
	hurt_vignette = 18
	sfx_player.play("hurt")
	screen_shake = 0.6
	if player_hp <= 0:
		player_hp = 0
		_start_death()
'''
    print('apply damage func added')

# ---------- 4) 玛丽苏战斗重做 ----------
start = s.index('func _patterns_marysue() -> void:')
end = s.index('\nfunc _spawn_two_whirls', start)
new_ms = '''func _patterns_marysue() -> void:
	# 重做：符纸环 + 阴阳球 + 激光，全部有预警、低频率、可躲
	match boss_phase:
		0:  # 壹 · 箱庭：绿色符纸环（缓慢外扩）
			if frame % 60 == 0:
				for k in range(8):
					var a := TAU * float(k) / 8.0 + elapsed * 0.5
					_spawn_bullet(boss_pos, Vector2(cos(a), sin(a)) * 150.0, HAZARD, "talisman", 5.0, 0.02)
		1:  # 贰 · 反语：阴阳球缓慢旋转外扩
			if frame % 65 == 0:
				for k in range(6):
					var a2 := -TAU * float(k) / 6.0 + elapsed * 0.9
					_spawn_bullet(boss_pos, Vector2(cos(a2), sin(a2)) * 170.0, HAZARD, "yinyang", 5.5, 0.25)
		2:  # 叁 · 镜廊：符纸雨（稀疏）+ 阴阳球
			if frame % 34 == 0:
				_spawn_bullet(Vector2(randf_range(_battle_left() + 60.0, _battle_right() - 60.0), 60.0),
					Vector2(0, 210.0), HAZARD, "talisman", 5.0, 0.0)
			if frame % 90 == 0:
				for k in range(5):
					var a3 := -PI * 0.5 + (float(k) - 2.0) * 0.28
					_spawn_bullet(boss_pos, Vector2(cos(a3), sin(a3)) * 200.0, HAZARD, "yinyang", 5.0, 0.3)
		3:  # 肆 · 断线：预警激光（先亮线 0.6s，再落柱；落在玩家侧前方，不贴脸）
			if boss_skill_state == "" and frame % 120 == 0:
				boss_skill_state = "telegraph"
				boss_skill_timer = 36
				skill_warnings.clear()
				for k in range(2):
					var off := (float(k) - 0.5) * 320.0
					var lx := clampf(player_pos.x + off, _battle_left() + 80.0, _battle_right() - 80.0)
					skill_warnings.append({"kind": "beam", "x": lx, "life": 0.6, "color": HAZARD})
			elif boss_skill_state == "telegraph":
				boss_skill_timer -= 1
				if boss_skill_timer <= 0:
					boss_skill_state = ""
					for w in skill_warnings:
						_spawn_beam(float(w["x"]), 0.9)
					skill_warnings.clear()
		4:  # 伍 · 狂言：绿闪 + 符纸环（无激光）
			green_flash_t = 1.0
			if frame % 70 == 0:
				for k in range(10):
					var a5 := TAU * float(k) / 10.0 + elapsed
					_spawn_bullet(boss_pos, Vector2(cos(a5), sin(a5)) * 160.0, HAZARD, "talisman", 5.0, 0.02)
		5:  # 陆 · 天地倒悬：镜像翻转 + 阴阳球 + 符纸
			if not mirror_flip:
				mirror_flip = true
			if frame % 55 == 0:
				for k in range(8):
					var a6 := TAU * float(k) / 8.0 + elapsed * 1.3
					_spawn_bullet(boss_pos, Vector2(cos(a6), sin(a6)) * 165.0, HAZARD, "yinyang", 5.5, 0.2)
			if frame % 34 == 0:
				for k in range(6):
					var a7 := TAU * float(k) / 6.0 - elapsed
					_spawn_bullet(boss_pos, Vector2(cos(a7), sin(a7)) * 140.0, HAZARD, "talisman", 5.0, 0.02)
'''
s = s[:start] + new_ms + s[end:]

# 激光预警绘制（skill_warnings kind beam）
if 'w.get("kind", "") == "beam"' not in s:
    s = s.replace('	for w in skill_warnings:',
                  '	for w in skill_warnings:\n'
                  '		if str(w.get("kind", "")) == "beam":\n'
                  '			# 激光预警：竖直虚线 + 地面光圈\n'
                  '			var bx: float = float(w.get("x", 0.0)) - camera_x\n'
                  '			var wa: float = clampf(float(w.get("life", 0.0)) / 0.6, 0.0, 1.0)\n'
                  '			draw_line(Vector2(bx, 40), Vector2(bx, GROUND_Y), Color(0.51, 1, 0, 0.35 + 0.35 * wa), 3.0)\n'
                  '			draw_circle(Vector2(bx, GROUND_Y - 12), 26.0, Color(0.51, 1, 0, 0.25))\n'
                  '			continue', 1)
    print('laser telegraph draw added')

# ---------- 5) 魔姬二阶段追击斩：先预警再冲，不贴脸 ----------
s = s.replace('''	elif boss_skill_state == "leap":
		boss_skill_timer -= 1
		boss_pos.y = lerpf(boss_pos.y, 420.0, 0.22)
		if boss_skill_timer <= 0:''','''	elif boss_skill_state == "leap":
		boss_skill_timer -= 1
		boss_pos.y = lerpf(boss_pos.y, 420.0, 0.10)
		if boss_skill_timer <= 0:''', 1)
s = s.replace('boss_skill_timer = 30\n\t\tboss_rush_side', 'boss_skill_timer = 40\n\t\tboss_rush_side', 1)
# 冲刺速度降低（不再一帧贴脸）
s = s.replace('boss_pos.x = move_toward(boss_pos.x, target_x, 15.0)', 'boss_pos.x = move_toward(boss_pos.x, target_x, 9.0)', 1)
# 起手不贴脸：先退开
s = s.replace('''		boss_skill_state = "leap"
		boss_skill_timer = 30
		boss_rush_side = signf(player_pos.x - boss_pos.x)''','''		boss_skill_state = "leap"
		boss_skill_timer = 40
		boss_rush_side = signf(player_pos.x - boss_pos.x)
		# 起手先拉开距离，避免贴脸瞬移
		boss_slide_to = clampf(player_pos.x - boss_rush_side * 380.0, _battle_left() + 120.0, _battle_right() - 120.0)''', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('patched')
