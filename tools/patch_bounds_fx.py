# -*- coding: utf-8 -*-
"""Boss 战边界可视化：边界外用红色火焰烧起来，靠近时边缘发红光提示。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 在战斗绘制里插入边界火焰（画在角色之前）
s = s.replace('\t_draw_boss_extras()\n\t_draw_fx_rings()\n\t_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)',
              '\t_draw_boss_extras()\n\t_draw_battle_bounds_fx()\n\t_draw_fx_rings()\n\t_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)', 1)

if 'func _draw_battle_bounds_fx' not in s:
    s += '''

## Boss 战边界：边界外烧起来的红色火焰墙 + 靠近提示
func _draw_battle_bounds_fx() -> void:
	var left_screen := BATTLE_LEFT - camera_x
	var right_screen := BATTLE_RIGHT - camera_x
	# 区域外压暗（越靠外越黑红）
	if left_screen > 0.0:
		draw_rect(Rect2(0, 0, left_screen, VIEW.y), Color(0.18, 0.0, 0.0, 0.55))
	if right_screen < VIEW.x:
		draw_rect(Rect2(right_screen, 0, VIEW.x - right_screen, VIEW.y), Color(0.18, 0.0, 0.0, 0.55))
	# 边界火焰：沿边界竖直一排跳动的火舌
	for side in [left_screen, right_screen]:
		if side < -60.0 or side > VIEW.x + 60.0:
			continue
		var base_x := clampf(side, -40.0, VIEW.x + 40.0)
		# 火墙底色
		draw_rect(Rect2(base_x - (18.0 if side == left_screen else -18.0), 0, 36, VIEW.y), Color(1, 0.12, 0.05, 0.18))
		var tongues := 16
		for i in range(tongues):
			var ty := float(i) * (VIEW.y / float(tongues))
			var ph := elapsed * 5.0 + float(i) * 0.9
			var h := 34.0 + 26.0 * sin(ph) + 12.0 * sin(ph * 2.7)
			var w := 22.0 + 8.0 * sin(ph * 1.7 + 1.0)
			var dir := 1.0 if side == left_screen else -1.0
			var tip := Vector2(base_x + dir * h, ty + 10.0)
			# 外焰（暗红）
			draw_colored_polygon(PackedVector2Array([
				Vector2(base_x, ty - w * 0.5), tip, Vector2(base_x, ty + w * 0.5)
			]), Color(1, 0.18, 0.05, 0.38))
			# 内焰（亮红）
			var tip2 := Vector2(base_x + dir * h * 0.6, ty + 6.0)
			draw_colored_polygon(PackedVector2Array([
				Vector2(base_x, ty - w * 0.25), tip2, Vector2(base_x, ty + w * 0.25)
			]), Color(1, 0.55, 0.2, 0.42))
			# 焰心（白热）
			var tip3 := Vector2(base_x + dir * h * 0.3, ty + 3.0)
			draw_colored_polygon(PackedVector2Array([
				Vector2(base_x, ty - w * 0.12), tip3, Vector2(base_x, ty + w * 0.12)
			]), Color(1, 0.9, 0.7, 0.45))
		# 边界线
		draw_line(Vector2(base_x, 0), Vector2(base_x, VIEW.y), Color(1, 0.25, 0.1, 0.8), 3.0)
	# 靠近边界：屏幕对应侧发红光
	var near := 150.0
	var px := player_pos.x - camera_x
	if px < (BATTLE_LEFT - camera_x) + near:
		var t := clampf(1.0 - (px - (BATTLE_LEFT - camera_x)) / near, 0.0, 1.0)
		draw_rect(Rect2(0, 0, 26, VIEW.y), Color(1, 0, 0, 0.35 * t))
	elif px > (BATTLE_RIGHT - camera_x) - near:
		var t2 := clampf(1.0 - ((BATTLE_RIGHT - camera_x) - px) / near, 0.0, 1.0)
		draw_rect(Rect2(VIEW.x - 26, 0, 26, VIEW.y), Color(1, 0, 0, 0.35 * t2))
'''
    print('battle bounds fx appended')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
