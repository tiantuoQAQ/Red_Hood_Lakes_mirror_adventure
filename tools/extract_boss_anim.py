# -*- coding: utf-8 -*-
"""从即梦 mp4 提取猩红魔姬动作帧（v2）：边缘泛洪去黑底，保留角色暗部与红色特效。

产出：art/battle/scarlet/anim/<动作>/frame_XX.png（整帧、透明底、不定尺寸裁切）
"""
import os
import glob
import shutil
import subprocess
from collections import deque
import numpy as np
from PIL import Image

FF = r'D:\ALLKINDSOFAPPS\ffmpeg\bin\ffmpeg.exe'
SRC = r'E:\UserDATAxtmr\下载'
TMP = 'tmp/bossanim'
OUT = 'art/battle/scarlet/anim'
FPS = 12
WIDTH = 480
KEEP = 16
DARK = 24          # 视为背景的亮度上限

VIDEOS = {
    'idle': '待机,站立,悬浮动画.mp4',
    'move': '移动,蓄力动作.mp4',
    'thrust': '突刺动画，向前突进动作，2倍速或者三倍速播放.mp4',
    'slash': '挥出斩击,释放剑气,需要加速三倍播放使用.mp4',
}


def key_black(img):
    a = np.array(img.convert('RGB')).astype(np.int16)
    lum = a.max(axis=2)
    bg = lum <= DARK
    h, w = bg.shape
    seen = np.zeros((h, w), dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bg[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if bg[y, x] and not seen[y, x]:
                seen[y, x] = True
                q.append((x, y))
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and bg[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((nx, ny))
    alpha = np.where(seen, 0, 255).astype(np.uint8)
    # 边缘 1px 羽化，避免硬边
    soft = alpha.copy()
    soft[1:, :] = np.minimum(soft[1:, :], alpha[:-1, :])
    soft[:-1, :] = np.minimum(soft[:-1, :], alpha[1:, :])
    out = np.dstack([a.astype(np.uint8), alpha])
    return Image.fromarray(out, 'RGBA')


def extract(name, path, tmpdir):
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    os.makedirs(tmpdir, exist_ok=True)
    subprocess.run([FF, '-y', '-v', 'error', '-i', path,
                    '-vf', 'fps=%d,scale=%d:-1' % (FPS, WIDTH),
                    os.path.join(tmpdir, 'f_%04d.png')], check=True)
    return sorted(glob.glob(os.path.join(tmpdir, 'f_*.png')))


def build(name):
    path = os.path.join(SRC, VIDEOS[name])
    if not os.path.exists(path):
        print('  缺少视频:', path)
        return
    files = extract(name, path, os.path.join(TMP, name))
    if len(files) < 4:
        return
    outdir = os.path.join(OUT, name)
    os.makedirs(outdir, exist_ok=True)
    for f in glob.glob(os.path.join(outdir, 'frame_*.png')):
        os.remove(f)
    idxs = [int(round(i * (len(files) - 1) / (KEEP - 1))) for i in range(KEEP)]
    for n, i in enumerate(idxs):
        key_black(Image.open(files[i])).save(os.path.join(outdir, 'frame_%02d.png' % n))
    print('  %s: %d 帧 -> %s' % (name, KEEP, outdir))


def main():
    print('提取猩红魔姬动作帧 v2')
    for name in VIDEOS:
        build(name)


if __name__ == '__main__':
    main()
