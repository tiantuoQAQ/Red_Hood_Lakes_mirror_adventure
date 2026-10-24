# 立绘预处理：把即梦出的白底图，切成能直接进游戏的透明立绘
#
# 做四件事：
#   1. 从四边洪水填充去白底（只去外部连通的白，角色身上的白色毛边不会被吃掉）
#   2. 按 alpha 裁掉四周空白
#   3. 等比缩放到目标高度
#   4. 底部居中放进统一画布（默认 512×768），输出到 art/portrait/<角色id>.png
#
# 用法:
#   python tools/prep_portrait.py <输入图> <角色id> [--canvas 512x768] [--height 720]

import os
import sys
import argparse
from collections import deque

from PIL import Image


def is_whiteish(px, tol=18):
    r, g, b, a = px
    if a < 8:
        return True
    mx, mn = max(r, g, b), min(r, g, b)
    return mx >= 255 - tol and (mx - mn) <= 10


def cut_background(im, tol=18):
    """从四边洪水填充，把外部白色背景变成透明。"""
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    q = deque()

    def push(x, y):
        i = y * w + x
        if seen[i]:
            return
        if not is_whiteish(px[x, y], tol):
            return
        seen[i] = 1
        q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    while q:
        x, y = q.popleft()
        r, g, b, a = px[x, y]
        px[x, y] = (r, g, b, 0)
        if x > 0:
            push(x - 1, y)
        if x < w - 1:
            push(x + 1, y)
        if y > 0:
            push(x, y - 1)
        if y < h - 1:
            push(x, y + 1)
    return im


def trim(im):
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


def fit(canvas_w, canvas_h, target_h):
    pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('char_id')
    ap.add_argument('--canvas', default='512x768')
    ap.add_argument('--height', type=int, default=0, help='默认 = 画布高度 - 24')
    ap.add_argument('--out', default='')
    args = ap.parse_args()

    cw, ch = [int(v) for v in args.canvas.lower().split('x')]
    target_h = args.height or (ch - 24)

    im = Image.open(args.src).convert('RGBA')
    has_alpha = im.getextrema()[3][0] < 250
    if not has_alpha:
        im = cut_background(im)
    im = trim(im)

    scale = target_h / im.height
    nw = max(1, int(round(im.width * scale)))
    im = im.resize((nw, target_h), Image.LANCZOS)

    # 太宽的话按宽度再限一次
    max_w = cw - 16
    if im.width > max_w:
        s2 = max_w / im.width
        im = im.resize((max_w, max(1, int(round(im.height * s2)))), Image.LANCZOS)

    canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    x = (cw - im.width) // 2
    y = ch - im.height
    canvas.alpha_composite(im, (x, y))

    out = args.out or os.path.join('art', 'portrait', args.char_id + '.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.save(out)
    print('立绘已生成: {}  ({}x{}, 内容 {}x{}, 底边居中)'.format(
        out, cw, ch, im.width, im.height))


if __name__ == '__main__':
    main()
