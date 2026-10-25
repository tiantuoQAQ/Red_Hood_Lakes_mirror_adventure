# -*- coding: utf-8 -*-
"""冲刺音效 v3：柔和的"呼——"空气声（低通噪声 + 缓慢包络），完全去掉尖啸与金属感。"""
import math
import os
import wave
import numpy as np

SR = 22050
OUT = 'audio/sfx'


def save(name, x, gain=0.8):
    os.makedirs(OUT, exist_ok=True)
    x = np.asarray(x, float)
    x = x / max(1e-9, np.abs(x).max()) * gain
    with wave.open(os.path.join(OUT, name), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())
    print(name, '%.2fs' % (len(x) / SR))


def one_pole(x, a):
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def bandpass(x, lo, hi):
    return one_pole(one_pole(x, hi), hi) - one_pole(one_pole(x, lo), lo)


d = 0.26
n = int(SR * d)
t = np.arange(n) / SR
rs = np.random.RandomState(23)

# 两层柔和的带通噪声，模拟布料摩擦 + 空气流动
cloth = bandpass(rs.randn(n), 0.02, 0.06)
air = bandpass(rs.randn(n), 0.004, 0.02)
env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2.2      # 缓慢起落，无突变
x = cloth * 0.6 * env + air * 0.9 * env
# 极轻的低频推感
x += 0.10 * np.sin(2 * math.pi * (70 - 25 * t / d) * t) * env
# 尾部快速收干净，避免"啪"的截断
fade = np.ones(n)
tail = int(SR * 0.06)
fade[-tail:] = np.linspace(1, 0, tail) ** 1.8
x *= fade
save('dash.wav', x, 0.5)
print('done')
