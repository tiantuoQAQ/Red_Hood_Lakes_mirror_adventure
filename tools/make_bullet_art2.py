# -*- coding: utf-8 -*-
"""新弹幕美术（参考用户给的弹幕地狱截图）：火焰弹 / 新月剑气 / 阴阳玉 / 符纸 / 激光柱。"""
import base64
import colorsys
import io
import json
import os
import time
import urllib.request
import numpy as np
from PIL import Image

KEY = os.environ.get('A6API_KEY', '')  # 从环境变量读取，勿硬编码
URL = 'https://api.a6api.com/v1/images/generations'

JOBS = [
    ('flame_bullet', 'Single game bullet sprite, centered on pure black background, square: a small red flame bullet, '
                     'teardrop shaped flame head with a short glowing ember tail trailing to the left, white hot core. '
                     'Flat cel-shaded anime bullet, high contrast, clean silhouette. '
                     'Palette strictly: pure red #FF0000, pure white, near-black, neutral grays. No text.'),
    ('crescent', 'Single game bullet sprite, centered on pure black background, square: a huge white-blue crescent energy '
                 'slash arc, like a sword wave, thick glowing white core with thin red edge, curved crescent moon shape '
                 'opening to the right. Flat cel-shaded anime effect, clean silhouette. '
                 'Palette strictly: pure white, pure red #FF0000, neutral grays. No blue, no text.'),
    ('yinyang_orb', 'Single game bullet sprite, centered on pure black background, square: a glossy orb with a white and '
                    'red yin-yang symbol on its face, red rim glow, small white specular highlight, clean round shape. '
                    'Flat cel-shaded anime style. Palette strictly: pure red #FF0000, pure white, near-black, grays. No text.'),
    ('talisman', 'Single game bullet sprite, centered on pure black background, square: a small rectangular paper talisman, '
                 'white paper strip with a red vertical seal mark and red border, slightly tilted, red glow behind. '
                 'Flat cel-shaded anime style, clean silhouette. Palette strictly: pure white, pure red #FF0000, near-black, grays. No text.'),
    ('beam_pillar', 'Vertical laser beam texture, centered on pure black background, tall narrow composition: a bright '
                    'white-hot vertical energy column with red outer glow and jagged sparks along the edges, '
                    'brighter at the center, fading at top and bottom. Flat cel-shaded anime effect. '
                    'Palette strictly: pure white, pure red #FF0000, near-black, grays. No text.'),
]


def gen(prompt, size='1024x1024'):
    body = json.dumps({'model': 'gpt-image-2', 'prompt': prompt, 'n': 1, 'size': size,
                       'response_format': 'b64_json'}).encode()
    req = urllib.request.Request(URL, data=body, method='POST',
                                 headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        obj = json.loads(r.read().decode())
    for item in (obj.get('data') or []):
        if item.get('b64_json'):
            return base64.b64decode(item['b64_json'])
        if item.get('url'):
            with urllib.request.urlopen(item['url'], timeout=300) as rr:
                return rr.read()
    raise RuntimeError('no image in response: ' + str(obj)[:200])


def process(raw, out, size_px=128):
    img = Image.open(io.BytesIO(raw)).convert('RGBA')
    a = np.array(img).astype(np.float32) / 255.0
    rgb, alpha = a[:, :, :3], a[:, :, 3]
    lum = rgb.max(axis=2)
    k = np.clip((lum - 0.05) / 0.28, 0.0, 1.0)
    flat = rgb.reshape(-1, 3)
    for i in range(flat.shape[0]):
        r, g, b = flat[i]
        _, l, s = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if s < 0.06:
            continue
        flat[i] = colorsys.hls_to_rgb(0.0, l, max(s, 0.3))
    rgb2 = flat.reshape(rgb.shape)
    im = Image.fromarray(np.clip(np.dstack([rgb2, alpha * k]) * 255, 0, 255).astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    side = max(im.width, im.height)
    canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
    canvas.resize((size_px, size_px), Image.LANCZOS).save(out)
    print('  ->', out)


os.makedirs('art/fx/bullets', exist_ok=True)
for name, prompt in JOBS:
    t = time.time()
    size = '1024x1536' if name == 'beam_pillar' else '1024x1024'
    process(gen(prompt, size), 'art/fx/bullets/%s.png' % name, 128)
    time.sleep(1)
print('done')
