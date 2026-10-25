extends Node2D

## MIRROR Godot vertical slice.
## The story is data driven from docs/story_export.json; combat keeps the
## browser prototype's fixed 60 Hz numbers and is drawn in this single scene
## so it remains easy to tune against the Web reference.

const CHAPTER_BATTLE_BGM := {
	"mirror_meet": "crimson_bgm",
	"final": "marysue_bgm"
}
const CHAPTER_BGM := {
	"prologue": "norden_bgm",
	"ambush": "marysue_world_bgm",
	"wake_talk": "norden_bgm",
	"enter_mirror": "mirrorworld_bgm",
	"mirror": "mirrorworld_bgm",
	"mirror_meet": "mirrorworld_bgm",
	"crimson_fall": "interlude_bgm",
	"final": "interlude_bgm"
}
const BATTLE_LEFT := 1500.0
const BATTLE_RIGHT := 2760.0
const BATTLE_HALF := 980.0
const PHASE_NAMES := {
	"crimson": ["壹 · 试锋", "贰 · 裂帛", "叁 · 血雨", "肆 · 镜刃", "伍 · 红之惨剧"],
	"marysue": ["壹 · 箱庭", "贰 · 反语", "叁 · 镜廊", "肆 · 断线", "伍 · 狂言", "陆 · 天地倒悬"]
}
const VIEW := Vector2(1280.0, 720.0)
const WORLD_W := 6400.0           # 用户要求：地图加长，初始看不到 NPC，要往右走才遇到
const WALK_SHIFT := 1200.0        # 走位段的 NPC/道具整体右移，避免一进图就看见
const GROUND_Y := 574.0
const ARENA_LEFT := 48.0
const ARENA_RIGHT := WORLD_W - 48.0
const ARENA_TOP := 48.0
# Player & Boss battle display heights (user spec 2026-10-25, wave 11)
const PLAYER_HEIGHT := 70.0   # Player displayed at 70px in battle
const BOSS_HEIGHT := 70.0     # Boss matches player height
# NPC map display heights (scaled proportionally: 70/100 ratio)
const NPC_NORDEN_HEIGHT := 110.0  # Was 120, now 120 × 70/100 ≈ 85
const NPC_MABEL_HEIGHT := 124.0   # Was 135, now 135 × 70/100 ≈ 95
# Ring animation: new circular rune (3.1 × character height = 3.1 × 70)
const RING_DISPLAY_DIAMETER := 217.0
const RED := Color("#ff0000")
const HAZARD := Color("#82ff00")
const CYAN := Color("#00baff")
const WHITE := Color("#f1f1f1")
const GREY := Color("#9a9a9a")
const BLACK := Color("#090909")
const BG := Color("#111111")
const FIXED_DT := 1.0 / 60.0
const DASH_STAMINA_COST := 40.0   # 用户要求：一次冲刺消耗 40 体力
const DASH_FRAMES := preload("res://godot/character_art.gd").DASH_FRAMES
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
var story_text_alpha := 0.45   # 台词淡入（0.45→1，10 帧，避免空白帧）
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
var story_chapter := ""
var map_bgm_player: AudioStreamPlayer
var mirror_bgm_player: AudioStreamPlayer
var norden_bgm_player: AudioStreamPlayer
var marysue_world_bgm_player: AudioStreamPlayer
var interlude_bgm_player: AudioStreamPlayer
var bgm_tracks: Dictionary = {}
var map_bgm_started := false
var intro_hold := 0.0      # 竖幅在下一句仍停留的秒数
var seen_speakers: Array = []  # 本章已登场过的角色（首次说话时弹称号）
var known_names: Array = ["rek", "norden", "mabel", "crimson", "rek_crimson"]  # 已自报姓名（玛丽苏靠 reveal）
var portrait_fade := 0.0      # 对话结束后立绘淡出（1 → 0）
var last_left := ""
var last_right := ""
var story_bg := "night"
var story_fade := 0.0
var story_fade_target := 0.0
var story_fade_speed := 0.0
var story_flash_seq: Array = []
var story_flash_index := 0
var story_flash_frames := 0
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
var ball_fx: Array = []            # 球形态粒子池
var ball_fx_tick := 0
var ball_trail_frames: Array = []   # 球形态拖尾 8 帧
var boss_anim: Dictionary = {}   # 魔姬动作帧: idle/move/thrust/slash
var intro_anim: Dictionary = {}  # 战前开场视频帧: crimson / marysue
var cutin_active := false
var cutin_timer := 0.0
var battle_intro_t := 0.0     # 开场动画剩余秒数
var whirls: Array = []        # 地面旋风 {x, phase}
var lock_timer := 0.0         # 锁定突刺计时
var lock_target := Vector2.ZERO
var lock_cooldown := 0
var lock_state := ""          # "", "aim", "spike"
var spikes: Array = []        # 突刺锋 {pos, life, max}
var green_flash_t := 0.0      # 半透明绿闪
var flash_green_t := 0.0      # 完全不透明绿幕遮挡
var mirror_flip := false      # 第六阶段：左右交换
var boss_hit_flash := 0
var boss_prev_pos := Vector2.ZERO
var boss_move_particle_tick := 0
var boss_ring_flash := 0  # Ring alpha flash state: 0 = steady 0.85, >0 = flashing
var boss_skill_name := ""
# Boss movement state machine
enum BossState { IDLE, REPOSITION, TELEGRAPH, LUNGE }
var boss_state := BossState.IDLE
var boss_state_timer := 0
var boss_reposition_target := Vector2.ZERO
var boss_lunge_start := Vector2.ZERO
var boss_lunge_return := Vector2.ZERO
# Boss special skill state
var boss_skill_state := ""  # "telegraph", "firing", "cooldown"
var boss_skill_timer := 0
var boss_skill_subframe := 0
var boss_rush_side := 1.0
var boss_slide_to := -1.0  # Frame counter within current skill phase
var bullets: Array = []
var shots: Array = []
var warnings: Array = []
var skill_warnings: Array = []  # Visual telegraph lines/circles for special skills
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
var player_move_facing := 1.0
var player_dash_direction := 1.0
var player_dash_buffer_direction := 1.0
var player_hp := 5
const PLAYER_MAX_HP := 5
var player_stamina := 100.0
var player_stamina_display := 100.0  # Smooth lerp display value for stamina bar
var player_courage := 0.0
var player_energy: float = 4.0
const ENERGY_MAX := 4.0
const ENERGY_PER_GRAZE := 0.45   # 擦弹回复能量
const ENERGY_PER_HIT := 0.16     # 子弹命中回复能量（明显可见）
var energy_flash := 0            # 能量满/消耗时的闪动
var hurt_vignette := 0
var ball_hint_t := 0.0
var tutorial_timer := 0.0
var death_timer := 0.0
var death_shards: Array = []
var death_flash := 0.0
var death_reason := ""
var battle_start_pos := Vector2(500.0, 500.0)
var tutorial_shown := false
var boss_bgm_pending := false
var battle_cmd_index := -1
var battle_cmd_boss := ""
var battle_bgm_started := false
var tragedy_buff_t := 0.0
var battle_bgm_player: AudioStreamPlayer
var fx_rings: Array = []         # 冲击环 {pos, r, max, life, color, width}
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
var sfx_player: Node  # SFX player pool

# Dash FX state
var dash_fx_active := false
var dash_speed_lines: Array = []  # { pos, vel, life, max_life, width }
var dash_dots: Array = []          # { pos, vel, life, max_life, radius, color }
var dash_screen_fx := 0           # Screen edge flash countdown (4 frames)
var graze_this_frame := false     # Deduplication flag for graze SFX

# Walk dust state
var walk_dust: Array = []  # { pos, vel, life, max_life, alpha }
var walk_dust_timer := 0

# Jump squash state
var jump_squash := Vector2.ONE  # (x_scale, y_scale) for player visual
var jump_squash_timer := 0

# NPC interaction glow state
var npc_glow_alpha := 0.0  # Current glow alpha [0..1]
var npc_glow_target := 0.0 # Target alpha (0 outside, 1 inside range)
var last_land_frame := -999  # Frame of last land SFX to enforce min interval

# Debug flag for testing: when true, draw only player on black background
var debug_player_only := false

func _ready() -> void:
	_setup_window_stretch()
	map_bgm_player = AudioStreamPlayer.new()
	map_bgm_player.bus = "Master"
	map_bgm_player.volume_db = -10.0
	add_child(map_bgm_player)
	if ResourceLoader.exists("res://audio/map_bgm.ogg"):
		map_bgm_player.stream = load("res://audio/map_bgm.ogg")
	mirror_bgm_player = AudioStreamPlayer.new()
	mirror_bgm_player.bus = "Master"
	mirror_bgm_player.volume_db = -12.0
	add_child(mirror_bgm_player)
	# BGM 池：id -> player（统一加载/循环）
	for spec in [["norden_bgm", -12.0], ["mirrorworld_bgm", -12.0],
			["marysue_world_bgm", -12.0], ["interlude_bgm", -12.0], ["map_bgm", -12.0]]:
		var track_id := str(spec[0])
		var path := "res://audio/%s.ogg" % track_id
		if not ResourceLoader.exists(path):
			continue
		var pl := AudioStreamPlayer.new()
		pl.bus = "Master"
		pl.volume_db = float(spec[1])
		add_child(pl)
		var st: AudioStream = load(path)
		if st is AudioStreamOggVorbis:
			st.loop = true
		pl.stream = st
		bgm_tracks[track_id] = pl
	norden_bgm_player = AudioStreamPlayer.new()
	norden_bgm_player.bus = "Master"
	norden_bgm_player.volume_db = -12.0
	add_child(norden_bgm_player)
	if ResourceLoader.exists("res://audio/norden_bgm.ogg"):
		var ns: AudioStream = load("res://audio/norden_bgm.ogg")
		if ns is AudioStreamOggVorbis:
			ns.loop = true
		norden_bgm_player.stream = ns
	if ResourceLoader.exists("res://audio/mirrorworld_bgm.ogg"):
		var ms: AudioStream = load("res://audio/mirrorworld_bgm.ogg")
		if ms is AudioStreamOggVorbis:
			ms.loop = true
		mirror_bgm_player.stream = ms

	_load_assets()
	_load_story()
	music_player = AudioStreamPlayer.new()
	music_player.name = "BattleMusic"
	add_child(music_player)
	sfx_player = preload("res://godot/sfx_player.gd").new()
	sfx_player.name = "SFXPlayer"
	add_child(sfx_player)
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
		"bg_forest": "res://art/bg/bg_forest.png",
		"bg_mirrorworld": "res://art/bg/bg_mirrorworld.png",
		"mirror_alt": "res://art/bg/mirror_alt.jpg",
		"throne": "res://art/obj/throne.png",
		"throne_new": "res://art/obj/throne_new.png",
		"mirror_stand": "res://art/obj/mirror_stand.png",
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
		"cutin_marysue": "res://art/cg/cutin_marysue.png",
		"logo_hongzhijing": "res://art/logo/hongzhijing_logo.png",
		"skill_icon_red": "res://art/ui/skill_red_tragedy.png",
		"bullet_blade": "res://art/fx/bullets/bullet_blade.png",
		"bullet_orb": "res://art/fx/bullets/bullet_orb.png",
		"bullet_laser": "res://art/fx/bullets/bullet_laser.png",
		"bullet_rain": "res://art/fx/bullets/bullet_rain.png",
		"bullet_flame": "res://art/fx/bullets/flame_bullet.png",
		"bullet_crescent": "res://art/fx/bullets/crescent.png",
		"bullet_yinyang": "res://art/fx/bullets/yinyang_orb.png",
		"bullet_talisman": "res://art/fx/bullets/talisman.png",
		"bullet_beam": "res://art/fx/bullets/beam_pillar.png",
		"bullet_talisman_green": "res://art/fx/bullets/talisman_green.png",
		"bullet_yinyang_green": "res://art/fx/bullets/yinyang_orb_green.png",
		"bullet_beam_green": "res://art/fx/bullets/beam_pillar_green.png",
		"bullet_crescent_green": "res://art/fx/bullets/crescent_green.png",
		"skill_icon_gun": "res://art/ui/skill_gunfire.png",
		"skill_icon_hell": "res://art/ui/skill_hellfire.png"
	}
	for key in paths:
		var tex = _load_texture(paths[key])
		if tex is Texture2D:
			textures[key] = tex
	
	# Load new circular rune magic arrays (single frame each)
	for ring_dir in ["scarlet", "marysue"]:
		var ring_path := "res://art/battle/%s/ring2/circle.png" % ring_dir
		var ring_key := "ring_circle_%s" % ring_dir
		var ring_tex := _load_texture(ring_path)
		if ring_tex:
			textures[ring_key] = ring_tex

	# 球形态拖尾帧（用户提供素材）
	ball_trail_frames.clear()
	for fi in range(8):
		var btex := _load_texture("res://art/fx/ball_trail/frame_%02d.png" % fi)
		if btex:
			ball_trail_frames.append(btex)
	# 战前开场动画帧（即梦 mp4 抽帧，24 帧）
	for who in ["crimson", "marysue"]:
		var iframes: Array = []
		for fi in range(24):
			var itex := _load_texture("res://art/cg/intro_%s/frame_%02d.png" % [who, fi])
			if itex:
				iframes.append(itex)
		if iframes.size() > 0:
			intro_anim[who] = iframes
	# 猩红魔姬动作序列（来自即梦视频，每套 16 帧）
	boss_anim.clear()
	for anim_name in ["idle", "move", "thrust", "slash"]:
		var frames: Array = []
		for fi in range(16):
			var ftex := _load_texture("res://art/battle/scarlet/anim/%s/frame_%02d.png" % [anim_name, fi])
			if ftex:
				frames.append(ftex)
		if frames.size() > 0:
			boss_anim[anim_name] = frames
	var ms_frames: Array = []
	for fi in range(16):
		var mtex := _load_texture("res://art/battle/marysue/anim/idle/frame_%02d.png" % fi)
		if mtex:
			ms_frames.append(mtex)
	if ms_frames.size() > 0:
		boss_anim["marysue_idle"] = ms_frames

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
	_decay_shake()

	frame += 1
	elapsed += FIXED_DT
	input_state = _read_inputs()
	if _just("mute"):
		if music_player:
			music_player.volume_db = -80.0 if music_player.volume_db > -40.0 else -4.0
	if _just("pause") and mode == Mode.BATTLE:
		paused = not paused
	if paused and (_just("confirm") or _just("shoot")):
		paused = false
	if tutorial_timer > 0.0:
		tutorial_timer = maxf(0.0, tutorial_timer - FIXED_DT)
		if _just("confirm") or _just("skip") or _just("shoot"):
			tutorial_timer = 0.0
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
		"skill": Input.is_key_pressed(KEY_E),
		"gunfire": Input.is_key_pressed(KEY_C),
		"hellfire": Input.is_key_pressed(KEY_V),
		"confirm": Input.is_key_pressed(KEY_ENTER) or Input.is_key_pressed(KEY_SPACE) or Input.is_key_pressed(KEY_W) or Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT),
		"skip": Input.is_key_pressed(KEY_TAB),
		"pause": Input.is_key_pressed(KEY_P) or Input.is_key_pressed(KEY_ESCAPE),
		"restart": Input.is_key_pressed(KEY_R),
		"mute": Input.is_key_pressed(KEY_M)
	}

func _just(action: String) -> bool:
	return bool(input_state.get(action, false)) and not bool(previous_input.get(action, false))

func _update_title() -> void:
	if _just("confirm"):
		_start_story("prologue")

func _start_story(id: String) -> void:
	seen_speakers.clear()
	# 换章时清空对话立绘（否则上一章角色会残留）
	story_left = ""
	story_right = ""
	last_left = ""
	last_right = ""
	portrait_fade = 0.0
	_stop_battle_bgm()
	# 预计算本章战斗命令位置（用于提前 2 句起战斗 BGM）
	battle_cmd_index = -1
	battle_cmd_boss = ""
	var cmds: Array = story_data.get(id, {}).get("cmds", [])
	for i in range(cmds.size()):
		if str(cmds[i].get("t", "")) == "battle":
			battle_cmd_index = i
			battle_cmd_boss = str(cmds[i].get("boss", "crimson"))
			break
	story_chapter = id
	var want_bgm := _chapter_bgm(id)
	if want_bgm != "":
		_play_bgm(want_bgm)
	if not story_data.has(id):
		mode = Mode.END
		return
	# Mirror shards transition on chapter change (story → story)
	if mode == Mode.STORY and id != chapter_id:
		_spawn_mirror_shards(18, 0.75)
	
	chapter_id = id
	story_commands = Array(story_data[id].get("cmds", []))
	story_index = 0
	story_cmd = {}
	story_text = ""
	story_reveal = 0.0
	story_flash_seq.clear()
	mode = Mode.STORY
	_story_advance()

func _story_advance() -> void:
	var guard := 0
	while guard < 32 and story_index < story_commands.size():
		guard += 1
		var command: Dictionary = story_commands[story_index]
		story_index += 1
		var kind := str(command.get("t", ""))
		# 战斗 BGM 提前两句话进（用户要求）
		if battle_cmd_index >= 0 and not battle_bgm_started and story_index >= battle_cmd_index - 4:
			battle_bgm_started = true
			_start_battle_bgm_for(battle_cmd_boss)
		story_cmd = command
		story_title = ""
		story_title_sub = ""
		story_intro = ""
		if kind != "cg":
			story_cg = null
		if kind != "flash":
			story_flash_seq.clear()
		if kind != "card":
			story_card = ["", ""]
		match kind:
			"scene":
				story_bg = str(command.get("bg", story_bg))
				if bool(command.get("clear", false)):
					story_left = ""
					story_right = ""
					story_left_expr = ""
					story_right_expr = ""
				camera_x = 0.0
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
					banner = "习得技能「红之惨剧」"
					banner_timer = 150
				continue
			"battle":
				_start_battle(str(command.get("boss", "crimson")), str(command.get("after", "ending")))
				return
			"walk":
				_start_walk(command, true)
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
			"sfx":
				sfx_player.play(str(command.get("name", "")))
				return
			"reveal":
				var rw := str(command.get("who", ""))
				var rkey := _portrait_base(rw)
				if rkey != "" and not known_names.has(rkey):
					known_names.append(rkey)
				story_intro = rkey
				intro_hold = 3.2
				story_timer = 0.6
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
				story_fade_speed = 1.0 / maxf(FIXED_DT, story_timer)
				if story_timer <= FIXED_DT:
					story_fade = story_fade_target
					story_timer = 0.0
					continue
				return
			"flash":
				story_flash_seq = Array(command.get("seq", [])).duplicate()
				story_flash_index = 0
				if story_flash_seq.is_empty():
					continue
				story_flash_frames = maxi(1, int(story_flash_seq[0].get("f", 1)))
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
				var path := "res://" + art_path
				story_cg = _load_texture(path) if art_path != "" and FileAccess.file_exists(path) else null
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
	story_text_alpha = 0.0
	if story_who != "":
		_set_portrait(story_who, story_expr)
		var speaker_key := _portrait_base(story_who)
		if not seen_speakers.has(speaker_key) and CHAR_TITLES.has(speaker_key):
			seen_speakers.append(speaker_key)
			story_intro = speaker_key
			intro_hold = 3.2
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
	var locked: bool = bool(story_cmd.get("locked", false)) or story_cmd.get("t", "") == "flash"
	if _just("skip") and not locked:
		while story_index < story_commands.size():
			var skip_kind := str(story_commands[story_index].get("t", ""))
			story_index += 1
			if skip_kind == "battle" or skip_kind == "walk":
				story_cmd = story_commands[story_index - 1]
				if skip_kind == "battle":
					_start_battle(str(story_cmd.get("boss", "crimson")), str(story_cmd.get("after", "ending")))
				else:
					_start_walk(story_cmd, true)
				return
		if story_index >= story_commands.size():
			mode = Mode.END
			return
	if story_cmd.get("t", "") == "say" or story_cmd.get("t", "") == "duel":
		story_text_alpha = minf(1.0, story_text_alpha + 1.0 / 10.0)
		story_reveal = minf(float(story_text.length()), story_reveal + 1.9)
		if _just("confirm"):
			if story_reveal < story_text.length():
				story_reveal = float(story_text.length())
			else:
				_story_advance()
		return
	if not story_flash_seq.is_empty():
		story_flash_frames -= 1
		if story_flash_frames <= 0:
			story_flash_index += 1
			if story_flash_index >= story_flash_seq.size():
				story_flash_seq.clear()
				_story_advance()
			else:
				story_flash_frames = maxi(1, int(story_flash_seq[story_flash_index].get("f", 1)))
		return
	if story_timer > 0.0:
		story_timer -= FIXED_DT
	if story_fade != story_fade_target:
		story_fade = move_toward(story_fade, story_fade_target, story_fade_speed * FIXED_DT)
	if _just("confirm") and story_timer > 0.0 and not locked:
		story_timer = 0.0
	if story_timer <= 0.0 and absf(story_fade - story_fade_target) < 0.02:
		_story_advance()

