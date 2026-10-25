# -*- coding: utf-8 -*-
"""玛丽苏弹幕改绿色：HAZARD 颜色的弹幕使用 *_green 贴图。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 注册绿色贴图
if 'bullet_talisman_green' not in s:
    s = s.replace('\t\t"bullet_beam": "res://art/fx/bullets/beam_pillar.png",',
                  '\t\t"bullet_beam": "res://art/fx/bullets/beam_pillar.png",\n'
                  '\t\t"bullet_talisman_green": "res://art/fx/bullets/talisman_green.png",\n'
                  '\t\t"bullet_yinyang_green": "res://art/fx/bullets/yinyang_orb_green.png",\n'
                  '\t\t"bullet_beam_green": "res://art/fx/bullets/beam_pillar_green.png",\n'
                  '\t\t"bullet_crescent_green": "res://art/fx/bullets/crescent_green.png",', 1)
    print('green textures registered')

# 绘制时按颜色选绿色版本
s = s.replace('\t\tif btex_key != "" and textures.has(btex_key):',
              '\t\t# 玛丽苏（HAZARD 绿）用绿色贴图\n'
              '\t\tif color == HAZARD and textures.has(btex_key + "_green"):\n'
              '\t\t\tbtex_key = btex_key + "_green"\n'
              '\t\tif btex_key != "" and textures.has(btex_key):', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
