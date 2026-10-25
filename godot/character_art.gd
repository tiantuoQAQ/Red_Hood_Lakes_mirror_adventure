extends RefCounted

## Equal scaling and visible-foot anchors for map NPCs and player art.
var bounds_cache: Dictionary = {}
# Player display height in battle: 100px (user spec 2026-10-25, wave 7)
# Scale is computed from this height / natural visible bounds height
const PLAYER_HEIGHT := 100.0
const PLAYER_FOOT := Vector2(550, 730)  # Anchor point in source texture (768px natural)
const PLAYER_NECK := Vector2(610, 320)  # Neck pivot in source texture
const DASH_FRAMES := 20
const BREATHE_FRAMES := 8
const BREATHE_FPS := 8.0

var npc_breathe_cache: Dictionary = {}  # { "norden": [tex0, tex1, ...], "mabel": [...] }

func visible_bounds(texture: Texture2D) -> Rect2:
	if texture == null:
		return Rect2()
	var key := texture.get_instance_id()
	if not bounds_cache.has(key):
		var source := texture.get_image()
		bounds_cache[key] = Rect2(source.get_used_rect()) if source else Rect2(Vector2.ZERO, texture.get_size())
	return bounds_cache[key]

func ground_rect(texture: Texture2D, foot: Vector2, height: float) -> Rect2:
	var bounds := visible_bounds(texture)
	if bounds.size.y <= 0:
		return Rect2()
	var scale := height / bounds.size.y
	var size := bounds.size * scale
	return Rect2(foot - Vector2(size.x * 0.5, size.y), size)

func draw_ground(canvas: CanvasItem, texture: Texture2D, foot: Vector2, height: float, tint: Color = Color.WHITE) -> void:
	if texture:
		canvas.draw_texture_rect_region(texture, ground_rect(texture, foot, height), visible_bounds(texture), tint)

func player_state(dash_frames: int, dash_out: int, shooting: bool) -> String:
	if dash_frames > 0:
		return "dash_%02d" % clampi((DASH_FRAMES - dash_frames) * 3 / DASH_FRAMES + 1, 1, 3)
	if dash_out > 0:
		return "dash_03"
	return "body_charge" if shooting else "body_move"

func draw_player(canvas: CanvasItem, art: Dictionary, foot: Vector2, facing: float, state: String, aim: Vector2, tint: Color, squash: Vector2 = Vector2.ONE) -> bool:
	var texture: Texture2D = art.get("rek_" + state)
	if not texture:
		return false
	# Compute scale from target display height / natural texture visible height
	var bounds := visible_bounds(texture)
	if bounds.size.y <= 0:
		return false
	var scale := PLAYER_HEIGHT / bounds.size.y
	canvas.draw_set_transform(foot, 0, Vector2(facing, 1) * squash)
	canvas.draw_texture_rect(texture, Rect2(-PLAYER_FOOT * scale, texture.get_size() * scale), false, tint)
	if not state.begins_with("dash_"):
		var head: Texture2D = art.get("rek_head")
		if head:
			var neck := (PLAYER_NECK - PLAYER_FOOT) * scale
			var local_aim := Vector2(aim.x * facing, aim.y)
			var angle := clampf(local_aim.angle() * 0.16, -0.25, 0.25)
			canvas.draw_set_transform(foot + Vector2(neck.x * facing, neck.y), angle * facing, Vector2(facing, 1) * squash)
			canvas.draw_texture_rect(head, Rect2(-PLAYER_NECK * scale, head.get_size() * scale), false, tint)
	canvas.draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)
	return true

## Load 8-frame breathing animation for NPC (norden or mabel).
## Returns array of 8 textures or null if fallback to single idle.png needed.
func load_npc_breathe(npc_id: String) -> Array:
	if npc_breathe_cache.has(npc_id):
		return npc_breathe_cache[npc_id]
	var frames: Array = []
	for i in range(BREATHE_FRAMES):
		var path := "res://art/char/%s_idle_breathe/frame_%02d.png" % [npc_id, i]
		if not FileAccess.file_exists(path):
			npc_breathe_cache[npc_id] = []  # Mark as fallback
			return []
		var source := Image.load_from_file(path)
		if source:
			frames.append(ImageTexture.create_from_image(source))
		else:
			npc_breathe_cache[npc_id] = []
			return []
	npc_breathe_cache[npc_id] = frames
	return frames

## Draw NPC with breathing animation (8 frames @ 8fps) or fallback to single idle.png.
## foot is the base position at y=574 (GROUND_Y). elapsed is total elapsed time.
func draw_npc_breathe(canvas: CanvasItem, npc_id: String, foot: Vector2, height: float, elapsed: float, fallback_tex: Texture2D) -> void:
	var frames := load_npc_breathe(npc_id)
	if frames.is_empty():
		# Fallback: use single idle.png
		if fallback_tex:
			draw_ground(canvas, fallback_tex, foot, height)
		return
	var frame_idx := int(elapsed * BREATHE_FPS) % BREATHE_FRAMES
	var tex: Texture2D = frames[frame_idx]
	if tex:
		draw_ground(canvas, tex, foot, height)