func _flash_color() -> Color:
	if story_flash_seq.is_empty():
		return Color.TRANSPARENT
	match str(story_flash_seq[story_flash_index].get("c", "white")):
		"black": return Color.BLACK
		"green": return HAZARD
		_: return Color.WHITE

func _finish_walk() -> void:
	var next := walk_next
	walk_target = {}
	walk_props.clear()
	walk_next = ""
	if next != "":
		_start_story(next)
	else:
		mode = Mode.TITLE

func _start_walk(command: Dictionary, long_map: bool = false) -> void:
	last_left = ""
	last_right = ""
	portrait_fade = 0.0
	var walk_bgm := _chapter_bgm(story_chapter)
	if walk_bgm == "":
		walk_bgm = "norden_bgm" if story_bg == "forest" else "mirrorworld_bgm"
	_play_bgm(walk_bgm)
	ball_hint_t = 6.0
	# Mirror shards transition (from any mode → walk)
	if mode != Mode.WALK:
		_spawn_mirror_shards(20, 0.8)
	
	mode = Mode.WALK
	paused = false
	walk_next = str(command.get("next", ""))
	walk_until = float(command.get("untilX", -1.0))
	var player_x = command.get("playerX", 180.0)
	player_pos = Vector2(float(player_x), GROUND_Y - 20.0)
	player_vel = Vector2.ZERO
	player_grounded = true
	player_facing = 1.0
	player_move_facing = 1.0
	player_dash_direction = 1.0
	player_dash_buffer_direction = 1.0
	player_ball = false
	player_dash_frames = 0
	player_dash_buffer = 0
	player_dash_ramp = 0
	player_dash_out = 0
	player_dash_cd = 0
	player_dash_invuln = 0
	player_jump_buffer = 0
	player_stamina = 100.0
	player_stamina_display = 100.0
	bullets.clear()
	warnings.clear()
	shots.clear()
	trail.clear()
	particles.clear()
	walk_dust.clear()
	walk_target = (command.get("target", {}) as Dictionary).duplicate(true)
	walk_props = (command.get("props", []) as Array).duplicate(true)
	# 地图加长：走位段的 NPC/道具整体右移，玩家要先往右走才会遇到
	if long_map:
		if walk_target.has("x"):
			walk_target["x"] = float(walk_target["x"]) + WALK_SHIFT
		# 镜子/交互物必须在玩家前方，否则玩家会以为"没东西可交互"（用户反馈）
		if str(walk_target.get("kind", "")) == "mirror" and float(walk_target.get("x", 0.0)) < player_pos.x + 400.0:
			walk_target["x"] = player_pos.x + 700.0
		for prop in walk_props:
			if prop is Dictionary and prop.has("x"):
				prop["x"] = float(prop["x"]) + WALK_SHIFT
	walk_camera = bool(command.get("cam", true))   # 走位段默认跟随小红帽
	if command.has("bg"):
		story_bg = str(command.get("bg", story_bg))
	# 起始就把镜头对齐到玩家，避免先跳到地图最左再滑过来
	if walk_camera:
		camera_x = clampf(player_pos.x - VIEW.x * 0.38, 0.0, WORLD_W - VIEW.x)
	else:
		camera_x = 0.0

func _update_walk() -> void:
	if portrait_fade > 0.0:
		portrait_fade = maxf(0.0, portrait_fade - 1.0 / 18.0)
	_update_player()
	_update_ball_fx()
	_update_shots()
	if not tutorial_shown and mode == Mode.WALK and story_chapter != "":
		tutorial_shown = true
		tutorial_timer = 20.0
	_update_npc_glow()
	if walk_camera:
		var cam_target := clampf(player_pos.x - VIEW.x * 0.38, 0.0, WORLD_W - VIEW.x)
		camera_x = lerpf(camera_x, cam_target, 1.0 - pow(0.0004, FIXED_DT))
	if walk_target.size() > 0:
		var target_x := float(walk_target.get("x", player_pos.x))
		if _just("confirm") and absf(player_pos.x - target_x) < 110.0:
			_finish_walk()
			return
	if walk_until >= 0.0 and player_pos.x >= walk_until:
		_finish_walk()

func _start_battle(id: String, after: String) -> void:
	# Mirror shards transition (from any mode → battle)
	if mode != Mode.BATTLE:
		_spawn_mirror_shards(20, 0.9)
	
	mode = Mode.BATTLE
	_stop_map_bgm()
	_stop_mirror_bgm()
	battle_intro_t = 2.6
	boss_bgm_pending = true
	battle_bgm_started = true
	cutin_active = false
	cutin_timer = 0.0
	whirls.clear()
	spikes.clear()
	lock_state = ""
	lock_timer = 0.0
	green_flash_t = 0.0
	mirror_flip = false
	boss_id = id
	boss_after = after
	boss_max_hp = 240.0 if id == "crimson" else 420.0
	boss_hp = boss_max_hp
	boss_phase = 0
	boss_phase_count = 5 if id == "crimson" else 6
	boss_pos = Vector2(2280.0, 226.0)
	boss_target = boss_pos
	boss_attack_timer = 45 if id == "crimson" else 30
	boss_move_timer = 0
	boss_hit_flash = 0
	boss_ring_flash = 0
	boss_skill_name = "猩红裁决" if id == "crimson" else "黑童话·终章"
	boss_state = BossState.IDLE
	boss_state_timer = 0
	boss_reposition_target = boss_pos
	boss_lunge_start = Vector2.ZERO
	boss_lunge_return = Vector2.ZERO
	boss_skill_state = ""
	boss_skill_timer = 0
	boss_skill_subframe = 0
	bullets.clear()
	warnings.clear()
	skill_warnings.clear()
	shots.clear()
	particles.clear()
	trail.clear()
	walk_dust.clear()
	mirror_shards.clear()
	player_pos = Vector2(350.0, GROUND_Y - 20.0)
	player_vel = Vector2.ZERO
	player_grounded = true
	player_hp = PLAYER_MAX_HP
	player_facing = 1.0
	player_move_facing = 1.0
	player_dash_direction = 1.0
	player_dash_buffer_direction = 1.0
	player_stamina = 100.0
	player_stamina_display = 100.0
	player_courage = 0.0
	player_energy = 0.0   # 从 0 起，方便看到擦弹/命中回复
	battle_start_pos = player_pos
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
	# Smooth lerp stamina display value for UI
	player_stamina_display = lerpf(player_stamina_display, player_stamina, 0.18)
	for item in trail:
		item["life"] = float(item.get("life", 0.0)) - FIXED_DT
	trail = trail.filter(func(item): return float(item.get("life", 0.0)) > 0.0)
	var axis := float(int(input_state.get("right", false)) - int(input_state.get("left", false)))
	var vertical := float(int(input_state.get("down", false)) - int(input_state.get("up", false)))
	if axis != 0.0:
		player_move_facing = signf(axis)
	if player_dash_frames > 0 or player_dash_out > 0:
		player_facing = player_dash_direction
	else:
		player_facing = player_move_facing
	if _just("jump"):
		player_jump_buffer = 8
	var dash_pressed := _just("dash")
	if player_ball:
		player_stamina = maxf(0.0, player_stamina - 32.0 * FIXED_DT)  # Ball form continuous drain: 32 stamina/s (Web規格)
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
			player_pos.y = clampf(player_pos.y, 48.0, GROUND_Y - 20.0)
			if frame % 2 == 0:
				_spawn_particle(player_pos - player_vel.normalized() * 18.0, Color(1, 0.22, 0.22, 0.9), 0.45, -player_vel.normalized() * 70.0, 5.0)
			_check_graze_and_hits()
			return
	if dash_pressed and not player_grounded and bool(input_state.get("up", false)) and player_stamina > 20.0:
		player_ball = true
		player_dash_frames = 0
		player_dash_out = 0
		player_dash_buffer = 0
		player_stamina = maxf(0.0, player_stamina - BALL_ENTRY_STAMINA_COST)  # Ball entry cost: 7 stamina
		player_vel.x *= 0.4
		player_vel.y = -450.0
		player_ball_launch = 5
		_spawn_burst(player_pos, RED, 14)
		return
	elif dash_pressed and not player_grounded and bool(input_state.get("up", false)) and player_stamina <= 20.0:
		# Insufficient stamina for ball form feedback
		banner = "体力不足"
		banner_timer = 20
	if dash_pressed:
		player_dash_buffer = 8
		player_dash_buffer_direction = player_move_facing
	if player_dash_buffer > 0:
		if player_dash_cd <= 0 and player_dash_frames == 0 and player_dash_out == 0 and player_stamina >= DASH_STAMINA_COST:
			player_stamina -= DASH_STAMINA_COST  # Dash cost: 3 stamina
			player_dash_buffer = 0
			player_dash_direction = signf(axis) if axis != 0.0 else player_dash_buffer_direction
			player_facing = player_dash_direction
			player_dash_frames = DASH_FRAMES
			player_dash_ramp = 3
			player_dash_cd = DASH_FRAMES + 16  # Dash CD: 20 frames dash + 16 frames cooldown
			player_dash_invuln = maxi(DASH_FRAMES + 4, 12)  # 冲刺无敌：至少 0.2 秒（12 帧）
			_spawn_burst(player_pos, RED, 8)
			_start_dash_fx()
		elif player_dash_cd <= 0 and player_stamina < DASH_STAMINA_COST:
			# Insufficient stamina feedback: brief red flash
			player_dash_buffer = 0
			banner = "体力不足"
			banner_timer = 20
		else:
			player_dash_buffer -= 1
	if player_dash_frames > 0:
		player_dash_frames -= 1
		var ramp := 1.0
		if player_dash_ramp > 0:
			var progress := 1.0 - float(player_dash_ramp) / 3.0
			ramp = 0.45 + 0.55 * (1.0 - pow(1.0 - progress, 2.0))
			player_dash_ramp -= 1
		player_vel = Vector2(player_dash_direction * 1020.0 * ramp, 0)
		player_pos += player_vel * FIXED_DT
		trail.append({"pos": player_pos, "life": 0.2, "max": 0.2, "facing": player_dash_direction, "state": character_art.player_state(player_dash_frames, 1, false)})
		if trail.size() > 12:
			trail.pop_front()
		if player_dash_frames == 0:
			player_dash_out = 6
	elif player_dash_out > 0:
		player_dash_out -= 1
		player_vel.x = lerpf(player_vel.x, player_dash_direction * 340.0, 0.28)
		player_pos += player_vel * FIXED_DT
	else:
		if player_grounded and player_jump_buffer > 0:
			player_vel.y = -700.0
			player_grounded = false
			player_jump_buffer = 0
			_trigger_jump_squash("jump")
		var target_speed := axis * 510.0   # 用户要求：左右移速 ×1.5
		var control := 4600.0 if axis != 0.0 else 3800.0
		player_vel.x = move_toward(player_vel.x, target_speed, control * FIXED_DT)
		if not player_grounded:
			player_vel.y += 2000.0 * FIXED_DT
		player_pos += player_vel * FIXED_DT
		if player_grounded:
			player_stamina = minf(100.0, player_stamina + 78.0 * FIXED_DT)   # 体力回复 ×1.5  # Ground stamina recovery: +26 stamina/s (允许连续冲刺)
			# Walk dust (grounded, moving)
			if absf(player_vel.x) > 80.0:
				walk_dust_timer -= 1
				if walk_dust_timer <= 0:
					walk_dust_timer = randi_range(6, 10)
					_spawn_walk_dust()
		if bool(input_state.get("shoot", false)) and player_fire_cd <= 0:
			_fire_shot()
	if mode == Mode.BATTLE and player_hp <= 0 and death_timer <= 0.0:
		_start_death()
	if mode == Mode.BATTLE:
		player_pos.x = clampf(player_pos.x, _battle_left(), _battle_right())
	else:
		player_pos.x = clampf(player_pos.x, ARENA_LEFT, ARENA_RIGHT)
	var was_grounded := player_grounded
	if player_pos.y + 20.0 >= GROUND_Y:
		player_pos.y = GROUND_Y - 20.0
		player_vel.y = 0.0
		player_grounded = true
		if not was_grounded:
			_trigger_land()
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
	_spawn_burst(player_pos, Color(1, 0.3, 0.3), 6)

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
	boss_ring_flash = maxi(0, boss_ring_flash - 1)
	boss_attack_timer -= 1
	boss_state_timer -= 1
	
	# State machine: IDLE (float+drift) → REPOSITION (smooth move) → TELEGRAPH (charge hover) → LUNGE (dash+return)
	match boss_state:
		BossState.IDLE:
			# Enhanced idle: vertical sin wave + slow horizontal drift
			var base_y := 226.0
			boss_pos.y = base_y + sin(float(frame) * 0.017 * 0.85) * 22.0
			# Slow horizontal drift (sine wave, ~80 pixel range, ~4s period)
			var drift_x := sin(float(frame) * 0.017 * 0.5) * 40.0
			boss_pos.x += drift_x * 0.016  # Accumulate drift slowly
			# Clamp to arena bounds
			# 不再硬钳制（会瞬移），改用平滑滑回战场内
			var bx_min := _battle_left() + 140.0
			var bx_max := _battle_right() - 140.0
			if boss_pos.x < bx_min:
				boss_pos.x = move_toward(boss_pos.x, bx_min, 420.0 * FIXED_DT)
			elif boss_pos.x > bx_max:
				boss_pos.x = move_toward(boss_pos.x, bx_max, 420.0 * FIXED_DT)
			
			# Phase 2+: add orbiting drift (sin x + cos y overlapping)
			if boss_phase >= 2:
				var orbit_phase := float(frame) * 0.017 * 0.65
				boss_pos.x += cos(orbit_phase) * 0.8
				boss_pos.y += sin(orbit_phase * 1.3) * 0.6
			
			# Trigger reposition: more frequent in higher phases
			var reposition_interval := 150 - boss_phase * 15  # 150/135/120/105/90... frames
			if boss_state_timer <= 0:
				boss_state_timer = reposition_interval
				# Pick a horizontal position offset from player (not instant teleport)
				var side := -1.0 if (frame / 90) % 2 == 0 else 1.0
				var target_x := clampf(player_pos.x + side * 420.0, 1680.0, 2600.0)
				var target_y := randf_range(170.0, 280.0)
				boss_reposition_target = Vector2(target_x, target_y)
				boss_lunge_start = boss_pos  # Record start position for interpolation
				boss_state = BossState.REPOSITION
				boss_state_timer = 55  # 55 frames smooth repositioning (eased, ~0.9s)
		
		BossState.REPOSITION:
			# Smooth eased movement toward target (ease-in-out for natural feel)
			var total_frames := 55.0
			var progress := 1.0 - float(boss_state_timer) / total_frames
			# Ease-in-out cubic
			var t := 4.0 * progress * progress * progress if progress < 0.5 else 1.0 - pow(-2.0 * progress + 2.0, 3.0) / 2.0
			var start_pos := boss_lunge_start  # Reuse as movement start
			boss_pos = start_pos.lerp(boss_reposition_target, t)
			# Add subtle vertical bob during movement
			boss_pos.y += sin(float(frame) * 0.017 * 0.85) * 1.2
			
			# Transition: reached target or timeout
			if boss_state_timer <= 0:
				# Higher phases: sometimes telegraph+lunge instead of returning to idle
				var lunge_chance := 0.3 + boss_phase * 0.1  # 30%/40%/50%...
				if randf() < lunge_chance and boss_phase >= 2:
					boss_state = BossState.TELEGRAPH
					boss_state_timer = 30  # 30 frames telegraph (player reaction window)
					boss_lunge_start = boss_pos
					# Lunge toward player's current position
					var lunge_dir := (player_pos - boss_pos).normalized()
					boss_lunge_return = boss_pos + lunge_dir * 320.0
					boss_lunge_return.x = clampf(boss_lunge_return.x, 1250.0, 2180.0)
					boss_lunge_return.y = clampf(boss_lunge_return.y, ARENA_TOP + 80.0, GROUND_Y - 180.0)
				else:
					boss_state = BossState.IDLE
					boss_state_timer = 60
		
		BossState.TELEGRAPH:
			# Charge-up: hover in place, slight pulsing (visual warning)
			var pulse := 1.0 + sin(float(boss_state_timer) * 0.4) * 0.08
			boss_pos.y += (pulse - 1.0) * 3.0
			
			if boss_state_timer <= 0:
				boss_state = BossState.LUNGE
				boss_state_timer = 22  # 22 frames lunge duration (18~24 target range)
		
		BossState.LUNGE:
			# Fast dash toward lunge_return, then smooth return to start
			var progress := 1.0 - float(boss_state_timer) / 22.0
			if progress < 0.6:
				# Outward lunge (first 60% of duration)
				var t := progress / 0.6
				# Ease-out quad for snappy start
				t = 1.0 - pow(1.0 - t, 2.0)
				boss_pos = boss_lunge_start.lerp(boss_lunge_return, t)
			else:
				# Return phase (last 40%)
				var t := (progress - 0.6) / 0.4
				t = pow(t, 1.5)  # Ease-in for smooth return
				boss_pos = boss_lunge_return.lerp(boss_lunge_start, t)
			
			# Spawn ring bullets at lunge peak
			if boss_state_timer == 9:  # Mid-lunge
				for i in range(14):
					var a := TAU * float(i) / 14.0
					_spawn_bullet(boss_pos, Vector2(cos(a), sin(a)) * 215.0, RED if boss_id == "crimson" else HAZARD, "hazard")
				screen_shake = 6.0
			
			if boss_state_timer <= 0:
				boss_state = BossState.IDLE
				boss_state_timer = 45
	
	# Attack pattern timer (independent of movement)
	# 修：带状态的招式（预警→发射）必须每帧推进，否则一招要等几十秒才出弹
	# 招式按帧驱动（新招式全部是 frame%N 形式），演出期间暂停
	if not cutin_active and battle_intro_t <= 0.0:
		_spawn_boss_pattern()
	
	_boss_move_particles()
	if boss_slide_to > 0.0:
		boss_pos.x = move_toward(boss_pos.x, boss_slide_to, 900.0 * FIXED_DT)
		if absf(boss_pos.x - boss_slide_to) < 4.0:
			boss_pos.x = boss_slide_to
			boss_slide_to = -1.0
	# 非硬直状态缓慢回到悬空高度（避免瞬移）
	if boss_skill_state == "" and str(boss_id) == "crimson":
		boss_pos.y = move_toward(boss_pos.y, 226.0, 220.0 * FIXED_DT)
	_update_beam_warnings()
	_update_death()
	_update_boss_extras()
	_update_fx_rings()
	if cutin_active:
		cutin_timer -= FIXED_DT
		if cutin_timer <= 0.0:
			cutin_active = false
	if battle_intro_t > 0.0:
		battle_intro_t = maxf(0.0, battle_intro_t - FIXED_DT)
		if battle_intro_t <= 0.0 and boss_bgm_pending:
			boss_bgm_pending = false
			_start_battle_bgm()
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
			_spawn_fx_ring(boss_pos, Color(1, 1, 1, 0.9), 420.0, 0.5, 6.0)
			_spawn_mirror_shards(10, 0.8)
			banner = "PHASE %d" % (boss_phase + 1)
			banner_timer = 85
			if boss_phase == boss_phase_count - 1:
				cutin_active = true
				cutin_timer = 2.0
				sfx_player.play("skill")
				_spawn_mirror_shards(18, 1.2)
			screen_shake = 10.0
			boss_ring_flash = 10  # Phase transition ring flash
			_spawn_mirror_shards(18, 1.0)
			# Reset state on phase change
			boss_state = BossState.IDLE
			boss_state_timer = 60
			# Reset position for clean phase start
			boss_lunge_start = boss_pos
		else:
			mode = Mode.VICTORY
			_stop_battle_bgm()
			banner = ""
			_spawn_burst(boss_pos, RED if boss_id == "crimson" else HAZARD, 58)
			_stop_music()

