# 一次性补齐：激光 / BOSS 冲刺 / 追踪弹 / 濒死慢动作 / 预警线
import io, re, sys

ROOT = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam\src'
ok = True

def patch(fname, pairs):
    global ok
    p = ROOT + '\\' + fname
    t = io.open(p, encoding='utf-8').read()
    for old, new in pairs:
        if old not in t:
            print('!! 未找到锚点 in %s: %r' % (fname, old[:60]))
            ok = False
            continue
        t = t.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
    print('%s patched' % fname)

# ---------------------------------------------------------------- config
patch('config.js', [
("""  bullets: {
    speedScale: 1,""",
 """  bullets: {
    speedScale: 1,
    homingSpeed: 215,
    homingTurn: 1.7,        // 追踪弹每秒最大转向（弧度）"""),

("""  skill: { damage: 36, invFrames: 130 }""",
 """  beam: { width: 26, warmup: 45, active: 34, len: 1700 },
  bossDash: { speed: 1500, frames: 18 },
  skill: { damage: 36, invFrames: 130 }"""),

("""const PHASES = [
  { at: 1.0, script: ['ring', 'mirrorFan'] },
  { at: 0.66, script: ['mirrorFan', 'spiral', 'lances'] },
  { at: 0.33, script: ['lances', 'orbit', 'crossfire', 'spiral'] }
];""",
 """const PHASES = [
  { at: 1.0, script: ['ring', 'mirrorFan'] },
  { at: 0.66, script: ['mirrorFan', 'lances', 'laser'] },
  { at: 0.33, script: ['laser', 'homing', 'bossDash', 'orbit'] }
];"""),
])

# ---------------------------------------------------------------- game.js
patch('game.js', [
# 状态容器
("""  particles: [],
  warnings: [],""",
 """  particles: [],
  warnings: [],
  beams: [],"""),

# boss 冲刺状态
("""    gap: 60,
    flash: 0""",
 """    gap: 60,
    flash: 0,
    pending: null,
    dashT: 0,
    dashTo: null"""),

# reset 清理
("""  Game.screenHurt = 0;
  Game.grazePulse = 0;""",
 """  Game.screenHurt = 0;
  Game.grazePulse = 0;
  Game.slowT = 0;
  Game.dying = false;
  Game.warnings.length = 0;
  Game.beams.length = 0;"""),

# update：慢动作 + 预警线 + 光束
("""function update(dt) {
  Game.frame++;
""",
 """function update(dt) {
  Game.frame++;

  // 濒死慢动作：只在死亡瞬间使用。帧计数会随之变慢，这是演出效果的可接受代价
  if (Game.slowT > 0) {
    Game.slowT--;
    dt *= 0.28;
    if (Game.slowT === 0 && Game.dying) {
      Game.dying = false;
      Game.mode = 'dead';
      Game.deadT = 0;
    }
  }

  for (let i = Game.warnings.length - 1; i >= 0; i--) {
    Game.warnings[i].life--;
    if (Game.warnings[i].life <= 0) Game.warnings.splice(i, 1);
  }
  for (let i = Game.beams.length - 1; i >= 0; i--) {
    Game.beams[i].life--;
    if (Game.beams[i].life <= 0) Game.beams.splice(i, 1);
  }
"""),

# 死亡改为先演出
("""  if (Game.lives <= 0) {
    Game.mode = 'dead';
    Game.deadT = 0;
    Sfx.dead();
  }""",
 """  if (Game.lives <= 0) {
    Game.dying = true;
    Game.slowT = 26;              // 约 0.43 秒慢动作，之后进入死亡界面
    Sfx.dead();
  }"""),

# 追踪弹转向
("""  for (let i = Game.bullets.length - 1; i >= 0; i--) {
    const b = Game.bullets[i];
    b.x += b.vx * dt;""",
 """  for (let i = Game.bullets.length - 1; i >= 0; i--) {
    const b = Game.bullets[i];

    // 追踪弹：限制转向速率，玩家可以靠横移绕开，不会被必中
    if (b.kind === 'homing') {
      const want = Math.atan2(p.y - b.y, p.x - b.x);
      let cur = Math.atan2(b.vy, b.vx);
      let dA = want - cur;
      while (dA > Math.PI) dA -= Math.PI * 2;
      while (dA < -Math.PI) dA += Math.PI * 2;
      const maxTurn = CFG.bullets.homingTurn * dt;
      cur += Math.max(-maxTurn, Math.min(maxTurn, dA));
      const sp = Math.hypot(b.vx, b.vy);
      b.vx = Math.cos(cur) * sp;
      b.vy = Math.sin(cur) * sp;
    }

    b.x += b.vx * dt;"""),
])

# ---------------------------------------------------------------- game.js：光束伤害 + BOSS 冲刺
p = ROOT + '\\game.js'
t = io.open(p, encoding='utf-8').read()

beam_fn = """
// 点到线段的距离：光束是线段而不是圆，必须单独判定
function distToSegment(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len2 = dx * dx + dy * dy;
  let t = len2 > 0 ? ((px - x1) * dx + (py - y1) * dy) / len2 : 0;
  t = Math.max(0, Math.min(1, t));
  const cx = x1 + dx * t;
  const cy = y1 + dy * t;
  return Math.hypot(px - cx, py - cy);
}

function updateBeams(dt) {
  const p = Game.player;
  const invincible = p.invT > 0 || p.ball;
  for (let i = 0; i < Game.beams.length; i++) {
    const bm = Game.beams[i];
    const elapsed = bm.max - bm.life;
    if (elapsed < bm.warmup) continue;          // 蓄力阶段不伤血
    const x2 = bm.x + Math.cos(bm.a) * CFG.beam.len;
    const y2 = bm.y + Math.sin(bm.a) * CFG.beam.len;
    const d = distToSegment(p.x, p.y, bm.x, bm.y, x2, y2);
    if (d < CFG.beam.width * 0.5 + CFG.player.hitR && !invincible && !bm.hit) {
      bm.hit = true;
      hitPlayer({ x: p.x, y: p.y });
    }
  }
}

"""
anchor = "function updateShots(dt) {"
assert anchor in t
t = t.replace(anchor, beam_fn + anchor, 1)

# 在 update 链里加入光束判定
old_chain = """  updateShots(dt);
  updateBullets(dt);"""
assert old_chain in t
t = t.replace(old_chain, """  updateShots(dt);
  updateBullets(dt);
  updateBeams(dt);""", 1)

# BOSS 冲刺移动
old_bob = """  b.y = b.y0 + Math.sin(Game.frame * 0.017 * B.bobSpeed) * B.bobAmp;
  if (b.flash > 0) b.flash--;"""
assert old_bob in t
t = t.replace(old_bob, """  if (b.dashT > 0 && b.dashTo) {
    // 冲刺：直接插值到目标点，期间不发射，到位后打一圈环形弹
    b.x += (b.dashTo.x - b.x) / b.dashT;
    b.y += (b.dashTo.y - b.y) / b.dashT;
    b.dashT--;
    if (b.dashT === 0) {
      const n = 14;
      for (let i = 0; i < n; i++) {
        spawnBullet(Game.bullets, b.x, b.y, (i * Math.PI * 2) / n, CFG.bullets.ringSpeed, CFG.bullets.r);
      }
      Game.shake = 8;
      b.dashTo = null;
      b.gap = 24;
    }
    return;
  }

  b.y = b.y0 + Math.sin(Game.frame * 0.017 * B.bobSpeed) * B.bobAmp;
  if (b.flash > 0) b.flash--;""", 1)

io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('game.js beams + dash patched')
print('OK' if ok else 'HAS MISSES')
