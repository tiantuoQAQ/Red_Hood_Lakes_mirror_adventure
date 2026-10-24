extends Node2D

const VIEW := Vector2(1280.0, 720.0)
const GROUND_Y := 588.0
const RED := Color("#ff0000")
const GREEN := Color("#82ff00")
const CYAN := Color("#00baff")
const WHITE := Color("#f1f1f1")
const GREY := Color("#9a9a9a")
const DARK := Color("#08090d")

enum Mode { TITLE, BATTLE, VICTORY }
var mode: Mode = Mode.TITLE
var boss_id := "scarlet"
var elapsed := 0.0
var victory_elapsed := 0.0
var banner := ""
var player := {
	"pos": Vector2(250, GROUND_Y - 52),
	"vel": Vector2.ZERO,
	"grounded": true,
	"dash": 0.0,
	"dash_cd": 0.0,
	"invuln": 0.0,
	"shoot_cd": 0.0,
	"hp": 3
}
var boss := {}
var bullets: Array = []
var shots: Array = []
var trail: Array = []
var particles: Array = []
var textures: Dictionary = {}

func _ready() -> void:
	_load_assets()
	_reset_boss("scarlet")
	queue_redraw()

func _load_assets() -> void:
	var paths := {
		"scarlet_01": "res://art/battle/scarlet/scarlet-action-red-eyes-01-cutout.png",
		"scarlet_02": "res://art/battle/scarlet/scarlet-action-red-eyes-02-cutout.png",
		"scarlet_03": "res://art/battle/scarlet/scarlet-action-red-eyes-03-cutout.png",
		"scarlet_04": "res://art/battle/scarlet/scarlet-action-red-eyes-04-cutout.png",
		"marysue_01": "res://art/battle/marysue/marysue-battle-01.png",
		"marysue_02": "res://art/battle/marysue/marysue-battle-02.png",
		"marysue_03": "res://art/battle/marysue/marysue-battle-03.png"
	}
	for key in paths:
		var tex = load(paths[key])
		if tex:
			textures[key] = tex

func _reset_boss(id: String) -> void:
	boss_id = id
	var max_hp := 360.0 if id == "marysue" else 240.0
	boss = {"hp": max_hp, "max_hp": max_hp, "timer": 0.0, "phase": 0, "hit_flash": 0.0, "attack": 0.0}
	bullets.clear()
	shots.clear()
	particles.clear()
	victory_elapsed = 0.0
	banner = ""
	player.pos = Vector2(250, GROUND_Y - 52)
	player.vel = Vector2.ZERO
	player.hp = 3

func _process(delta: float) -> void:
	elapsed += delta
	match mode:
		Mode.TITLE:
			if Input.is_action_just_pressed("start"):
				mode = Mode.BATTLE
				_reset_boss("scarlet")
		Mode.BATTLE:
			_update_battle(delta)
		Mode.VICTORY:
			victory_elapsed += delta
			if Input.is_action_just_pressed("start"):
				if boss_id == "scarlet":
					mode = Mode.BATTLE
					_reset_boss("marysue")
				else:
					mode = Mode.TITLE
					_reset_boss("scarlet")
			if Input.is_action_just_pressed("ui_cancel"):
				mode = Mode.TITLE
				_reset_boss("scarlet")
	queue_redraw()

func _update_battle(delta: float) -> void:
	_update_player(delta)
	_update_boss(delta)
	_update_shots(delta)
	_update_bullets(delta)
	_update_particles(delta)
	if Input.is_action_just_pressed("ui_cancel"):
		mode = Mode.TITLE
		_reset_boss("scarlet")

