# -*- coding: utf-8 -*-
"""修：掉光血后被打又变 3 血——旧版死亡逻辑残留（player_hp = 3 并传送回 x=350）与新死亡流程冲突。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

old = '''			if player_hp <= 0:
				player_dying = true
				player_hp = 3
				player_pos = Vector2(350, GROUND_Y - 20)
				bullets.clear()
			return'''
new = '''			if player_hp <= 0:
				player_hp = 0
				_start_death()
			return'''
if old in s:
    s = s.replace(old, new, 1)
    print('old death override removed')

# _start_death 加防重入
s = s.replace('func _start_death() -> void:\n\tdeath_timer = 1.9',
              'func _start_death() -> void:\n\tif death_timer > 0.0:\n\t\treturn\n\tdeath_timer = 1.9', 1)

# 其它直接扣血处统一走 _apply_player_damage（避免重复实现）
s = s.replace('''		if dx < 70.0 and player_grounded and player_hurt_invuln <= 0 and player_dash_invuln <= 0 and not player_ball:
			player_hp -= 1
			player_hurt_invuln = 70
			player_vel.x = signf(player_pos.x - float(w["x"])) * 420.0
			sfx_player.play("hurt")
			if player_hp <= 0:
				player_hp = 0''','''		if dx < 70.0 and player_grounded and player_hurt_invuln <= 0 and player_dash_invuln <= 0 and not player_ball:
			player_vel.x = signf(player_pos.x - float(w["x"])) * 420.0
			_apply_player_damage()''', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
