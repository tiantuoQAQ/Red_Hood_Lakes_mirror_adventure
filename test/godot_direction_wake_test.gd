extends SceneTree

class ScriptedMain:
	extends "res://godot/main.gd"
	var scripted_input: Dictionary = {}
	func _read_inputs() -> Dictionary:
		return scripted_input

var game: ScriptedMain
var viewport: SubViewport
var failures := 0
const OUTPUT_DIR := "res://tmp/godot_direction_wake"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Use a real rendering backend for this regression.")
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
	DirAccess.make_dir_recursive_absolute(OUTPUT_DIR)
	game._start_walk({"playerX": 500})
	game.mouse_seen = true
	game.scripted_input = {"right": true, "dash": true}
	game._physics_process(1.0/60.0)
	_expect(game.player_vel.x > 0, "D dash moves right even when the mouse is behind")
	var start := 500.0
	var reversed := false
	for tick in range(24):
		# Reverse the keyboard while the pointer remains behind the player.
		game.scripted_input = {"left": true}
		game._physics_process(1.0/60.0)
		if game.player_vel.x < 0 or game.player_facing < 0:
			reversed = true
	_expect(not reversed, "Dash and its slide never turn back mid-move")
	_expect(game.player_pos.x - start > 320, "Dash travels at least 320 pixels including its slide")
	game._start_walk({"playerX": 700})
	game.previous_input = {}
	game.scripted_input = {"left": true, "dash": true}
	game._physics_process(1.0/60.0)
	_expect(game.player_vel.x < 0, "A dash moves left")
	game._start_walk({"playerX": 700})
	game.mouse_seen = false
	game.previous_input = {}
	game.scripted_input = {"right": true}
	game._physics_process(1.0/60.0)
	game.scripted_input = {}
	game._physics_process(1.0/60.0)
	game.mouse_seen = true
	game.scripted_input = {"dash": true}
	game._physics_process(1.0/60.0)
	_expect(game.player_vel.x > 0, "Dash without A/D uses the last movement direction")
	game._start_story("ambush")
	# Start at the real flash command, after all the confrontation dialogue.
	for index in range(game.story_commands.size()):
		if game.story_commands[index].get("t") == "flash":
			game.story_index = index
			break
	game._story_advance()
	game.scripted_input = {}
	_expect(game.story_cmd.get("t") == "flash", "Confrontation ends with the flash sequence")
	if game.has_method("_flash_color"):
		_expect(game.call("_flash_color") == Color.WHITE, "The first flash is fully white")
		var white_frame := await _capture("04_white_flash.png")
		_expect(_is_solid(white_frame, Color.WHITE), "The actual rendered flash covers the screen in white")
		for tick in range(7):
			game._physics_process(1.0/60.0)
		_expect(game.call("_flash_color") == Color.BLACK, "The flash sequence advances to black")
	else:
		_expect(false, "Flash segments expose their actual draw color")
	for tick in range(31):
		game._physics_process(1.0/60.0)
	var transition_frame := await _capture("08_flash_to_blackout.png")
	_expect(_is_solid(transition_frame, Color.BLACK), "The final black flash connects to the blackout without exposing the old scene")
	var saw_black_hold := false
	var hold_ticks := 0
	var captured_hold := false
	for tick in range(600):
		var current_kind: String = game.story_cmd.get("t", "")
		if current_kind == "wait" and game.story_fade > .98:
			saw_black_hold = true
			hold_ticks += 1
			if not captured_hold:
				captured_hold = true
				var black_frame := await _capture("05_blackout.png")
				_expect(_is_solid(black_frame, Color.BLACK), "The blackout renders a fully black screen")
		if current_kind == "say":
			break
		game.scripted_input = {"confirm": tick % 2 == 0}
		game._physics_process(1.0/60.0)
	_expect(saw_black_hold and hold_ticks >= 145, "Blackout holds for 2.5 seconds even if Enter is pressed")
	_expect(game.story_cmd.get("t") == "say" and "哪里" in game.story_text and game.story_who == "rek", "Rek wakes and asks where she is before meeting Norden")
	_expect(game.story_fade < .02, "The screen has brightened before the wake-up line")
	_expect(game.story_data["ambush"]["cmds"].filter(func(command): return command.get("t") == "flash")[0]["seq"].size() == 4, "Playing the flash does not erase the reusable story sequence")
	_expect(game.story_right == "", "Marysue's portrait has left before Rek wakes")
	game.story_reveal = float(game.story_text.length())
	await _capture("06_rek_wakes.png")
	game.previous_input = {}
	game.scripted_input = {"confirm": true}
	game._physics_process(1.0/60.0)
	_expect(game.mode == game.Mode.WALK, "Wake-up dialogue continues to exploration")
	var npc_x: float = game.walk_target.get("x", 0.0)
	_expect(game.camera_x == 0 and npc_x > 1450, "Norden starts beyond the first screen")
	await _capture("01_wake_exploration.png")
	game.scripted_input = {"right": true}
	for tick in range(420):
		game._physics_process(1.0/60.0)
	_expect(game.camera_x > 500 and npc_x - game.camera_x < 1250, "Walking right extends the camera and reveals Norden")
	await _capture("02_norden_revealed.png")
	game._start_story("ambush")
	game.story_fade = 0
	game.story_fade_target = 0
	game._set_portrait("rek", "eyes_open")
	game._start_say({"who": "marysue", "text": "……"})
	game.story_cmd = {"t": "say"}
	game.story_reveal = 3
	await _capture("03_lower_portraits.png")
	# Traverse the real opening without jumping over the missing CG fallback,
	# then walk all the way to Norden and interact using the actual input loop.
	game._start_story("prologue")
	game.previous_input = {}
	var saw_trap := false
	var saw_wake := false
	var saw_flash_again := false
	for tick in range(2400):
		game.scripted_input = {"confirm": tick % 2 == 0}
		if game.mode == game.Mode.WALK:
			game.scripted_input["right"] = true
		game._physics_process(1.0/60.0)
		if game.story_cmd.get("t") == "flash":
			saw_flash_again = true
		if game.story_cmd.get("t") == "cg" and not saw_trap:
			saw_trap = true
			await _capture("07_trap_fallback.png")
		if game.chapter_id == "ambush" and game.story_cmd.get("t") == "say" and "哪里" in game.story_text:
			saw_wake = true
		if game.chapter_id == "wake_talk":
			break
	_expect(saw_trap and saw_flash_again and saw_wake and game.chapter_id == "wake_talk", "The full opening reaches the trap, flashing, waking, exploration and Norden interaction")
	game._stop_music()
	print("GODOT_DIRECTION_WAKE_RESULT: %d failure(s)" % failures)
	quit(1 if failures else 0)

func _capture(filename: String) -> Image:
	game.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	var result := viewport.get_texture().get_image()
	_expect(result.save_png(OUTPUT_DIR.path_join(filename)) == OK, "Save screenshot: " + filename)
	return result

func _is_solid(snapshot: Image, color: Color) -> bool:
	for y in range(0, 720, 60):
		for x in range(0, 1280, 80):
			var pixel := snapshot.get_pixel(x, y)
			if absf(pixel.r - color.r) > .01 or absf(pixel.g - color.g) > .01 or absf(pixel.b - color.b) > .01:
				return false
	return true

func _expect(condition: bool, label: String) -> void:
	if condition:
		print("PASS: " + label)
	else:
		failures += 1
		push_error("FAIL: " + label)
