# -*- coding: utf-8 -*-
"""去白边（defringe）：抠图后角色轮廓上常残留一圈白色半透明边。

做法：只处理「紧贴透明区域的边缘像素」——
- 非常亮的（白雾）直接透明
- 中等亮的（半透明白边）降低不透明度
内部的白（荷叶边、白衣服）不在透明区旁边，不受影响。

用法：
    python tools/defringe.py art/portrait/*.png
"""
import sys
import glob
from PIL import Image

PASSES = 2


def defringe(path):
    im = Image.open(path).convert('RGBA')
    px = im.load()
    W, H = im.size
    removed = 0
    softened = 0

    for _ in range(PASSES):
        # 记录本轮要改的像素（避免边改边读导致扩散不一致）
        edits = []
        for y in range(H):
            for x in range(W):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                # 判断是否紧贴透明
                edge = False
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if nx < 0 or ny < 0 or nx >= W or ny >= H:
                        edge = True
                        break
                    if px[nx, ny][3] < 16:
                        edge = True
                        break
                if not edge:
                    continue
                mx, mn = max(r, g, b), min(r, g, b)
                if (mx - mn) > 26:      # 有彩色，不是白边
                    continue
                lum = (r + g + b) / 765.0
                if lum > 0.90:
                    edits.append((x, y, 0, 'rm'))
                elif lum > 0.78:
                    edits.append((x, y, int(a * 0.45), 'sf'))
        for x, y, na, kind in edits:
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, na)
            if kind == 'rm':
                removed += 1
            else:
                softened += 1

    im.save(path)
    print('{} 去白边 {} px / 减淡 {} px'.format(path, removed, softened))


if __name__ == '__main__':
    files = []
    for a in sys.argv[1:]:
        hits = glob.glob(a)
        files.extend(hits if hits else [a])
    for f in files:
        defringe(f)
