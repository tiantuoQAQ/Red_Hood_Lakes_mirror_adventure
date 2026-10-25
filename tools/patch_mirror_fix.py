# -*- coding: utf-8 -*-
"""1) 修六阶段左右颠倒：补回输入反转（之前被补丁弄丢了）
2) 玛丽苏第四阶段新招式：光轮切割（旋转阴阳轮盘）"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 输入反转 + 局面镜像开关
s = s.replace('''	var axis := float(int(input_state.get("right", false)) - int(input_state.get("left", false)))
	var vertical := float(int(input_state.get("down", false)) - int(input_state.get("up", false)))''','''	var axis := float(int(input_state.get("right", false)) - int(input_state.get("left", false)))
	# 六阶段「天地倒悬」：左右输入彻底反转
	if mirror_flip:
		axis = -axis
	var vertical := float(int(input_state.get("down", false)) - int(input_state.get("up", false)))''', 1)

# 2) 第四阶段：光轮切割（两道反向旋转的阴阳轮盘，卷成锯轮）
s = s.replace('''		3:  # 肆 · 断线：预警激光 + 镜面反弹符纸''','''		3:  # 肆 · 断线：预警激光 + 镜面反弹符纸 + 光轮切割
			if frame % 26 == 0:
				# 光轮切割：两臂反向旋转，逐圈扩散（像锯齿光轮）
				var arm := elapsed * 3.4
				for k in range(3):
					var ra := arm + float(k) * TAU / 3.0
					var rb := -arm + float(k) * TAU / 3.0 + PI
					var rad := 60.0 + float(frame % 130) * 1.6
					_spawn_bullet(boss_pos + Vector2(cos(ra), sin(ra)) * rad,
						Vector2(cos(ra + PI * 0.5), sin(ra + PI * 0.5)) * 210.0, HAZARD, "yinyang", 4.0, 0.0)
					_spawn_bullet(boss_pos + Vector2(cos(rb), sin(rb)) * rad,
						Vector2(cos(rb - PI * 0.5), sin(rb - PI * 0.5)) * 210.0, HAZARD, "talisman", 4.0, 0.0)
				_spawn_fx_ring(boss_pos, Color(0.51, 1, 0, 0.25), 180.0, 0.4, 2.0)''', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
