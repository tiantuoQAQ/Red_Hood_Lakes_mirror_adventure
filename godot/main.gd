extends Node2D

## MIRROR Godot vertical slice.
## The story is data driven from docs/story_export.json; combat keeps the
## browser prototype's fixed 60 Hz numbers and is drawn in this single scene
## so it remains easy to tune against the Web reference.

const VIEW := Vector2(1280.0, 720.0)
const WORLD_W := 2400.0
const GROUND_Y := 574.0
const ARENA_LEFT := 48.0
const ARENA_RIGHT := WORLD_W - 48.0
const RED := Color("#ff0000")
const HAZARD := Color("#82ff00")
const CYAN := Color("#00baff")
const WHITE := Color("#f1f1f1")
const GREY := Color("#9a9a9a")
const BLACK := Color("#090909")
const BG := Color("#111111")
const FIXED_DT := 1.0 / 60.0
const DASH_STAMINA_COST := 3.0
const BALL_ENTRY_STAMINA_COST := 7.0

enum Mode { TITLE, STORY, WALK, BATTLE, VICTORY, END }
var mode: Mode = Mode.TITLE
var frame := 0
var elapsed := 0.0
var paused := false
var previous_input: Dictionary = {}
var input_state: Dictionary = {}
var mouse_seen := false
var last_mouse := Vector2.ZERO

var story_data: Dictionary = {}
var chapter_id := ""
var story_commands: Array = []
var story_index := 0
var story_cmd: Dictionary = {}
var story_timer := 0.0
var story_reveal := 0.0
var story_text := ""
var story_who := ""
var story_expr := ""
var story_left := ""
var story_left_expr := ""
var story_right := ""
var story_right_expr := ""
var story_card := ["", ""]
var story_title := ""
var story_title_sub := ""
var story_intro := ""
var story_bg := "night"
var story_fade := 0.0
var story_fade_target := 0.0
var story_fade_speed := 0.0
var story_flash := 0.0
var story_cg: Texture2D
var story_next := ""
var walk_target: Dictionary = {}
var walk_props: Array = []
var walk_next := ""
var walk_until := -1.0
var walk_camera := false
var camera_x := 0.0

var boss_id := "crimson"
var boss_after := ""
var boss_pos := Vector2(1840.0, 226.0)
var boss_target := Vector2.ZERO
var boss_hp := 240.0
var boss_max_hp := 240.0
var boss_phase := 0
var boss_phase_count := 5
var boss_attack_timer := 0
var boss_move_timer := 0
var boss_hit_flash := 0
var boss_skill_name := ""
var bullets: Array = []
var shots: Array = []
var warnings: Array = []
var particles: Array = []
var mirror_shards: Array = []
var trail: Array = []
var hitstop := 0
var screen_shake := 0.0
var red_vignette := 0.0
var banner := ""
var banner_timer := 0
var hellfire_timer := 0
var hellfire_tick := 0

var player_pos := Vector2(250.0, GROUND_Y - 20.0)
var player_vel := Vector2.ZERO
var player_grounded := true
var player_facing := 1.0
var player_hp := 3
var player_stamina := 100.0
var player_courage := 0.0
var player_energy := 4
var player_dash_frames := 0
var player_dash_buffer := 0
var player_dash_ramp := 0
var player_dash_cd := 0
var player_dash_invuln := 0
var player_dash_out := 0
var player_ball := false
var player_ball_launch := 0
var player_hurt_invuln := 0
var player_fire_cd := 0
var player_jump_buffer := 0
var player_graze_chain := 0
var player_graze_age := 0
var player_dying := false
var skill_red_tragedy := false

var textures: Dictionary = {}
var character_art = preload("res://godot/character_art.gd").new()
var music_player: AudioStreamPlayer
var current_music := ""

func _ready() -> void:
	_load_assets()
	_load_story()
	music_player = AudioStreamPlayer.new()
	music_player.name = "BattleMusic"
	add_child(music_player)
	queue_redraw()

func _load_assets() -> void:
	var paths := {
		"rek_body_move": "res://art/battle/rek/body_move.png",
		"rek_body_charge": "res://art/battle/rek/body_charge.png",
		"rek_head": "res://art/battle/rek/head.png",
		"rek_dash_01": "res://art/battle/rek/dash_01.png",
		"rek_dash_02": "res://art/battle/rek/dash_02.png",
		"rek_dash_03": "res://art/battle/rek/dash_03.png",
		"mirror": "res://art/bg/mirror.jpg",
		"mirror_alt": "res://art/bg/mirror_alt.jpg",
		"throne": "res://art/obj/throne.png",
		"norden": "res://art/char/norden_idle.png",
		"mabel": "res://art/char/mabel_idle.png",
		"crimson_01": "res://art/battle/scarlet/scarlet-action-red-eyes-01-cutout.png",
		"crimson_02": "res://art/battle/scarlet/scarlet-action-red-eyes-02-cutout.png",
		"crimson_03": "res://art/battle/scarlet/scarlet-action-red-eyes-03-cutout.png",
		"crimson_04": "res://art/battle/scarlet/scarlet-action-red-eyes-04-cutout.png",
		"marysue_01": "res://art/battle/marysue/marysue-battle-01.png",
		"marysue_02": "res://art/battle/marysue/marysue-battle-02.png",
		"marysue_03": "res://art/battle/marysue/marysue-battle-03.png",
		"cutin_crimson": "res://art/cg/cutin_crimson.png",
		"cutin_marysue": "res://art/cg/cutin_marysue.png"
	}
	for key in paths:
		var tex = _load_texture(paths[key])
		if tex is Texture2D:
			textures[key] = tex

func _load_texture(path: String) -> Texture2D:
	if ResourceLoader.exists(path):
		var imported = load(path)
		if imported is Texture2D:
			return imported
	# Fresh PNGs can also run before the editor's next import scan.
	var source := Image.load_from_file(path)
	return ImageTexture.create_from_image(source) if source else null

func _load_story() -> void:
	var raw := FileAccess.get_file_as_string("res://docs/story_export.json")
	var parsed = JSON.parse_string(raw)
	if parsed is Dictionary:
		story_data = parsed

func _physics_process(_delta: float) -> void:
	frame += 1
	elapsed += FIXED_DT
	input_state = _read_inputs()
	if _just("mute"):
		if music_player:
			music_player.volume_db = -80.0 if music_player.volume_db > -40.0 else -4.0
	if _just("pause") and mode == Mode.BATTLE:
		paused = not paused
	if _just("restart") and mode != Mode.TITLE:
		mode = Mode.TITLE
		paused = false
		_stop_music()
	if not paused:
		match mode:
			Mode.TITLE:
				_update_title()
			Mode.STORY:
				_update_story()
			Mode.WALK:
				_update_walk()
			Mode.BATTLE:
				_update_battle()
			Mode.VICTORY:
				_update_victory()
			Mode.END:
				_update_end()
	_update_fx()
	previous_input = input_state.duplicate()
	queue_redraw()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		previous_input.clear()
		input_state.clear()
		# Only battle has a pause/resume control. Do not freeze the title
		# or dialogue when the player switches windows.
		paused = mode == Mode.BATTLE
	elif what == NOTIFICATION_APPLICATION_FOCUS_IN and mode != Mode.BATTLE:
		paused = false

func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		mouse_seen = true
		last_mouse = event.position
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT:
		get_viewport().set_input_as_handled()

