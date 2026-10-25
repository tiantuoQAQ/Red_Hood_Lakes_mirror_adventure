# -*- coding: utf-8 -*-
"""回退小红帽贴图为原版（分体头 + 身体），并让绘制支持任意尺寸贴图（自动按可见内容做底边锚定，避免悬空/陷地）。"""
import io

# 1) main.gd 资源表恢复原版
p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s
s = s.replace('\t\t"rek_body_move": "res://art/battle/rek/body_move.png",',
              '\t\t"rek_body_move": "res://art/battle/rek/body_move.png",\n'
              '\t\t"rek_head": "res://art/battle/rek/head.png",', 1)
s = s.replace('"rek_dash_01": "res://art/battle/rek/dash_full.png",', '"rek_dash_01": "res://art/battle/rek/dash_01.png",', 1)
s = s.replace('"rek_dash_02": "res://art/battle/rek/dash_full.png",', '"rek_dash_02": "res://art/battle/rek/dash_02.png",', 1)
s = s.replace('"rek_dash_03": "res://art/battle/rek/dash_full.png",', '"rek_dash_03": "res://art/battle/rek/dash_03.png",', 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('main.gd restored' if s != orig else 'NO CHANGE')

# 2) character_art.gd：自适应锚点 + 头部跟随（原版行为保留）
p2 = 'godot/character_art.gd'
c = io.open(p2, encoding='utf-8').read()
old = '''func draw_player(canvas: CanvasItem, art: Dictionary, foot: Vector2, facing: float, state: String, aim: Vector2, tint: Color, squash: Vector2 = Vector2.ONE) -> bool:
	var texture: Texture2D = art.get("rek_" + state)
	if not texture:
		return false
	# Compute scale from target display height / natural texture visible height
	var bounds := visible_bounds(texture)
	if bounds.size.y <= 0:
		return false
	var scale := PLAYER_HEIGHT / bounds.size.y
	canvas.draw_set_transform(foot, 0, Vector2(facing, 1) * squash)
	canvas.draw_texture_rect(texture, Rect2(-PLAYER_FOOT * scale, texture.get_size() * scale), false, tint)'''
new = '''func draw_player(canvas: CanvasItem, art: Dictionary, foot: Vector2, facing: float, state: String, aim: Vector2, tint: Color, squash: Vector2 = Vector2.ONE) -> bool:
	var texture: Texture2D = art.get("rek_" + state)
	if not texture:
		return false
	# Compute scale from target display height / natural texture visible height
	var bounds := visible_bounds(texture)
	if bounds.size.y <= 0:
		return false
	var scale := PLAYER_HEIGHT / bounds.size.y
	# 自适应锚点：极老的素材用标定锚点，其它尺寸按「可见内容底边中心」对齐地面，避免悬空或陷地
	var canvas_size := texture.get_size()
	var anchor := PLAYER_FOOT
	if absf(canvas_size.y - 768.0) > 1.0 or absf(canvas_size.x - 896.0) > 1.0:
		anchor = Vector2(bounds.position.x + bounds.size.x * 0.5, bounds.position.y + bounds.size.y)
	canvas.draw_set_transform(foot, 0, Vector2(facing, 1) * squash)
	canvas.draw_texture_rect(texture, Rect2(-anchor * scale, texture.get_size() * scale), false, tint)'''
if old in c:
    c = c.replace(old, new, 1)
    # 头部锚点：非标定素材时按 bbox 顶部估算颈部位置
    c = c.replace('''		var head: Texture2D = art.get("rek_head")
		if head:
			var neck := (PLAYER_NECK - PLAYER_FOOT) * scale''','''		var head: Texture2D = art.get("rek_head")
		if head:
			var neck_src := PLAYER_NECK
			if absf(canvas_size.y - 768.0) > 1.0 or absf(canvas_size.x - 896.0) > 1.0:
				neck_src = Vector2(bounds.position.x + bounds.size.x * 0.5, bounds.position.y + bounds.size.y * 0.18)
			var neck := (neck_src - anchor) * scale''', 1)
    c = c.replace('''			canvas.draw_texture_rect(head, Rect2(-PLAYER_NECK * scale, head.get_size() * scale), false, tint)''','''			canvas.draw_texture_rect(head, Rect2(-neck_src * scale, head.get_size() * scale), false, tint)''', 1)
    io.open(p2, 'w', encoding='utf-8').write(c)
    print('character_art.gd: adaptive anchor + head follow')
else:
    print('draw_player anchor block not found')