func _spawn_boss_pattern() -> void:
	if boss_id == "crimson":
		_patterns_crimson()
	else:
		_patterns_marysue()

func _crimson_thrust_lines() -> void:
	# Telegraph: 24 frames red line → thrust 900px/s
	if boss_skill_state == "":
		boss_skill_state = "telegraph"
		boss_skill_timer = 24
		boss_skill_subframe = 0
		var aim := (player_pos - boss_pos).normalized()
		skill_warnings.append({"kind": "line", "pos": boss_pos, "dir": aim, "life": 24.0 / 60.0, "color": RED})
	elif boss_skill_state == "telegraph":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = "firing"
			boss_skill_timer = 30  # Thrust duration
			# Fire single thrust blade (900px/s, length 420px)
			var aim: Vector2 = skill_warnings[0]["dir"] if skill_warnings.size() > 0 else Vector2(-1, 0)
			_spawn_bullet(boss_pos, aim * 900.0, RED, "lance")
	elif boss_skill_state == "firing":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			skill_warnings.clear()

# Crimson Stage 3: Fan slash (扇形 5-7 blades, safe gap)
func _crimson_fan_slash() -> void:
	if boss_skill_state == "":
		boss_skill_state = "telegraph"
		boss_skill_timer = 30  # 30 frames warning
		boss_skill_subframe = 0
		# Draw 7 telegraph lines (arc pattern)
		for i in range(7):
			var a := lerpf(-0.6, 0.6, float(i) / 6.0)  # Fan arc ±0.6 rad
			var dir := Vector2(-cos(a), sin(a))
			skill_warnings.append({"kind": "line", "pos": boss_pos, "dir": dir, "life": 30.0 / 60.0, "color": RED})
	elif boss_skill_state == "telegraph":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = "firing"
			boss_skill_timer = 7 * 4  # 7 blades @ 4 frame intervals
			boss_skill_subframe = 0
	elif boss_skill_state == "firing":
		boss_skill_timer -= 1
		# Fire one blade every 4 frames
		if boss_skill_timer % 4 == 0:
			var idx := (7 * 4 - boss_skill_timer) / 4
			if idx < skill_warnings.size():
				var warn: Dictionary = skill_warnings[idx]
				_spawn_bullet(boss_pos, warn["dir"] * 420.0, RED, "blade")
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			skill_warnings.clear()

# Crimson Stage 5: Red moon finale (12 waves @ 30° intervals, 420px/s)
func _crimson_red_moon_finale() -> void:
	if boss_skill_state == "":
		boss_skill_state = "telegraph"
		boss_skill_timer = 42  # 42 frames warning
		boss_skill_subframe = 0
		# Flash 3 times (visual only, no mechanic)
		for i in range(12):
			var a := float(i) * TAU / 12.0
			var dir := Vector2(cos(a), sin(a))
			skill_warnings.append({"kind": "line", "pos": boss_pos, "dir": dir, "life": 42.0 / 60.0, "color": RED})
	elif boss_skill_state == "telegraph":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = "firing"
			boss_skill_timer = 12 * 5  # 12 bullets @ 5 frame intervals
			boss_skill_subframe = 0
	elif boss_skill_state == "firing":
		boss_skill_timer -= 1
		# Fire one wave every 5 frames
		if boss_skill_timer % 5 == 0:
			var idx := (12 * 5 - boss_skill_timer) / 5
			if idx < skill_warnings.size():
				var warn: Dictionary = skill_warnings[idx]
				var speed := 420.0 if idx < 6 else 500.0  # Speed boost after 7th
				_spawn_bullet(boss_pos, warn["dir"] * speed, RED, "blade")
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			skill_warnings.clear()
			# Cooldown: 72 frames (handled by boss_attack_timer reset)

# Marysue Stage 1: Ring collapse (12 bullets, 260px/s, 96px gap)
func _marysue_ring_collapse() -> void:
	if boss_skill_state == "":
		boss_skill_state = "telegraph"
		boss_skill_timer = 36  # 36 frames warning
		boss_skill_subframe = 0
		# Draw collapsing ring visual (12 points)
		for i in range(12):
			var a := float(i) * TAU / 12.0
			var dir := Vector2(cos(a), sin(a))
			skill_warnings.append({"kind": "circle", "pos": boss_pos, "dir": dir, "life": 36.0 / 60.0, "color": HAZARD})
	elif boss_skill_state == "telegraph":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = "firing"
			boss_skill_timer = 12 * 4  # 12 bullets @ 4 frame intervals
			boss_skill_subframe = 0
	elif boss_skill_state == "firing":
		boss_skill_timer -= 1
		# Fire one bullet every 4 frames
		if boss_skill_timer % 4 == 0:
			var idx := (12 * 4 - boss_skill_timer) / 4
			if idx < skill_warnings.size():
				var warn: Dictionary = skill_warnings[idx]
				_spawn_bullet(boss_pos, warn["dir"] * 260.0, HAZARD, "hazard")
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			skill_warnings.clear()

# Marysue Stage 3: Wing sweep (left/right fan, 6 each, 380px/s)
func _marysue_wing_sweep() -> void:
	if boss_skill_state == "":
		boss_skill_state = "telegraph"
		boss_skill_timer = 30  # 30 frames warning
		boss_skill_subframe = 0
		# Left wing: 6 blades @ -60°/-40°/-20°/+20°/+40°/+60°
		for i in range(6):
			var angles := [-1.05, -0.7, -0.35, 0.35, 0.7, 1.05]  # Radians
			var dir := Vector2(cos(angles[i]), sin(angles[i]))
			skill_warnings.append({"kind": "line", "pos": boss_pos, "dir": dir, "life": 30.0 / 60.0, "color": HAZARD})
	elif boss_skill_state == "telegraph":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = "firing"
			boss_skill_timer = 6 * 5  # 6 blades @ 5 frame intervals
			boss_skill_subframe = 0
	elif boss_skill_state == "firing":
		boss_skill_timer -= 1
		# Fire one blade every 5 frames
		if boss_skill_timer % 5 == 0:
			var idx := (6 * 5 - boss_skill_timer) / 5
			if idx < skill_warnings.size():
				var warn: Dictionary = skill_warnings[idx]
				_spawn_bullet(boss_pos, warn["dir"] * 380.0, HAZARD, "blade")
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			skill_warnings.clear()

# Marysue Stage 6: Inverted finale (16 bullets, 340px/s, 128px gap, warning 60 frames)
func _marysue_inverted_finale() -> void:
	if boss_skill_state == "":
		boss_skill_state = "telegraph"
		boss_skill_timer = 60  # 60 frames warning
		boss_skill_subframe = 0
		# Four-corner runes (visual warning only, 16 bullets will cover 360°)
		for i in range(16):
			var a := float(i) * TAU / 16.0
			var dir := Vector2(cos(a), sin(a))
			skill_warnings.append({"kind": "circle", "pos": boss_pos, "dir": dir, "life": 60.0 / 60.0, "color": HAZARD})
	elif boss_skill_state == "telegraph":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = "firing"
			boss_skill_timer = 16 * 5  # 16 bullets @ 5 frame intervals
			boss_skill_subframe = 0
	elif boss_skill_state == "firing":
		boss_skill_timer -= 1
		# Fire one bullet every 5 frames
		if boss_skill_timer % 5 == 0:
			var idx := (16 * 5 - boss_skill_timer) / 5
			if idx < skill_warnings.size():
				var warn: Dictionary = skill_warnings[idx]
				_spawn_bullet(boss_pos, warn["dir"] * 340.0, HAZARD, "hazard")
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			skill_warnings.clear()

func _spawn_bullet(pos: Vector2, velocity: Vector2, color: Color, kind: String, life := 5.0, homing := 0.0) -> void:
	bullets.append({"pos": pos, "vel": velocity, "life": life, "color": color, "kind": kind, "angle": velocity.angle(), "grazed": false, "homing": homing})

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
			boss_hp = maxf(0.0, boss_hp - (8.0 if tragedy_buff_t > 0.0 else 3.0))
			boss_hit_flash = 8
			boss_ring_flash = 10
			_fx_boss_hit(shot["pos"])
			player_energy = minf(ENERGY_MAX, player_energy + ENERGY_PER_HIT)
			hitstop = 0  # 用户要求：命中 Boss 不顿帧
			screen_shake = 0.0
			_spawn_burst(shot["pos"], RED, 5)
			shot["life"] = 0.0
	shots = shots.filter(func(shot): return float(shot.get("life", 0.0)) > 0.0 and shot["pos"].x > -80.0 and shot["pos"].x < WORLD_W + 80.0 and shot["pos"].y > 0.0 and shot["pos"].y < VIEW.y)

func _update_bullets() -> void:
	for warning in warnings:
		warning["life"] = float(warning["life"]) - FIXED_DT
	warnings = warnings.filter(func(w): return float(w.get("life", 0.0)) > 0.0)
	for bullet in bullets:
		var prev_pos: Vector2 = bullet.get("prev_pos", bullet["pos"])
		bullet["prev_pos"] = bullet["pos"]
		bullet["pos"] += bullet["vel"] * FIXED_DT
		# 镜面反弹符纸：碰到战场边缘反向
		if str(bullet.get("kind", "")) == "bounce":
			var bvl: Vector2 = bullet["vel"]
			var bx2: float = bullet["pos"].x
			if bx2 < _battle_left() + 20.0 or bx2 > _battle_right() - 20.0:
				bullet["vel"] = Vector2(-bvl.x, bvl.y)
				bullet["angle"] = Vector2(bullet["vel"]).angle()
		# 激光/光柱沿线粒子（绿色火花）
		var bk := str(bullet.get("kind", ""))
		if (bk == "laser" or bk == "beam" or bk == "laser_down") and randf() < 0.55:
			var bpos: Vector2 = bullet["pos"]
			var px := bpos.x + randf_range(-16.0, 16.0)
			var py := bpos.y + randf_range(-90.0, 90.0)
			if bk == "beam":
				py = randf_range(60.0, GROUND_Y - 10.0)
			_spawn_particle(Vector2(px, py), Color(0.51, 1.0, 0.0, 0.9), randf_range(0.25, 0.55),
				Vector2(randf_range(-70, 70), randf_range(-170, -40)), randf_range(2.0, 4.5))
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
			player_energy = minf(ENERGY_MAX, player_energy + ENERGY_PER_GRAZE)
			_fx_graze(Vector2(bullet["pos"]))
			energy_flash = 8
			player_dash_cd = maxi(0, player_dash_cd - 2)
			_spawn_burst(center, WHITE, 4)
			# Graze SFX: play once per frame even if multiple grazes
			if not graze_this_frame:
				graze_this_frame = true
				if player_graze_chain % 5 == 0:
					sfx_player.play("graze_up")
				else:
					sfx_player.play("graze")
		if distance <= 10.0 and player_hurt_invuln <= 0 and player_dash_invuln <= 0:
			player_hp -= 1
			player_hurt_invuln = 70
			player_courage = maxf(0.0, player_courage - 18.0)
			player_graze_chain = 0
			player_graze_age = 0
			red_vignette = 18.0
			screen_shake = 9.0
			_spawn_burst(center, WHITE, 18)
			sfx_player.play("hurt")
			if player_hp <= 0:
				player_hp = 0
				_start_death()
			return

func _use_red_skill() -> void:
	# 用户要求：击败魔姬解锁后即可用，消耗 2 MP（不再要求满勇气）
	if not skill_red_tragedy:
		return
	if player_energy < 2:
		return
	player_energy -= 2.0          # 消耗 2 MP（用户要求）
	player_hp = mini(PLAYER_MAX_HP, player_hp + 2)   # 回复 2 HP
	tragedy_buff_t = 20.0         # 20 秒强化剑气
	sfx_player.play("skill")
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
	_fx_skill_cast(blast, RED)
	banner = "枪火击溃"
	banner_timer = 55
	hitstop = 6

func _use_hellfire() -> void:
	if player_energy < 2:
		return
	player_energy -= 2
	hellfire_timer = 180
	hellfire_tick = 1
	_fx_skill_cast(boss_pos, RED)
	banner = "业火"
	banner_timer = 55
	_spawn_burst(boss_pos, RED, 34)

func _update_camera() -> void:
	if mode == Mode.BATTLE:
		# 围绕 Boss 的稳定跟随：目标固定为 Boss 屏幕中心，缓慢插值，不做 min/max 反复钳制
		var half := (BATTLE_HALF + 120.0)
		var want := boss_pos.x - VIEW.x * 0.5
		var lo := _battle_left() - 80.0
		var hi := _battle_right() + 80.0 - VIEW.x
		want = clampf(want, minf(lo, hi), maxf(lo, hi))
		camera_x = lerpf(camera_x, want, 1.0 - pow(0.02, FIXED_DT))
		return
	var target := clampf(player_pos.x - VIEW.x * 0.38, 0.0, WORLD_W - VIEW.x)
	camera_x = lerpf(camera_x, target, 1.0 - pow(0.0004, FIXED_DT))

func _update_victory() -> void:
	if _just("confirm"):
		_start_story(boss_after)

func _update_end() -> void:
	# 结局停留，不再重跑游戏（用户要求）
	if _just("confirm"):
		pass
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
	
	# Update skill warnings
	for warn in skill_warnings:
		warn["life"] = float(warn.get("life", 0.0)) - FIXED_DT
	skill_warnings = skill_warnings.filter(func(w): return float(w.get("life", 0.0)) > 0.0)
	
	red_vignette = maxf(0.0, red_vignette - 1.0)
	if banner_timer <= 0:
		banner = ""
	
	# Update dash FX
	_update_dash_fx()
	
	# Update walk dust
	for dust in walk_dust:
		dust["pos"] += dust["vel"] * FIXED_DT
		dust["life"] = float(dust["life"]) - FIXED_DT
		var progress := 1.0 - float(dust["life"]) / float(dust["max_life"])
		dust["alpha"] = (1.0 - progress) * 0.35
	walk_dust = walk_dust.filter(func(d): return float(d.get("life", 0.0)) > 0.0)
	
	# Update jump squash timer
	if jump_squash_timer > 0:
		jump_squash_timer -= 1
		_update_jump_squash()
	else:
		jump_squash = Vector2.ONE
	
	# Reset graze frame flag
	graze_this_frame = false

func _spawn_particle(pos: Vector2, color: Color, life: float, vel := Vector2.ZERO, size := 4.0) -> void:
	particles.append({"pos": pos, "vel": vel, "life": life, "max": life, "color": color, "size": size})

func _spawn_burst(pos: Vector2, color: Color, count: int) -> void:
	for i in range(count):
		var angle := TAU * float(i) / maxf(1.0, float(count)) + randf_range(-0.18, 0.18)
		_spawn_particle(pos, color, randf_range(0.25, 0.7), Vector2(cos(angle), sin(angle)) * randf_range(45.0, 230.0), randf_range(2.0, 7.0))

func _spawn_mirror_shards(count: int, power: float) -> void:
	sfx_player.play("shards")
	for i in range(count):
		var angle := TAU * float(i) / maxf(1.0, float(count)) + randf_range(-0.3, 0.3)
		mirror_shards.append({"pos": Vector2(640, 350), "vel": Vector2(cos(angle), sin(angle)) * randf_range(90.0, 280.0) * power, "rot": randf_range(0, TAU), "spin": randf_range(-4, 4), "life": randf_range(0.7, 1.4), "size": randf_range(8, 24)})

func _draw() -> void:
	# Debug mode: draw only player on black background
	if debug_player_only:
		draw_rect(Rect2(Vector2.ZERO, VIEW), BLACK)
		_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)
		return
	
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
	# Story flash must be the final layer (above mirror shards and all FX)
	if mode == Mode.STORY and not story_flash_seq.is_empty():
		draw_rect(Rect2(Vector2.ZERO, VIEW), _flash_color())
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_background() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW), BLACK)
	# Battle mode: always use clean mirror.jpg background (not mirror_alt with crack panel)
	var bg_key := "bg_mirrorworld"
	if mode == Mode.BATTLE:
		bg_key = "bg_mirrorworld"
	elif story_bg == "forest":
		bg_key = "bg_forest"
	elif story_bg == "void":
		bg_key = "bg_mirrorworld"
	else:
		bg_key = "bg_mirrorworld"
	var bg_tex: Texture2D = null if (mode != Mode.BATTLE and story_bg == "void") else textures.get(bg_key)
	if bg_tex:
		var alpha := 0.42
		var tint := Color(1, 1, 1, alpha)
		if mode == Mode.BATTLE:
			# Battle: use top 60% of mirror.jpg (tree crown area, crop out sword hilt)
			# Darken with alpha 0.75 black overlay (multiply RGB by 0.25 = 0.4 * base alpha)
			tint = Color(0.25, 0.25, 0.25, alpha)
			var src_h := bg_tex.get_height()
			var crop_h := int(src_h * 0.6)  # Top 60% region
			var src_rect := Rect2(0, 0, bg_tex.get_width(), crop_h)
			# Scale to fill view width, keep aspect ratio
			var scale := VIEW.x * 1.45 / float(bg_tex.get_width())
			var dst_h := crop_h * scale
			var dst_rect := Rect2(-camera_x * 0.25, 0, VIEW.x * 1.45, dst_h)
			draw_texture_rect_region(bg_tex, dst_rect, src_rect, tint)
		else:
			draw_texture_rect(bg_tex, Rect2(-camera_x * 0.25, 0, VIEW.x * 1.45, VIEW.y), false, tint)
	for i in range(15):
		var y := float(i) * 46.0
		draw_line(Vector2(0, y), Vector2(VIEW.x, y), Color(1, 1, 1, 0.025), 1.0)
	for i in range(13):
		var x := float(i) * 118.0 - fmod(elapsed * 16.0, 118.0)
		draw_line(Vector2(x, 110), Vector2(x + 170, GROUND_Y), Color(CYAN, 0.075), 1.0)
		draw_line(Vector2(x + 80, 110), Vector2(x - 80, GROUND_Y), Color(CYAN, 0.04), 1.0)
	draw_line(Vector2(0, GROUND_Y), Vector2(VIEW.x, GROUND_Y), Color(CYAN, 0.28), 2.0)

func _draw_title() -> void:
	var logo_tex: Texture2D = textures.get("logo_hongzhijing")
	if logo_tex:
		# Logo: 1200×420 source, display at ~62% view width = ~790px width
		var logo_width := 790.0
		var logo_height := logo_tex.get_height() * (logo_width / float(logo_tex.get_width()))
		var logo_center := Vector2(VIEW.x * 0.5, 200.0)
		# Gentle breath animation: ±0.5% scale, 4 second cycle
		var breath := 1.0 + sin(elapsed * (TAU / 4.0)) * 0.005
		var logo_rect := Rect2(logo_center.x - logo_width * breath * 0.5, logo_center.y - logo_height * breath * 0.5, logo_width * breath, logo_height * breath)
		draw_texture_rect(logo_tex, logo_rect, false, Color.WHITE)
		
		# Prompt: "ENTER 开始游戏" below logo
		var prompt_y := logo_center.y + logo_height * 0.5 + 100.0
		draw_string(ThemeDB.fallback_font, Vector2(VIEW.x * 0.5 - 100.0, prompt_y), "ENTER 开始游戏", HORIZONTAL_ALIGNMENT_LEFT, -1, 30, RED)
		
		# Version: "DEMO v0.1" below prompt (gray 60%)
		var version_y := prompt_y + 50.0
		draw_string(ThemeDB.fallback_font, Vector2(VIEW.x * 0.5 - 50.0, version_y), "DEMO v0.1", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(GREY, 0.6))
		
		# Controls hint at bottom
		draw_string(ThemeDB.fallback_font, Vector2(414, 560), "A D 移动   SPACE 跳跃   SHIFT / K / 右键 冲刺   J / Z / 左键 射击", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, GREY)
	else:
		# Fallback: text-based title when logo fails to load
		draw_string(ThemeDB.fallback_font, Vector2(400, 220), "红之镜 DEMO", HORIZONTAL_ALIGNMENT_LEFT, -1, 70, RED)
		draw_string(ThemeDB.fallback_font, Vector2(450, 300), "MIRROR OF RED", HORIZONTAL_ALIGNMENT_LEFT, -1, 32, Color(GREY, 0.65))
		draw_string(ThemeDB.fallback_font, Vector2(460, 420), "按 ENTER / SPACE 开始", HORIZONTAL_ALIGNMENT_LEFT, -1, 30, RED)
		draw_string(ThemeDB.fallback_font, Vector2(520, 480), "DEMO v0.1", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(GREY, 0.6))
		draw_string(ThemeDB.fallback_font, Vector2(414, 560), "A D 移动   SPACE 跳跃   SHIFT / K / 右键 冲刺   J / Z / 左键 射击", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, GREY)

