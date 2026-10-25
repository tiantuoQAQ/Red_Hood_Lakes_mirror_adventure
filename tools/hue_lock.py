# -*- coding: utf-8 -*-
"""色相锁定：把彩色像素的色相吸附到允许的三个色相（0° / 89.4° / 196.2°），
保留原亮度与饱和度，不做去色。用于战斗大图（贴图不是纯色块，force_palette 会把它去色）。

用法：
    python tools/hue_lock.py <文件...> [--sat-min 0.18] [--dry]
"""
import sys
import colorsys
import numpy as np
from PIL import Image

ALLOWED = [0.0, 89.4 / 360.0, 196.2 / 360.0]
SAT_MIN = 0.04
CHROMA_MIN = 10


def nearest_hue(h):
    best, bd = ALLOWED[0], 9
    for a in ALLOWED:
        d = abs(h - a)
        d = min(d, 1 - d)
        if d < bd:
            bd, best = d, a
    return best


def run(path, dry=False):
    im = Image.open(path).convert('RGBA')
    a = np.array(im).astype(np.float32) / 255.0
    rgb, alpha = a[:, :, :3], a[:, :, 3]
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    chroma = (mx - mn) * 255
    changed = 0
    h, w = chroma.shape
    flat = rgb.reshape(-1, 3)
    out = flat.copy()
    idx = np.where((chroma.reshape(-1) > CHROMA_MIN) & (alpha.reshape(-1) > 0.05))[0]
    for i in idx:
        r, g, b = flat[i]
        hh, ll, ss = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if ss < SAT_MIN:
            continue
        # 皮肤：橙粉色系且偏亮 → 收成中性灰（R=G=B）
        hue_deg = hh * 360.0
        if 5.0 <= hue_deg <= 50.0 and ll > 0.62 and ss < 0.55:
            out[i] = (ll, ll, ll)
            changed += 1
            continue
        nh = nearest_hue(hh)
        if abs(nh - hh) < 1e-4:
            continue
        nr, ng, nb = colorsys.hls_to_rgb(nh, ll, ss)
        out[i] = (nr, ng, nb)
        changed += 1
    rgb2 = out.reshape(rgb.shape)
    res = np.concatenate([rgb2, alpha[:, :, None]], axis=2)
    img = Image.fromarray(np.clip(res * 255.0, 0, 255).astype(np.uint8), 'RGBA')
    if dry:
        print(path, '将改动像素', changed, '（dry run，未写盘）')
        return changed
    img.save(path)
    print(path, '色相吸附像素', changed)
    return changed


if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    dry = '--dry' in sys.argv
    for f in args:
        run(f, dry)