func _read_inputs() -> Dictionary:
	return {
		"left": Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT),
		"right": Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT),
		"up": Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP),
		"down": Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN),
		"jump": Input.is_key_pressed(KEY_SPACE),
		"dash": Input.is_key_pressed(KEY_SHIFT) or Input.is_key_pressed(KEY_K) or Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT),
		"shoot": Input.is_key_pressed(KEY_J) or Input.is_key_pressed(KEY_Z) or Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT),
		"skill": Input.is_key_pressed(KEY_L) or Input.is_key_pressed(KEY_X),
		"gunfire": Input.is_key_pressed(KEY_C),
		"hellfire": Input.is_key_pressed(KEY_V),
		"confirm": Input.is_key_pressed(KEY_ENTER) or Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_W),
		"skip": Input.is_key_pressed(KEY_TAB),
		"pause": Input.is_key_pressed(KEY_P),
		"restart": Input.is_key_pressed(KEY_R),
		"mute": Input.is_key_pressed(KEY_M)
	}

func _just(action: String) -> bool:
	return bool(input_state.get(action, false)) and not bool(previous_input.get(action, false))

func _update_title() -> void:
	if _just("confirm"):
		_start_story("prologue")

func _start_story(id: String) -> void:
	if not story_data.has(id):
		mode = Mode.END
		return
	chapter_id = id
	story_commands = Array(story_data[id].get("cmds", []))
	story_index = 0
	story_cmd = {}
	story_text = ""
	story_reveal = 0.0
	mode = Mode.STORY
	_story_advance()

func _story_advance() -> void:
	var guard := 0
	while guard < 32 and story_index < story_commands.size():
		guard += 1
		var command: Dictionary = story_commands[story_index]
		story_index += 1
		var kind := str(command.get("t", ""))
		story_cmd = command
		story_title = ""
		story_title_sub = ""
		story_intro = ""
		if kind != "cg":
			story_cg = null
		if kind != "card":
			story_card = ["", ""]
		match kind:
			"scene":
				story_bg = str(command.get("bg", story_bg))
				continue
			"music":
				_set_music(str(command.get("name", "stop")))
				continue
			"next":
				_start_story(str(command.get("chapter", "ending")))
				return
			"grant":
				if str(command.get("skill", "")) == "red_tragedy":
					skill_red_tragedy = true
					banner = str(command.get("banner", "红之惨剧"))
					banner_timer = 150
				continue
			"battle":
				_start_battle(str(command.get("boss", "crimson")), str(command.get("after", "ending")))
				return
			"walk":
				_start_walk(command)
				return
			"say":
				_start_say(command)
				return
			"duel":
				_start_duel(command)
				return
			"card":
				story_card = [str(command.get("line1", "")), str(command.get("line2", ""))]
				story_timer = float(command.get("frames", 120)) / 60.0
				return
			"title":
				story_title = str(command.get("title", command.get("text", "")))
				story_title_sub = str(command.get("subtitle", ""))
				story_timer = float(command.get("frames", 100)) / 60.0
				return
			"pose":
				if command.has("who"):
					_set_portrait(str(command.get("who", "")), str(command.get("expr", "")))
				story_timer = float(command.get("frames", 30)) / 60.0
				return
			"intro":
				story_intro = str(command.get("id", ""))
				story_timer = 1.8
				return
			"bossIntro":
				story_intro = str(command.get("id", boss_id))
				story_timer = float(command.get("frames", 120)) / 60.0
				return
			"fade":
				story_fade_target = 1.0 if str(command.get("to", "black")) == "black" else 0.0
				story_timer = float(command.get("frames", 30)) / 60.0
				story_fade_speed = 1.0 / maxf(0.1, story_timer)
				return
			"flash":
				story_flash = 0.25
				story_timer = 0.55
				return
			"wait":
				story_timer = float(command.get("frames", 30)) / 60.0
				return
			"mirrorfx":
				_spawn_mirror_shards(int(command.get("count", 20)), float(command.get("power", 1.0)))
				story_timer = float(command.get("dur", 90)) / 60.0
				return
			"cg":
				var art_path := str(command.get("art", ""))
				story_cg = load("res://" + art_path) if art_path != "" else null
				story_timer = float(command.get("frames", 90)) / 60.0
				return
			"end":
				mode = Mode.END
				return
			_:
				continue
	mode = Mode.END

func _start_say(command: Dictionary) -> void:
	story_who = str(command.get("who", ""))
	story_expr = str(command.get("expr", ""))
	story_text = str(command.get("text", ""))
	story_reveal = 0.0
	if story_who != "":
		_set_portrait(story_who, story_expr)
	story_timer = 0.0

func _start_duel(command: Dictionary) -> void:
	story_left = str(command.get("left", "rek"))
	story_right = str(command.get("right", ""))
	story_left_expr = str(command.get("left_expr", ""))
	story_right_expr = str(command.get("right_expr", ""))
	story_who = str(command.get("speaker", story_left))
	story_expr = ""
	story_text = str(command.get("text", ""))
	story_reveal = 0.0

func _set_portrait(who: String, expr: String) -> void:
	var id := _portrait_id(who, expr)
	if _portrait_base(who) == "rek":
		story_left = id
		story_left_expr = expr
	else:
		story_right = id
		story_right_expr = expr

func _portrait_id(who: String, expr: String) -> String:
	var base := _portrait_base(who)
	if base == "crimson" and expr == "":
		return "crimson_stand"
	return base + ("_" + expr if expr != "" else "")

func _portrait_base(who: String) -> String:
	var base := who
	if who == "rek_crimson":
		base = "crimson"
	if who == "蕾克":
		base = "rek"
	if who == "猩红魔姬":
		base = "crimson"
	if who == "诺登":
		base = "norden"
	if who == "梅贝尔":
		base = "mabel"
	if who == "玛丽苏":
		base = "marysue"
	return base

func _portrait_speaking(id: String) -> bool:
	var base := _portrait_base(story_who)
	return base != "" and (id == base or id.begins_with(base + "_"))

func _update_story() -> void:
	if _just("skip"):
		while story_index < story_commands.size():
			var skip_kind := str(story_commands[story_index].get("t", ""))
			story_index += 1
			if skip_kind == "battle" or skip_kind == "walk":
				story_cmd = story_commands[story_index - 1]
				if skip_kind == "battle":
					_start_battle(str(story_cmd.get("boss", "crimson")), str(story_cmd.get("after", "ending")))
				else:
					_start_walk(story_cmd)
				return
		if story_index >= story_commands.size():
			mode = Mode.END
			return
	if story_cmd.get("t", "") == "say" or story_cmd.get("t", "") == "duel":
		story_reveal = minf(float(story_text.length()), story_reveal + 1.9)
		if _just("confirm"):
			if story_reveal < story_text.length():
				story_reveal = float(story_text.length())
			else:
				_story_advance()
		return
	if story_timer > 0.0:
		story_timer -= FIXED_DT
	if story_fade != story_fade_target:
		story_fade = move_toward(story_fade, story_fade_target, story_fade_speed * FIXED_DT)
	if story_flash > 0.0:
		story_flash = maxf(0.0, story_flash - FIXED_DT)
	if _just("confirm") and story_timer > 0.0:
		story_timer = 0.0
	if story_timer <= 0.0 and absf(story_fade - story_fade_target) < 0.02:
		_story_advance()

func _finish_walk() -> void:
	var next := walk_next
	walk_target = {}
	walk_props.clear()
	walk_next = ""
	if next != "":
		_start_story(next)
	else:
		mode = Mode.TITLE

