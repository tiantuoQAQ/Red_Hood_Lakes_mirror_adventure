# -*- coding: utf-8 -*-
"""导入即梦立绘 v2：抹水印 → 黑白底抠除 → 只留最大连通块 → 缩放 512x768"""
from collections import deque
from PIL import Image

CANVAS_W, CANVAS_H = 512, 768
CONTENT_H = 744
PAD_BOTTOM = 12

PAIRS = [
    ('art/ref/mabel_v5_normal.jpg', 'art/portrait/mabel.png'),
    ('art/ref/mabel_v5_closed.jpg', 'art/portrait/mabel_eyes_closed.png'),
    ('art/ref/mabel_v5_open.jpg', 'art/portrait/mabel_eyes_open.png'),
    ('art/ref/mabel_v5_lookback.jpg', 'art/portrait/mabel_look_back.png'),
    ('art/ref/norden_v5.jpg', 'art/portrait/norden.png'),
]


def clean(src, dst):
    im = Image.open(src).convert('RGB')
    w, h = im.size
    px = im.load()
    corners = [px[2, 2], px[w - 3, 2], px[2, h - 3], px[w - 3, h - 3]]
    avg = sum(sum(c) for c in corners) / (3 * len(corners))
    fill = (0, 0, 0) if avg < 90 else (255, 255, 255)
    for y in range(int(h * 0.90), h):
        for x in range(int(w * 0.80), w):
            px[x, y] = fill

    im = im.convert('RGBA')
    px = im.load()
    W, H = im.size

    def is_bg(p):
        r, g, b, a = p
        if a == 0:
            return True
        mx, mn = max(r, g, b), min(r, g, b)
        if mx <= 12:
            return True
        return mn >= 238 and (mx - mn) <= 14

    seen = bytearray(W * H)
    q = deque()

    def push(x, y):
        i = y * W + x
        if seen[i] or not is_bg(px[x, y]):
            return
        seen[i] = 1
        q.append((x, y))

    for x in range(W):
        push(x, 0)
        push(x, H - 1)
    for y in range(H):
        push(0, y)
        push(W - 1, y)
    while q:
        x, y = q.popleft()
        r, g, b, a = px[x, y]
        px[x, y] = (r, g, b, 0)
        if x > 0:
            push(x - 1, y)
        if x < W - 1:
            push(x + 1, y)
        if y > 0:
            push(x, y - 1)
        if y < H - 1:
            push(x, y + 1)

    label = [[0] * W for _ in range(H)]
    comps = []
    cur = 0
    for sy in range(H):
        for sx in range(W):
            if px[sx, sy][3] == 0 or label[sy][sx]:
                continue
            cur += 1
            qq = deque([(sx, sy)])
            label[sy][sx] = cur
            pts = []
            while qq:
                x, y = qq.popleft()
                pts.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and px[nx, ny][3] > 0 and not label[ny][nx]:
                        label[ny][nx] = cur
                        qq.append((nx, ny))
            comps.append(pts)

    if comps:
        comps.sort(key=len, reverse=True)
        for pts in comps[1:]:
            for x, y in pts:
                r, g, b, _ = px[x, y]
                px[x, y] = (r, g, b, 0)

    bb = im.getbbox()
    im = im.crop(bb)
    k = CONTENT_H / im.height
    nw, nh = int(im.width * k), CONTENT_H
    if nw > CANVAS_W - 8:
        k = (CANVAS_W - 8) / im.width
        nw, nh = CANVAS_W - 8, int(im.height * k)
    im = im.resize((nw, nh), Image.LANCZOS)
    out = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    out.alpha_composite(im, ((CANVAS_W - nw) // 2, CANVAS_H - PAD_BOTTOM - nh))
    out.save(dst)
    print(dst, 'comps', len(comps), '->', out.size)


if __name__ == '__main__':
    for s, d in PAIRS:
        print(s)
        clean(s, d)
