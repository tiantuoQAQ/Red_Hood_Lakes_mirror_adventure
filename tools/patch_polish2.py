# -*- coding: utf-8 -*-
"""打磨：称号竖幅停留更久 + 受击红色晕影 + 刀光弹拖尾。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 竖幅停留：2.6 秒，并在下一句仍保留 0.6 秒
s = s.replace('\t\t"intro":\n\t\t\tstory_intro = str(command.get("id", ""))\n\t\t\tstory_timer = 1.8',
              '\t\t"intro":\n\t\t\tstory_intro = str(command.get("id", ""))\n\t\t\tstory_timer = 2.6', 1)

if 'var intro_hold' not in s:
    s = s.replace('var story_intro := ""', 'var story_intro := ""\nvar intro_hold := 0.0      # 竖幅在下一句仍停留的秒数', 1)

# 在 _story_advance 清空 intro 处保留 hold
s = s.replace('\tstory_intro = ""\n\tif kind != "cg":',
              '\tvar prev_intro := story_intro\n\tstory_intro = ""\n\tif prev_intro != "" and kind != "intro":\n\t\tstory_intro = prev_intro\n\t\tintro_hold = 0.6\n\tif kind != "cg":', 1)

# 每帧衰减 hold
s = s.replace('\tif story_fade > 0:',
              '\tif intro_hold > 0.0:\n\t\tintro_hold = maxf(0.0, intro_hold - FIXED_DT)\n\t\tif intro_hold <= 0.0:\n\t\t\tstory_intro = ""\n\tif story_fade > 0:', 1)

# 2) 受击红色晕影（玩家受伤后 18 帧）
if 'var hurt_vignette' not in s:
    s = s.replace('var fx_rings: Array = []', 'var hurt_vignette := 0\nvar fx_rings: Array = []', 1)
s = s.replace('\t\t\tplayer_hurt_invuln = 70\n\t\t\tsfx_player.play("hurt")',
              '\t\t\tplayer_hurt_invuln = 70\n\t\t\thurt_vignette = 18\n\t\t\tsfx_player.play("hurt")', 1)
if 'hurt_vignette > 0' not in s:
    s = s.replace('\t_draw_battle_overlays()',
                  '\tif hurt_vignette > 0:\n'
                  '\t\tvar hv := float(hurt_vignette) / 18.0\n'
                  '\t\tdraw_rect(Rect2(0, 0, VIEW.x, 14), Color(1, 0, 0, 0.45 * hv))\n'
                  '\t\tdraw_rect(Rect2(0, VIEW.y - 14, VIEW.x, 14), Color(1, 0, 0, 0.45 * hv))\n'
                  '\t\tdraw_rect(Rect2(0, 0, 14, VIEW.y), Color(1, 0, 0, 0.45 * hv))\n'
                  '\t\tdraw_rect(Rect2(VIEW.x - 14, 0, 14, VIEW.y), Color(1, 0, 0, 0.45 * hv))\n'
                  '\t\thurt_vignette -= 1\n'
                  '\t_draw_battle_overlays()', 1)

# 3) 刀光弹拖尾：在 _update_bullets 里给 blade/lance 记录上次位置并绘制残影
if 'trail_prev' not in s:
    s = s.replace('\tfor bullet in bullets:\n\t\tbullet["pos"] += bullet["vel"] * FIXED_DT',
                  '\tfor bullet in bullets:\n'
                  '\t\tvar prev_pos: Vector2 = bullet.get("prev_pos", bullet["pos"])\n'
                  '\t\tbullet["prev_pos"] = bullet["pos"]\n'
                  '\t\tbullet["pos"] += bullet["vel"] * FIXED_DT', 1)
    # 在绘制子弹处加拖尾（如果存在 draw_bullets 区域，用通用方式：在 _draw_battle_extras 里补）
    s = s.replace('func _draw_boss_extras() -> void:',
                  'func _draw_boss_extras() -> void:\n'
                  '\t# 刀光弹/激光拖尾\n'
                  '\tfor b in bullets:\n'
                  '\t\tvar kind := str(b.get("kind", ""))\n'
                  '\t\tif kind != "blade" and kind != "lance" and kind != "laser":\n'
                  '\t\t\tcontinue\n'
                  '\t\tvar pv: Vector2 = Vector2(b.get("prev_pos", b["pos"])) - Vector2(camera_x, 0)\n'
                  '\t\tvar pn: Vector2 = Vector2(b["pos"]) - Vector2(camera_x, 0)\n'
                  '\t\tif pv.distance_to(pn) < 60.0:\n'
                  '\t\t\tvar col: Color = b["color"]\n'
                  '\t\t\tcol.a = 0.28\n'
                  '\t\t\tdraw_line(pv, pn, col, 6.0)', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