func _start_walk(command: Dictionary) -> void:
	mode = Mode.WALK
	paused = false
	walk_next = str(command.get("next", ""))
	walk_until = float(command.get("untilX", -1.0))
	var player_x = command.get("playerX", 180.0)
	player_pos = Vector2(float(player_x), GROUND_Y - 20.0)
	player_vel = Vector2.ZERO
	player_grounded = true
	player_ball = false
	player_dash_frames = 0
	player_dash_buffer = 0
	player_dash_ramp = 0
	player_dash_out = 0
	player_dash_cd = 0
	player_jump_buffer = 0
	player_stamina = 100.0
	bullets.clear()
	warnings.clear()
	shots.clear()
	trail.clear()
	particles.clear()
	walk_target = command.get("target", {})
	walk_props = command.get("props", [])
	walk_camera = bool(command.get("cam", false))
	if command.has("bg"):
		story_bg = str(command.get("bg", story_bg))
	camera_x = 0.0

func _update_walk() -> void:
	_update_player()
	_update_shots()
	if walk_camera:
		camera_x = lerpf(camera_x, clampf(player_pos.x - 360.0, 0.0, WORLD_W - VIEW.x), 0.12)
	if walk_target.size() > 0:
		var target_x := float(walk_target.get("x", player_pos.x))
		if _just("confirm") and absf(player_pos.x - target_x) < 110.0:
			_finish_walk()
			return
	if walk_until >= 0.0 and player_pos.x >= walk_until:
		_finish_walk()

func _start_battle(id: String, after: String) -> void:
	mode = Mode.BATTLE
	boss_id = id
	boss_after = after
	boss_max_hp = 240.0 if id == "crimson" else 420.0
	boss_hp = boss_max_hp
	boss_phase = 0
	boss_phase_count = 5 if id == "crimson" else 6
	boss_pos = Vector2(1840.0, 226.0)
	boss_target = boss_pos
	boss_attack_timer = 45 if id == "crimson" else 30
	boss_move_timer = 0
	boss_hit_flash = 0
	boss_skill_name = "猩红裁决" if id == "crimson" else "黑童话·终章"
	bullets.clear()
	warnings.clear()
	shots.clear()
	particles.clear()
	trail.clear()
	mirror_shards.clear()
	player_pos = Vector2(350.0, GROUND_Y - 20.0)
	player_vel = Vector2.ZERO
	player_grounded = true
	player_hp = 3
	player_stamina = 100.0
	player_courage = 0.0
	player_energy = 4
	player_dash_frames = 0
	player_dash_buffer = 0
	player_dash_ramp = 0
	player_dash_cd = 0
	player_dash_invuln = 0
	player_dash_out = 0
	player_ball = false
	player_hurt_invuln = 0
	player_graze_chain = 0
	player_graze_age = 0
	player_dying = false
	camera_x = 0.0
	banner = "BATTLE START"
	banner_timer = 90
	_set_music("crimson" if id == "crimson" else "marysue")

func _set_music(name: String) -> void:
	if name == "stop":
		_stop_music()
		return
	if name == current_music and music_player.playing:
		return
	var path := "res://audio/" + name + "_bgm.ogg"
	var stream = load(path)
	if stream:
		music_player.stream = stream
		music_player.volume_db = -4.0
		music_player.play()
		current_music = name

func _stop_music() -> void:
	if music_player:
		music_player.stop()
	current_music = ""

func _update_battle() -> void:
	if hitstop > 0:
		hitstop -= 1
		return
	_update_player()
	_update_boss()
	_update_shots()
	_update_bullets()
	_update_camera()
	if _just("skill"):
		_use_red_skill()
	if _just("gunfire"):
		_use_gunfire()
	if _just("hellfire"):
		_use_hellfire()
	if banner_timer > 0:
		banner_timer -= 1
	if screen_shake > 0.0:
		screen_shake = maxf(0.0, screen_shake - 0.36)

func _update_player() -> void:
	player_dash_cd = maxi(0, player_dash_cd - 1)
	player_dash_invuln = maxi(0, player_dash_invuln - 1)
	player_hurt_invuln = maxi(0, player_hurt_invuln - 1)
	player_fire_cd = maxi(0, player_fire_cd - 1)
	player_jump_buffer = maxi(0, player_jump_buffer - 1)
	player_graze_age = maxi(0, player_graze_age - 1)
	if player_graze_age == 0:
		player_graze_chain = 0
	for item in trail:
		item["life"] = float(item.get("life", 0.0)) - FIXED_DT
	trail = trail.filter(func(item): return float(item.get("life", 0.0)) > 0.0)
	var axis := float(int(input_state.get("right", false)) - int(input_state.get("left", false)))
	var vertical := float(int(input_state.get("down", false)) - int(input_state.get("up", false)))
	if axis != 0.0:
		player_facing = signf(axis)
	var aim_world := get_viewport().get_mouse_position() + Vector2(camera_x, 0)
	if mouse_seen and absf(aim_world.x - player_pos.x) > 18.0:
		player_facing = -1.0 if aim_world.x < player_pos.x else 1.0
	if _just("jump"):
		player_jump_buffer = 8
	var dash_pressed := _just("dash")
	if player_ball:
		player_stamina = maxf(0.0, player_stamina - 32.0 * FIXED_DT)
		if not bool(input_state.get("dash", false)) or player_stamina <= 0.0:
			_exit_ball()
		else:
			var ball_dir := Vector2(axis, vertical)
			if player_ball_launch > 0:
				ball_dir = Vector2(0, -1)
				player_ball_launch -= 1
			if ball_dir.length() > 0.0:
				ball_dir = ball_dir.normalized()
			player_vel = ball_dir * 450.0
			player_pos += player_vel * FIXED_DT
			player_pos.x = clampf(player_pos.x, ARENA_LEFT, ARENA_RIGHT)
			player_pos.y = clampf(player_pos.y, 48.0, GROUND_Y - 20.0)
			if frame % 2 == 0:
				_spawn_particle(player_pos - player_vel.normalized() * 18.0, CYAN, 0.4, -player_vel.normalized() * 60.0, 4.0)
			_check_graze_and_hits()
			return
	if dash_pressed and not player_grounded and bool(input_state.get("up", false)) and player_stamina > 20.0:
		player_ball = true
		player_dash_frames = 0
		player_dash_out = 0
		player_dash_buffer = 0
		player_stamina = maxf(0.0, player_stamina - BALL_ENTRY_STAMINA_COST)
		player_vel.x *= 0.4
		player_vel.y = -450.0
		player_ball_launch = 5
		_spawn_burst(player_pos, RED, 14)
		return
	if dash_pressed:
		player_dash_buffer = 8
	if player_dash_buffer > 0:
		if player_dash_cd <= 0 and player_dash_frames == 0 and player_dash_out == 0 and player_stamina >= DASH_STAMINA_COST:
			player_stamina -= DASH_STAMINA_COST
			player_dash_buffer = 0
			player_dash_frames = 12
			player_dash_ramp = 3
			player_dash_cd = 28
			player_dash_invuln = 16
			_spawn_burst(player_pos, RED, 8)
		else:
			player_dash_buffer -= 1
	if player_dash_frames > 0:
		player_dash_frames -= 1
		var ramp := 1.0
		if player_dash_ramp > 0:
			var progress := 1.0 - float(player_dash_ramp) / 3.0
			ramp = 0.45 + 0.55 * (1.0 - pow(1.0 - progress, 2.0))
			player_dash_ramp -= 1
		player_vel = Vector2(player_facing * 1020.0 * ramp, 0)
		player_pos += player_vel * FIXED_DT
		trail.append({"pos": player_pos, "life": 0.2, "max": 0.2})
		if trail.size() > 12:
			trail.pop_front()
		if player_dash_frames == 0:
			player_dash_out = 6
	elif player_dash_out > 0:
		player_dash_out -= 1
		player_vel.x = lerpf(player_vel.x, axis * 340.0, 0.28)
		player_pos += player_vel * FIXED_DT
	else:
		if player_grounded and player_jump_buffer > 0:
			player_vel.y = -700.0
			player_grounded = false
			player_jump_buffer = 0
		var target_speed := axis * 340.0
		var control := 4600.0 if axis != 0.0 else 3800.0
		player_vel.x = move_toward(player_vel.x, target_speed, control * FIXED_DT)
		if not player_grounded:
			player_vel.y += 2000.0 * FIXED_DT
		player_pos += player_vel * FIXED_DT
		if player_grounded:
			player_stamina = minf(100.0, player_stamina + 26.0 * FIXED_DT)
		if bool(input_state.get("shoot", false)) and player_fire_cd <= 0:
			_fire_shot()
	player_pos.x = clampf(player_pos.x, ARENA_LEFT, ARENA_RIGHT)
	if player_pos.y + 20.0 >= GROUND_Y:
		player_pos.y = GROUND_Y - 20.0
		player_vel.y = 0.0
		player_grounded = true
	else:
		player_grounded = false
	if player_pos.y < 48.0:
		player_pos.y = 48.0
		if player_vel.y < 0:
			player_vel.y = 0
	_check_graze_and_hits()

