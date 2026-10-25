# -*- coding: utf-8 -*-
"""玛丽苏新招式：螺旋光轮、箱庭囚笼、镜面反弹符纸、虚空裂隙。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# --- 阶段1：螺旋光轮（阴阳球螺旋外扩）
s = s.replace('''		0:  # 壹 · 箱庭：绿色符纸环（缓慢外扩）''','''		0:  # 壹 · 箱庭：绿色符纸环 + 螺旋光轮
			if frame % 90 == 0:
				for k in range(10):
					var sp_a := float(k) * 0.62 + elapsed * 2.2
					_spawn_bullet(boss_pos, Vector2(cos(sp_a), sin(sp_a)) * (120.0 + float(k) * 14.0), HAZARD, "yinyang", 5.5, 0.15)
			''' , 1)

# --- 阶段3：箱庭囚笼（玩家周围一圈符纸，只留缺口）
s = s.replace('''		2:  # 叁 · 镜廊：符纸雨（稀疏）+ 阴阳球''','''		2:  # 叁 · 镜廊：符纸雨 + 阴阳球 + 箱庭囚笼
			if frame % 160 == 0:
				var gap := randf_range(0.0, TAU)
				var ccx := clampf(player_pos.x, _battle_left() + 120.0, _battle_right() - 120.0)
				for k in range(16):
					var ca := TAU * float(k) / 16.0
					if absf(wrapf(ca - gap, -PI, PI)) < 0.55:
						continue   # 留一个缺口
					_spawn_bullet(Vector2(ccx + cos(ca) * 210.0, GROUND_Y - 150.0 + sin(ca) * 120.0),
						Vector2(-cos(ca), -sin(ca)) * 60.0, HAZARD, "talisman", 4.5, 0.0)
				_spawn_fx_ring(Vector2(ccx, GROUND_Y - 150.0), Color(0.51, 1, 0, 0.6), 240.0, 0.4, 3.0)
			''' , 1)

# --- 阶段4：镜面反弹符纸（碰到边界反弹）
s = s.replace('''		3:  # 肆 · 断线：预警激光''','''		3:  # 肆 · 断线：预警激光 + 镜面反弹符纸
			if frame % 110 == 0:
				for k in range(4):
					var ba := randf_range(0.0, TAU)
					_spawn_bullet(boss_pos, Vector2(cos(ba), sin(ba)) * 240.0, HAZARD, "bounce", 6.0, 0.0)
			''' , 1)

# --- 阶段6：虚空裂隙（多处激光预警）
s = s.replace('''			if frame % 220 == 0:
				var lx1 := clampf(player_pos.x + randf_range(-160.0, 160.0), _battle_left() + 90.0, _battle_right() - 90.0)
				_beam_warning(lx1)''','''			if frame % 220 == 0:
				var lx1 := clampf(player_pos.x + randf_range(-160.0, 160.0), _battle_left() + 90.0, _battle_right() - 90.0)
				_beam_warning(lx1)
			if frame % 130 == 0:
				# 虚空裂隙：连续三道错开的激光
				for k in range(3):
					var vx := clampf(player_pos.x + (float(k) - 1.0) * 260.0, _battle_left() + 90.0, _battle_right() - 90.0)
					_beam_warning(vx)''', 1)

# --- 反弹弹运动逻辑
s = s.replace('''		# 激光/光柱沿线粒子（绿色火花）''','''		# 镜面反弹符纸：碰到战场边缘反向
		if str(bullet.get("kind", "")) == "bounce":
			var bvl: Vector2 = bullet["vel"]
			var bx2: float = bullet["pos"].x
			if bx2 < _battle_left() + 20.0 or bx2 > _battle_right() - 20.0:
				bullet["vel"] = Vector2(-bvl.x, bvl.y)
				bullet["angle"] = Vector2(bullet["vel"]).angle()
		# 激光/光柱沿线粒子（绿色火花）''', 1)

# --- 反弹符纸绘制：用 talisman 外观
s = s.replace('			"talisman":', '			"talisman", "bounce":', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
