#!/usr/bin/env python
"""Check that an image stays inside the allowed three-hue palette.

Rules (matching docs/美术资产交接.md):
  - Pixels with alpha < 26 are ignored (transparent).
  - Pixels whose absolute chroma (max channel - min channel) is below
    CHROMA_MIN * 255 are treated as neutral gray and ignored. Absolute chroma is
    used instead of HSV saturation because HSV saturation is relative: a very
    dark blue-gray such as #0B0E13 reads as 42% saturated even though it is
    visually neutral.
  - Every remaining pixel's hue must fall within +/- TOL degrees of one of the
    three allowed hue centers (0, 89.4, 196.2).
  - The share of offending pixels must stay below MAX_OUTSIDE (default 1%).

Usage:
  python tools/check_palette.py <file-or-dir> [<file-or-dir> ...]
  python tools/check_palette.py --selftest
"""

import argparse
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

ALLOWED_HUES = [0.0, 89.4, 196.2]
HUE_NAMES = ['red #FF0000', 'yellow-green #82FF00', 'cyan #00BAFF']


def load_rgba(path):
    im = Image.open(path)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    return np.array(im)


def hue_map(arr):
    """Return (hue_degrees, chroma) arrays for an RGBA uint8 array."""
    rgb = arr[..., :3].astype(np.float32) / 255.0
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    delta = mx - mn
    chroma = delta  # absolute chroma in 0..1

    safe = np.where(delta == 0, 1.0, delta)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    h = np.zeros_like(mx)
    h = np.where(mx == r, ((g - b) / safe) % 6.0, h)
    h = np.where((mx == g) & (mx != r), (b - r) / safe + 2.0, h)
    h = np.where((mx != r) & (mx != g), (r - g) / safe + 4.0, h)
    h = h * 60.0
    return h, chroma


def analyse(path, chroma_min=0.08, tol=12.0, max_outside=0.01, verbose=True):
    arr = load_rgba(path)
    if arr.ndim != 3 or arr.shape[2] < 3:
        return {'path': path, 'error': 'not an RGB image'}

    alpha = arr[..., 3] if arr.shape[2] == 4 else np.full(arr.shape[:2], 255, np.uint8)
    h, chroma = hue_map(arr)

    mask = (alpha >= 26) & (chroma >= chroma_min)
    hues = h[mask]

    if hues.size == 0:
        result = {'path': path, 'colored': 0, 'outside_share': 0.0, 'ok': True,
                  'shares': [0.0] * len(ALLOWED_HUES), 'size': (arr.shape[1], arr.shape[0])}
        if verbose:
            print('  {:<24} 全灰阶（无色相像素）  PASS'.format(os.path.basename(path)))
        return result

    d = np.abs(hues[:, None] - np.array(ALLOWED_HUES)[None, :])
    d = np.minimum(d, 360.0 - d)
    nearest = d.min(axis=1)
    inside = nearest <= tol
    outside_share = float((~inside).mean())

    shares = []
    for i in range(len(ALLOWED_HUES)):
        shares.append(float((d.argmin(axis=1)[inside] == i).sum()) / hues.size)

    ok = outside_share < max_outside
    if verbose:
        print('  {:<24} 有色像素 {:.1f}%  红 {:.1f}% / 绿 {:.1f}% / 青 {:.1f}%  越界 {:.2f}%  {}'
              .format(os.path.basename(path), mask.mean() * 100,
                      shares[0] * 100, shares[1] * 100, shares[2] * 100,
                      outside_share * 100, 'PASS' if ok else 'FAIL'))
        if not ok:
            bad = hues[~inside]
            hist, edges = np.histogram(bad, bins=36, range=(0, 360))
            top = np.argsort(hist)[::-1][:3]
            for t in top:
                if hist[t] == 0:
                    continue
                print('        越界色相集中在 {:>3.0f}°-{:<3.0f}°  占越界像素 {:.0f}%'
                      .format(edges[t], edges[t + 1], hist[t] / bad.size * 100))

    return {'path': path, 'colored': int(hues.size), 'outside_share': outside_share,
            'ok': ok, 'shares': shares, 'size': (arr.shape[1], arr.shape[0])}


def collect(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                for n in names:
                    if n.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        files.append(os.path.join(root, n))
        elif os.path.isfile(p):
            files.append(p)
    return sorted(files)


def selftest():
    """Build synthetic images and verify the checker accepts/rejects correctly."""
    tmp = tempfile.mkdtemp(prefix='palette_')
    ok_path = os.path.join(tmp, 'good.png')
    bad_path = os.path.join(tmp, 'bad.png')

    w, h = 256, 256
    ok = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ok)
    d.rectangle([0, 0, 80, 80], fill=(0x82, 0xFF, 0x00, 255))
    d.rectangle([88, 0, 168, 80], fill=(0xFF, 0x00, 0x00, 255))
    d.rectangle([176, 0, 255, 80], fill=(0x00, 0xBA, 0xFF, 255))
    d.rectangle([0, 88, 255, 150], fill=(128, 128, 128, 255))       # gray, ignored
    for i in range(100):                                              # red -> white gradient
        t = i / 99.0
        c = (int(255), int(255 * (1 - t) + 255 * t), int(255 * (1 - t) + 255 * t))
        d.rectangle([0, 160 + i, 255, 160 + i], fill=c + (255,))
    ok.save(ok_path)

    bad = ok.copy()
    db = ImageDraw.Draw(bad)
    db.rectangle([0, 0, 255, 30], fill=(255, 140, 0, 255))            # orange = 4th hue
    bad.save(bad_path)

    r_ok = analyse(ok_path)
    r_bad = analyse(bad_path)

    print('')
    ok_res = r_ok['ok'] is True
    bad_res = r_bad['ok'] is False
    print('self-test: 合规图应通过 -> {}'.format('PASS' if ok_res else 'FAIL'))
    print('self-test: 含橙色应被抓 -> {}'.format('PASS' if bad_res else 'FAIL'))
    return 0 if (ok_res and bad_res) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--chroma', type=float, default=0.08,
                    help='absolute chroma below this is treated as neutral gray (0-1)')
    ap.add_argument('--tol', type=float, default=12.0)
    ap.add_argument('--max-outside', type=float, default=0.01)
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    files = collect(args.paths)
    if not files:
        print('没有找到图片。用法: python tools/check_palette.py <文件夹或图片>')
        sys.exit(2)

    print('检查 {} 张图片（越界阈值 {:.1f}%，容差 ±{:.0f}°）'
          .format(len(files), args.max_outside * 100, args.tol))
    bad = 0
    for f in files:
        r = analyse(f, chroma_min=args.chroma, tol=args.tol, max_outside=args.max_outside)
        if not r.get('ok', False):
            bad += 1

    print('')
    print('结果: {} 张通过, {} 张越界'.format(len(files) - bad, bad))
    sys.exit(0 if bad == 0 else 1)


if __name__ == '__main__':
    main()
