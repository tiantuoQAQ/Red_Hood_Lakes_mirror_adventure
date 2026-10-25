# -*- coding: utf-8 -*-
"""作弊键 L（免费红之惨剧，演示跳关用）+ 技能说明更新。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 新增 cheat_skill 输入（L 键），与正常 skill(E) 区分
s = s.replace('"skill": Input.is_key_pressed(KEY_E),',
              '"skill": Input.is_key_pressed(KEY_E),\n\t\t"cheat_skill": Input.is_key_pressed(KEY_L),', 1)

# 2) 作弊技能实现：跳过解锁与 MP 检查，直接释放
if 'func _use_cheat_tragedy' not in s:
    s = s.replace('\tif _just("hellfire"):\n\t\t_use_hellfire()',
                  '\tif _just("hellfire"):\n\t\t_use_hellfire()\n'
                  '\tif _just("cheat_skill"):\n\t\t_use_cheat_tragedy()', 1)
    s += '''

## 作弊键 L：免费红之惨剧（演示/跳关用，不消耗 MP、无需解锁）
func _use_cheat_tragedy() -> void:
	bullets.clear()
	spikes.clear()
	beam_warning_list.clear()
	boss_hp = maxf(0.0, boss_hp - 120.0)
	player_hp = mini(PLAYER_MAX_HP, player_hp + 2)
	tragedy_buff_t = 20.0
	player_hurt_invuln = 120
	banner = "红之惨剧（演示）"
	banner_timer = 90
	screen_shake = 12.0
	_spawn_mirror_shards(30, 1.3)
	_spawn_fx_ring(boss_pos, Color(1, 0.2, 0.2, 0.9), 420.0, 0.5, 6.0)
	sfx_player.play("skill")
'''
    print('cheat tragedy added')

# 3) 技能说明更新
s = s.replace('''	draw_string(ThemeDB.fallback_font, Vector2(150, 502), "· 枪火击溃：一次性大范围冲击，清掉近身弹幕", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 530), "· 业火：持续灼烧 Boss，造成多段伤害", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 558), "· 红之惨剧：回复 2 HP，并强化剑气 20 秒", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))''',
'''	draw_string(ThemeDB.fallback_font, Vector2(150, 502), "· 红之惨剧（E）：全图清除弹幕，并对 Boss 造成大伤害，回复 2 HP + 强化剑气 20 秒", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 530), "· 枪火击溃（C）：在鼠标位置造成范围伤害", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 558), "· 业火（V）：全屏伤害，无需瞄准", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))''', 1)

# 技能格说明
s = s.replace('var desc: String = str({"skill_icon_red": "回2HP + 20秒强化剑气"}.get(slot["tex"], ""))',
              'var desc: String = str({"skill_icon_red": "清弹+伤害+回2HP", "skill_icon_gun": "鼠标处范围伤害", "skill_icon_hell": "全屏伤害"}.get(slot["tex"], ""))', 1)

# 教程里的按键行也改
s = s.replace('["L", "红之惨剧（击败魔姬后解锁，2 MP）", "", ""]',
              '["E", "红之惨剧（击败魔姬后解锁，2 MP）", "L", "演示键：免费红之惨剧"]', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
