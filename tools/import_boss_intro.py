# -*- coding: utf-8 -*-
"""Boss 战开场视频 → 可播放帧序列（Godot 用）。
- 魔姬开场：即梦 1170（4.4MB）
- 玛丽苏开场：Desktop/mirror/marysue-boss-intro.mp4
每套抽 24 帧，缩放 640 宽，保留原始画面（黑底，播放时用 additive/正常混合）
产出：art/cg/intro_crimson/frame_XX.png、art/cg/intro_marysue/frame_XX.png
"""
import os
import glob
import shutil
import subprocess

FF = r'D:\ALLKINDSOFAPPS\ffmpeg\bin\ffmpeg.exe'
JOBS = [
    (r'E:\UserDATAxtmr\下载\jimeng-2026-10-24-1170-正向提示词 生成一段约4秒、16_9横版游戏Boss战开场动画。严格以我上传的猩....mp4',
     'art/cg/intro_crimson'),
    (r'E:\UserDATAxtmr\Desktop\mirror\marysue-boss-intro.mp4', 'art/cg/intro_marysue'),
]
FPS = 8
WIDTH = 640
KEEP = 24


def run(src, outdir):
    if not os.path.exists(src):
        print('缺少视频:', src)
        return
    tmp = os.path.join('tmp', 'intro_frames', os.path.basename(outdir))
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([FF, '-y', '-v', 'error', '-i', src, '-vf', 'fps=%d,scale=%d:-1' % (FPS, WIDTH),
                    os.path.join(tmp, 'f_%04d.png')], check=True)
    files = sorted(glob.glob(os.path.join(tmp, 'f_*.png')))
    if not files:
        print('抽帧失败:', src)
        return
    os.makedirs(outdir, exist_ok=True)
    for f in glob.glob(os.path.join(outdir, 'frame_*.png')):
        os.remove(f)
    idxs = [int(round(i * (len(files) - 1) / (KEEP - 1))) for i in range(KEEP)]
    for n, i in enumerate(idxs):
        shutil.copyfile(files[i], os.path.join(outdir, 'frame_%02d.png' % n))
    print('%s -> %s (%d 帧)' % (os.path.basename(src)[:30], outdir, KEEP))


for src, outdir in JOBS:
    run(src, outdir)
