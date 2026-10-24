'use strict';

// 游戏状态与主循环逻辑。所有手感参数都来自 CFG，可运行时修改。

const Game = {
  mode: 'title',      // title | story | play | dead | win
  paused: false,
  frame: 0,
  lives: 3,
  courage: 0,
  skills: {},         // 剧情解锁的技能，例如 { red_tragedy: true }
  afterBattle: null,  // 打完这场接哪个剧情章节；空则回结算
  currentBossId: 'marysue',
  walk: null,         // 走位段：{ untilX, next, target }
  theme: 'normal',    // 背景主题：normal | mirror（进入镜中世界后切换）
  cam: { x: 0 },      // 横向镜头（世界坐标 → 屏幕坐标偏移）
  bullets: [],
  shots: [],
  particles: [],
  warnings: [],
  beams: [],
  player: null,
  boss: null,
  banner: '',
  bannerT: 0,
  shake: 0,
  hitstop: 0,
  slowT: 0,
  dying: false,
  screenHurt: 0,
  dmgTexts: [],
  grazePulse: 0,
  deadT: 0,
  debug: { hitbox: true, latencyMs: 0 }
};

// ---------------------------------------------------------------- 构造

function makePlayer() {
  const P = CFG.player;
  return {
    x: MIRROR_X - 260,
    y: GROUND_Y - P.visualR,
    vx: 0,
    vy: 0,
    onGround: true,
    facing: 1,
    dashT: 0,
    dashCd: 0,
    dashRampT: 0,
    dashOut: 0,
    dashBuf: 0,
    invT: 0,
    ball: false,
    ballLaunch: 0,
    grazeChain: 0,
    grazeTimer: 0,
    stamina: 100,
    fireT: 0,
    jumpBuf: 0,
    coyote: 0,
    hurtFlash: 0,
    trail: []
  };
}

function makeBoss(id) {
  const B = CFG.boss;
  const def = (typeof BOSSES !== 'undefined' && id && BOSSES[id]) || null;
  const hp = def ? def.hp : B.hp;
  return {
    id: id || 'marysue',
    name: def ? def.name : 'BOSS',
    x: B.x,
    y0: B.y,
    y: B.y,
    hp: hp,
    maxHp: hp,
    r: B.r,
    phase: 0,
    scriptIdx: 0,
    scriptT: 0,
    gap: 60,
    flash: 0,
    pending: null,
    dashT: 0,
    dashTo: null
  };
}

function resetGame(bossId) {
  Game.currentBossId = bossId || Game.currentBossId || 'marysue';
  Game.mode = 'play';
  Game.paused = false;
  Game.frame = 0;
  Game.lives = CFG.player.lives;
  Game.courage = 0;
  Game.bullets.length = 0;
  Game.shots.length = 0;
  Game.particles.length = 0;
  Game.player = makePlayer();
  Game.boss = makeBoss(Game.currentBossId);
  Game.cam = { x: 0 };
  Game.banner = '';
  Game.bannerT = 0;
  Game.shake = 0;
  Game.hitstop = 0;
  Game.screenHurt = 0;
  Game.grazePulse = 0;
  Game.slowT = 0;
  Game.dying = false;
  Game.warnings.length = 0;
  Game.beams.length = 0;
  Game.dmgTexts.length = 0;
  Game.deadT = 0;
}

// ---------------------------------------------------------------- 更新

function update(dt) {
  Game.frame++;

  // 走位段：只有移动，没有 BOSS / 弹幕 / 射击
  if (Game.mode === 'walk') { updateWalk(dt); return; }

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

  if (Game.shake > 0) Game.shake = Math.max(0, Game.shake - dt * 30);
  if (Game.bannerT > 0) Game.bannerT--;
  if (Game.screenHurt > 0) Game.screenHurt--;
  if (Game.grazePulse > 0) Game.grazePulse--;

  if (Game.hitstop > 0) {
    Game.hitstop--;
    updateParticles(dt);
    updateDmgTexts(dt);
    return;
  }

  updatePlayer(dt);
  updateBoss(dt);
  updateShots(dt);
  updateBullets(dt);
  updateBeams(dt);
  updateParticles(dt);
  updateDmgTexts(dt);
  updateCamera(dt);
}