func _draw_story() -> void:
	if story_cg:
		draw_texture_rect(story_cg, Rect2(0, 70, VIEW.x, 580), false, Color(1, 1, 1, 0.84))
	elif story_cmd.get("t", "") == "cg" and story_cmd.get("label", "") == "法环陷阱":
		_draw_trap_cg()
	if story_cmd.get("t", "") != "card":
		_draw_portrait(story_left, Vector2(340, 580), 0.62, _portrait_speaking(story_left), false)
		_draw_portrait(story_right, Vector2(940, 580), 0.62, _portrait_speaking(story_right), true)
	# A scene can stay black during narration (the prologue reads a letter).
	# Fade the scenery and portraits before drawing text and continue prompts.
	# All fade layers (partial and full blackout) are drawn here, before dialogue.
	if intro_hold > 0.0:
		intro_hold = maxf(0.0, intro_hold - FIXED_DT)
		if intro_hold <= 0.0:
			story_intro = ""
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
		var slide := (1.0 - story_text_alpha) * 10.0
		var box_alpha := 0.9 * clampf(story_text_alpha * 1.4, 0.0, 1.0)
		draw_rect(Rect2(50, 520 + slide, 1180, 150), Color(0.02, 0.02, 0.02, box_alpha))
		# Name plate color by speaker: rek/crimson #FF0000, marysue #82FF00, norden #FFFFFF, mabel #00BAFF
		var name_color := WHITE  # Default
		match story_who:
			"rek", "蕾克", "rek_crimson", "猩红魔姬":
				name_color = RED  # #FF0000
			"marysue", "玛丽苏":
				name_color = HAZARD  # #82FF00
			"norden", "诺登":
				name_color = WHITE  # #FFFFFF
			"mabel", "梅贝尔":
				name_color = CYAN  # #00BAFF
		var line_col: Color = name_color.lerp(Color(0.6, 0.6, 0.6), 0.2)
		line_col.a *= clampf(story_text_alpha * 1.3, 0.0, 1.0)
		draw_line(Vector2(50, 520 + slide), Vector2(1230, 520 + slide), line_col, 2.0)
		if story_who != "":
			# 黑影/未识别的说话者显示「？？？」
			var who_key := _portrait_base(story_who)
			var is_unknown := (not known_names.has(who_key)) or story_expr == "shadow"
			var shown_name := "？？？" if is_unknown else _display_name(story_who)
			if not is_unknown:
				var skey := _portrait_base(story_who)
				if CHAR_TITLES.has(skey):
					var ttl := str(CHAR_TITLES[skey].get("title", ""))
					if ttl != "":
						shown_name = shown_name + "  ·  " + ttl
			var plate_color := Color(0.75, 0.75, 0.75) if is_unknown else name_color
			var name_a := plate_color
			name_a.a *= clampf(story_text_alpha * 1.3, 0.0, 1.0)
			draw_string(ThemeDB.fallback_font, Vector2(82, 555 + slide), shown_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, name_a)
		var shown := story_text.substr(0, int(story_reveal))
		var text_col := WHITE
		text_col.a = clampf(story_text_alpha * 1.35, 0.0, 1.0)
		draw_string(ThemeDB.fallback_font, Vector2(82, 605 + slide), shown, HORIZONTAL_ALIGNMENT_LEFT, 1110, 24, text_col)
		draw_string(ThemeDB.fallback_font, Vector2(1000, 652), "ENTER / SPACE 继续    TAB 跳过", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, GREY)
	# Flash moved to top-level _draw() final layer (after mirror shards)

func _draw_trap_cg() -> void:
	draw_set_transform(Vector2(925, 285), elapsed * 0.18, Vector2(1, 0.72))
	for radius in [130.0, 178.0, 218.0]:
		draw_arc(Vector2.ZERO, radius, 0, TAU, 96, Color(RED, 0.8), 3.0)
	for i in range(12):
		var angle := float(i) * TAU / 12.0
		var direction := Vector2.from_angle(angle)
		draw_line(direction * 178.0, direction * 218.0, Color(WHITE, 0.75), 2.0)
		draw_line(direction * 130.0, Vector2.from_angle(angle + TAU / 3.0) * 130.0, Color(RED, 0.18), 1.0)
	draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)

func _draw_portrait(id: String, center: Vector2, scale: float, active: bool, flipped: bool, alpha_mul: float = 1.0) -> void:
	if id == "":
		return
	var tex: Texture2D = _get_portrait_texture(id)
	if not tex:
		return
	var size := Vector2(tex.get_width(), tex.get_height()) * scale
	var tint := Color(1, 1, 1, alpha_mul)   # 立绘始终不透明（用户要求）
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

# 登场竖幅：家徽 + 双描边 + 回纹 + 缎带尾 + 竖排「名字 / 称号」（与网页版 drawIntro 同款）
const CHAR_TITLES := {
	"rek": {"name": "蕾克", "title": "小红帽", "color": Color(1, 0, 0), "tcolor": Color(1, 1, 1)},
	"rek_crimson": {"name": "猩红魔姬·雷帝", "title": "自负的暴君", "color": Color(1, 0, 0), "tcolor": Color(1, 0, 0)},
	"crimson": {"name": "猩红魔姬·雷帝", "title": "自负的暴君", "color": Color(1, 0, 0), "tcolor": Color(1, 0, 0)},
	"norden": {"name": "诺登", "title": "计时者 白之兔", "color": Color(1, 0.31, 0.31), "tcolor": Color(1, 1, 1)},
	"marysue": {"name": "玛丽苏", "title": "扭曲的黑童话作家", "color": Color(0.51, 1, 0), "tcolor": Color(0.51, 1, 0)},
	"mabel": {"name": "梅贝尔", "title": "来自虚空的虚无少女", "color": Color(0, 0.73, 1), "tcolor": Color(0, 0.73, 1)}
}

func _draw_intro(id: String) -> void:
	var data: Dictionary = CHAR_TITLES.get(id, {"name": _display_name(id), "title": "", "color": RED, "tcolor": Color(1, 1, 1)})
	var name_txt: String = data["name"]
	var title_txt: String = data["title"]
	var accent: Color = data["color"]
	var tcolor: Color = data["tcolor"]
	var bw := 116.0
	var body_len := maxf(float(name_txt.length()) * 42.0, float(title_txt.length()) * 28.0)
	var bh := maxf(160.0, 56.0 + body_len)
	var bx := VIEW.x - 72.0 - bw
	var by := 96.0
	var cx := bx + bw * 0.5

	# 顶部家徽：菱形 + 两侧尖翼
	var crest_y := by - 26.0
	var dia := PackedVector2Array([Vector2(cx, crest_y - 15), Vector2(cx + 12, crest_y), Vector2(cx, crest_y + 15), Vector2(cx - 12, crest_y)])
	draw_colored_polygon(dia, accent)
	for sgn in [-1.0, 1.0]:
		var wing := PackedVector2Array([Vector2(cx + sgn * 13, crest_y), Vector2(cx + sgn * 38, crest_y - 8), Vector2(cx + sgn * 31, crest_y), Vector2(cx + sgn * 38, crest_y + 8)])
		draw_colored_polygon(wing, Color(accent, 0.5))

	# 幅面：底 + 外粗边 + 内细边
	draw_rect(Rect2(bx, by, bw, bh), Color(0.06, 0.06, 0.07, 0.94))
	draw_rect(Rect2(bx, by, bw, bh), accent, false, 3.0)
	draw_rect(Rect2(bx + 6, by + 6, bw - 12, bh - 12), Color(1, 1, 1, 0.5), false, 1.0)

	# 两侧回纹
	var y := by + 24.0
	while y < by + bh - 26.0:
		draw_rect(Rect2(bx + 12, y, 9, 3), Color(accent, 0.45))
		draw_rect(Rect2(bx + 12, y, 3, 9), Color(accent, 0.45))
		draw_rect(Rect2(bx + bw - 21, y, 9, 3), Color(accent, 0.45))
		draw_rect(Rect2(bx + bw - 15, y, 3, 9), Color(accent, 0.45))
		y += 26.0

	# 底部缎带尾
	var ty := by + bh
	draw_colored_polygon(PackedVector2Array([Vector2(bx + 8, ty - 1), Vector2(cx - 3, ty + 26), Vector2(cx - 3, ty - 1)]), accent)
	draw_colored_polygon(PackedVector2Array([Vector2(bx + bw - 8, ty - 1), Vector2(cx + 3, ty + 26), Vector2(cx + 3, ty - 1)]), accent)

	# 竖排名字（烫印：黑边 + 主色 + 白高光）
	var name_h := float(name_txt.length()) * 42.0
	var name_top := by + maxf(40.0, (bh - name_h) * 0.5 + 18.0)
	for i in range(name_txt.length()):
		var ch := name_txt.substr(i, 1)
		var pos := Vector2(cx - 10.0, name_top + i * 42.0)
		draw_string_outline(ThemeDB.fallback_font, pos, ch, HORIZONTAL_ALIGNMENT_CENTER, -1, 34, 8, Color(0, 0, 0, 0.9))
		draw_string(ThemeDB.fallback_font, pos, ch, HORIZONTAL_ALIGNMENT_CENTER, -1, 34, accent)
		draw_string(ThemeDB.fallback_font, pos - Vector2(1, 1), ch, HORIZONTAL_ALIGNMENT_CENTER, -1, 34, Color(1, 1, 1, 0.18))

	# 竖排称号（左侧）
	if title_txt != "":
		for i in range(title_txt.length()):
			var ch2 := title_txt.substr(i, 1)
			draw_string_outline(ThemeDB.fallback_font, Vector2(bx - 34.0, by + 34.0 + i * 28.0), ch2, HORIZONTAL_ALIGNMENT_CENTER, -1, 20, 5, Color(0, 0, 0, 0.85))
			draw_string(ThemeDB.fallback_font, Vector2(bx - 34.0, by + 34.0 + i * 28.0), ch2, HORIZONTAL_ALIGNMENT_CENTER, -1, 20, tcolor)

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
		if kind == "throne":
			# 地图王座：新生成的低调暗铁王座（压暗过，不抢画面）
			var ttex: Texture2D = textures.get("throne_new")
			if ttex:
				character_art.draw_ground(self, ttex, pos, 330.0)
			else:
				_draw_mirror_gate(pos)
		elif kind == "norden" or kind == "mabel":
			var fallback_tex: Texture2D = textures.get(kind)
			var height := NPC_MABEL_HEIGHT if kind == "mabel" else NPC_NORDEN_HEIGHT
			character_art.draw_npc_breathe(self, kind, pos, height, elapsed, fallback_tex)
		elif kind == "mirror":
			_draw_mirror_gate(pos)
		elif kind == "shadow":
			# 远处玛丽苏黑影：纯黑剪影 + 微红眼
			draw_rect(Rect2(pos.x - 26, pos.y - 150, 52, 150), Color(0, 0, 0, 0.92))
			draw_circle(Vector2(pos.x - 8, pos.y - 138), 3, Color(1, 0, 0, 0.85))
			draw_circle(Vector2(pos.x + 8, pos.y - 138), 3, Color(1, 0, 0, 0.85))
	if walk_target.size() > 0:
		var kind := str(walk_target.get("kind", ""))
		var p := Vector2(float(walk_target.get("x", 0.0)) - camera_x, GROUND_Y)
		if kind == "norden" or kind == "mabel":
			var fallback_tex: Texture2D = textures.get(kind)
			var height := NPC_MABEL_HEIGHT if kind == "mabel" else NPC_NORDEN_HEIGHT
			_draw_npc_glow(p, height)
			character_art.draw_npc_breathe(self, kind, p, height, elapsed, fallback_tex)
			# 头顶交互徽章（显眼）
			var tip: String = str(walk_target.get("label", "按 W 交互"))
			var tip_pos := p + Vector2(-58, -height - 30.0)
			draw_rect(Rect2(tip_pos, Vector2(116, 26)), Color(0, 0, 0, 0.72))
			draw_rect(Rect2(tip_pos, Vector2(116, 26)), Color(1, 1, 1, 0.75), false, 1.5)
			draw_string(ThemeDB.fallback_font, tip_pos + Vector2(10, 19), tip, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, WHITE)
		elif kind == "mirror":
			_draw_mirror_gate(p)
	_draw_walk_dust()
	_draw_dash_fx()
	_draw_dash_trail()
	_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)
	_draw_signboard()
	_draw_tutorial()
	_draw_particles_world()
	# 走位段不画对话立绘（用户要求：对话结束立即消失）
	draw_string(ThemeDB.fallback_font, Vector2(40, 48), "A / D 移动    SPACE 跳跃    SHIFT / K / 右键 冲刺    W 靠近并交互", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, WHITE)

func _npc_rect(id: String, foot: Vector2) -> Rect2:
	var height := NPC_MABEL_HEIGHT if id == "mabel" else NPC_NORDEN_HEIGHT
	return character_art.ground_rect(textures.get(id), foot, height)

func _draw_world_grid() -> void:
	draw_rect(Rect2(0, GROUND_Y + 2, VIEW.x, VIEW.y - GROUND_Y), Color(0.02, 0.02, 0.02, 1))
	for i in range(24):
		var x := float(i) * 120.0 - fmod(camera_x, 120.0)
		draw_line(Vector2(x, GROUND_Y), Vector2(x + 90, GROUND_Y - 185), Color(CYAN, 0.08), 1.0)

func _draw_mirror_gate(pos: Vector2) -> void:
	# 新镜子立绘（gpt-image-2 生成，三色合规）；缺图时退回程序绘制
	var mtex: Texture2D = textures.get("mirror_stand")
	if mtex:
		# 镜面底部光晕，暗场景里更醒目
		draw_circle(Vector2(pos.x, pos.y - 10), 90.0, Color(0, 0.73, 1, 0.10))
		character_art.draw_ground(self, mtex, pos, 460.0)
		return
	draw_rect(Rect2(pos.x - 74, pos.y - 260, 148, 260), Color(CYAN, 0.12))
	draw_rect(Rect2(pos.x - 62, pos.y - 248, 124, 236), Color(CYAN, 0.16), false, 3.0)
	draw_line(pos + Vector2(-45, -205), pos + Vector2(30, -135), Color(1, 1, 1, 0.7), 2.0)
	draw_line(pos + Vector2(30, -135), pos + Vector2(-8, -70), Color(1, 1, 1, 0.6), 2.0)

func _draw_battle() -> void:
	var mirror_world := mirror_flip
	if mirror_world:
		draw_set_transform(Vector2(VIEW.x, 0), 0.0, Vector2(-1, 1))
	_draw_world_grid()
	_draw_boss_fx()
	_draw_projectiles()
	_draw_walk_dust()
	_draw_dash_fx()
	_draw_dash_trail()
	_draw_boss()
	_draw_boss_extras()
	_draw_beam_warnings()
	_draw_battle_bounds_fx()
	_draw_fx_rings()
	if mirror_world:
		draw_set_transform(Vector2(VIEW.x, 0), 0.0, Vector2(-1, 1))
	_draw_player_at(player_pos - Vector2(camera_x, 0), WHITE)
	_draw_particles_world()
	if tragedy_buff_t > 0.0:
		tragedy_buff_t = maxf(0.0, tragedy_buff_t - FIXED_DT)
	if ball_hint_t > 0.0 and mode == Mode.WALK:
		ball_hint_t = maxf(0.0, ball_hint_t - FIXED_DT)
		var ha := minf(1.0, ball_hint_t / 1.0)
		draw_string(ThemeDB.fallback_font, Vector2(360, 200), "空中 按住 W + 冲刺 → 球形态（无敌）", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color(1, 1, 1, 0.85 * ha))
	if hurt_vignette > 0:
		var hv := float(hurt_vignette) / 18.0
		draw_rect(Rect2(0, 0, VIEW.x, 14), Color(1, 0, 0, 0.45 * hv))
		draw_rect(Rect2(0, VIEW.y - 14, VIEW.x, 14), Color(1, 0, 0, 0.45 * hv))
		draw_rect(Rect2(0, 0, 14, VIEW.y), Color(1, 0, 0, 0.45 * hv))
		draw_rect(Rect2(VIEW.x - 14, 0, 14, VIEW.y), Color(1, 0, 0, 0.45 * hv))
		hurt_vignette -= 1
	if mirror_world:
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	_draw_battle_overlays()
	_draw_death_overlay()
	_draw_hud()

func _draw_boss_fx() -> void:
	# Defensive transform reset before boss rendering (prevents stale transform from previous draw calls)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	
	var center := boss_pos - Vector2(camera_x, 0)
	var color := RED if boss_id == "crimson" else HAZARD
	
	# Draw new circular rune magic array (behind boss)
	# 950×950 source → 217px display (3.1 × 70px character height)
	var ring_dir := "scarlet" if boss_id == "crimson" else "marysue"
	var ring_key := "ring_circle_%s" % ring_dir
	var ring_tex: Texture2D = textures.get(ring_key)
	if ring_tex:
		# Rotation: +0.55 rad/s ≈ 31.5°/s
		var rotation := elapsed * 0.55
		# Breathing scale: 1 ± 0.02, period 2.4 rad/s
		var breathe := 1.0 + sin(elapsed * 2.4) * 0.02
		# Flash alpha: 0.85 → 1.0 → 0.85 (10 frames, triggered by boss_ring_flash)
		var alpha := 0.85
		if boss_ring_flash > 0:
			# Flash curve: ramp up first 5 frames (0.85→1.0), ramp down last 5 frames (1.0→0.85)
			var flash_progress := 1.0 - float(boss_ring_flash) / 10.0
			if flash_progress < 0.5:
				# First half: 0.85 → 1.0
				alpha = lerpf(0.85, 1.0, flash_progress * 2.0)
			else:
				# Second half: 1.0 → 0.85
				alpha = lerpf(1.0, 0.85, (flash_progress - 0.5) * 2.0)
		
		var ring_scale := (RING_DISPLAY_DIAMETER / 950.0) * breathe
		var ring_size := Vector2(950.0, 950.0) * ring_scale
		# Draw behind boss (this function is called before _draw_boss)
		draw_set_transform(center, rotation, Vector2.ONE)
		draw_texture_rect(ring_tex, Rect2(-ring_size * 0.5, ring_size), false, Color(1, 1, 1, alpha))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

const ANIM_BODY_H := {"crimson": 150.0, "marysue": 360.0}

func _draw_boss() -> void:
	var center := boss_pos - Vector2(camera_x, 0)
	# Select boss pose based on state
	var key := _boss_pose_key()
	var tex: Texture2D = textures.get(key)
	# 猩红魔姬：优先播动作序列（待机/移动/突刺/斩击）
	if boss_id == "marysue" and boss_anim.has("marysue_idle"):
		var msf: Array = boss_anim["marysue_idle"]
		tex = msf[int(frame / 5) % msf.size()]
	elif boss_id == "crimson" and boss_anim.size() > 0:
		var anim_name := "idle"
		match boss_state:
			BossState.LUNGE:
				anim_name = "thrust"
			BossState.TELEGRAPH:
				anim_name = "move"
			BossState.REPOSITION:
				anim_name = "move"
			_:
				anim_name = "idle"
		if boss_skill_state == "firing" and boss_anim.has("slash"):
			anim_name = "slash"
		var seq: Array = boss_anim.get(anim_name, [])
		if seq.size() > 0:
			tex = seq[int(frame / 4) % seq.size()]
	if tex:
		var tint := WHITE if boss_hit_flash == 0 or frame % 4 < 2 else Color(1, 1, 1, 0.4)
		# 等比缩放（宽高同一比例，绝不压扁）：按参考身体高度换算
		var vb: Rect2 = character_art.visible_bounds(tex)
		var ref_h: float = float(ANIM_BODY_H.get(boss_id, vb.size.y))
		var scale := BOSS_HEIGHT / maxf(1.0, ref_h)
		var draw_size := tex.get_size() * scale
		var draw_pos := Vector2(center.x - (vb.position.x + vb.size.x * 0.5) * scale,
			center.y + float(BOSS_HEIGHT) * 0.5 - (vb.position.y + vb.size.y) * scale)
		draw_texture_rect(tex, Rect2(draw_pos, draw_size), false, tint)
	else:
		draw_circle(center, 48, Color(GREY, 0.9))
		draw_circle(center + Vector2(-16, -10), 7, RED if boss_id == "crimson" else HAZARD)
		draw_circle(center + Vector2(16, -10), 7, RED if boss_id == "crimson" else HAZARD)

