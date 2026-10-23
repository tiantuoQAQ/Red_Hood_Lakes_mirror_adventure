#!/usr/bin/env python
"""Recolor character art into the three-hue palette without touching its shape.

This is the deterministic implementation of "方案 A" in docs/三视图改色交接书.md:

  - The silhouette, alpha channel and every pixel's position stay identical.
  - Relative luminance of each pixel is kept and remapped into the character's
    assigned lightness band.
  - Hue is replaced with the character's assigned hue.
  - Pixels that were already nearly neutral stay neutral (so black line art and
    white highlights are not tinted).

Usage:
  python tools/recolor.py input.png -o out.png --hue 196.2 --lightness 0.40 0.75
  python tools/recolor.py art_src/ -o art_out/ --id rek --hue 196.2 --lightness 0.40 0.75
  python tools/recolor.py --selftest
"""

import argparse
import os
import sys

import numpy as np
from PIL import Image

LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def hsl_to_rgb(h, s, l):
    """Vectorised HSL -> RGB. h in degrees, s and l in 0..1."""
    h = np.mod(h, 360.0) / 360.0
    c = (1.0 - np.abs(2.0 * l - 1.0)) * s
    hp = h * 6.0
    x = c * (1.0 - np.abs(np.mod(hp, 2.0) - 1.0))
    m = l - c / 2.0

    r = np.zeros_like(h)
    g = np.zeros_like(h)
    b = np.zeros_like(h)

    seg = np.floor(hp).astype(np.int32) % 6
    masks = [seg == i for i in range(6)]
    combos = [(c, x, 0.0), (x, c, 0.0), (0.0, c, x), (0.0, x, c), (x, 0.0, c), (c, 0.0, x)]
    for mask, (rr, gg, bb) in zip(masks, combos):
        r = np.where(mask, rr, r)
        g = np.where(mask, gg, g)
        b = np.where(mask, bb, b)
    return np.clip(np.stack([r + m, g + m, b + m], axis=-1), 0, 1)


def recolor(arr, hue, lo, hi, sat_boost=0.25, chroma_min=0.08):
    """Return a recoloured RGBA uint8 array with identical shape and alpha."""
    rgb = arr[..., :3].astype(np.float32) / 255.0
    alpha = arr[..., 3]

    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    chroma = mx - mn

    lrel = (rgb * LUMA).sum(axis=2)
    lout = lo + (hi - lo) * lrel

    # saturation follows the source: flat colours stay saturated, shading stays softer
    ssrc = np.where(mx > 1e-6, chroma / np.maximum(mx, 1e-6), 0.0)
    sout = np.clip(ssrc + sat_boost, 0.0, 1.0)
    sout = np.where(ssrc < 0.05, 0.0, sout)   # near-flat areas: keep neutral-ish

    out_rgb = hsl_to_rgb(np.full_like(lrel, hue), sout, np.clip(lout, 0.0, 1.0))

    # HSL lightness is not perceptual luminance (green looks brighter than blue at
    # the same L), so rescale each pixel to hit the intended luminance. This keeps
    # the original light/dark ordering intact instead of shifting it per hue.
    cur_lum = (out_rgb * LUMA).sum(axis=2)
    scale = np.where(cur_lum > 1e-6, lout / np.maximum(cur_lum, 1e-6), 1.0)
    scale = np.clip(scale, 0.0, 3.0)
    out_rgb = np.clip(out_rgb * scale[..., None], 0.0, 1.0)

    # pixels that were already neutral stay neutral (line art, white highlight)
    neutral = chroma < chroma_min
    gray = np.stack([lrel, lrel, lrel], axis=-1)
    out_rgb = np.where(neutral[..., None], gray, out_rgb)

    out = np.empty_like(arr)
    out[..., :3] = np.clip(out_rgb * 255.0, 0, 255).astype(np.uint8)
    out[..., 3] = alpha
    return out


def process_file(src, dst, hue, lo, hi):
    im = Image.open(src)
    arr = np.array(im.convert('RGBA'))
    out = recolor(arr, hue, lo, hi)
    Image.fromarray(out, 'RGBA').save(dst)
    return dst


