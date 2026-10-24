# 把任何一张图强制压进「三色相 + 中性灰」的调色板
#
# 与 tools/check_palette.py 判定口径对齐：
#   - chroma = (max(r,g,b) - min(r,g,b)) / 255；chroma < 0.08 的像素算「灰」，不参与色相检查
#   - 其余像素的色相必须落在 0° / 89.4° / 196.2° 的 ±12° 内
#
# 本脚本用比判定更严的阈值（灰 0.11 / 色相 ±10°），保证过检：
#   1. chroma 很低       → 直接变中性灰（保住明度）
#   2. 色相已在 ±10°内   → 原样保留
#   3. 其余：低 chroma   → 去色成中性灰（皮肤、米色、浅棕）
#            高 chroma   → 色相拧到最近的允许色相
#
# 用法: python tools/force_palette.py <in.png> [out.png]
import colorsys

import sys

from PIL import Image

ALLOWED = [0.0, 89.4, 196.2]
GRAY_CHROMA = 0.11
HUE_TOL = 10.0


def hue_dist(a, b):
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def nearest_hue(deg):
    best = ALLOWED[0]
    bd = 999.0
    for h in ALLOWED:
        d = hue_dist(deg, h)
        if d < bd:
            bd = d
            best = h
    return best


def to_gray(r, g, b):
    # 用亮度加权，避免整体变暗或变亮
    v = int(round(0.299 * r + 0.587 * g + 0.114 * b))
    return v, v, v


def force(src, dst):
    im = Image.open(src).convert('RGBA')
    px = im.load()
    w, h = im.size
    grays = 0
    snapped = 0

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue

            mx, mn = max(r, g, b), min(r, g, b)
            chroma = (mx - mn) / 255.0

            if chroma < GRAY_CHROMA:
                if chroma > 0.002:
                    px[x, y] = to_gray(r, g, b) + (a,)
                    grays += 1
                continue

            hh, ll, ss = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
            deg = hh * 360.0

            if min(hue_dist(deg, h2) for h2 in ALLOWED) <= HUE_TOL:
                continue

            if chroma <= 0.35:
                px[x, y] = to_gray(r, g, b) + (a,)
                grays += 1
            else:
                # 高彩度但色相不对：不要"拧到最近色相"（会把肤色拧成红色），统一去色
                px[x, y] = to_gray(r, g, b) + (a,)
                grays += 1

    im.save(dst)
    print('压色完成: {} -> {}  去色 {} px / 归位 {} px'.format(src, dst, grays, snapped))


if __name__ == '__main__':
    s = sys.argv[1]
    d = sys.argv[2] if len(sys.argv) > 2 else s
    force(s, d)
