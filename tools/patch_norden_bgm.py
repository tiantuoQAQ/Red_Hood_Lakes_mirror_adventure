# -*- coding: utf-8 -*-
"""诺登世界（正常森林）BGM：audio/norden_bgm.ogg（轶事性知识，循环）。
优先级：森林 → norden_bgm；镜中世界 → mirrorworld_bgm；都没加载则退回 map_bgm。
"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

if 'norden_bgm_player' not in s:
    s = s.replace('var mirror_bgm_player: AudioStreamPlayer',
                  'var mirror_bgm_player: AudioStreamPlayer\nvar norden_bgm_player: AudioStreamPlayer', 1)
    s = s.replace('\tif ResourceLoader.exists("res://audio/mirrorworld_bgm.ogg"):',
                  '\tnorden_bgm_player = AudioStreamPlayer.new()\n'
                  '\tnorden_bgm_player.bus = "Master"\n'
                  '\tnorden_bgm_player.volume_db = -12.0\n'
                  '\tadd_child(norden_bgm_player)\n'
                  '\tif ResourceLoader.exists("res://audio/norden_bgm.ogg"):\n'
                  '\t\tvar ns: AudioStream = load("res://audio/norden_bgm.ogg")\n'
                  '\t\tif ns is AudioStreamOggVorbis:\n'
                  '\t\t\tns.loop = true\n'
                  '\t\tnorden_bgm_player.stream = ns\n'
                  '\tif ResourceLoader.exists("res://audio/mirrorworld_bgm.ogg"):', 1)
    print('norden bgm player added')

if 'func _start_norden_bgm' not in s:
    s += '''

## 诺登世界（森林）BGM（循环）
func _start_norden_bgm() -> void:
	if norden_bgm_player != null and norden_bgm_player.stream != null:
		if not norden_bgm_player.playing:
			norden_bgm_player.play()
		return
	_start_map_bgm()

func _stop_norden_bgm() -> void:
	if norden_bgm_player != null and norden_bgm_player.playing:
		norden_bgm_player.stop()
'''
    print('norden bgm funcs appended')

# 走位段 BGM 选择：森林 → 诺登世界曲
s = s.replace('\tif story_bg == "forest":\n\t\t_start_map_bgm()\n\t\t_stop_mirror_bgm()',
              '\tif story_bg == "forest":\n'
              '\t\t_start_norden_bgm()\n'
              '\t\t_stop_mirror_bgm()', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
