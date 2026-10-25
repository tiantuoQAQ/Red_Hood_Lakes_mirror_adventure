# -*- coding: utf-8 -*-
"""修：胜利后镜头持续震动 / 魔姬称号缺失 / 六阶段镜像改为顶层变换 / 玛丽苏前期加密度。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 屏幕震动全局衰减（任何模式都会停）
s = s.replace('\tif banner_timer > 0:\n\t\tbanner_timer -= 1\n\tif screen_shake > 0:',
              '\tif banner_timer > 0:\n\t\tbanner_timer -= 1\n\tif screen_shake > 0:')

if 'func _decay_shake' not in s:
    s = s.replace('func _physics_process(_delta: float) -> void:',
                  'func _physics_process(_delta: float) -> void:\n'
                  '\t_decay_shake()\n', 1)
    s += '''

## 全局屏震衰减（避免胜利/剧情模式下一直抖）
func _decay_shake() -> void:
	if screen_shake > 0.0:
		screen_shake = maxf(0.0, screen_shake - 0.42)
'''
    print('global shake decay added')

# 2) 魔姬称号别名：crimson -> rek_crimson
s = s.replace('"rek_crimson": {"name": "猩红魔姬·雷帝", "title": "自负的暴君", "color": Color(1, 0, 0), "tcolor": Color(1, 0, 0)},',
              '"rek_crimson": {"name": "猩红魔姬·雷帝", "title": "自负的暴君", "color": Color(1, 0, 0), "tcolor": Color(1, 0, 0)},\n'
              '\t"crimson": {"name": "猩红魔姬·雷帝", "title": "自负的暴君", "color": Color(1, 0, 0), "tcolor": Color(1, 0, 0)},', 1)

# 3) 六阶段镜像：在 _draw 顶层包一层世界变换（HUD 前复位）
s = s.replace('''	draw_set_transform(shake, 0.0, Vector2.ONE)
	_draw_background()''','''	draw_set_transform(shake, 0.0, Vector2.ONE)
	# 六阶段：整个世界水平镜像（HUD 前会复位）
	var mirror_world := mirror_flip and mode == Mode.BATTLE
	if mirror_world:
		draw_set_transform(shake + Vector2(VIEW.x, 0), 0.0, Vector2(-1, 1))
	_draw_background()''', 1)
s = s.replace('\t_draw_battle_overlays()\n\t_draw_death_overlay()',
              '\tif mirror_world:\n'
              '\t\tdraw_set_transform(shake, 0.0, Vector2.ONE)\n'
              '\t_draw_battle_overlays()\n\t_draw_death_overlay()', 1)
# 移除旧的 _draw_battle 内层镜像（避免双重翻转）
s = s.replace('''	# 六阶段镜像翻转：整层世界水平镜像
	if mirror_flip:
		draw_set_transform(Vector2(VIEW.x, 0), 0.0, Vector2(-1, 1))
''', '', 1)
s = s.replace('''	_draw_particles_world()
	if mirror_flip:
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	if tragedy_buff_t > 0.0:''','''	_draw_particles_world()
	if tragedy_buff_t > 0.0:''', 1)

# 4) 玛丽苏前期加密度
s = s.replace('''			if frame % 60 == 0:
				for k in range(8):
					var a := TAU * float(k) / 8.0 + elapsed * 0.5
					_spawn_bullet(boss_pos, Vector2(cos(a), sin(a)) * 150.0, HAZARD, "talisman", 5.0, 0.02)''','''			if frame % 40 == 0:
				for k in range(10):
					var a := TAU * float(k) / 10.0 + elapsed * 0.5
					_spawn_bullet(boss_pos, Vector2(cos(a), sin(a)) * 150.0, HAZARD, "talisman", 5.0, 0.02)
			if frame % 75 == 0:
				for k in range(6):
					var a_s := TAU * float(k) / 6.0 - elapsed * 0.8
					_spawn_bullet(boss_pos, Vector2(cos(a_s), sin(a_s)) * 190.0, HAZARD, "yinyang", 5.0, 0.15)''', 1)
s = s.replace('''			if frame % 65 == 0:
				for k in range(6):
					var a2 := -TAU * float(k) / 6.0 + elapsed * 0.9
					_spawn_bullet(boss_pos, Vector2(cos(a2), sin(a2)) * 170.0, HAZARD, "yinyang", 5.5, 0.25)''','''			if frame % 45 == 0:
				for k in range(8):
					var a2 := -TAU * float(k) / 8.0 + elapsed * 0.9
					_spawn_bullet(boss_pos, Vector2(cos(a2), sin(a2)) * 170.0, HAZARD, "yinyang", 5.5, 0.25)''', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
