# 游戏尺寸预览：把正面全身图缩到 40px / 80px 高，再放大 8 倍，检查剪影是否成立
import os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam'
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from recolor import recolor           # noqa: E402

SRC = r'E:\UserDATAxtmr\Documents\DSH\.dsh-vision-router\artifacts\.runs\.vision-run-handoff\materialized\337e4d80df4e2555c61c.png'
OUT = os.path.join(ROOT, 'art_preview')
arr = np.array(Image.open(SRC).convert('RGBA'))
rgb = np.array(Image.open(SRC).convert('RGB')).astype(int)
h, w, _ = rgb.shape

# 找出左半部分的独立图形块（列方向的空白分隔）
nonwhite = rgb.min(axis=2) < 235
col_has = nonwhite.any(axis=0)
blocks = []
start = None
for x in range(w):
    if col_has[x] and start is None:
        start = x
    elif not col_has[x] and start is not None:
        if x - start > 40:
            blocks.append((start, x))
        start = None
if start is not None:
    blocks.append((start, w))
print('列块:', blocks[:6])

x0, x1 = blocks[0]
sub = nonwhite[:, x0:x1]
rows = np.nonzero(sub.any(axis=1))[0]
y0, y1 = rows.min(), rows.max()
print('第一个图形的包围盒: x %d..%d  y %d..%d  尺寸 %dx%d' % (x0, x1, y0, y1, x1 - x0, y1 - y0))

SKIN = (12.0, 62.0)
variants = [
    ('RED layered',   0.0,   0.30, 0.86, SKIN),
    ('CYAN layered',  196.2, 0.26, 0.80, SKIN),
    ('CRIMSON layer', 0.0,   0.16, 0.52, SKIN),
]

panels = [('ORIGINAL', rgb[y0:y1 + 1, x0:x1 + 1].astype(np.uint8))]
for name, hue, lo, hi, nh in variants:
    o = recolor(arr, hue, lo, hi, neutral_hues=nh)[..., :3]
    panels.append((name, o[y0:y1 + 1, x0:x1 + 1]))

SCALE = 8
cell = 40 * SCALE
pad = 16
sheet_w = len(panels) * (cell + pad) + pad
sheet_h = 2 * (cell + 34) + pad
sheet = Image.new('RGB', (sheet_w, sheet_h), (14, 14, 14))
d = ImageDraw.Draw(sheet)

for i, (label, img) in enumerate(panels):
    im = Image.fromarray(img, 'RGB')
    ratio = img.shape[0] / img.shape[1]
    for row, target_h in enumerate((40, 80)):
        target_w = max(1, int(target_h / ratio))
        small = im.resize((target_w, target_h), Image.LANCZOS)
        big = small.resize((target_w * SCALE, target_h * SCALE), Image.NEAREST)
        px = i * (cell + pad) + pad + (cell - big.size[0]) // 2
        py = pad + row * (cell + 34)
        sheet.paste(big, (px, py))
        d.text((i * (cell + pad) + pad, py - 12), '%s  %dpx' % (label, target_h), fill=(220, 220, 220))

p = os.path.join(OUT, 'sprite_scale.png')
sheet.save(p)
print('游戏尺寸预览:', p, sheet.size)
