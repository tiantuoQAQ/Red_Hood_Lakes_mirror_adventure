# -*- coding: utf-8 -*-
"""1) 死亡流程（镜裂→碎镜→回到战场起点→「…是幻觉么。」）
2) 战场整体右移（王座/玛丽苏/Boss 判定点）
3) 弹幕全局加光晕与拖尾（更“光污染”）
"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 2) 战场右移 ----------
s = s.replace('const BATTLE_LEFT := 1080.0', 'const BATTLE_LEFT := 1500.0', 1)
s = s.replace('const BATTLE_RIGHT := 2320.0', 'const BATTLE_RIGHT := 2760.0', 1)
s = s.replace('boss_pos = Vector2(1840.0, 226.0)', 'boss_pos = Vector2(2280.0, 226.0)', 1)
s = s.replace('clampf(player_pos.x + side * 420.0, 1250.0, 2180.0)', 'clampf(player_pos.x + side * 420.0, 1680.0, 2600.0)', 1)
s = s.replace('boss_pos.x = clampf(player_pos.x, 1250.0, 2180.0)', 'boss_pos.x = clampf(player_pos.x, 1680.0, 2600.0)', 1)
s = s.replace('clampf(player_pos.x + randf_range(-200.0, 200.0), 1250.0, 2180.0)', 'clampf(player_pos.x + randf_range(-200.0, 200.0), 1680.0, 2600.0)', 1)

# ---------- 1) 死亡流程 ----------
if 'var death_timer' not in s:
    s = s.replace('var tutorial_timer := 0.0',
                  'var tutorial_timer := 0.0\nvar death_timer := 0.0\nvar death_reason := ""\nvar battle_start_pos := Vector2(500.0, 500.0)', 1)
    print('death vars added')

# 战斗开始时记录起点
s = s.replace('\tplayer_energy = 0.0   # 从 0 起，方便看到擦弹/命中回复',
              '\tplayer_energy = 0.0   # 从 0 起，方便看到擦弹/命中回复\n\tbattle_start_pos = player_pos', 1)

# 死亡触发：血量归零 + 计时
if 'func _start_death' not in s:
    s = s.replace('\tif mode == Mode.BATTLE:\n\t\tplayer_pos.x = clampf(player_pos.x, BATTLE_LEFT, BATTLE_RIGHT)',
                  '\tif mode == Mode.BATTLE and player_hp <= 0 and death_timer <= 0.0:\n'
                  '\t\t_start_death()\n'
                  '\tif mode == Mode.BATTLE:\n\t\tplayer_pos.x = clampf(player_pos.x, BATTLE_LEFT, BATTLE_RIGHT)', 1)
    s += '''

## 死亡流程：镜裂 → 碎镜 → 回到起点 → 幻觉台词
func _start_death() -> void:
	death_timer = 1.6
	player_hp = 0
	bullets.clear()
	_spawn_mirror_shards(46, 1.6)
	screen_shake = 0.9
	sfx_player.play("shards")
	if sfx_player:
		sfx_player.play("explode")

func _update_death() -> void:
	if death_timer <= 0.0:
		return
	death_timer = maxf(0.0, death_timer - FIXED_DT)
	if death_timer <= 0.0:
		# 复活：回到战场起点，满血，清弹，Boss 重置本阶段血量
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
	var k := clampf(death_timer / 1.6, 0.0, 1.0)
	var a := 1.0 - k
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.55 * a))
	# 镜裂：从画面中心放射的裂缝
	var c := VIEW * 0.5
	draw_set_transform(c, 0.0, Vector2(1, 1))
	for i in range(14):
		var ang := TAU * float(i) / 14.0 + 0.21
		var length := 260.0 + 90.0 * sin(float(i) * 2.3)
		var p0 := Vector2.ZERO
		var seg := 4
		for s2 in range(seg):
			var t0 := float(s2) / float(seg)
			var t1 := float(s2 + 1) / float(seg)
			var jitter := Vector2(randf_range(-18, 18), randf_range(-18, 18)) * t1
			var q0 := Vector2(cos(ang), sin(ang)) * length * t0 + jitter * 0.5
			var q1 := Vector2(cos(ang), sin(ang)) * length * t1 + jitter
			draw_line(q0, q1, Color(1, 1, 1, 0.75 * a), 2.6)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# 镜片飞出
	_spawn_mirror_shards(0, 0.0)
	draw_string(ThemeDB.fallback_font, Vector2(500, 370), "镜 碎 了", HORIZONTAL_ALIGNMENT_LEFT, -1, 40, Color(1, 1, 1, a))
'''
    print('death sequence added')

# 更新与绘制调用
s = s.replace('\t_update_boss_extras()', '\t_update_death()\n\t_update_boss_extras()', 1)
s = s.replace('\t_draw_battle_overlays()', '\t_draw_battle_overlays()\n\t_draw_death_overlay()', 1)

# ---------- 3) 弹幕全局光晕 + 拖尾 ----------
if 'btex_key' not in s or True:
    s = s.replace('''		var bdir := Vector2(cos(angle), sin(angle))
		var perp := Vector2(-bdir.y, bdir.x)''','''		var bdir := Vector2(cos(angle), sin(angle))
		var perp := Vector2(-bdir.y, bdir.x)
		# 全局：弹幕拖尾（上一帧位置连线，淡出）
		var trail_p: Vector2 = Vector2(bullet.get("prev_pos", bullet["pos"])) - Vector2(camera_x, 0)
		if trail_p.distance_to(p) > 2.0 and trail_p.distance_to(p) < 160.0:
			draw_line(trail_p, p, Color(color, 0.18), 9.0)
			draw_line(trail_p.lerp(p, 0.4), p, Color(color, 0.30), 5.0)
		# 全局：外圈光晕（所有弹幕都发光）
		draw_circle(p, 26.0, Color(color, 0.06))
		draw_circle(p, 17.0, Color(color, 0.10))''', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
