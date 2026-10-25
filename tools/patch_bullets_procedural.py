# -*- coding: utf-8 -*-
"""弹幕改为程序化绘制（参考 GPT 预览的高亮+辉光+流光感），替代粗糙贴图。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()

start = s.index('\t\tvar btex_key := ""')
end = s.index('\t\tmatch kind:', start)
# 找到贴图分支结束位置：第一个 "\n\t\tmatch kind:\n" 之后的弹幕形状绘制其实在同一函数；用贴图块结尾锚点
anchor_tail = '\t\tif btex_key != "" and textures.has(btex_key):'
tail_end = s.index('\n', s.index('\t\t\tcontinue', s.index(anchor_tail))) + 1

new_block = '''		# 程序化绘制：多层辉光 + 白色高热核心 + 流光，接近参考图效果
		var dir := Vector2(cos(angle), sin(angle))
		var perp := Vector2(-dir.y, dir.x)
		match kind:
			"blade", "crescent":
				var ln := 74.0 if kind == "blade" else 104.0
				var wd := 13.0 if kind == "blade" else 20.0
				var tip := p + dir * ln * 0.55
				var back := p - dir * ln * 0.45
				# 外辉光
				for g in range(3):
					var gk := 1.0 + float(g) * 0.55
					draw_colored_polygon(PackedVector2Array([
						tip + dir * 8.0, p + perp * wd * gk * 0.5, back - dir * 6.0, p - perp * wd * gk * 0.5
					]), Color(color, 0.10 + 0.05 * float(g)))
				# 主体
				draw_colored_polygon(PackedVector2Array([
					tip, p + perp * wd * 0.5, back, p - perp * wd * 0.5
				]), Color(color, 0.92))
				# 白热核心
				draw_line(back + dir * 6.0, tip - dir * 5.0, Color(1, 1, 1, 0.95), wd * 0.34)
				draw_line(back + dir * 10.0, tip - dir * 12.0, Color(1, 1, 1, 0.55), wd * 0.14)
				# 拖尾
				draw_line(back, back - dir * ln * 0.9, Color(color, 0.28), wd * 0.5)
				continue
			"lance":
				var ll := 96.0
				for g in range(3):
					draw_line(p - dir * ll * 0.5, p + dir * ll * 0.5, Color(color, 0.10 + 0.05 * float(g)), 10.0 + float(g) * 6.0)
				draw_line(p - dir * ll * 0.5, p + dir * ll * 0.5, Color(color, 0.9), 9.0)
				draw_line(p - dir * ll * 0.45, p + dir * ll * 0.5, Color(1, 1, 1, 0.95), 3.4)
				draw_circle(p + dir * ll * 0.5, 5.0, Color(1, 1, 1, 0.9))
				continue
			"laser", "laser_down", "beam":
				var lw := 26.0 if kind == "beam" else 15.0
				var llen := 130.0 if kind == "beam" else 220.0
				var a := p - dir * llen * 0.5
				var b := p + dir * llen * 0.5
				# 外层辉光（多段，模拟 shadowBlur）
				for g in range(4):
					draw_line(a, b, Color(color, 0.07 + 0.05 * float(g)), lw * (2.4 - float(g) * 0.4))
				# 柱体
				draw_line(a, b, Color(color, 0.88), lw)
				# 流动条纹
				for k2 in range(3):
					var off := fmod(elapsed * 220.0 + float(k2) * 46.0, llen) - llen * 0.5
					var q := p + dir * off
					draw_line(q - dir * 14.0, q + dir * 14.0, Color(1, 1, 1, 0.5), lw * 0.35)
				# 白热核心
				draw_line(a, b, Color(1, 1, 1, 0.95), lw * 0.34)
				# 端点光斑
				draw_circle(b, lw * 0.55, Color(1, 1, 1, 0.75))
				draw_circle(b, lw * 0.9, Color(color, 0.22))
				continue
			"hazard", "homing", "homing_laser", "flame", "bigorb":
				var rr := 15.0 if kind == "hazard" else 19.0
				if kind == "flame":
					rr = 17.0
				if kind == "bigorb":
					rr = 40.0
				# 外辉光三层
				draw_circle(p, rr * 2.5, Color(color, 0.10))
				draw_circle(p, rr * 1.7, Color(color, 0.22))
				draw_circle(p, rr * 1.15, Color(color, 0.55))
				# 主体
				draw_circle(p, rr, Color(color, 0.95))
				# 白色核心 + 高光
				draw_circle(p, rr * 0.45, Color(1, 1, 1, 0.95))
				draw_circle(p - Vector2(rr * 0.3, rr * 0.3), rr * 0.22, Color(1, 1, 1, 0.8))
				# 火焰尾巴（flame）
				if kind == "flame":
					draw_line(p - dir * rr, p - dir * rr * 2.6, Color(color, 0.5), rr * 0.8)
					draw_line(p - dir * rr * 1.4, p - dir * rr * 3.1, Color(color, 0.25), rr * 0.4)
				continue
			"talisman":
				var tw := 13.0
				var th := 22.0
				draw_set_transform(p, angle + PI * 0.5, Vector2(1, 1))
				draw_rect(Rect2(-tw * 1.6, -th * 1.6, tw * 3.2, th * 3.2), Color(color, 0.14))
				draw_rect(Rect2(-tw, -th, tw * 2.0, th * 2.0), Color(1, 1, 1, 0.94))
				draw_rect(Rect2(-tw, -th, tw * 2.0, th * 2.0), Color(color, 0.9), false, 2.5)
				for k3 in range(3):
					draw_line(Vector2(-tw * 0.4 + float(k3) * 4.0, -th * 0.6), Vector2(-tw * 0.4 + float(k3) * 4.0, th * 0.6), Color(color, 0.85), 1.6)
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
				continue
			"yinyang":
				draw_circle(p, 34.0, Color(color, 0.12))
				draw_circle(p, 25.0, Color(color, 0.9))
				draw_circle(p, 17.0, Color(1, 1, 1, 0.95))
				draw_circle(p + Vector2(0, -8.5), 8.5, Color(color, 0.95))
				draw_circle(p - Vector2(0, 8.5), 8.5, Color(1, 1, 1, 0.98))
				draw_circle(p + Vector2(0, -8.5), 2.6, Color(1, 1, 1, 0.95))
				draw_circle(p - Vector2(0, 8.5), 2.6, Color(color, 0.95))
				continue
			"rain":
				var rdir := Vector2(cos(angle), sin(angle))
				draw_line(p - rdir * 16.0, p + rdir * 22.0, Color(color, 0.9), 7.0)
				draw_line(p - rdir * 18.0, p + rdir * 22.0, Color(1, 1, 1, 0.95), 2.6)
				draw_line(p - rdir * 26.0, p - rdir * 60.0, Color(color, 0.25), 4.0)
				continue
'''
s = s[:start] + new_block + s[tail_end:]
io.open(p, 'w', encoding='utf-8').write(s)
print('procedural bullets written')
