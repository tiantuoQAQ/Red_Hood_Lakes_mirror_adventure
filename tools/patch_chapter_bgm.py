# -*- coding: utf-8 -*-
"""按章节切换 BGM：
- 序章/森林/诺登世界 → norden_bgm
- ambush（刚遇到玛丽苏的虚空）→ marysue_world_bgm（Scorching Sun）
- mirror / mirror_meet（镜中世界探索）→ mirrorworld_bgm
- crimson_fall → final（魔姬战败后到玛丽苏战前）→ interlude_bgm（帕累托法则）
战斗 BGM 仍由 _start_battle 处理。
"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 追加两个播放器 + 加载
if 'marysue_world_bgm_player' not in s:
    s = s.replace('var norden_bgm_player: AudioStreamPlayer',
                  'var norden_bgm_player: AudioStreamPlayer\n'
                  'var marysue_world_bgm_player: AudioStreamPlayer\n'
                  'var interlude_bgm_player: AudioStreamPlayer\n'
                  'var bgm_tracks: Dictionary = {}', 1)
    s = s.replace('\tnorden_bgm_player = AudioStreamPlayer.new()',
                  '\t# BGM 池：id -> player（统一加载/循环）\n'
                  '\tfor spec in [["norden_bgm", -12.0], ["mirrorworld_bgm", -12.0],\n'
                  '\t\t\t["marysue_world_bgm", -12.0], ["interlude_bgm", -12.0], ["map_bgm", -12.0]]:\n'
                  '\t\tvar track_id := str(spec[0])\n'
                  '\t\tvar path := "res://audio/%s.ogg" % track_id\n'
                  '\t\tif not ResourceLoader.exists(path):\n'
                  '\t\t\tcontinue\n'
                  '\t\tvar pl := AudioStreamPlayer.new()\n'
                  '\t\tpl.bus = "Master"\n'
                  '\t\tpl.volume_db = float(spec[1])\n'
                  '\t\tadd_child(pl)\n'
                  '\t\tvar st: AudioStream = load(path)\n'
                  '\t\tif st is AudioStreamOggVorbis:\n'
                  '\t\t\tst.loop = true\n'
                  '\t\tpl.stream = st\n'
                  '\t\tbgm_tracks[track_id] = pl\n'
                  '\tnorden_bgm_player = AudioStreamPlayer.new()', 1)
    print('bgm pool added')

if 'CHAPTER_BGM' not in s:
    s = s.replace('const PHASE_NAMES := {',
                  'const CHAPTER_BGM := {\n'
                  '\t"prologue": "norden_bgm",\n'
                  '\t"ambush": "marysue_world_bgm",\n'
                  '\t"wake_talk": "norden_bgm",\n'
                  '\t"enter_mirror": "mirrorworld_bgm",\n'
                  '\t"mirror": "mirrorworld_bgm",\n'
                  '\t"mirror_meet": "mirrorworld_bgm",\n'
                  '\t"crimson_fall": "interlude_bgm",\n'
                  '\t"final": "interlude_bgm"\n'
                  '}\n'
                  'const PHASE_NAMES := {', 1)
    print('chapter bgm table added')

if 'func _play_bgm' not in s:
    s += '''

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
'''
    print('bgm funcs appended')

# 2) 章节开始时切歌
s = s.replace('func _start_story(id: String) -> void:\n\tseen_speakers.clear()',
              'func _start_story(id: String) -> void:\n\tseen_speakers.clear()\n'
              '\tvar want_bgm := _chapter_bgm(id)\n'
              '\tif want_bgm != "":\n\t\t_play_bgm(want_bgm)', 1)

# 3) 走位段也按背景选（保留原逻辑，但走位段章节内允许章节曲持续）
io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
