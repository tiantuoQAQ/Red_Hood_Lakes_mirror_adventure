# 修正粒子贴图的色相：把偏暖的米色星点改成中性白，保留 alpha 与形状。
# 用法: python tools/_fix_fx_palette.py <in.png> [out.png]
import os
import sys
import colorsys
from PIL import Image


def fix(path, out):
    im = Image.open(path).convert('RGBA')
    px = im.load()
    w, h = im.size
    changed = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            hh, ll, ss = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
            deg = hh * 360.0
            # 红(0°) 与青(196°) 是允许的；其余有彩色的像素一律拉成中性白
            if ss < 0.06:
                continue
            near_red = deg < 8 or deg > 352
            near_cyan = 184 <= deg <= 208
            if near_red or near_cyan:
                continue
            # 保持明度，去掉色相，做成中性灰白
            v = int(round(255 * (0.55 + 0.45 * ll)))
            px[x, y] = (v, v, v, a)
            changed += 1
    im.save(out)
    print('修正像素: {} / {}   -> {}'.format(changed, w * h, out))


if __name__ == '__main__':
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    fix(src, dst)
