# -*- coding: utf-8 -*-
"""重新生成王座贴图（更暗、更简洁、剪影感，不抢画面）。"""
import base64
import colorsys
import io
import json
import os
import time
import urllib.request

import numpy as np
from PIL import Image

KEY = 'REDACTED-API-KEY'
URL = 'https://api.a6api.com/v1/images/generations'

PROMPT = ('Game background prop on pure black background: a simple DARK gothic throne, front view, '
          'almost a silhouette — blackened iron frame, straight tall backrest with a few thin pointed spikes at the top, '
          'small dark-red velvet seat, very little detail, no ornament clutter, no gemstones, no quilted pattern. '
          'Low contrast, muted, heavy shadows so it sits quietly in a dark forest scene. '
          'Flat cel-shaded anime prop style, thin clean edge highlight only. '
          'Palette strictly: near-black, dark neutral grays, deep red #FF0000 only on the seat, tiny white rim highlight. '
          'No character, no text, no watermark. Entire throne inside frame.')


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


def process(raw, out):
    img = Image.open(io.BytesIO(raw)).convert('RGBA')
    a = np.array(img).astype(np.float32) / 255.0
    rgb, alpha = a[:, :, :3], a[:, :, 3]
    lum = rgb.max(axis=2)
    k = np.clip((lum - 0.035) / 0.16, 0.0, 1.0)      # 只把纯黑背景抹掉，暗部保留
    flat = rgb.reshape(-1, 3)
    for i in range(flat.shape[0]):
        r, g, b = flat[i]
        _, ll, ss = colorsys.rgb_to_hls(float(r), float(g), float(b))
        if ss < 0.06:
            continue
        flat[i] = colorsys.hls_to_rgb(0.0, ll * 0.9, max(ss, 0.35))
    rgb2 = flat.reshape(rgb.shape)
    im = Image.fromarray(np.clip(np.dstack([rgb2, alpha * k]) * 255, 0, 255).astype(np.uint8), 'RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
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
        print('retry', type(exc).__name__, exc)
        time.sleep(6)
if raw:
    process(raw, 'art/obj/throne_new.png')