def selftest():
    """Build a fake three-view, recolour it, and verify shape is preserved."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from check_palette import analyse  # noqa: E402

    h = w = 320
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 3] = 0

    # torso: red cloth
    arr[100:230, 110:210, :3] = (192, 57, 43)
    arr[100:230, 110:210, 3] = 255
    # darker red block (shading)
    arr[180:230, 110:210, :3] = (123, 36, 28)
    # face: skin tone
    arr[60:100, 130:190, :3] = (242, 201, 160)
    arr[60:100, 130:190, 3] = 255
    # boots: brown
    arr[230:290, 120:150, :3] = (74, 48, 32)
    arr[230:290, 120:150, 3] = 255
    arr[230:290, 170:200, :3] = (74, 48, 32)
    arr[230:290, 170:200, 3] = 255
    # outline: near black
    arr[100:102, 110:210, :3] = (26, 26, 26)
    arr[100:102, 110:210, 3] = 255

    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_selftest_out.png')
    Image.fromarray(arr, 'RGBA').save(tmp)

    out = recolor(np.array(Image.open(tmp).convert('RGBA')), 196.2, 0.32, 0.82)
    out_path = tmp.replace('_selftest_out', '_selftest_recolored')
    Image.fromarray(out, 'RGBA').save(out_path)

    problems = []

    # 1. alpha identical
    if not np.array_equal(out[..., 3], arr[..., 3]):
        problems.append('alpha 通道被改动')

    # 2. RGB changed on coloured areas (something actually happened)
    if np.array_equal(out[..., :3], arr[..., :3]):
        problems.append('图像没有任何变化')

    # 3. luminance structure preserved: the ordering must survive, even if the
    #    absolute luminance shifts a little because cyan/red are darker than the
    #    original colours at the same HSL lightness.
    a_l = (arr[..., :3].astype(np.float32) / 255.0 * LUMA).sum(axis=2).ravel()
    b_l = (out[..., :3].astype(np.float32) / 255.0 * LUMA).sum(axis=2).ravel()
    pearson = float(np.corrcoef(a_l, b_l)[0, 1])
    ra = np.argsort(np.argsort(a_l)).astype(np.float32)
    rb = np.argsort(np.argsort(b_l)).astype(np.float32)
    spearman = float(np.corrcoef(ra, rb)[0, 1])
    if spearman < 0.98:
        problems.append('明暗层级被破坏（Spearman %.4f）' % spearman)

    # 4. palette compliant
    res = analyse(out_path, verbose=False)
    if not res.get('ok'):
        problems.append('改色后色相越界 %.2f%%' % (res.get('outside_share', 1) * 100))

    print('自检：alpha 保持 / 明暗 Spearman %.4f / Pearson %.4f / 色相越界 %.2f%%'
          % (spearman, pearson, res.get('outside_share', 0) * 100))
    for p in problems:
        print('FAIL  ' + p)
    print('结果：' + ('通过' if not problems else '不通过'))
    return 0 if not problems else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src', nargs='?')
    ap.add_argument('-o', '--out', required=False)
    ap.add_argument('--hue', type=float, default=196.2)
    ap.add_argument('--lightness', type=float, nargs=2, default=[0.35, 0.80])
    ap.add_argument('--id', default='')
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    if not args.src or not args.out:
        print('用法: python tools/recolor.py <图片或文件夹> -o <输出路径> --hue 196.2 --lightness 0.35 0.80')
        sys.exit(2)

    lo, hi = args.lightness
    if os.path.isdir(args.src):
        os.makedirs(args.out, exist_ok=True)
        n = 0
        for name in sorted(os.listdir(args.src)):
            if name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                dst = os.path.join(args.out, name)
                process_file(os.path.join(args.src, name), dst, args.hue, lo, hi)
                print('  改色 -> {}'.format(dst))
                n += 1
        print('共处理 {} 张'.format(n))
    else:
        out_path = args.out
        if os.path.isdir(out_path):
            out_path = os.path.join(out_path, os.path.basename(args.src))
        process_file(args.src, out_path, args.hue, lo, hi)
        print('改色 -> {}'.format(out_path))
        print('下一步: python tools/check_palette.py "{}"'.format(out_path))


if __name__ == '__main__':
    main()
