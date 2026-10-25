# -*- coding: utf-8 -*-
"""HUD 技能格打磨：加大、加按键徽章、冷却/能量不足显示、可用时描边发光。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
start = s.index('\t# ---- 技能图标（血条旁边，标注能量与按键）----')
end = s.index('\tdraw_string(ThemeDB.fallback_font, Vector2(640, 675), "冲刺', start) if s.find('\tdraw_string(ThemeDB.fallback_font, Vector2(640, 675), "冲刺', start) > 0 else -1
# 找不到锚点就替换到行尾的下一个 func
if end < 0:
    end = s.index('\nfunc ', start)

new = '''	# ---- 技能图标（血条旁边，标注能量与按键）----
	var slots := [
		{"tex": "skill_icon_red", "cost": 2, "key": "L", "name": "红之惨剧"},
		{"tex": "skill_icon_gun", "cost": 2, "key": "C", "name": "枪火击溃"},
		{"tex": "skill_icon_hell", "cost": 2, "key": "V", "name": "业火"}
	]
	var sx0 := 620.0
	for si in range(slots.size()):
		var slot: Dictionary = slots[si]
		var rect := Rect2(sx0 + float(si) * 68.0, 632, 60, 60)
		var can := player_energy >= float(slot["cost"])
		var pulse := 0.5 + 0.5 * sin(elapsed * 4.0 + float(si))
		# 外框：可用时白边+红晕，不可用时暗灰
		draw_rect(rect, Color(0.04, 0.04, 0.05, 0.9))
		if can:
			draw_rect(Rect2(rect.position - Vector2(2, 2), rect.size + Vector2(4, 4)), Color(1, 0, 0, 0.25 + 0.15 * pulse), false, 3.0)
		draw_rect(rect, Color(1, 1, 1, 0.55 if can else 0.16), false, 2.0)
		var itex: Texture2D = textures.get(slot["tex"])
		if itex:
			var pad := 6.0
			draw_texture_rect(itex, Rect2(rect.position + Vector2(pad, pad), rect.size - Vector2(pad * 2, pad * 2)), false,
				Color(1, 1, 1, 1.0 if can else 0.28))
		# 能量消耗徽章（左下）
		var cbadge := Rect2(rect.position + Vector2(2, rect.size.y - 18), Vector2(20, 16))
		draw_rect(cbadge, Color(0, 0, 0, 0.8))
		draw_string(ThemeDB.fallback_font, cbadge.position + Vector2(4, 13), str(slot["cost"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13,
			Color(1, 0.25, 0.25) if can else GREY)
		# 按键徽章（右上）
		var kbadge := Rect2(rect.position + Vector2(rect.size.x - 20, 2), Vector2(18, 16))
		draw_rect(kbadge, Color(0, 0, 0, 0.8))
		draw_string(ThemeDB.fallback_font, kbadge.position + Vector2(5, 13), str(slot["key"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13,
			WHITE if can else GREY)
		# 技能名（格下方小字）
		draw_string(ThemeDB.fallback_font, rect.position + Vector2(0, rect.size.y + 13), str(slot["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 12,
			Color(1, 0.4, 0.4) if can else GREY)
'''
s = s[:start] + new + s[end:]
io.open(p, 'w', encoding='utf-8').write(s)
print('skill slots polished')
