# -*- coding: utf-8 -*-
"""用户 7 条反馈修复：
1 立绘不透明 2 冲刺音效换柔和 3 称号更常出现且更久 4 诺登立绘放大 30%
5 交互提示做成头顶徽章 6 鼠标左键推进对话 7 镜子可见性
"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---- 1) 立绘完全不透明 ----
s = s.replace('var tint := Color(1, 1, 1, (1.0 if active else 0.78) * alpha_mul)',
              'var tint := Color(1, 1, 1, alpha_mul)   # 立绘始终不透明（用户要求）', 1)

# ---- 3) 称号：更常出现 + 更久 ----
if 'seen_speakers' not in s:
    s = s.replace('var intro_hold := 0.0      # 竖幅在下一句仍停留的秒数',
                  'var intro_hold := 0.0      # 竖幅在下一句仍停留的秒数\n'
                  'var seen_speakers: Array = []  # 本章已登场过的角色（首次说话时弹称号）', 1)
    # 每章开始时清空
    s = s.replace('func _start_story(id: String) -> void:',
                  'func _start_story(id: String) -> void:\n\tseen_speakers.clear()', 1)
    # say 时首次出现 → 弹竖幅
    s = s.replace('\tif story_who != "":\n\t\t_set_portrait(story_who, story_expr)',
                  '\tif story_who != "":\n'
                  '\t\t_set_portrait(story_who, story_expr)\n'
                  '\t\tvar speaker_key := _portrait_base(story_who)\n'
                  '\t\tif not seen_speakers.has(speaker_key) and CHAR_TITLES.has(speaker_key):\n'
                  '\t\t\tseen_speakers.append(speaker_key)\n'
                  '\t\t\tstory_intro = speaker_key\n'
                  '\t\t\tintro_hold = 2.4', 1)

# 竖幅停留更久
s = s.replace('story_timer = 2.6', 'story_timer = 3.0', 1)
s = s.replace('intro_hold = 0.6', 'intro_hold = 2.4', 1)

# ---- 4) NPC 高度 +30% ----
s = s.replace('const NPC_NORDEN_HEIGHT := 85.0', 'const NPC_NORDEN_HEIGHT := 110.0', 1)
s = s.replace('const NPC_MABEL_HEIGHT := 95.0', 'const NPC_MABEL_HEIGHT := 124.0', 1)

# ---- 5) 交互提示：头顶徽章 ----
old_prompt = '\t\tdraw_string(ThemeDB.fallback_font, p + Vector2(-52, -330), str(walk_target.get("label", "按 W 交互")), HORIZONTAL_ALIGNMENT_LEFT, -1, 16, WHITE)'
new_prompt = '''		var tip: String = str(walk_target.get("label", "按 W 交互"))
		var tip_pos := p + Vector2(-58, -height - 28.0)
		var tip_w := 116.0
		draw_rect(Rect2(tip_pos, Vector2(tip_w, 26)), Color(0, 0, 0, 0.72))
		draw_rect(Rect2(tip_pos, Vector2(tip_w, 26)), Color(1, 1, 1, 0.75), false, 1.5)
		draw_string(ThemeDB.fallback_font, tip_pos + Vector2(10, 19), tip, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, WHITE)'''
if old_prompt in s:
    s = s.replace(old_prompt, new_prompt, 1)
    print('interaction badge added')

# ---- 6) 鼠标左键推进对话 ----
s = s.replace('"confirm": Input.is_key_pressed(KEY_ENTER) or Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_W),',
              '"confirm": Input.is_key_pressed(KEY_ENTER) or Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_W) or Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT),', 1)

# ---- 7) 镜子更醒目：抬高一点 + 加地面光 ----
s = s.replace('\tvar mtex: Texture2D = textures.get("mirror_stand")\n\tif mtex:\n\t\tcharacter_art.draw_ground(self, mtex, pos, 420.0)\n\t\treturn',
              '\tvar mtex: Texture2D = textures.get("mirror_stand")\n\tif mtex:\n'
              '\t\t# 镜面底部光晕，暗场景里更醒目\n'
              '\t\tdraw_circle(Vector2(pos.x, pos.y - 10), 90.0, Color(0, 0.73, 1, 0.10))\n'
              '\t\tcharacter_art.draw_ground(self, mtex, pos, 460.0)\n'
              '\t\treturn', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
