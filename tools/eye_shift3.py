# -*- coding: utf-8 -*-
"""眼睛视线左移 v3：虹膜整体左移，只写进「亮部」（不覆盖睫毛/眼线）。"""
import sys
from collections import deque
import numpy as np
from PIL import Image

SRC, DST = sys.argv[1], sys.argv[2]
DX = int(sys.argv[3]) if len(sys.argv) > 3 else -20

a = np.array(Image.open(SRC).convert('RGB'))
R, G, B = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
lum = (R + G + B) / 3.0
cyan = (G > 90) & (B > 90) & (R < G - 40) & (R < B - 40)


def comps_of(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    out = []
    cur = 0
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
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = cur
                        q.append((nx, ny))
            out.append(pts)
    out.sort(key=len, reverse=True)
    return out


eyes = [c for c in comps_of(cyan)[:2] if len(c) > 200]
out = a.copy()
H, W = a.shape[:2]

for pts in eyes:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    m = 3
    x0p, x1p = max(0, x0 - m), min(W - 1, x1 + m)
    y0p, y1p = max(0, y0 - m), min(H - 1, y1 + m)
    hh, ww = y1p - y0p + 1, x1p - x0p + 1

    patch = a[y0p:y1p + 1, x0p:x1p + 1].copy()
    pl = lum[y0p:y1p + 1, x0p:x1p + 1]
    bright = pl > 110                                  # 非睫毛/眼线

    # 虹膜掩码（青色，填洞把瞳孔和高光包进来）
    seed = cyan[y0p:y1p + 1, x0p:x1p + 1].copy()
    # 填洞：内部不能从边界泛洪到的区域
    seen = np.zeros((hh, ww), dtype=bool)
    q = deque()
    for x in range(ww):
        for y in (0, hh - 1):
            if not seed[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((x, y))
    for y in range(hh):
        for x in (0, ww - 1):
            if not seed[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((x, y))
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < ww and 0 <= ny < hh and not seed[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((nx, ny))
    iris = (~seen) & (~seed) | seed
    iris = iris & bright                                   # 不碰睫毛

    sclera_mask = bright & (~iris)
    sclera_patch = patch[sclera_mask] if sclera_mask.sum() > 50 else patch[bright]
    sclera = tuple(int(v) for v in np.median(sclera_patch, axis=0))

    region = out[y0p:y1p + 1, x0p:x1p + 1]
    region[iris] = sclera                                   # 抹掉原虹膜

    rows, cols = np.where(iris)
    for yy, xx in zip(rows, cols):
        nx = xx + DX
        if 0 <= nx < ww and bright[yy, nx]:
            region[yy, nx] = patch[yy, xx]
    print('eye', (x0, y0, x1, y1), 'dx', DX)

Image.fromarray(out).save(DST)
print('saved', DST)
