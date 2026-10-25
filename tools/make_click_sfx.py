# -*- coding: utf-8 -*-
"""「啪嗒」机关声：短促的机械卡扣（木质 + 金属轻碰），0.12s。"""
import math
import os
import wave
import numpy as np

SR = 22050
OUT = 'audio/sfx/click.wav'


def save(path, x, gain=0.85):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    x = np.asarray(x, float)
    x = x / max(1e-9, np.abs(x).max()) * gain
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())
    print('click.wav', '%.3fs' % (len(x) / SR))


d = 0.13
n = int(SR * d)
t = np.arange(n) / SR
rs = np.random.RandomState(41)

# 三部分：木质闷击 + 金属轻响 + 极短噪声"咔"
wood = np.sin(2 * math.pi * (180 * np.exp(-t * 26) + 70) * t) * np.exp(-t * 42)
metal = np.sin(2 * math.pi * 2350 * t) * np.exp(-t * 95) * 0.35
metal += np.sin(2 * math.pi * 3150 * t) * np.exp(-t * 120) * 0.18
click = rs.randn(n) * np.exp(-t * 260) * 0.25

x = wood * 0.9 + metal + click
# 5ms 起音，避免爆音
a = int(SR * 0.005)
x[:a] *= np.linspace(0, 1, a)
# 尾部 20ms 收干净
tail = int(SR * 0.02)
x[-tail:] *= np.linspace(1, 0, tail)
save(OUT, x, 0.9)
