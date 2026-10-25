# -*- coding: utf-8 -*-
"""删除「TAB 一键跳过剧情」功能：Godot 与网页端同时移除（含 HUD 提示）。"""
import io

# ---------- Godot ----------
p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 剧情推进里不再接受 skip
s = s.replace('\t\tif _just("skip") and not locked:', '\t\tif false and not locked:   # TAB 跳过已移除', 1)
# 2) 教学/死亡等待里也不再用 skip 关闭
s = s.replace('if _just("confirm") or _just("skip") or _just("shoot"):', 'if _just("confirm") or _just("shoot"):', 1)
# 3) 移除输入映射
s = s.replace('\t\t"skip": Input.is_key_pressed(KEY_TAB),\n', '', 1)
# 4) HUD 提示去掉 TAB
s = s.replace('"ENTER / SPACE 继续    TAB 跳过"', '"ENTER / SPACE 继续"', 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('godot: tab skip removed' if s != orig else 'godot: NO CHANGE')

# ---------- Web ----------
p2 = 'src/cutscene.js'
w = io.open(p2, encoding='utf-8').read()
w2 = w
w2 = w2.replace("  if (Input.pressed('skip') && !locked) { skip(); return; }",
                "  // TAB 一键跳过已移除（反馈有 bug，先关闭该功能）")
w2 = w2.replace("label(ctx, 'Enter / 空格 继续    Tab 跳过', W - 30, H - 16, 13,",
                "label(ctx, 'Enter / 空格 继续', W - 30, H - 16, 13,")
io.open(p2, 'w', encoding='utf-8').write(w2)
print('web: tab skip removed' if w2 != w else 'web: NO CHANGE')

# ---------- Web input 映射 ----------
p3 = 'src/input.js'
i = io.open(p3, encoding='utf-8').read()
i2 = i.replace("  skip: ['Tab'],\n", "")
io.open(p3, 'w', encoding='utf-8').write(i2)
print('web input: tab mapping removed' if i2 != i else 'web input: NO CHANGE')
