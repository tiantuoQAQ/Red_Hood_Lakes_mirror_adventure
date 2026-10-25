# 统一色相 + 减少灰阶数量（让画面看起来"只有三种颜色"而不是"渐变很多颜色"）
#
# 与 force_palette.py 的区别：
#   - force_palette 只管"过检"（把越界像素压回允许范围）
#   - 本脚本进一步"统一"：
#       1) 红色一律锁到 0°、青色一律锁到 196°，不让色相在 0-30°/330-360° 之间漂
#       2) 灰阶量化到 12 档，减少"看起来有很多颜色"的柔和过渡
#
# 用法: python tools/unify_palette.py <in.png> [out.png] [--gray 12]
import colorsys
import sys

from PIL import Image

CYAN_HUE = 196.2
GREEN_HUE = 89.4
GRAY_STEPS = 12


def unify(src, dst, gray_steps=GRAY_STEPS):
    im = Image.open(src).convert('RGBA')
    px = im.load()
    w, h = im.size
    locked = 0
    grayed = 0

    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue

            mx, mn = max(r, g, b), min(r, g, b)
            chroma = (mx - mn) / 255.0
            hh, ll, ss = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
            deg = hh * 360.0

            # 灰：保持原样（灰阶量化会在白毛/皮肤上产生噪点，不做）
            if chroma < 0.08:
                continue

            # 红/青：按**彩度**判断，不用 HLS 饱和度（接近白色时 HLS 饱和度会虚高，
            # 浅粉色腮红会被误判成高饱和红色）
            near_red = deg <= 14 or deg >= 346
            near_cyan = abs(deg - CYAN_HUE) <= 45
            near_green = abs(deg - GREEN_HUE) <= 78

            # 绿要先于青判定：黄绿(89°)与青(196°)之间有重叠带(151-167)，
            # 重叠区归绿，否则玛丽苏的绿泳衣上会冒出青色斑点
            if near_red and chroma >= 0.42:
                rr, gg, bb = colorsys.hls_to_rgb(0.0, ll, ss)
                px[x, y] = (int(rr * 255 + 0.5), int(gg * 255 + 0.5), int(bb * 255 + 0.5), a)
                locked += 1
            elif near_green and chroma >= 0.20 and ll <= 0.86:
                rr, gg, bb = colorsys.hls_to_rgb(GREEN_HUE / 360.0, ll, ss)
                px[x, y] = (int(rr * 255 + 0.5), int(gg * 255 + 0.5), int(bb * 255 + 0.5), a)
                locked += 1
            elif near_cyan and chroma >= 0.20 and ll <= 0.88:
                rr, gg, bb = colorsys.hls_to_rgb(CYAN_HUE / 360.0, ll, ss)
                px[x, y] = (int(rr * 255 + 0.5), int(gg * 255 + 0.5), int(bb * 255 + 0.5), a)
                locked += 1
            else:
                # 浅红/粉/其它低彩度颜色：一律变灰（腮红、泛红、暖灰都消失）
                v = int(round(255 * ll))
                px[x, y] = (v, v, v, a)
                grayed += 1

    im.save(dst)
    print('统一完成: {} -> {}  锁色相 {} px / 转灰 {} px'.format(src, dst, locked, grayed))


if __name__ == '__main__':
    s = sys.argv[1]
    d = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else s
    steps = GRAY_STEPS
    if '--gray' in sys.argv:
        steps = int(sys.argv[sys.argv.index('--gray') + 1])
    unify(s, d, steps)
