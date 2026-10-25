# -*- coding: utf-8 -*-
"""接入新版小红帽完整立绘（自带头部）：移除分离头贴图，冲刺用新图。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 用完整立绘替换旧的分体素材（去掉 rek_head，draw_player 便不再叠加头部）
s = s.replace('\t\t"rek_head": "res://art/battle/rek/head.png",\n', '', 1)
s = s.replace('"rek_dash_01": "res://art/battle/rek/dash_01.png",', '"rek_dash_01": "res://art/battle/rek/dash_full.png",', 1)
s = s.replace('"rek_dash_02": "res://art/battle/rek/dash_02.png",', '"rek_dash_02": "res://art/battle/rek/dash_full.png",', 1)
s = s.replace('"rek_dash_03": "res://art/battle/rek/dash_03.png",', '"rek_dash_03": "res://art/battle/rek/dash_full.png",', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
