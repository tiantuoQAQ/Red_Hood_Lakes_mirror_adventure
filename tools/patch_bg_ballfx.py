# -*- coding: utf-8 -*-
"""背景重做接入 + 地面倒影 + 球形态提示 + 球形态特效(拖尾/激光/烟雾) + 序章长走位与远处黑影。"""
import io

# ---------------- story：序章走位加长 + 远处黑影 ----------------
p = 'src/story.js'
s = io.open(p, encoding='utf-8').read()
old = "{ t: 'walk', untilX: 1040, next: 'ambush' }"
new = "{ t: 'walk', untilX: 2600, props: [{ kind: 'shadow', x: 2800 }], next: 'ambush' }"
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('prologue walk extended + shadow prop')
else:
    print('prologue walk not found')

# ---------------- Godot ----------------
p2 = 'godot/main.gd'
g = io.open(p2, encoding='utf-8').read()
orig = g

# 1) 载入新背景 + 球拖尾帧
if 'bg_forest' not in g:
    g = g.replace('\t\t"mirror": "res://art/bg/mirror.jpg",',
                  '\t\t"mirror": "res://art/bg/mirror.jpg",\n'
                  '\t\t"bg_forest": "res://art/bg/bg_forest.png",\n'
                  '\t\t"bg_mirrorworld": "res://art/bg/bg_mirrorworld.png",', 1)
    print('bg textures registered')

if 'ball_trail_frames' not in g:
    g = g.replace('var boss_anim: Dictionary = {}',
                  'var ball_trail_frames: Array = []   # 球形态拖尾 8 帧\nvar boss_anim: Dictionary = {}', 1)
    g = g.replace('\t# 战前开场动画帧（即梦 mp4 抽帧，24 帧）',
                  '\t# 球形态拖尾帧（用户提供素材）\n'
                  '\tball_trail_frames.clear()\n'
                  '\tfor fi in range(8):\n'
                  '\t\tvar btex := _load_texture("res://art/fx/ball_trail/frame_%02d.png" % fi)\n'
                  '\t\tif btex:\n'
                  '\t\t\tball_trail_frames.append(btex)\n'
                  '\t# 战前开场动画帧（即梦 mp4 抽帧，24 帧）', 1)
    print('ball trail frames loader added')

# 2) 背景选择：forest → bg_forest；mirror 世界 → bg_mirrorworld
g = g.replace('\tvar bg_key := "mirror" if mode == Mode.BATTLE else (story_bg if story_bg == "mirror" else "mirror_alt")',
              '\tvar bg_key := "bg_mirrorworld"\n'
              '\tif mode == Mode.BATTLE:\n'
              '\t\tbg_key = "bg_mirrorworld"\n'
              '\telif story_bg == "forest":\n'
              '\t\tbg_key = "bg_forest"\n'
              '\telif story_bg == "void":\n'
              '\t\tbg_key = "bg_mirrorworld"\n'
              '\telse:\n'
              '\t\tbg_key = "bg_mirrorworld"', 1)

# 3) 走位段：远处黑影道具
g = g.replace('\t\telif kind == "mirror":\n\t\t\t_draw_mirror_gate(pos)',
              '\t\telif kind == "mirror":\n\t\t\t_draw_mirror_gate(pos)\n'
              '\t\telif kind == "shadow":\n'
              '\t\t\t# 远处玛丽苏黑影：纯黑剪影 + 微红眼\n'
              '\t\t\tdraw_rect(Rect2(pos.x - 26, pos.y - 150, 52, 150), Color(0, 0, 0, 0.92))\n'
              '\t\t\tdraw_circle(Vector2(pos.x - 8, pos.y - 138), 3, Color(1, 0, 0, 0.85))\n'
              '\t\t\tdraw_circle(Vector2(pos.x + 8, pos.y - 138), 3, Color(1, 0, 0, 0.85))', 1)

