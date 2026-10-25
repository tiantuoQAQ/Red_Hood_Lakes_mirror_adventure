# -*- coding: utf-8 -*-
"""球形态特效重做：拖尾丝带（持久粒子）、红色激光残影、烟雾、流光粒子。数量/尺寸全部加大。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()

start = s.index('func _draw_ball_fx() -> void:')
end = s.index('\n## 镜中世界 BGM', start)

new = '''func _spawn_ball_fx() -> void:
	if not player_ball:
		return
	var vel := player_vel
	var dir := vel.normalized() if vel.length() > 1.0 else Vector2(-1, 0)
	ball_fx_tick += 1
	# 1) 拖尾丝带：每帧 1 片，寿命 0.45 秒，形成连续"拉丝"
	if ball_trail_frames.size() > 0:
		var ttex: Texture2D = ball_trail_frames[ball_fx_tick % ball_trail_frames.size()]
		ball_fx.append({"kind": "ribbon", "pos": player_pos - dir * 20.0, "tex": ttex,
			"rot": dir.angle() + PI * 0.5, "size": randf_range(86.0, 112.0), "life": 0.45, "max": 0.45})
	# 2) 红色激光残影：每 2 帧一道
	if ball_fx_tick % 2 == 0:
		ball_fx.append({"kind": "laser", "pos": player_pos, "dir": dir,
			"len": randf_range(180.0, 320.0), "life": 0.32, "max": 0.32})
	# 3) 烟雾：每 3 帧一团，向上飘
	if ball_fx_tick % 3 == 0:
		ball_fx.append({"kind": "smoke", "pos": player_pos - dir * randf_range(10.0, 60.0) + Vector2(randf_range(-14, 14), randf_range(10, 30)),
			"r": randf_range(9.0, 15.0), "life": 0.9, "max": 0.9, "vel": Vector2(randf_range(-25, 25), randf_range(-60, -20))})
	# 4) 流光火星：每帧 2 颗，带初速度
	for k in range(2):
		var ang := randf() * TAU
		ball_fx.append({"kind": "spark", "pos": player_pos + Vector2(cos(ang), sin(ang)) * randf_range(8.0, 26.0),
			"vel": -dir * randf_range(80.0, 220.0) + Vector2(randf_range(-70, 70), randf_range(-70, 70)),
			"size": randf_range(2.5, 5.5), "life": randf_range(0.3, 0.6), "max": 0.6})

func _update_ball_fx() -> void:
	_spawn_ball_fx()
	for fx in ball_fx:
		fx["life"] = float(fx["life"]) - FIXED_DT
		if fx.has("vel"):
			fx["pos"] = Vector2(fx["pos"]) + Vector2(fx["vel"]) * FIXED_DT
		if str(fx["kind"]) == "smoke":
			fx["r"] = float(fx["r"]) + 34.0 * FIXED_DT
			fx["pos"] = Vector2(fx["pos"]) + Vector2(fx.get("vel", Vector2.ZERO)) * FIXED_DT
	ball_fx = ball_fx.filter(func(x): return float(x.get("life", 0.0)) > 0.0)

func _draw_ball_fx() -> void:
	for fx in ball_fx:
		var k: float = clampf(float(fx["life"]) / maxf(0.01, float(fx.get("max", 1.0))), 0.0, 1.0)
		var pos: Vector2 = Vector2(fx["pos"]) - Vector2(camera_x, 0)
		match str(fx["kind"]):
			"ribbon":
				var ttex: Texture2D = fx["tex"]
				var sz: float = float(fx["size"]) * (0.75 + 0.25 * k)
				draw_set_transform(pos, float(fx["rot"]), Vector2(1, 1))
				draw_texture_rect(ttex, Rect2(Vector2(-sz * 0.5, -sz * 0.5), Vector2(sz, sz)), false,
					Color(1, 1, 1, 0.85 * k))
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
			"laser":
				var dir: Vector2 = fx["dir"]
				var ln: float = float(fx["len"]) * (0.5 + 0.5 * k)
				draw_line(pos, pos - dir * ln, Color(1, 0.1, 0.1, 0.55 * k), 7.0 * k + 1.0)
				draw_line(pos, pos - dir * ln * 0.7, Color(1, 0.7, 0.7, 0.5 * k), 2.5 * k + 0.5)
			"smoke":
				draw_circle(pos, float(fx["r"]), Color(0.62, 0.62, 0.62, 0.28 * k))
				draw_circle(pos, float(fx["r"]) * 0.6, Color(0.8, 0.8, 0.8, 0.16 * k))
			"spark":
				draw_circle(pos, float(fx["size"]) * (0.4 + 0.6 * k), Color(1, 0.25, 0.25, 0.9 * k))
				draw_circle(pos, float(fx["size"]) * 0.45, Color(1, 1, 1, 0.9 * k))
'''
s = s[:start] + new + s[end:]

# 变量
if 'var ball_fx: Array' not in s:
    s = s.replace('var ball_trail_frames: Array = []',
                  'var ball_fx: Array = []            # 球形态粒子池\nvar ball_fx_tick := 0\nvar ball_trail_frames: Array = []', 1)

# 更新：在 _update_player 后调用（找 _update_shots() 调用处）
s = s.replace('\t_update_shots()', '\t_update_ball_fx()\n\t_update_shots()', 1)

# 离开球形态时清空粒子（避免残留）
s = s.replace('func _draw_ball_fx() -> void:', 'func _draw_ball_fx() -> void:', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('ball fx rewritten')
