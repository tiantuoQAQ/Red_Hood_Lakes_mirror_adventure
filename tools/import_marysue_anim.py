# -*- coding: utf-8 -*-
"""导入玛丽苏待机动作帧（即梦视频拆的透明帧）→ 16 帧循环，并做三色锁定。"""
import os
import glob
from PIL import Image

SRC = r'E:\UserDATAxtmr\Desktop\mirror\marysue-battle-cutouts\marysue-battle-04-frames'
OUT = 'art/battle/marysue/anim/idle'
KEEP = 16


def main():
    files = sorted(glob.glob(os.path.join(SRC, '*.png')))
    if not files:
        print('没找到帧:', SRC)
        return
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, 'frame_*.png')):
        os.remove(f)
    idxs = [int(round(i * (len(files) - 1) / (KEEP - 1))) for i in range(KEEP)]
    # 统一裁切框（取所有帧的并集）
    union = None
    for i in idxs:
        im = Image.open(files[i]).convert('RGBA')
        bb = im.getbbox()
        if bb:
            union = bb if union is None else (min(union[0], bb[0]), min(union[1], bb[1]),
                                              max(union[2], bb[2]), max(union[3], bb[3]))
    for n, i in enumerate(idxs):
        im = Image.open(files[i]).convert('RGBA').crop(union)
        im.save(os.path.join(OUT, 'frame_%02d.png' % n))
    print('玛丽苏待机帧 %d -> %s 裁切 %s' % (KEEP, OUT, union))


if __name__ == '__main__':
    main()