func _update_player(delta: float) -> void:
	player.dash_cd = maxf(0.0, player.dash_cd - delta)
	player.invuln = maxf(0.0, player.invuln - delta)
	player.shoot_cd = maxf(0.0, player.shoot_cd - delta)
	for item in trail:
		item.life -= delta
		item.pos += item.drift * delta
	trail = trail.filter(func(item): return item.life > 0.0)

	var axis := Input.get_axis("move_left", "move_right")
	if player.dash > 0.0:
		player.dash -= delta
		player.vel.x = 760.0 * signf(player.vel.x if absf(player.vel.x) > 0.1 else 1.0)
		player.vel.y = 0.0
		_spawn_dash_trail()
	else:
		player.vel.x = move_toward(player.vel.x, axis * 300.0, 1800.0 * delta)
		player.vel.y += 1450.0 * delta
		if player.grounded and Input.is_action_just_pressed("jump"):
			player.vel.y = -560.0
			player.grounded = false
		if Input.is_action_just_pressed("dash") and player.dash_cd <= 0.0:
			player.dash = 0.20
			player.dash_cd = 0.62
			player.invuln = 0.28
			player.vel.x = (axis if absf(axis) > 0.1 else 1.0) * 760.0
			_spawn_burst(player.pos, RED, 12)
		if Input.is_action_just_pressed("shoot") and player.shoot_cd <= 0.0:
			player.shoot_cd = 0.18
			shots.append({"pos": player.pos + Vector2(22, -20), "vel": Vector2(780, 0), "life": 1.4})
	player.pos += player.vel * delta
	player.pos.x = clampf(player.pos.x, 64.0, 1216.0)
	if player.pos.y >= GROUND_Y - 52.0:
		player.pos.y = GROUND_Y - 52.0
		player.vel.y = 0.0
		player.grounded = true
	else:
		player.grounded = false
	if player.dash <= 0.0 and player.dash_cd > 0.0 and player.grounded:
		player.vel.x = move_toward(player.vel.x, 0.0, 500.0 * delta)
	_check_player_hits()

func _spawn_dash_trail() -> void:
	trail.append({"pos": player.pos, "life": 0.22, "max_life": 0.22, "drift": Vector2(-32, 0)})
	if trail.size() > 12:
		trail.pop_front()
	if int(elapsed * 80.0) % 3 == 0:
		_spawn_particle(player.pos + Vector2(-12, randf_range(-28, 28)), RED, randf_range(0.12, 0.24), Vector2(-randf_range(30, 110), randf_range(-25, 25)))

func _update_boss(delta: float) -> void:
	boss.timer += delta
	boss.attack += delta
	boss.hit_flash = maxf(0.0, boss.hit_flash - delta)
	boss.phase = mini(4, int((boss.max_hp - boss.hp) / (boss.max_hp / 5.0)))
	if boss.attack >= (0.74 if boss_id == "scarlet" else 0.92):
		boss.attack = 0.0
		_spawn_boss_pattern()
	if boss.hp <= 0.0:
		mode = Mode.VICTORY
		victory_elapsed = 0.0
		_spawn_burst(Vector2(1010, 330), RED if boss_id == "scarlet" else GREEN, 48)

func _spawn_boss_pattern() -> void:
	var origin := Vector2(960, 350)
	var color := RED if boss_id == "scarlet" else GREEN
	var phase: int = int(boss.phase)
	if boss_id == "scarlet":
		if phase % 3 == 0:
			for i in range(3):
				_spawn_blade(origin, Vector2(-520.0, (i - 1) * 92.0), color, "line")
		elif phase % 3 == 1:
			for i in range(6):
				var a := lerpf(-0.72, 0.72, float(i) / 5.0)
				_spawn_blade(origin, Vector2(-430.0 * cos(a), 430.0 * sin(a)), color, "fan")
		else:
			for i in range(5):
				var target: Vector2 = player.pos + Vector2(0, -8) - origin
				var v: Vector2 = target.normalized().rotated((i - 2) * 0.12) * (360.0 + i * 18.0)
				_spawn_blade(origin, v, color, "homing")
	else:
		if phase % 2 == 0:
			for i in range(7):
				var a := lerpf(-1.0, 1.0, float(i) / 6.0)
				_spawn_blade(origin, Vector2(-300.0 * cos(a), 300.0 * sin(a)), color, "leaf")
		else:
			for i in range(4):
				_spawn_blade(origin + Vector2(0, i * 24 - 36), Vector2(-500, 0), color, "laser")

func _spawn_blade(pos: Vector2, vel: Vector2, color: Color, kind: String) -> void:
	bullets.append({"pos": pos, "vel": vel, "life": 4.2, "color": color, "kind": kind, "angle": vel.angle()})

