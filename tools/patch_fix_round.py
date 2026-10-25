# -*- coding: utf-8 -*-
"""一轮修：战斗战场限制/白色剑气改红且降频/BGM按章节起/玛丽苏招式重做成绿色激光雨/能量回复加大+改名MP。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 1) 能量回复加大 + MP 改名 ----------
s = s.replace('const ENERGY_PER_HIT := 0.035    # 子弹命中缓慢回复能量（用户要求：慢）',
              'const ENERGY_PER_HIT := 0.16     # 子弹命中回复能量（明显可见）', 1)
s = s.replace('const ENERGY_PER_GRAZE := 0.28   # 擦弹回复能量',
              'const ENERGY_PER_GRAZE := 0.45   # 擦弹回复能量', 1)
s = s.replace('"能量", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, WHITE)', '"MP", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, WHITE)', 1)

# ---------- 2) 战斗战场：限制活动范围，Boss 始终在屏幕内 ----------
if 'const BATTLE_LEFT' not in s:
    s = s.replace('const PHASE_NAMES := {',
                  'const BATTLE_LEFT := 1080.0\nconst BATTLE_RIGHT := 2320.0\nconst PHASE_NAMES := {', 1)

# 玩家横向限制（战斗内）
s = s.replace('\tplayer_pos.x = clampf(player_pos.x, ARENA_LEFT, ARENA_RIGHT)',
              '\tif mode == Mode.BATTLE:\n'
              '\t\tplayer_pos.x = clampf(player_pos.x, BATTLE_LEFT, BATTLE_RIGHT)\n'
              '\telse:\n'
              '\t\tplayer_pos.x = clampf(player_pos.x, ARENA_LEFT, ARENA_RIGHT)', 1)

# 战斗镜头：保证 Boss 与玩家都在画面内
s = s.replace('\tvar target := clampf(player_pos.x - VIEW.x * 0.38, 0.0, WORLD_W - VIEW.x)',
              '\tvar target := clampf(player_pos.x - VIEW.x * 0.38, 0.0, WORLD_W - VIEW.x)\n'
              '\tif mode == Mode.BATTLE:\n'
              '\t\tvar lo := minf(player_pos.x, boss_pos.x) - VIEW.x * 0.34\n'
              '\t\tvar hi := maxf(player_pos.x, boss_pos.x) - VIEW.x * 0.66\n'
              '\t\ttarget = clampf(player_pos.x - VIEW.x * 0.38, lo, maxf(lo, hi))', 1)

# ---------- 3) 白色剑气：改成红色刀刃且降频 ----------
s = s.replace('_crimson_crescent_volley(3)', '_crimson_crescent_volley(2)', 1)
s = s.replace('_crimson_crescent_volley(2)', '_crimson_crescent_volley(1)', 1)
s = s.replace('_crimson_crescent_volley(5)', '_crimson_crescent_volley(3)', 1)
s = s.replace('if boss_skill_state == "" and frame % 26 == 0:', 'if boss_skill_state == "" and frame % 52 == 0:', 1)
s = s.replace('if frame % 40 == 0:\n\t\t\t\t_crimson_crescent_volley', 'if frame % 80 == 0:\n\t\t\t\t_crimson_crescent_volley', 1)
s = s.replace('_spawn_bullet(boss_pos + d * 40.0, d * 520.0, RED, "crescent", 2.6, 0.0)',
              '_spawn_bullet(boss_pos + d * 40.0, d * 520.0, RED, "blade", 2.6, 0.0)', 1)

# ---------- 4) BGM：在对应对话章节开始时播 ----------
if 'CHAPTER_BATTLE_BGM' not in s:
    s = s.replace('const CHAPTER_BGM := {',
                  'const CHAPTER_BATTLE_BGM := {\n'
                  '\t"mirror_meet": "crimson_bgm",\n'
                  '\t"final": "marysue_bgm"\n'
                  '}\n'
                  'const CHAPTER_BGM := {', 1)
    s = s.replace('\tvar want_bgm := _chapter_bgm(id)',
                  '\tif CHAPTER_BATTLE_BGM.has(id):\n'
                  '\t\t_start_battle_bgm_for(str(CHAPTER_BATTLE_BGM[id]))\n'
                  '\t\tbattle_bgm_started = true\n'
                  '\tvar want_bgm := _chapter_bgm(id)', 1)
    print('chapter battle bgm added')

# ---------- 5) 玛丽苏招式：全部绿色激光雨 / 绿激光 / 绿符纸 ----------
start = s.index('func _patterns_marysue() -> void:')
end = s.index('\nfunc _spawn_two_whirls', start)
new_ms = '''func _patterns_marysue() -> void:
	# 用户要求：只用绿色激光类攻击（激光雨 / 横向扫射 / 追踪激光），不要魔姬的红色弹幕
	match boss_phase:
		0:  # 一：绿色激光雨（从天而降的激光柱，间歇）
			if frame % 45 == 0:
				for k in range(2):
					var lx := clampf(player_pos.x + randf_range(-260.0, 260.0), BATTLE_LEFT, BATTLE_RIGHT)
					_spawn_beam(lx, 0.9)
		1:  # 二：横向缓慢追踪激光
			if frame % 40 == 0:
				for k in range(3):
					var d := (player_pos - boss_pos).normalized()
					var off := (float(k) - 1.0) * 0.22
					_spawn_bullet(boss_pos, Vector2(cos(d.angle() + off), sin(d.angle() + off)) * 150.0, HAZARD, "laser", 4.5, 0.05)
		2:  # 三：激光雨 + 光球
			if frame % 26 == 0:
				var lx2 := clampf(player_pos.x + randf_range(-320.0, 320.0), BATTLE_LEFT, BATTLE_RIGHT)
				_spawn_beam(lx2, 0.8)
			if frame % 60 == 0:
				for k in range(5):
					var a := -PI * 0.5 + (float(k) - 2.0) * 0.26
					_spawn_bullet(boss_pos, Vector2(cos(a), sin(a)) * 210.0, HAZARD, "hazard", 4.0, 0.02)
		3:  # 四：地图随机激光（持续 2 秒）
			if frame % 55 == 0:
				for k in range(3):
					var rx := randf_range(BATTLE_LEFT + 80.0, BATTLE_RIGHT - 80.0)
					_spawn_beam(rx, 2.0)
		4:  # 五：地面冲刺带绿激光 + 绿闪
			green_flash_t = 1.2
			if boss_skill_state == "":
				boss_skill_state = "firing"
				boss_skill_timer = 46
				boss_pos.y = 420.0
				boss_pos.x = clampf(player_pos.x + randf_range(-220.0, 220.0), BATTLE_LEFT + 120.0, BATTLE_RIGHT - 120.0)
				_spawn_bullet(boss_pos, Vector2(-1, 0) * 760.0, HAZARD, "laser", 1.1, 0.0)
			elif boss_skill_state == "firing":
				boss_skill_timer -= 1
				if boss_skill_timer <= 0:
					boss_skill_state = ""
					boss_pos.y = 226.0
		5:  # 六：镜像翻转 + 密集绿色激光雨
			if not mirror_flip:
				mirror_flip = true
			if frame % 24 == 0:
				for k in range(2):
					var lx3 := clampf(player_pos.x + randf_range(-340.0, 340.0), BATTLE_LEFT, BATTLE_RIGHT)
					_spawn_beam(lx3, 1.0)
			if frame % 70 == 0:
				for k in range(6):
					var a6 := -PI * 0.5 + (float(k) - 2.5) * 0.2
					_spawn_bullet(boss_pos, Vector2(cos(a6), sin(a6)) * 240.0, HAZARD, "laser", 3.0, 0.03)

## 绿色激光柱（竖直向下，带预警后出现，持续 seconds 秒）
func _spawn_beam(x: float, seconds: float) -> void:
	_spawn_bullet(Vector2(x, GROUND_Y - 190.0), Vector2.ZERO, HAZARD, "beam", seconds, 0.0)
	_spawn_fx_ring(Vector2(x, GROUND_Y - 40.0), Color(0.51, 1, 0, 0.8), 120.0, 0.35, 3.0)
	for k in range(6):
		_spawn_particle(Vector2(x + randf_range(-18, 18), GROUND_Y - 30.0), Color(0.51, 1, 0, 0.9),
			0.5, Vector2(randf_range(-40, 40), randf_range(-150, -50)), 4.0)
'''
s = s[:start] + new_ms + s[end:]

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