func _exit_ball() -> void:
	player_ball = false
	player_vel = Vector2.ZERO
	_spawn_burst(player_pos, CYAN, 6)

func _fire_shot() -> void:
	player_fire_cd = 9
	var aim := Vector2(player_facing, 0)
	var mouse := get_viewport().get_mouse_position() + Vector2(camera_x, 0)
	if mouse_seen or mouse.distance_to(player_pos) > 16.0:
		aim = (mouse - player_pos).normalized()
	if aim.length() < 0.1:
		aim = Vector2(player_facing, 0)
	shots.append({"pos": player_pos + aim * 22.0, "vel": aim * 900.0, "life": 1.5, "trail": []})
	_spawn_particle(player_pos + aim * 20.0, WHITE, 0.16, aim * 40.0, 3.0)
	player_facing = -1.0 if aim.x < 0.0 else 1.0

func _update_boss() -> void:
	boss_hit_flash = maxi(0, boss_hit_flash - 1)
	boss_attack_timer -= 1
	boss_move_timer -= 1
	if boss_move_timer <= 0:
		boss_move_timer = 90 if boss_id == "crimson" else 72
		var side := -1.0 if (frame / 90) % 2 == 0 else 1.0
		boss_target = Vector2(clampf(player_pos.x + side * 420.0, 1250.0, 2180.0), 170.0 + fmod(float(frame * 13), 230.0))
	if boss_pos.distance_to(boss_target) > 2.0:
		boss_pos = boss_pos.move_toward(boss_target, (22.0 if boss_id == "crimson" else 28.0) * FIXED_DT * 60.0)
	boss_pos.y += sin(float(frame) * 0.017 * 0.85) * 0.9
	if boss_attack_timer <= 0:
		boss_attack_timer = 78 if boss_id == "crimson" else 64
		_spawn_boss_pattern()
	if hellfire_timer > 0:
		hellfire_timer -= 1
		hellfire_tick -= 1
		if hellfire_tick <= 0:
			hellfire_tick = 20
			boss_hp = maxf(0.0, boss_hp - 6.0)
			_spawn_burst(boss_pos, RED, 8)
	if boss_hp <= 0.0:
		if boss_phase + 1 < boss_phase_count:
			boss_phase += 1
			boss_hp = boss_max_hp
			bullets.clear()
			warnings.clear()
			banner = "PHASE %d" % (boss_phase + 1)
			banner_timer = 85
			screen_shake = 10.0
			_spawn_mirror_shards(18, 1.0)
		else:
			mode = Mode.VICTORY
			banner = ""
			_spawn_burst(boss_pos, RED if boss_id == "crimson" else HAZARD, 58)
			_stop_music()

func _spawn_boss_pattern() -> void:
	var color := RED if boss_id == "crimson" else HAZARD
	var pattern := (boss_phase + int(frame / 80)) % (6 if boss_id == "crimson" else 7)
	var origin := boss_pos
	match pattern:
		0:
			for i in range(18):
				var a := TAU * float(i) / 18.0 + float(frame) * 0.01
				_spawn_bullet(origin, Vector2(cos(a), sin(a)) * 215.0, color, "hazard")
		1:
			for i in range(7):
				var a := lerpf(-0.95, 0.95, float(i) / 6.0)
				_spawn_bullet(origin, Vector2(-cos(a), sin(a)) * 300.0, color, "lance")
				_spawn_bullet(origin + Vector2(0, 24), Vector2(-cos(a), -sin(a)) * 300.0, color, "lance")
		2:
			for i in range(8):
				var a := float(i) * TAU / 8.0 + float(frame) * 0.02
				_spawn_bullet(origin, Vector2(cos(a), sin(a)) * 250.0, color, "homing")
		3:
			for i in range(12):
				var x := 1250.0 + float(i) * 82.0
				_spawn_bullet(Vector2(x, 50.0), Vector2(0, 300.0), color, "rain")
		4:
			for i in range(5):
				var a := -0.55 + float(i) * 0.27
				_spawn_bullet(origin, Vector2(-cos(a), sin(a)) * 420.0, color, "blade")
				_spawn_bullet(origin, Vector2(-cos(a), -sin(a)) * 420.0, color, "blade")
		5:
			warnings.append({"pos": origin, "angle": (player_pos - origin).angle(), "life": 0.65})
			for i in range(2):
				_spawn_bullet(origin, Vector2(-1, 0).rotated(0.10 if i == 0 else -0.10) * 520.0, color, "laser")

func _spawn_bullet(pos: Vector2, velocity: Vector2, color: Color, kind: String) -> void:
	bullets.append({"pos": pos, "vel": velocity, "life": 5.0, "color": color, "kind": kind, "angle": velocity.angle(), "grazed": false})

func _update_shots() -> void:
	for shot in shots:
		var pos: Vector2 = shot["pos"]
		var vel: Vector2 = shot["vel"]
		var to_boss := boss_pos - pos
		if mode == Mode.BATTLE and to_boss.length() < 280.0 and to_boss.length() > 0.1:
			var desired := to_boss.normalized()
			var current_angle := vel.angle()
			var target_angle := desired.angle()
			var turn := clampf(wrapf(target_angle - current_angle, -PI, PI), -3.4 * FIXED_DT, 3.4 * FIXED_DT)
			vel = vel.rotated(turn)
			shot["vel"] = vel
		shot["pos"] = pos + vel * FIXED_DT
		shot["life"] = float(shot["life"]) - FIXED_DT
		if mode == Mode.BATTLE and shot["pos"].distance_to(boss_pos) < 52.0:
			boss_hp = maxf(0.0, boss_hp - 3.0)
			boss_hit_flash = 8
			hitstop = 4
			screen_shake = maxf(screen_shake, 2.5)
			_spawn_burst(shot["pos"], RED, 5)
			shot["life"] = 0.0
	shots = shots.filter(func(shot): return float(shot.get("life", 0.0)) > 0.0 and shot["pos"].x > -80.0 and shot["pos"].x < WORLD_W + 80.0 and shot["pos"].y > 0.0 and shot["pos"].y < VIEW.y)

