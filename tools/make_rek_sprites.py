# -*- coding: utf-8 -*-
"""重出小红帽战斗立绘（完整身体，chibi 风格与头像统一）：跑步 / 蓄力 / 冲刺。"""
import base64
import colorsys
import io
import json
import os
import time
import urllib.request
from collections import deque

import numpy as np
from PIL import Image

KEY = 'REDACTED-API-KEY'
URL = 'https://api.a6api.com/v1/images/generations'

BASE = ('Anime game sprite, full body, single character, centered on pure white background. '
        'Character: chibi-proportioned girl, about 4.5 heads tall (big head, small body, cute but fierce), '
        'red hooded cloak with pointed cat ears and white fur trim, gray bob hair, bright cyan-blue eyes, '
        'black corset top with cross lacing, black shorts, black thigh-high boots, a pendant necklace. '
        'Flat cel-shaded anime style with clean thick black linework, high contrast, strong silhouette. '
        'Palette strictly: pure red #FF0000, pure white, near-black, neutral grays, cyan #00BAFF only for eyes. '
        'No text, no watermark, no background elements, full body inside frame with margin. ')

POSES = [
    ('rek_body_move.png', 'Pose: running to the right in a dynamic side view, cloak flaring behind, arms swinging, determined expression.'),
    ('rek_body_charge.png', 'Pose: standing battle stance, leaning slightly forward, one hand raised charging red energy, fierce expression.'),
    ('rek_dash_full.png', 'Pose: fast dashing to the right, body almost horizontal, cloak streaming straight back, motion blur lines behind her.'),
]


def gen(prompt):
    body = json.dumps({'model': 'gpt-image-2', 'prompt': prompt, 'n': 1, 'size': '1024x1536',
                       'response_format': 'b64_json'}).encode()
    req = urllib.request.Request(URL, data=body, method='POST',
                                 headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        obj = json.loads(r.read().decode())
    for it in (obj.get('data') or []):
        if it.get('b64_json'):
            return base64.b64decode(it['b64_json'])
    raise RuntimeError('no image')


def process(raw, out):
    img = Image.open(io.BytesIO(raw)).convert('RGBA')
    a = np.array(img).astype(np.int16)
    rgb, alpha = a[:, :, :3], a[:, :, 3]
    lum = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    bg = (lum >= 232) & ((lum - mn) <= 14)
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

    rgb_f = rgb.astype(np.float32) / 255.0
    flat = rgb_f.reshape(-1, 3)
    for i in range(flat.shape[0]):
        r, g, b = flat[i]
        hh, l, s = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if s < 0.07:
            continue
        deg = hh * 360.0
        if 160.0 <= deg <= 215.0:            # 蓝眼保留青蓝
            flat[i] = colorsys.hls_to_rgb(195.0 / 360.0, l, max(s, 0.45))
        elif deg <= 70.0 or deg >= 290.0:    # 红橙系吸附纯红
            flat[i] = colorsys.hls_to_rgb(0.0, l, max(s, 0.35))
        else:                                 # 其它颜色去饱和度
            _, l2, _ = colorsys.rgb_to_hls(float(r), float(g), float(b))
            flat[i] = (l2, l2, l2)
    im = Image.fromarray(np.clip(np.dstack([flat.reshape(rgb_f.shape), alpha / 255.0]) * 255, 0, 255)
                         .astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    os.makedirs('art/battle/rek', exist_ok=True)
    im.save(out)
    print('  ->', out, im.size)


for name, pose in POSES:
    out = os.path.join('art/battle/rek', name)
    if os.path.exists(out) and '_full' not in name:
        Image.open(out).save(out.replace('.png', '_old.png'))
    for attempt in range(3):
        try:
            t = time.time()
            process(gen(BASE + pose), out)
            print('   %.1fs' % (time.time() - t))
            break
        except Exception as exc:  # noqa: BLE001
            print('   retry', type(exc).__name__, exc)
            time.sleep(5)
print('done')
