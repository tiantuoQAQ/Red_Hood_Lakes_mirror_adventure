extends SceneTree

class ScriptedMain:
	extends "res://godot/main.gd"
	var scripted_input: Dictionary = {}
	func _read_inputs() -> Dictionary:
		return scripted_input

var game: ScriptedMain
var viewport: SubViewport
var failures := 0
const OUTPUT_DIR := "res://tmp/godot_walk_art"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("This art regression requires real rendering; omit --headless.")
		quit(2)
		return
	viewport = SubViewport.new()
	viewport.size = Vector2i(1280, 720)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	get_root().add_child(viewport)
	game = ScriptedMain.new()
	viewport.add_child(game)
	game.set_physics_process(false)
	game.set_process_input(false)
	game._start_walk({"target": {"kind": "norden", "x": 740.0}})
	game.scripted_input = {"dash": true, "right": true}
	game._physics_process(1.0 / 60.0)
	_expect(game.player_dash_frames > 0, "Walk mode starts a dash")
	var start_x := game.player_pos.x
	for tick in range(6):
		game._physics_process(1.0 / 60.0)
	_expect(game.player_pos.x - start_x > 55.0, "Walk dash actually moves faster than running")
	_expect(game.player_stamina < 100.0, "Walk dash consumes stamina")
	game._start_walk({})
	game.previous_input = {}
	game.player_dash_cd = 4
	game.scripted_input = {"dash": true}
	game._physics_process(1.0 / 60.0)
	game.scripted_input = {}
	for tick in range(3):
		game._physics_process(1.0 / 60.0)
	_expect(game.player_dash_frames > 0, "A dash pressed before cooldown ends is buffered")
	game._start_walk({})
	game.previous_input = {}
	game.player_stamina = 45
	game.scripted_input = {"dash": true}
	game._physics_process(1.0 / 60.0)
	_expect(game.player_dash_frames > 0, "The remaining stamina can pay a normal dash")
	game._start_walk({"target": {"kind": "norden", "x": 740.0}})
	game.previous_input = {}
	game.scripted_input = {"jump": true}
	game._physics_process(1.0 / 60.0)
	_expect(not game.player_grounded and game.player_pos.y < 550.0, "Walk mode can jump")
	game._start_walk({"target": {"kind": "norden", "x": 740.0}})
	game.scripted_input = {}
	game.previous_input = {}
	_expect(game.player_dash_frames == 0 and game.player_grounded, "A new walk clears old movement state")
	DirAccess.make_dir_recursive_absolute(OUTPUT_DIR)
	if DisplayServer.get_name() != "headless":
		var snapshot := await _capture("norden_walk.png")
		_expect(_visible_npc_reaches_ground(snapshot), "Norden's visible feet touch the ground")
	if game.has_method("_npc_rect"):
		var rect: Rect2 = game.call("_npc_rect", "norden", Vector2(740, 574))
		# User spec 2026-10-25 wave 11: Norden 85px (was 120, scaled 70/100)
		_expect(rect.size.y > 80 and rect.size.x / rect.size.y < 0.43, "Norden retains the source silhouette proportions")
	else:
		_expect(false, "NPC rendering exposes the shared ground placement")
	for id in ["rek_body_move", "rek_body_charge", "rek_head", "rek_dash_01", "rek_dash_02", "rek_dash_03"]:
		var texture: Texture2D = game.textures.get(id)
		_expect(texture != null, "Runtime sprite loaded: " + id)
		if texture:
			var source := texture.get_image()
			_expect(source.get_pixel(0, 0).a < 0.01, "Runtime sprite has a transparent background: " + id)
	game._start_walk({"target": {"kind": "mabel", "x": 740.0}})
	game.previous_input = {}
	game.scripted_input = {}
	if DisplayServer.get_name() != "headless":
		await _capture("mabel_walk.png")
	game.scripted_input = {"shoot": true}
	game._physics_process(1.0 / 60.0)
	_expect(game.shots.size() > 0, "Walk shooting still emits separate projectiles")
	if DisplayServer.get_name() != "headless":
		await _capture("rek_charge.png")
	game.scripted_input = {"dash": true, "right": true}
	game._physics_process(1.0 / 60.0)
	if DisplayServer.get_name() != "headless":
		await _capture("rek_dash.png")
	for tick in range(7):
		game._physics_process(1.0 / 60.0)
	_expect(game.character_art.player_state(game.player_dash_frames, game.player_dash_out, false) == "dash_02", "Dash advances to the second art frame")
	if DisplayServer.get_name() != "headless":
		await _capture("rek_dash_02.png")
	for tick in range(7):
		game._physics_process(1.0 / 60.0)
	_expect(game.character_art.player_state(game.player_dash_frames, game.player_dash_out, false) == "dash_03", "Dash advances to the third art frame")
	if DisplayServer.get_name() != "headless":
		await _capture("rek_dash_03.png")
	game._start_story("mirror_meet")
	game.story_fade = 0
	game.story_fade_target = 0
	game._set_portrait("rek", "eyes_open")
	game._start_say({"who": "rek_crimson", "expr": "seated_closed", "text": "……"})
	game.story_cmd = {"t": "say"}
	game.story_reveal = 3
	_expect(game._portrait_speaking("crimson_seated_closed"), "An expression variant still highlights its speaker")
	_expect(not game._portrait_speaking("rek_ready"), "The other dialogue portrait remains dim")
	var portrait: Texture2D = game._get_portrait_texture("crimson_seated_closed")
	_expect(portrait != null, "Dialogue expression texture loads")
	_expect(game._get_portrait_texture("crimson") != null, "Crimson base portrait resolves to the standing asset")
	if DisplayServer.get_name() != "headless":
		await _capture("dialogue_expression.png")
		game.story_cmd = {"t": "bossIntro"}
		game.story_intro = "rek_crimson"
		await _capture("crimson_cg.png")
		game.story_intro = "marysue"
		await _capture("marysue_cg.png")
		game._start_battle("crimson", "crimson_fall")
		game.boss_pos = Vector2(930, 226)
		await _capture("crimson_battle.png")
		game._start_battle("marysue", "marysue_defeat")
		game.boss_pos = Vector2(930, 226)
		await _capture("marysue_battle.png")
		# Battle action screenshots: 180 frames after battle start (3 seconds of combat)
		game._start_battle("crimson", "crimson_fall")
		game.boss_pos = Vector2(930, 226)
		game.scripted_input = {"right": true}
		for tick in range(180):
			game._physics_process(1.0 / 60.0)
		await _capture("crimson_battle_action.png")
		game._start_battle("marysue", "marysue_defeat")
		game.boss_pos = Vector2(930, 226)
		game.scripted_input = {"right": true}
		for tick in range(180):
			game._physics_process(1.0 / 60.0)
		await _capture("marysue_battle_action.png")
		# Player-only screenshot to debug gray bar artifact
		await _capture_player_only("player_only.png")
		# Magic circle alignment check: ring center vs boss art center (wave 15 spec)
		var boss_center := game.boss_pos - Vector2(game.camera_x, 0)
		var boss_tex: Texture2D = game.textures.get(game._boss_pose_key())
		if boss_tex:
			var boss_scale := game.BOSS_HEIGHT / boss_tex.get_height()
			var boss_rect := Rect2(boss_center.x - boss_tex.get_width() * boss_scale * 0.5, boss_center.y - boss_tex.get_height() * boss_scale * 0.5, boss_tex.get_width() * boss_scale, boss_tex.get_height() * boss_scale)
			var boss_art_center := boss_rect.get_center()
			var ring_center := boss_center  # Ring is drawn at boss_pos, which is the boss float reference
			var offset := boss_art_center.distance_to(ring_center)
			_expect(offset <= 2.0, "Magic circle concentric with boss art (offset <= 2px): %.1f px" % offset)
	game._stop_music()
	game._start_battle("crimson", "crimson_fall")
	game._stop_music()
	game.previous_input = {}
	game.scripted_input = {"dash": true, "right": true}
	game._physics_process(1.0 / 60.0)
	_expect(game.player_dash_frames > 0 and is_equal_approx(game.player_vel.x, 459.0), "Combat dash begins at 45 percent speed")
	game.scripted_input = {"right": true}
	for tick in range(3):
		game._physics_process(1.0 / 60.0)
	_expect(is_equal_approx(game.player_vel.x, 1020.0), "Combat dash reaches full speed after its ramp")
	print("GODOT_WALK_ART_RESULT: %d failure(s)" % failures)
	quit(1 if failures > 0 else 0)

func _capture(filename: String) -> Image:
	game.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	var result := viewport.get_texture().get_image()
	_expect(result.save_png(OUTPUT_DIR.path_join(filename)) == OK, "Save screenshot: " + filename)
	return result

func _capture_player_only(filename: String) -> Image:
	# Enable player-only rendering mode
	game.debug_player_only = true
	game.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	var result := viewport.get_texture().get_image()
	_expect(result.save_png(OUTPUT_DIR.path_join(filename)) == OK, "Save player-only screenshot: " + filename)
	# Restore normal rendering
	game.debug_player_only = false
	return result

func _visible_npc_reaches_ground(screenshot: Image) -> bool:
	# The lowest visible feet are neutral gray. The background in this band
	# is dark; the floor/cyan line is outside this region.
	var count := 0
	for y in range(564, 574):
		for x in range(710, 770):
			var c := screenshot.get_pixel(x, y)
			if c.r > 0.45 and absf(c.r - c.g) < 0.08 and absf(c.r - c.b) < 0.08:
				count += 1
	return count > 12

func _expect(condition: bool, label: String) -> void:
	if condition:
		print("PASS: " + label)
	else:
		failures += 1
		push_error("FAIL: " + label)
