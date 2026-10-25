# -*- coding: utf-8 -*-
"""死亡机制修正：死亡有代价（Boss 不回血）、计死亡次数并显示、死亡期间禁操作。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 死亡计数变量
if 'var death_count' not in s:
    s = s.replace('var death_timer := 0.0', 'var death_timer := 0.0\nvar death_count := 0', 1)

# 2) 战斗开始时清零
s = s.replace('\tbattle_start_pos = player_pos', '\tbattle_start_pos = player_pos\n\tdeath_count = 0', 1)

# 3) 死亡触发时 +1
s = s.replace('''	death_timer = 1.9
	death_flash = 1.0
	player_hp = 0''','''	death_timer = 1.9
	death_flash = 1.0
	death_count += 1
	player_hp = 0''', 1)

# 4) 复活不再重置 Boss 血量（死亡有代价：Boss 保持当前阶段与血量）
s = s.replace('\t\tboss_hp = boss_max_hp\n\t\tbanner = "……是幻觉么。"',
              '\t\t# Boss 血量不重置：死亡只让你自己重来，战斗进度保留（死几次都别想白嫖）\n'
              '\t\tbanner = "……是幻觉么。（第 %d 次）" % death_count', 1)

# 5) 死亡演出期间禁止玩家操作
s = s.replace('func _update_player() -> void:\n',
              'func _update_player() -> void:\n\tif death_timer > 0.0:\n\t\tplayer_vel = Vector2.ZERO\n\t\treturn\n', 1)

# 6) HUD 显示死亡次数
s = s.replace('draw_string(ThemeDB.fallback_font, Vector2(1040, 675), "擦弹链 %d" % player_graze_chain',
              'if death_count > 0:\n\t\tdraw_string(ThemeDB.fallback_font, Vector2(40, 700), "DEATH × %d" % death_count, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 0.35, 0.35))\n\t\tdraw_string(ThemeDB.fallback_font, Vector2(1040, 675), "擦弹链 %d" % player_graze_chain', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
