# -*- coding: utf-8 -*-
"""死亡镜碎重做：真实碎片（不规则多边形 + 白边反光 + 旋转飞出）+ 分叉裂纹 + 冲击白闪。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 变量 ----------
if 'var death_shards' not in s:
    s = s.replace('var death_timer := 0.0',
                  'var death_timer := 0.0\nvar death_shards: Array = []\nvar death_flash := 0.0', 1)

# ---------- 生成真实碎片 ----------
start = s.index('func _start_death() -> void:')
end = s.index('\nfunc ', s.index('func _draw_death_overlay', start))
new = '''func _start_death() -> void:
	death_timer = 1.9
	death_flash = 1.0
	player_hp = 0
	bullets.clear()
	screen_shake = 1.2
	sfx_player.play("shards")
	sfx_player.play("explode")
	# 生成不规则玻璃碎片（以命中点为中心向外炸开）
	death_shards.clear()
	var center := player_pos - Vector2(camera_x, 0) + Vector2(0, -20)
	for i in range(34):
		var ang := TAU * float(i) / 34.0 + randf_range(-0.12, 0.12)
		var dist := randf_range(30.0, 210.0)
		var px := center + Vector2(cos(ang), sin(ang)) * dist
		# 多边形顶点（3~5 边，不规则）
		var pts := PackedVector2Array()
		var n := randi_range(3, 5)
		var r0 := randf_range(18.0, 52.0)
		for k in range(n):
			var a2 := TAU * float(k) / float(n) + randf_range(-0.35, 0.35)
			var rr := r0 * randf_range(0.55, 1.25)
			pts.append(Vector2(cos(a2), sin(a2)) * rr)
		death_shards.append({
			"pos": px,
			"vel": Vector2(cos(ang), sin(ang)) * randf_range(160.0, 620.0),
			"rot": randf_range(0.0, TAU),
			"spin": randf_range(-7.0, 7.0),
			"life": randf_range(1.1, 1.9),
			"max": 1.9,
			"pts": pts,
			"tint": randf_range(0.55, 1.0),
		})

func _update_death() -> void:
	if death_timer <= 0.0:
		return
	death_timer = maxf(0.0, death_timer - FIXED_DT)
	death_flash = maxf(0.0, death_flash - FIXED_DT * 3.2)
	for sh in death_shards:
		sh["life"] = float(sh["life"]) - FIXED_DT
		sh["pos"] = Vector2(sh["pos"]) + Vector2(sh["vel"]) * FIXED_DT
		sh["vel"] = Vector2(sh["vel"]) * 0.985 + Vector2(0, 520.0) * FIXED_DT
		sh["rot"] = float(sh["rot"]) + float(sh["spin"]) * FIXED_DT
	death_shards = death_shards.filter(func(x): return float(x.get("life", 0.0)) > 0.0)
	if death_timer <= 0.0:
		player_hp = PLAYER_MAX_HP
		player_pos = battle_start_pos
		player_vel = Vector2.ZERO
		player_hurt_invuln = 90
		bullets.clear()
		spikes.clear()
		whirls.clear()
		boss_hp = boss_max_hp
		banner = "……是幻觉么。"
		banner_timer = 170
		_spawn_fx_ring(player_pos, Color(1, 1, 1, 0.9), 260.0, 0.5, 5.0)

func _draw_death_overlay() -> void:
	if death_timer <= 0.0:
		return
	var k := clampf(death_timer / 1.9, 0.0, 1.0)          # 1 → 0
	var dark := clampf(1.0 - k * 1.5, 0.0, 1.0)           # 越到后面越黑
	# 玻璃碎片
	for sh in death_shards:
		var lk := clampf(float(sh["life"]) / float(sh["max"]), 0.0, 1.0)
		var pts: PackedVector2Array = sh["pts"]
		var pos: Vector2 = sh["pos"]
		var rot: float = sh["rot"]
		var world := PackedVector2Array()
		for pv in pts:
			world.append(pos + pv.rotated(rot))
		# 玻璃本体：半透明白 + 冷灰
		var tint: float = float(sh["tint"])
		draw_colored_polygon(world, Color(0.82 * tint, 0.86 * tint, 0.92 * tint, 0.42 * lk))
		# 高光边（玻璃反光）
		var closed := world.duplicate()
		closed.append(world[0])
		draw_polyline(closed, Color(1, 1, 1, 0.85 * lk), 1.6)
		# 内层反光条
		if world.size() >= 3:
			draw_line(world[0], world[1], Color(1, 1, 1, 0.55 * lk), 3.0)
	# 分叉裂纹（从中心向外，随时间变细）
	var c := Vector2(640, 340)
	for i in range(16):
		var ang := TAU * float(i) / 16.0 + 0.13
		var length := (240.0 + 120.0 * sin(float(i) * 2.7)) * (1.0 - k * 0.35)
		var p0 := c
		var dir := Vector2(cos(ang), sin(ang))
		var seg := 5
		for s2 in range(seg):
			var t0 := float(s2) / float(seg)
			var t1 := float(s2 + 1) / float(seg)
			var jitter := Vector2(randf_range(-14, 14), randf_range(-14, 14)) * t1
			var q0 := c + dir * length * t0 + jitter * 0.6
			var q1 := c + dir * length * t1 + jitter
			draw_line(q0, q1, Color(1, 1, 1, (0.9 - float(s2) * 0.12) * (1.0 - k)), 3.2 - float(s2) * 0.45)
			# 分叉
			if s2 == 2:
				var bdir := (dir.rotated(randf_range(-0.9, 0.9))).normalized()
				draw_line(q1, q1 + bdir * randf_range(60.0, 130.0), Color(0.9, 0.9, 0.95, 0.5 * (1.0 - k)), 1.5)
	# 冲击白闪
	if death_flash > 0.0:
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(1, 1, 1, 0.85 * death_flash))
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.45 * dark))
	if death_timer > 0.9:
		var ta := clampf((death_timer - 0.9) / 0.6, 0.0, 1.0)
		draw_string(ThemeDB.fallback_font, Vector2(520, 372), "镜 碎 了", HORIZONTAL_ALIGNMENT_LEFT, -1, 40, Color(1, 1, 1, ta))
'''
s = s[:start] + new + s[end:]

io.open(p, 'w', encoding='utf-8').write(s)
print('death shatter rewritten')
