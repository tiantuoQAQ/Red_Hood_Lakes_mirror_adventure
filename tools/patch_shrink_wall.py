# -*- coding: utf-8 -*-
"""新增：地图外圈向内收拢的弹幕墙（缩圈），并适度降低既有密度。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 缩圈弹幕：从战场外左右/上方向内缓慢推进
if 'func _wall_shrink_pattern' not in s:
    s += '''

## 缩圈弹幕：从战场外框向内缓慢收拢（玩家必须往中间挤）
func _wall_shrink_pattern(spacing: float = 96.0, speed: float = 78.0) -> void:
	var left := _battle_left() - 90.0
	var right := _battle_right() + 90.0
	var y := 80.0
	while y < GROUND_Y - 20.0:
		# 左右两侧墙
		_spawn_bullet(Vector2(left, y), Vector2(speed, 0), HAZARD, "talisman", 8.0, 0.0)
		_spawn_bullet(Vector2(right, y), Vector2(-speed, 0), HAZARD, "talisman", 8.0, 0.0)
		y += spacing
	# 顶部下压
	var x := left
	while x < right:
		_spawn_bullet(Vector2(x, 40.0), Vector2(0, speed * 0.85), HAZARD, "yinyang", 8.0, 0.0)
		x += spacing * 1.35
	_spawn_fx_ring(Vector2((left + right) * 0.5, GROUND_Y - 120.0), Color(0.51, 1, 0, 0.5), 340.0, 0.6, 3.0)
'''
    print('wall shrink added')

# 阶段 2 与阶段 4 加入缩圈；并降低原有密度
s = s.replace('''		2:  # 叁 · 镜廊：符纸雨 + 阴阳球 + 箱庭囚笼''','''		2:  # 叁 · 镜廊：符纸雨 + 阴阳球 + 箱庭囚笼 + 缩圈
			if frame % 260 == 0:
				_wall_shrink_pattern()''', 1)
s = s.replace('''		3:  # 肆 · 断线：预警激光 + 镜面反弹符纸 + 光轮切割''','''		3:  # 肆 · 断线：预警激光 + 镜面反弹符纸 + 光轮切割 + 缩圈
			if frame % 300 == 0:
				_wall_shrink_pattern(110.0, 66.0)''', 1)

# 降密度：符纸环 10→7，阴阳球 8→6，符纸雨 34→46 帧
s = s.replace('for k in range(10):\n\t\t\t\t\tvar a := TAU * float(k) / 10.0 + elapsed * 0.5',
              'for k in range(7):\n\t\t\t\t\tvar a := TAU * float(k) / 7.0 + elapsed * 0.5', 1)
s = s.replace('for k in range(8):\n\t\t\t\t\tvar a2 := -TAU * float(k) / 8.0 + elapsed * 0.9',
              'for k in range(6):\n\t\t\t\t\tvar a2 := -TAU * float(k) / 6.0 + elapsed * 0.9', 1)
s = s.replace('\t\t\tif frame % 34 == 0:\n\t\t\t\t_spawn_bullet(Vector2(randf_range(_battle_left() + 60.0, _battle_right() - 60.0), 60.0),',
              '\t\t\tif frame % 48 == 0:\n\t\t\t\t_spawn_bullet(Vector2(randf_range(_battle_left() + 60.0, _battle_right() - 60.0), 60.0),', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
