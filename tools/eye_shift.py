# -*- coding: utf-8 -*-
"""把眼睛的虹膜整体平移到看向左侧（不是翻转图片）。
做法：
1. 找青色虹膜连通块（两只眼睛）
2. 虹膜区域做「填洞」，把瞳孔/高光一起纳入
3. 该区域整体左移 dx，原位置用眼白颜色补上
4. 保存
"""
import sys
from collections import deque
import numpy as np
from PIL import Image

SRC = sys.argv[1]
DST = sys.argv[2]
SHIFT_FRAC = float(sys.argv[3]) if len(sys.argv) > 3 else 0.22   # 相对眼睛宽度


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


def fill_holes(sub):
    """sub: 布尔小图；从边界泛洪，剩下的就是洞"""
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
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and not sub[ny, nx] and not outside[ny, nx]:
                outside[ny, nx] = True
                q.append((nx, ny))
    return ~outside


im = Image.open(SRC).convert('RGB')
a = np.array(im)
R, G, B = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)

# 青色虹膜
cyan = (G > 90) & (B > 90) & (R < G - 40) & (R < B - 40)
comps = label(cyan)
comps.sort(key=len, reverse=True)
comps = [c for c in comps[:2] if len(c) > 200]
print('iris blobs:', [len(c) for c in comps])
if len(comps) < 2:
    print('没找到两只眼睛，退出')
    sys.exit(1)

out = a.copy()
H, W = a.shape[:2]

for pts in comps:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    pad = 2
    x0p, x1p = max(0, x0 - pad), min(W - 1, x1 + pad)
    y0p, y1p = max(0, y0 - pad), min(H - 1, y1 + pad)

    sub = cyan[y0p:y1p + 1, x0p:x1p + 1].copy()
    filled = fill_holes(sub)
    # 再膨胀 1px，避免留下虹膜描边
    dil = filled.copy()
    dil[1:, :] |= filled[:-1, :]
    dil[:-1, :] |= filled[1:, :]
    dil[:, 1:] |= filled[:, :-1]
    dil[:, :-1] |= filled[:, 1:]
    filled = dil

    hh, ww = filled.shape
    dx = -max(2, int(round(ww * SHIFT_FRAC)))

    # 眼白颜色：取这个矩形里偏亮的像素中位数
    patch = a[y0p:y1p + 1, x0p:x1p + 1].reshape(-1, 3)
    bright = patch[patch.min(axis=1) > 200]
    sclera = tuple(int(v) for v in (np.median(bright, axis=0) if len(bright) else np.array([250, 250, 250])))

    # 原位置填眼白
    region = out[y0p:y1p + 1, x0p:x1p + 1]
    region[filled] = sclera

    # 平移虹膜
    src_patch = a[y0p:y1p + 1, x0p:x1p + 1].copy()
    for yy in range(hh):
        for xx in range(ww):
            if not filled[yy, xx]:
                continue
            nx = xx + dx
            if 0 <= nx < ww:
                region[yy, nx] = src_patch[yy, xx]
    print('eye bbox', (x0, y0, x1, y1), 'shift', dx, 'sclera', sclera)

Image.fromarray(out).save(DST)
print('saved', DST)
