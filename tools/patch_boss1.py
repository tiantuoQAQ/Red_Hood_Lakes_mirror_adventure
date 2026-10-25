# -*- coding: utf-8 -*-
"""Boss 战大改：
1) 新音效注册（lock_beep / spike / explode）
2) 每阶段名字（显示在血条下方）
3) 开场播放 mp4 抽帧序列
4) 最后阶段进入时弹「！」必杀插图并短暂冻结
"""
import io

# ---------- 1) SFX ----------
p = 'godot/sfx_player.gd'
s = io.open(p, encoding='utf-8').read()
if 'lock_beep' not in s:
    s = s.replace('\t_load_sfx("shards", "res://audio/sfx/shards.wav")',
                  '\t_load_sfx("shards", "res://audio/sfx/shards.wav")\n'
                  '\t_load_sfx("lock_beep", "res://audio/sfx/lock_beep.wav")\n'
                  '\t_load_sfx("spike", "res://audio/sfx/spike.wav")\n'
                  '\t_load_sfx("explode", "res://audio/sfx/explode.wav")', 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('sfx registered')

# ---------- 2) main.gd ----------
p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 阶段名常量
if 'PHASE_NAMES' not in s:
    s = s.replace('const VIEW := Vector2(1280.0, 720.0)',
                  'const PHASE_NAMES := {\n'
                  '\t"crimson": ["壹 · 试锋", "贰 · 裂帛", "叁 · 血雨", "肆 · 镜刃", "伍 · 红之惨剧"],\n'
                  '\t"marysue": ["壹 · 箱庭", "贰 · 反语", "叁 · 镜廊", "肆 · 断线", "伍 · 狂言", "陆 · 天地倒悬"]\n'
                  '}\n'
                  'const VIEW := Vector2(1280.0, 720.0)', 1)
    print('phase names const added')

# 血条下方画阶段名
if 'PHASE_NAMES.get' not in s:
    s = s.replace(
        '\tvar stage_label := "STAGE %d / %d" % [boss_phase + 1, boss_phase_count] if boss_id == "crimson" else "STAGE %d" % (boss_phase + 1)',
        '\tvar stage_label := "STAGE %d / %d" % [boss_phase + 1, boss_phase_count] if boss_id == "crimson" else "STAGE %d" % (boss_phase + 1)', 1)
    # 在 stage_label 绘制之后追加阶段名
    s = s.replace(
        '\tdraw_string(ThemeDB.fallback_font, Vector2(940, 118), stage_label, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color(0.85, 0.85, 0.85))',
        '\tdraw_string(ThemeDB.fallback_font, Vector2(940, 118), stage_label, HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color(0.85, 0.85, 0.85))\n'
        '\tvar pnames: Array = PHASE_NAMES.get(boss_id, [])\n'
        '\tif boss_phase < pnames.size():\n'
        '\t\tdraw_string(ThemeDB.fallback_font, Vector2(1060, 118), str(pnames[boss_phase]), HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(RED if boss_id == "crimson" else HAZARD))', 1)
    print('phase name hud added')

# 开场帧序列加载 + 播放
if 'intro_anim' not in s:
    s = s.replace('var boss_anim: Dictionary = {}   # 魔姬动作帧: idle/move/thrust/slash',
                  'var boss_anim: Dictionary = {}   # 魔姬动作帧: idle/move/thrust/slash\n'
                  'var intro_anim: Dictionary = {}  # 战前开场视频帧: crimson / marysue\n'
                  'var cutin_active := false\n'
                  'var cutin_timer := 0.0', 1)
    s = s.replace('\t# 猩红魔姬动作序列（来自即梦视频，每套 16 帧）',
                  '\t# 战前开场动画帧（即梦 mp4 抽帧，24 帧）\n'
                  '\tfor who in ["crimson", "marysue"]:\n'
                  '\t\tvar iframes: Array = []\n'
                  '\t\tfor fi in range(24):\n'
                  '\t\t\tvar itex := _load_texture("res://art/cg/intro_%s/frame_%02d.png" % [who, fi])\n'
                  '\t\t\tif itex:\n'
                  '\t\t\t\tiframes.append(itex)\n'
                  '\t\tif iframes.size() > 0:\n'
                  '\t\t\tintro_anim[who] = iframes\n'
                  '\t# 猩红魔姬动作序列（来自即梦视频，每套 16 帧）', 1)
    print('intro frames loader added')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
