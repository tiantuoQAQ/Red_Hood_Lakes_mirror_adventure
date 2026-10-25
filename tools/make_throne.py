# -*- coding: utf-8 -*-
"""生成地图用王座贴图（低调不突兀：黑铁+暗红坐垫，三色合规），并接回地图 prop。"""
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

KEY = os.environ.get('A6API_KEY', '')  # 从环境变量读取，勿硬编码
URL = 'https://api.a6api.com/v1/images/generations'
PROMPT = ('Game background prop, centered on pure black background: an empty gothic throne seen from the front, '
          'tall blackened-iron backrest with thin thorn-like points, worn dark red velvet cushion, subtle red rim light, '
          'muted and understated so it blends into a dark forest scene. Flat cel-shaded anime style, thick clean black '
          'linework, soft inner glow. Palette strictly: pure red #FF0000, near-black, neutral grays, small pure white '
          'highlights. No character, no text, no watermark. Whole throne fully inside frame.')


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
        if it.get('url'):
            with urllib.request.urlopen(it['url'], timeout=300) as rr:
                return rr.read()
    raise RuntimeError('no image')


def key_black(raw, out):
    img = Image.open(io.BytesIO(raw)).convert('RGBA')
    a = np.array(img).astype(np.float32) / 255.0
    rgb, alpha = a[:, :, :3], a[:, :, 3]
    lum = rgb.max(axis=2)
    k = np.clip((lum - 0.045) / 0.22, 0.0, 1.0)
    flat = rgb.reshape(-1, 3)
    for i in range(flat.shape[0]):
        r, g, b = flat[i]
        _, ll, ss = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if ss < 0.06:
            continue
        flat[i] = colorsys.hls_to_rgb(0.0, ll, max(ss, 0.3))
    rgb2 = flat.reshape(rgb.shape)
    im = Image.fromarray(np.clip(np.dstack([rgb2, alpha * k]) * 255, 0, 255).astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    # 统一到高 420（地图里王座大小）
    ratio = 420.0 / im.height
    im = im.resize((max(1, int(im.width * ratio)), 420), Image.LANCZOS)
    os.makedirs('art/obj', exist_ok=True)
    im.save(out)
    print('saved', out, im.size)


raw = None
for attempt in range(3):
    try:
        raw = gen(PROMPT)
        break
    except Exception as exc:  # noqa: BLE001
        print('retry', exc)
        time.sleep(5)
if raw:
    key_black(raw, 'art/obj/throne_new.png')