func _update_bullets() -> void:
	for warning in warnings:
		warning["life"] = float(warning["life"]) - FIXED_DT
	warnings = warnings.filter(func(w): return float(w.get("life", 0.0)) > 0.0)
	for bullet in bullets:
		bullet["pos"] += bullet["vel"] * FIXED_DT
		bullet["life"] = float(bullet["life"]) - FIXED_DT
		if bullet["kind"] == "homing" and bullet["life"] > 2.0:
			var desired: Vector2 = (player_pos - bullet["pos"]).normalized() * bullet["vel"].length()
			var diff := clampf(wrapf(desired.angle() - bullet["vel"].angle(), -PI, PI), -1.7 * FIXED_DT, 1.7 * FIXED_DT)
			bullet["vel"] = bullet["vel"].rotated(diff)
			bullet["angle"] = bullet["vel"].angle()
	bullets = bullets.filter(func(b): return float(b.get("life", 0.0)) > 0.0 and b["pos"].x > -140.0 and b["pos"].x < WORLD_W + 140.0 and b["pos"].y > -100.0 and b["pos"].y < VIEW.y + 100.0)

func _check_graze_and_hits() -> void:
	if mode != Mode.BATTLE or player_ball:
		return
	var center := player_pos + Vector2(0, -2)
	for bullet in bullets:
		var distance: float = bullet["pos"].distance_to(center)
		if not bool(bullet["grazed"]) and distance <= 30.0 and distance > 10.0:
			bullet["grazed"] = true
			player_graze_chain += 1
			player_graze_age = 80
			var multiplier := minf(3.0, 1.0 + floor(float(player_graze_chain) / 5.0) * 0.5)
			player_courage = minf(100.0, player_courage + multiplier)
			player_dash_cd = maxi(0, player_dash_cd - 2)
			_spawn_burst(center, WHITE, 4)
		if distance <= 10.0 and player_hurt_invuln <= 0 and player_dash_invuln <= 0:
			player_hp -= 1
			player_hurt_invuln = 70
			player_courage = maxf(0.0, player_courage - 18.0)
			player_graze_chain = 0
			player_graze_age = 0
			red_vignette = 18.0
			screen_shake = 9.0
			_spawn_burst(center, WHITE, 18)
			if player_hp <= 0:
				player_dying = true
				player_hp = 3
				player_pos = Vector2(350, GROUND_Y - 20)
				bullets.clear()
			return

func _use_red_skill() -> void:
	if player_courage < 100.0:
		return
	player_courage = 0.0
	if skill_red_tragedy:
		bullets.clear()
		boss_hp = maxf(0.0, boss_hp - 80.0)
		player_hurt_invuln = 200
		banner = "红之惨剧"
		banner_timer = 100
		screen_shake = 18.0
		_spawn_mirror_shards(42, 1.45)
	else:
		boss_hp = maxf(0.0, boss_hp - 36.0)
		player_hurt_invuln = 130
		banner = "冰封"
		banner_timer = 80
		_spawn_burst(player_pos, CYAN, 30)
	hitstop = 8

func _use_gunfire() -> void:
	if player_energy < 2:
		return
	player_energy -= 2
	var aim := (boss_pos - player_pos).normalized()
	if mouse_seen:
		aim = ((get_viewport().get_mouse_position() + Vector2(camera_x, 0)) - player_pos).normalized()
	var blast := player_pos + aim * 250.0
	boss_hp = maxf(0.0, boss_hp - 70.0)
	_spawn_burst(blast, RED, 42)
	_spawn_particle(blast, WHITE, 0.4, Vector2.ZERO, 30.0)
	banner = "枪火击溃"
	banner_timer = 55
	hitstop = 6

func _use_hellfire() -> void:
	if player_energy < 2:
		return
	player_energy -= 2
	hellfire_timer = 180
	hellfire_tick = 1
	banner = "业火"
	banner_timer = 55
	_spawn_burst(boss_pos, RED, 34)

func _update_camera() -> void:
	var target := clampf(player_pos.x - VIEW.x * 0.38, 0.0, WORLD_W - VIEW.x)
	var boss_left := minf(player_pos.x, boss_pos.x) - 160.0
	var boss_right := maxf(player_pos.x, boss_pos.x) + 160.0
	if boss_right - boss_left < VIEW.x:
		target = clampf((boss_left + boss_right) * 0.5 - VIEW.x * 0.5, 0.0, WORLD_W - VIEW.x)
	camera_x = lerpf(camera_x, target, 1.0 - pow(0.0001, FIXED_DT))

func _update_victory() -> void:
	if _just("confirm"):
		_start_story(boss_after)

func _update_end() -> void:
	if _just("confirm"):
		mode = Mode.TITLE
		_start_story("prologue")

func _update_fx() -> void:
	for item in particles:
		item["pos"] += item["vel"] * FIXED_DT
		item["vel"] *= pow(0.08, FIXED_DT)
		item["life"] = float(item["life"]) - FIXED_DT
	particles = particles.filter(func(item): return float(item.get("life", 0.0)) > 0.0)
	for shard in mirror_shards:
		shard["pos"] += shard["vel"] * FIXED_DT
		shard["rot"] = float(shard["rot"]) + float(shard["spin"]) * FIXED_DT
		shard["life"] = float(shard["life"]) - FIXED_DT
	mirror_shards = mirror_shards.filter(func(s): return float(s.get("life", 0.0)) > 0.0)
	red_vignette = maxf(0.0, red_vignette - 1.0)
	if banner_timer <= 0:
		banner = ""

func _spawn_particle(pos: Vector2, color: Color, life: float, vel := Vector2.ZERO, size := 4.0) -> void:
	particles.append({"pos": pos, "vel": vel, "life": life, "max": life, "color": color, "size": size})

func _spawn_burst(pos: Vector2, color: Color, count: int) -> void:
	for i in range(count):
		var angle := TAU * float(i) / maxf(1.0, float(count)) + randf_range(-0.18, 0.18)
		_spawn_particle(pos, color, randf_range(0.25, 0.7), Vector2(cos(angle), sin(angle)) * randf_range(45.0, 230.0), randf_range(2.0, 7.0))

func _spawn_mirror_shards(count: int, power: float) -> void:
	for i in range(count):
		var angle := TAU * float(i) / maxf(1.0, float(count)) + randf_range(-0.3, 0.3)
		mirror_shards.append({"pos": Vector2(640, 350), "vel": Vector2(cos(angle), sin(angle)) * randf_range(90.0, 280.0) * power, "rot": randf_range(0, TAU), "spin": randf_range(-4, 4), "life": randf_range(0.7, 1.4), "size": randf_range(8, 24)})

