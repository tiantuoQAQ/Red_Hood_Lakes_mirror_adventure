# -*- coding: utf-8 -*-
"""1) 对话框名牌直接显示称号（保底可见）2) 地图 BGM 支持 3) 竖幅触发更稳"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---- 1) 名牌：名字 + 称号 ----
old = '\t\t\tvar shown_name := "？？？" if story_expr == "shadow" else _display_name(story_who)'
new = '''			var shown_name := "？？？" if story_expr == "shadow" else _display_name(story_who)
			if story_expr != "shadow":
				var skey := _portrait_base(story_who)
				if CHAR_TITLES.has(skey):
					var ttl := str(CHAR_TITLES[skey].get("title", ""))
					if ttl != "":
						shown_name = shown_name + "  ·  " + ttl'''
if old in s:
    s = s.replace(old, new, 1)
    print('nameplate title added')

# ---- 2) 地图 BGM ----
if 'map_bgm_player' not in s:
    s = s.replace('var intro_hold := 0.0', 'var map_bgm_player: AudioStreamPlayer\nvar map_bgm_started := false\nvar intro_hold := 0.0', 1)
    s = s.replace('func _ready() -> void:',
                  'func _ready() -> void:\n'
                  '\tmap_bgm_player = AudioStreamPlayer.new()\n'
                  '\tmap_bgm_player.bus = "Master"\n'
                  '\tmap_bgm_player.volume_db = -10.0\n'
                  '\tadd_child(map_bgm_player)\n'
                  '\tif ResourceLoader.exists("res://audio/map_bgm.ogg"):\n'
                  '\t\tmap_bgm_player.stream = load("res://audio/map_bgm.ogg")\n', 1)
    print('map bgm player added')

# 进走位段播地图 BGM；进战斗停
s = s.replace('\tif last_left != "" or last_right != "":\n\t\tportrait_fade = 1.0',
              '\tif last_left != "" or last_right != "":\n\t\tportrait_fade = 1.0\n'
              '\t_start_map_bgm()', 1)
if 'func _start_map_bgm' not in s:
    s += '''

## 地图/走位段 BGM：把音乐文件放 audio/map_bgm.ogg 即自动循环播放
func _start_map_bgm() -> void:
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
'''

# 战斗开始停地图 BGM
s = s.replace('\tmode = Mode.BATTLE\n\tbattle_intro_t = 2.6', '\tmode = Mode.BATTLE\n\t_stop_map_bgm()\n\tbattle_intro_t = 2.6', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
