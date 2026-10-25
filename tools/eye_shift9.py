# -*- coding: utf-8 -*-
"""眼睛视线左移 v9（凸包版，最稳）
用青色像素的凸包当虹膜区域（自然包含瞳孔/高光/反光带，且不会吞到眼白），
整块左移，原位置填眼白。
"""
import sys
from collections import deque
import numpy as np
from PIL import Image

SRC, DST = sys.argv[1], sys.argv[2]
DX = int(sys.argv[3]) if len(sys.argv) > 3 else -18

a = np.array(Image.open(SRC).convert('RGB'))
R, G, B = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
lum = (R + G + B) / 3.0
cyan = (G > 90) & (B > 90) & (R < G - 40) & (R < B - 40)
H, W = a.shape[:2]


def comps_of(mask):
    lab = np.zeros(mask.shape, dtype=np.int32)
    out = []
    cur = 0
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or lab[y, x]:
                continue
            cur += 1
            q = deque([(x, y)])
            lab[y, x] = cur
            pts = []
            while q:
                cx, cy = q.popleft()
                pts.append((cx, cy))
                for dxx, dyy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dxx, cy + dyy
                    if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = cur
                        q.append((nx, ny))
            out.append(pts)
    out.sort(key=len, reverse=True)
    return out


def convex_hull(points):
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a_, b_):
        return (a_[0] - o[0]) * (b_[1] - o[1]) - (a_[1] - o[1]) * (b_[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


eyes = [c for c in comps_of(cyan)[:2] if len(c) > 200]
out = a.copy()

for pts in eyes:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad = 4
    x0p, x1p = max(0, x0 - pad), min(W - 1, x1 + pad)
    y0p, y1p = max(0, y0 - pad), min(H - 1, y1 + pad)
    hh, ww = y1p - y0p + 1, x1p - x0p + 1

    patch = a[y0p:y1p + 1, x0p:x1p + 1].copy()
    pl = lum[y0p:y1p + 1, x0p:x1p + 1]
    bright = pl > 110

    hull = convex_hull([(x - x0p, y - y0p) for (x, y) in pts])
    iris = np.zeros((hh, ww), dtype=bool)
    # 多边形扫描线填充
    hy = [p[1] for p in hull]
    for yy in range(min(hy), max(hy) + 1):
        xint = []
        n = len(hull)
        for i in range(n):
            ax, ay = hull[i]
            bx, by = hull[(i + 1) % n]
            if ay == by:
                continue
            if (ay <= yy < by) or (by <= yy < ay):
                t = (yy - ay) / (by - ay)
                xint.append(ax + t * (bx - ax))
        if len(xint) >= 2:
            xint.sort()
            for i in range(0, len(xint) - 1, 2):
                iris[yy, int(round(xint[i])):int(round(xint[i + 1])) + 1] = True
    iris = iris & bright

    rest = bright & (~iris) & (patch.min(axis=2) > 232)
    sclera = tuple(int(v) for v in np.median(patch[rest], axis=0)) if rest.sum() > 30 else (250, 250, 250)

    region = out[y0p:y1p + 1, x0p:x1p + 1]
    region[iris] = sclera

    rows, cols = np.where(iris)
    for yy, xx in zip(rows, cols):
        nx = xx + DX
        if 0 <= nx < ww and bright[yy, nx]:
            region[yy, nx] = patch[yy, xx]
    print('eye', (x0, y0, x1, y1), 'dx', DX, 'sclera', sclera)

Image.fromarray(out).save(DST)
print('saved', DST)
