# -*- coding: utf-8 -*-
"""生成两张背景（gpt-image-2）：正常森林 / 镜中世界。16:9，暗色，三色合规。"""
import base64
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
    ('bg_forest', 'Dark anime game background, 16:9 side-scrolling forest at night, ground line at lower third, '
                  'tall bare trees with thin branches, cold moonlight haze, scattered small rocks and grass tufts, '
                  'NO characters, NO text. Flat cel-shaded illustration, ink-like linework, high contrast. '
                  'Palette strictly: near-black, neutral grays, pure white highlights, a few faint red embers. '
                  'No blue, no green, no gold. Horizontal composition, seamless-ish edges for scrolling.'),
    ('bg_mirrorworld', 'Dark anime game background, 16:9 side-scrolling "mirror world": everything inverted and wrong, '
                       'huge trees growing UPSIDE DOWN from the top of the frame, their roots hanging in the air, '
                       'a cracked mirror-like sky with sharp shards and thin cracks, pale ground with faint reflections, '
                       'NO characters, NO text. Flat cel-shaded ink illustration, high contrast. '
                       'Palette strictly: near-black, neutral grays, pure white, thin pure red crack lines. '
                       'No blue, no green, no gold. Horizontal composition for scrolling.'),
]


def gen(prompt, size='1536x864'):
    body = json.dumps({'model': 'gpt-image-2', 'prompt': prompt, 'n': 1,
                       'size': size, 'response_format': 'b64_json'}).encode()
    req = urllib.request.Request(URL, data=body, method='POST',
                                 headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=400) as r:
        return base64.b64decode(json.loads(r.read().decode())['data'][0]['b64_json'])


os.makedirs('art/bg', exist_ok=True)
for name, prompt in JOBS:
    t = time.time()
    raw = gen(prompt)
    path = 'art/bg/%s.png' % name
    open(path, 'wb').write(raw)
    print(path, '%.1fs' % (time.time() - t), Image.open(io.BytesIO(raw)).size)
