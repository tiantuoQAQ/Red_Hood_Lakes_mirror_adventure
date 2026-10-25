# -*- coding: utf-8 -*-
"""1) 玛丽苏保留激光但更慢（长预警、低频率）
2) 六阶段左右颠倒真正生效（输入反转 + 画面镜像 + 提示）
3) 五阶段改成完全不透明的绿幕遮挡数秒
4) 结局改为 THANKS FOR PLAYING（不再重跑）
"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 1) 玛丽苏激光：慢频率 + 长预警（阶段 2/3/6 各一处） ----------
s = s.replace('''		2:  # 叁 · 镜廊：符纸雨（稀疏）+ 阴阳球''','''		2:  # 叁 · 镜廊：符纸雨（稀疏）+ 阴阳球
			if frame % 200 == 0:
				var lx0 := clampf(player_pos.x + randf_range(-200.0, 200.0), _battle_left() + 90.0, _battle_right() - 90.0)
				for i2 in range(30):
					skill_warnings.append({"kind": "beam", "x": lx0, "life": 0.5, "color": HAZARD}) if false else null
				_beam_warning(lx0)''', 1)

if 'func _beam_warning' not in s:
    s += '''

## 激光预警：先亮 0.7 秒（画线 + 地面光圈），再落柱
var beam_warning_list: Array = []

func _beam_warning(x: float) -> void:
	beam_warning_list.append({"x": x, "t": 0.7})

func _update_beam_warnings() -> void:
	for w in beam_warning_list:
		w["t"] = float(w["t"]) - FIXED_DT
		if float(w["t"]) <= 0.0:
			_spawn_beam(float(w["x"]), 0.9)
	beam_warning_list = beam_warning_list.filter(func(w): return float(w["t"]) > 0.0)

func _draw_beam_warnings() -> void:
	for w in beam_warning_list:
		var bx: float = float(w["x"]) - camera_x
		var k: float = clampf(float(w["t"]) / 0.7, 0.0, 1.0)
		draw_line(Vector2(bx, 40), Vector2(bx, GROUND_Y), Color(0.51, 1, 0, 0.30 + 0.45 * (1.0 - k)), 3.0)
		draw_circle(Vector2(bx, GROUND_Y - 12), 28.0 + 10.0 * (1.0 - k), Color(0.51, 1, 0, 0.22))
'''
    print('beam warning helpers added')

s = s.replace('\t_update_death()', '\t_update_beam_warnings()\n\t_update_death()', 1)
s = s.replace('\t_draw_battle_bounds_fx()', '\t_draw_beam_warnings()\n\t_draw_battle_bounds_fx()', 1)

# 阶段 6 也来一发慢激光
s = s.replace('''			if frame % 34 == 0:
				for k in range(6):
					var a7 := TAU * float(k) / 6.0 - elapsed''','''			if frame % 220 == 0:
				var lx1 := clampf(player_pos.x + randf_range(-160.0, 160.0), _battle_left() + 90.0, _battle_right() - 90.0)
				_beam_warning(lx1)
			if frame % 34 == 0:
				for k in range(6):
					var a7 := TAU * float(k) / 6.0 - elapsed''', 1)

# ---------- 2) 六阶段左右颠倒：输入反转 + 画面水平镜像 ----------
s = s.replace('\tif mirror_flip:\n\t\taxis = -axis', '\tif mirror_flip:\n\t\taxis = -axis   # 镜中世界：左右颠倒', 1)
# 画面镜像：在 _draw_battle 里整体翻转世界层（不含 HUD）
s = s.replace('func _draw_battle() -> void:\n\t_draw_world_grid()',
              'func _draw_battle() -> void:\n'
              '\t# 六阶段镜像翻转：整层世界水平镜像\n'
              '\tif mirror_flip:\n'
              '\t\tdraw_set_transform(Vector2(VIEW.x, 0), 0.0, Vector2(-1, 1))\n'
              '\t_draw_world_grid()', 1)
s = s.replace('\t_draw_particles_world()\n\tif tragedy_buff_t > 0.0:',
              '\t_draw_particles_world()\n'
              '\tif mirror_flip:\n'
              '\t\tdraw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)\n'
              '\tif tragedy_buff_t > 0.0:', 1)

# ---------- 3) 五阶段：不透明绿幕遮挡 ----------
s = s.replace('\t\t\tgreen_flash_t = 1.0\n\t\t\tif frame % 70 == 0:',
              '\t\t\tif flash_green_t <= 0.0 and frame % 180 == 0:\n\t\t\t\tflash_green_t = 2.2\n\t\t\tif frame % 70 == 0:', 1)
if 'var flash_green_t' not in s:
    s = s.replace('var green_flash_t := 0.0      # 全屏绿闪剩余秒数',
                  'var green_flash_t := 0.0      # 半透明绿闪\nvar flash_green_t := 0.0      # 完全不透明绿幕遮挡', 1)
s = s.replace('\tif green_flash_t > 0.0:\n\t\tgreen_flash_t = maxf(0.0, green_flash_t - FIXED_DT)',
              '\tif green_flash_t > 0.0:\n\t\tgreen_flash_t = maxf(0.0, green_flash_t - FIXED_DT)\n'
              '\tif flash_green_t > 0.0:\n\t\tflash_green_t = maxf(0.0, flash_green_t - FIXED_DT)', 1)
# 绘制：完全不透明绿幕
s = s.replace('\tdraw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(0.51, 1.0, 0.0, ga * clampf(green_flash_t, 0.0, 1.0)))',
              '\tdraw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(0.51, 1.0, 0.0, ga * clampf(green_flash_t, 0.0, 1.0)))\n'
              '\tif flash_green_t > 0.0:\n'
              '\t\t# 完全不透明的绿幕：彻底挡住视野\n'
              '\t\tvar fa := 1.0 if flash_green_t > 0.25 else flash_green_t / 0.25\n'
              '\t\tdraw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(0.51, 1.0, 0.0, fa))', 1)

# ---------- 4) 结局：THANKS FOR PLAYING ----------
s = s.replace('''func _draw_end() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.5))
	draw_string(ThemeDB.fallback_font, Vector2(430, 300), "主线 · 终", HORIZONTAL_ALIGNMENT_LEFT, -1, 48, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(370, 370), "镜面碎成了千万片，每一片里都有她", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, CYAN)
	draw_string(ThemeDB.fallback_font, Vector2(450, 500), "ENTER / SPACE 重新开始", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, GREY)''',
'''func _draw_end() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.78))
	draw_string(ThemeDB.fallback_font, Vector2(300, 300), "THANKS FOR PLAYING", HORIZONTAL_ALIGNMENT_LEFT, -1, 46, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(330, 372), "红之镜 · DEMO", HORIZONTAL_ALIGNMENT_LEFT, -1, 26, RED)
	draw_string(ThemeDB.fallback_font, Vector2(352, 418), "镜面碎成了千万片，每一片里都有她", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(0.85, 0.85, 0.85))
	draw_string(ThemeDB.fallback_font, Vector2(430, 540), "感谢试玩", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(0.6, 0.6, 0.6))''', 1)
# 结局不再返回标题（保留原地，不重开）
s = s.replace('func _update_end() -> void:\n\tif _just("confirm"):\n\t\tmode = Mode.TITLE',
              'func _update_end() -> void:\n\t# 结局停留，不再重跑游戏（用户要求）\n\tif _just("confirm"):\n\t\tpass', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
