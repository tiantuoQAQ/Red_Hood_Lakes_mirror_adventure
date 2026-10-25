# -*- coding: utf-8 -*-
"""把红色法环帧转成绿色（黄绿 89.4°）：逐像素强制设定色相，保留亮度/饱和度。"""
import glob
import colorsys
import numpy as np
from PIL import Image

SRC = 'art/battle/scarlet/ring/frame_*.png'
DST = 'art/battle/marysue/ring/'
HUE = 89.4 / 360.0


def convert(path):
    im = Image.open(path).convert('RGBA')
    a = np.array(im).astype(np.float32) / 255.0
    rgb, alpha = a[:, :, :3], a[:, :, 3]
    h, w = alpha.shape
    out = rgb.reshape(-1, 3).copy()
    al = alpha.reshape(-1)
    for i in range(out.shape[0]):
        if al[i] <= 0.01:
            continue
        r, g, b = out[i]
        _, l, s = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if s < 0.02:
            # 灰白像素：略微带绿，避免整帧变灰
            s = 0.35 if l > 0.5 else 0.15
        nr, ng, nb = colorsys.hls_to_rgb(HUE, l, max(s, 0.25))
        out[i] = (nr, ng, nb)
    res = np.concatenate([out.reshape(rgb.shape), alpha[:, :, None]], axis=2)
    Image.fromarray(np.clip(res * 255.0, 0, 255).astype(np.uint8), 'RGBA').save(path)


for f in sorted(glob.glob(SRC)):
    name = f.split('\\')[-1].split('/')[-1]
    im = Image.open(f).convert('RGBA')
    tmp = DST + name
    im.save(tmp)
    convert(tmp)
print('绿色法环转换完成')
