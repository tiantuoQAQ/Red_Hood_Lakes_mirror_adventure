extends SceneTree

## Run with a rendering backend (omit --headless):
## Godot --path <repo> --script res://test/godot_startup_test.gd
## This catches a fade overlay hiding the opening dialogue after Enter.

class ScriptedMain:
	extends "res://godot/main.gd"
	var scripted_input: Dictionary = {}

	func _read_inputs() -> Dictionary:
		return scripted_input

var game: ScriptedMain
var viewport: SubViewport
var failures := 0
const OUTPUT_DIR := "res://tmp/godot_startup"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("This regression test requires real rendering; omit --headless.")
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
	game.scripted_input = {"confirm": true}
	game._physics_process(1.0 / 60.0)
	game.scripted_input = {}
	for tick in range(120):
		game._physics_process(1.0 / 60.0)
	_expect(game.story_fade > 0.98, "Opening retains its intended black scene")
	_expect(game.mode == game.Mode.STORY, "Enter enters the opening chapter")
	_expect(game.story_cmd.get("t") == "say", "Opening reaches the first dialogue")
	_expect(game.story_text.length() > 0 and game.story_reveal > 0, "Opening text is revealed")
	var first_image := await _capture("01_enter.png")
	_expect(_has_visible_text(first_image), "First dialogue remains visible on the black background")
	game.scripted_input = {"confirm": true}
	game._physics_process(1.0 / 60.0)
	game.scripted_input = {}
	for tick in range(60):
		game._physics_process(1.0 / 60.0)
	_expect(game.story_index == 4, "Enter advances to the next opening line")
	var next_image := await _capture("02_next.png")
	_expect(_has_visible_text(next_image), "Next opening line also remains visible")
	game._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	game._notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	_expect(not game.paused, "Refocusing dialogue keeps Enter progression available")
	game.mode = game.Mode.TITLE
	game.paused = false
	game._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	game._notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	_expect(not game.paused, "Refocusing the title keeps the start button available")
	game.mode = game.Mode.BATTLE
	game.paused = false
	game._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	_expect(game.paused, "Battle still pauses automatically when focus is lost")
	print("GODOT_STARTUP_RESULT: %d failure(s)" % failures)
	quit(1 if failures > 0 else 0)

func _capture(filename: String) -> Image:
	game.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	var result := viewport.get_texture().get_image()
	_expect(result.save_png(OUTPUT_DIR.path_join(filename)) == OK, "Save screenshot: " + filename)
	return result

func _has_visible_text(screenshot: Image) -> bool:
	# Inspect the opening text band, away from the border and continue hint.
	# The expected output is readable white text, not a particular glyph/font.
	var light_pixels := 0
	for y in range(578, 610):
		for x in range(80, 760):
			var color := screenshot.get_pixel(x, y)
			if color.r > 0.7 and color.g > 0.7 and color.b > 0.7:
				light_pixels += 1
	return light_pixels > 80

func _expect(condition: bool, label: String) -> void:
	if condition:
		print("PASS: " + label)
	else:
		failures += 1
		push_error("FAIL: " + label)