// ---------------------------------------------------------------- 镜头
// 目标：玩家在屏幕中间；平滑跟随；到地图边缘时被夹住（玩家随之靠边）。
function updateCamera(dt) {
  if (!Game.cam) Game.cam = { x: 0 };
  if (Game.mode === 'walk') { Game.cam.x = 0; return; }
  const p = Game.player;
  if (!p) return;

  const maxX = Math.max(0, WORLD_W - W);
  const target = Math.max(0, Math.min(maxX, p.x - W / 2));

  // 帧率无关的指数平滑：每帧保留约 14% 的差距
  const k = 1 - Math.pow(0.0001, dt);
  Game.cam.x += (target - Game.cam.x) * k;
  Game.cam.x = Math.max(0, Math.min(maxX, Game.cam.x));
}

// ---------------------------------------------------------------- 走位段
// 剧情用的「可操控向前走」：只有移动和跳跃，没有 BOSS、弹幕、射击。
// 走到 untilX 之后自动切回演出（Cutscene.start(next)）。

function startWalk(opts) {
  const P = CFG.player;
  Game.mode = 'walk';
  Game.paused = false;
  Game.boss = null;
  Game.bullets.length = 0;
  Game.shots.length = 0;
  Game.warnings.length = 0;
  Game.beams.length = 0;
  Game.dmgTexts.length = 0;
  Game.player = makePlayer();
  Game.player.x = ARENA.left + 60;
  Game.player.y = GROUND_Y - P.visualR;
  if (Game.cam) Game.cam.x = 0;
  Game.walk = {
    untilX: (opts && opts.untilX) || (ARENA.right - 140),
    next: (opts && opts.next) || null,
    // target: 可交互对象 { kind:'norden'|'mirror'|..., x, label }
    target: (opts && opts.target) ||
            (opts && opts.npc ? { kind: opts.npc, x: opts.npcX || 0, label: opts.npc } : null),
    bg: (opts && opts.bg) || 'normal',
    doneT: 0
  };
}

function leaveWalk(next) {
  Game.walk = null;
  if (next && typeof Cutscene !== 'undefined') {
    Game.mode = 'story';
    Cutscene.start(next);
  } else {
    Game.mode = 'title';
  }
}

function updateWalk(dt) {
  const p = Game.player;
  if (Game.cam) Game.cam.x = 0;
  updatePlayer(dt);

  // 越界钳制（走位段不许走出画面）
  if (p.x < ARENA.left + CFG.player.visualR) p.x = ARENA.left + CFG.player.visualR;
  if (p.x > ARENA.right - CFG.player.visualR) p.x = ARENA.right - CFG.player.visualR;

  const w = Game.walk;
  if (!w) return;

  // 有可交互对象：靠近 + 按 W 才继续
  if (w.target) {
    const tx = w.target.x || 0;
    if (Math.abs(p.x - tx) < 120 && Input.pressed('up')) {
      leaveWalk(w.next);
    }
    return;
  }

  if (p.x >= w.untilX) leaveWalk(w.next);
}

