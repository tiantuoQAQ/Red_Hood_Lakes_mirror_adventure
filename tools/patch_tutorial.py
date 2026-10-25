# -*- coding: utf-8 -*-
"""诺登对话结束后：进入走位段自动弹出操作教程（背景压暗 + 字幕 + 技能说明）。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

if 'var tutorial_timer' not in s:
    s = s.replace('var ball_hint_t := 0.0',
                  'var ball_hint_t := 0.0\nvar tutorial_timer := 0.0\nvar tutorial_shown := false', 1)
    print('tutorial vars added')

# 触发展示：诺登对话结束进入走位段（wake_talk / enter_mirror / mirror 第一章）
if 'tutorial_timer = 18.0' not in s:
    s = s.replace('\t_start_walk({"t": "walk"}',
                  '\t_start_walk({"t": "walk"}') # no-op safeguard
    s = s.replace('\t_update_npc_glow()',
                  '\tif not tutorial_shown and story_chapter in ["wake_talk", "enter_mirror", "mirror"] and mode == Mode.WALK:\n'
                  '\t\ttutorial_shown = true\n'
                  '\t\ttutorial_timer = 20.0\n'
                  '\t_update_npc_glow()', 1)
    print('tutorial trigger added')

# 绘制：在 _draw_walk 末尾（_draw_hud 之前）画教程面板
if 'func _draw_tutorial' not in s:
    s = s.replace('\t_draw_particles_world()\n\tdraw_string(ThemeDB.fallback_font, Vector2(40, 48)',
                  '\t_draw_tutorial()\n\t_draw_particles_world()\n\tdraw_string(ThemeDB.fallback_font, Vector2(40, 48)', 1)
    s += '''

## 操作教程（背景压暗 + 字幕）
func _draw_tutorial() -> void:
	if tutorial_timer <= 0.0:
		return
	var a := clampf(tutorial_timer / 1.2, 0.0, 1.0)   # 最后 1.2 秒淡出
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.62 * a))
	draw_rect(Rect2(80, 90, 1120, 560), Color(0.02, 0.02, 0.03, 0.90 * a))
	draw_rect(Rect2(80, 90, 1120, 560), Color(1, 1, 1, 0.25 * a), false, 2.0)
	draw_string(ThemeDB.fallback_font, Vector2(112, 140), "操作指南", HORIZONTAL_ALIGNMENT_LEFT, -1, 30, Color(1, 1, 1, a))
	draw_line(Vector2(112, 156), Vector2(1168, 156), Color(1, 1, 1, 0.35 * a), 1.5)

	var lines := [
		["A / D", "左右移动", "SHIFT / K / 鼠标右键", "冲刺（0.2 秒无敌）"],
		["SPACE", "跳跃", "空中 W + 冲刺", "化为光球（无敌，可穿越弹幕）"],
		["J / Z / 鼠标左键", "射击", "P / ESC", "暂停 / 继续"],
		["C", "枪火击溃（2 MP）", "V", "业火（2 MP）"],
		["L", "红之惨剧（击败魔姬后解锁，2 MP）", "", ""],
	]
	var y := 200.0
	for row in lines:
		draw_string(ThemeDB.fallback_font, Vector2(120, y), "【" + str(row[0]) + "】", HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Color(1, 0.45, 0.45, a))
		draw_string(ThemeDB.fallback_font, Vector2(330, y), str(row[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Color(1, 1, 1, a))
		if str(row[2]) != "":
			draw_string(ThemeDB.fallback_font, Vector2(700, y), "【" + str(row[2]) + "】", HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Color(0.6, 0.85, 1, a))
			draw_string(ThemeDB.fallback_font, Vector2(880, y), str(row[3]), HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(1, 1, 1, a))
		y += 44.0

	draw_string(ThemeDB.fallback_font, Vector2(120, 470), "技能效果：", HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Color(1, 1, 1, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 502), "· 枪火击溃：一次性大范围冲击，清掉近身弹幕", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 530), "· 业火：持续灼烧 Boss，造成多段伤害", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 558), "· 红之惨剧：回复 2 HP，并强化剑气 20 秒", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 594), "MP 回复：命中敌人 + 擦弹（贴近弹幕但不被击中）", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(1, 0.8, 0.4, a))
	draw_string(ThemeDB.fallback_font, Vector2(930, 624), "ENTER 继续", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(0.75, 0.75, 0.75, a))
'''
    print('tutorial draw appended')

# 每帧计时 & 可跳过
s = s.replace('\tif ball_hint_t > 0.0 and mode == Mode.WALK:',
              '\tif tutorial_timer > 0.0:\n'
              '\t\ttutorial_timer = maxf(0.0, tutorial_timer - FIXED_DT)\n'
              '\t\tif _just("confirm") or _just("skip"):\n'
              '\t\t\ttutorial_timer = 0.0\n'
              '\tif ball_hint_t > 0.0 and mode == Mode.WALK:', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