func _draw() -> void:
	var shake := Vector2.ZERO
	if screen_shake > 0.0:
		shake = Vector2(sin(float(frame) * 2.3) * screen_shake, cos(float(frame) * 1.7) * screen_shake * 0.6)
	draw_set_transform(shake, 0.0, Vector2.ONE)
	_draw_background()
	match mode:
		Mode.TITLE:
			_draw_title()
		Mode.STORY:
			_draw_story()
		Mode.WALK:
			_draw_walk()
		Mode.BATTLE:
			_draw_battle()
		Mode.VICTORY:
			_draw_battle()
			_draw_victory()
		Mode.END:
			_draw_end()
	_draw_fx_overlay()
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_background() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW), BLACK)
	var bg_tex: Texture2D = textures.get("mirror") if story_bg == "mirror" else textures.get("mirror_alt")
	if bg_tex:
		draw_texture_rect(bg_tex, Rect2(-camera_x * 0.25, 0, VIEW.x * 1.45, VIEW.y), false, Color(1, 1, 1, 0.42))
	for i in range(15):
		var y := float(i) * 46.0
		draw_line(Vector2(0, y), Vector2(VIEW.x, y), Color(1, 1, 1, 0.025), 1.0)
	for i in range(13):
		var x := float(i) * 118.0 - fmod(elapsed * 16.0, 118.0)
		draw_line(Vector2(x, 110), Vector2(x + 170, GROUND_Y), Color(CYAN, 0.075), 1.0)
		draw_line(Vector2(x + 80, 110), Vector2(x - 80, GROUND_Y), Color(CYAN, 0.04), 1.0)
	draw_line(Vector2(0, GROUND_Y), Vector2(VIEW.x, GROUND_Y), Color(CYAN, 0.28), 2.0)

func _draw_title() -> void:
	draw_string(ThemeDB.fallback_font, Vector2(386, 220), "M I R R O R", HORIZONTAL_ALIGNMENT_LEFT, -1, 70, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(520, 278), "镜", HORIZONTAL_ALIGNMENT_LEFT, -1, 46, CYAN)
	draw_line(Vector2(350, 310), Vector2(930, 310), Color(CYAN, 0.45), 2.0)
	draw_string(ThemeDB.fallback_font, Vector2(450, 400), "横版镜面 Boss Rush", HORIZONTAL_ALIGNMENT_LEFT, -1, 26, GREY)
	draw_string(ThemeDB.fallback_font, Vector2(460, 510), "按 ENTER / SPACE 开始", HORIZONTAL_ALIGNMENT_LEFT, -1, 30, RED)
	draw_string(ThemeDB.fallback_font, Vector2(414, 560), "A D 移动   SPACE 跳跃   SHIFT / K / 右键 冲刺   J / Z / 左键 射击", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, GREY)

func _draw_story() -> void:
	if story_cg:
		draw_texture_rect(story_cg, Rect2(0, 70, VIEW.x, 580), false, Color(1, 1, 1, 0.84))
	if story_cmd.get("t", "") != "card":
		_draw_portrait(story_left, Vector2(340, 520), 0.62, _portrait_speaking(story_left), false)
		_draw_portrait(story_right, Vector2(940, 520), 0.62, _portrait_speaking(story_right), true)
	# A scene can stay black during narration (the prologue reads a letter).
	# Fade the scenery and portraits before drawing text and continue prompts.
	if story_fade > 0:
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, story_fade))
	if story_cmd.get("t", "") == "card":
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.72))
		draw_string(ThemeDB.fallback_font, Vector2(390, 310), str(story_card[0]), HORIZONTAL_ALIGNMENT_LEFT, -1, 42, WHITE)
		draw_string(ThemeDB.fallback_font, Vector2(390, 365), str(story_card[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, 22, GREY)
	if story_intro != "":
		if story_cmd.get("t", "") == "bossIntro":
			_draw_boss_intro(story_intro)
		else:
			_draw_intro(story_intro)
	if story_title != "":
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.35))
		draw_string(ThemeDB.fallback_font, Vector2(440, 275), story_title, HORIZONTAL_ALIGNMENT_LEFT, -1, 38, RED if "猩红" in story_title else WHITE)
		if story_title_sub != "":
			draw_string(ThemeDB.fallback_font, Vector2(440, 320), story_title_sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, GREY)
	if story_cmd.get("t", "") == "say" or story_cmd.get("t", "") == "duel":
		draw_rect(Rect2(50, 520, 1180, 150), Color(0.02, 0.02, 0.02, 0.9))
		draw_line(Vector2(50, 520), Vector2(1230, 520), Color(RED if story_who == "rek" else CYAN, 0.8), 2.0)
		if story_who != "":
			draw_string(ThemeDB.fallback_font, Vector2(82, 555), _display_name(story_who), HORIZONTAL_ALIGNMENT_LEFT, -1, 22, RED if story_who == "rek" else CYAN)
		var shown := story_text.substr(0, int(story_reveal))
		draw_string(ThemeDB.fallback_font, Vector2(82, 605), shown, HORIZONTAL_ALIGNMENT_LEFT, 1110, 24, WHITE)
		draw_string(ThemeDB.fallback_font, Vector2(1000, 652), "ENTER / SPACE 继续    TAB 跳过", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, GREY)
	if story_flash > 0:
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(1, 1, 1, story_flash))

func _draw_portrait(id: String, center: Vector2, scale: float, active: bool, flipped: bool) -> void:
	if id == "":
		return
	var tex: Texture2D = _get_portrait_texture(id)
	if not tex:
		return
	var size := Vector2(tex.get_width(), tex.get_height()) * scale
	var tint := Color(1, 1, 1, 1.0 if active else 0.6)
	if flipped:
		draw_set_transform(center, 0.0, Vector2(-1, 1))
		draw_texture_rect(tex, Rect2(-size.x * 0.5, -size.y, size.x, size.y), false, tint)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	else:
		draw_texture_rect(tex, Rect2(center.x - size.x * 0.5, center.y - size.y, size.x, size.y), false, tint)
	if active:
		draw_circle(center + Vector2(0, -size.y * 0.56), size.x * 0.48, Color(CYAN if flipped else RED, 0.08))

func _get_portrait_texture(id: String) -> Texture2D:
	var cache_key := "portrait_" + id
	if textures.has(cache_key):
		return textures[cache_key]
	var path := "res://art/portrait/" + id + ".png"
	if FileAccess.file_exists(path):
		var tex = _load_texture(path)
		if tex is Texture2D:
			textures[cache_key] = tex
			return tex
	var base := id.split("_")[0]
	path = "res://art/portrait/" + _portrait_id(base, "") + ".png"
	var fallback = _load_texture(path) if FileAccess.file_exists(path) else null
	textures[cache_key] = fallback
	return fallback if fallback is Texture2D else null

func _draw_intro(id: String) -> void:
	var accent := RED if "crimson" in id or "rek" in id else CYAN
	draw_rect(Rect2(930, 120, 210, 360), Color(0.02, 0.02, 0.02, 0.88))
	draw_line(Vector2(930, 120), Vector2(930, 480), accent, 5.0)
	draw_string(ThemeDB.fallback_font, Vector2(980, 230), _display_name(id), HORIZONTAL_ALIGNMENT_LEFT, -1, 32, accent)
	draw_string(ThemeDB.fallback_font, Vector2(980, 280), "登场", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, GREY)

