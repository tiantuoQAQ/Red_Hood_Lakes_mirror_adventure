# -*- coding: utf-8 -*-
"""把轮廓外围一整圈白色描边整段吃掉（多轮侵蚀，直到碰到深色/彩色像素）。"""
import glob
from PIL import Image

FILES = glob.glob('art/portrait/mabel*.png')
PASSES = 60
TH = 0.62


def lum(c):
    return (c[0] + c[1] + c[2]) / 765.0


def run(path):
    im = Image.open(path).convert('RGBA')
    px = im.load()
    W, H = im.size
    total = 0
    for _ in range(PASSES):
        edits = []
        for y in range(H):
            for x in range(W):
                r, g, b, a = px[x, y]
                if a < 16:
                    continue
                mx, mn = max(r, g, b), min(r, g, b)
                if (mx - mn) > 40:      # 有颜色（红/蓝），留着
                    continue
                if lum((r, g, b)) < TH:  # 深色，留着
                    continue
                # 只吃紧贴透明的
                edge = False
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if nx < 0 or ny < 0 or nx >= W or ny >= H or px[nx, ny][3] < 16:
                        edge = True
                        break
                if edge:
                    edits.append((x, y))
        if not edits:
            break
        for x, y in edits:
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 0)
            total += 1
    im.save(path)
    print(path, 'white outline eroded px', total)


for f in FILES:
    run(f)
