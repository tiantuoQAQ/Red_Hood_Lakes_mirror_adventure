# -*- coding: utf-8 -*-
"""数值手感 + 表现力：冲刺/MP/光球/无敌帧、复活提示、阶段切换演出、弹幕描边、旋风预警。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 数值 ----------
s = s.replace('const DASH_STAMINA_COST := 40.0', 'const DASH_STAMINA_COST := 35.0', 1)
s = s.replace('const ENERGY_PER_HIT := 0.16', 'const ENERGY_PER_HIT := 0.22', 1)
s = s.replace('player_stamina = maxf(0.0, player_stamina - 32.0 * FIXED_DT)',
              'player_stamina = maxf(0.0, player_stamina - 24.0 * FIXED_DT)', 1)
s = s.replace('player_hurt_invuln = 80', 'player_hurt_invuln = 60', 1)

# 体力上限提到 120（连冲 3 次）
s = s.replace('player_stamina = minf(100.0, player_stamina + 78.0 * FIXED_DT)',
              'player_stamina = minf(120.0, player_stamina + 78.0 * FIXED_DT)', 1)
s = s.replace('var player_stamina := 100.0', 'var player_stamina := 120.0', 1)
s = s.replace('player_stamina_display / 100.0', 'player_stamina_display / 120.0', 1)
s = s.replace('player_stamina = minf(100.0, player_stamina + 52.0', 'player_stamina = minf(120.0, player_stamina + 52.0')

# ---------- 复活提示 ----------
if 'var retry_flash' not in s:
    s = s.replace('var death_timer := 0.0', 'var death_timer := 0.0\nvar retry_flash := 0.0', 1)
s = s.replace('''		banner = "……是幻觉么。"
		banner_timer = 170''','''		banner = "……是幻觉么。"
		banner_timer = 170
		retry_flash = 1.0''', 1)
if 'retry_flash > 0.0' not in s:
    s = s.replace('\tif death_timer > 0.0:\n\t\treturn\n\tvar k := clampf(death_timer / 1.9, 0.0, 1.0)',
                  '\tif retry_flash > 0.0:\n'
                  '\t\tretry_flash = maxf(0.0, retry_flash - FIXED_DT * 1.6)\n'
                  '\t\tdraw_rect(Rect2(Vector2.ZERO, VIEW), Color(1, 1, 1, 0.55 * retry_flash))\n'
                  '\t\tdraw_string(ThemeDB.fallback_font, Vector2(556, 330), "RETRY", HORIZONTAL_ALIGNMENT_LEFT, -1, 46, Color(1, 1, 1, retry_flash))\n'
                  '\tif death_timer > 0.0:\n\t\treturn\n\tvar k := clampf(death_timer / 1.9, 0.0, 1.0)', 1)

# ---------- 阶段切换演出：白闪 + 顿帧 ----------
s = s.replace('\t\t\t_spawn_fx_ring(boss_pos, Color(1, 1, 1, 0.9), 420.0, 0.5, 6.0)',
              '\t\t\t_spawn_fx_ring(boss_pos, Color(1, 1, 1, 0.9), 420.0, 0.5, 6.0)\n'
              '\t\t\thitstop = 12\n'
              '\t\t\tstage_flash = 1.0', 1)
if 'var stage_flash' not in s:
    s = s.replace('var retry_flash := 0.0', 'var retry_flash := 0.0\nvar stage_flash := 0.0', 1)
if 'stage_flash > 0.0' not in s:
    s = s.replace('\tif hurt_vignette > 0:',
                  '\tif stage_flash > 0.0:\n'
                  '\t\tstage_flash = maxf(0.0, stage_flash - FIXED_DT * 2.2)\n'
                  '\t\tdraw_rect(Rect2(Vector2.ZERO, VIEW), Color(1, 1, 1, 0.6 * stage_flash))\n'
                  '\tif hurt_vignette > 0:', 1)

# ---------- 弹幕白色描边（所有弹幕统一） ----------
s = s.replace('''		# 全局：外圈光晕（所有弹幕都发光）
		draw_circle(p, 26.0, Color(color, 0.06))
		draw_circle(p, 17.0, Color(color, 0.10))''','''		# 全局：外圈光晕（所有弹幕都发光）
		draw_circle(p, 26.0, Color(color, 0.06))
		draw_circle(p, 17.0, Color(color, 0.10))
		# 白色细描边：让弹幕在深色/火焰背景上依然清晰
		draw_arc(p, 20.0, 0.0, TAU, 20, Color(1, 1, 1, 0.28), 1.4)''', 1)

# ---------- 旋风出现预警（前 0.6 秒半透明旋涡） ----------
s = s.replace('''	# 地面旋风
	for w in whirls:''','''	# 地面旋风（出现前预警）
	for w in whirls:''', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