func _draw_boss_intro(id: String) -> void:
	var key := "cutin_crimson" if id == "crimson" or id == "rek_crimson" else "cutin_marysue"
	var tex: Texture2D = textures.get(key)
	if tex:
		var factor := minf(VIEW.x / tex.get_width(), VIEW.y / tex.get_height())
		var size := tex.get_size() * factor
		draw_texture_rect(tex, Rect2((VIEW - size) * 0.5, size), false)
	draw_string(ThemeDB.fallback_font, Vector2(430, 590), "BATTLE START", HORIZONTAL_ALIGNMENT_LEFT, -1, 42, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(470, 640), _display_name(id), HORIZONTAL_ALIGNMENT_LEFT, -1, 28, RED if key == "cutin_crimson" else HAZARD)

func _display_name(id: String) -> String:
	match id:
		"rek", "蕾克": return "蕾克"
		"crimson", "rek_crimson": return "猩红魔姬·雷帝"
		"marysue", "玛丽苏": return "玛丽苏"
		"norden", "诺登": return "诺登"
		"mabel", "梅贝尔": return "梅贝尔"
	return id

func _draw_walk() -> void:
	_draw_world_grid()
	for prop in walk_props:
		var kind := str(prop.get("kind", ""))
		var pos := Vector2(float(prop.get("x", 0.0)) - camera_x, GROUND_Y)
		if kind == "throne" and textures.get("throne"):
			var tex: Texture2D = textures["throne"]
			character_art.draw_ground(self, tex, pos, 320.0)
		elif kind == "mirror":
			_draw_mirror_gate(pos)
	if walk_target.size() > 0:
		var kind := str(walk_target.get("kind", ""))
		var p := Vector2(float(walk_target.get("x", 0.0)) - camera_x, GROUND_Y)
		if kind == "norden" or kind == "mabel":
			var tex: Texture2D = textures.get(kind)
			if tex:
				draw_texture_rect_region(tex, _npc_rect(kind, p), character_art.visible_bounds(tex), WHITE)
			draw_string(ThemeDB.fallback_font, p + Vector2(-52, -330), str(walk_target.get("label", "按 W 交互")), HORIZONTAL_ALIGNMENT_LEFT, -1, 16, WHITE)
		elif kind == "mirror":
			_draw_mirror_gate(p)
	_draw_dash_trail()
	_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)
	_draw_particles_world()
	draw_string(ThemeDB.fallback_font, Vector2(40, 48), "A / D 移动    SPACE 跳跃    SHIFT / K / 右键 冲刺    W 靠近并交互", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, WHITE)

func _npc_rect(id: String, foot: Vector2) -> Rect2:
	return character_art.ground_rect(textures.get(id), foot, 340.0 if id == "mabel" else 300.0)

func _draw_world_grid() -> void:
	draw_rect(Rect2(0, GROUND_Y + 2, VIEW.x, VIEW.y - GROUND_Y), Color(0.02, 0.02, 0.02, 1))
	for i in range(24):
		var x := float(i) * 120.0 - fmod(camera_x, 120.0)
		draw_line(Vector2(x, GROUND_Y), Vector2(x + 90, GROUND_Y - 185), Color(CYAN, 0.08), 1.0)

func _draw_mirror_gate(pos: Vector2) -> void:
	draw_rect(Rect2(pos.x - 74, pos.y - 260, 148, 260), Color(CYAN, 0.12))
	draw_rect(Rect2(pos.x - 62, pos.y - 248, 124, 236), Color(CYAN, 0.16), false, 3.0)
	draw_line(pos + Vector2(-45, -205), pos + Vector2(30, -135), Color(1, 1, 1, 0.7), 2.0)
	draw_line(pos + Vector2(30, -135), pos + Vector2(-8, -70), Color(1, 1, 1, 0.6), 2.0)

func _draw_battle() -> void:
	_draw_world_grid()
	_draw_boss_fx()
	_draw_projectiles()
	_draw_dash_trail()
	_draw_boss()
	_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)
	_draw_particles_world()
	_draw_hud()

func _draw_boss_fx() -> void:
	var center := boss_pos - Vector2(camera_x, 0)
	var color := RED if boss_id == "crimson" else HAZARD
	for ring in range(3):
		var radius := 112.0 + ring * 22.0 + sin(elapsed * 2.0 + ring) * 4.0
		draw_arc(center, radius, elapsed * (0.55 + ring * 0.13), elapsed * (0.55 + ring * 0.13) + PI * 1.45, 48, Color(color, 0.24 - ring * 0.04), 2.0)
		draw_arc(center, radius, elapsed * (0.55 + ring * 0.13) + PI, elapsed * (0.55 + ring * 0.13) + PI * 1.68, 48, Color(color, 0.15 - ring * 0.02), 2.0)

func _draw_boss() -> void:
	var center := boss_pos - Vector2(camera_x, 0)
	var key := ""
	if boss_id == "crimson":
		key = "crimson_%02d" % ((frame / 9 + boss_phase) % 4 + 1)
	else:
		key = "marysue_%02d" % ((frame / 18) % 3 + 1)
	var tex: Texture2D = textures.get(key)
	if tex:
		var tint := WHITE if boss_hit_flash == 0 or frame % 4 < 2 else Color(1, 1, 1, 0.4)
		var scale := 0.30 if boss_id == "crimson" else 0.28
		draw_texture_rect(tex, Rect2(center.x - tex.get_width() * scale * 0.5, center.y - tex.get_height() * scale * 0.5, tex.get_width() * scale, tex.get_height() * scale), false, tint)
	else:
		draw_circle(center, 48, Color(GREY, 0.9))
		draw_circle(center + Vector2(-16, -10), 7, RED if boss_id == "crimson" else HAZARD)
		draw_circle(center + Vector2(16, -10), 7, RED if boss_id == "crimson" else HAZARD)

func _draw_projectiles() -> void:
	for warning in warnings:
		var p: Vector2 = warning["pos"] - Vector2(camera_x, 0)
		var dir := Vector2(cos(warning["angle"]), sin(warning["angle"]))
		draw_line(p - dir * 700.0, p + dir * 700.0, Color(WHITE, 0.3), 2.0)
	for shot in shots:
		var p: Vector2 = shot["pos"] - Vector2(camera_x, 0)
		var d: Vector2 = shot["vel"].normalized()
		draw_line(p - d * 22.0, p + d * 9.0, Color(RED, 0.3), 8.0)
		draw_line(p - d * 12.0, p + d * 12.0, WHITE, 3.0)
		draw_circle(p, 5, RED)
	for bullet in bullets:
		var p: Vector2 = bullet["pos"] - Vector2(camera_x, 0)
		var color: Color = bullet["color"]
		var radius := 12.0 if bullet["kind"] == "laser" else 8.0
		var angle: float = bullet["angle"]
		var points := PackedVector2Array([Vector2(radius * 2.2, 0), Vector2(0, radius * 0.55), Vector2(-radius * 1.2, 0), Vector2(0, -radius * 0.55)])
		for i in range(points.size()):
			points[i] = p + points[i].rotated(angle)
		draw_colored_polygon(points, Color(color, 0.9))
		draw_line(p - Vector2(cos(angle), sin(angle)) * radius * 2.0, p, WHITE, 1.5)
		draw_circle(p, radius * 1.5, Color(color, 0.12))

func _draw_dash_trail() -> void:
	for item in trail:
		var pos: Vector2 = item["pos"] - Vector2(camera_x, 0)
		var alpha := clampf(float(item["life"]) / float(item["max"]), 0.0, 1.0) * 0.28
		_draw_player_at(pos, Color(1, 0, 0, alpha))

