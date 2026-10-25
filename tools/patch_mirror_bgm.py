# -*- coding: utf-8 -*-
"""镜中世界 BGM：audio/mirrorworld_bgm.ogg（循环）。森林走位用 map_bgm，镜中世界用这首。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

if 'mirror_bgm_player' not in s:
    s = s.replace('var map_bgm_player: AudioStreamPlayer',
                  'var map_bgm_player: AudioStreamPlayer\nvar mirror_bgm_player: AudioStreamPlayer', 1)
    # _ready 里创建 + 加载
    s = s.replace('\tif ResourceLoader.exists("res://audio/map_bgm.ogg"):\n\t\tmap_bgm_player.stream = load("res://audio/map_bgm.ogg")',
                  '\tif ResourceLoader.exists("res://audio/map_bgm.ogg"):\n\t\tmap_bgm_player.stream = load("res://audio/map_bgm.ogg")\n'
                  '\tmirror_bgm_player = AudioStreamPlayer.new()\n'
                  '\tmirror_bgm_player.bus = "Master"\n'
                  '\tmirror_bgm_player.volume_db = -12.0\n'
                  '\tadd_child(mirror_bgm_player)\n'
                  '\tif ResourceLoader.exists("res://audio/mirrorworld_bgm.ogg"):\n'
                  '\t\tvar ms: AudioStream = load("res://audio/mirrorworld_bgm.ogg")\n'
                  '\t\tif ms is AudioStreamOggVorbis:\n'
                  '\t\t\tms.loop = true\n'
                  '\t\tmirror_bgm_player.stream = ms', 1)
    print('mirror bgm player added')

if 'func _start_mirror_bgm' not in s:
    s += '''

## 镜中世界 BGM（循环）
func _start_mirror_bgm() -> void:
	if mirror_bgm_player == null or mirror_bgm_player.stream == null:
		return
	if not mirror_bgm_player.playing:
		mirror_bgm_player.play()

func _stop_mirror_bgm() -> void:
	if mirror_bgm_player != null and mirror_bgm_player.playing:
		mirror_bgm_player.stop()
'''
    print('mirror bgm funcs appended')

# 走位段按背景选 BGM
s = s.replace('\t_start_map_bgm()',
              '\tif story_bg == "forest":\n'
              '\t\t_start_map_bgm()\n'
              '\t\t_stop_mirror_bgm()\n'
              '\telse:\n'
              '\t\t_start_mirror_bgm()\n'
              '\t\tif map_bgm_player != null and map_bgm_player.playing:\n'
              '\t\t\tmap_bgm_player.stop()', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