func _boss_pose_key() -> String:
	# Select boss art frame based on state (not continuous frame-based cycling)
	if boss_id == "crimson":
		match boss_state:
			BossState.IDLE:
				return "crimson_02"  # Red eyes idle
			BossState.REPOSITION:
				return "crimson_02"  # Red eyes idle during movement
			BossState.TELEGRAPH:
				return "crimson_02"  # Red eyes for charge-up
			BossState.LUNGE:
				# Dive or thrust during lunge
				var progress := 1.0 - float(boss_state_timer) / 24.0
				if progress < 0.3:
					return "crimson_01"  # Dive start
				elif progress < 0.7:
					return "crimson_04"  # Thrust mid
				else:
					return "crimson_03"  # Slash instant
	else:  # marysue
		match boss_state:
			BossState.IDLE:
				# Cycle idle @ 12fps when in idle
				return "marysue_%02d" % ((frame / 5) % 3 + 1)
			BossState.REPOSITION:
				return "marysue_01"  # Idle during movement
			BossState.TELEGRAPH:
				return "marysue_02"  # Charge-up
			BossState.LUNGE:
				return "marysue_03"  # Burst
	return "crimson_02"  # Fallback

func _draw_projectiles() -> void:
	# Draw skill warnings (telegraph visual: lines/circles for special moves)
	for warn in skill_warnings:
		if not warn.has("pos"):
			continue
		var p: Vector2 = warn["pos"] - Vector2(camera_x, 0)
		var kind := str(warn.get("kind", "line"))
		var alpha := clampf(float(warn.get("life", 0.0)) * 2.0, 0.0, 1.0) * 0.45
		if kind == "line":
			var dir: Vector2 = warn["dir"]
			draw_line(p, p + dir * 720.0, Color(warn["color"], alpha), 3.0)
		elif kind == "circle":
			var dir: Vector2 = warn["dir"]
			draw_circle(p + dir * 180.0, 12.0, Color(warn["color"], alpha * 0.6))
	
	for warning in warnings:
		var p: Vector2 = warning["pos"] - Vector2(camera_x, 0)
		var dir := Vector2(cos(warning["angle"]), sin(warning["angle"]))
		draw_line(p - dir * 700.0, p + dir * 700.0, Color(WHITE, 0.3), 2.0)
	
	# Player shots: red tapered blade with white core
	for shot in shots:
		var p: Vector2 = shot["pos"] - Vector2(camera_x, 0)
		var d: Vector2 = shot["vel"].normalized()
		var shot_w := 16.0 if tragedy_buff_t > 0.0 else 8.0
		draw_line(p - d * 30.0, p + d * 12.0, Color(RED, 0.3), shot_w)
		draw_line(p - d * 12.0, p + d * 12.0, WHITE, 3.0)
		draw_circle(p, 11.0 if tragedy_buff_t > 0.0 else 5.0, RED)
	
	# Enemy bullets: 程序化绘制（多层辉光 + 白热核心 + 流光条纹），参考 GPT 预览效果
	for bullet in bullets:
		var p: Vector2 = bullet["pos"] - Vector2(camera_x, 0)
		var color: Color = bullet["color"]
		var kind := str(bullet.get("kind", "ring"))
		var angle: float = bullet["angle"]
		var bdir := Vector2(cos(angle), sin(angle))
		var perp := Vector2(-bdir.y, bdir.x)
		# 全局：弹幕拖尾（上一帧位置连线，淡出）
		var trail_p: Vector2 = Vector2(bullet.get("prev_pos", bullet["pos"])) - Vector2(camera_x, 0)
		if trail_p.distance_to(p) > 2.0 and trail_p.distance_to(p) < 160.0:
			draw_line(trail_p, p, Color(color, 0.18), 9.0)
			draw_line(trail_p.lerp(p, 0.4), p, Color(color, 0.30), 5.0)
		# 全局：外圈光晕（所有弹幕都发光）
		draw_circle(p, 26.0, Color(color, 0.06))
		draw_circle(p, 17.0, Color(color, 0.10))
		match kind:
			"blade", "crescent":
				var ln := 78.0 if kind == "blade" else 108.0
				var wd := 13.0 if kind == "blade" else 21.0
				var tip := p + bdir * ln * 0.55
				var back := p - bdir * ln * 0.45
				for g in range(3):
					var gk := 1.0 + float(g) * 0.6
					draw_colored_polygon(PackedVector2Array([
						tip + bdir * 9.0, p + perp * wd * gk * 0.5, back - bdir * 7.0, p - perp * wd * gk * 0.5
					]), Color(color, 0.09 + 0.05 * float(g)))
				draw_colored_polygon(PackedVector2Array([
					tip, p + perp * wd * 0.5, back, p - perp * wd * 0.5
				]), Color(color, 0.92))
				draw_line(back + bdir * 8.0, tip - bdir * 6.0, Color(1, 1, 1, 0.95), wd * 0.34)
				draw_line(back + bdir * 14.0, tip - bdir * 14.0, Color(1, 1, 1, 0.5), wd * 0.13)
				draw_line(back, back - bdir * ln * 1.0, Color(color, 0.26), wd * 0.5)
				continue
			"lance":
				var ll := 100.0
				for g in range(3):
					draw_line(p - bdir * ll * 0.5, p + bdir * ll * 0.5, Color(color, 0.09 + 0.05 * float(g)), 10.0 + float(g) * 7.0)
				draw_line(p - bdir * ll * 0.5, p + bdir * ll * 0.5, Color(color, 0.9), 9.0)
				draw_line(p - bdir * ll * 0.45, p + bdir * ll * 0.5, Color(1, 1, 1, 0.95), 3.4)
				draw_circle(p + bdir * ll * 0.5, 5.0, Color(1, 1, 1, 0.9))
				continue
			"laser", "laser_down", "beam":
				# 参考图：粗壮激光——外辉光 + 主柱 + 白热核心 + 流动条纹 + 枪口光斑
				var lw := 46.0 if kind == "beam" else 26.0
				var llen := 760.0 if kind == "beam" else 420.0
				var la := p - bdir * llen * 0.25
				var lb := p + bdir * llen * 0.75
				if kind == "beam":
					la = Vector2(p.x, 20.0)
					lb = Vector2(p.x, GROUND_Y)
					bdir = Vector2(0, 1)
					llen = lb.y - la.y
				# 外辉光（4 层）
				for g in range(4):
					draw_line(la, lb, Color(color, 0.05 + 0.05 * float(g)), lw * (3.0 - float(g) * 0.5))
				# 主柱（略带锥形感：内层更亮更窄）
				draw_line(la, lb, Color(color, 0.85), lw)
				draw_line(la, lb, Color(color, 0.95), lw * 0.62)
				# 流光：6 道明亮条纹 + 3 个移动光团（明显可见）
				for k2 in range(6):
					var off := fmod(elapsed * 420.0 + float(k2) * (llen / 6.0), llen) - llen * 0.25
					var q := la + bdir * off
					draw_line(q - bdir * 26.0, q + bdir * 26.0, Color(0.72, 1, 0.4, 0.55), lw * 0.42)
					draw_line(q - bdir * 20.0, q + bdir * 20.0, Color(1, 1, 1, 0.85), lw * 0.22)
				for k3 in range(3):
					var off2 := fmod(elapsed * 300.0 + float(k3) * (llen / 3.0), llen) - llen * 0.2
					var q2 := la + bdir * off2
					draw_circle(q2, lw * 0.55, Color(0.72, 1, 0.4, 0.35))
					draw_circle(q2, lw * 0.28, Color(1, 1, 1, 0.8))
				# 波纹：沿光束正弦摆动的亮线（模拟能量流动）
				var perp2 := Vector2(-bdir.y, bdir.x)
				for wv in range(2):
					var pts := PackedVector2Array()
					var steps := 22
					for si in range(steps + 1):
						var t2 := float(si) / float(steps)
						var base := la.lerp(lb, t2)
						var amp := lw * (0.55 + 0.35 * float(wv))
						var ph := elapsed * (9.0 + float(wv) * 3.0) + t2 * 26.0 + float(wv) * 1.7
						pts.append(base + perp2 * sin(ph) * amp * 0.22)
					draw_polyline(pts, Color(1, 1, 1, 0.35 - 0.12 * float(wv)), 2.2)
				# 尾光带：比主柱更宽的柔和光带（缓慢流动）
				var band_off := fmod(elapsed * 160.0, 240.0)
				var band_c := la.lerp(lb, 0.5)
				draw_line(la, lb, Color(color, 0.12), lw * 4.2)
				draw_line(band_c - bdir * band_off * 0.5, band_c + bdir * band_off * 0.5, Color(1, 1, 1, 0.10), lw * 1.8)
				# 白热核心
				draw_line(la, lb, Color(1, 1, 1, 0.98), lw * 0.34)
				# 枪口光斑 + 末端爆点
				draw_circle(la, lw * 0.85, Color(color, 0.35))
				draw_circle(la, lw * 0.45, Color(1, 1, 1, 0.9))
				draw_circle(lb, lw * 0.55, Color(1, 1, 1, 0.75))
				draw_circle(lb, lw * 1.0, Color(color, 0.2))
				continue
			"hazard", "homing", "homing_laser", "flame", "bigorb":
				var rr := 16.0
				if kind == "homing" or kind == "homing_laser":
					rr = 19.0
				elif kind == "flame":
					rr = 18.0
				elif kind == "bigorb":
					rr = 42.0
				draw_circle(p, rr * 2.6, Color(color, 0.09))
				draw_circle(p, rr * 1.75, Color(color, 0.2))
				draw_circle(p, rr * 1.18, Color(color, 0.5))
				draw_circle(p, rr, Color(color, 0.95))
				draw_circle(p, rr * 0.44, Color(1, 1, 1, 0.95))
				draw_circle(p - Vector2(rr * 0.3, rr * 0.3), rr * 0.2, Color(1, 1, 1, 0.85))
				if kind == "flame":
					draw_line(p - bdir * rr, p - bdir * rr * 2.6, Color(color, 0.5), rr * 0.8)
					draw_line(p - bdir * rr * 1.4, p - bdir * rr * 3.2, Color(color, 0.24), rr * 0.4)
				continue
			"talisman", "bounce":
				draw_set_transform(p, angle + PI * 0.5, Vector2(1, 1))
				draw_rect(Rect2(-21.0, -34.0, 42.0, 68.0), Color(color, 0.13))
				draw_rect(Rect2(-13.0, -21.0, 26.0, 42.0), Color(1, 1, 1, 0.95))
				draw_rect(Rect2(-13.0, -21.0, 26.0, 42.0), Color(color, 0.92), false, 2.6)
				for k3 in range(3):
					var lx := -6.0 + float(k3) * 6.0
					draw_line(Vector2(lx, -14.0), Vector2(lx, 14.0), Color(color, 0.85), 1.8)
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
				continue
			"yinyang":
				draw_circle(p, 36.0, Color(color, 0.11))
				draw_circle(p, 26.0, Color(color, 0.92))
				draw_circle(p, 17.5, Color(1, 1, 1, 0.95))
				draw_circle(p + Vector2(0, -8.8), 8.8, Color(color, 0.95))
				draw_circle(p - Vector2(0, 8.8), 8.8, Color(1, 1, 1, 0.98))
				draw_circle(p + Vector2(0, -8.8), 2.8, Color(1, 1, 1, 0.96))
				draw_circle(p - Vector2(0, 8.8), 2.8, Color(color, 0.95))
				continue
			"rain":
				draw_line(p - bdir * 18.0, p + bdir * 24.0, Color(color, 0.9), 7.0)
				draw_line(p - bdir * 20.0, p + bdir * 24.0, Color(1, 1, 1, 0.95), 2.6)
				draw_line(p - bdir * 30.0, p - bdir * 66.0, Color(color, 0.22), 4.0)
				continue
		# 兜底：环形弹
		draw_circle(p, 9.0, Color(color, 0.85))
		draw_circle(p, 4.0, Color(1, 1, 1, 0.9))

func _draw_dash_trail() -> void:
	# Draw dash trail as tapered red polygons (not full character silhouettes)
	var active_dashing := player_dash_frames > 0 or player_dash_out > 0
	if not active_dashing:
		return
	
	for item in trail:
		var pos: Vector2 = item["pos"] - Vector2(camera_x, 0)
		var life_ratio := clampf(float(item["life"]) / float(item["max"]), 0.0, 1.0)
		var alpha_start := life_ratio * 0.34
		var facing: float = item["facing"]
		# Tapered polygon: wide at back, narrow at front (red #FF0000)
		var width_back := 28.0 * life_ratio
		var width_front := 8.0 * life_ratio
		var length := 42.0
		var dir := Vector2(facing, 0)
		var perp := Vector2(0, 1)
		var back := pos - dir * length * 0.5
		var front := pos + dir * length * 0.5
		var points := PackedVector2Array([
			back + perp * width_back,
			back - perp * width_back,
			front - perp * width_front,
			front + perp * width_front
		])
		draw_colored_polygon(points, Color(RED, alpha_start))

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
			draw_arc(pos, radius * 1.32, start, start + 0.85, 20, Color(1, 0.18, 0.18, 0.78), 2.4)
			draw_arc(pos, radius * 1.18, start + 0.3, start + 1.05, 20, Color(1, 1, 1, 0.45), 1.4)
		draw_circle(pos, radius * 0.5, Color(1, 1, 1, 0.92))
		return
	var state: String = character_art.player_state(player_dash_frames, player_dash_out, bool(input_state.get("shoot", false)))
	var aim := (get_viewport().get_mouse_position() - pos - Vector2(0, -80)).normalized() if mouse_seen else Vector2(player_facing, 0)
	
	# Apply jump squash & stretch to character art
	if character_art.draw_player(self, textures, pos + Vector2(0, 20), player_facing, state, aim, tint, jump_squash):
		return
	
	# Fallback procedural player (also apply squash)
	draw_set_transform(pos, 0.0, jump_squash * (Vector2(-1, 1) if mirrored else Vector2.ONE))
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
	# Weapon line removed: was drawing incorrectly as a fixed horizontal line in screenshots
	# draw_line(Vector2(18, -22), Vector2(52, -4), Color(0.9, 0.9, 0.9, tint.a), 5.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_particles_world() -> void:
	for p in particles:
		var alpha := clampf(float(p["life"]) / float(p["max"]), 0.0, 1.0)
		draw_circle(p["pos"] - Vector2(camera_x, 0), float(p["size"]) * alpha, Color(p["color"], alpha))

func _draw_hud() -> void:
	var color := RED if boss_id == "crimson" else HAZARD
	draw_string(ThemeDB.fallback_font, Vector2(32, 36), "MIRROR // BATTLE", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, GREY)
	# Boss HUD: name / health bar / stage label stacked with >= 6px spacing
	draw_string(ThemeDB.fallback_font, Vector2(890, 36), "猩红魔姬·雷帝" if boss_id == "crimson" else "黑童话之母·玛丽苏", HORIZONTAL_ALIGNMENT_LEFT, -1, 19, color)
	# Health bar: y=58 (36 + 19 line height ~22, leave 6px gap)
	draw_rect(Rect2(820, 58, 400, 16), Color(0.08, 0.08, 0.08, 1))
	draw_rect(Rect2(820, 58, 400 * boss_hp / boss_max_hp, 16), color)
	# Stage label: y=90 (58 + 16 bar + 6px gap)
	var stage_label := "STAGE %d / %d" % [boss_phase + 1, boss_phase_count] if boss_id == "crimson" else "STAGE %d" % (boss_phase + 1)
	draw_string(ThemeDB.fallback_font, Vector2(890, 90), stage_label, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, GREY)
	# 阶段名（血条下方，用户要求）
	var pnames: Array = PHASE_NAMES.get(boss_id, [])
	if boss_phase < pnames.size():
		draw_string(ThemeDB.fallback_font, Vector2(1060, 92), str(pnames[boss_phase]), HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(RED if boss_id == "crimson" else HAZARD))
	draw_string(ThemeDB.fallback_font, Vector2(40, 650), "HP", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, GREY)
	# 血量图标：小镜子（完整的亮、破损的暗且带裂纹）
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
			draw_line(mir + Vector2(1, 2), mir + Vector2(7, -6), Color(0.8, 0.8, 0.8, 0.45), 1.0)
	# Stamina bar: below courage bar (lower left area), thin bar
	# Base: neutral gray; Fill: cyan #00BAFF; < 7: red #FF0000
	draw_string(ThemeDB.fallback_font, Vector2(40, 675), "体力", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, GREY)
	draw_rect(Rect2(78, 665, 140, 10), Color(0.4, 0.4, 0.4, 1))  # Base: neutral gray
	var stamina_fill_ratio := clampf(player_stamina_display / 100.0, 0.0, 1.0)
	var stamina_color := Color("#FF0000") if player_stamina < 7.0 else Color("#00BAFF")  # Red when < 7, cyan otherwise
	draw_rect(Rect2(78, 665, 140 * stamina_fill_ratio, 10), stamina_color)
	# Optional: display stamina number
	draw_string(ThemeDB.fallback_font, Vector2(226, 675), "%d" % int(player_stamina), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, WHITE)
	# Courage bar
	draw_string(ThemeDB.fallback_font, Vector2(280, 675), "勇气 %03d" % int(player_courage), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, WHITE)
	# ---- 能量条（血条旁边）----
	draw_string(ThemeDB.fallback_font, Vector2(400, 675), "MP", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, WHITE)
	draw_rect(Rect2(442, 665, 160, 10), Color(0.35, 0.35, 0.35, 1))
	var e_ratio := clampf(player_energy / ENERGY_MAX, 0.0, 1.0)
	var e_color := Color("#FF0000") if player_energy >= 2.0 else Color("#8a2a2a")
	draw_rect(Rect2(442, 665, 160 * e_ratio, 10), e_color)
	for seg in range(1, int(ENERGY_MAX)):
		var sx := 442.0 + 160.0 * float(seg) / ENERGY_MAX
		draw_line(Vector2(sx, 663), Vector2(sx, 677), Color(0, 0, 0, 0.75), 2.0)
	if energy_flash > 0:
		draw_rect(Rect2(442, 663, 160, 14), Color(1, 1, 1, 0.25 * float(energy_flash) / 8.0))
		energy_flash -= 1
	# ---- 技能图标（血条旁边，标注能量与按键）----
	var slots: Array = []
	if skill_red_tragedy:
		slots.append({"tex": "skill_icon_red", "cost": 2, "key": "L", "name": "红之惨剧"})
	slots.append({"tex": "skill_icon_gun", "cost": 2, "key": "C", "name": "枪火击溃"})
	slots.append({"tex": "skill_icon_hell", "cost": 2, "key": "V", "name": "业火"})
	var sx0 := 620.0
	for si in range(slots.size()):
		var slot: Dictionary = slots[si]
		var rect := Rect2(sx0 + float(si) * 68.0, 632, 60, 60)
		var can := player_energy >= float(slot["cost"])
		var pulse := 0.5 + 0.5 * sin(elapsed * 4.0 + float(si))
		# 外框：可用时白边+红晕，不可用时暗灰
		draw_rect(rect, Color(0.04, 0.04, 0.05, 0.9))
		if can:
			draw_rect(Rect2(rect.position - Vector2(2, 2), rect.size + Vector2(4, 4)), Color(1, 0, 0, 0.25 + 0.15 * pulse), false, 3.0)
		draw_rect(rect, Color(1, 1, 1, 0.55 if can else 0.16), false, 2.0)
		var itex: Texture2D = textures.get(slot["tex"])
		if itex:
			var pad := 6.0
			draw_texture_rect(itex, Rect2(rect.position + Vector2(pad, pad), rect.size - Vector2(pad * 2, pad * 2)), false,
				Color(1, 1, 1, 1.0 if can else 0.28))
		# 能量消耗徽章（左下）
		var cbadge := Rect2(rect.position + Vector2(2, rect.size.y - 18), Vector2(20, 16))
		draw_rect(cbadge, Color(0, 0, 0, 0.8))
		draw_string(ThemeDB.fallback_font, cbadge.position + Vector2(4, 13), str(slot["cost"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13,
			Color(1, 0.25, 0.25) if can else GREY)
		# 按键徽章（右上）
		var kbadge := Rect2(rect.position + Vector2(rect.size.x - 20, 2), Vector2(18, 16))
		draw_rect(kbadge, Color(0, 0, 0, 0.8))
		draw_string(ThemeDB.fallback_font, kbadge.position + Vector2(5, 13), str(slot["key"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13,
			WHITE if can else GREY)
		# 技能说明（格下方小字）
		var desc: String = str({"skill_icon_red": "回2HP + 20秒强化剑气"}.get(slot["tex"], ""))
		if desc != "":
			draw_string(ThemeDB.fallback_font, rect.position + Vector2(0, rect.size.y + 26), desc, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.8, 0.8, 0.8))
		# 技能名（格下方小字）
		draw_string(ThemeDB.fallback_font, rect.position + Vector2(0, rect.size.y + 13), str(slot["name"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 12,
			Color(1, 0.4, 0.4) if can else GREY)
	draw_string(ThemeDB.fallback_font, Vector2(880, 675), "冲刺 %s" % ("READY" if player_dash_cd <= 0 else "%02d" % player_dash_cd), HORIZONTAL_ALIGNMENT_LEFT, -1, 14, RED if player_dash_cd <= 0 else GREY)
	draw_string(ThemeDB.fallback_font, Vector2(1040, 675), "擦弹链 %d" % player_graze_chain, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, WHITE)
	if banner_timer > 0 and banner != "":
		draw_string(ThemeDB.fallback_font, Vector2(510, 340), banner, HORIZONTAL_ALIGNMENT_LEFT, -1, 34, WHITE)
	if paused:
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.62))
		draw_string(ThemeDB.fallback_font, Vector2(556, 250), "PAUSED", HORIZONTAL_ALIGNMENT_LEFT, -1, 40, WHITE)
		# 继续游戏（点击或按 Enter）
		var resume_rect := Rect2(500, 300, 280, 56)
		var hover_resume := resume_rect.has_point(get_local_mouse_position())
		draw_rect(resume_rect, Color(0.08, 0.08, 0.10, 0.95))
		draw_rect(resume_rect, Color(1, 1, 1, 0.85 if hover_resume else 0.5), false, 2.0)
		draw_string(ThemeDB.fallback_font, Vector2(548, 336), "继续游戏  (ENTER / 鼠标左键)", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, WHITE)
		# 回标题
		var title_rect := Rect2(500, 372, 280, 48)
		var hover_title := title_rect.has_point(get_local_mouse_position())
		draw_rect(title_rect, Color(0.08, 0.08, 0.10, 0.95))
		draw_rect(title_rect, Color(1, 0.3, 0.3, 0.85 if hover_title else 0.45), false, 2.0)
		draw_string(ThemeDB.fallback_font, Vector2(556, 402), "回到标题  (R)", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(1, 0.6, 0.6))
		if hover_resume and _mouse_clicked():
			paused = false
		elif hover_title and _mouse_clicked():
			mode = Mode.TITLE
			paused = false
			_stop_music()
			_stop_battle_bgm()

func _draw_victory() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.46))
	draw_string(ThemeDB.fallback_font, Vector2(420, 300), "猩红魔姬 · 破" if boss_id == "crimson" else "镜界静默", HORIZONTAL_ALIGNMENT_LEFT, -1, 42, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(410, 370), "ENTER / SPACE 继续剧情", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, CYAN)

func _draw_end() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.78))
	draw_string(ThemeDB.fallback_font, Vector2(300, 300), "THANKS FOR PLAYING", HORIZONTAL_ALIGNMENT_LEFT, -1, 46, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(330, 372), "红之镜 · DEMO", HORIZONTAL_ALIGNMENT_LEFT, -1, 26, RED)
	draw_string(ThemeDB.fallback_font, Vector2(352, 418), "镜面碎成了千万片，每一片里都有她", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(0.85, 0.85, 0.85))
	draw_string(ThemeDB.fallback_font, Vector2(430, 540), "感谢试玩", HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(0.6, 0.6, 0.6))

