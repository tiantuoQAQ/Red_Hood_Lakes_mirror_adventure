# -*- coding: utf-8 -*-
"""导入「法环」透明帧：裁剪到环的包围盒、统一尺寸、色相锁到规范色，供游戏实时旋转/播放。

来源：E:/UserDATAxtmr/Desktop/mirror/scarlet-cape-ring-overlay-frames/frame-XXX.png（97 帧透明 PNG）
产出：
    art/battle/scarlet/ring/frame_00.png ...  （红，40 帧 @20fps 循环）
    art/battle/marysue/ring/frame_00.png ...  （绿，同帧序列重上色）

用法：python tools/import_rings.py
"""
import os
import glob
import math
import numpy as np
from PIL import Image

SRC = 'E:/UserDATAxtmr/Desktop/mirror/scarlet-cape-ring-overlay-frames'
OUT_RED = 'art/battle/scarlet/ring'
OUT_GREEN = 'art/battle/marysue/ring'
KEEP = 40                      # 97 帧里均匀抽 40 帧
RING_SCALE = 0.90              # 统一缩放（环视觉直径 ≈ 594px，约为角色高度的 2.3 倍）


def hue_to(rgba, target_deg):
    """把彩色像素的色相吸附到 target_deg，保留亮度/饱和度（只动有透明度的像素）"""
    import colorsys
    a = np.array(rgba).astype(np.float32) / 255.0
    rgb, alpha = a[:, :, :3], a[:, :, 3]
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    mask = (sat > 0.04) & (alpha > 0.02)
    idx = np.where(mask.reshape(-1))[0]
    flat = rgb.reshape(-1, 3)
    tgt = target_deg / 360.0
    for i in idx:
        r, g, b = flat[i]
        h, l, s = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if s < 0.04:
            continue
        nr, ng, nb = colorsys.hls_to_rgb(tgt, l, s)
        flat[i] = (nr, ng, nb)
    res = np.concatenate([flat.reshape(rgb.shape), alpha[:, :, None]], axis=2)
    return Image.fromarray(np.clip(res * 255.0, 0, 255).astype(np.uint8), 'RGBA')


def main():
    files = sorted(glob.glob(os.path.join(SRC, 'frame-*.png')))
    if not files:
        print('没找到源帧:', SRC)
        return
    idxs = [int(round(i * (len(files) - 1) / (KEEP - 1))) for i in range(KEEP)]
    os.makedirs(OUT_RED, exist_ok=True)
    os.makedirs(OUT_GREEN, exist_ok=True)

    # 先用第一帧定包围盒（所有帧同尺寸）
    base = Image.open(files[0]).convert('RGBA')
    bb = base.getbbox()
    ring_d = max(bb[2] - bb[0], bb[3] - bb[1])
    scale = RING_SCALE
    print('环包围盒', bb, '直径', ring_d, '-> 缩放', round(scale, 3))

    for n, i in enumerate(idxs):
        im = Image.open(files[i]).convert('RGBA')
        im = im.crop(bb)
        w, h = int(im.width * scale), int(im.height * scale)
        im = im.resize((w, h), Image.LANCZOS)
        im.save(os.path.join(OUT_RED, 'frame_%02d.png' % n))
        hue_to(im, 89.4).save(os.path.join(OUT_GREEN, 'frame_%02d.png' % n))
    print('导出', KEEP, '帧 ->', OUT_RED, '与', OUT_GREEN)


if __name__ == '__main__':
    main()
