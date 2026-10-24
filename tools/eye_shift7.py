# -*- coding: utf-8 -*-
"""眼睛视线左移 v7（稳定版）
虹膜区域 = 青色填洞 ∪ 膨胀2px（限制在亮部），先整块抹成眼白，再整块右移贴回。
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


def fill_holes(sub):
    h, w = sub.shape
    outside = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if not sub[y, x] and not outside[y, x]:
                outside[y, x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if not sub[y, x] and not outside[y, x]:
                outside[y, x] = True
                q.append((x, y))
    while q:
        cx, cy = q.popleft()
        for dxx, dyy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dxx, cy + dyy
            if 0 <= nx < w and 0 <= ny < h and not sub[ny, nx] and not outside[ny, nx]:
                outside[ny, nx] = True
                q.append((nx, ny))
    return ~outside


def dilate(m, n):
    out = m.copy()
    for _ in range(n):
        d = out.copy()
        d[1:, :] |= out[:-1, :]
        d[:-1, :] |= out[1:, :]
        d[:, 1:] |= out[:, :-1]
        d[:, :-1] |= out[:, 1:]
        out = d
    return out


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
    sub_cyan = cyan[y0p:y1p + 1, x0p:x1p + 1]

    iris = fill_holes(sub_cyan)
    iris = iris & bright
    iris_e = dilate(iris, 2) & bright

    rest = bright & (~iris_e) & (patch.min(axis=2) > 232)
    if rest.sum() > 30:
        sclera = tuple(int(v) for v in np.median(patch[rest], axis=0))
    else:
        sclera = (250, 250, 250)

    region = out[y0p:y1p + 1, x0p:x1p + 1]
    region[iris_e] = sclera

    rows, cols = np.where(iris_e)
    for yy, xx in zip(rows, cols):
        nx = xx + DX
        if 0 <= nx < ww and bright[yy, nx]:
            region[yy, nx] = patch[yy, xx]
    print('eye', (x0, y0, x1, y1), 'dx', DX, 'sclera', sclera)

Image.fromarray(out).save(DST)
print('saved', DST)
