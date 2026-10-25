# -*- coding: utf-8 -*-
"""修：崩溃/魔姬瞬移/新招式/教程牌位置/红之惨剧改 E 键且能用。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 1) 崩溃：skill_warnings 里可能没有 pos（激光柱用 x） ----------
s = s.replace('''	for warn in skill_warnings:
		var p: Vector2 = warn["pos"] - Vector2(camera_x, 0)''','''	for warn in skill_warnings:
		if not warn.has("pos"):
			continue
		var p: Vector2 = warn["pos"] - Vector2(camera_x, 0)''', 1)

# ---------- 2) 魔姬不再瞬移 ----------
s = s.replace('\t\tboss_pos.x = clampf(boss_pos.x, 1250.0, 2180.0)',
              '\t\t# 不再硬钳制（会瞬移），改用平滑滑回战场内\n'
              '\t\tvar bx_min := _battle_left() + 140.0\n'
              '\t\tvar bx_max := _battle_right() - 140.0\n'
              '\t\tif boss_pos.x < bx_min:\n'
              '\t\t\tboss_pos.x = move_toward(boss_pos.x, bx_min, 420.0 * FIXED_DT)\n'
              '\t\telif boss_pos.x > bx_max:\n'
              '\t\t\tboss_pos.x = move_toward(boss_pos.x, bx_max, 420.0 * FIXED_DT)', 1)
s = s.replace('\t\tboss_pos.x = move_toward(boss_pos.x, target_x, 9.0)\n\t\tboss_pos.y = 420.0',
              '\t\tboss_pos.x = move_toward(boss_pos.x, target_x, 9.0)\n'
              '\t\tboss_pos.y = move_toward(boss_pos.y, 420.0, 300.0 * FIXED_DT)', 1)
s = s.replace('\t\t\tboss_skill_state = ""\n\t\t\tboss_pos.y = 226.0',
              '\t\t\tboss_skill_state = ""', 1)
# 落回空中高度改为每帧平滑（放在 _update_boss 的状态机后）
s = s.replace('\t_update_beam_warnings()',
              '\t# 非硬直状态缓慢回到悬空高度（避免瞬移）\n'
              '\tif boss_skill_state == "" and str(boss_id) == "crimson":\n'
              '\t\tboss_pos.y = move_toward(boss_pos.y, 226.0, 220.0 * FIXED_DT)\n'
              '\t_update_beam_warnings()', 1)

# ---------- 3) 新招式：环形剑阵（阶段1）+ 地刺追击（阶段3） ----------
s = s.replace('''		0:  # 一：火焰弹幕（弱追踪，3 秒后消散）''','''		0:  # 一：火焰弹幕（弱追踪，3 秒后消散）
			if frame % 150 == 0:
				# 环形剑阵：先收缩再向外炸开
				for k in range(14):
					var a0 := TAU * float(k) / 14.0 + elapsed * 0.4
					_spawn_bullet(boss_pos + Vector2(cos(a0), sin(a0)) * 30.0,
						Vector2(cos(a0), sin(a0)) * 180.0, RED, "blade", 3.2, 0.0)
				_spawn_fx_ring(boss_pos, Color(1, 0.3, 0.2, 0.85), 220.0, 0.4, 4.0)''', 1)
s = s.replace('''		3:  # 四：火焰弹雨 + 新月剑气''','''		3:  # 四：地刺追击 + 火焰弹雨 + 新月剑气
			if frame % 90 == 0:
				for k in range(2):
					var sx0 := player_pos.x + (float(k) - 0.5) * 220.0
					spikes.append({"pos": Vector2(clampf(sx0, _battle_left() + 70.0, _battle_right() - 70.0), GROUND_Y - 20.0), "life": 0.5, "max": 0.5})
				sfx_player.play("spike")''', 1)

# ---------- 4) 教程牌只在镜中世界章节（梅贝尔那段不要） ----------
s = s.replace('if walk_target.size() == 0 or story_chapter == "":\n\t\treturn',
              'if walk_target.size() == 0 or story_chapter == "":\n\t\treturn\n\tif story_chapter not in ["wake_talk", "enter_mirror", "mirror"]:\n\t\treturn', 1)

# ---------- 5) 红之惨剧：E 键 + 解锁后可用（不再要求勇气 100） ----------
s = s.replace('"skill": Input.is_key_pressed(KEY_L) or Input.is_key_pressed(KEY_X),',
              '"skill": Input.is_key_pressed(KEY_E),', 1)
s = s.replace('''func _use_red_skill() -> void:
	if player_courage < 100.0:
		return
	player_courage = 0.0''','''func _use_red_skill() -> void:
	# 用户要求：击败魔姬解锁后即可用，消耗 2 MP（不再要求满勇气）
	if not skill_red_tragedy:
		return
	if player_energy < 2:
		return''', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
