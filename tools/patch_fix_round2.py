# -*- coding: utf-8 -*-
"""修一批：
1) MP 真正修复（player_energy 被推断成 int，导致小数增长被截断成 0）
2) 地图加长（4800 → 6400）
3) 教程改为「镜子旁的告示牌」+ 保留全屏教程并真正调用
4) 战斗 BGM 改为临战前 4 句
5) 称号竖幅：停留时间加长到 3 秒
"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 1) MP 修复 ----------
s = s.replace('var player_energy := 4', 'var player_energy: float = 4.0', 1)
# 去掉调试 print
s = s.replace('\t\t\tprint("HIT energy=", player_energy, " max=", ENERGY_MAX, " per=", ENERGY_PER_HIT)\n', '', 1)

# ---------- 2) 地图加长 ----------
s = s.replace('const WORLD_W := 4800.0', 'const WORLD_W := 6400.0', 1)

# ---------- 3) 教程：真正调用 + 告示牌 ----------
s = s.replace('\t_draw_tutorial()\n\t_draw_particles_world()', '\t_draw_particles_world()', 1)  # 清理可能的坏插入
s = s.replace('\t_draw_particles_world()\n\tdraw_string(ThemeDB.fallback_font, Vector2(40, 48)',
              '\t_draw_tutorial()\n\t_draw_signboard()\n\t_draw_particles_world()\n\tdraw_string(ThemeDB.fallback_font, Vector2(40, 48)', 1)

# 教程触发：任何走位章节都可（去掉章节名单限制）
s = s.replace('\tif not tutorial_shown and story_chapter in ["wake_talk", "enter_mirror", "mirror"] and mode == Mode.WALK:',
              '\tif not tutorial_shown and mode == Mode.WALK:', 1)

if 'func _draw_signboard' not in s:
    s += '''

## 镜子旁的告示牌：木质牌面 + 操作说明（不需要弹窗也能看到）
func _draw_signboard() -> void:
	# 只在有交互目标的走位段显示
	if walk_target.size() == 0:
		return
	var tx := float(walk_target.get("x", 0.0))
	if tx <= 0.0:
		return
	var sx := tx - camera_x - 150.0
	var base_y := GROUND_Y
	# 木桩
	draw_rect(Rect2(sx + 52, base_y - 96, 10, 96), Color(0.24, 0.2, 0.18))
	# 牌面
	var board := Rect2(sx, base_y - 190, 128, 106)
	draw_rect(board, Color(0.13, 0.11, 0.10, 0.96))
	draw_rect(board, Color(1, 1, 1, 0.55), false, 2.0)
	draw_line(board.position + Vector2(6, 8), board.position + Vector2(board.size.x - 6, 8), Color(1, 0.3, 0.3, 0.8), 2.0)
	var tips := ["A / D  移动", "SPACE 跳跃", "SHIFT 冲刺", "空中W+冲刺 = 光球", "J / Z  射击", "C / V  技能"]
	var ty := board.position.y + 26.0
	for t in tips:
		draw_string(ThemeDB.fallback_font, Vector2(board.position.x + 8, ty), t, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.92, 0.92, 0.92))
		ty += 15.0
'''
    print('signboard appended')

# ---------- 4) BGM 临战前 4 句 ----------
s = s.replace('\tif CHAPTER_BATTLE_BGM.has(id):\n\t\t_start_battle_bgm_for(str(CHAPTER_BATTLE_BGM[id]))\n\t\tbattle_bgm_started = true\n', '', 1)
s = s.replace('story_index >= battle_cmd_index - 2', 'story_index >= battle_cmd_index - 4', 1)

# ---------- 5) 称号停留更久 ----------
s = s.replace('intro_hold = 2.4', 'intro_hold = 3.2')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
