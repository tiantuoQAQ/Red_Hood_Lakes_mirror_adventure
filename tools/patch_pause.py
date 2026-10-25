# -*- coding: utf-8 -*-
"""暂停可退出：P/Esc 切换，暂停面板支持鼠标点击继续、M 静音、R 回标题。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) Esc 也能暂停/继续
s = s.replace('"pause": Input.is_key_pressed(KEY_P),',
              '"pause": Input.is_key_pressed(KEY_P) or Input.is_key_pressed(KEY_ESCAPE),', 1)

# 2) 暂停时点击画面 / 按 Enter 继续（不依赖按钮）
s = s.replace('\tif _just("restart") and mode != Mode.TITLE:',
              '\tif paused and (_just("confirm") or _just("shoot")):\n'
              '\t\tpaused = false\n'
              '\tif _just("restart") and mode != Mode.TITLE:', 1)

# 3) 暂停面板：画两个可点区域提示（继续 / 回标题），并支持鼠标点击
s = s.replace('''	if paused:
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.55))
		draw_string(ThemeDB.fallback_font, Vector2(570, 360), "PAUSED", HORIZONTAL_ALIGNMENT_LEFT, -1, 36, WHITE)''',
'''	if paused:
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.62))
		draw_string(ThemeDB.fallback_font, Vector2(556, 250), "PAUSED", HORIZONTAL_ALIGNMENT_LEFT, -1, 40, WHITE)
		# 继续游戏（点击或按 Enter）
		var resume_rect := Rect2(500, 300, 280, 56)
		var hover_resume := resume_rect.has_point(get_local_mouse_position())
		draw_rect(resume_rect, Color(0.08, 0.08, 0.10, 0.95))
		draw_rect(resume_rect, Color(1, 1, 1, 0.85 if hover_resume else 0.5), false, 2.0)
		draw_string(ThemeDB.fallback_font, Vector2(548, 336), "继续游戏  (ENTER / 鼠标左键)", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, WHITE)
		# 回标题
		var title_rect := Rect2(500, 372, 280, 48)
		var hover_title := title_rect.has_point(get_local_mouse_position())
		draw_rect(title_rect, Color(0.08, 0.08, 0.10, 0.95))
		draw_rect(title_rect, Color(1, 0.3, 0.3, 0.85 if hover_title else 0.45), false, 2.0)
		draw_string(ThemeDB.fallback_font, Vector2(556, 402), "回到标题  (R)", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(1, 0.6, 0.6))
		if hover_resume and _mouse_clicked():
			paused = false
		elif hover_title and _mouse_clicked():
			mode = Mode.TITLE
			paused = false
			_stop_music()
			_stop_battle_bgm()''', 1)

# 4) 鼠标点击检测辅助
if 'func _mouse_clicked' not in s:
    s += '''

## 本帧是否有点击（鼠标左键按下沿）
var _mouse_was_down := false

func _mouse_clicked() -> bool:
	var down := Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
	var clicked := down and not _mouse_was_down
	_mouse_was_down = down
	return clicked
'''
    print('mouse click helper added')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