function updatePlayer(dt) {
  const P = CFG.player;
  const p = Game.player;

  if (p.dashCd > 0) p.dashCd--;
  if (p.invT > 0) p.invT--;
  if (p.hurtFlash > 0) p.hurtFlash--;
  if (p.jumpBuf > 0) p.jumpBuf--;
  if (p.fireT > 0) p.fireT--;
  if (p.coyote > 0) p.coyote--;
  if (p.grazeTimer > 0) {
    p.grazeTimer--;
    if (p.grazeTimer === 0) p.grazeChain = 0;   // 窗口超时，连击中断
  }

  const left = Input.held('left');
  const right = Input.held('right');
  const up = Input.held('up');
  const down = Input.held('down');

  // ---- 球形态：空中「按住 ↑ + 按冲刺」进入 ----
  // 必须离地：地面上按组合键只算普通冲刺，否则会变成站桩无敌。
  if (!p.ball) {
    if (!p.onGround && up && Input.pressed('dash') && p.stamina > P.ballMinStamina) {
      Input.consume('dash');           // 吃掉这次按下，不再额外触发一次普通冲刺
      p.ball = true;
      p.ballLaunch = P.ballLaunchFrames;
      p.dashT = 0;
      p.vx *= 0.4;
      p.vy = -P.ballSpeed;
      burst(p.x, p.y, COLORS.player, 14);
      Sfx.ballOn();
    }
  } else if (!Input.held('dash')) {
    // 松开冲刺立刻变回人——这才是玩家期待的控制感
    endBall(false);
  }

  // ---- 普通冲刺（带输入缓冲）----
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
  }

  // ---- 跳跃（带输入缓冲 + 郊狼时间）----
  if (Input.pressed('jump', 8)) p.jumpBuf = 8;
  if (!p.ball && p.jumpBuf > 0 && (p.onGround || p.coyote > 0)) {
    p.vy = P.jumpVel;
    p.onGround = false;
    p.coyote = 0;
    p.jumpBuf = 0;
    burst(p.x, p.y + P.visualR, COLORS.player, 6);
  }

  // ---- 移动 ----
  if (p.ball) {
    p.stamina -= P.ballDrain * dt;
    let dx = (right ? 1 : 0) - (left ? 1 : 0);
    let dy = (down ? 1 : 0) - (up ? 1 : 0);
    if (p.ballLaunch > 0) {
      p.ballLaunch--;
      dy = -1;                    // 起手上冲阶段忽略垂直输入
    }
    const len = Math.hypot(dx, dy);
    if (len > 0) { dx /= len; dy /= len; }
    p.vx = dx * P.ballSpeed;
    p.vy = dy * P.ballSpeed;
    if (dx !== 0) p.facing = dx > 0 ? 1 : -1;
    if (p.stamina <= 0) {
      p.stamina = 0;
      endBall(false);
    }
  } else {
    const dir = (right ? 1 : 0) - (left ? 1 : 0);
    if (p.dashT > 0) {
      // 起步不是瞬间满速：用 3 帧从 45% 推到 100%，让「发力」看得见
      if (p.dashRampT > 0) {
        // 先用当前档位算速度，再推进档位；反过来的话触发帧就被推到满速了
        const total = Math.max(1, P.dashRampFrames);
        const k = 1 - p.dashRampT / total;
        const eased = 1 - Math.pow(1 - k, 2);
        p.vx = p.facing * P.dashSpeed * (0.45 + 0.55 * eased);
        p.dashRampT--;
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
    } else if (dir !== 0) {
      p.vx += dir * P.accel * dt;
      p.vx = Math.max(-P.speed, Math.min(P.speed, p.vx));
      p.facing = dir;
    } else {
      const f = P.friction * dt;
      if (Math.abs(p.vx) <= f) p.vx = 0;
      else p.vx -= Math.sign(p.vx) * f;
    }
    p.vy += P.gravity * dt;
    // 体力回复
    p.stamina = Math.min(100, p.stamina + P.ballRegen * dt);
  }

  // ---- 位移 ----
  p.x += p.vx * dt;
  p.y += p.vy * dt;

  const r = P.visualR;
  if (p.x < ARENA.left + r) { p.x = ARENA.left + r; p.vx = 0; }
  if (p.x > ARENA.right - r) { p.x = ARENA.right - r; p.vx = 0; }
  if (p.y < ARENA.top + r) { p.y = ARENA.top + r; if (p.vy < 0) p.vy = 0; }

  if (p.y + r >= GROUND_Y) {
    p.y = GROUND_Y - r;
    if (p.ball) {
      if (P.ballExitOnLand) endBall(true);
      else p.vy = 0;           // 贴地悬浮，等玩家松开冲刺
    } else {
      p.vy = 0;
      p.onGround = true;
    }
  } else {
    p.onGround = false;
  }

  // 光球拖尾：每两帧在身后撒一颗，速度反向于移动方向
  if (p.ball && Game.frame % 2 === 0 && Game.particles.length < 260) {
    const back = Math.atan2(-p.vy, -p.vx || 0.0001);
    const a = back + (Math.random() - 0.5) * 0.9;
    const sp = 40 + Math.random() * 90;
    const life = 16 + Math.random() * 10;
    Game.particles.push({
      kind: 'fx',
      x: p.x + (Math.random() - 0.5) * 12,
      y: p.y + (Math.random() - 0.5) * 12,
      vx: Math.cos(a) * sp,
      vy: Math.sin(a) * sp,
      life: life,
      max: life,
      r: 2,
      size: 56 + Math.random() * 44,
      rot: Math.random() * 6.283,
      spin: (Math.random() - 0.5) * 0.22,
      color: COLORS.player
    });
  }

  // 冲刺残影衰减
  for (let i = p.trail.length - 1; i >= 0; i--) {
    p.trail[i].life--;
    if (p.trail[i].life <= 0) p.trail.splice(i, 1);
  }

  // ---- 射击：自动瞄准 BOSS ----
  // 走位段没有目标，直接不进入这一段
  if (Game.mode === 'walk') return;
  if (Input.held('fire') && p.fireT <= 0) {
    p.fireT = P.fireInterval;
    const b = Game.boss;
    const a = aimAngle(p.x, p.y, b.x, b.y);
    Game.shots.push({
      x: p.x,
      y: p.y,
      vx: Math.cos(a) * P.shotSpeed,
      vy: Math.sin(a) * P.shotSpeed,
      r: P.shotRadius,
      dmg: P.shotDamage
    });
    Sfx.shoot();
  }

  // ---- 技能：勇气满时释放 ----
  // 剧情中期解锁「红之惨剧」后，同一个键升格成清场 + 长无敌。
  if (Input.pressed('skill') && Game.courage >= P.courageMax) {
    const hasTragedy = !!(Game.skills && Game.skills.red_tragedy);
    Game.courage = 0;
    if (hasTragedy) {
      p.invT = Math.max(p.invT, 200);
      Game.boss.hp -= 80;
      Game.bullets.length = 0;          // 全屏清弹：翻盘键
      Game.shake = 18;
      Game.hitstop = 10;
      Game.banner = '红 之 惨 剧';
      Game.bannerT = 90;
      burst(Game.boss.x, Game.boss.y, COLORS.player, 70);
      for (let i = 0; i < 8; i++) {
        burst(p.x + (Math.random() - 0.5) * 260, p.y + (Math.random() - 0.5) * 160, COLORS.player, 6);
      }
      addDmgText(Game.boss.x, Game.boss.y - 30, 80, COLORS.player, false);
    } else {
      p.invT = Math.max(p.invT, CFG.skill.invFrames);
      Game.boss.hp -= CFG.skill.damage;
      Game.shake = 12;
      Game.hitstop = 6;
      Game.banner = '冰 封';
      Game.bannerT = 60;
      burst(Game.boss.x, Game.boss.y, COLORS.env, 44);
      addDmgText(Game.boss.x, Game.boss.y - 30, CFG.skill.damage, COLORS.env, false);
    }
    Sfx.skill();
    checkBossDeath();
  }
}

