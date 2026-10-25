# -*- coding: utf-8 -*-
"""用 gpt-image-2 图生图把猩红魔姬立绘改成成熟比例（保持原始设计）。"""
import io
import json
import os
import time
import urllib.request
import uuid

KEY = 'REDACTED-API-KEY'
URL = 'https://api.a6api.com/v1/images/edits'
SRC = 'art/portrait/crimson_stand.png'
OUT = 'art/portrait/crimson_mature_raw.png'

PROMPT = ('Keep this exact character design: white fur-trimmed hood with red cat-ear insides, gray-white hair, '
          'red eyes, red-and-black fur-trimmed coat, black corset with lacing, black shorts, black boots, '
          'palette only pure red #FF0000 / pure white / neutral grays. '
          'Change ONLY body proportions: make her a MATURE adult anime woman about 7 heads tall with long legs and a '
          'narrower head, calm arrogant expression with a faint smirk, gothic and elegant, not cute, not chibi. '
          'Same full-body standing pose, flat cel-shaded anime style with clean thick black linework, '
          'plain pure white background, character fully in frame, no text, no watermark.')


def multipart(fields, files):
    boundary = '----dsh' + uuid.uuid4().hex
    body = io.BytesIO()
    for k, v in fields.items():
        body.write(('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n'
                    % (boundary, k, v)).encode())
    for k, (fn, data, ctype) in files.items():
        body.write(('--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\n'
                    'Content-Type: %s\r\n\r\n' % (boundary, k, fn, ctype)).encode())
        body.write(data)
        body.write(b'\r\n')
    body.write(('--%s--\r\n' % boundary).encode())
    return body.getvalue(), 'multipart/form-data; boundary=' + boundary


data = open(SRC, 'rb').read()
fields = {'model': 'gpt-image-2', 'prompt': PROMPT, 'n': '1', 'size': '1024x1536'}
files = {'image': (os.path.basename(SRC), data, 'image/png')}
payload, ctype = multipart(fields, files)
req = urllib.request.Request(URL, data=payload, method='POST',
                             headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': ctype})
t = time.time()
with urllib.request.urlopen(req, timeout=300) as r:
    obj = json.loads(r.read().decode())
import base64
open(OUT, 'wb').write(base64.b64decode(obj['data'][0]['b64_json']))
print('saved', OUT, '%.1fs' % (time.time() - t))
