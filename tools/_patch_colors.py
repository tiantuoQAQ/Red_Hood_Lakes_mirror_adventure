# 一次性补丁：把语义色键重命名并逐行改写引用
# player(红) = 我方 / hazard(绿) = 危险 / env(青) = 环境与中立
import io, sys, re

RENDER = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam\src\render.js'
GAME   = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam\src\game.js'

def patch(path, repl):
    with io.open(path, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
    changed = 0
    for lineno, new in repl.items():
        idx = lineno - 1
        if idx >= len(lines):
            print('越界', path, lineno); continue
        if lines[idx] != new:
            lines[idx] = new
            changed += 1
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines))
    print('%s 改动 %d 行' % (path.rsplit('\\', 1)[-1], changed))

render_repl = {
    57:  '  ctx.strokeStyle = hexToRgba(COLORS.env, 0.16);',
    68:  '  ctx.fillStyle = hexToRgba(COLORS.env, 0.30);',
    95:  '  ctx.strokeStyle = COLORS.env;',
    100: '  ctx.strokeStyle = hexToRgba(COLORS.env, 0.35);',
    157: '    glowCircle(ctx, s.x, s.y, s.r, COLORS.player, 2.6, 0.95);',
    175: '    ctx.fillStyle = COLORS.player;',
    187: '    glowCircle(ctx, p.x, p.y, P.visualR * 1.05, COLORS.player, 2.2, 0.5);',
    188: '    ctx.strokeStyle = hexToRgba(COLORS.env, 0.85);',
    198: '    ctx.fillStyle = hexToRgba(COLORS.player, 0.30);',
    205: '    ctx.fillStyle = hexToRgba(COLORS.player, 0.22);',
    207: '    ctx.strokeStyle = COLORS.player;',
    238: '    ctx.strokeStyle = hexToRgba(COLORS.player, 0.55);',
    250: '    ctx.strokeStyle = hexToRgba(COLORS.player, ga * 0.8);',
    258: '    bar(ctx, p.x - w / 2, p.y - P.visualR * 2.2, w, 4, p.stamina / 100, COLORS.player);',
    292: "    g.addColorStop(0, 'rgba(255,0,0,0)');",
    293: "    g.addColorStop(1, 'rgba(255,0,0,' + (a * 0.62).toFixed(3) + ')');",
    336: '    drawDiamond(ctx, 68 + i * 22, 38, 6, COLORS.player, i < Game.lives);',
    340: '  bar(ctx, 60, 660, 240, 8, Game.courage / P.courageMax, COLORS.player);',
    343: "    mono(ctx, 'L / X 释放冰封', 312, 668, 12, COLORS.env);",
    349: "    mono(ctx, '擦弹 x' + pl.grazeChain, 60, 638, 12, COLORS.player);",
    350: '    bar(ctx, 130, 628, 120, 5, pl.grazeTimer / P.grazeChainWindow, COLORS.player);',
    384: "    label(ctx, 'M I R R O R   ·   弹幕闪避原型', W / 2, 236, 16, COLORS.env, 'center', 500);",
    405: "    label(ctx, '按 Enter 开始', W / 2, y + 40, 20, COLORS.player, 'center', 600);",
    412: "    label(ctx, '再来一次', W / 2, H / 2 - 10, 44, COLORS.player, 'center', 700);",
    418: "    label(ctx, '通关', W / 2, H / 2 - 10, 44, COLORS.env, 'center', 700);",
}

game_repl = {
    153: '    burst(p.x, p.y, COLORS.player, 14);',
    166: '    burst(p.x, p.y, COLORS.player, 8);',
    177: '    burst(p.x, p.y + P.visualR, COLORS.player, 6);',
    272: '    burst(Game.boss.x, Game.boss.y, COLORS.env, 44);',
    273: '    addDmgText(Game.boss.x, Game.boss.y - 30, CFG.skill.damage, COLORS.env, false);',
    288: '  if (landed) burst(p.x, p.y + CFG.player.visualR, COLORS.player, 12);',
}

patch(RENDER, render_repl)
patch(GAME, game_repl)

# 校验：不应再有 ice / self 键
for p in (RENDER, GAME):
    with io.open(p, 'r', encoding='utf-8') as f:
        txt = f.read()
    left = len(re.findall(r'COLORS\.(ice|self)\b', txt))
    print('%s 残留 ice/self 引用: %d' % (p.rsplit('\\', 1)[-1], left))