func _draw_fx_overlay() -> void:
	# Draw mirror shards ONLY when fade/flash are not blocking (no blackout)
	var fade_blocking := (mode == Mode.STORY and story_fade > 0.02)
	var flash_blocking := (mode == Mode.STORY and not story_flash_seq.is_empty())
	if not fade_blocking and not flash_blocking:
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
	
	# Draw dash screen FX (white edge flash, 4 frames)
	if dash_screen_fx > 0:
		var alpha_seq := [0.10, 0.075, 0.045, 0.015]
		var idx := 4 - dash_screen_fx
		if idx >= 0 and idx < alpha_seq.size():
			var alpha: float = alpha_seq[idx]
			var margin := 64.0
			# Top/bottom edge bars
			draw_rect(Rect2(0, 0, VIEW.x, margin), Color(WHITE, alpha))
			draw_rect(Rect2(0, VIEW.y - margin, VIEW.x, margin), Color(WHITE, alpha))
			# Left/right edge bars
			draw_rect(Rect2(0, 0, margin, VIEW.y), Color(WHITE, alpha))
			draw_rect(Rect2(VIEW.x - margin, 0, margin, VIEW.y), Color(WHITE, alpha))

## Start dash FX: trigger screen flash and initial burst
func _start_dash_fx() -> void:
	dash_fx_active = true
	dash_screen_fx = 0  # 用户要求：冲刺不要闪屏
	sfx_player.play("dash")
	# Burst: 8 red + 1 white center dot
	for i in range(8):
		var angle := TAU * float(i) / 8.0 + randf_range(-0.18, 0.18)
		var dir := Vector2(cos(angle), sin(angle))
		var speed := randf_range(40.0, 130.0)
		dash_dots.append({
			"pos": player_pos,
			"vel": dir * speed,
			"life": randf_range(10.0, 16.0) / 60.0,
			"max_life": 16.0 / 60.0,
			"radius": randf_range(1.5, 3.0),
			"color": RED
		})

## Update dash FX every frame during dash
func _update_dash_fx() -> void:
	if dash_screen_fx > 0:
		dash_screen_fx -= 1
	
	var active := player_dash_frames > 0 or player_dash_out > 0
	if not active:
		dash_fx_active = false
	
	if not dash_fx_active:
		return
	
	var speed_ratio := clampf(absf(player_vel.x) / 1020.0, 0.0, 1.0)
	var back_dir := Vector2(-signf(player_vel.x), 0) if absf(player_vel.x) > 10.0 else Vector2(-player_dash_direction, 0)
	
	# Speed lines: 1 per frame (reduced from 2 to prevent foot-level bar artifacts)
	# Offset tightened to ±3px to avoid vertical clustering
	var length := lerpf(18.0, 72.0, speed_ratio)
	var width := lerpf(1.5, 2.5, speed_ratio)  # Reduced from 2.0-3.5 to prevent thick overlaps
	var offset := randf_range(-3.0, 3.0)  # Tightened from ±7 to ±3
	var start := player_pos + Vector2(0, offset)
	dash_speed_lines.append({
		"pos": start,
		"vel": back_dir * length,
		"life": 3.0 / 60.0,
		"max_life": 3.0 / 60.0,
		"width": width
	})
	
	# Light dots: 1 per frame during dash
	if frame % 2 == 0 and dash_dots.size() < 32:
		var angle := back_dir.angle() + randf_range(-0.5, 0.5)
		var dir := Vector2(cos(angle), sin(angle))
		dash_dots.append({
			"pos": player_pos,
			"vel": dir * randf_range(40.0, 80.0),
			"life": randf_range(10.0, 16.0) / 60.0,
			"max_life": 16.0 / 60.0,
			"radius": randf_range(1.5, 3.0),
			"color": RED
		})
	
	# Update speed lines
	for line in dash_speed_lines:
		line["life"] = float(line["life"]) - FIXED_DT
	dash_speed_lines = dash_speed_lines.filter(func(l): return float(l.get("life", 0.0)) > 0.0)
	
	# Update dash dots
	for dot in dash_dots:
		dot["pos"] += dot["vel"] * FIXED_DT
		dot["life"] = float(dot["life"]) - FIXED_DT
	dash_dots = dash_dots.filter(func(d): return float(d.get("life", 0.0)) > 0.0)

## Draw dash FX (speed lines + dots) before player
func _draw_dash_fx() -> void:
	# Speed lines: white, additive
	for line in dash_speed_lines:
		var progress := 1.0 - float(line["life"]) / float(line["max_life"])
		var alpha := 0.62 * pow(1.0 - progress, 0.75)
		var start: Vector2 = line["pos"] - Vector2(camera_x, 0)
		var vel: Vector2 = line["vel"]
		# Safety: skip lines with abnormal length (prevent bar artifacts)
		if vel.length() > 100.0:
			continue
		var end: Vector2 = start + vel
		draw_line(start, end, Color(WHITE, alpha), line["width"], true)
	
	# Dash dots: red, additive
	for dot in dash_dots:
		var progress := 1.0 - float(dot["life"]) / float(dot["max_life"])
		var alpha := 1.0 - progress
		var radius := float(dot["radius"]) * (1.0 - 0.45 * progress)
		var p: Vector2 = dot["pos"] - Vector2(camera_x, 0)
		draw_circle(p, radius, Color(dot["color"], alpha))

## Spawn walk dust particle
func _spawn_walk_dust() -> void:
	var back := player_pos + Vector2(-player_facing * 12.0, 16.0)
	var vel := Vector2(-player_facing * randf_range(20.0, 40.0), randf_range(-10.0, 0.0))
	walk_dust.append({
		"pos": back,
		"vel": vel,
		"life": randf_range(10.0, 16.0) / 60.0,
		"max_life": 16.0 / 60.0,
		"alpha": 0.35,
		"radius": randf_range(1.5, 3.0)
	})

## Draw walk dust particles
func _draw_walk_dust() -> void:
	for dust in walk_dust:
		var p: Vector2 = dust["pos"] - Vector2(camera_x, 0)
		var radius: float = dust.get("radius", 2.0)
		# Safety: skip dust with abnormal radius (prevent bar artifacts)
		if radius > 4.0:
			continue
		draw_circle(p, radius, Color(GREY, dust["alpha"]))

## Trigger jump squash & stretch animation
func _trigger_jump_squash(phase: String) -> void:
	match phase:
		"prejump":
			jump_squash_timer = 2
			jump_squash = Vector2(1.10, 0.88)
		"jump":
			jump_squash_timer = 3
			jump_squash = Vector2(0.94, 1.10)
		"land":
			jump_squash_timer = 4
			jump_squash = Vector2(1.12, 0.84)

func _update_jump_squash() -> void:
	# Lerp back to Vector2.ONE over remaining frames
	var t := 1.0 / float(maxi(1, jump_squash_timer))
	jump_squash = jump_squash.lerp(Vector2.ONE, t)

## Trigger land event
func _trigger_land() -> void:
	_trigger_jump_squash("land")
	# Land SFX with minimum 12-frame interval
	if frame - last_land_frame >= 12:
		sfx_player.play("land")
		last_land_frame = frame

## Update NPC interaction glow (walk mode only)
func _update_npc_glow() -> void:
	if mode != Mode.WALK or walk_target.size() == 0:
		npc_glow_target = 0.0
	else:
		var target_x := float(walk_target.get("x", player_pos.x))
		var distance := absf(player_pos.x - target_x)
		npc_glow_target = 1.0 if distance < 110.0 else 0.0
	
	# Smooth transition: 8 frames fade-in, 12 frames fade-out
	var speed := (1.0 / 8.0) if npc_glow_target > npc_glow_alpha else (1.0 / 12.0)
	npc_glow_alpha = move_toward(npc_glow_alpha, npc_glow_target, speed)

## Draw NPC glow (breathing radial gradient)
func _draw_npc_glow(foot: Vector2, height: float) -> void:
	if npc_glow_alpha <= 0.01:
		return
	var breathe := 1.0 + sin(elapsed * 0.8 * TAU) * 0.15
	var base_alpha: float = lerpf(0.18, 0.25, (breathe + 1.0) * 0.5) * npc_glow_alpha
	var center := foot - Vector2(0, height * 0.5)
	var radius := height * 0.62 * breathe
	# Draw radial gradient as concentric circles (simple approximation)
	for i in range(6, 0, -1):
		var r := radius * float(i) / 6.0
		var a: float = base_alpha * (1.0 - float(i - 1) / 6.0) * 0.5
		draw_circle(center, r, Color(CYAN, a))


# 魔姬：横向激光扫射（预警 30 帧 → 三束激光）
func _crimson_laser_sweep() -> void:
	if boss_skill_state == "":
		boss_skill_state = "telegraph"
		boss_skill_timer = 30
		var dir := (player_pos - boss_pos).normalized()
		skill_warnings.clear()
		for i in range(3):
			var off := (float(i) - 1.0) * 0.12
			var d2 := Vector2(cos(dir.angle() + off), sin(dir.angle() + off))
			skill_warnings.append({"kind": "line", "pos": boss_pos, "dir": d2, "life": 30.0 / 60.0, "color": RED})
	elif boss_skill_state == "telegraph":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = "firing"
			boss_skill_timer = 26
			for w in skill_warnings:
				_spawn_bullet(boss_pos, w["dir"] * 780.0, RED, "laser")
	elif boss_skill_state == "firing":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			skill_warnings.clear()

# 玛丽苏：翡翠贯射（预警 36 帧 → 5 束绿色激光扇形）
func _marysue_laser_beam() -> void:
	if boss_skill_state == "":
		boss_skill_state = "telegraph"
		boss_skill_timer = 36
		var dir := (player_pos - boss_pos).normalized()
		skill_warnings.clear()
		for i in range(5):
			var off := (float(i) - 2.0) * 0.09
			var d2 := Vector2(cos(dir.angle() + off), sin(dir.angle() + off))
			skill_warnings.append({"kind": "line", "pos": boss_pos, "dir": d2, "life": 36.0 / 60.0, "color": HAZARD})
	elif boss_skill_state == "telegraph":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = "firing"
			boss_skill_timer = 30
			for w in skill_warnings:
				_spawn_bullet(boss_pos, w["dir"] * 700.0, HAZARD, "laser")
	elif boss_skill_state == "firing":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = ""
			skill_warnings.clear()


# ======================= 新 Boss 招式体系 =======================

func _patterns_crimson() -> void:
	# 参考用户截图：满屏火焰弹（弱追踪、会自动消散）、落地追击斩、新月剑气
	match boss_phase:
		0:  # 一：火焰弹幕（弱追踪，3 秒后消散）
			if frame % 150 == 0:
				# 环形剑阵：先收缩再向外炸开
				for k in range(14):
					var a0 := TAU * float(k) / 14.0 + elapsed * 0.4
					_spawn_bullet(boss_pos + Vector2(cos(a0), sin(a0)) * 30.0,
						Vector2(cos(a0), sin(a0)) * 180.0, RED, "blade", 3.2, 0.0)
				_spawn_fx_ring(boss_pos, Color(1, 0.3, 0.2, 0.85), 220.0, 0.4, 4.0)
			if frame % 18 == 0:
				for k in range(2):
					var a := (player_pos - boss_pos).angle() + randf_range(-0.55, 0.55)
					_spawn_bullet(boss_pos + Vector2(randf_range(-16, 16), randf_range(-16, 16)),
						Vector2(cos(a), sin(a)) * randf_range(170.0, 260.0), RED, "flame", 3.0, 0.05)
			if frame % 150 == 0:
				for k in range(8):
					var a2 := TAU * float(k) / 10.0 + elapsed
					_spawn_bullet(boss_pos, Vector2(cos(a2), sin(a2)) * 210.0, RED, "flame", 3.4, 0.03)
		1:  # 二：落地追击斩 + 火焰弹
			_crimson_rush_attack(true)
		2:  # 三：落地追击斩 + 新月剑气 + 双旋风
			_spawn_two_whirls()
			_crimson_rush_attack(false)
			if boss_skill_state == "" and frame % 52 == 0:
				_crimson_crescent_volley(1)
		3:  # 四：地刺追击 + 火焰弹雨 + 新月剑气 + 双旋风 + 追踪火球
			if frame % 100 == 0:
				for k in range(3):
					_spawn_bullet(boss_pos, Vector2(randf_range(-1, 1), randf_range(-0.4, 0.4)).normalized() * 190.0, RED, "flame", 5.0, 0.5)
			_spawn_two_whirls()
			if frame % 90 == 0:
				for k in range(2):
					var sx0 := player_pos.x + (float(k) - 0.5) * 220.0
					spikes.append({"pos": Vector2(clampf(sx0, _battle_left() + 70.0, _battle_right() - 70.0), GROUND_Y - 20.0), "life": 0.5, "max": 0.5})
				sfx_player.play("spike")
			_crimson_rush_attack(false)
			if frame % 16 == 0:
				var rx := 150.0 + randf() * 2100.0
				_spawn_bullet(Vector2(rx, 40.0), Vector2(0, 260.0), RED, "flame", 4.0, 0.02)
			if frame % 80 == 0:
				_crimson_crescent_volley(2)
		4:  # 五：高频追击斩 + 火焰弹幕 + 锁定突刺锋 + 双旋风 + 落雷
			if frame % 120 == 0:
				for k in range(2):
					var lxr := clampf(player_pos.x + (float(k) - 0.5) * 280.0, _battle_left() + 80.0, _battle_right() - 80.0)
					_beam_warning_crimson(lxr)
			_spawn_two_whirls()
			_crimson_rush_attack(true)
			if frame % 12 == 0:
				for k in range(2):
					var a5 := (player_pos - boss_pos).angle() + randf_range(-0.4, 0.4)
					_spawn_bullet(boss_pos, Vector2(cos(a5), sin(a5)) * 240.0, RED, "flame", 2.8, 0.06)
			if lock_state == "" and lock_cooldown <= 0:
				lock_state = "aim"
				lock_timer = 0.5
				lock_target = player_pos
				lock_cooldown = 120
				sfx_player.play("lock_beep")

func _crimson_crescent_volley(count: int) -> void:
	var dir := (player_pos - boss_pos).normalized()
	for k in range(count):
		var off := (float(k) - float(count - 1) * 0.5) * 0.16
		var d := Vector2(cos(dir.angle() + off), sin(dir.angle() + off))
		_spawn_bullet(boss_pos + d * 40.0, d * 520.0, RED, "blade", 2.6, 0.0)
	_spawn_fx_ring(boss_pos, Color(1, 0.3, 0.3, 0.8), 120.0, 0.3, 3.0)

## 落地追击斩：先落到地面（带拖尾），再沿地面追击小红帽，落地后放新月剑气
func _crimson_rush_attack(finish_crescent: bool) -> void:
	if boss_skill_state == "":
		boss_skill_state = "leap"
		boss_skill_timer = 40
		boss_rush_side = signf(player_pos.x - boss_pos.x)
		_spawn_fx_ring(boss_pos, Color(1, 0, 0, 0.7), 90.0, 0.25, 3.0)
	elif boss_skill_state == "leap":
		boss_skill_timer -= 1
		boss_pos.y = lerpf(boss_pos.y, 420.0, 0.10)
		if boss_skill_timer <= 0:
			boss_skill_state = "rush"
			boss_skill_timer = 34
			sfx_player.play("skill")
	elif boss_skill_state == "rush":
		boss_skill_timer -= 1
		# 追着小红帽砍：向玩家方向加速冲
		var target_x: float = player_pos.x - boss_rush_side * 60.0
		boss_pos.x = move_toward(boss_pos.x, target_x, 9.0)
		boss_pos.y = move_toward(boss_pos.y, 420.0, 300.0 * FIXED_DT)
		# 冲刺拖尾（帅气）
		for k in range(2):
			_spawn_particle(Vector2(boss_pos.x - boss_rush_side * (20.0 + float(k) * 26.0), boss_pos.y - 30.0 + randf_range(-20, 20)),
				Color(1, 0.15, 0.15, 0.85), 0.28, Vector2(-boss_rush_side * 260.0, randf_range(-30, 30)), 7.0)
		if frame % 14 == 0:
			var d := (player_pos - boss_pos).normalized()
			_spawn_bullet(boss_pos + d * 30.0, d * 620.0, RED, "crescent", 2.2, 0.0)
		if boss_skill_timer <= 0:
			boss_skill_state = "land"
			boss_skill_timer = 14
			_spawn_fx_ring(Vector2(boss_pos.x, GROUND_Y - 10.0), Color(1, 0.35, 0.35, 0.9), 200.0, 0.35, 5.0)
			_spawn_burst(Vector2(boss_pos.x, GROUND_Y - 10.0), Color(1, 0.6, 0.4), 14)
			if finish_crescent:
				_crimson_crescent_volley(3)
	elif boss_skill_state == "land":
		boss_skill_timer -= 1
		if boss_skill_timer <= 0:
			boss_skill_state = ""

