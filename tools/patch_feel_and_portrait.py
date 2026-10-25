# -*- coding: utf-8 -*-
"""手感调整：
1) 左右移速 ×1.5（340 → 510）
2) 冲刺后 0.2 秒无敌（12 帧，取最大不覆盖原有无敌）
3) 体力回复 ×1.5（52 → 78）
4) 魔姬攻击频率降低（间隔拉长、连发减少）
5) 魔姬立绘：竖直拉长 12% 再整体等比缩小到 0.9
"""
import glob
import io

import numpy as np
from PIL import Image

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 移速 ×1.5
s = s.replace('var target_speed := axis * 340.0', 'var target_speed := axis * 510.0   # 用户要求：左右移速 ×1.5', 1)

# 2) 冲刺无敌 0.2s（12 帧）——取与现有无敌帧的最大值，不缩短
s = s.replace('player_dash_invuln = DASH_FRAMES + 4  # Dash invuln: 24 frames (20 dash + 4 extra, from Web規格)',
              'player_dash_invuln = maxi(DASH_FRAMES + 4, 12)  # 冲刺无敌：至少 0.2 秒（12 帧）', 1)

# 3) 体力回复 ×1.5
s = s.replace('player_stamina = minf(100.0, player_stamina + 52.0 * FIXED_DT)',
              'player_stamina = minf(100.0, player_stamina + 78.0 * FIXED_DT)   # 体力回复 ×1.5', 1)

# 4) 魔姬攻击频率降低
s = s.replace('\t\t\tif frame % 10 == 0:\n\t\t\t\tfor k in range(2):', '\t\t\tif frame % 18 == 0:\n\t\t\t\tfor k in range(2):', 1)
s = s.replace('\t\t\tif frame % 90 == 0:\n\t\t\t\tfor k in range(10):', '\t\t\tif frame % 150 == 0:\n\t\t\t\tfor k in range(8):', 1)
s = s.replace('\t\t\tif frame % 6 == 0:\n\t\t\t\tfor k in range(2):\n\t\t\t\t\tvar a5 :=', '\t\t\tif frame % 12 == 0:\n\t\t\t\tfor k in range(2):\n\t\t\t\t\tvar a5 :=', 1)
s = s.replace('\t\tif frame % 6 == 0:\n\t\t\tvar d := (player_pos - boss_pos).normalized()\n\t\t\t_spawn_bullet(boss_pos + d * 30.0, d * 620.0, RED, "crescent", 2.2, 0.0)',
              '\t\tif frame % 14 == 0:\n\t\t\tvar d := (player_pos - boss_pos).normalized()\n\t\t\t_spawn_bullet(boss_pos + d * 30.0, d * 620.0, RED, "crescent", 2.2, 0.0)', 1)
s = s.replace('\t\t\tif frame % 8 == 0:\n\t\t\t\tvar rx := 150.0 + randf() * 2100.0', '\t\t\tif frame % 20 == 0:\n\t\t\t\tvar rx := 150.0 + randf() * 2100.0', 1)
# 追击斩间隔放宽
s = s.replace('boss_skill_timer = 22\n\t\tboss_rush_side', 'boss_skill_timer = 30\n\t\tboss_rush_side', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('godot patched' if s != orig else 'NO CHANGE')

# 5) 魔姬立绘：竖直拉长 12% → 整体等比 ×0.9
for f in glob.glob('art/portrait/crimson_*.png'):
    if '_old' in f or '_chibi' in f:
        continue
    im = Image.open(f).convert('RGBA')
    bb = im.getbbox()
    if bb:
        im = im.crop(bb)
    stretched = im.resize((im.width, int(round(im.height * 1.12))), Image.LANCZOS)
    scaled = stretched.resize((max(1, int(stretched.width * 0.9)), max(1, int(stretched.height * 0.9))), Image.LANCZOS)
    canvas = Image.new('RGBA', (512, 768), (0, 0, 0, 0))
    if scaled.width <= 512 and scaled.height <= 768:
        canvas.alpha_composite(scaled, ((512 - scaled.width) // 2, 768 - scaled.height))
    else:
        ratio = min(512.0 / scaled.width, 768.0 / scaled.height)
        scaled = scaled.resize((int(scaled.width * ratio), int(scaled.height * ratio)), Image.LANCZOS)
        canvas.alpha_composite(scaled, ((512 - scaled.width) // 2, 768 - scaled.height))
    canvas.save(f)
    print('portrait adjusted:', f, canvas.size)
