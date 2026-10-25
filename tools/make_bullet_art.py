# -*- coding: utf-8 -*-
"""生成弹幕精灵（好看版）：刃形剑气 / 光球 / 追踪激光头 / 剑雨。三色合规。"""
import base64
import io
import json
import os
import time
import urllib.request
import colorsys
import numpy as np
from PIL import Image

KEY = os.environ.get('A6API_KEY', '')  # 从环境变量读取，勿硬编码
URL = 'https://api.a6api.com/v1/images/generations'

JOBS = [
    ('bullet_blade', 'Single game bullet sprite, centered on pure black background, 1:1 square: a crescent crimson energy blade / sword slash arc pointing RIGHT, '
                     'sharp curving talon-like tip, white hot inner edge, red outer glow, thin white highlight line. '
                     'Flat cel-shaded, high contrast, clean silhouette with no background elements. '
                     'Palette strictly: pure red #FF0000, pure white, near-black, neutral grays. No text, no watermark.'),
    ('bullet_orb', 'Single game bullet sprite, centered on pure black background, 1:1 square: a crimson energy orb with a white hot core, '
                   'a thin rotating rune ring inside, two sharp red spikes, soft red glow. '
                   'Flat cel-shaded, high contrast, clean silhouette. '
                   'Palette strictly: pure red #FF0000, pure white, near-black, neutral grays. No text, no watermark.'),
    ('bullet_laser', 'Single game bullet sprite, centered on pure black background, 1:1 square: a crimson laser bolt / energy lance pointing RIGHT, '
                     'long tapered white-hot core with red shell and jagged energy sparks. '
                     'Flat cel-shaded, high contrast, clean silhouette. '
                     'Palette strictly: pure red #FF0000, pure white, near-black, neutral grays. No text, no watermark.'),
    ('bullet_rain', 'Single game bullet sprite, centered on pure black background, 1:1 square: a sharp crimson falling blade tip pointing DOWN, '
                    'like a small sword thrown downward, white edge highlight, red glow. '
                    'Flat cel-shaded, high contrast, clean silhouette. '
                    'Palette strictly: pure red #FF0000, pure white, near-black, neutral grays. No text, no watermark.'),
]


def gen(prompt):
    body = json.dumps({'model': 'gpt-image-2', 'prompt': prompt, 'n': 1,
                       'size': '1024x1024', 'response_format': 'b64_json'}).encode()
    req = urllib.request.Request(URL, data=body, method='POST',
                                 headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return base64.b64decode(json.loads(r.read().decode())['data'][0]['b64_json'])


def process(raw, out):
    img = Image.open(io.BytesIO(raw)).convert('RGBA')
    a = np.array(img).astype(np.float32) / 255.0
    rgb, alpha = a[:, :, :3], a[:, :, 3]
    lum = rgb.max(axis=2)
    # 黑底转透明
    k = np.clip((lum - 0.05) / 0.30, 0.0, 1.0)
    # 色相锁到纯红（保留亮白高光）
    flat = rgb.reshape(-1, 3)
    for i in range(flat.shape[0]):
        r, g, b = flat[i]
        _, l, s = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if s < 0.06:
            continue
        flat[i] = colorsys.hls_to_rgb(0.0, l, max(s, 0.35))
    rgb2 = flat.reshape(rgb.shape)
    out_a = alpha * k
    im = Image.fromarray(np.clip(np.dstack([rgb2, out_a]) * 255, 0, 255).astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    side = max(im.width, im.height)
    canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
    canvas.resize((128, 128), Image.LANCZOS).save(out)
    print('  ->', out)


os.makedirs('art/fx/bullets', exist_ok=True)
for name, prompt in JOBS:
    t = time.time()
    process(gen(prompt), 'art/fx/bullets/%s.png' % name)
    time.sleep(1)
print('done')