func _patterns_marysue() -> void:
	# 重做：符纸环 + 阴阳球 + 激光，全部有预警、低频率、可躲
	match boss_phase:
		0:  # 壹 · 箱庭：绿色符纸环 + 螺旋光轮
			if frame % 90 == 0:
				for k in range(10):
					var sp_a := float(k) * 0.62 + elapsed * 2.2
					_spawn_bullet(boss_pos, Vector2(cos(sp_a), sin(sp_a)) * (120.0 + float(k) * 14.0), HAZARD, "yinyang", 5.5, 0.15)
			
			if frame % 40 == 0:
				for k in range(10):
					var a := TAU * float(k) / 10.0 + elapsed * 0.5
					_spawn_bullet(boss_pos, Vector2(cos(a), sin(a)) * 150.0, HAZARD, "talisman", 5.0, 0.02)
			if frame % 75 == 0:
				for k in range(6):
					var a_s := TAU * float(k) / 6.0 - elapsed * 0.8
					_spawn_bullet(boss_pos, Vector2(cos(a_s), sin(a_s)) * 190.0, HAZARD, "yinyang", 5.0, 0.15)
		1:  # 贰 · 反语：阴阳球缓慢旋转外扩
			if frame % 45 == 0:
				for k in range(8):
					var a2 := -TAU * float(k) / 8.0 + elapsed * 0.9
					_spawn_bullet(boss_pos, Vector2(cos(a2), sin(a2)) * 170.0, HAZARD, "yinyang", 5.5, 0.25)
		2:  # 叁 · 镜廊：符纸雨 + 阴阳球 + 箱庭囚笼
			if frame % 160 == 0:
				var gap := randf_range(0.0, TAU)
				var ccx := clampf(player_pos.x, _battle_left() + 120.0, _battle_right() - 120.0)
				for k in range(16):
					var ca := TAU * float(k) / 16.0
					if absf(wrapf(ca - gap, -PI, PI)) < 0.55:
						continue   # 留一个缺口
					_spawn_bullet(Vector2(ccx + cos(ca) * 210.0, GROUND_Y - 150.0 + sin(ca) * 120.0),
						Vector2(-cos(ca), -sin(ca)) * 60.0, HAZARD, "talisman", 4.5, 0.0)
				_spawn_fx_ring(Vector2(ccx, GROUND_Y - 150.0), Color(0.51, 1, 0, 0.6), 240.0, 0.4, 3.0)
			
			if frame % 200 == 0:
				var lx0 := clampf(player_pos.x + randf_range(-200.0, 200.0), _battle_left() + 90.0, _battle_right() - 90.0)
				_beam_warning(lx0)
			if frame % 34 == 0:
				_spawn_bullet(Vector2(randf_range(_battle_left() + 60.0, _battle_right() - 60.0), 60.0),
					Vector2(0, 210.0), HAZARD, "talisman", 5.0, 0.0)
			if frame % 90 == 0:
				for k in range(5):
					var a3 := -PI * 0.5 + (float(k) - 2.0) * 0.28
					_spawn_bullet(boss_pos, Vector2(cos(a3), sin(a3)) * 200.0, HAZARD, "yinyang", 5.0, 0.3)
		3:  # 肆 · 断线：预警激光 + 镜面反弹符纸
			if frame % 110 == 0:
				for k in range(4):
					var ba := randf_range(0.0, TAU)
					_spawn_bullet(boss_pos, Vector2(cos(ba), sin(ba)) * 240.0, HAZARD, "bounce", 6.0, 0.0)
			# 预警激光：先亮线 0.6 秒，再落柱；落在玩家侧前方，不贴脸
			if boss_skill_state == "" and frame % 120 == 0:
				boss_skill_state = "telegraph"
				boss_skill_timer = 36
				skill_warnings.clear()
				for k in range(2):
					var off := (float(k) - 0.5) * 320.0
					var lx := clampf(player_pos.x + off, _battle_left() + 80.0, _battle_right() - 80.0)
					skill_warnings.append({"kind": "beam", "x": lx, "life": 0.6, "color": HAZARD})
			elif boss_skill_state == "telegraph":
				boss_skill_timer -= 1
				if boss_skill_timer <= 0:
					boss_skill_state = ""
					for w in skill_warnings:
						_spawn_beam(float(w["x"]), 0.9)
					skill_warnings.clear()
		4:  # 伍 · 狂言：绿闪 + 符纸环（无激光）
			if flash_green_t <= 0.0 and frame % 180 == 0:
				flash_green_t = 2.2
			if frame % 70 == 0:
				for k in range(10):
					var a5 := TAU * float(k) / 10.0 + elapsed
					_spawn_bullet(boss_pos, Vector2(cos(a5), sin(a5)) * 160.0, HAZARD, "talisman", 5.0, 0.02)
		5:  # 陆 · 天地倒悬：镜像翻转 + 阴阳球 + 符纸
			if not mirror_flip:
				mirror_flip = true
			if frame % 55 == 0:
				for k in range(8):
					var a6 := TAU * float(k) / 8.0 + elapsed * 1.3
					_spawn_bullet(boss_pos, Vector2(cos(a6), sin(a6)) * 165.0, HAZARD, "yinyang", 5.5, 0.2)
			if frame % 220 == 0:
				var lx1 := clampf(player_pos.x + randf_range(-160.0, 160.0), _battle_left() + 90.0, _battle_right() - 90.0)
				_beam_warning(lx1)
			if frame % 130 == 0:
				# 虚空裂隙：连续三道错开的激光
				for k in range(3):
					var vx := clampf(player_pos.x + (float(k) - 1.0) * 260.0, _battle_left() + 90.0, _battle_right() - 90.0)
					_beam_warning(vx)
			if frame % 34 == 0:
				for k in range(6):
					var a7 := TAU * float(k) / 6.0 - elapsed
					_spawn_bullet(boss_pos, Vector2(cos(a7), sin(a7)) * 140.0, HAZARD, "talisman", 5.0, 0.02)

func _spawn_two_whirls() -> void:
	if whirls.size() >= 2:
		return
	var base := clampf(player_pos.x, 300.0, 2100.0)
	whirls = [{"x": base - 320.0, "phase": 0.0, "mode": "chase", "dir": 1.0},
			   {"x": base + 320.0, "phase": 1.7, "mode": "sweep", "dir": 1.0}]

func _update_boss_extras() -> void:
	# 旋风：转动 + 碰撞（贴地才伤害，带无敌帧判定）
	for w in whirls:
		w["phase"] = float(w.get("phase", 0.0)) + FIXED_DT * 3.0
		# 移动：一个慢慢追玩家，一个在地上左右来回扫
		if str(w.get("mode", "chase")) == "chase":
			var to_x: float = player_pos.x - float(w["x"])
			w["x"] = float(w["x"]) + signf(to_x) * minf(absf(to_x), 38.0 * FIXED_DT)
		else:
			w["x"] = float(w["x"]) + float(w.get("dir", 1.0)) * 30.0 * FIXED_DT
			if float(w["x"]) < 200.0:
				w["dir"] = 1.0
			if float(w["x"]) > WORLD_W - 200.0:
				w["dir"] = -1.0
		var dx: float = absf(player_pos.x - float(w["x"]))
		if dx < 62.0 and player_grounded and player_hurt_invuln <= 0 and player_dash_invuln <= 0 and not player_ball:
			# 中心核心伤害（冲刺有无敌帧，可以穿过去）
			player_vel.x = signf(player_pos.x - float(w["x"])) * 420.0
			_apply_player_damage()
	# 锁定突刺锋
	if lock_cooldown > 0:
		lock_cooldown -= 1
	if lock_state == "aim":
		lock_timer -= FIXED_DT
		if lock_timer <= 0.0:
			lock_state = "spike"
			lock_timer = 0.5
			spikes.append({"pos": lock_target, "life": 0.5, "max": 0.5})
			sfx_player.play("spike")
	elif lock_state == "spike":
		lock_timer -= FIXED_DT
		if lock_timer <= 0.0:
			lock_state = ""
	# 突刺锋伤害 + 淡出
	for sp in spikes:
		sp["life"] = float(sp["life"]) - FIXED_DT
		var d: float = Vector2(sp["pos"]).distance_to(Vector2(player_pos.x, GROUND_Y - 20.0))
		if d < 46.0:
			_apply_player_damage()
	spikes = spikes.filter(func(x): return float(x.get("life", 0.0)) > 0.0)
	# 绿闪衰减
	if green_flash_t > 0.0:
		green_flash_t = maxf(0.0, green_flash_t - FIXED_DT)
	if flash_green_t > 0.0:
		flash_green_t = maxf(0.0, flash_green_t - FIXED_DT)

func _draw_boss_extras() -> void:
	# 刀光弹/激光拖尾
	for b in bullets:
		var kind := str(b.get("kind", ""))
		if kind != "blade" and kind != "lance" and kind != "laser":
			continue
		var pv: Vector2 = Vector2(b.get("prev_pos", b["pos"])) - Vector2(camera_x, 0)
		var pn: Vector2 = Vector2(b["pos"]) - Vector2(camera_x, 0)
		if pv.distance_to(pn) < 60.0:
			var col: Color = b["color"]
			col.a = 0.28
			draw_line(pv, pn, col, 6.0)
	var cam := Vector2(camera_x, 0.0)
	# 地面旋风
	for w in whirls:
		var wx: float = float(w["x"]) - camera_x
		var ph: float = float(w["phase"])
		for k in range(5):
			var rr := 30.0 + float(k) * 16.0
			draw_arc(Vector2(wx, GROUND_Y - 26.0 - float(k) * 16.0), rr, ph + float(k), ph + float(k) + PI * 1.3, 18, Color(1, 0, 0, 0.55 - float(k) * 0.1), 3.0)
		draw_circle(Vector2(wx, GROUND_Y - 12.0), 62.0, Color(1, 0, 0, 0.15))
	# 锁定瞄准特效
	if lock_state == "aim":
		var t := Vector2(lock_target.x - camera_x, lock_target.y)
		var blink := 0.5 + 0.5 * sin(elapsed * 30.0)
		draw_arc(t, 34.0, 0, TAU, 40, Color(1, 0, 0, 0.5 + 0.4 * blink), 2.5)
		draw_line(t + Vector2(-46, 0), t + Vector2(-24, 0), Color(1, 0, 0, 0.9), 2.0)
		draw_line(t + Vector2(24, 0), t + Vector2(46, 0), Color(1, 0, 0, 0.9), 2.0)
		draw_line(t + Vector2(0, -46), t + Vector2(0, -24), Color(1, 0, 0, 0.9), 2.0)
		draw_line(t + Vector2(0, 24), t + Vector2(0, 46), Color(1, 0, 0, 0.9), 2.0)
	# 突刺锋（地面刀锋）
	for sp in spikes:
		var a: float = clampf(float(sp["life"]) / maxf(0.01, float(sp["max"])), 0.0, 1.0)
		var bx: float = float(sp["pos"].x) - camera_x
		var top := Vector2(bx, GROUND_Y - 150.0 * a)
		draw_colored_polygon(PackedVector2Array([top, Vector2(bx - 26, GROUND_Y), Vector2(bx + 26, GROUND_Y)]), Color(1, 0, 0, 0.75 * a))
		draw_line(Vector2(bx, GROUND_Y), top, Color(1, 1, 1, 0.85 * a), 3.0)

func _draw_battle_overlays() -> void:
	# 开场动画
	if battle_intro_t > 0.0 and intro_anim.has(boss_id):
		var frames: Array = intro_anim[boss_id]
		if frames.size() > 0:
			var idx := int((2.6 - battle_intro_t) / 2.6 * float(frames.size() - 1))
			idx = clampi(idx, 0, frames.size() - 1)
			var tex: Texture2D = frames[idx]
			var factor := maxf(VIEW.x / tex.get_width(), VIEW.y / tex.get_height())
			var size := tex.get_size() * factor
			draw_texture_rect(tex, Rect2((VIEW - size) * 0.5, size), false)
			draw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(0, 0, 0, 0.25))
			draw_string(ThemeDB.fallback_font, Vector2(470, 600), "BATTLE START", HORIZONTAL_ALIGNMENT_LEFT, -1, 46, WHITE)
	# 必杀插图「！」
	if cutin_active:
		var ct: Texture2D = textures.get("cutin_crimson" if boss_id == "crimson" else "cutin_marysue")
		draw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(0, 0, 0, 0.55))
		if ct:
			var cw := VIEW.x * 0.62
			var ch := cw * ct.get_height() / float(ct.get_width())
			draw_texture_rect(ct, Rect2((VIEW.x - cw) * 0.5, (VIEW.y - ch) * 0.5 - 20, cw, ch), false)
		draw_string(ThemeDB.fallback_font, Vector2(420, 660), "！  必  杀", HORIZONTAL_ALIGNMENT_LEFT, -1, 54, RED if boss_id == "crimson" else HAZARD)
	# 全屏绿闪（无伤害、遮挡视野）
	if green_flash_t > 0.0:
		var ga := 0.28 + 0.22 * absf(sin(elapsed * 9.0))
		draw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(0.51, 1.0, 0.0, ga * clampf(green_flash_t, 0.0, 1.0)))
	if flash_green_t > 0.0:
		# 完全不透明的绿幕：彻底挡住视野
		var fa := 1.0 if flash_green_t > 0.25 else flash_green_t / 0.25
		draw_rect(Rect2(0, 0, VIEW.x, VIEW.y), Color(0.51, 1.0, 0.0, fa))
	# 镜像翻转提示
	if mirror_flip:
		draw_string(ThemeDB.fallback_font, Vector2(430, 150), "镜中世界 · 左右交换", HORIZONTAL_ALIGNMENT_LEFT, -1, 30, HAZARD)


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
		_spawn_particle(pos + Vector2(cos(a), sin(a)) * 20.0, color, 0.5, Vector2(cos(a), sin(a)) * 260.0, 5.0)


## 地图/走位段 BGM：把音乐文件放 audio/map_bgm.ogg 即自动循环播放
func _start_map_bgm() -> void:
	_play_bgm("map_bgm")
	if map_bgm_player == null:
		return
	if map_bgm_player.stream == null:
		return
	if not map_bgm_player.playing:
		map_bgm_player.play()
		map_bgm_started = true

func _stop_map_bgm() -> void:
	if map_bgm_player != null and map_bgm_player.playing:
		map_bgm_player.stop()


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

func _spawn_ball_fx() -> void:
	if not player_ball:
		if ball_fx.size() > 0 and not player_ball:
			pass
		return
	var vel := player_vel
	var dir := vel.normalized() if vel.length() > 1.0 else Vector2(-1, 0)
	ball_fx_tick += 1
	# 1) 拖尾丝带：每帧 1 片，寿命 0.45 秒，形成连续"拉丝"
	if ball_trail_frames.size() > 0:
		var ttex: Texture2D = ball_trail_frames[ball_fx_tick % ball_trail_frames.size()]
		ball_fx.append({"kind": "ribbon", "pos": player_pos - dir * 20.0, "tex": ttex,
			"rot": dir.angle() + PI * 0.5, "size": randf_range(86.0, 112.0), "life": 0.45, "max": 0.45})
	# 2) 红色激光残影：每 2 帧一道
	if ball_fx_tick % 2 == 0:
		ball_fx.append({"kind": "laser", "pos": player_pos, "dir": dir,
			"len": randf_range(180.0, 320.0), "life": 0.32, "max": 0.32})
	# 3) 烟雾：每 3 帧一团，向上飘
	if ball_fx_tick % 3 == 0:
		ball_fx.append({"kind": "smoke", "pos": player_pos - dir * randf_range(10.0, 60.0) + Vector2(randf_range(-14, 14), randf_range(10, 30)),
			"r": randf_range(9.0, 15.0), "life": 0.9, "max": 0.9, "vel": Vector2(randf_range(-25, 25), randf_range(-60, -20))})
	# 4) 流光火星：每帧 2 颗，带初速度
	for k in range(2):
		var ang := randf() * TAU
		ball_fx.append({"kind": "spark", "pos": player_pos + Vector2(cos(ang), sin(ang)) * randf_range(8.0, 26.0),
			"vel": -dir * randf_range(80.0, 220.0) + Vector2(randf_range(-70, 70), randf_range(-70, 70)),
			"size": randf_range(2.5, 5.5), "life": randf_range(0.3, 0.6), "max": 0.6})

func _update_ball_fx() -> void:
	_spawn_ball_fx()
	for fx in ball_fx:
		fx["life"] = float(fx["life"]) - FIXED_DT
		if fx.has("vel"):
			fx["pos"] = Vector2(fx["pos"]) + Vector2(fx["vel"]) * FIXED_DT
		if str(fx["kind"]) == "smoke":
			fx["r"] = float(fx["r"]) + 34.0 * FIXED_DT
			fx["pos"] = Vector2(fx["pos"]) + Vector2(fx.get("vel", Vector2.ZERO)) * FIXED_DT
	ball_fx = ball_fx.filter(func(x): return float(x.get("life", 0.0)) > 0.0)

func _draw_ball_fx() -> void:
	for fx in ball_fx:
		var k: float = clampf(float(fx["life"]) / maxf(0.01, float(fx.get("max", 1.0))), 0.0, 1.0)
		var pos: Vector2 = Vector2(fx["pos"]) - Vector2(camera_x, 0)
		match str(fx["kind"]):
			"ribbon":
				var ttex: Texture2D = fx["tex"]
				var sz: float = float(fx["size"]) * (0.75 + 0.25 * k)
				draw_set_transform(pos, float(fx["rot"]), Vector2(1, 1))
				draw_texture_rect(ttex, Rect2(Vector2(-sz * 0.5, -sz * 0.5), Vector2(sz, sz)), false,
					Color(1.0, 0.42, 0.42, 0.9 * k))
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
			"laser":
				var dir: Vector2 = fx["dir"]
				var ln: float = float(fx["len"]) * (0.5 + 0.5 * k)
				draw_line(pos, pos - dir * ln, Color(1, 0.1, 0.1, 0.55 * k), 7.0 * k + 1.0)
				draw_line(pos, pos - dir * ln * 0.7, Color(1, 0.7, 0.7, 0.5 * k), 2.5 * k + 0.5)
			"smoke":
				draw_circle(pos, float(fx["r"]), Color(0.62, 0.62, 0.62, 0.28 * k))
				draw_circle(pos, float(fx["r"]) * 0.6, Color(0.8, 0.8, 0.8, 0.16 * k))
			"spark":
				draw_circle(pos, float(fx["size"]) * (0.4 + 0.6 * k), Color(1, 0.25, 0.25, 0.9 * k))
				draw_circle(pos, float(fx["size"]) * 0.45, Color(1, 1, 1, 0.9 * k))

## 镜中世界 BGM（循环）
func _start_mirror_bgm() -> void:
	_play_bgm("mirrorworld_bgm")

func _stop_mirror_bgm() -> void:
	if mirror_bgm_player != null and mirror_bgm_player.playing:
		mirror_bgm_player.stop()


## 诺登世界（森林）BGM（循环）
func _start_norden_bgm() -> void:
	_play_bgm("norden_bgm")
	if false:
		if not norden_bgm_player.playing:
			norden_bgm_player.play()
		return
	_start_map_bgm()

func _stop_norden_bgm() -> void:
	if norden_bgm_player != null and norden_bgm_player.playing:
		norden_bgm_player.stop()


