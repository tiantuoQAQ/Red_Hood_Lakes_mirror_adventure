# -*- coding: utf-8 -*-
"""给地图内待机立绘做「呼吸起伏」循环帧。

原理：以脚底为锚点，做轻微的竖向缩放 + 上下浮动 + 上半身微移，
生成 N 帧序列（默认 8 帧）与 GIF 预览。

用法：
    python tools/make_breathing.py                    # 处理 norden / mabel
    python tools/make_breathing.py art/char/xxx.png   # 处理指定图
"""
import io
import os
import sys
import math
from PIL import Image, ImageDraw

FRAMES = 8
AMPL_Y = 0.014      # 竖向缩放幅度（±1.4%）
AMPL_X = 0.006      # 横向反向缩放（±0.6%，保持体积感）
BOB = 2.5           # 整体上下浮动像素
UPPER_SHIFT = 1.2   # 上半身横向微移像素

DEFAULT = ['art/char/norden_idle.png', 'art/char/mabel_idle.png']


def content_box(im):
    bb = im.getbbox()
    return bb if bb else (0, 0, im.width, im.height)


def breathe_frames(src):
    im = Image.open(src).convert('RGBA')
    bb = content_box(im)
    x0, y0, x1, y1 = bb
    w, h = x1 - x0, y1 - y0
    body = im.crop(bb)
    out = []
    for i in range(FRAMES):
        ph = (i + 0.35) / FRAMES * math.tau   # 偏移相位，避免第 0/4 帧重复
        sy = 1 + AMPL_Y * math.sin(ph)
        sx = 1 - AMPL_X * math.sin(ph)
        nw, nh = max(1, int(w * sx)), max(1, int(h * sy))
        fr = body.resize((nw, nh), Image.LANCZOS)
        # 上半身微移：把上部 45% 再横向偏移一点，做出胸腔感
        if UPPER_SHIFT:
            cut = int(nh * 0.45)
            upper = fr.crop((0, 0, nw, cut))
            shifted = Image.new('RGBA', (nw, cut), (0, 0, 0, 0))
            dx = int(round(UPPER_SHIFT * math.sin(ph)))
            shifted.alpha_composite(upper, (dx, 0))
            fr.paste(shifted, (0, 0))
        canvas = Image.new('RGBA', im.size, (0, 0, 0, 0))
        bx = x0 + (w - nw) // 2
        bob = int(round(BOB * math.sin(ph)))
        by = y1 - nh - bob          # 脚底固定（略随呼吸起伏）
        canvas.alpha_composite(fr, (max(0, bx), max(0, by)))
        out.append(canvas)
    return out


def save(src):
    name = os.path.splitext(os.path.basename(src))[0]
    outdir = os.path.join(os.path.dirname(src), name + '_breathe')
    os.makedirs(outdir, exist_ok=True)
    frames = breathe_frames(src)
    for i, f in enumerate(frames):
        f.save(os.path.join(outdir, 'frame_%02d.png' % i))
    # GIF 预览（黑底，避免透明变白）
    gif_frames = []
    for f in frames:
        bg = Image.new('RGBA', f.size, (12, 12, 12, 255))
        bg.alpha_composite(f)
        gif_frames.append(bg.convert('RGB'))
    preview = os.path.join('art_preview', name + '_breathe.gif')
    os.makedirs('art_preview', exist_ok=True)
    gif_frames[0].save(preview, save_all=True, append_images=gif_frames[1:],
                       duration=int(1000 / FRAMES), loop=0, optimize=False)
    print(src, '->', outdir, FRAMES, 'frames; preview', preview)


if __name__ == '__main__':
    targets = sys.argv[1:] or DEFAULT
    for t in targets:
        if os.path.exists(t):
            save(t)
        else:
            print('跳过（不存在）:', t)
