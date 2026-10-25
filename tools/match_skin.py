# -*- coding: utf-8 -*-
"""把立绘的「皮肤灰」亮度对齐到统一目标，解决不同批次出图肤色深浅不一的问题。

只作用于低彩度像素（chroma < 0.08，即已经压成中性的皮肤/白发/白衣），
按脸部区域的灰阶中位数算一个增益，再整体乘上去。色相不变，所以不会破三色规范。

用法：
    python tools/match_skin.py art/portrait/*.png --target 0.70
"""
import sys
import glob
from PIL import Image

TARGET = 0.70
FACTOR_MIN = 0.88
FACTOR_MAX = 1.38
FACE_BOX = (0.28, 0.18, 0.72, 0.46)   # 相对坐标，取脸部区域
CHROMA_MAX = 0.08


def face_gray_median(im):
    w, h = im.size
    x0, y0, x1, y1 = FACE_BOX
    box = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
    px = box.load()
    bw, bh = box.size
    vals = []
    for y in range(0, bh, 2):
        for x in range(0, bw, 2):
            r, g, b, a = px[x, y]
            if a < 200:
                continue
            if (max(r, g, b) - min(r, g, b)) / 255.0 > 0.06:
                continue
            vals.append((r + g + b) / 765.0)
    if not vals:
        return None
    vals.sort()
    return vals[len(vals) // 2]


def process(path, target=TARGET):
    im = Image.open(path).convert('RGBA')
    med = face_gray_median(im)
    if med is None or med <= 0.01:
        print('跳过（无灰度皮肤）:', path)
        return
    factor = target / med
    factor = max(FACTOR_MIN, min(FACTOR_MAX, factor))
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            mx, mn = max(r, g, b), min(r, g, b)
            if (mx - mn) / 255.0 > CHROMA_MAX:
                continue
            px[x, y] = (
                min(255, int(r * factor + 0.5)),
                min(255, int(g * factor + 0.5)),
                min(255, int(b * factor + 0.5)),
                a,
            )
    im.save(path)
    print('对齐肤色: {}  脸中位 {:.2f} -> {:.2f}  增益 {:.2f}'.format(path, med, target, factor))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--target' in sys.argv:
        TARGET = float(sys.argv[sys.argv.index('--target') + 1])
        args = [a for a in args if a != str(TARGET)]
    files = []
    for a in args:
        files.extend(glob.glob(a))
    for f in files:
        process(f, TARGET)
