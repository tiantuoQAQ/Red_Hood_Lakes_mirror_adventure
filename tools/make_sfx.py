# -*- coding: utf-8 -*-
"""程序化生成 Godot 用的音效 WAV（不依赖外部素材，风格与网页版 WebAudio 一致）。

产出：audio/sfx/*.wav（22050Hz 单声道 16bit）
    graze.wav     擦弹（短促高频"叮"）
    graze_up.wav  擦弹连击升档（更高更亮）
    dash.wav      冲刺（噪声 whoosh + 下滑音）
    land.wav      落地（低频闷响 + 少量尘土噪声）
    hurt.wav      受击（低频下坠 + 噪声）
    skill.wav     技能（上扬扫频 + 泛音）
    shards.wav    镜碎片（短促高频碎响）

用法：python tools/make_sfx.py
"""
import os
import math
import wave
import numpy as np

SR = 22050
OUT = 'audio/sfx'


def env(n, attack=0.005, decay=0.25, power=2.0):
    a = int(SR * attack)
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    tail = np.linspace(0, 1, n - a) ** power
    e[a:] = 1 - tail * decay / max(decay, 1e-6) * 0 + (1 - tail) * 0
    # 简洁：指数衰减
    t = np.arange(n) / SR
    e = np.exp(-t * (4.0 / max(decay * 4, 0.05)))
    e[:a] *= np.linspace(0, 1, a)
    return e


def tone(freq, dur, kind='sine', detune=0.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    if kind == 'sine':
        w = np.sin(2 * math.pi * freq * t)
    elif kind == 'tri':
        w = 2 * np.abs(2 * ((t * freq) % 1) - 1) - 1
    else:
        w = np.sign(np.sin(2 * math.pi * freq * t))
    if detune:
        w = (w + 0.5 * np.sin(2 * math.pi * freq * 2 * t)) / 1.5
    return w


def sweep(f0, f1, dur, kind='sine'):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = np.linspace(f0, f1, n)
    phase = 2 * math.pi * np.cumsum(f) / SR
    w = np.sin(phase) if kind == 'sine' else 2 * np.abs(2 * ((phase / (2 * math.pi)) % 1) - 1) - 1
    return w


def noise(dur, lowpass=0.35):
    n = int(SR * dur)
    x = np.random.RandomState(7).randn(n)
    # 一阶低通
    y = np.zeros(n)
    acc = 0.0
    for i in range(n):
        acc = acc + lowpass * (x[i] - acc)
        y[i] = acc
    return y


def mix(*segs):
    n = max(len(x) for x in segs)
    out = np.zeros(n)
    for x in segs:
        out[:len(x)] += x
    return out


def save(name, x, gain=0.8):
    os.makedirs(OUT, exist_ok=True)
    x = np.asarray(x, dtype=np.float64)
    x = x / max(1e-9, np.max(np.abs(x))) * gain
    data = (x * 32767).astype('<i2').tobytes()
    with wave.open(os.path.join(OUT, name), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    print('  ', name, '%.2fs' % (len(x) / SR))


def main():
    print('生成音效 ->', OUT)
    # 擦弹：极短高频叮
    x = mix(tone(1760, 0.10, 'sine') * env(int(SR * 0.10), 0.002, 0.10),
            tone(2640, 0.08, 'sine') * 0.4 * env(int(SR * 0.08), 0.001, 0.06))
    save('graze.wav', x, 0.5)

    # 擦弹升档：更高更亮
    x = mix(tone(2200, 0.14, 'sine') * env(int(SR * 0.14), 0.002, 0.13),
            tone(3300, 0.12, 'sine') * 0.5 * env(int(SR * 0.12), 0.001, 0.10))
    save('graze_up.wav', x, 0.55)

    # 冲刺：噪声 whoosh + 下滑
    d = 0.22
    n = int(SR * d)
    x = mix(noise(d, 0.5) * 0.9 * env(n, 0.004, d * 0.8, 1.5),
            sweep(900, 260, d) * 0.45 * env(n, 0.004, d, 1.2))
    save('dash.wav', x, 0.65)

    # 落地：低频闷响 + 粉尘
    d = 0.20
    n = int(SR * d)
    x = mix(sweep(180, 60, d) * 0.9 * env(n, 0.002, d, 1.8),
            noise(d, 0.18) * 0.35 * env(n, 0.002, 0.12, 2.0))
    save('land.wav', x, 0.6)

    # 受击
    d = 0.35
    n = int(SR * d)
    x = mix(sweep(420, 90, d) * 0.8 * env(n, 0.002, d, 1.4),
            noise(d, 0.3) * 0.5 * env(n, 0.002, 0.18, 1.8))
    save('hurt.wav', x, 0.7)

    # 技能：上扬扫频 + 泛音
    d = 0.55
    n = int(SR * d)
    sw = sweep(300, 1400, d)
    x = mix(sw * 0.7 * env(n, 0.01, d, 1.1),
            sw * 2 * 0.25 * env(n, 0.01, d * 0.8, 1.3))
    save('skill.wav', x, 0.6)

    # 镜碎片：短促高频碎响（多条随机短音叠加）
    d = 0.45
    n = int(SR * d)
    x = np.zeros(n)
    rs = np.random.RandomState(3)
    for i in range(14):
        st = int(rs.rand() * (n - 2000))
        ln = int(rs.rand() * 1800) + 400
        f = rs.uniform(1200, 4200)
        seg = tone(f, ln / SR, 'sine')
        e2 = env(len(seg), 0.001, 0.05, 2.0)
        seg = seg[:len(e2)] * e2 * (0.5 + rs.rand() * 0.5)
        x[st:st + len(seg)] += seg[:n - st]
    save('shards.wav', x, 0.55)

    print('完成：', len(os.listdir(OUT)), '个文件')


if __name__ == '__main__':
    main()