func _draw_player_at(pos: Vector2, tint: Color) -> void:
	var mirrored := player_facing < 0.0
	var body_color := Color(0.08, 0.08, 0.08, tint.a)
	var cape_color := Color(0.78, 0.02, 0.02, tint.a)
	if player_ball:
		var pulse := 1.0 + sin(float(frame) * 0.22) * 0.07
		var radius := 24.0 * pulse
		draw_circle(pos, radius * 2.6, Color(RED, 0.08))
		draw_circle(pos, radius * 1.5, Color(RED, 0.20))
		for i in range(3):
			var start := float(frame) * 0.12 + float(i) * TAU / 3.0
			draw_arc(pos, radius * 1.32, start, start + 0.85, 20, Color(CYAN, 0.72), 2.0)
		draw_circle(pos, radius * 0.5, Color(1, 1, 1, 0.92))
		return
	var state: String = character_art.player_state(player_dash_frames, player_dash_out, bool(input_state.get("shoot", false)))
	var aim := (get_viewport().get_mouse_position() - pos - Vector2(0, -80)).normalized() if mouse_seen else Vector2(player_facing, 0)
	if character_art.draw_player(self, textures, pos + Vector2(0, 20), player_facing, state, aim, tint):
		return
	draw_set_transform(pos, 0.0, Vector2(-1, 1) if mirrored else Vector2.ONE)
	draw_colored_polygon(PackedVector2Array([Vector2(-18, -18), Vector2(-68, 8), Vector2(-80, 52), Vector2(-8, 22)]), cape_color)
	draw_rect(Rect2(-16, -28, 32, 56), body_color)
	draw_circle(Vector2(0, -52), 24, Color(0.72, 0.72, 0.72, tint.a))
	draw_colored_polygon(PackedVector2Array([Vector2(-28, -67), Vector2(-18, -100), Vector2(-4, -76), Vector2(8, -76), Vector2(27, -100), Vector2(31, -61)]), RED)
	var mouse := get_viewport().get_mouse_position() + Vector2(camera_x, 0)
	var head_dir := (mouse - (pos + Vector2(0, -52))).normalized()
	if head_dir.length() < 0.2:
		head_dir = Vector2(player_facing, 0)
	draw_circle(Vector2(-10, -55) + head_dir * 3.0, 4, CYAN)
	draw_circle(Vector2(10, -55) + head_dir * 3.0, 4, CYAN)
	draw_line(Vector2(18, -22), Vector2(52, -4), Color(0.9, 0.9, 0.9, tint.a), 5.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_particles_world() -> void:
	for p in particles:
		var alpha := clampf(float(p["life"]) / float(p["max"]), 0.0, 1.0)
		draw_circle(p["pos"] - Vector2(camera_x, 0), float(p["size"]) * alpha, Color(p["color"], alpha))

func _draw_hud() -> void:
	var color := RED if boss_id == "crimson" else HAZARD
	draw_string(ThemeDB.fallback_font, Vector2(32, 36), "MIRROR // BATTLE", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, GREY)
	draw_string(ThemeDB.fallback_font, Vector2(910, 36), "猩红魔姬·雷帝" if boss_id == "crimson" else "黑童话之母·玛丽苏", HORIZONTAL_ALIGNMENT_LEFT, -1, 21, color)
	draw_rect(Rect2(820, 52, 400, 16), Color(0.08, 0.08, 0.08, 1))
	draw_rect(Rect2(820, 52, 400 * boss_hp / boss_max_hp, 16), color)
	var stage_label := "STAGE %d / %d" % [boss_phase + 1, boss_phase_count] if boss_id == "crimson" else "STAGE %d" % (boss_phase + 1)
	draw_string(ThemeDB.fallback_font, Vector2(820, 94), stage_label, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, GREY)
	draw_string(ThemeDB.fallback_font, Vector2(40, 650), "HP", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, GREY)
	for i in range(3):
		var heart := Vector2(78 + i * 26, 644)
		draw_colored_polygon(PackedVector2Array([heart + Vector2(0, 10), heart + Vector2(-9, -2), heart + Vector2(-6, -10), heart + Vector2(0, -5), heart + Vector2(6, -10), heart + Vector2(9, -2)]), RED if i < player_hp else Color(GREY, 0.25))
	draw_string(ThemeDB.fallback_font, Vector2(180, 650), "体力", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, GREY)
	draw_rect(Rect2(230, 638, 160, 12), Color(0.08, 0.08, 0.08, 1))
	draw_rect(Rect2(230, 638, 160 * player_stamina / 100.0, 12), CYAN)
	draw_string(ThemeDB.fallback_font, Vector2(410, 650), "勇气 %03d" % int(player_courage), HORIZONTAL_ALIGNMENT_LEFT, -1, 16, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(560, 650), "能量 %d/4" % player_energy, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, RED)
	draw_string(ThemeDB.fallback_font, Vector2(760, 650), "冲刺 %s" % ("READY" if player_dash_cd <= 0 else "%02d" % player_dash_cd), HORIZONTAL_ALIGNMENT_LEFT, -1, 16, RED if player_dash_cd <= 0 else GREY)
	draw_string(ThemeDB.fallback_font, Vector2(960, 650), "擦弹链 %d" % player_graze_chain, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, WHITE)
	if banner_timer > 0 and banner != "":
		draw_string(ThemeDB.fallback_font, Vector2(510, 340), banner, HORIZONTAL_ALIGNMENT_LEFT, -1, 34, WHITE)
	if paused:
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.55))
		draw_string(ThemeDB.fallback_font, Vector2(570, 360), "PAUSED", HORIZONTAL_ALIGNMENT_LEFT, -1, 36, WHITE)

func _draw_victory() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.46))
	draw_string(ThemeDB.fallback_font, Vector2(420, 300), "猩红魔姬 · 破" if boss_id == "crimson" else "镜界静默", HORIZONTAL_ALIGNMENT_LEFT, -1, 42, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(410, 370), "ENTER / SPACE 继续剧情", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, CYAN)

func _draw_end() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.5))
	draw_string(ThemeDB.fallback_font, Vector2(430, 300), "主线 · 终", HORIZONTAL_ALIGNMENT_LEFT, -1, 48, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(370, 370), "镜面碎成了千万片，每一片里都有她", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, CYAN)
	draw_string(ThemeDB.fallback_font, Vector2(450, 500), "ENTER / SPACE 重新开始", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, GREY)

func _draw_fx_overlay() -> void:
	for shard in mirror_shards:
		var p: Vector2 = shard["pos"]
		var size: float = shard["size"]
		var points := PackedVector2Array([p + Vector2(-size, -size * 0.4), p + Vector2(size * 0.6, -size), p + Vector2(size, size * 0.45), p + Vector2(-size * 0.5, size)])
		var transformed := PackedVector2Array()
		for point in points:
			transformed.append(p + (point - p).rotated(shard["rot"]))
		draw_colored_polygon(transformed, Color(WHITE, clampf(float(shard["life"]), 0.0, 1.0) * 0.32))
	if red_vignette > 0.0:
		var alpha := clampf(red_vignette / 18.0, 0.0, 1.0) * 0.34
		draw_rect(Rect2(0, 0, VIEW.x, 18), Color(RED, alpha))
		draw_rect(Rect2(0, VIEW.y - 18, VIEW.x, 18), Color(RED, alpha))
		draw_rect(Rect2(0, 0, 18, VIEW.y), Color(RED, alpha))
		draw_rect(Rect2(VIEW.x - 18, 0, 18, VIEW.y), Color(RED, alpha))
