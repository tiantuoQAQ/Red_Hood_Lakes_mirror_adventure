extends Node

## SFX player pool: allows simultaneous playback of the same effect.
## Each SFX has a pool of AudioStreamPlayer nodes for concurrent playback.

const SFX_VOLUME_DB := -8.0  # Unified volume: -8dB
const POOL_SIZE := 4  # Max concurrent playback per SFX

var streams: Dictionary = {}  # { "graze": AudioStream, ... }
var pools: Dictionary = {}    # { "graze": [AudioStreamPlayer, ...], ... }

func _ready() -> void:
	_load_sfx("graze", "res://audio/sfx/graze.wav")
	_load_sfx("graze_up", "res://audio/sfx/graze_up.wav")
	_load_sfx("dash", "res://audio/sfx/dash.wav")
	_load_sfx("land", "res://audio/sfx/land.wav")
	_load_sfx("hurt", "res://audio/sfx/hurt.wav")
	_load_sfx("skill", "res://audio/sfx/skill.wav")
	_load_sfx("shards", "res://audio/sfx/shards.wav")

func _load_sfx(id: String, path: String) -> void:
	if not ResourceLoader.exists(path):
		push_warning("SFX not found: " + path)
		return
	var stream = load(path)
	if stream is AudioStream:
		streams[id] = stream
		pools[id] = []
		for i in range(POOL_SIZE):
			var player := AudioStreamPlayer.new()
			player.stream = stream
			player.volume_db = SFX_VOLUME_DB
			player.bus = "Master"
			add_child(player)
			pools[id].append(player)

## Play a sound effect. Returns true if played, false if all pool slots busy.
func play(id: String) -> bool:
	if not pools.has(id):
		return false
	var pool: Array = pools[id]
	for player in pool:
		if not player.playing:
			player.play()
			return true
	# All busy: stop the oldest (first) and replay
	pool[0].play()
	return true
