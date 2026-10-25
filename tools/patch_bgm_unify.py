# -*- coding: utf-8 -*-
"""统一 BGM：旧函数改为委托 _play_bgm；走位段按章节曲优先。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 记录当前章节
if 'var story_chapter' not in s:
    s = s.replace('var story_intro := ""', 'var story_intro := ""\nvar story_chapter := ""', 1)
    s = s.replace('func _start_story(id: String) -> void:\n\tseen_speakers.clear()',
                  'func _start_story(id: String) -> void:\n\tseen_speakers.clear()\n\tstory_chapter = id', 1)

# 走位段：按章节曲优先
s = s.replace('\tif story_bg == "forest":\n\t\t_start_norden_bgm()\n\t\t_stop_mirror_bgm()\n\telse:\n\t\t_start_mirror_bgm()\n\t\tif map_bgm_player != null and map_bgm_player.playing:\n\t\t\tmap_bgm_player.stop()',
              '\tvar walk_bgm := _chapter_bgm(story_chapter)\n'
              '\tif walk_bgm == "":\n'
              '\t\twalk_bgm = "norden_bgm" if story_bg == "forest" else "mirrorworld_bgm"\n'
              '\t_play_bgm(walk_bgm)', 1)

# 旧函数委托到统一播放
s = s.replace('func _start_norden_bgm() -> void:\n\tif norden_bgm_player != null and norden_bgm_player.stream != null:',
              'func _start_norden_bgm() -> void:\n\t_play_bgm("norden_bgm")\n\tif false:')
s = s.replace('func _start_mirror_bgm() -> void:\n\tif mirror_bgm_player == null or mirror_bgm_player.stream == null:\n\t\treturn\n\tif not mirror_bgm_player.playing:\n\t\tmirror_bgm_player.play()',
              'func _start_mirror_bgm() -> void:\n\t_play_bgm("mirrorworld_bgm")')
s = s.replace('func _start_map_bgm() -> void:\n\tif map_bgm_player == null:\n\t\treturn',
              'func _start_map_bgm() -> void:\n\t_play_bgm("map_bgm")\n\tif map_bgm_player == null:\n\t\treturn')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