function endBall(landed) {
  const p = Game.player;
  if (!p.ball) return;
  p.ball = false;
  p.vx = 0;
  p.vy = 0;
  p.ballLaunch = 0;
  if (landed) burst(p.x, p.y + CFG.player.visualR, COLORS.player, 12);
  Sfx.ballOff();
}

function updateBoss(dt) {
  const b = Game.boss;
  const B = CFG.boss;

  if (b.dashT > 0 && b.dashTo) {
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
  if (b.flash > 0) b.flash--;

  // 阶段判定（每个 BOSS 有自己的阶段表）
  const phases = (typeof BOSSES !== 'undefined' && BOSSES[b.id] && BOSSES[b.id].phases) || PHASES;
  const ratio = b.hp / b.maxHp;
  let ph = 0;
  for (let i = 0; i < phases.length; i++) {
    if (ratio <= phases[i].at) ph = i;
  }
  if (ph !== b.phase) {
    b.phase = ph;
    b.gap = 70;
    b.scriptIdx = 0;
    b.scriptT = 0;
    Game.bullets.length = 0;     // 换阶段清屏：给玩家一口喘息，也算难度重置
    Game.shake = 10;
    Game.banner = 'PHASE ' + (ph + 1);
    Game.bannerT = 90;
    burst(b.x, b.y, COLORS.hazard, 30);
    Sfx.phase();
  }

  if (b.gap > 0) { b.gap--; return; }

  const script = phases[b.phase].script;
  const name = script[b.scriptIdx % script.length];
  const pat = PATTERNS[name];
  if (!pat) { b.gap = 30; return; }

  pat.fire(Game, b, b.scriptT);
  b.scriptT++;
  if (b.scriptT >= pat.dur) {
    b.scriptT = 0;
    b.scriptIdx++;
    b.gap = 34;
  }
}


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

function updateShots(dt) {
  const b = Game.boss;
  for (let i = Game.shots.length - 1; i >= 0; i--) {
    const s = Game.shots[i];
    s.x += s.vx * dt;
    s.y += s.vy * dt;
    if (s.x < ARENA.left - 160 || s.x > ARENA.right + 160 || s.y < -60 || s.y > H + 60) {
      Game.shots.splice(i, 1);
      continue;
    }
    if (Math.hypot(s.x - b.x, s.y - b.y) < b.r + s.r) {
      b.hp -= s.dmg;
      b.flash = 4;          // 闪的是 BOSS 本身，不是全屏
      Game.courage = Math.min(CFG.player.courageMax, Game.courage + CFG.player.couragePerHit);
    burst(s.x, s.y, COLORS.player, 4);
    addDmgText(s.x, s.y - 12, s.dmg, COLORS.player, false);
      Game.shake = Math.max(Game.shake, 1.8);
      Sfx.bossHit();
      Game.shots.splice(i, 1);
      checkBossDeath();
    }
  }
}

function updateBullets(dt) {
  const p = Game.player;
  const P = CFG.player;
  const invincible = p.invT > 0 || p.ball;

  for (let i = Game.bullets.length - 1; i >= 0; i--) {
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

    b.x += b.vx * dt;
    b.y += b.vy * dt;
    b.life--;

    if (b.life <= 0 || b.x < ARENA.left - 220 || b.x > ARENA.right + 220 ||
        b.y < -90 || b.y > H + 90) {
      Game.bullets.splice(i, 1);
      continue;
    }

    const d = Math.hypot(b.x - p.x, b.y - p.y);
    if (d < P.hitR + b.r) {
      if (!invincible) {
        hitPlayer(b);
        Game.bullets.splice(i, 1);
        continue;
      }
    } else if (!b.grazed && d < P.grazeR + b.r) {
      b.grazed = true;
      if (!invincible) {
        // 擦弹连击：连续贴身躲，勇气倍率上升，同时返还冲刺冷却
        p.grazeChain++;
        p.grazeTimer = P.grazeChainWindow;
        const mult = Math.min(
          P.grazeChainMaxMult,
          1 + Math.floor(p.grazeChain / P.grazeChainCourageStep) * 0.5
        );
        const gain = P.couragePerGraze * mult;
        Game.courage = Math.min(P.courageMax, Game.courage + gain);
        p.dashCd = Math.max(0, p.dashCd - P.grazeDashRefund);
        Game.grazePulse = 10;

        burst(b.x, b.y, COLORS.player, 2);
        addDmgText(b.x, b.y - 6,  + (gain % 1 === 0 ? gain : gain.toFixed(1)), COLORS.player, true);
        Sfx.graze(p.grazeChain);
      }
    }
  }
}

function hitPlayer(b) {
  const P = CFG.player;
  const p = Game.player;

  Game.lives--;
  Game.courage = Math.max(0, Game.courage - P.courageLoss);
  p.invT = P.hurtIFrames;
  p.hurtFlash = 12;
  p.ball = false;
  p.dashT = 0;
  p.grazeChain = 0;      // 中弹清空擦弹连击：这是贴脸躲的代价
  p.grazeTimer = 0;

  // 不击飞、也不顿帧：受击瞬间的时间与位移都必须保持连续，
  // 否则玩家正在躲的那口气会被打断。只靠无敌帧 + 视听觉反馈表达「被打到了」。
  Game.shake = 9;
  Game.screenHurt = 18;
  burst(p.x, p.y, COLORS.hazard, 18);
  Sfx.hurt();

  if (Game.lives <= 0) {
    Game.dying = true;
    Game.slowT = 26;              // 约 0.43 秒慢动作，之后进入死亡界面
    Sfx.dead();
  }
}

function checkBossDeath() {
  const b = Game.boss;
  if (b.hp <= 0) {
    b.hp = 0;
    Game.shake = 16;
    Game.hitstop = 8;
    burst(b.x, b.y, COLORS.hazard, 60);
    Sfx.win();

    // 剧情推进：这场打完有后续章节就切过场，没有才进结算
    if (Game.afterBattle && typeof Cutscene !== 'undefined') {
      const next = Game.afterBattle;
      Game.afterBattle = null;
      Cutscene.start(next);
      return;
    }
    Game.mode = 'win';
  }
}

// ---------------------------------------------------------------- 粒子

function burst(x, y, color, n) {
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2;
    const sp = 60 + Math.random() * 280;
    const life = 18 + Math.random() * 26;
    Game.particles.push({
      x: x,
      y: y,
      vx: Math.cos(a) * sp,
      vy: Math.sin(a) * sp,
      life: life,
      max: life,
      r: 1.5 + Math.random() * 2.5,
      color: color
    });
  }
}

