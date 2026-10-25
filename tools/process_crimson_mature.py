# -*- coding: utf-8 -*-
"""成熟立绘后处理：白底抠透明 + 色相锁 + 覆盖原立绘（备份 chibi 版）。
同时把坐姿两张也做成熟化（图生图）。"""
import io
import json
import os
import time
import urllib.request
import uuid
import base64
import colorsys
import numpy as np
from PIL import Image

KEY = 'REDACTED-API-KEY'
URL = 'https://api.a6api.com/v1/images/edits'


def key_white(path, out, size=(512, 768)):
    im = Image.open(path).convert('RGBA')
    a = np.array(im).astype(np.int16)
    rgb = a[:, :, :3]
    lum = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    bg = (lum >= 235) & ((lum - mn) <= 12)
    from collections import deque
    h, w = bg.shape
    seen = np.zeros((h, w), bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bg[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if bg[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((x, y))
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and bg[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((nx, ny))
    alpha = np.where(seen, 0, 255).astype(np.uint8)
    # 色相锁：非灰像素吸附到 0°（红）
    rgb_f = rgb.astype(np.float32) / 255.0
    flat = rgb_f.reshape(-1, 3)
    for i in range(flat.shape[0]):
        r, g, b = flat[i]
        _, l, s = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if s < 0.06:
            continue
        flat[i] = colorsys.hls_to_rgb(0.0, l, max(s, 0.3))
    res = np.dstack([flat.reshape(rgb_f.shape), alpha / 255.0])
    img = Image.fromarray(np.clip(res * 255, 0, 255).astype(np.uint8), 'RGBA')
    bb = img.getbbox()
    if bb:
        img = img.crop(bb)
    img = img.resize(size, Image.LANCZOS)
    img.save(out)
    print('keyed ->', out, img.size)


def edit(src, prompt, out):
    boundary = '----dsh' + uuid.uuid4().hex
    body = io.BytesIO()
    for k, v in {'model': 'gpt-image-2', 'prompt': prompt, 'n': '1', 'size': '1024x1536'}.items():
        body.write(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (boundary, k, v)).encode())
    data = open(src, 'rb').read()
    body.write(('--%s\r\nContent-Disposition: form-data; name="image"; filename="%s"\r\nContent-Type: image/png\r\n\r\n'
                % (boundary, os.path.basename(src))).encode())
    body.write(data)
    body.write(b'\r\n')
    body.write(('--%s--\r\n' % boundary).encode())
    req = urllib.request.Request(URL, data=body.getvalue(), method='POST',
                                 headers={'Authorization': 'Bearer ' + KEY,
                                          'Content-Type': 'multipart/form-data; boundary=' + boundary})
    with urllib.request.urlopen(req, timeout=300) as r:
        obj = json.loads(r.read().decode())
    open(out, 'wb').write(base64.b64decode(obj['data'][0]['b64_json']))
    print('edited ->', out)


PROMPT = ('Keep this exact character design: white fur-trimmed hood with red cat-ear insides, gray-white hair, '
          'red eyes, red-and-black fur-trimmed coat, black corset with lacing, black shorts, black boots, '
          'palette only pure red #FF0000 / pure white / neutral grays. '
          'Change ONLY body proportions: mature adult anime woman about 7 heads tall, long legs, '
          'calm arrogant expression, gothic and elegant, not chibi. Keep the same seated pose and same background. '
          'Flat cel-shaded anime style, clean thick linework, plain white background, no text, no watermark.')

base = 'art/portrait'
# 备份 chibi
for f in ['crimson_stand.png', 'crimson_seated_closed.png', 'crimson_seated_open.png']:
    src = os.path.join(base, f)
    bak = os.path.join(base, f.replace('.png', '_chibi.png'))
    if os.path.exists(src) and not os.path.exists(bak):
        Image.open(src).save(bak)
        print('backup', bak)

# 站立：直接用生成的成熟图
key_white('art/portrait/crimson_mature_raw.png', os.path.join(base, 'crimson_stand.png'))

# 两张坐姿：图生图成熟化再抠
for f in ['crimson_seated_closed.png', 'crimson_seated_open.png']:
    src = os.path.join(base, f.replace('.png', '_chibi.png'))
    if not os.path.exists(src):
        continue
    raw = os.path.join('tmp', 'mature_' + f)
    try:
        edit(src, PROMPT, raw)
        key_white(raw, os.path.join(base, f))
    except Exception as exc:  # noqa: BLE001
        print('坐姿处理失败', f, exc)
print('done')
