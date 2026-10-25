# 对比：原图 / 整体单色化 / 保留皮肤与头发的分层版
import os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam'
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from recolor import recolor            # noqa: E402
from check_palette import analyse      # noqa: E402

SRC = r'E:\UserDATAxtmr\Documents\DSH\.dsh-vision-router\artifacts\.runs\.vision-run-handoff\materialized\337e4d80df4e2555c61c.png'
OUT = os.path.join(ROOT, 'art_preview')
os.makedirs(OUT, exist_ok=True)

arr = np.array(Image.open(SRC).convert('RGBA'))
SKIN = (12.0, 62.0)     # 皮肤与金发所在的源色相窗口

variants = [
    ('A red mono',      0.0,   0.30, 0.86, None),
    ('B red layered',   0.0,   0.30, 0.86, SKIN),
    ('C cyan layered',  196.2, 0.26, 0.80, SKIN),
    ('D crimson layer', 0.0,   0.16, 0.52, SKIN),
]

outs = []
for name, hue, lo, hi, nh in variants:
    o = recolor(arr, hue, lo, hi, neutral_hues=nh)
    p = os.path.join(OUT, name.split()[1] + ('_mono' if nh is None else '_layered') +
                     ('_cyan' if 'cyan' in name else '') + '.png')
    Image.fromarray(o, 'RGBA').save(p)
    res = analyse(p, verbose=False)
    print('%-16s 越界 %.2f%% %s' % (name, res.get('outside_share', 0) * 100,
                                    'PASS' if res.get('ok') else 'FAIL'))
    outs.append((name, o, p))

# 拼图：原图 + 四版
TH = 560
panels = [('ORIGINAL', Image.open(SRC).convert('RGB'))]
for name, o, p in outs:
    panels.append((name.upper(), Image.fromarray(o[..., :3], 'RGB')))

scaled = []
for label, img in panels:
    w, h = img.size
    scaled.append((label, img.resize((TH, int(h * TH / w)), Image.LANCZOS)))

H = max(s[1].size[1] for s in scaled) + 30
W = TH * len(scaled)
sheet = Image.new('RGB', (W, H), (16, 16, 16))
d = ImageDraw.Draw(sheet)
for i, (label, img) in enumerate(scaled):
    sheet.paste(img, (i * TH, 30))
    d.text((i * TH + 6, 9), label, fill=(235, 235, 235))
    d.rectangle([i * TH, 0, i * TH + TH - 1, H - 1], outline=(55, 55, 55))

cmp_path = os.path.join(OUT, 'compare2.png')
sheet.save(cmp_path)
print('对比图:', cmp_path, sheet.size)

# 游戏尺寸预览：把正面全身图缩到 40px 高，再放大 10 倍看剪影是否成立
# 先自动找出左侧第一组「非白像素」的列范围与行范围
rgb = np.array(Image.open(SRC).convert('RGB')).astype(int)
nonwhite = (rgb.min(axis=2) < 235)
cols = np.nonzero(nonwhite.any(axis=0))[0]
print('内容列范围 %d..%d' % (cols.min(), cols.max()))