# 4) 地面倒影：走位/战斗都画（镜中世界）
if 'func _draw_player_reflection' not in g:
    g += '''

# ======================= 地面倒影 + 球形态特效 =======================
func _draw_player_reflection() -> void:
	if mode != Mode.WALK and mode != Mode.BATTLE:
		return
	if player_ball:
		return
	var tex: Texture2D = textures.get("rek_body_move")
	if tex == null:
		return
	var foot := Vector2(player_pos.x - camera_x, GROUND_Y)
	var h := 70.0
	var w := h * tex.get_width() / float(tex.get_height())
	var refl := Color(1, 1, 1, 0.22)
	draw_set_transform(foot, 0.0, Vector2(1.0, -1.0))
	draw_texture_rect(tex, Rect2(Vector2(-w * 0.5, 0), Vector2(w, h)), false, refl)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_ball_fx() -> void:
	if not player_ball:
		return
	var center := player_pos - Vector2(camera_x, 0)
	var vel := player_vel
	var dir := vel.normalized() if vel.length() > 1.0 else Vector2.LEFT
	# 1) 拖尾丝带（用户素材，8 帧）
	for i in range(3):
		if ball_trail_frames.size() == 0:
			break
		var idx := int(frame / 3 + i * 3) % ball_trail_frames.size()
		var ttex: Texture2D = ball_trail_frames[idx]
		var back := center - dir * (26.0 + float(i) * 22.0)
		var sz := 74.0 - float(i) * 12.0
		var a := 0.55 - float(i) * 0.12
		draw_set_transform(back, dir.angle() + PI * 0.5, Vector2(1, 1))
		draw_texture_rect(ttex, Rect2(Vector2(-sz * 0.5, -sz * 0.5), Vector2(sz, sz)), false, Color(1, 1, 1, a))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	# 2) 红色激光淡出（两道）
	for i in range(2):
		var side := (1.0 if i == 0 else -1.0) * 14.0
		var from := center - dir * 18.0 + Vector2(0, side)
		var to := center - dir * (150.0 + float(i) * 60.0) + Vector2(0, side * 1.6)
		draw_line(from, to, Color(1, 0, 0, 0.45 - float(i) * 0.16), 4.0 - float(i) * 1.2)
		draw_line(from, to, Color(1, 1, 1, 0.20 - float(i) * 0.07), 1.5)
	# 3) 烟雾：缓慢扩散的灰色圆
	for i in range(4):
		var ph := fmod(elapsed * 0.9 + float(i) * 0.25, 1.0)
		var smoke_pos := center - dir * (30.0 + ph * 90.0) + Vector2(0, sin(float(i) * 2.1 + elapsed) * 10.0)
		draw_circle(smoke_pos, 10.0 + ph * 22.0, Color(0.55, 0.55, 0.55, 0.16 * (1.0 - ph)))
'''
    print('reflection + ball fx appended')

# 5) 调用：倒影在玩家之前，球特效在玩家之后
g = g.replace('\t_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)\n\t_draw_particles_world()\n\t_draw_battle_overlays()',
              '\t_draw_player_reflection()\n\t_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)\n\t_draw_ball_fx()\n\t_draw_particles_world()\n\t_draw_battle_overlays()', 1)
g = g.replace('\t_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)\n\t_draw_particles_world()\n\tdraw_string(ThemeDB.fallback_font, Vector2(40, 48)',
              '\t_draw_player_reflection()\n\t_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)\n\t_draw_ball_fx()\n\t_draw_particles_world()\n\tdraw_string(ThemeDB.fallback_font, Vector2(40, 48)', 1)

# 6) 球形态教学提示（走位段前 6 秒）
if 'var ball_hint_t' not in g:
    g = g.replace('var hurt_vignette := 0', 'var hurt_vignette := 0\nvar ball_hint_t := 0.0', 1)
    g = g.replace('\t_start_map_bgm()', '\t_start_map_bgm()\n\tball_hint_t = 6.0', 1)
    g = g.replace('\tif hurt_vignette > 0:', '\tif ball_hint_t > 0.0:\n\t\tball_hint_t = maxf(0.0, ball_hint_t - FIXED_DT)\n\t\tvar ha := minf(1.0, ball_hint_t / 1.0)\n\t\tdraw_string(ThemeDB.fallback_font, Vector2(360, 200), "空中 按住 W + 冲刺 → 球形态（无敌）", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color(1, 1, 1, 0.85 * ha))\n\tif hurt_vignette > 0:', 1)

io.open(p2, 'w', encoding='utf-8').write(g)
print('godot patched' if g != orig else 'godot unchanged')
