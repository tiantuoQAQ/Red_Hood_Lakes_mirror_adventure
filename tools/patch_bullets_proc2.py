# -*- coding: utf-8 -*-
"""把「敌方弹幕绘制」整块替换成程序化绘制（高亮辉光 + 白热核心 + 流光），彻底摆脱粗糙贴图。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()

start = s.index('\t# Enemy bullets')
end = s.index('\nfunc ', start)

block = '''	# Enemy bullets: 程序化绘制（多层辉光 + 白热核心 + 流光条纹），参考 GPT 预览效果
	for bullet in bullets:
		var p: Vector2 = bullet["pos"] - Vector2(camera_x, 0)
		var color: Color = bullet["color"]
		var kind := str(bullet.get("kind", "ring"))
		var angle: float = bullet["angle"]
		var bdir := Vector2(cos(angle), sin(angle))
		var perp := Vector2(-bdir.y, bdir.x)
		match kind:
			"blade", "crescent":
				var ln := 78.0 if kind == "blade" else 108.0
				var wd := 13.0 if kind == "blade" else 21.0
				var tip := p + bdir * ln * 0.55
				var back := p - bdir * ln * 0.45
				for g in range(3):
					var gk := 1.0 + float(g) * 0.6
					draw_colored_polygon(PackedVector2Array([
						tip + bdir * 9.0, p + perp * wd * gk * 0.5, back - bdir * 7.0, p - perp * wd * gk * 0.5
					]), Color(color, 0.09 + 0.05 * float(g)))
				draw_colored_polygon(PackedVector2Array([
					tip, p + perp * wd * 0.5, back, p - perp * wd * 0.5
				]), Color(color, 0.92))
				draw_line(back + bdir * 8.0, tip - bdir * 6.0, Color(1, 1, 1, 0.95), wd * 0.34)
				draw_line(back + bdir * 14.0, tip - bdir * 14.0, Color(1, 1, 1, 0.5), wd * 0.13)
				draw_line(back, back - bdir * ln * 1.0, Color(color, 0.26), wd * 0.5)
				continue
			"lance":
				var ll := 100.0
				for g in range(3):
					draw_line(p - bdir * ll * 0.5, p + bdir * ll * 0.5, Color(color, 0.09 + 0.05 * float(g)), 10.0 + float(g) * 7.0)
				draw_line(p - bdir * ll * 0.5, p + bdir * ll * 0.5, Color(color, 0.9), 9.0)
				draw_line(p - bdir * ll * 0.45, p + bdir * ll * 0.5, Color(1, 1, 1, 0.95), 3.4)
				draw_circle(p + bdir * ll * 0.5, 5.0, Color(1, 1, 1, 0.9))
				continue
			"laser", "laser_down", "beam":
				var lw := 28.0 if kind == "beam" else 16.0
				var llen := 150.0 if kind == "beam" else 230.0
				var la := p - bdir * llen * 0.5
				var lb := p + bdir * llen * 0.5
				for g in range(4):
					draw_line(la, lb, Color(color, 0.06 + 0.05 * float(g)), lw * (2.5 - float(g) * 0.42))
				draw_line(la, lb, Color(color, 0.88), lw)
				# 流光条纹（沿弹道流动）
				for k2 in range(3):
					var off := fmod(elapsed * 240.0 + float(k2) * 52.0, llen) - llen * 0.5
					var q := p + bdir * off
					draw_line(q - bdir * 15.0, q + bdir * 15.0, Color(1, 1, 1, 0.5), lw * 0.34)
				draw_line(la, lb, Color(1, 1, 1, 0.95), lw * 0.32)
				draw_circle(lb, lw * 0.6, Color(1, 1, 1, 0.7))
				draw_circle(lb, lw * 1.0, Color(color, 0.2))
				continue
			"hazard", "homing", "homing_laser", "flame", "bigorb":
				var rr := 16.0
				if kind == "homing" or kind == "homing_laser":
					rr = 19.0
				elif kind == "flame":
					rr = 18.0
				elif kind == "bigorb":
					rr = 42.0
				draw_circle(p, rr * 2.6, Color(color, 0.09))
				draw_circle(p, rr * 1.75, Color(color, 0.2))
				draw_circle(p, rr * 1.18, Color(color, 0.5))
				draw_circle(p, rr, Color(color, 0.95))
				draw_circle(p, rr * 0.44, Color(1, 1, 1, 0.95))
				draw_circle(p - Vector2(rr * 0.3, rr * 0.3), rr * 0.2, Color(1, 1, 1, 0.85))
				if kind == "flame":
					draw_line(p - bdir * rr, p - bdir * rr * 2.6, Color(color, 0.5), rr * 0.8)
					draw_line(p - bdir * rr * 1.4, p - bdir * rr * 3.2, Color(color, 0.24), rr * 0.4)
				continue
			"talisman":
				draw_set_transform(p, angle + PI * 0.5, Vector2(1, 1))
				draw_rect(Rect2(-21.0, -34.0, 42.0, 68.0), Color(color, 0.13))
				draw_rect(Rect2(-13.0, -21.0, 26.0, 42.0), Color(1, 1, 1, 0.95))
				draw_rect(Rect2(-13.0, -21.0, 26.0, 42.0), Color(color, 0.92), false, 2.6)
				for k3 in range(3):
					var lx := -6.0 + float(k3) * 6.0
					draw_line(Vector2(lx, -14.0), Vector2(lx, 14.0), Color(color, 0.85), 1.8)
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
				continue
			"yinyang":
				draw_circle(p, 36.0, Color(color, 0.11))
				draw_circle(p, 26.0, Color(color, 0.92))
				draw_circle(p, 17.5, Color(1, 1, 1, 0.95))
				draw_circle(p + Vector2(0, -8.8), 8.8, Color(color, 0.95))
				draw_circle(p - Vector2(0, 8.8), 8.8, Color(1, 1, 1, 0.98))
				draw_circle(p + Vector2(0, -8.8), 2.8, Color(1, 1, 1, 0.96))
				draw_circle(p - Vector2(0, 8.8), 2.8, Color(color, 0.95))
				continue
			"rain":
				draw_line(p - bdir * 18.0, p + bdir * 24.0, Color(color, 0.9), 7.0)
				draw_line(p - bdir * 20.0, p + bdir * 24.0, Color(1, 1, 1, 0.95), 2.6)
				draw_line(p - bdir * 30.0, p - bdir * 66.0, Color(color, 0.22), 4.0)
				continue
		# 兜底：环形弹
		draw_circle(p, 9.0, Color(color, 0.85))
		draw_circle(p, 4.0, Color(1, 1, 1, 0.9))
'''
s = s[:start] + block + s[end:]
io.open(p, 'w', encoding='utf-8').write(s)
print('replaced bullet draw block')
