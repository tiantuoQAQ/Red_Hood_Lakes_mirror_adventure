# -*- coding: utf-8 -*-
"""让苏醒回归测试适应剧情新增台词（不再强依赖当前句就是「哪里」）。"""
import io

p = 'test/godot_direction_wake_test.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

old = '''	_expect(game.story_cmd.get("t") == "say" and "哪里" in game.story_text and game.story_who == "rek", "Rek wakes and asks where she is before meeting Norden")
	_expect(game.story_fade < .02, "The screen has brightened before the wake-up line")'''
new = '''	# 台词可能新增缓冲句：向后推进直到看到「哪里」这一句（或进入走位）
	var saw_where := "哪里" in game.story_text and game.story_who == "rek"
	for extra in range(30):
		if saw_where or game.mode == game.Mode.WALK:
			break
		game.previous_input = {}
		game.scripted_input = {"confirm": true}
		game._physics_process(1.0 / 60.0)
		if "哪里" in game.story_text and game.story_who == "rek":
			saw_where = true
	_expect(saw_where, "Rek wakes and asks where she is before meeting Norden")
	_expect(game.story_fade < .02, "The screen has brightened before the wake-up line")'''
if old in s:
    s = s.replace(old, new, 1)
    print('wake assertion made tolerant')

old2 = '''	game.previous_input = {}
	game.scripted_input = {"confirm": true}
	game._physics_process(1.0/60.0)
	_expect(game.mode == game.Mode.WALK, "Wake-up dialogue continues to exploration")'''
new2 = '''	game.previous_input = {}
	for extra in range(60):
		if game.mode == game.Mode.WALK:
			break
		game.previous_input = {}
		game.scripted_input = {"confirm": true}
		game._physics_process(1.0/60.0)
	_expect(game.mode == game.Mode.WALK, "Wake-up dialogue continues to exploration")'''
if old2 in s:
    s = s.replace(old2, new2, 1)
    print('walk transition made tolerant')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
