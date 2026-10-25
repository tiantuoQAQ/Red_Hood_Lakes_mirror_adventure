# -*- coding: utf-8 -*-
"""生成三个技能图标（gpt-image-2），抠黑底 → 透明 PNG，色相锁到规范色。"""
import base64
import io
import json
import os
import time
import urllib.request
import colorsys
import numpy as np
from PIL import Image

KEY = 'REDACTED-API-KEY'
URL = 'https://api.a6api.com/v1/images/generations'

ICONS = [
    ('red_tragedy', 'Game skill icon, square, single emblem centered on pure black background: an ornate crimson seal / talisman with a curved dagger and a few blood drops, thick black outlines, flat cel shading, glowing red core. STRICT palette: pure red #FF0000, white, neutral grays only. No text, no letters, no watermark.'),
    ('gunfire', 'Game skill icon, square, centered on pure black background: a stylized muzzle flash with a bullet and two shockwave rings, flat cel shading, thick black outlines. STRICT palette: pure red #FF0000, white, neutral grays only. No text, no letters, no watermark.'),
    ('hellfire', 'Game skill icon, square, centered on pure black background: a stylized flame inside a broken circle ring, flat cel shading, thick black outlines, glowing core. STRICT palette: pure red #FF0000, white, neutral grays only. No text, no letters, no watermark.'),
]


def gen(prompt):
    body = json.dumps({'model': 'gpt-image-2', 'prompt': prompt, 'n': 1,
                       'size': '1024x1024', 'response_format': 'b64_json'}).encode()
    req = urllib.request.Request(URL, data=body, method='POST',
                                 headers={'Authorization': 'Bearer ' + KEY,
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return base64.b64decode(json.loads(r.read().decode())['data'][0]['b64_json'])


def key_and_tint(raw: bytes, out: str):
    img = Image.open(io.BytesIO(raw)).convert('RGBA')
    a = np.array(img)
    rgb = a[:, :, :3].astype(np.float32) / 255.0
    lum = rgb.max(axis=2)
    alpha = np.clip((lum - 0.06) / 0.35, 0.0, 1.0)
    # 色相锁到纯红 0°
    h, w = alpha.shape
    flat = rgb.reshape(-1, 3)
    for i in range(flat.shape[0]):
        r, g, b = flat[i]
        _, l, s = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if s < 0.05:
            continue
        flat[i] = colorsys.hls_to_rgb(0.0, l, max(s, 0.25))
    res = np.concatenate([flat.reshape(rgb.shape), alpha[:, :, None]], axis=2)
    im = Image.fromarray(np.clip(res * 255, 0, 255).astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    side = max(im.width, im.height)
    canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
    canvas = canvas.resize((256, 256), Image.LANCZOS)
    os.makedirs('art/ui', exist_ok=True)
    canvas.save(out)
    print('  ->', out)


for name, prompt in ICONS:
    t = time.time()
    raw = gen(prompt)
    key_and_tint(raw, 'art/ui/skill_%s.png' % name)
    time.sleep(1)
print('done')
