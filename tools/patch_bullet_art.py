# -*- coding: utf-8 -*-
"""弹幕改用生成的美术贴图（blade/orb/laser/rain），保留原有形状作为兜底。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 贴图注册
if 'bullet_blade' not in s:
    s = s.replace('\t\t"skill_icon_red": "res://art/ui/skill_red_tragedy.png",',
                  '\t\t"skill_icon_red": "res://art/ui/skill_red_tragedy.png",\n'
                  '\t\t"bullet_blade": "res://art/fx/bullets/bullet_blade.png",\n'
                  '\t\t"bullet_orb": "res://art/fx/bullets/bullet_orb.png",\n'
                  '\t\t"bullet_laser": "res://art/fx/bullets/bullet_laser.png",\n'
                  '\t\t"bullet_rain": "res://art/fx/bullets/bullet_rain.png",', 1)
    print('bullet textures registered')

# 2) 在子弹绘制循环最前面：有贴图就直接画贴图并 continue
anchor = '''	# Enemy bullets: redesigned primitive shapes
	for bullet in bullets:
		var p: Vector2 = bullet["pos"] - Vector2(camera_x, 0)
		var color: Color = bullet["color"]
		var kind := str(bullet.get("kind", "ring"))
		var angle: float = bullet["angle"]
'''
new = '''	# Enemy bullets: 优先使用生成美术（贴图），无图时退回程序绘制
	for bullet in bullets:
		var p: Vector2 = bullet["pos"] - Vector2(camera_x, 0)
		var color: Color = bullet["color"]
		var kind := str(bullet.get("kind", "ring"))
		var angle: float = bullet["angle"]
		var btex_key := ""
		var bsize := 0.0
		var rot := angle
		match kind:
			"blade", "lance", "laser", "laser_down":
				btex_key = "bullet_laser" if kind == "lance" else "bullet_blade"
				bsize = 56.0 if kind != "lance" else 78.0
			"hazard", "homing", "homing_laser":
				btex_key = "bullet_orb"
				bsize = 30.0 if kind == "hazard" else 34.0
			"rain":
				btex_key = "bullet_rain"
				bsize = 42.0
				rot = PI * 0.5
			"bigorb":
				btex_key = "bullet_orb"
				bsize = 84.0
		if btex_key != "" and textures.has(btex_key):
			var bt: Texture2D = textures.get(btex_key)
			draw_set_transform(p, rot, Vector2(1, 1))
			draw_texture_rect(bt, Rect2(Vector2(-bsize * 0.5, -bsize * 0.5), Vector2(bsize, bsize)), false, Color(1, 1, 1, 1))
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
			continue
'''
if anchor in s:
    s = s.replace(anchor, new, 1)
    print('bullet sprite drawing inserted')
else:
    print('bullet anchor miss')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
