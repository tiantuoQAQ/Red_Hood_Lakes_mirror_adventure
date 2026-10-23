# 冲刺手感：起步加速 + 结束滑行 + 输入缓冲
import io

ROOT = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam'
ok = True

def patch(rel, pairs):
    global ok
    p = ROOT + '\\' + rel
    t = io.open(p, encoding='utf-8').read()
    for old, new in pairs:
        if old not in t:
            print('!! 锚点缺失 %s: %r' % (rel, old[:70]))
            ok = False
            continue
        t = t.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
    print('%s patched' % rel)

# ---------------- 参数
patch('src/config.js', [
("""    dashSpeed: 1020,
    dashFrames: 12,
    dashIFrames: 16,
    dashCd: 16,""",
 """    dashSpeed: 1020,
    dashFrames: 12,
    dashIFrames: 16,
    dashCd: 16,
    dashRampFrames: 3,     // 起步加速帧数：0 = 瞬间满速（手感硬、但会有"啪"的突变）
    dashOutFrames: 6,      // 冲刺结束后的滑行帧数
    dashOutKeep: 0.72,     // 滑行阶段每帧保留的速度比例
    inputBuffer: 8,        // 提前按键的缓存帧数"""),
])

# ---------------- 玩家状态
patch('src/game.js', [
("""    dashT: 0,
    dashCd: 0,""",
 """    dashT: 0,
    dashCd: 0,
    dashRampT: 0,
    dashOut: 0,
    dashBuf: 0,"""),

# ---------------- 冲刺触发改为带缓冲
("""  // ---- 普通冲刺 ----
  if (!p.ball && Input.pressed('dash') && p.dashCd <= 0) {
    p.dashT = P.dashFrames;
    p.dashCd = P.dashCd + P.dashFrames;
    p.invT = Math.max(p.invT, P.dashIFrames);
    p.vx = p.facing * P.dashSpeed;
    burst(p.x, p.y, COLORS.player, 8);
    Sfx.dash();
  }""",
 """  // ---- 普通冲刺（带输入缓冲）----
  // 按下时先记进缓冲，条件成熟的那一帧自动触发。
  // 这样「在冷却结束前一瞬间按」不会白按——这是连招不断的关键。
  if (!p.ball && Input.pressed('dash')) p.dashBuf = P.inputBuffer;
  if (p.dashBuf > 0) {
    p.dashBuf--;
    if (!p.ball && p.dashCd <= 0 && p.dashT === 0 && p.dashOut === 0) {
      p.dashBuf = 0;
      p.dashT = P.dashFrames;
      p.dashRampT = P.dashRampFrames;
      p.dashCd = P.dashCd + P.dashFrames;
      p.invT = Math.max(p.invT, P.dashIFrames);
      p.vx = p.facing * P.dashSpeed * 0.45;
      burst(p.x, p.y, COLORS.player, 8);
      Sfx.dash();
    }
  }"""),

# ---------------- 冲刺位移：起步加速 + 结束滑行
("""    if (p.dashT > 0) {
      p.vx = p.facing * P.dashSpeed;
      p.dashT--;
      if (Game.frame % 2 === 0) {
        p.trail.push({ x: p.x, y: p.y, life: 12, max: 12, facing: p.facing });
      }
    } else if (dir !== 0) {""",
 """    if (p.dashT > 0) {
      // 起步不是瞬间满速：用 3 帧从 45% 推到 100%，让「发力」看得见
      if (p.dashRampT > 0) {
        p.dashRampT--;
        const total = Math.max(1, P.dashRampFrames);
        const k = 1 - p.dashRampT / total;
        const eased = 1 - Math.pow(1 - k, 2);
        p.vx = p.facing * P.dashSpeed * (0.45 + 0.55 * eased);
      } else {
        p.vx = p.facing * P.dashSpeed;
      }
      p.dashT--;
      if (p.dashT === 0) p.dashOut = P.dashOutFrames;
      if (Game.frame % 2 === 0) {
        p.trail.push({ x: p.x, y: p.y, life: 12, max: 12, facing: p.facing });
      }
    } else if (p.dashOut > 0) {
      // 滑行：结束时不「撞墙」，让速度指数衰减到当前输入对应的目标速度
      p.dashOut--;
      const target = dir !== 0 ? dir * P.speed : 0;
      p.vx += (target - p.vx) * (1 - P.dashOutKeep);
      if (Game.frame % 2 === 0) {
        p.trail.push({ x: p.x, y: p.y, life: 8, max: 8, facing: p.facing });
      }
    } else if (dir !== 0) {"""),
])

print('OK' if ok else 'HAS MISSES')
