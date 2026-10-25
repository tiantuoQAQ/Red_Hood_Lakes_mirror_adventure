# -*- coding: utf-8 -*-
"""数值/UI 一批：
- 冲刺体力 40；血量 5；能量命中小幅恢复
- 红之惨剧击败魔姬前不显示也不可用
- 血量图标由心形改为「镜子」，掉血后镜子破碎
- 魔姬战斗 BGM 延后到开场演出结束
- 猩红旋风放大且会移动（一个追玩家、一个来回扫）
"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 数值 ----------
s = s.replace('const DASH_STAMINA_COST := 3.0', 'const DASH_STAMINA_COST := 40.0   # 用户要求：一次冲刺消耗 40 体力', 1)
s = s.replace('var player_hp := 3', 'var player_hp := 5\nconst PLAYER_MAX_HP := 5', 1)
s = s.replace('\tplayer_hp = 3', '\tplayer_hp = PLAYER_MAX_HP', 1)
s = s.replace('const ENERGY_PER_HIT := 0.06     # 子弹命中回复能量',
              'const ENERGY_PER_HIT := 0.035    # 子弹命中缓慢回复能量（用户要求：慢）', 1)

# 中途掉血判定用 0 判断不变；受击扣 1 保持不变

# ---------- 红之惨剧：未解锁不显示 ----------
s = s.replace('\tvar slots := [\n\t\t{"tex": "skill_icon_red", "cost": 2, "key": "L", "name": "红之惨剧"},\n\t\t{"tex": "skill_icon_gun", "cost": 2, "key": "C", "name": "枪火击溃"},\n\t\t{"tex": "skill_icon_hell", "cost": 2, "key": "V", "name": "业火"}\n\t]',
              '\tvar slots: Array = []\n'
              '\tif skill_red_tragedy:\n'
              '\t\tslots.append({"tex": "skill_icon_red", "cost": 2, "key": "L", "name": "红之惨剧"})\n'
              '\tslots.append({"tex": "skill_icon_gun", "cost": 2, "key": "C", "name": "枪火击溃"})\n'
              '\tslots.append({"tex": "skill_icon_hell", "cost": 2, "key": "V", "name": "业火"})', 1)

# ---------- 血量图标：镜子（5 面），掉血后破碎 ----------
old_hearts = '''	for i in range(3):
		var heart := Vector2(78 + i * 26, 644)
		draw_colored_polygon(PackedVector2Array([heart + Vector2(0, 10), heart + Vector2(-9, -2), heart + Vector2(-6, -10), heart + Vector2(0, -5), heart + Vector2(6, -10), heart + Vector2(9, -2)]), RED if i < player_hp else Color(GREY, 0.25))'''
new_hearts = '''	# 血量图标：小镜子（完整的亮、破损的暗且带裂纹）
	for i in range(PLAYER_MAX_HP):
		var mir := Vector2(78 + i * 24, 644)
		var alive: bool = i < player_hp
		var frame_col := Color(1, 0, 0) if alive else Color(0.35, 0.35, 0.35)
		var glass_col := Color(1, 1, 1, 0.85) if alive else Color(0.25, 0.25, 0.25, 0.9)
		# 椭圆镜面 + 边框（用多边形近似，尺寸与旧心形相当）
		var pts := PackedVector2Array()
		for k in range(14):
			var ang := TAU * float(k) / 14.0
			pts.append(mir + Vector2(cos(ang) * 8.0, sin(ang) * 11.0))
		draw_colored_polygon(pts, glass_col)
		draw_polyline(pts + PackedVector2Array([pts[0]]), frame_col, 2.0)
		if alive:
			# 完整镜面：左上高光
			draw_line(mir + Vector2(-4, -5), mir + Vector2(-1, 1), Color(1, 1, 1, 0.9), 1.5)
		else:
			# 破碎：几道裂纹
			draw_line(mir + Vector2(-7, -8), mir + Vector2(1, 2), Color(0.8, 0.8, 0.8, 0.55), 1.2)
			draw_line(mir + Vector2(1, 2), mir + Vector2(6, 9), Color(0.8, 0.8, 0.8, 0.55), 1.2)
			draw_line(mir + Vector2(1, 2), mir + Vector2(7, -6), Color(0.8, 0.8, 0.8, 0.45), 1.0)'''
if old_hearts in s:
    s = s.replace(old_hearts, new_hearts, 1)
    print('mirror hp icons done')

# ---------- 战斗 BGM 延后到开场结束 ----------
s = s.replace('\t_stop_map_bgm()\n\tbattle_intro_t = 2.6',
              '\t_stop_map_bgm()\n\t_stop_mirror_bgm()\n\tbattle_intro_t = 2.6\n\tboss_bgm_pending = true', 1)
if 'var boss_bgm_pending' not in s:
    s = s.replace('var ball_hint_t := 0.0', 'var ball_hint_t := 0.0\nvar boss_bgm_pending := false', 1)

# 开场结束后再放战斗 BGM（找 battle_intro_t 递减处）
s = s.replace('\tif battle_intro_t > 0.0:\n\t\tbattle_intro_t = maxf(0.0, battle_intro_t - FIXED_DT)',
              '\tif battle_intro_t > 0.0:\n'
              '\t\tbattle_intro_t = maxf(0.0, battle_intro_t - FIXED_DT)\n'
              '\t\tif battle_intro_t <= 0.0 and boss_bgm_pending:\n'
              '\t\t\tboss_bgm_pending = false\n'
              '\t\t\t_start_battle_bgm()', 1)

if 'func _start_battle_bgm' not in s:
    s += '''

## 战斗 BGM：延后到开场演出结束再响
func _start_battle_bgm() -> void:
	var path := "res://audio/crimson_bgm.ogg" if boss_id == "crimson" else "res://audio/marysue_bgm.ogg"
	if not ResourceLoader.exists(path):
		return
	if battle_bgm_player == null:
		battle_bgm_player = AudioStreamPlayer.new()
		battle_bgm_player.bus = "Master"
		battle_bgm_player.volume_db = -10.0
		add_child(battle_bgm_player)
	var st: AudioStream = load(path)
	if st is AudioStreamOggVorbis:
		st.loop = true
	battle_bgm_player.stream = st
	if not battle_bgm_player.playing:
		battle_bgm_player.play()

func _stop_battle_bgm() -> void:
	if battle_bgm_player != null and battle_bgm_player.playing:
		battle_bgm_player.stop()
'''
    s = s.replace('var boss_bgm_pending := false', 'var boss_bgm_pending := false\nvar battle_bgm_player: AudioStreamPlayer', 1)
    print('battle bgm funcs added')

# ---------- 旋风：放大 + 移动 ----------
s = s.replace('\twhirls = [{"x": base - 320.0, "phase": 0.0}, {"x": base + 320.0, "phase": 1.7}]',
              '\twhirls = [{"x": base - 320.0, "phase": 0.0, "mode": "chase", "dir": 1.0},\n'
              '\t           {"x": base + 320.0, "phase": 1.7, "mode": "sweep", "dir": 1.0}]', 1)

s = s.replace('\tfor w in whirls:\n\t\tw["phase"] = float(w.get("phase", 0.0)) + FIXED_DT * 3.0',
              '\tfor w in whirls:\n'
              '\t\tw["phase"] = float(w.get("phase", 0.0)) + FIXED_DT * 3.0\n'
              '\t\t# 移动：一个慢慢追玩家，一个在地上左右来回扫\n'
              '\t\tif str(w.get("mode", "chase")) == "chase":\n'
              '\t\t\tvar to_x: float = player_pos.x - float(w["x"])\n'
              '\t\t\tw["x"] = float(w["x"]) + signf(to_x) * minf(absf(to_x), 38.0 * FIXED_DT)\n'
              '\t\telse:\n'
              '\t\t\tw["x"] = float(w["x"]) + float(w.get("dir", 1.0)) * 30.0 * FIXED_DT\n'
              '\t\t\tif float(w["x"]) < 200.0:\n\t\t\t\tw["dir"] = 1.0\n'
              '\t\t\tif float(w["x"]) > WORLD_W - 200.0:\n\t\t\t\tw["dir"] = -1.0', 1)

# 碰撞半径放大
s = s.replace('\t\tif dx < 36.0 and player_grounded', '\t\tif dx < 70.0 and player_grounded', 1)
# 绘制放大
s = s.replace('\t\tfor k in range(4):\n\t\t\tvar rr := 14.0 + float(k) * 9.0',
              '\t\tfor k in range(5):\n\t\t\tvar rr := 30.0 + float(k) * 16.0', 1)
s = s.replace('\t\tdraw_circle(Vector2(wx, GROUND_Y - 8.0), 26.0, Color(1, 0, 0, 0.12))',
              '\t\tdraw_circle(Vector2(wx, GROUND_Y - 12.0), 62.0, Color(1, 0, 0, 0.15))', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
