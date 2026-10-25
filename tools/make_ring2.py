# -*- coding: utf-8 -*-
"""把 gpt-image-2 生成的法环图处理成游戏用透明环（红/绿两版）。

产出：
    art/battle/scarlet/ring2/circle.png   红色法环（透明底，1024 见方裁剪后 ~1000）
    art/battle/marysue/ring2/circle.png   绿色法环（同构，色相锁 89.4°）

说明：单帧 + 引擎旋转即可（对称环形旋转不会露馅），比 40 帧序列更省内存且更圆。
"""
import os
import colorsys
import numpy as np
from PIL import Image

SRC = 'art/logo/ring_raw.png'
OUTS = [('art/battle/scarlet/ring2/circle.png', 0.0), ('art/battle/marysue/ring2/circle.png', 89.4)]


def key_black(im):
    """黑底转透明：按亮度给 alpha，保留辉光的半透明过渡"""
    a = np.array(im.convert('RGBA')).astype(np.float32)
    rgb = a[:, :, :3]
    mx = rgb.max(axis=2)
    alpha = np.clip((mx - 8.0) / 120.0, 0.0, 1.0) ** 0.75   # 暗处透明，亮处不透明
    out = np.dstack([rgb / 255.0, alpha]).astype(np.float32)
    return out


def recolour(arr, target_deg):
    """把所有不透明像素的色相统一到 target_deg，保留亮度与饱和度"""
    rgb = arr[:, :, :3].copy()
    alpha = arr[:, :, 3]
    h, w = alpha.shape
    flat = rgb.reshape(-1, 3)
    al = alpha.reshape(-1)
    tgt = target_deg / 360.0
    for i in range(flat.shape[0]):
        if al[i] <= 0.02:
            continue
        r, g, b = flat[i]
        _, l, s = colorsys.rgb_to_hls(float(r), float(g), float(b))
        s = max(s, 0.55)          # 保证是明确的彩色
        nr, ng, nb = colorsys.hls_to_rgb(tgt, l, s)
        flat[i] = (nr, ng, nb)
    return np.dstack([flat.reshape(rgb.shape), alpha])


def main():
    im = Image.open(SRC).convert('RGBA')
    arr = key_black(im)
    for path, hue in OUTS:
        out = recolour(arr.copy(), hue)
        img = Image.fromarray(np.clip(out * 255.0, 0, 255).astype(np.uint8), 'RGBA')
        bb = img.getbbox()
        img = img.crop(bb)
        # 正方形画布，边留 2%
        side = max(img.width, img.height)
        pad = int(side * 0.02)
        side += pad * 2
        canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
        canvas.alpha_composite(img, ((side - img.width) // 2, (side - img.height) // 2))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        canvas.save(path)
        print(path, canvas.size)


if __name__ == '__main__':
    main()
