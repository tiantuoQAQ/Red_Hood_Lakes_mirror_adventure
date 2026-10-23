'use strict';

// 游戏状态与主循环逻辑。所有手感参数都来自 CFG，可运行时修改。

const Game = {
  mode: 'title',      // title | play | dead | win
  paused: false,
  frame: 0,
  lives: 3,
  courage: 0,
  bullets: [],
  shots: [],
  particles: [],
  player: null,
  boss: null,
  banner: '',
  bannerT: 0,
  shake: 0,
  hitstop: 0,
  screenHurt: 0,
  dmgTexts: [],
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
    invT: 0,
    ball: false,
    ballLaunch: 0,
    dashHold: 0,
    stamina: 100,
    fireT: 0,
    jumpBuf: 0,
    coyote: 0,
    hurtFlash: 0,
    trail: []
  };
}

function makeBoss() {
  const B = CFG.boss;
  return {
    x: B.x,
    y0: B.y,
    y: B.y,
    hp: B.hp,
    maxHp: B.hp,
    r: B.r,
    phase: 0,
    scriptIdx: 0,
    scriptT: 0,
    gap: 60,
    flash: 0
  };
}

function resetGame() {
  Game.mode = 'play';
  Game.paused = false;
  Game.frame = 0;
  Game.lives = CFG.player.lives;
  Game.courage = 0;
  Game.bullets.length = 0;
  Game.shots.length = 0;
  Game.particles.length = 0;
  Game.player = makePlayer();
  Game.boss = makeBoss();
  Game.banner = '';
  Game.bannerT = 0;
  Game.shake = 0;
  Game.hitstop = 0;
  Game.screenHurt = 0;
  Game.dmgTexts.length = 0;
  Game.deadT = 0;
}

// ---------------------------------------------------------------- 更新