func _update_shots(delta: float) -> void:
	for shot in shots:
		shot.pos += shot.vel * delta
		shot.life -= delta
		if shot.pos.distance_to(Vector2(1000, 350)) < 82.0:
			boss.hp = maxf(0.0, boss.hp - 7.0)
			boss.hit_flash = 0.08
			shot.life = 0.0
			_spawn_burst(shot.pos, RED, 4)
	shots = shots.filter(func(shot): return shot.life > 0.0 and shot.pos.x < 1320.0)

func _update_bullets(delta: float) -> void:
	for bullet in bullets:
		bullet.pos += bullet.vel * delta
		bullet.life -= delta
		if bullet.kind == "homing" and bullet.life > 2.8:
			var desired: Vector2 = (player.pos - bullet.pos).normalized() * bullet.vel.length()
			bullet.vel = bullet.vel.lerp(desired, delta * 0.7)
			bullet.angle = bullet.vel.angle()
	bullets = bullets.filter(func(b): return b.life > 0.0 and b.pos.x > -120.0 and b.pos.x < 1400.0 and b.pos.y > 10.0 and b.pos.y < 700.0)

func _check_player_hits() -> void:
	if player.invuln > 0.0:
		return
	for bullet in bullets:
		if bullet.pos.distance_to(player.pos + Vector2(0, -8)) < 30.0:
			player.hp -= 1
			player.invuln = 1.1
			_spawn_burst(player.pos, WHITE, 16)
			if player.hp <= 0:
				_reset_boss(boss_id)
				banner = "镜面回溯"
			return

func _update_particles(delta: float) -> void:
	for p in particles:
		p.pos += p.vel * delta
		p.vel *= pow(0.08, delta)
		p.life -= delta
	particles = particles.filter(func(p): return p.life > 0.0)

func _spawn_particle(pos: Vector2, color: Color, life: float, vel := Vector2.ZERO) -> void:
	particles.append({"pos": pos, "vel": vel, "life": life, "max_life": life, "color": color, "size": randf_range(2.0, 6.0)})

func _spawn_burst(pos: Vector2, color: Color, count: int) -> void:
	for i in range(count):
		var a := TAU * float(i) / float(count) + randf_range(-0.15, 0.15)
		_spawn_particle(pos, color, randf_range(0.28, 0.68), Vector2(cos(a), sin(a)) * randf_range(35, 180))

func _draw() -> void:
	_draw_background()
	match mode:
		Mode.TITLE:
			_draw_title()
		Mode.BATTLE:
			_draw_battle()
		Mode.VICTORY:
			_draw_battle()
			_draw_victory()

func _draw_background() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW), DARK)
	for i in range(12):
		var y := float(i) * 50.0
		draw_rect(Rect2(0, y, VIEW.x, 50), Color(0.03 + i * 0.003, 0.035 + i * 0.003, 0.06 + i * 0.006, 1))
	for i in range(11):
		var x := float(i) * 128.0 - fmod(elapsed * 18.0, 128.0)
		draw_line(Vector2(x, 110), Vector2(x + 160, GROUND_Y), Color(0.0, 0.73, 1.0, 0.08), 1.0)
		draw_line(Vector2(x + 80, 110), Vector2(x - 80, GROUND_Y), Color(0.0, 0.73, 1.0, 0.045), 1.0)
	draw_line(Vector2(0, GROUND_Y), Vector2(VIEW.x, GROUND_Y), Color(0.0, 0.73, 1.0, 0.32), 2.0)
	for i in range(18):
		var x := fmod(float(i) * 107.0 + 43.0, VIEW.x)
		var y := 135.0 + fmod(float(i) * 71.0 + elapsed * (8.0 + i), 390.0)
		draw_circle(Vector2(x, y), 1.5 + (i % 3), Color(0.0, 0.73, 1.0, 0.18))

func _draw_title() -> void:
	draw_string(ThemeDB.fallback_font, Vector2(390, 220), "M I R R O R", HORIZONTAL_ALIGNMENT_LEFT, -1, 68, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(515, 275), "镜", HORIZONTAL_ALIGNMENT_LEFT, -1, 42, CYAN)
	draw_line(Vector2(360, 305), Vector2(920, 305), Color(0.0, 0.73, 1.0, 0.45), 2.0)
	draw_string(ThemeDB.fallback_font, Vector2(470, 410), "横版 Boss Rush · Godot 垂直切片", HORIZONTAL_ALIGNMENT_LEFT, -1, 24, GREY)
	draw_string(ThemeDB.fallback_font, Vector2(470, 510), "按 ENTER / SPACE 开始", HORIZONTAL_ALIGNMENT_LEFT, -1, 28, RED)
	draw_string(ThemeDB.fallback_font, Vector2(470, 555), "A D 移动   SPACE 跳跃   SHIFT / K 冲刺   J / Z 射击", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, GREY)

