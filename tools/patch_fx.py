# -*- coding: utf-8 -*-
"""战斗特效强化：冲击环、命中火花、擦弹星芒、技能全屏表现。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 冲击环数组
if 'var fx_rings' not in s:
    s = s.replace('var energy_flash := 0            # 能量满/消耗时的闪动',
                  'var energy_flash := 0            # 能量满/消耗时的闪动\n'
                  'var fx_rings: Array = []         # 冲击环 {pos, r, max, life, color, width}', 1)
    print('fx vars added')

# 2) 生成/更新/绘制函数
if 'func _spawn_fx_ring' not in s:
    s += '''

# ======================= 战斗特效强化 =======================
func _spawn_fx_ring(pos: Vector2, color: Color, max_r: float, life: float = 0.35, width: float = 3.0) -> void:
	fx_rings.append({"pos": pos, "r": 8.0, "max": max_r, "life": life, "max_life": life, "color": color, "width": width})

func _update_fx_rings() -> void:
	for r in fx_rings:
		r["life"] = float(r["life"]) - FIXED_DT
		var k: float = 1.0 - clampf(float(r["life"]) / maxf(0.01, float(r["max_life"])), 0.0, 1.0)
		r["r"] = 8.0 + (float(r["max"]) - 8.0) * k
	fx_rings = fx_rings.filter(func(x): return float(x.get("life", 0.0)) > 0.0)

func _draw_fx_rings() -> void:
	for r in fx_rings:
		var k: float = clampf(float(r["life"]) / maxf(0.01, float(r["max_life"])), 0.0, 1.0)
		var col: Color = r["color"]
		col.a *= k
		draw_arc(Vector2(r["pos"]) - Vector2(camera_x, 0), float(r["r"]), 0.0, TAU, 48, col, float(r["width"]) * (0.4 + 0.6 * k))

func _fx_boss_hit(pos: Vector2) -> void:
	_spawn_fx_ring(pos, Color(1, 1, 1, 0.85), 46.0, 0.22, 2.5)
	_spawn_burst(pos, WHITE, 3)

func _fx_graze(pos: Vector2) -> void:
	_spawn_fx_ring(pos, Color(0, 0.73, 1, 0.7), 26.0, 0.18, 1.5)

func _fx_skill_cast(pos: Vector2, color: Color) -> void:
	_spawn_fx_ring(pos, color, 260.0, 0.45, 5.0)
	_spawn_fx_ring(pos, Color(1, 1, 1, 0.9), 150.0, 0.3, 3.0)
	for i in range(24):
		var a := TAU * float(i) / 24.0
		_spawn_bullet_particle_only(pos + Vector2(cos(a), sin(a)) * 20.0, Vector2(cos(a), sin(a)) * 260.0, color)
'''
    print('fx funcs appended')

# 3) 调用更新/绘制
s = s.replace('\t_update_boss_extras()', '\t_update_boss_extras()\n\t_update_fx_rings()', 1)
s = s.replace('\t_draw_boss_extras()', '\t_draw_boss_extras()\n\t_draw_fx_rings()', 1)

# 4) 命中 Boss 时加火花
s = s.replace('\t\t\tboss_hit_flash = 8\n\t\t\tboss_ring_flash = 10',
              '\t\t\tboss_hit_flash = 8\n\t\t\tboss_ring_flash = 10\n\t\t\t_fx_boss_hit(shot["pos"])', 1)

# 5) 擦弹星芒
s = s.replace('\t\t\tplayer_energy = minf(ENERGY_MAX, player_energy + ENERGY_PER_GRAZE)',
              '\t\t\tplayer_energy = minf(ENERGY_MAX, player_energy + ENERGY_PER_GRAZE)\n\t\t\t_fx_graze(Vector2(bullet["pos"]))', 1)

# 6) 技能释放：冲击环 + 闪屏
s = s.replace('\tbanner = "红 之 惨 剧"', '\t_fx_skill_cast(player_pos, RED)\n\tbanner = "红 之 惨 剧"', 1)
s = s.replace('\tbanner = "枪火击溃"', '\t_fx_skill_cast(blast, RED)\n\tbanner = "枪火击溃"', 1)
s = s.replace('\tbanner = "业火"', '\t_fx_skill_cast(boss_pos, RED)\n\tbanner = "业火"', 1)

# 7) 阶段切换：全屏闪 + Boss 冲击环
s = s.replace('\t\t\tbanner = "PHASE %d" % (boss_phase + 1)',
              '\t\t\t_spawn_fx_ring(boss_pos, Color(1, 1, 1, 0.9), 420.0, 0.5, 6.0)\n\t\t\t_spawn_mirror_shards(10, 0.8)\n\t\t\tbanner = "PHASE %d" % (boss_phase + 1)', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
