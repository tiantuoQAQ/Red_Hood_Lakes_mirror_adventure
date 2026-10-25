# -*- coding: utf-8 -*-
"""魔姬/玛丽苏新招式（参考用户弹幕地狱截图）：
魔姬：火焰弹幕带弱追踪并自动消散；落地追击斩（冲刺拖尾）；落地后连发新月剑气。
玛丽苏：符纸环 + 阴阳玉旋转 + 激光柱 + 粒子流光。
"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 贴图注册
if 'crescent' not in s:
    s = s.replace('\t\t"bullet_rain": "res://art/fx/bullets/bullet_rain.png",',
                  '\t\t"bullet_rain": "res://art/fx/bullets/bullet_rain.png",\n'
                  '\t\t"bullet_flame": "res://art/fx/bullets/flame_bullet.png",\n'
                  '\t\t"bullet_crescent": "res://art/fx/bullets/crescent.png",\n'
                  '\t\t"bullet_yinyang": "res://art/fx/bullets/yinyang_orb.png",\n'
                  '\t\t"bullet_talisman": "res://art/fx/bullets/talisman.png",\n'
                  '\t\t"bullet_beam": "res://art/fx/bullets/beam_pillar.png",', 1)
    print('new bullet textures registered')

# 2) 子弹支持 homing / 生命周期 / 贴图
if 'homing_turn' not in s:
    s = s.replace(
        'func _spawn_bullet(pos: Vector2, velocity: Vector2, color: Color, kind: String) -> void:\n'
        '\tbullets.append({"pos": pos, "vel": velocity, "life": 5.0, "color": color, "kind": kind, "angle": velocity.angle(), "grazed": false})',
        'func _spawn_bullet(pos: Vector2, velocity: Vector2, color: Color, kind: String, life := 5.0, homing := 0.0) -> void:\n'
        '\tbullets.append({"pos": pos, "vel": velocity, "life": life, "color": color, "kind": kind, '
        '"angle": velocity.angle(), "grazed": false, "homing": homing})', 1)
    print('spawn_bullet extended')

# 子弹更新：弱追踪
if '"homing": ' not in s and 'bullet["homing"]' not in s:
    s = s.replace('\tfor bullet in bullets:\n\t\tvar prev_pos: Vector2 = bullet.get("prev_pos", bullet["pos"])',
                  '\tfor bullet in bullets:\n'
                  '\t\tvar homing := float(bullet.get("homing", 0.0))\n'
                  '\t\tif homing > 0.0:\n'
                  '\t\t\tvar want := (player_pos - Vector2(bullet["pos"])).normalized() * Vector2(bullet["vel"]).length()\n'
                  '\t\t\tbullet["vel"] = Vector2(bullet["vel"]).lerp(want, homing * FIXED_DT * 60.0 * 0.02)\n'
                  '\t\t\tbullet["angle"] = Vector2(bullet["vel"]).angle()\n'
                  '\t\tvar prev_pos: Vector2 = bullet.get("prev_pos", bullet["pos"])', 1)
    print('homing update added')

# 3) 绘制映射加入新类型
s = s.replace('\t\t\t"rain":\n\t\t\t\tbtex_key = "bullet_rain"\n\t\t\t\tbsize = 42.0\n\t\t\t\trot = PI * 0.5',
              '\t\t\t"rain":\n\t\t\t\tbtex_key = "bullet_rain"\n\t\t\t\tbsize = 42.0\n\t\t\t\trot = PI * 0.5\n'
              '\t\t\t"flame":\n\t\t\t\tbtex_key = "bullet_flame"\n\t\t\t\tbsize = 34.0\n'
              '\t\t\t"crescent":\n\t\t\t\tbtex_key = "bullet_crescent"\n\t\t\t\tbsize = 86.0\n'
              '\t\t\t"yinyang":\n\t\t\t\tbtex_key = "bullet_yinyang"\n\t\t\t\tbsize = 54.0\n'
              '\t\t\t"talisman":\n\t\t\t\tbtex_key = "bullet_talisman"\n\t\t\t\tbsize = 32.0\n'
              '\t\t\t"beam":\n\t\t\t\tbtex_key = "bullet_beam"\n\t\t\t\tbsize = 120.0\n\t\t\t\trot = 0.0', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
