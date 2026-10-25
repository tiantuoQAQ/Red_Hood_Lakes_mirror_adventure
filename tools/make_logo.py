# -*- coding: utf-8 -*-
"""合成《红之镜 DEMO》Logo：碎镜徽记（gpt-image-2 生成）+ 毛笔字标题。

产出：
    art/logo/hongzhijing_logo.png   透明底、1200x420，供游戏标题界面直接贴
    art_preview/logo_preview.png    1280x720 标题界面预览（黑底）
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

EMBLEM = 'art/logo/emblem_raw.png'
BRUSH = 'art/font/cutin_brush.ttf'
FALLBACK = 'C:/Windows/Fonts/msyh.ttc'
OUT = 'art/logo/hongzhijing_logo.png'
W, H = 1200, 420
RED = (255, 0, 0, 255)
WHITE = (255, 255, 255, 255)
GREY = (150, 150, 150, 255)
DARK = (10, 10, 10, 255)


def key_black(im, thr=26):
    """把近黑背景变透明"""
    a = np.array(im.convert('RGBA')).astype(np.int16)
    lum = a[:, :, :3].mean(axis=2)
    a[:, :, 3] = np.where(lum <= thr, 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size), path
    except Exception:
        return ImageFont.truetype(FALLBACK, size), FALLBACK


def text_with_outline(draw, xy, text, font, fill, outline, width):
    x, y = xy
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx * dx + dy * dy <= width * width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


def main():
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    # --- 徽记：key 掉黑底，缩放到 H 的 92%
    emb = key_black(Image.open(EMBLEM))
    em_h = int(H * 0.92)
    em = emb.resize((em_h, em_h), Image.LANCZOS)
    canvas.alpha_composite(em, (0, (H - em_h) // 2))

    # --- 标题「红之镜」
    tx = em_h + 26
    font_title, used = load_font(BRUSH, 190)
    tmp = ImageDraw.Draw(canvas)
    # 量宽度
    bbox = tmp.textbbox((0, 0), '红之镜', font=font_title)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    ty = int(H * 0.14) - bbox[1]
    text_with_outline(tmp, (tx, ty), '红之镜', font_title, RED, (0, 0, 0, 255), 6)

    # 细白高光（模拟烫印，低透明）
    hi = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hi)
    hd.text((tx - 2, ty - 2), '红之镜', font=font_title, fill=(255, 255, 255, 38))
    canvas.alpha_composite(hi)

    # --- 分隔线 + DEMO
    line_y = ty + th + 34
    tmp.line([(tx, line_y), (tx + tw, line_y)], fill=(255, 255, 255, 120), width=2)

    font_demo, _ = load_font(FALLBACK, 46)
    demo = 'D E M O'
    db = tmp.textbbox((0, 0), demo, font=font_demo)
    text_with_outline(tmp, (tx + tw - (db[2] - db[0]), line_y + 10), demo, font_demo, WHITE, (0, 0, 0, 255), 4)

    font_sub, _ = load_font(FALLBACK, 26)
    tmp.text((tx + 4, line_y + 74), 'M I R R O R   O F   R E D', font=font_sub, fill=(150, 150, 150, 220))

    os.makedirs('art/logo', exist_ok=True)
    canvas.save(OUT)

    # 预览：贴到 1280x720 黑底
    prev = Image.new('RGBA', (1280, 720), (8, 8, 10, 255))
    logo = canvas.copy()
    scale = min(1.0, 1080 / logo.width)
    logo = logo.resize((int(logo.width * scale), int(logo.height * scale)), Image.LANCZOS)
    prev.alpha_composite(logo, ((1280 - logo.width) // 2, (720 - logo.height) // 2 - 40))
    d2 = ImageDraw.Draw(prev)
    f2, _ = load_font(FALLBACK, 22)
    d2.text((1280 // 2 - 90, 560), 'ENTER  开始游戏', font=f2, fill=(230, 230, 230, 255))
    os.makedirs('art_preview', exist_ok=True)
    prev.convert('RGB').save('art_preview/logo_preview.png')
    print('字体:', used, '| 标题宽高:', tw, th)
    print('输出:', OUT, '与 art_preview/logo_preview.png')


if __name__ == '__main__':
    main()
