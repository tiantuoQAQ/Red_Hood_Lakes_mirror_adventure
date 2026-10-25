# -*- coding: utf-8 -*-
"""技能图标 + 能量条 + 能量获取（擦弹/命中）+ 技能特效强化。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 1) 图标加载 ----------
if 'skill_icon_red' not in s:
    s = s.replace('\t\t"logo_hongzhijing": "res://art/logo/hongzhijing_logo.png"',
                  '\t\t"logo_hongzhijing": "res://art/logo/hongzhijing_logo.png",\n'
                  '\t\t"skill_icon_red": "res://art/ui/skill_red_tragedy.png",\n'
                  '\t\t"skill_icon_gun": "res://art/ui/skill_gunfire.png",\n'
                  '\t\t"skill_icon_hell": "res://art/ui/skill_hellfire.png"', 1)
    print('icons registered')

# ---------- 2) 能量获取：擦弹 + 命中 ----------
if 'ENERGY_PER_GRAZE' not in s:
    s = s.replace('var player_energy := 4',
                  'var player_energy := 4\n'
                  'const ENERGY_MAX := 4.0\n'
                  'const ENERGY_PER_GRAZE := 0.28   # 擦弹回复能量\n'
                  'const ENERGY_PER_HIT := 0.06     # 子弹命中回复能量\n'
                  'var energy_flash := 0            # 能量满/消耗时的闪动', 1)
    print('energy consts added')

# 擦弹加能量（勇气增加处）
if 'ENERGY_PER_GRAZE)' not in s:
    s = s.replace('player_courage = minf(100.0, player_courage + multiplier)',
                  'player_courage = minf(100.0, player_courage + multiplier)\n'
                  '\t\tplayer_energy = minf(ENERGY_MAX, player_energy + ENERGY_PER_GRAZE)\n'
                  '\t\tenergy_flash = 8', 1)
    print('graze energy added')

# 命中加能量
if 'ENERGY_PER_HIT)' not in s:
    s = s.replace('\t\t\tboss_hit_flash = 8\n\t\t\tboss_ring_flash = 10',
                  '\t\t\tboss_hit_flash = 8\n'
                  '\t\t\tboss_ring_flash = 10\n'
                  '\t\t\tplayer_energy = minf(ENERGY_MAX, player_energy + ENERGY_PER_HIT)', 1)
    print('hit energy added')

# ---------- 3) HUD：能量条 + 技能图标 ----------
if 'skill slot' not in s:
    old = '\tdraw_string(ThemeDB.fallback_font, Vector2(460, 675), "能量 %d/4" % player_energy, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, RED)'
    new = '''	# ---- 能量条（血条旁边）----
	draw_string(ThemeDB.fallback_font, Vector2(400, 675), "能量", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, WHITE)
	draw_rect(Rect2(442, 665, 160, 10), Color(0.35, 0.35, 0.35, 1))
	var e_ratio := clampf(player_energy / ENERGY_MAX, 0.0, 1.0)
	var e_color := Color("#FF0000") if player_energy >= 2.0 else Color("#8a2a2a")
	draw_rect(Rect2(442, 665, 160 * e_ratio, 10), e_color)
	for seg in range(1, int(ENERGY_MAX)):
		var sx := 442.0 + 160.0 * float(seg) / ENERGY_MAX
		draw_line(Vector2(sx, 663), Vector2(sx, 677), Color(0, 0, 0, 0.75), 2.0)
	if energy_flash > 0:
		draw_rect(Rect2(442, 663, 160, 14), Color(1, 1, 1, 0.25 * float(energy_flash) / 8.0))
		energy_flash -= 1
	# ---- 技能图标（血条旁边，标注能量与按键）----
	var slots := [
		{"tex": "skill_icon_red", "cost": 2, "key": "L", "name": "红之惨剧"},
		{"tex": "skill_icon_gun", "cost": 2, "key": "C", "name": "枪火击溃"},
		{"tex": "skill_icon_hell", "cost": 2, "key": "V", "name": "业火"}
	]
	var sx0 := 620.0
	for si in range(slots.size()):
		var slot: Dictionary = slots[si]
		var rect := Rect2(sx0 + float(si) * 62.0, 640, 52, 52)
		var can := player_energy >= float(slot["cost"])
		draw_rect(rect, Color(0.05, 0.05, 0.06, 0.85))
		draw_rect(rect, Color(1, 1, 1, 0.55 if can else 0.18), false, 2.0)
		var itex: Texture2D = textures.get(slot["tex"])
		if itex:
			draw_texture_rect(itex, Rect2(rect.position + Vector2(4, 4), Vector2(44, 44)), false,
				Color(1, 1, 1, 1.0 if can else 0.32))
		# 能量消耗（左下角）
		draw_string(ThemeDB.fallback_font, rect.position + Vector2(4, 48), str(slot["cost"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(1, 0.25, 0.25) if can else GREY)
		# 按键（右上角）
		draw_string(ThemeDB.fallback_font, rect.position + Vector2(30, 14), str(slot["key"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, WHITE if can else GREY)'''
    if old in s:
        s = s.replace(old, new, 1)
        print('energy bar + skill slots added')
    else:
        print('hud anchor miss')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
