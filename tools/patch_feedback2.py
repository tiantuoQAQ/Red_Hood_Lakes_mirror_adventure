# -*- coding: utf-8 -*-
"""用户反馈批：立绘残留/BGM 切换与时机/体力回复×2/剑雨稀疏/弹幕放大减量/习得技能提示/红之惨剧效果/能量从 0 起。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 1) 换章清立绘 ----------
s = s.replace('func _start_story(id: String) -> void:\n\tseen_speakers.clear()',
              'func _start_story(id: String) -> void:\n\tseen_speakers.clear()\n'
              '\t# 换章时清空对话立绘（否则上一章角色会残留）\n'
              '\tstory_left = ""\n\tstory_right = ""\n\tlast_left = ""\n\tlast_right = ""\n\tportrait_fade = 0.0\n'
              '\t_stop_battle_bgm()\n'
              '\t# 预计算本章战斗命令位置（用于提前 2 句起战斗 BGM）\n'
              '\tbattle_cmd_index = -1\n\tbattle_cmd_boss = ""\n'
              '\tvar cmds: Array = story_data.get(id, {}).get("cmds", [])\n'
              '\tfor i in range(cmds.size()):\n'
              '\t\tif str(cmds[i].get("t", "")) == "battle":\n'
              '\t\t\tbattle_cmd_index = i\n\t\t\tbattle_cmd_boss = str(cmds[i].get("boss", "crimson"))\n\t\t\tbreak', 1)

if 'var battle_cmd_index' not in s:
    s = s.replace('var boss_bgm_pending := false', 'var boss_bgm_pending := false\nvar battle_cmd_index := -1\nvar battle_cmd_boss := ""\nvar battle_bgm_started := false\nvar tragedy_buff_t := 0.0', 1)

# ---------- 2) 提前 2 句起战斗 BGM ----------
s = s.replace('\tvar kind := str(command.get("t", ""))',
              '\tvar kind := str(command.get("t", ""))\n'
              '\t# 战斗 BGM 提前两句话进（用户要求）\n'
              '\tif battle_cmd_index >= 0 and not battle_bgm_started and story_index >= battle_cmd_index - 2:\n'
              '\t\tbattle_bgm_started = true\n'
              '\t\t_start_battle_bgm_for(battle_cmd_boss)', 1)

# 战斗开始时标记已起（避免重复）
s = s.replace('\tboss_bgm_pending = true', '\tboss_bgm_pending = true\n\tbattle_bgm_started = true', 1)

# ---------- 3) BGM 播放函数：支持指定 boss ----------
if 'func _start_battle_bgm_for' not in s:
    s = s.replace('## 战斗 BGM：延后到开场演出结束再响\nfunc _start_battle_bgm() -> void:\n\tvar path := "res://audio/crimson_bgm.ogg" if boss_id == "crimson" else "res://audio/marysue_bgm.ogg"',
                  '## 战斗 BGM：延后到开场演出结束再响\nfunc _start_battle_bgm() -> void:\n\t_start_battle_bgm_for(boss_id)\n\n'
                  'func _start_battle_bgm_for(who: String) -> void:\n'
                  '\tvar path := "res://audio/crimson_bgm.ogg" if who == "crimson" else "res://audio/marysue_bgm.ogg"', 1)

# ---------- 4) 胜利/换章停战斗 BGM ----------
s = s.replace('\t\t\tmode = Mode.VICTORY\n\t\t\tbanner = ""',
              '\t\t\tmode = Mode.VICTORY\n\t\t\t_stop_battle_bgm()\n\t\t\tbanner = ""', 1)
s = s.replace('func _stop_battle_bgm() -> void:\n\tif battle_bgm_player != null and battle_bgm_player.playing:\n\t\tbattle_bgm_player.stop()',
              'func _stop_battle_bgm() -> void:\n\tif battle_bgm_player != null and battle_bgm_player.playing:\n\t\tbattle_bgm_player.stop()\n\tbattle_bgm_started = false', 1)

# ---------- 5) 体力回复 ×2 ----------
s = s.replace('player_stamina = minf(100.0, player_stamina + 26.0 * FIXED_DT)', 'player_stamina = minf(100.0, player_stamina + 52.0 * FIXED_DT)', 1)

# ---------- 6) 能量：战斗从 0 起（原来满格看不出回复） ----------
s = s.replace('\tplayer_energy = 4', '\tplayer_energy = 0.0   # 从 0 起，方便看到擦弹/命中回复', 1)

# ---------- 7) 剑雨稀疏 ----------
s = s.replace('\t\t\tif frame % 8 == 0:\n\t\t\t\tvar rx := 150.0 + randf() * 2100.0\n\t\t\t\t_spawn_bullet(Vector2(rx, 40.0), Vector2(0, 300.0), RED, "flame", 4.0, 0.02)',
              '\t\t\tif frame % 16 == 0:\n\t\t\t\tvar rx := 150.0 + randf() * 2100.0\n\t\t\t\t_spawn_bullet(Vector2(rx, 40.0), Vector2(0, 260.0), RED, "flame", 4.0, 0.02)', 1)
s = s.replace('\t\t\tif frame % 7 == 0:\n\t\t\t\t_spawn_bullet(Vector2(120.0 + randf() * 2100.0, 40.0), Vector2(0, 260.0), HAZARD, "talisman", 4.0, 0.02)',
              '\t\t\tif frame % 16 == 0:\n\t\t\t\t_spawn_bullet(Vector2(120.0 + randf() * 2100.0, 40.0), Vector2(0, 240.0), HAZARD, "talisman", 4.0, 0.02)', 1)
# 数量减少
s = s.replace('\t\t\t\tfor k in range(10):\n\t\t\t\t\tvar a := TAU * float(k) / 10.0 + elapsed * 0.6',
              '\t\t\t\tfor k in range(7):\n\t\t\t\t\tvar a := TAU * float(k) / 7.0 + elapsed * 0.6', 1)

# ---------- 8) 弹幕放大 ----------
s = s.replace('\t\t\t"flame":\n\t\t\t\tbtex_key = "bullet_flame"\n\t\t\t\tbsize = 34.0', '\t\t\t"flame":\n\t\t\t\tbtex_key = "bullet_flame"\n\t\t\t\tbsize = 46.0', 1)
s = s.replace('\t\t\t"crescent":\n\t\t\t\tbtex_key = "bullet_crescent"\n\t\t\t\tbsize = 86.0', '\t\t\t"crescent":\n\t\t\t\tbtex_key = "bullet_crescent"\n\t\t\t\tbsize = 104.0', 1)
s = s.replace('\t\t\t"yinyang":\n\t\t\t\tbtex_key = "bullet_yinyang"\n\t\t\t\tbsize = 54.0', '\t\t\t"yinyang":\n\t\t\t\tbtex_key = "bullet_yinyang"\n\t\t\t\tbsize = 68.0', 1)
s = s.replace('\t\t\t"talisman":\n\t\t\t\tbtex_key = "bullet_talisman"\n\t\t\t\tbsize = 32.0', '\t\t\t"talisman":\n\t\t\t\tbtex_key = "bullet_talisman"\n\t\t\t\tbsize = 42.0', 1)
s = s.replace('\t\t\t"hazard", "homing", "homing_laser":\n\t\t\t\tbtex_key = "bullet_orb"\n\t\t\t\tbsize = 30.0 if kind == "hazard" else 34.0',
              '\t\t\t"hazard", "homing", "homing_laser":\n\t\t\t\tbtex_key = "bullet_orb"\n\t\t\t\tbsize = 40.0 if kind == "hazard" else 44.0', 1)

# ---------- 9) 习得技能提示 ----------
s = s.replace('\t\t\tskill_red_tragedy = true',
              '\t\t\tskill_red_tragedy = true\n\t\t\tbanner = "习得技能「红之惨剧」"\n\t\t\tbanner_timer = 150', 1)

# ---------- 10) 红之惨剧效果：回 2HP + 20 秒强化剑气 ----------
if 'func _use_red_skill' in s:
    i = s.index('func _use_red_skill')
    j = s.index('\nfunc ', i + 10)
    body = s[i:j]
    if 'tragedy_buff_t = 20.0' not in body:
        new_body = body.replace('player_energy -= 2', 'player_energy -= 2\n\tplayer_hp = mini(PLAYER_MAX_HP, player_hp + 2)\n\ttragedy_buff_t = 20.0', 1)
        s = s[:i] + new_body + s[j:]
        print('tragedy effect added')

# 强化剑气：玩家子弹伤害/尺寸在 buff 期间提升
s = s.replace('\t\t\tboss_hp = maxf(0.0, boss_hp - 3.0)',
              '\t\t\tboss_hp = maxf(0.0, boss_hp - (8.0 if tragedy_buff_t > 0.0 else 3.0))', 1)
if 'tragedy_buff_t = maxf' not in s:
    s = s.replace('\tif ball_hint_t > 0.0 and mode == Mode.WALK:',
                  '\tif tragedy_buff_t > 0.0:\n\t\ttragedy_buff_t = maxf(0.0, tragedy_buff_t - FIXED_DT)\n\tif ball_hint_t > 0.0 and mode == Mode.WALK:', 1)

# 玩家子弹视觉放大（强化期间）
s = s.replace('\tdraw_circle(p, 5, RED)', '\tdraw_circle(p, 11.0 if tragedy_buff_t > 0.0 else 5.0, RED)', 1)
s = s.replace('\t\tdraw_line(p - d * 22.0, p + d * 9.0, Color(RED, 0.3), 8.0)',
              '\t\tvar shot_w := 16.0 if tragedy_buff_t > 0.0 else 8.0\n\t\tdraw_line(p - d * 30.0, p + d * 12.0, Color(RED, 0.3), shot_w)', 1)

# ---------- 11) 技能说明文字 ----------
s = s.replace('\t\t# 技能名（格下方小字）',
              '\t\t# 技能说明（格下方小字）\n'
              '\t\tvar desc := {"skill_icon_red": "回2HP + 20秒强化剑气"}.get(slot["tex"], "")\n'
              '\t\tif desc != "":\n'
              '\t\t\tdraw_string(ThemeDB.fallback_font, rect.position + Vector2(0, rect.size.y + 26), desc, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.8, 0.8, 0.8))\n'
              '\t\t# 技能名（格下方小字）', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