## 切 BGM：只播目标曲目，其它全部停掉（淡出靠 volume 简单处理）
func _play_bgm(track_id: String) -> void:
	for key in bgm_tracks.keys():
		var pl: AudioStreamPlayer = bgm_tracks[key]
		if key == track_id:
			if not pl.playing:
				pl.play()
		elif pl.playing:
			pl.stop()
	if track_id == "":
		return
	if not bgm_tracks.has(track_id):
		# 兜底：旧的两个单独播放器
		if track_id == "norden_bgm":
			_start_norden_bgm()
		elif track_id == "mirrorworld_bgm":
			_start_mirror_bgm()

func _chapter_bgm(chapter: String) -> String:
	return str(CHAPTER_BGM.get(chapter, ""))


## 战斗 BGM：延后到开场演出结束再响
func _start_battle_bgm() -> void:
	_start_battle_bgm_for(boss_id)

func _start_battle_bgm_for(who: String) -> void:
	var path := "res://audio/crimson_bgm.ogg" if who == "crimson" else "res://audio/marysue_bgm.ogg"
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
	battle_bgm_started = false


## Boss 移动时的粒子特效（小光点）
func _boss_move_particles() -> void:
	var delta := boss_pos - boss_prev_pos
	var speed := delta.length() / maxf(FIXED_DT, 0.0001)
	boss_prev_pos = boss_pos
	boss_move_particle_tick += 1
	if speed < 40.0:
		return
	var dir := delta.normalized()
	var amount := 2 if speed < 200.0 else 3
	if boss_move_particle_tick % 2 != 0:
		return
	for k in range(amount):
		var offset := Vector2(randf_range(-26, 26), randf_range(-46, 46))
		var origin := boss_pos + offset - dir * 18.0
		if boss_id == "crimson":
			# 红色余烬：向后飘散、缓慢下落
			_spawn_particle(origin, Color(1, randf_range(0.1, 0.35), 0.1, 0.9), randf_range(0.35, 0.7),
				Vector2(-dir.x * randf_range(60, 160) + randf_range(-30, 30), randf_range(20, 90)), randf_range(2.5, 5.0))
		else:
			# 绿色光点：向上飘、带轻微旋转感
			_spawn_particle(origin, Color(0.51, 1.0, 0.0, 0.9), randf_range(0.45, 0.85),
				Vector2(-dir.x * randf_range(30, 90) + randf_range(-40, 40), randf_range(-110, -30)), randf_range(2.0, 4.5))
	# 高速时额外一圈细腻光尘
	if speed > 500.0:
		for k in range(3):
			var a := randf() * TAU
			_spawn_particle(boss_pos + Vector2(cos(a), sin(a)) * randf_range(20.0, 60.0),
				Color(1, 1, 1, 0.55) if boss_id == "crimson" else Color(0.51, 1.0, 0.0, 0.7),
				randf_range(0.2, 0.4), Vector2(randf_range(-60, 60), randf_range(-60, 60)), 2.0)


## 让窗口放大时画面等比放大（1280×720 逻辑分辨率）
func _setup_window_stretch() -> void:
	var win := get_window()
	if win == null:
		return
	win.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	win.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_EXPAND
	win.content_scale_size = Vector2i(1280, 720)
	win.min_size = Vector2i(960, 540)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		# F11 全屏切换
		if event.keycode == KEY_F11:
			var win := get_window()
			win.mode = Window.MODE_WINDOWED if win.mode == Window.MODE_FULLSCREEN else Window.MODE_FULLSCREEN
			get_viewport().set_input_as_handled()
		# F10 放大窗口到 1600×900
		elif event.keycode == KEY_F10:
			var win2 := get_window()
			win2.mode = Window.MODE_WINDOWED
			win2.size = Vector2i(1600, 900)
			get_viewport().set_input_as_handled()


## 本帧是否有点击（鼠标左键按下沿）
var _mouse_was_down := false

func _mouse_clicked() -> bool:
	var down := Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
	var clicked := down and not _mouse_was_down
	_mouse_was_down = down
	return clicked


## 操作教程（背景压暗 + 字幕）
func _draw_tutorial() -> void:
	if tutorial_timer <= 0.0:
		return
	var a := clampf(tutorial_timer / 1.2, 0.0, 1.0)   # 最后 1.2 秒淡出
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.62 * a))
	draw_rect(Rect2(80, 90, 1120, 560), Color(0.02, 0.02, 0.03, 0.90 * a))
	draw_rect(Rect2(80, 90, 1120, 560), Color(1, 1, 1, 0.25 * a), false, 2.0)
	draw_string(ThemeDB.fallback_font, Vector2(112, 140), "操作指南", HORIZONTAL_ALIGNMENT_LEFT, -1, 30, Color(1, 1, 1, a))
	draw_line(Vector2(112, 156), Vector2(1168, 156), Color(1, 1, 1, 0.35 * a), 1.5)

	var lines := [
		["A / D", "左右移动", "SHIFT / K / 鼠标右键", "冲刺（0.2 秒无敌）"],
		["SPACE", "跳跃", "空中 W + 冲刺", "化为光球（无敌，可穿越弹幕）"],
		["J / Z / 鼠标左键", "射击", "P / ESC", "暂停 / 继续"],
		["C", "枪火击溃（2 MP）", "V", "业火（2 MP）"],
		["L", "红之惨剧（击败魔姬后解锁，2 MP）", "", ""],
	]
	var y := 200.0
	for row in lines:
		draw_string(ThemeDB.fallback_font, Vector2(120, y), "【" + str(row[0]) + "】", HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Color(1, 0.45, 0.45, a))
		draw_string(ThemeDB.fallback_font, Vector2(330, y), str(row[1]), HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Color(1, 1, 1, a))
		if str(row[2]) != "":
			draw_string(ThemeDB.fallback_font, Vector2(700, y), "【" + str(row[2]) + "】", HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Color(0.6, 0.85, 1, a))
			draw_string(ThemeDB.fallback_font, Vector2(880, y), str(row[3]), HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(1, 1, 1, a))
		y += 44.0

	draw_string(ThemeDB.fallback_font, Vector2(120, 470), "技能效果：", HORIZONTAL_ALIGNMENT_LEFT, -1, 19, Color(1, 1, 1, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 502), "· 枪火击溃：一次性大范围冲击，清掉近身弹幕", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 530), "· 业火：持续灼烧 Boss，造成多段伤害", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 558), "· 红之惨剧：回复 2 HP，并强化剑气 20 秒", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(0.9, 0.9, 0.9, a))
	draw_string(ThemeDB.fallback_font, Vector2(150, 594), "MP 回复：命中敌人 + 擦弹（贴近弹幕但不被击中）", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color(1, 0.8, 0.4, a))
	draw_string(ThemeDB.fallback_font, Vector2(930, 624), "ENTER 继续", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(0.75, 0.75, 0.75, a))


## 镜子旁的告示牌：木质牌面 + 操作说明（不需要弹窗也能看到）
func _draw_signboard() -> void:
	# 只在有交互目标的走位段显示
	if walk_target.size() == 0 or story_chapter == "":
		return
	if story_chapter not in ["wake_talk", "enter_mirror", "mirror"]:
		return
	var tx := float(walk_target.get("x", 0.0))
	if tx <= 0.0:
		return
	var sx := tx - camera_x - 150.0
	var base_y := GROUND_Y
	# 木桩
	draw_rect(Rect2(sx + 52, base_y - 96, 10, 96), Color(0.24, 0.2, 0.18))
	# 牌面
	var board := Rect2(sx, base_y - 190, 128, 106)
	draw_rect(board, Color(0.13, 0.11, 0.10, 0.96))
	draw_rect(board, Color(1, 1, 1, 0.55), false, 2.0)
	draw_line(board.position + Vector2(6, 8), board.position + Vector2(board.size.x - 6, 8), Color(1, 0.3, 0.3, 0.8), 2.0)
	var tips := ["A / D  移动", "SPACE 跳跃", "SHIFT 冲刺", "空中W+冲刺 = 光球", "J / Z  射击", "C / V  技能"]
	var ty := board.position.y + 26.0
	for t in tips:
		draw_string(ThemeDB.fallback_font, Vector2(board.position.x + 8, ty), t, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.92, 0.92, 0.92))
		ty += 15.0


## 死亡流程：镜裂 → 碎镜 → 回到起点 → 幻觉台词
func _start_death() -> void:
	if death_timer > 0.0:
		return
	death_timer = 1.9
	death_flash = 1.0
	player_hp = 0
	bullets.clear()
	screen_shake = 1.2
	sfx_player.play("shards")
	sfx_player.play("explode")
	# 生成不规则玻璃碎片（以受击点为中心炸开）
	death_shards.clear()
	var center := player_pos - Vector2(camera_x, 0) + Vector2(0, -20)
	for i in range(34):
		var ang := TAU * float(i) / 34.0 + randf_range(-0.12, 0.12)
		var dist := randf_range(30.0, 210.0)
		var px := center + Vector2(cos(ang), sin(ang)) * dist
		var pts := PackedVector2Array()
		var n := randi_range(3, 5)
		var r0 := randf_range(18.0, 52.0)
		for k in range(n):
			var a2 := TAU * float(k) / float(n) + randf_range(-0.35, 0.35)
			var rr := r0 * randf_range(0.55, 1.25)
			pts.append(Vector2(cos(a2), sin(a2)) * rr)
		death_shards.append({
			"pos": px,
			"vel": Vector2(cos(ang), sin(ang)) * randf_range(160.0, 620.0),
			"rot": randf_range(0.0, TAU),
			"spin": randf_range(-7.0, 7.0),
			"life": randf_range(1.1, 1.9),
			"max": 1.9,
			"pts": pts,
			"tint": randf_range(0.55, 1.0)
		})

func _update_death() -> void:
	if death_timer <= 0.0:
		return
	death_timer = maxf(0.0, death_timer - FIXED_DT)
	death_flash = maxf(0.0, death_flash - FIXED_DT * 3.2)
	for sh in death_shards:
		sh["life"] = float(sh["life"]) - FIXED_DT
		sh["pos"] = Vector2(sh["pos"]) + Vector2(sh["vel"]) * FIXED_DT
		sh["vel"] = Vector2(sh["vel"]) * 0.985 + Vector2(0, 520.0) * FIXED_DT
		sh["rot"] = float(sh["rot"]) + float(sh["spin"]) * FIXED_DT
	death_shards = death_shards.filter(func(x): return float(x.get("life", 0.0)) > 0.0)
	if death_timer <= 0.0:
		player_hp = PLAYER_MAX_HP
		player_pos = battle_start_pos
		player_vel = Vector2.ZERO
		player_hurt_invuln = 90
		bullets.clear()
		spikes.clear()
		whirls.clear()
		boss_hp = boss_max_hp
		banner = "……是幻觉么。"
		banner_timer = 170
		_spawn_fx_ring(player_pos, Color(1, 1, 1, 0.9), 260.0, 0.5, 5.0)

func _draw_death_overlay() -> void:
	if death_timer <= 0.0:
		return
	var k := clampf(death_timer / 1.9, 0.0, 1.0)
	var dark := clampf(1.0 - k * 1.5, 0.0, 1.0)
	# 玻璃碎片：不规则多边形 + 冷白半透明 + 反光边
	for sh in death_shards:
		var lk := clampf(float(sh["life"]) / float(sh["max"]), 0.0, 1.0)
		var pts: PackedVector2Array = sh["pts"]
		var pos: Vector2 = sh["pos"]
		var rot: float = sh["rot"]
		var world := PackedVector2Array()
		for pv in pts:
			world.append(pos + pv.rotated(rot))
		var tint: float = float(sh["tint"])
		draw_colored_polygon(world, Color(0.82 * tint, 0.86 * tint, 0.92 * tint, 0.42 * lk))
		var closed := world.duplicate()
		closed.append(world[0])
		draw_polyline(closed, Color(1, 1, 1, 0.95 * lk), 2.0)
		if world.size() >= 3:
			draw_line(world[0], world[1], Color(1, 1, 1, 0.55 * lk), 3.0)
	# 分叉裂纹
	var c := Vector2(640, 340)
	for i in range(16):
		var ang := TAU * float(i) / 16.0 + 0.13
		var length := (240.0 + 120.0 * sin(float(i) * 2.7)) * (1.0 - k * 0.35)
		var dir := Vector2(cos(ang), sin(ang))
		var seg := 5
		for s2 in range(seg):
			var t0 := float(s2) / float(seg)
			var t1 := float(s2 + 1) / float(seg)
			var jitter := Vector2(randf_range(-14, 14), randf_range(-14, 14)) * t1
			var q0 := c + dir * length * t0 + jitter * 0.6
			var q1 := c + dir * length * t1 + jitter
			draw_line(q0, q1, Color(1, 1, 1, (1.0 - float(s2) * 0.1) * (1.0 - k)), 4.0 - float(s2) * 0.5)
			if s2 == 2:
				var bdir := dir.rotated(randf_range(-0.9, 0.9)).normalized()
				draw_line(q1, q1 + bdir * randf_range(60.0, 130.0), Color(0.9, 0.9, 0.95, 0.5 * (1.0 - k)), 1.5)
	if death_flash > 0.0:
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(1, 1, 1, 0.5 * death_flash))
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.62 * dark))
	if death_timer > 0.9:
		var ta := clampf((death_timer - 0.9) / 0.6, 0.0, 1.0)
		draw_string(ThemeDB.fallback_font, Vector2(520, 372), "镜 碎 了", HORIZONTAL_ALIGNMENT_LEFT, -1, 40, Color(1, 1, 1, ta))


## Boss 战边界：边界外烧起来的红色火焰墙 + 靠近提示
func _draw_battle_bounds_fx() -> void:
	var left_screen := _battle_left() - camera_x
	var right_screen := _battle_right() - camera_x
	# 区域外压暗（越靠外越黑红）
	if left_screen > 0.0:
		draw_rect(Rect2(0, 0, left_screen, VIEW.y), Color(0.18, 0.0, 0.0, 0.55))
	if right_screen < VIEW.x:
		draw_rect(Rect2(right_screen, 0, VIEW.x - right_screen, VIEW.y), Color(0.18, 0.0, 0.0, 0.55))
	# 边界火焰：沿边界竖直一排跳动的火舌
	for side in [left_screen, right_screen]:
		if side < -60.0 or side > VIEW.x + 60.0:
			continue
		var base_x := clampf(side, -40.0, VIEW.x + 40.0)
		# 火墙底色
		draw_rect(Rect2(base_x - (18.0 if side == left_screen else -18.0), 0, 36, VIEW.y), Color(1, 0.12, 0.05, 0.18))
		var tongues := 16
		for i in range(tongues):
			var ty := float(i) * (VIEW.y / float(tongues))
			var ph := elapsed * 5.0 + float(i) * 0.9
			var h := 34.0 + 26.0 * sin(ph) + 12.0 * sin(ph * 2.7)
			var w := 22.0 + 8.0 * sin(ph * 1.7 + 1.0)
			var dir := 1.0 if side == left_screen else -1.0
			var tip := Vector2(base_x + dir * h, ty + 10.0)
			# 外焰（暗红）
			draw_colored_polygon(PackedVector2Array([
				Vector2(base_x, ty - w * 0.5), tip, Vector2(base_x, ty + w * 0.5)
			]), Color(1, 0.18, 0.05, 0.38))
			# 内焰（亮红）
			var tip2 := Vector2(base_x + dir * h * 0.6, ty + 6.0)
			draw_colored_polygon(PackedVector2Array([
				Vector2(base_x, ty - w * 0.25), tip2, Vector2(base_x, ty + w * 0.25)
			]), Color(1, 0.55, 0.2, 0.42))
			# 焰心（白热）
			var tip3 := Vector2(base_x + dir * h * 0.3, ty + 3.0)
			draw_colored_polygon(PackedVector2Array([
				Vector2(base_x, ty - w * 0.12), tip3, Vector2(base_x, ty + w * 0.12)
			]), Color(1, 0.9, 0.7, 0.45))
		# 边界线
		draw_line(Vector2(base_x, 0), Vector2(base_x, VIEW.y), Color(1, 0.25, 0.1, 0.8), 3.0)
	# 靠近边界：屏幕对应侧发红光
	var near := 150.0
	var px := player_pos.x - camera_x
	if px < (_battle_left() - camera_x) + near:
		var t := clampf(1.0 - (px - (_battle_left() - camera_x)) / near, 0.0, 1.0)
		draw_rect(Rect2(0, 0, 26, VIEW.y), Color(1, 0, 0, 0.35 * t))
	elif px > (_battle_right() - camera_x) - near:
		var t2 := clampf(1.0 - ((_battle_right() - camera_x) - px) / near, 0.0, 1.0)
		draw_rect(Rect2(VIEW.x - 26, 0, 26, VIEW.y), Color(1, 0, 0, 0.35 * t2))


## 战场边界跟随 Boss：Boss 左右各 ±700，并限制在地图内
func _battle_left() -> float:
	return clampf(boss_pos.x - BATTLE_HALF, 120.0, WORLD_W - 200.0)

func _battle_right() -> float:
	return clampf(boss_pos.x + BATTLE_HALF, 120.0 + 400.0, WORLD_W - 120.0)


## 玩家扣血（统一入口，带无敌帧与红晕）
func _apply_player_damage() -> void:
	if player_hurt_invuln > 0 or player_dash_invuln > 0 or player_ball:
		return
	player_hp -= 1
	player_hurt_invuln = 80
	hurt_vignette = 18
	sfx_player.play("hurt")
	screen_shake = 0.6
	if player_hp <= 0:
		player_hp = 0
		_start_death()


## 绿色激光柱（竖直，从天空落到地面；持续 seconds 秒）
func _spawn_beam(x: float, seconds: float) -> void:
	_spawn_bullet(Vector2(x, (40.0 + GROUND_Y) * 0.5), Vector2.ZERO, HAZARD, "beam", seconds, 0.0)
	_spawn_fx_ring(Vector2(x, GROUND_Y - 30.0), Color(0.51, 1, 0, 0.8), 120.0, 0.35, 3.0)
	for k in range(6):
		_spawn_particle(Vector2(x + randf_range(-18, 18), GROUND_Y - 30.0), Color(0.51, 1, 0, 0.9),
			0.5, Vector2(randf_range(-40, 40), randf_range(-150, -50)), 4.0)


## 激光预警：先亮 0.7 秒（画线 + 地面光圈），再落柱
var beam_warning_list: Array = []

func _beam_warning(x: float) -> void:
	beam_warning_list.append({"x": x, "t": 0.7})

func _update_beam_warnings() -> void:
	for w in beam_warning_list:
		w["t"] = float(w["t"]) - FIXED_DT
		if float(w["t"]) <= 0.0:
			if bool(w.get("crimson", false)):
				_spawn_beam_crimson(float(w["x"]), 0.9)
			else:
				_spawn_beam(float(w["x"]), 0.9)
	beam_warning_list = beam_warning_list.filter(func(w): return float(w["t"]) > 0.0)

func _draw_beam_warnings() -> void:
	for w in beam_warning_list:
		var bx: float = float(w["x"]) - camera_x
		var k: float = clampf(float(w["t"]) / 0.7, 0.0, 1.0)
		draw_line(Vector2(bx, 40), Vector2(bx, GROUND_Y), Color(0.51, 1, 0, 0.30 + 0.45 * (1.0 - k)), 3.0)
		draw_circle(Vector2(bx, GROUND_Y - 12), 28.0 + 10.0 * (1.0 - k), Color(0.51, 1, 0, 0.22))


## 全局屏震衰减（避免胜利/剧情模式下一直抖）
func _decay_shake() -> void:
	if screen_shake > 0.0:
		screen_shake = maxf(0.0, screen_shake - 0.42)


## 雷帝落雷预警（红色）
func _beam_warning_crimson(x: float) -> void:
	beam_warning_list.append({"x": x, "t": 0.7, "crimson": true})

## 红色落雷（复用 beam 贴图与判定）
func _spawn_beam_crimson(x: float, seconds: float) -> void:
	_spawn_bullet(Vector2(x, (40.0 + GROUND_Y) * 0.5), Vector2.ZERO, RED, "beam", seconds, 0.0)
	_spawn_fx_ring(Vector2(x, GROUND_Y - 30.0), Color(1, 0.25, 0.15, 0.85), 130.0, 0.35, 3.0)
