# -*- coding: utf-8 -*-
"""白底图的 alpha 抠像精修：
对「紧贴透明区 2px 内」的像素，按与白色的混合程度重算 alpha，并反预乘颜色，
这样白边会变成半透明过渡，不会留一圈硬白。

用法：
    python tools/matte_white.py art/portrait/mabel.png [--band 2]
"""
import sys
import glob
from PIL import Image

BAND = 2


def near_transparent(alpha, W, H, x, y, r):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            nx, ny = x + dx, y + dy
            if nx < 0 or ny < 0 or nx >= W or ny >= H:
                return True
            if alpha[ny][nx] < 8:
                return True
    return False


def run(path, band=BAND):
    im = Image.open(path).convert('RGBA')
    px = im.load()
    W, H = im.size

    alpha = [[px[x, y][3] for x in range(W)] for y in range(H)]
    edits = []
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if not near_transparent(alpha, W, H, x, y, band):
                continue
            mn = min(r, g, b)
            # 与白色的混合度：越白越透明
            na = max(0, min(255, int((255 - mn) * 1.02)))
            if na >= a:
                continue
            if na < 24:
                edits.append((x, y, (r, g, b, 0)))
                continue
            # 反预乘：把白色背景贡献去掉
            k = na / 255.0
            nr = int(max(0, min(255, (r - 255 * (1 - k)) / max(k, 0.01))))
            ng = int(max(0, min(255, (g - 255 * (1 - k)) / max(k, 0.01))))
            nb = int(max(0, min(255, (b - 255 * (1 - k)) / max(k, 0.01))))
            edits.append((x, y, (nr, ng, nb, na)))

    for x, y, col in edits:
        px[x, y] = col
    im.save(path)
    print(path, 'matte pixels', len(edits))


if __name__ == '__main__':
    args = sys.argv[1:]
    files = [a for a in args if not a.startswith('--')]
    if '--band' in args:
        BAND = int(args[args.index('--band') + 1])
        files = [f for f in files if f != str(BAND)]
    expanded = []
    for p in files:
        hits = glob.glob(p)
        expanded.extend(hits if hits else [p])
    for f in expanded:
        run(f)
