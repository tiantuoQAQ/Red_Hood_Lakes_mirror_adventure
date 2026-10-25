# -*- coding: utf-8 -*-
"""补：默认已知角色 + Godot 侧 reveal 机制。"""
import io

# ---------- Web：默认已知 ----------
p = 'src/cutscene.js'
w = io.open(p, encoding='utf-8').read()
if 'const KNOWN = Object.create(null);' in w and 'KNOWN.rek = true' not in w:
    w = w.replace('const KNOWN = Object.create(null);   // 已自报姓名的角色',
                  'const KNOWN = Object.create(null);   // 已自报姓名的角色\n'
                  "  ['rek', 'norden', 'mabel', 'rek_crimson'].forEach(function (k) { KNOWN[k] = true; });", 1)
    io.open(p, 'w', encoding='utf-8').write(w)
    print('web: default known set')

# ---------- Godot ----------
p2 = 'godot/main.gd'
s = io.open(p2, encoding='utf-8').read()
orig = s

if 'var known_names' not in s:
    s = s.replace('var seen_speakers: Array = []  # 本章已登场过的角色（首次说话时弹称号）',
                  'var seen_speakers: Array = []  # 本章已登场过的角色（首次说话时弹称号）\n'
                  'var known_names: Array = ["rek", "norden", "mabel", "crimson", "rek_crimson"]  # 已自报姓名（玛丽苏靠 reveal）', 1)
    print('godot: known_names added')

# reveal 命令处理
if '"reveal":' not in s:
    s = s.replace('\t\t\t"intro":',
                  '\t\t\t"reveal":\n'
                  '\t\t\t\tvar rw := str(command.get("who", ""))\n'
                  '\t\t\t\tvar rkey := _portrait_base(rw)\n'
                  '\t\t\t\tif rkey != "" and not known_names.has(rkey):\n'
                  '\t\t\t\t\tknown_names.append(rkey)\n'
                  '\t\t\t\tstory_intro = rkey\n'
                  '\t\t\t\tintro_hold = 2.4\n'
                  '\t\t\t\tstory_timer = 0.6\n'
                  '\t\t\t\treturn\n'
                  '\t\t\t"intro":', 1)
    print('godot: reveal command added')

# 名牌：未揭示 → ？？？
s = s.replace('\t\t\tvar shown_name := "？？？" if story_expr == "shadow" else _display_name(story_who)',
              '\t\t\tvar who_key := _portrait_base(story_who)\n'
              '\t\t\tvar is_unknown := (not known_names.has(who_key)) or story_expr == "shadow"\n'
              '\t\t\tvar shown_name := "？？？" if is_unknown else _display_name(story_who)', 1)
s = s.replace('\t\t\tvar plate_color := Color(0.75, 0.75, 0.75) if story_expr == "shadow" else name_color',
              '\t\t\tvar plate_color := Color(0.75, 0.75, 0.75) if is_unknown else name_color', 1)
# 未揭示时不追加称号
s = s.replace('\t\t\tif story_expr != "shadow":',
              '\t\t\tif not is_unknown:', 1)

io.open(p2, 'w', encoding='utf-8').write(s)
print('godot patched' if s != orig else 'godot unchanged')
