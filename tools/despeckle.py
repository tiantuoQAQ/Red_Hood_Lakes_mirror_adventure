# -*- coding: utf-8 -*-
"""清除「绿色残斑」：压色后，皮肤/腿部上残留的低彩度绿会变成脏斑点。

做法：对每个偏绿的像素，看它周围窗口里同色像素的占比；
占比太低（孤立/边缘过渡）就把它转成中性灰，占比高（真正的头发/衣服）保留。

用法：
    python tools/despeckle.py art/portrait/marysue.png [--win 9] [--min 0.35] [--hue 120]
"""
import sys
import glob
import colorsys
from PIL import Image

WIN = 9
MIN_RATIO = 0.35
HUE_TOL = 120.0     # 与「绿」的允许偏差（度）
GREEN_HUE = 89.4


def is_greenish(r, g, b):
    mx, mn = max(r, g, b), min(r, g, b)
    if (mx - mn) / 255.0 < 0.12:
        return False
    hh, ll, ss = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    deg = hh * 360.0
    d = abs(deg - GREEN_HUE)
    d = min(d, 360 - d)
    return d <= HUE_TOL


def process(path, win=WIN, min_ratio=MIN_RATIO):
    im = Image.open(path).convert('RGBA')
    px = im.load()
    w, h = im.size
    mask = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 0 and is_greenish(r, g, b):
                mask[y][x] = True

    half = win // 2
    fixed = 0
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            tot = 0
            hit = 0
            for dy in range(-half, half + 1):
                yy = y + dy
                if yy < 0 or yy >= h:
                    continue
                for dx in range(-half, half + 1):
                    xx = x + dx
                    if xx < 0 or xx >= w:
                        continue
                    r, g, b, a = px[xx, yy]
                    if a == 0:
                        continue
                    tot += 1
                    if mask[yy][xx]:
                        hit += 1
            if tot and hit / tot < min_ratio:
                r, g, b, a = px[x, y]
                v = int(round((r + g + b) / 3))
                px[x, y] = (v, v, v, a)
                fixed += 1
    im.save(path)
    print('去绿斑: {}  清理 {} px'.format(path, fixed))


if __name__ == '__main__':
    args = sys.argv[1:]
    files = [a for a in args if not a.startswith('--')]
    if '--win' in args:
        WIN = int(args[args.index('--win') + 1])
        files = [f for f in files if f != str(WIN)]
    if '--min' in args:
        MIN_RATIO = float(args[args.index('--min') + 1])
        files = [f for f in files if f != str(MIN_RATIO)]
    expanded = []
    for pattern in files:
        hits = glob.glob(pattern)
        expanded.extend(hits if hits else [pattern])
    for f in expanded:
        process(f)
