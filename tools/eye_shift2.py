# -*- coding: utf-8 -*-
"""眼睛视线左移 v2：虹膜在「眼白口袋」内平移，不越界、不盖住睫毛轮廓。"""
import sys
from collections import deque
import numpy as np
from PIL import Image

SRC = sys.argv[1]
DST = sys.argv[2]
SHIFT_FRAC = float(sys.argv[3]) if len(sys.argv) > 3 else 0.22


def flood(mask, seeds):
    h, w = mask.shape
    seen = np.zeros((h, w), dtype=bool)
    q = deque()
    for x, y in seeds:
        if 0 <= x < w and 0 <= y < h and not mask[y, x] and not seen[y, x]:
            seen[y, x] = True
            q.append((x, y))
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and not mask[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((nx, ny))
    return seen


def label(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    comps = []
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
            comps.append(pts)
    return comps


im = Image.open(SRC).convert('RGB')
a = np.array(im)
R, G, B = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
lum = (R + G + B) / 3.0

cyan = (G > 90) & (B > 90) & (R < G - 40) & (R < B - 40)
comps = label(cyan)
comps.sort(key=len, reverse=True)
comps = [c for c in comps[:2] if len(c) > 200]
if len(comps) < 2:
    print('没找到两只眼睛')
    sys.exit(1)

out = a.copy()
H, W = a.shape[:2]

for pts in comps:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    m = 10                                     # 外扩，纳入睫毛轮廓
    x0p, x1p = max(0, x0 - m), min(W - 1, x1 + m)
    y0p, y1p = max(0, y0 - m), min(H - 1, y1 + m)

    dark = lum[y0p:y1p + 1, x0p:x1p + 1] < 100       # 睫毛/眼球轮廓
    hh, ww = dark.shape
    outside = flood(dark, [(0, 0), (ww - 1, 0), (0, hh - 1), (ww - 1, hh - 1)])
    pocket = ~outside & ~np.pad(dark, 0)            # 眼球内部（含虹膜/瞳孔/眼白）
    pocket = pocket & ~dark

    # 虹膜区域（含瞳孔与高光）：青色 + 洞
    sub_cyan = cyan[y0p:y1p + 1, x0p:x1p + 1]
    iris_seed = sub_cyan.copy()
    # 填洞：把瞳孔/高光包进来
    not_seed = ~iris_seed
    hole_out = flood(iris_seed, [(0, 0), (ww - 1, 0), (0, hh - 1), (ww - 1, hh - 1)])
    iris = ~hole_out & pocket

    # 允许的最大左移：虹膜左缘到眼球左缘的距离
    cols = np.where(iris.any(axis=0))[0]
    pcols = np.where(pocket.any(axis=0))[0]
    if len(cols) == 0 or len(pcols) == 0:
        continue
    room = int(cols.min() - pcols.min()) - 1
    want = max(2, int(round(ww * SHIFT_FRAC)))
    dx = -int(min(want, max(0, room)))
    if dx == 0:
        continue

    patch = a[y0p:y1p + 1, x0p:x1p + 1].copy()
    bright = patch[pocket & (patch.min(axis=2) > 195)]
    sclera = tuple(int(v) for v in (np.median(bright, axis=0) if len(bright) else np.array([250, 250, 250])))

    region = out[y0p:y1p + 1, x0p:x1p + 1]
    region[iris] = sclera                              # 清空原虹膜

    dst = np.zeros_like(iris)
    for yy in range(hh):
        for xx in range(ww):
            if iris[yy, xx]:
                nx = xx + dx
                if 0 <= nx < ww and pocket[yy, nx]:
                    dst[yy, nx] = True

    # 把虹膜像素按 dx 搬过去
    src_rows, src_cols = np.where(iris)
    for yy, xx in zip(src_rows, src_cols):
        nx = xx + dx
        if 0 <= nx < ww and pocket[yy, nx]:
            region[yy, nx] = patch[yy, xx]

    print('eye', (x0, y0, x1, y1), 'shift', dx, 'room', room)

Image.fromarray(out).save(DST)
print('saved', DST)
