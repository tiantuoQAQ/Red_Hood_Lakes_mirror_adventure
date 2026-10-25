"""Prepare the 2026-10-25 white-background references as separate runtime art.

Original references are never modified. Background removal is edge connected,
so white fur enclosed by the character's ink outline remains opaque. All
runtime frames share a 768px canvas and explicit neck/feet anchors.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'art/ref/rek_battle_2026-10-25'
OUTPUT = ROOT / 'art/battle/rek'
SIZE = (896, 768)
FOOT = (550, 730)
NECK = (610, 320)


def cutout(filename, threshold):
    image = Image.open(SOURCE / filename).convert('RGB')
    rgb = np.asarray(image).copy()
    lo, hi = rgb.min(axis=2), rgb.max(axis=2)
    background = (lo >= threshold) & ((hi.astype(int) - lo) < 34)
    mask = Image.fromarray(np.where(background, 255, 0).astype('uint8')).copy()
    for point in [(0, 0), (image.width-1, 0), (0, image.height-1), (image.width-1, image.height-1)]:
        if mask.getpixel(point) == 255:
            ImageDraw.floodfill(mask, point, 128, thresh=0)
    exterior = np.asarray(mask) == 128
    alpha = np.where(exterior, 0, 255).astype('uint8')
    # Feather the immediate outer edge without erasing white interior fur.
    near = np.asarray(Image.fromarray(exterior.astype('uint8') * 255).filter(ImageFilter.MaxFilter(3))) > 0
    edge = near & ~exterior & (lo > 160)
    alpha[edge] = np.clip((255 - lo[edge].astype(float)) * 3, 0, 255).astype('uint8')
    # Neutralize off-palette warm shading while retaining red and cyan.
    pixels = rgb.astype(float) / 255
    mx, mn = pixels.max(2), pixels.min(2)
    chroma = mx - mn
    delta = np.where(chroma == 0, 1, chroma)
    hue = np.zeros_like(mx)
    r, g, b = pixels[..., 0], pixels[..., 1], pixels[..., 2]
    hue = np.where(mx == r, ((g-b)/delta) % 6, hue)
    hue = np.where((mx == g) & (mx != r), (b-r)/delta + 2, hue)
    hue = np.where((mx == b) & (mx != r) & (mx != g), (r-g)/delta + 4, hue) * 60
    distance = np.min([np.minimum(np.abs(hue-center), 360-np.abs(hue-center)) for center in [0, 89.4, 196.2]], axis=0)
    neutral = (chroma < .11) | (distance > 10)
    gray = np.round(rgb @ np.array([.299, .587, .114])).astype('uint8')
    rgb[neutral] = np.repeat(gray[neutral, None], 3, axis=1)
    # The reference head uses teal that lies between the allowed blue hues.
    # Keep the eye color by mapping that region to the project's cyan.
    cyan = (hue > 155) & (hue < 215) & (chroma > .16) & ~exterior
    value = mx[cyan]
    rgb[cyan] = np.stack([value*.02, value*.73, value], axis=1) * 255
    rgb[exterior] = 0
    rgba = Image.fromarray(np.dstack([rgb, alpha]))
    bounds = rgba.getbbox()
    return rgba.crop(bounds), bounds


def paste_scaled(image, scale, anchor_source, anchor_canvas):
    canvas = Image.new('RGBA', SIZE)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    x = round(anchor_canvas[0] - anchor_source[0] * scale)
    y = round(anchor_canvas[1] - anchor_source[1] * scale)
    canvas.alpha_composite(resized, (x, y))
    return canvas


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {'canvas': SIZE, 'foot': FOOT, 'neck': NECK, 'runtime_scale': .34, 'source_bounds': {}}
    bodies = [('body_move', 'rek-body-move-source-white-bg.png', 228, (.660, .233)),
              ('body_charge', 'rek-body-charge-source-white-bg.png', 225, (.625, .233))]
    for key, filename, threshold, neck_uv in bodies:
        source_size = Image.open(SOURCE / filename).size
        crop, bounds = cutout(filename, threshold)
        neck = (source_size[0] * neck_uv[0] - bounds[0], source_size[1] * neck_uv[1] - bounds[1])
        scale = (FOOT[1] - NECK[1]) / (crop.height - neck[1])
        result = paste_scaled(crop, scale, neck, NECK)
        result.save(OUTPUT / (key + '.png'))
        manifest['source_bounds'][key] = bounds
    head, bounds = cutout('rek-head-source-white-bg.png', 228)
    head = ImageOps.mirror(head)
    # Hood opening sits at the neck; overlay it onto the body's collar.
    scale = 290 / head.height
    result = paste_scaled(head, scale, (head.width * .53, head.height * .92), NECK)
    result.save(OUTPUT / 'head.png')
    manifest['source_bounds']['head'] = bounds
    manifest['head_flipped'] = True
    for index, threshold in [(1, 228), (2, 190), (3, 220)]:
        key = f'dash_{index:02}'
        crop, bounds = cutout(f'rek-dash-keyframe-{index:02}.png', threshold)
        scale = min(630/crop.width, 655/crop.height)
        result = paste_scaled(crop, scale, (crop.width * .64, crop.height), FOOT)
        result.save(OUTPUT / (key + '.png'))
        manifest['source_bounds'][key] = bounds
    (OUTPUT / 'anchors.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    # Preview is a build artifact, not a runtime sprite.
    preview = Image.new('RGB', (1536, 1152), '#222222')
    draw = ImageDraw.Draw(preview)
    for index, key in enumerate(['move', 'charge', 'dash_01', 'dash_02', 'dash_03']):
        if key in ['move', 'charge']:
            item = Image.open(OUTPUT / ('body_' + key + '.png')).convert('RGBA')
            item.alpha_composite(Image.open(OUTPUT / 'head.png'))
        else:
            item = Image.open(OUTPUT / (key + '.png')).convert('RGBA')
        item.thumbnail((512, 512))
        x, y = (index % 3) * 512, (index // 3) * 576 + 35
        preview.paste(item, (x, y), item)
        draw.text((x + 16, y-25), key, fill='white')
    preview_dir = ROOT / 'tmp/rek_art'
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview.save(preview_dir / 'runtime_contact.png')
    print('Prepared 6 transparent runtime sprites in', OUTPUT)


if __name__ == '__main__':
    main()
