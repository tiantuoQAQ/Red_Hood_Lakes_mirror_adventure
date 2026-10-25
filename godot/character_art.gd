extends RefCounted

## Equal scaling and visible-foot anchors for map NPCs and player art.
var bounds_cache: Dictionary = {}
const PLAYER_SCALE := 0.34
const PLAYER_FOOT := Vector2(550, 730)
const PLAYER_NECK := Vector2(610, 320)

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
		return "dash_%02d" % clampi((12 - dash_frames) / 4 + 1, 1, 3)
	if dash_out > 0:
		return "dash_03"
	return "body_charge" if shooting else "body_move"

func draw_player(canvas: CanvasItem, art: Dictionary, foot: Vector2, facing: float, state: String, aim: Vector2, tint: Color) -> bool:
	var texture: Texture2D = art.get("rek_" + state)
	if not texture:
		return false
	canvas.draw_set_transform(foot, 0, Vector2(facing, 1))
	canvas.draw_texture_rect(texture, Rect2(-PLAYER_FOOT * PLAYER_SCALE, texture.get_size() * PLAYER_SCALE), false, tint)
	if not state.begins_with("dash_"):
		var head: Texture2D = art.get("rek_head")
		if head:
			var neck := (PLAYER_NECK - PLAYER_FOOT) * PLAYER_SCALE
			var local_aim := Vector2(aim.x * facing, aim.y)
			var angle := clampf(local_aim.angle() * 0.16, -0.25, 0.25)
			canvas.draw_set_transform(foot + Vector2(neck.x * facing, neck.y), angle * facing, Vector2(facing, 1))
			canvas.draw_texture_rect(head, Rect2(-PLAYER_NECK * PLAYER_SCALE, head.get_size() * PLAYER_SCALE), false, tint)
	canvas.draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)
	return true
