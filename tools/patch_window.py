# -*- coding: utf-8 -*-
"""窗口缩放：确保拉伸模式正确，并给出全屏/放大窗口的快捷键（F11 全屏、F10 放大 1600x900）。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

if '_setup_window_stretch' not in s:
    s = s.replace('func _ready() -> void:', 'func _ready() -> void:\n\t_setup_window_stretch()', 1)
    s += '''

## 让窗口放大时画面等比放大（1280×720 逻辑分辨率）
func _setup_window_stretch() -> void:
	var win := get_window()
	if win == null:
		return
	win.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	win.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
	win.content_scale_size = Vector2i(1280, 720)
	win.min_size = Vector2i(960, 540)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		# F11 全屏切换
		if event.keycode == KEY_F11:
			var win := get_window()
			win.mode = Window.MODE_WINDOWED if win.mode == Window.MODE_FULLSCREEN else Window.MODE_FULLSCREEN
			get_viewport().set_input_as_handled()
		# F10 放大窗口到 1600×900
		elif event.keycode == KEY_F10:
			var win2 := get_window()
			win2.mode = Window.MODE_WINDOWED
			win2.size = Vector2i(1600, 900)
			get_viewport().set_input_as_handled()
'''
    print('window stretch setup appended')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
