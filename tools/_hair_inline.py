# -*- coding: utf-8 -*-
"""把「头发区域」里的白色内描边改成头发的深蓝色（限定区域，绝不碰脸）。"""
import glob
from PIL import Image

FILES = glob.glob('art/portrait/mabel*.png') + glob.glob('art/char/mabel_idle.png')


def lum(c):
    return (c[0] + c[1] + c[2]) / 765.0


def in_hair(x, y, W, H):
    # 两侧头发 + 头顶：排除脸（中心 30%~70% × 18%~52%）
    face = (0.30 * W <= x <= 0.70 * W) and (0.18 * H <= y <= 0.52 * H)
    return not face


def run(path):
    im = Image.open(path).convert('RGBA')
    px = im.load()
    W, H = im.size
    n = 0
    edits = []
    for y in range(int(H * 0.62)):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a < 16 or min(r, g, b) < 205:
                continue
            if not in_hair(x, y, W, H):
                continue
            darks = []
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if (dx or dy) and 0 <= nx < W and 0 <= ny < H and px[nx, ny][3] > 16:
                        c = px[nx, ny][:3]
                        if lum(c) < 0.45:
                            darks.append(c)
            if len(darks) >= 2:
                cr = sum(c[0] for c in darks) // len(darks)
                cg = sum(c[1] for c in darks) // len(darks)
                cb = sum(c[2] for c in darks) // len(darks)
                edits.append((x, y, (cr, cg, cb)))
    for x, y, col in edits:
        px[x, y] = (col[0], col[1], col[2], 255)
        n += 1
    im.save(path)
    print(path, 'hair inner white line -> dark', n)


for f in FILES:
    run(f)