function updateParticles(dt) {
  for (let i = Game.particles.length - 1; i >= 0; i--) {
    const q = Game.particles[i];
    if (q.kind === 'fx') {
      // 光球拖尾：无重力、只做阻尼，带自转
      q.x += q.vx * dt;
      q.y += q.vy * dt;
      q.vx *= 0.90;
      q.vy *= 0.90;
      q.rot += q.spin;
    } else {
      q.x += q.vx * dt;
      q.y += q.vy * dt;
      q.vx *= 0.94;
      q.vy = q.vy * 0.94 + 60 * dt;
    }
    q.life--;
    if (q.life <= 0) Game.particles.splice(i, 1);
  }
}

// 飘字：伤害数字与擦弹 +1，是最直接的「你打中了」的证明
function addDmgText(x, y, text, color, small) {
  Game.dmgTexts.push({
    x: x + (Math.random() - 0.5) * 16,
    y: y,
    vy: small ? -34 : -62,
    life: small ? 26 : 34,
    max: small ? 26 : 34,
    text: String(text),
    color: color,
    small: !!small
  });
}

function updateDmgTexts(dt) {
  for (let i = Game.dmgTexts.length - 1; i >= 0; i--) {
    const t = Game.dmgTexts[i];
    t.y += t.vy * dt;
    t.vy *= 0.92;
    t.life--;
    if (t.life <= 0) Game.dmgTexts.splice(i, 1);
  }
}
