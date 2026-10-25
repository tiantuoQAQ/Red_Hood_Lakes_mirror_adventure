# 生成占位贴图（三层），用于验证贴图管线是否接通
import os
from PIL import Image, ImageDraw

OUT = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam\art\rek'
os.makedirs(OUT, exist_ok=True)

W, H = 512, 768          # 2 倍图
FOOT_Y = H - 24          # 脚底位置
CX = W // 2

RED = (255, 0, 0, 255)
DARK = (40, 40, 40, 255)
WHITE = (255, 255, 255, 255)


def canvas():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


# --- 斗篷：身后的一块梯形 ---
cape = canvas()
d = ImageDraw.Draw(cape)
d.polygon([(CX - 40, 120), (CX + 60, 120), (CX + 110, FOOT_Y - 60), (CX - 90, FOOT_Y - 60)], fill=RED)
cape.save(os.path.join(OUT, 'cape.png'))

# --- 后发：头后的一团 ---
hair = canvas()
d = ImageDraw.Draw(hair)
d.ellipse([CX - 70, 80, CX + 40, 300], fill=DARK)
hair.save(os.path.join(OUT, 'hair.png'))

# --- 身体：躯干 + 双腿（头已经拆出去了） ---
body = canvas()
d = ImageDraw.Draw(body)
d.polygon([(CX - 55, 185), (CX + 55, 185), (CX + 40, 430), (CX - 40, 430)], fill=RED)  # 躯干
d.rectangle([CX - 38, 430, CX - 8, FOOT_Y], fill=DARK)     # 左腿
d.rectangle([CX + 8, 430, CX + 38, FOOT_Y], fill=DARK)     # 右腿
d.ellipse([CX - 45, FOOT_Y - 14, CX - 2, FOOT_Y + 6], fill=DARK)   # 左靴
d.ellipse([CX + 2, FOOT_Y - 14, CX + 45, FOOT_Y + 6], fill=DARK)   # 右靴
body.save(os.path.join(OUT, 'body.png'))

# --- 头部：脸 + 兜帽 + 两只兽耳（绕脖子转，用来验证 head 层） ---
head = canvas()
d = ImageDraw.Draw(head)
d.ellipse([CX - 45, 70, CX + 45, 190], fill=DARK)                       # 脸
d.pieslice([CX - 52, 58, CX + 52, 178], 180, 360, fill=RED)             # 兜帽
d.polygon([(CX - 46, 96), (CX - 26, 42), (CX - 8, 92)], fill=RED)       # 左耳
d.polygon([(CX + 8, 92), (CX + 26, 42), (CX + 46, 96)], fill=RED)       # 右耳
d.ellipse([CX + 8, 118, CX + 24, 134], fill=WHITE)                      # 眼睛
head.save(os.path.join(OUT, 'head.png'))

print('占位贴图生成完成 ->', OUT)
for n in ('cape.png', 'hair.png', 'body.png', 'head.png'):
    p = os.path.join(OUT, n)
    print('  ', n, os.path.getsize(p), 'bytes')
