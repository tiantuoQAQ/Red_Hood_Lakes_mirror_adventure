# -*- coding: utf-8 -*-
"""Boss 战第二阶段大改：开场动画、必杀插图、旋风、锁定突刺锋、大光球爆炸、随机激光、绿闪、镜像翻转、逐阶段招式。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# ---------- 变量 ----------
if 'var whirls: Array' not in s:
    s = s.replace(
        'var cutin_active := false\nvar cutin_timer := 0.0',
        'var cutin_active := false\nvar cutin_timer := 0.0\n'
        'var battle_intro_t := 0.0     # 开场动画剩余秒数\n'
        'var whirls: Array = []        # 地面旋风 {x, phase}\n'
        'var lock_timer := 0.0         # 锁定突刺计时\n'
        'var lock_target := Vector2.ZERO\n'
        'var lock_state := ""          # "", "aim", "spike"\n'
        'var spikes: Array = []        # 突刺锋 {pos, life, max}\n'
        'var green_flash_t := 0.0      # 全屏绿闪剩余秒数\n'
        'var mirror_flip := false      # 第六阶段：左右交换', 1)
    print('vars added')

# ---------- 开场动画 + 重置 ----------
if 'battle_intro_t = 2.6' not in s:
    s = s.replace(
        '\tmode = Mode.BATTLE\n\tboss_id = id',
        '\tmode = Mode.BATTLE\n\tbattle_intro_t = 2.6\n\tcutin_active = false\n\tcutin_timer = 0.0\n\twhirls.clear()\n\tspikes.clear()\n\tlock_state = ""\n\tlock_timer = 0.0\n\tgreen_flash_t = 0.0\n\tmirror_flip = false\n\tboss_id = id', 1)
    print('battle intro reset added')

# ---------- 进入最后阶段时弹「！」 ----------
if 'cutin_active = true' not in s:
    s = s.replace(
        '\t\t\tbanner = "PHASE %d" % (boss_phase + 1)\n\t\t\tbanner_timer = 85',
        '\t\t\tbanner = "PHASE %d" % (boss_phase + 1)\n\t\t\tbanner_timer = 85\n'
        '\t\t\tif boss_phase == boss_phase_count - 1:\n'
        '\t\t\t\tcutin_active = true\n'
        '\t\t\t\tcutin_timer = 2.0\n'
        '\t\t\t\tsfx_player.play("skill")\n'
        '\t\t\t\t_spawn_mirror_shards(18, 1.2)', 1)
    print('cutin trigger added')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
