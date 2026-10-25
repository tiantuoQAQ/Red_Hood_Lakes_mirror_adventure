# -*- coding: utf-8 -*-
"""镜头丝滑跟随小红帽：走位段默认跟随、起始即对齐、边缘钳制、指数平滑。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 默认跟随
s = s.replace('\twalk_camera = bool(command.get("cam", walk_target.size() > 0))   # 有交互目标时默认跟随（否则目标可能在屏幕外）',
              '\twalk_camera = bool(command.get("cam", true))   # 走位段默认跟随小红帽', 1)

# 2) 起始直接对齐（不再先跳到 0 再滑过来）
s = s.replace('\tif command.has("bg"):\n\t\tstory_bg = str(command.get("bg", story_bg))\n\tcamera_x = 0.0',
              '\tif command.has("bg"):\n\t\tstory_bg = str(command.get("bg", story_bg))\n'
              '\t# 起始就把镜头对齐到玩家，避免先跳到地图最左再滑过来\n'
              '\tif walk_camera:\n'
              '\t\tcamera_x = clampf(player_pos.x - VIEW.x * 0.38, 0.0, WORLD_W - VIEW.x)\n'
              '\telse:\n'
              '\t\tcamera_x = 0.0', 1)

# 3) 指数平滑跟随（帧率无关，比 lerp 0.12 更跟手）
s = s.replace('\tif walk_camera:\n\t\tcamera_x = lerpf(camera_x, clampf(player_pos.x - 360.0, 0.0, WORLD_W - VIEW.x), 0.12)',
              '\tif walk_camera:\n'
              '\t\tvar cam_target := clampf(player_pos.x - VIEW.x * 0.38, 0.0, WORLD_W - VIEW.x)\n'
              '\t\tcamera_x = lerpf(camera_x, cam_target, 1.0 - pow(0.0004, FIXED_DT))', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
