# -*- coding: utf-8 -*-
"""1) 修教程卡住（计时/关闭挪到 _physics_process，任何模式都生效）
2) 窗口默认 1920x1080
3) Boss 战边界跟随 Boss（±700，随位置移动）
4) 魔姬不再瞬移（相位里的直接赋值改成快速移动）
"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 1) 教程计时挪到 _physics_process ----------
# 去掉 battle draw 里的教程计时块
s = s.replace('''	if tutorial_timer > 0.0:
		tutorial_timer = maxf(0.0, tutorial_timer - FIXED_DT)
		if _just("confirm") or _just("skip"):
			tutorial_timer = 0.0
''', '', 1)
# 在 _physics_process 的输入处理区加
s = s.replace('\tif _just("restart") and mode != Mode.TITLE:',
              '\tif tutorial_timer > 0.0:\n'
              '\t\ttutorial_timer = maxf(0.0, tutorial_timer - FIXED_DT)\n'
              '\t\tif _just("confirm") or _just("skip") or _just("shoot"):\n'
              '\t\t\ttutorial_timer = 0.0\n'
              '\tif _just("restart") and mode != Mode.TITLE:', 1)
print('tutorial timer moved')

# ---------- 3) 动态边界（跟随 Boss） ----------
if 'func _battle_left()' not in s:
    s = s.replace('const BATTLE_RIGHT := 2760.0',
                  'const BATTLE_RIGHT := 2760.0\nconst BATTLE_HALF := 700.0', 1)
    s += '''

## 战场边界跟随 Boss：Boss 左右各 ±700，并限制在地图内
func _battle_left() -> float:
	return clampf(boss_pos.x - BATTLE_HALF, 120.0, WORLD_W - 200.0)

func _battle_right() -> float:
	return clampf(boss_pos.x + BATTLE_HALF, 120.0 + 400.0, WORLD_W - 120.0)
'''
    print('dynamic bounds funcs added')

# 玩家钳制
s = s.replace('\t\tplayer_pos.x = clampf(player_pos.x, BATTLE_LEFT, BATTLE_RIGHT)',
              '\t\tplayer_pos.x = clampf(player_pos.x, _battle_left(), _battle_right())', 1)
# 边界火焰绘制
s = s.replace('\tvar left_screen := BATTLE_LEFT - camera_x', '\tvar left_screen := _battle_left() - camera_x', 1)
s = s.replace('\tvar right_screen := BATTLE_RIGHT - camera_x', '\tvar right_screen := _battle_right() - camera_x', 1)
s = s.replace('if px < (BATTLE_LEFT - camera_x) + near:', 'if px < (_battle_left() - camera_x) + near:', 1)
s = s.replace('var t := clampf(1.0 - (px - (BATTLE_LEFT - camera_x)) / near, 0.0, 1.0)',
              'var t := clampf(1.0 - (px - (_battle_left() - camera_x)) / near, 0.0, 1.0)', 1)
s = s.replace('elif px > (BATTLE_RIGHT - camera_x) - near:', 'elif px > (_battle_right() - camera_x) - near:', 1)
s = s.replace('var t2 := clampf(1.0 - ((BATTLE_RIGHT - camera_x) - px) / near, 0.0, 1.0)',
              'var t2 := clampf(1.0 - ((_battle_right() - camera_x) - px) / near, 0.0, 1.0)', 1)
# 玛丽苏激光位置钳制
s = s.replace('clampf(player_pos.x + randf_range(-260.0, 260.0), BATTLE_LEFT, BATTLE_RIGHT)',
              'clampf(player_pos.x + randf_range(-260.0, 260.0), _battle_left(), _battle_right())', 1)
s = s.replace('clampf(player_pos.x + randf_range(-320.0, 320.0), BATTLE_LEFT, BATTLE_RIGHT)',
              'clampf(player_pos.x + randf_range(-320.0, 320.0), _battle_left(), _battle_right())', 1)
s = s.replace('randf_range(BATTLE_LEFT + 80.0, BATTLE_RIGHT - 80.0)',
              'randf_range(_battle_left() + 80.0, _battle_right() - 80.0)', 1)
s = s.replace('clampf(player_pos.x + randf_range(-340.0, 340.0), BATTLE_LEFT, BATTLE_RIGHT)',
              'clampf(player_pos.x + randf_range(-340.0, 340.0), _battle_left(), _battle_right())', 1)
s = s.replace('clampf(player_pos.x + randf_range(-220.0, 220.0), BATTLE_LEFT + 120.0, BATTLE_RIGHT - 120.0)',
              'clampf(player_pos.x + randf_range(-220.0, 220.0), _battle_left() + 120.0, _battle_right() - 120.0)', 1)

# ---------- 4) 魔姬不瞬移 ----------
s = s.replace('\t\t\t\tboss_pos.x = clampf(player_pos.x, 1680.0, 2600.0)',
              '\t\t\t\tboss_slide_to = clampf(player_pos.x, _battle_left() + 140.0, _battle_right() - 140.0)', 1)
s = s.replace('\t\t\t\tboss_pos.x = clampf(player_pos.x + randf_range(-200.0, 200.0), 1680.0, 2600.0)',
              '\t\t\t\tboss_slide_to = clampf(player_pos.x + randf_range(-200.0, 200.0), _battle_left() + 140.0, _battle_right() - 140.0)', 1)
if 'var boss_slide_to' not in s:
    s = s.replace('var boss_rush_side := 1.0', 'var boss_rush_side := 1.0\nvar boss_slide_to := -1.0', 1)
# 每帧平滑滑动到目标
s = s.replace('\t_update_death()', '\tif boss_slide_to > 0.0:\n'
              '\t\tboss_pos.x = move_toward(boss_pos.x, boss_slide_to, 900.0 * FIXED_DT)\n'
              '\t\tif absf(boss_pos.x - boss_slide_to) < 4.0:\n'
              '\t\t\tboss_pos.x = boss_slide_to\n'
              '\t\t\tboss_slide_to = -1.0\n'
              '\t_update_death()', 1)

# ---------- 2) 窗口默认 1920x1080 ----------
io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')

pg = 'project.godot'
t = io.open(pg, encoding='utf-8').read()
t = t.replace('window/size/window_width_override=1600', 'window/size/window_width_override=1920')
t = t.replace('window/size/window_height_override=900', 'window/size/window_height_override=1080')
io.open(pg, 'w', encoding='utf-8').write(t)
print('window default 1920x1080')
