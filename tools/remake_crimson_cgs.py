# -*- coding: utf-8 -*-
"""统一重跑猩红魔姬全套对话 CG（以成熟版站立图为风格/设计基准），
输出统一画风、统一身高比例（等比缩放，不拉伸）。"""
import base64
import colorsys
import io
import json
import os
import time
import urllib.request
import uuid
from collections import deque

import numpy as np
from PIL import Image

KEY = os.environ.get('A6API_KEY', '')  # 从环境变量读取，勿硬编码
URL = 'https://api.a6api.com/v1/images/edits'
REF = 'art/portrait/crimson_stand.png'          # 成熟版基准
OUT_DIR = 'art/portrait'
CANVAS = (512, 768)                              # 目标画布
BODY_RATIO = 0.86                                # 角色高度占画布比例（统一身高）

STYLE = ('Use the reference image as the exact character design and art style reference. '
         'Keep identical: white fur-trimmed hood with red cat-ear insides, gray-white shoulder-length hair, '
         'red eyes, red-and-black fur-trimmed coat, black corset with lacing, black shorts, black boots, '
         'mature adult anime proportions about 7 heads tall, flat cel-shaded anime style with clean thick black '
         'linework, high contrast. Palette strictly pure red #FF0000 / pure white / near-black / neutral grays. '
         'Plain pure white background, single character full body inside frame, no text, no watermark. ')

POSES = [
    ('crimson_stand.png', 'Same standing pose as the reference, calm arrogant smirk, arms relaxed at her sides.'),
    ('crimson_stand_ready.png', 'Same character, combat ready stance: knees slightly bent, one hand raised with a '
                                'crimson energy blade forming, fierce confident expression.'),
    ('crimson_seated_closed.png', 'Same character sitting on an ornate gothic throne, legs crossed, eyes CLOSED, '
                                  'head slightly lowered, composed and tired expression.'),
    ('crimson_seated_open.png', 'Same character sitting on an ornate gothic throne, legs crossed, eyes OPEN glaring '
                                'forward with a cold arrogant look.'),
    ('crimson_defeated.png', 'Same character kneeling on the ground defeated, head bowed, hair covering her eyes, '
                             'coat slipping off one shoulder, a few red cracks of light on her body.'),
]


def multipart(fields, files):
    boundary = '----dsh' + uuid.uuid4().hex
    body = io.BytesIO()
    for k, v in fields.items():
        body.write(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (boundary, k, v)).encode())
    for k, (fn, data, ctype) in files.items():
        body.write(('--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\nContent-Type: %s\r\n\r\n'
                    % (boundary, k, fn, ctype)).encode())
        body.write(data)
        body.write(b'\r\n')
    body.write(('--%s--\r\n' % boundary).encode())
    return body.getvalue(), 'multipart/form-data; boundary=' + boundary


def edit(prompt, ref_bytes):
    fields = {'model': 'gpt-image-2', 'prompt': prompt, 'n': '1', 'size': '1024x1536'}
    files = {'image': ('ref.png', ref_bytes, 'image/png')}
    payload, ctype = multipart(fields, files)
    req = urllib.request.Request(URL, data=payload, method='POST',
                                 headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': ctype})
    with urllib.request.urlopen(req, timeout=300) as r:
        obj = json.loads(r.read().decode())
    for it in (obj.get('data') or []):
        if it.get('b64_json'):
            return base64.b64decode(it['b64_json'])
        if it.get('url'):
            with urllib.request.urlopen(it['url'], timeout=300) as rr:
                return rr.read()
    raise RuntimeError('no image: ' + str(obj)[:200])


def finish(raw, out):
    """白底抠透明 + 色相锁 + 等比缩放到统一身高（不拉伸）。"""
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
    # 色相锁红
    rgb_f = rgb.astype(np.float32) / 255.0
    flat = rgb_f.reshape(-1, 3)
    for i in range(flat.shape[0]):
        r, g, b = flat[i]
        _, l, s_col = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if s_col < 0.06:
            continue
        flat[i] = colorsys.hls_to_rgb(0.0, l, max(s_col, 0.32))
    im = Image.fromarray(np.clip(np.dstack([flat.reshape(rgb_f.shape), alpha / 255.0]) * 255, 0, 255)
                         .astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    # 等比缩放：目标高度 = 画布高 × BODY_RATIO
    target_h = int(CANVAS[1] * BODY_RATIO)
    scale = target_h / float(im.height)
    new_w = max(1, int(round(im.width * scale)))
    im = im.resize((new_w, target_h), Image.LANCZOS)
    if new_w > CANVAS[0]:
        # 太宽则按宽度限制（仍然等比）
        scale2 = CANVAS[0] / float(new_w)
        im = im.resize((CANVAS[0], max(1, int(round(target_h * scale2)))), Image.LANCZOS)
    canvas = Image.new('RGBA', CANVAS, (0, 0, 0, 0))
    canvas.alpha_composite(im, ((CANVAS[0] - im.width) // 2, CANVAS[1] - im.height))
    canvas.save(out)
    print('  ->', out, canvas.size)


ref_bytes = open(REF, 'rb').read()
for name, pose in POSES:
    out = os.path.join(OUT_DIR, name)
    if os.path.exists(out):
        Image.open(out).save(os.path.join(OUT_DIR, name.replace('.png', '_old.png')))
    for attempt in range(3):
        try:
            t = time.time()
            finish(edit(STYLE + pose, ref_bytes), out)
            print('   %s  %.1fs' % (name, time.time() - t))
            break
        except Exception as exc:  # noqa: BLE001
            print('   retry', name, type(exc).__name__, exc)
            time.sleep(5)
    time.sleep(1)
print('done')