func _draw_battle() -> void:
	_draw_platform()
	_draw_boss_fx()
	_draw_boss()
	_draw_projectiles()
	_draw_dash_trail()
	_draw_player()
	_draw_particles()
	_draw_hud()

func _draw_platform() -> void:
	draw_rect(Rect2(0, GROUND_Y + 2, VIEW.x, VIEW.y - GROUND_Y), Color(0.02, 0.03, 0.05, 1))
	for i in range(14):
		var x := float(i) * 100.0 - fmod(elapsed * 40.0, 100.0)
		draw_line(Vector2(x, GROUND_Y + 15), Vector2(x + 55, GROUND_Y + 15), Color(0.0, 0.73, 1.0, 0.14), 1)

func _draw_boss_fx() -> void:
	var color := RED if boss_id == "scarlet" else GREEN
	var center := Vector2(1000, 345 + sin(elapsed * 1.8) * 8.0)
	for ring in range(3):
		var radius := 148.0 + ring * 21.0 + sin(elapsed * 2.2 + ring) * 4.0
		draw_arc(center, radius, elapsed * (0.55 + ring * 0.14), elapsed * (0.55 + ring * 0.14) + PI * 1.52, 56, Color(color, 0.20 - ring * 0.04), 2.0)
		draw_arc(center, radius, elapsed * (0.55 + ring * 0.14) + PI, elapsed * (0.55 + ring * 0.14) + PI * 1.72, 56, Color(color, 0.15 - ring * 0.03), 2.0)
	for i in range(20):
		var a := elapsed * 0.8 + float(i) * TAU / 20.0
		var r := 155.0 + fmod(float(i) * 31.0 + elapsed * 22.0, 70.0)
		var p := center + Vector2(cos(a), sin(a)) * r
		draw_circle(p, 1.5 + (i % 3), Color(color, 0.35))

func _draw_boss() -> void:
	var center := Vector2(1000, 345 + sin(elapsed * 1.8) * 8.0)
	var key := ""
	if boss_id == "scarlet":
		var frame: int = (int(elapsed * 7.0) + int(boss.phase)) % 4 + 1
		key = "scarlet_%02d" % frame
	else:
		key = "marysue_%02d" % ((int(elapsed * 3.0) % 3) + 1)
	var tex = textures.get(key)
	if tex:
		var tint := WHITE if boss.hit_flash <= 0.0 or int(elapsed * 50.0) % 2 == 0 else Color(1, 1, 1, 0.45)
		draw_set_transform(center, 0.0, Vector2(0.30, 0.30))
		draw_texture(tex, Vector2(-tex.get_width() / 2.0, -tex.get_height() / 2.0), tint)
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	else:
		_draw_boss_placeholder(center)

func _draw_boss_placeholder(center: Vector2) -> void:
	var color := RED if boss_id == "scarlet" else GREEN
	draw_circle(center + Vector2(0, -72), 42, Color("#bdbdbd"))
	draw_circle(center + Vector2(-15, -78), 7, color)
	draw_circle(center + Vector2(15, -78), 7, color)
	draw_colored_polygon(PackedVector2Array([center + Vector2(-40, -35), center + Vector2(40, -35), center + Vector2(90, 85), center + Vector2(-90, 85)]), color)

func _draw_projectiles() -> void:
	for shot in shots:
		draw_line(shot.pos - Vector2(18, 0), shot.pos + Vector2(10, 0), Color(1, 0.25, 0.25, 0.32), 8)
		draw_line(shot.pos - Vector2(10, 0), shot.pos + Vector2(13, 0), WHITE, 3)
	for bullet in bullets:
		var c: Color = bullet.color
		var p: Vector2 = bullet.pos
		var angle: float = bullet.angle
		var size := 20.0 if bullet.kind != "laser" else 36.0
		var points := PackedVector2Array([Vector2(size, 0), Vector2(-size * 0.45, -size * 0.36), Vector2(-size * 0.9, 0), Vector2(-size * 0.45, size * 0.36)])
		for i in range(points.size()):
			points[i] = p + points[i].rotated(angle)
		draw_colored_polygon(points, Color(c, 0.80))
		draw_line(p - Vector2(cos(angle), sin(angle)) * size * 1.8, p, WHITE, 2)
		draw_circle(p, size * 0.8, Color(c, 0.12))

