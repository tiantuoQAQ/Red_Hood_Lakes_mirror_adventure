# -*- coding: utf-8 -*-
"""重做冲刺音效：柔和的布料/空气 whoosh（去掉刺耳高频噪声）。"""
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


def lowpass(x, alpha):
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += alpha * (x[i] - acc)
        y[i] = acc
    return y


# 冲刺：低频空气流动 + 轻微布料的柔和 whoosh，无尖啸
d = 0.30
n = int(SR * d)
t = np.arange(n) / SR
rs = np.random.RandomState(11)
noise = rs.randn(n)
air = lowpass(lowpass(noise, 0.10), 0.10)          # 很低的频段
body = lowpass(noise, 0.06)
env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.6   # 平滑起落
x = air * 0.9 * env + body * 0.35 * env
# 一点点柔和的低频扫频，给出"发力"感
x += 0.18 * np.sin(2 * math.pi * (90 - 40 * t / d) * t) * env
save('dash.wav', x, 0.55)
print('done')