function update(dt) {
  Game.frame++;

  if (Game.shake > 0) Game.shake = Math.max(0, Game.shake - dt * 30);
  if (Game.bannerT > 0) Game.bannerT--;
  if (Game.screenHurt > 0) Game.screenHurt--;

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
  updateParticles(dt);
  updateDmgTexts(dt);
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

  const left = Input.held('left');
  const right = Input.held('right');
  const up = Input.held('up');
  const down = Input.held('down');

  // ---- 进入球形态：空中长按冲刺 ----
  // 长按而不是按一下：这段延迟本身是手感的一部分，玩家能预期「按住就是在蓄力」
  if (!p.ball) {
    if (Input.held('dash') && !p.onGround) p.dashHold++;
    else p.dashHold = 0;

    if (p.dashHold >= P.ballHoldFrames && p.stamina > P.ballMinStamina) {
      p.ball = true;
      p.dashHold = 0;
      p.ballLaunch = P.ballLaunchFrames; // 起手强制上冲，避免贴地进入瞬间被地面取消
      p.dashT = 0;
      p.vx *= 0.4;
      p.vy = -P.ballSpeed;
      burst(p.x, p.y, COLORS.ice, 14);
      Sfx.ballOn();
    }
  } else {
    p.dashHold = 0;
  }

  // ---- 普通冲刺 ----
  if (!p.ball && Input.pressed('dash') && p.dashCd <= 0) {
    p.dashT = P.dashFrames;
    p.dashCd = P.dashCd + P.dashFrames;
    p.invT = Math.max(p.invT, P.dashIFrames);
    p.vx = p.facing * P.dashSpeed;
    burst(p.x, p.y, COLORS.ice, 8);
    Sfx.dash();
  }

  // ---- 跳跃（带输入缓冲 + 郊狼时间）----
  if (Input.pressed('jump', 8)) p.jumpBuf = 8;
  if (!p.ball && p.jumpBuf > 0 && (p.onGround || p.coyote > 0)) {
    p.vy = P.jumpVel;
    p.onGround = false;
    p.coyote = 0;
    p.jumpBuf = 0;
    burst(p.x, p.y + P.visualR, COLORS.ice, 6);
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
      p.vx = p.facing * P.dashSpeed;
      p.dashT--;
      if (Game.frame % 2 === 0) {
        p.trail.push({ x: p.x, y: p.y, life: 12, max: 12, facing: p.facing });
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
      endBall(true);           // 落地即取消球形态（核心设计）
    } else {
      p.vy = 0;
      p.onGround = true;
    }
  } else {
    p.onGround = false;
  }

  // 冲刺残影衰减
  for (let i = p.trail.length - 1; i >= 0; i--) {
    p.trail[i].life--;
    if (p.trail[i].life <= 0) p.trail.splice(i, 1);
  }

  // ---- 射击：自动瞄准 BOSS ----
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
  if (Input.pressed('skill') && Game.courage >= P.courageMax) {
    Game.courage = 0;
    p.invT = Math.max(p.invT, CFG.skill.invFrames);
    Game.boss.hp -= CFG.skill.damage;
    Game.shake = 12;
    Game.hitstop = 6;
    Game.banner = '冰 封';
    Game.bannerT = 60;
    burst(Game.boss.x, Game.boss.y, COLORS.ice, 44);
    addDmgText(Game.boss.x, Game.boss.y - 30, CFG.skill.damage, COLORS.ice, false);
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
  if (landed) burst(p.x, p.y + CFG.player.visualR, COLORS.ice, 12);
  Sfx.ballOff();
}

function updateBoss(dt) {
  const b = Game.boss;
  const B = CFG.boss;

  b.y = b.y0 + Math.sin(Game.frame * 0.017 * B.bobSpeed) * B.bobAmp;
  if (b.flash > 0) b.flash--;

  // 阶段判定
  const ratio = b.hp / b.maxHp;
  let ph = 0;
  for (let i = 0; i < PHASES.length; i++) {
    if (ratio <= PHASES[i].at) ph = i;
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

  const script = PHASES[b.phase].script;
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

function updateShots(dt) {
  const b = Game.boss;
  for (let i = Game.shots.length - 1; i >= 0; i--) {
    const s = Game.shots[i];
    s.x += s.vx * dt;
    s.y += s.vy * dt;
    if (s.x < -60 || s.x > W + 60 || s.y < -60 || s.y > H + 60) {
      Game.shots.splice(i, 1);
      continue;
    }
    if (Math.hypot(s.x - b.x, s.y - b.y) < b.r + s.r) {
      b.hp -= s.dmg;
      b.flash = 4;          // 闪的是 BOSS 本身，不是全屏
      Game.courage = Math.min(CFG.player.courageMax, Game.courage + CFG.player.couragePerHit);
      burst(s.x, s.y, COLORS.self, 4);
      addDmgText(s.x, s.y - 12, s.dmg, COLORS.self, false);
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
    b.x += b.vx * dt;
    b.y += b.vy * dt;
    b.life--;

    if (b.life <= 0 || b.x < -90 || b.x > W + 90 || b.y < -90 || b.y > H + 90) {
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
        Game.courage = Math.min(P.courageMax, Game.courage + P.couragePerGraze);
        burst(b.x, b.y, COLORS.self, 2);
        addDmgText(b.x, b.y - 6, '+' + P.couragePerGraze, COLORS.self, true);
        Sfx.graze();
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

  const dir = p.x < b.x ? -1 : 1;
  p.vx = dir * P.knockback;
  p.vy = -280;

  Game.shake = 9;
  Game.hitstop = 4;
  Game.screenHurt = 18;
  burst(p.x, p.y, COLORS.hazard, 18);
  Sfx.hurt();

  if (Game.lives <= 0) {
    Game.mode = 'dead';
    Game.deadT = 0;
    Sfx.dead();
  }
}

function checkBossDeath() {
  const b = Game.boss;
  if (b.hp <= 0) {
    b.hp = 0;
    Game.mode = 'win';
    Game.shake = 16;
    Game.hitstop = 8;
    burst(b.x, b.y, COLORS.hazard, 60);
    Sfx.win();
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
    q.x += q.vx * dt;
    q.y += q.vy * dt;
    q.vx *= 0.94;
    q.vy = q.vy * 0.94 + 60 * dt;
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