func _draw_dash_trail() -> void:
	for item in trail:
		var alpha: float = clampf(item.life / item.max_life, 0.0, 1.0) * 0.28
		_draw_player_at(item.pos, Color(1, 0, 0, alpha))

func _draw_player() -> void:
	var tint := WHITE if player.invuln <= 0.0 or int(elapsed * 32.0) % 2 == 0 else Color(1, 1, 1, 0.32)
	_draw_player_at(player.pos, tint)

func _draw_player_at(pos: Vector2, tint: Color) -> void:
	var cape := Color(0.76, 0.02, 0.02, tint.a)
	var body := Color(0.08, 0.08, 0.1, tint.a)
	draw_colored_polygon(PackedVector2Array([pos + Vector2(-18, -30), pos + Vector2(-70, -8), pos + Vector2(-88, 38), pos + Vector2(-12, 18)]), cape)
	draw_rect(Rect2(pos + Vector2(-16, -30), Vector2(32, 62)), body)
	draw_circle(pos + Vector2(0, -54), 26, Color(0.72, 0.72, 0.72, tint.a))
	draw_colored_polygon(PackedVector2Array([pos + Vector2(-29, -68), pos + Vector2(-18, -101), pos + Vector2(-4, -76), pos + Vector2(8, -76), pos + Vector2(27, -101), pos + Vector2(31, -61)]), RED)
	draw_circle(pos + Vector2(-10, -56), 4, RED)
	draw_circle(pos + Vector2(10, -56), 4, RED)
	draw_line(pos + Vector2(18, -23), pos + Vector2(47, -5), Color(0.9, 0.9, 0.9, tint.a), 5)

func _draw_particles() -> void:
	for p in particles:
		var alpha: float = clampf(p.life / p.max_life, 0.0, 1.0)
		draw_circle(p.pos, p.size * alpha, Color(p.color, alpha))

func _draw_hud() -> void:
	var color := RED if boss_id == "scarlet" else GREEN
	draw_string(ThemeDB.fallback_font, Vector2(38, 42), "MIRROR // BATTLE", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, GREY)
	draw_string(ThemeDB.fallback_font, Vector2(940, 42), "猩红魔姬 · 雷帝" if boss_id == "scarlet" else "黑童话之母 · 玛丽苏", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, color)
	draw_rect(Rect2(840, 58, 370, 14), Color(0.08, 0.08, 0.1, 1))
	draw_rect(Rect2(840, 58, 370 * (boss.hp / boss.max_hp), 14), color)
	draw_string(ThemeDB.fallback_font, Vector2(840, 103), "STAGE %d / 5" % (boss.phase + 1), HORIZONTAL_ALIGNMENT_LEFT, -1, 15, GREY)
	draw_string(ThemeDB.fallback_font, Vector2(40, 678), "HP %d" % player.hp, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, WHITE)
	draw_string(ThemeDB.fallback_font, Vector2(170, 678), "冲刺 %s" % ("READY" if player.dash_cd <= 0.0 else "COOLDOWN"), HORIZONTAL_ALIGNMENT_LEFT, -1, 18, RED if player.dash_cd <= 0.0 else GREY)
	if banner != "":
		draw_string(ThemeDB.fallback_font, Vector2(520, 350), banner, HORIZONTAL_ALIGNMENT_LEFT, -1, 30, WHITE)

func _draw_victory() -> void:
	draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0.0, 0.0, 0.0, 0.42))
	var title := "猩红魔姬 · 破" if boss_id == "scarlet" else "镜界静默"
	draw_string(ThemeDB.fallback_font, Vector2(430, 300), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 42, WHITE)
	var next := "按 ENTER / SPACE 进入玛丽苏战斗" if boss_id == "scarlet" else "按 ENTER / SPACE 返回标题"
	draw_string(ThemeDB.fallback_font, Vector2(430, 375), next, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, GREEN if boss_id == "scarlet" else CYAN)
