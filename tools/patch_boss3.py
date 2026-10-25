# -*- coding: utf-8 -*-
"""Boss 战第三阶段：逐阶段招式 + 旋风/锁定突刺锋/大光球爆炸/随机激光/绿闪/镜像翻转 + 开场与插图绘制。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()

# ---------- 1) 用新调度器替换 _spawn_boss_pattern ----------
start = s.index('func _spawn_boss_pattern() -> void:')
nxt = s.index('\nfunc ', start + 10)
old_block = s[start:nxt]

new_block = '''func _spawn_boss_pattern() -> void:
	if boss_id == "crimson":
		_patterns_crimson()
	else:
		_patterns_marysue()
'''
s = s[:start] + new_block + s[nxt:]
print('dispatcher replaced')

# ---------- 2) 追加新函数 ----------
s += '''

# ======================= 新 Boss 招式体系 =======================

func _patterns_crimson() -> void:
	var color := RED
	match boss_phase:
		0:  # 一阶段：天上直线剑气（非追踪）
			if boss_skill_state == "":
				boss_skill_state = "telegraph"
				boss_skill_timer = 22
				var dir := (player_pos - boss_pos).normalized()
				skill_warnings.append({"kind": "line", "pos": boss_pos, "dir": dir, "life": 22.0 / 60.0, "color": RED})
			elif boss_skill_state == "telegraph":
				boss_skill_timer -= 1
				if boss_skill_timer <= 0:
					boss_skill_state = "firing"
					boss_skill_timer = 20
					var aim: Vector2 = skill_warnings[0]["dir"] if skill_warnings.size() > 0 else Vector2.LEFT
					for k in range(3):
						var off := (float(k) - 1.0) * 0.10
						_spawn_bullet(boss_pos, Vector2(cos(aim.angle() + off), sin(aim.angle() + off)) * 620.0, color, "blade")
			elif boss_skill_state == "firing":
				boss_skill_timer -= 1
				if boss_skill_timer <= 0:
					boss_skill_state = ""
					skill_warnings.clear()
		1:  # 二阶段：落地突刺 + 少量追踪剑气
			if boss_skill_state == "":
				boss_skill_state = "telegraph"
				boss_skill_timer = 28
				boss_pos.y = 380.0
				skill_warnings.append({"kind": "line", "pos": boss_pos, "dir": (player_pos - boss_pos).normalized(), "life": 28.0 / 60.0, "color": RED})
			elif boss_skill_state == "telegraph":
				boss_skill_timer -= 1
				if boss_skill_timer <= 0:
					boss_skill_state = "firing"
					boss_skill_timer = 30
					boss_pos.x = clampf(player_pos.x, 1250.0, 2180.0)
					_spawn_bullet(boss_pos, Vector2(-1, 0) * 900.0, color, "lance")
					for k in range(3):
						var hb := (player_pos - boss_pos).normalized()
						_spawn_bullet(boss_pos, hb * 300.0, color, "homing")
			elif boss_skill_state == "firing":
				boss_skill_timer -= 1
				if boss_skill_timer <= 0:
					boss_skill_state = ""
					skill_warnings.clear()
					boss_pos.y = 226.0
		2:  # 三阶段：天上追踪剑气 + 两个旋风
			_spawn_two_whirls()
			if boss_skill_state == "":
				boss_skill_state = "firing"
				boss_skill_timer = 60
				for k in range(3):
					var hb2 := (player_pos - boss_pos).normalized()
					_spawn_bullet(boss_pos, hb2 * 280.0, color, "homing")
			elif boss_skill_state == "firing":
				boss_skill_timer -= 1
				if boss_skill_timer <= 0:
					boss_skill_state = ""
		3:  # 四阶段：剑雨 + 剑气
			_spawn_two_whirls()
			if frame % 6 == 0:
				for k in range(3):
					var rx := 150.0 + randf() * 2200.0
					_spawn_bullet(Vector2(rx, 30.0), Vector2(0, 420.0), color, "rain")
			if frame % 30 == 0:
				var dir3 := (player_pos - boss_pos).normalized()
				_spawn_bullet(boss_pos, dir3 * 700.0, color, "blade")
		4:  # 五阶段：高频突刺 + 剑气 + 每 2 秒锁定突刺锋
			_spawn_two_whirls()
			if frame % 14 == 0:
				var dir4 := (player_pos - boss_pos).normalized()
				_spawn_bullet(boss_pos, dir4 * 760.0, color, "blade")
			if frame % 24 == 0:
				_spawn_bullet(boss_pos, Vector2(randf_range(-1, 1), randf_range(-0.3, 0.6)).normalized() * 620.0, color, "lance")
			if lock_state == "" and lock_cooldown <= 0:
				lock_state = "aim"
				lock_timer = 0.5
				lock_target = player_pos
				lock_cooldown = 120
				sfx_player.play("lock_beep")

func _patterns_marysue() -> void:
	var color := HAZARD
	match boss_phase:
		0:  # 一阶段：小光球
			if frame % 42 == 0:
				for i in range(12):
					var a := TAU * float(i) / 12.0 + elapsed
					_spawn_bullet(boss_pos, Vector2(cos(a), sin(a)) * 140.0, color, "hazard")
		1:  # 二阶段：缓慢移动的追踪激光
			if frame % 50 == 0:
				for i in range(3):
					var d := (player_pos - boss_pos).normalized()
					var off := (float(i) - 1.0) * 0.35
					_spawn_bullet(boss_pos, Vector2(cos(d.angle() + off), sin(d.angle() + off)) * 130.0, color, "homing_laser")
		2:  # 三阶段：光球雨 + 大光球（落地爆炸 + 冲击波）
			if frame % 8 == 0:
				_spawn_bullet(Vector2(120.0 + randf() * 2000.0, 40.0), Vector2(0, 260.0), color, "rain")
			if frame % 150 == 0:
				_spawn_bullet(Vector2(player_pos.x, 60.0), Vector2(0, 300.0), color, "bigorb")
		3:  # 四阶段：地图随机各处激光，持续 2 秒
			if frame % 70 == 0:
				for i in range(4):
					var lx := 120.0 + randf() * 2000.0
					_spawn_bullet(Vector2(lx, 40.0), Vector2(0, 300.0), color, "laser_down")
		4:  # 五阶段：带激光在地面冲刺 + 全屏绿闪（无伤害、遮挡视野）
			green_flash_t = 1.2
			if boss_skill_state == "":
				boss_skill_state = "firing"
				boss_skill_timer = 40
				boss_pos.y = 420.0
				boss_pos.x = clampf(player_pos.x + randf_range(-200.0, 200.0), 1250.0, 2180.0)
				_spawn_bullet(boss_pos, Vector2(-1, 0) * 800.0, color, "laser")
			elif boss_skill_state == "firing":
				boss_skill_timer -= 1
				if boss_skill_timer <= 0:
					boss_skill_state = ""
					boss_pos.y = 226.0
		5:  # 六阶段：镜像翻转
			if not mirror_flip:
				mirror_flip = true
			if frame % 40 == 0:
				for i in range(8):
					var a5 := TAU * float(i) / 8.0 + elapsed * 1.3
					_spawn_bullet(boss_pos, Vector2(cos(a5), sin(a5)) * 210.0, color, "hazard")

func _spawn_two_whirls() -> void:
	if whirls.size() >= 2:
		return
	var base := clampf(player_pos.x, 300.0, 2100.0)
	whirls = [{"x": base - 320.0, "phase": 0.0}, {"x": base + 320.0, "phase": 1.7}]

func _update_boss_extras() -> void:
	# 旋风：转动 + 碰撞（贴地才伤害，带无敌帧判定）
	for w in whirls:
		w["phase"] = float(w.get("phase", 0.0)) + FIXED_DT * 3.0
		var dx: float = absf(player_pos.x - float(w["x"]))
		if dx < 36.0 and player_grounded and player_hurt_invuln <= 0 and player_dash_invuln <= 0 and not player_ball:
			player_hp -= 1
			player_hurt_invuln = 70
			player_vel.x = signf(player_pos.x - float(w["x"])) * 420.0
			sfx_player.play("hurt")
			if player_hp <= 0:
				player_hp = 0
	# 锁定突刺锋
	if lock_cooldown > 0:
		lock_cooldown -= 1
	if lock_state == "aim":
		lock_timer -= FIXED_DT
		if lock_timer <= 0.0:
			lock_state = "spike"
			lock_timer = 0.5
			spikes.append({"pos": lock_target, "life": 0.5, "max": 0.5})
			sfx_player.play("spike")
	elif lock_state == "spike":
		lock_timer -= FIXED_DT
		if lock_timer <= 0.0:
			lock_state = ""
	# 突刺锋伤害 + 淡出
	for sp in spikes:
		sp["life"] = float(sp["life"]) - FIXED_DT
		var d: float = Vector2(sp["pos"]).distance_to(Vector2(player_pos.x, GROUND_Y - 20.0))
		if d < 46.0 and player_hurt_invuln <= 0 and player_dash_invuln <= 0 and not player_ball:
			player_hp -= 1
			player_hurt_invuln = 70
			sfx_player.play("hurt")
	spikes = spikes.filter(func(x): return float(x.get("life", 0.0)) > 0.0)
	# 绿闪衰减
	if green_flash_t > 0.0:
		green_flash_t = maxf(0.0, green_flash_t - FIXED_DT)

func _draw_boss_extras() -> void:
	var cam := Vector2(camera_x, 0.0)
	# 地面旋风
	for w in whirls:
		var wx: float = float(w["x"]) - camera_x
		var ph: float = float(w["phase"])
		for k in range(4):
			var rr := 14.0 + float(k) * 9.0
			draw_arc(Vector2(wx, GROUND_Y - 26.0 - float(k) * 16.0), rr, ph + float(k), ph + float(k) + PI * 1.3, 18, Color(1, 0, 0, 0.55 - float(k) * 0.1), 3.0)
		draw_circle(Vector2(wx, GROUND_Y - 8.0), 26.0, Color(1, 0, 0, 0.12))
	# 锁定瞄准特效
	if lock_state == "aim":
		var t := Vector2(lock_target.x - camera_x, lock_target.y)
		var blink := 0.5 + 0.5 * sin(elapsed * 30.0)
		draw_arc(t, 34.0, 0, TAU, 40, Color(1, 0, 0, 0.5 + 0.4 * blink), 2.5)
		draw_line(t + Vector2(-46, 0), t + Vector2(-24, 0), Color(1, 0, 0, 0.9), 2.0)
		draw_line(t + Vector2(24, 0), t + Vector2(46, 0), Color(1, 0, 0, 0.9), 2.0)
		draw_line(t + Vector2(0, -46), t + Vector2(0, -24), Color(1, 0, 0, 0.9), 2.0)
		draw_line(t + Vector2(0, 24), t + Vector2(0, 46), Color(1, 0, 0, 0.9), 2.0)
	# 突刺锋（地面刀锋）
	for sp in spikes:
		var a: float = clampf(float(sp["life"]) / maxf(0.01, float(sp["max"])), 0.0, 1.0)
		var bx: float = float(sp["pos"].x) - camera_x
		var top := Vector2(bx, GROUND_Y - 150.0 * a)
		draw_colored_polygon(PackedVector2Array([top, Vector2(bx - 26, GROUND_Y), Vector2(bx + 26, GROUND_Y)]), Color(1, 0, 0, 0.75 * a))
		draw_line(Vector2(bx, GROUND_Y), top, Color(1, 1, 1, 0.85 * a), 3.0)

func _draw_battle_overlays() -> void:
	# 开场动画
	if battle_intro_t > 0.0 and intro_anim.has(boss_id):
		var frames: Array = intro_anim[boss_id]
		if frames.size() > 0:
			var idx := int((2.6 - battle_intro_t) / 2.6 * float(frames.size() - 1))
			idx = clampi(idx, 0, frames.size() - 1)
			var tex: Texture2D = frames[idx]
			var factor := maxf(VIEW.x / tex.get_width(), VIEW.y / tex.get_height())
			var size := tex.get_size() * factor
			draw_texture_rect(tex, Rect2((VIEW - size) * 0.5, size), false)
			draw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(0, 0, 0, 0.25))
			draw_string(ThemeDB.fallback_font, Vector2(470, 600), "BATTLE START", HORIZONTAL_ALIGNMENT_LEFT, -1, 46, WHITE)
	# 必杀插图「！」
	if cutin_active:
		var ct: Texture2D = textures.get("cutin_crimson" if boss_id == "crimson" else "cutin_marysue")
		draw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(0, 0, 0, 0.55))
		if ct:
			var cw := VIEW.x * 0.62
			var ch := cw * ct.get_height() / float(ct.get_width())
			draw_texture_rect(ct, Rect2((VIEW.x - cw) * 0.5, (VIEW.y - ch) * 0.5 - 20, cw, ch), false)
		draw_string(ThemeDB.fallback_font, Vector2(420, 660), "！  必  杀", HORIZONTAL_ALIGNMENT_LEFT, -1, 54, RED if boss_id == "crimson" else HAZARD)
	# 全屏绿闪（无伤害、遮挡视野）
	if green_flash_t > 0.0:
		var ga := 0.28 + 0.22 * absf(sin(elapsed * 9.0))
		draw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(0.51, 1.0, 0.0, ga * clampf(green_flash_t, 0.0, 1.0)))
	# 镜像翻转提示
	if mirror_flip:
		draw_string(ThemeDB.fallback_font, Vector2(430, 150), "镜中世界 · 左右交换", HORIZONTAL_ALIGNMENT_LEFT, -1, 30, HAZARD)
'''

# ---------- 3) 调用点 ----------
# lock_cooldown 变量
if 'var lock_cooldown' not in s:
    s = s.replace('var lock_target := Vector2.ZERO', 'var lock_target := Vector2.ZERO\nvar lock_cooldown := 0', 1)

# _update_boss 里调用 extras（在攻击计时块之后）
s = s.replace('\tif hellfire_timer > 0:',
              '\t_update_boss_extras()\n\tif cutin_active:\n\t\tcutin_timer -= FIXED_DT\n\t\tif cutin_timer <= 0.0:\n\t\t\tcutin_active = false\n\tif battle_intro_t > 0.0:\n\t\tbattle_intro_t = maxf(0.0, battle_intro_t - FIXED_DT)\n\tif hellfire_timer > 0:', 1)

# _draw_battle 里画 extras + overlays
s = s.replace('\t_draw_boss()\n\t_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)',
              '\t_draw_boss()\n\t_draw_boss_extras()\n\t_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)', 1)
s = s.replace('\t_draw_particles_world()\n\t_draw_hud()',
              '\t_draw_particles_world()\n\t_draw_battle_overlays()\n\t_draw_hud()', 1)

# 镜像翻转：左右输入取反
s = s.replace('\tvar axis := (1.0 if input_state.get("right", false) else 0.0) - (1.0 if input_state.get("left", false) else 0.0)',
              '\tvar axis := (1.0 if input_state.get("right", false) else 0.0) - (1.0 if input_state.get("left", false) else 0.0)\n\tif mirror_flip:\n\t\taxis = -axis', 1)

# 演出期间冻结 Boss 攻击
s = s.replace('\tif boss_skill_state != "":\n\t\t_spawn_boss_pattern()\n\t\tboss_attack_timer = 40',
              '\tif cutin_active or battle_intro_t > 0.0:\n\t\tpass\n\telif boss_skill_state != "":\n\t\t_spawn_boss_pattern()\n\t\tboss_attack_timer = 40', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('patched')
