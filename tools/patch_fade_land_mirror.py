# -*- coding: utf-8 -*-
"""1) 落地音效换柔和版 2) 镜子保证出现在玩家前方 3) 场景淡入淡出加缓动（丝滑）"""
import io
import math
import os
import wave
import numpy as np

# ---------- 1) 落地音效 ----------
SR = 22050


def one_pole(x, a):
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def save(name, x, gain=0.8):
    os.makedirs('audio/sfx', exist_ok=True)
    x = np.asarray(x, float)
    x = x / max(1e-9, np.abs(x).max()) * gain
    with wave.open('audio/sfx/' + name, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())
    print(name, '%.2fs' % (len(x) / SR))


d = 0.22
n = int(SR * d)
t = np.arange(n) / SR
rs = np.random.RandomState(31)
# 柔和闷响：低频正弦快速衰减 + 一点点中频"沙"，没有金属/脆响
thud = np.sin(2 * math.pi * (110 * np.exp(-t * 6) + 55) * t) * np.exp(-t * 22)
sand = one_pole(rs.randn(n), 0.05) * np.exp(-t * 30) * 0.5
env = np.clip(t / 0.006, 0, 1)  # 极短 attack，避免"啪"
x = (thud * 0.9 + sand) * env
tail = int(SR * 0.04)
x[-tail:] *= np.linspace(1, 0, tail)
save('land.wav', x, 0.75)

# ---------- 2)(3) 代码补丁 ----------
p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 镜子目标保证在玩家前方
s = s.replace(
    '\tif long_map:\n\t\tif walk_target.has("x"):\n\t\t\twalk_target["x"] = float(walk_target["x"]) + WALK_SHIFT',
    '\tif long_map:\n\t\tif walk_target.has("x"):\n\t\t\twalk_target["x"] = float(walk_target["x"]) + WALK_SHIFT\n'
    '\t\t# 镜子/交互物必须在玩家前方，否则玩家会以为"没东西可交互"（用户反馈）\n'
    '\t\tif str(walk_target.get("kind", "")) == "mirror" and float(walk_target.get("x", 0.0)) < player_pos.x + 400.0:\n'
    '\t\t\twalk_target["x"] = player_pos.x + 700.0', 1)

# 淡入淡出加缓动：用 ease（smoothstep）而不是线性 move_toward
if 'story_fade_t' not in s:
    s = s.replace('var story_fade_speed := 0.0',
                  'var story_fade_speed := 0.0\nvar story_fade_t := 0.0        # 0→1 进度，用于缓动\nvar story_fade_from := 0.0\nvar story_fade_to := 0.0', 1)
    s = s.replace('\t\t\t\tstory_fade_speed = 1.0 / maxf(FIXED_DT, story_timer)',
                  '\t\t\t\tstory_fade_speed = 1.0 / maxf(FIXED_DT, story_timer)\n'
                  '\t\t\t\tstory_fade_from = story_fade\n'
                  '\t\t\t\tstory_fade_to = story_fade_target\n'
                  '\t\t\t\tstory_fade_t = 0.0', 1)
    # 每帧缓动推进
    s = s.replace('\tif story_fade != story_fade_target:\n\t\tstory_fade = move_toward(story_fade, story_fade_target, story_fade_speed * FIXED_DT)',
                  '\tif story_fade != story_fade_target:\n'
                  '\t\tstory_fade_t = minf(1.0, story_fade_t + story_fade_speed * FIXED_DT)\n'
                  '\t\tvar k := story_fade_t * story_fade_t * (3.0 - 2.0 * story_fade_t)   # smoothstep 缓动\n'
                  '\t\tstory_fade = lerpf(story_fade_from, story_fade_to, k)', 1)
    print('fade eased')

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
