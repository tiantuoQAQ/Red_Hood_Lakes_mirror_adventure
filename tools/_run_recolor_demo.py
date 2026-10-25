# 对三视图跑三套配色，并生成对比图与一致性校验
import io, os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam'
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from recolor import recolor            # noqa: E402
from check_palette import analyse      # noqa: E402

SRC = r'E:\UserDATAxtmr\Documents\DSH\.dsh-vision-router\artifacts\.runs\.vision-run-handoff\materialized\337e4d80df4e2555c61c.png'
OUT = os.path.join(ROOT, 'art_preview')
os.makedirs(OUT, exist_ok=True)

im = Image.open(SRC).convert('RGBA')
arr = np.array(im)
print('原图尺寸: %dx%d' % im.size)

VARIANTS = [
    ('rek_red',     0.0,   0.30, 0.86),
    ('rek_cyan',    196.2, 0.26, 0.80),
    ('rek_crimson', 0.0,   0.16, 0.52),
]

def lum(a):
    return (a[..., :3].astype(np.float32) / 255.0 * np.array([0.2126, 0.7152, 0.0722])).sum(axis=2)

base_l = lum(arr).ravel()
outs = []
for name, hue, lo, hi in VARIANTS:
    o = recolor(arr, hue, lo, hi)
    p = os.path.join(OUT, name + '.png')
    Image.fromarray(o, 'RGBA').save(p)
    outs.append((name, o, p))
    print('写出 %s' % p)

print('')
print('=== 一致性与合规校验 ===')
for name, o, p in outs:
    b_l = lum(o).ravel()
    ra = np.argsort(np.argsort(base_l)).astype(np.float32)
    rb = np.argsort(np.argsort(b_l)).astype(np.float32)
    spear = float(np.corrcoef(ra, rb)[0, 1])

    # 形状一致性：对每个像素，原图「是否为线条/中性区」与改色后应当一致
    src_chroma = np.array(Image.open(SRC).convert('RGB')).astype(np.float32).max(2) - \
                 np.array(Image.open(SRC).convert('RGB')).astype(np.float32).min(2)
    out_chroma = o[..., :3].astype(np.float32).max(2) - o[..., :3].astype(np.float32).min(2)
    neutral_src = (src_chroma / 255.0) < 0.08
    neutral_out = (out_chroma / 255.0) < 0.08
    neutral_agree = float((neutral_src == neutral_out).mean())

    res = analyse(p, verbose=False)
    print('%-12s 明暗Spearman %.4f | 中性区一致率 %.4f | 色相越界 %.2f%% %s'
          % (name, spear, neutral_agree, res.get('outside_share', 0) * 100,
             'PASS' if res.get('ok') else 'FAIL'))

# 三套之间：像素位置必须完全一致（alpha 相同）
a0 = outs[0][1][..., 3]
same_alpha = all(np.array_equal(a0, v[1][..., 3]) for v in outs)
print('三套 alpha 完全一致: %s' % same_alpha)

# 对比图：原图 | 红 | 青 | 猩红
TH = 520
panels = []
panels.append(('ORIGINAL', Image.open(SRC).convert('RGB')))
for name, o, p in outs:
    panels.append((name.upper(), Image.fromarray(o[..., :3], 'RGB')))

scaled = []
for label, img in panels:
    w, h = img.size
    nh = int(h * TH / w)
    scaled.append((label, img.resize((TH, nh), Image.LANCZOS)))

H = max(s[1].size[1] for s in scaled) + 34
W = TH * len(scaled)
sheet = Image.new('RGB', (W, H), (18, 18, 18))
d = ImageDraw.Draw(sheet)
for i, (label, img) in enumerate(scaled):
    sheet.paste(img, (i * TH, 34))
    d.text((i * TH + 8, 10), label, fill=(230, 230, 230))
    d.rectangle([i * TH, 0, i * TH + TH - 1, H - 1], outline=(60, 60, 60))
cmp_path = os.path.join(OUT, 'compare.png')
sheet.save(cmp_path)
print('对比图: %s (%dx%d)' % (cmp_path, W, H))
