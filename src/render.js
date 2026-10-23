'use strict';

const TAU = Math.PI * 2;

function render(ctx) {
  ctx.save();
  if (Game.shake > 0) {
    // 用衰减正弦而不是随机抖动：震动更「有力」，也不会让画面糊掉
    const s = Game.shake;
    const t = Game.frame * 0.85;
    ctx.translate(Math.sin(t) * s * 0.75, Math.cos(t * 1.37) * s * 0.55);
  }

  drawBackground(ctx);
  if (Game.player && Game.boss) {
    drawBoss(ctx);
    drawBullets(ctx);
    drawShots(ctx);
    drawPlayer(ctx);
  }
  drawParticles(ctx);
  drawDmgTexts(ctx);
  ctx.restore();

  drawScreenEffects(ctx);
  if (Game.player && Game.boss) drawHUD(ctx);
  drawBanner(ctx);
  drawOverlay(ctx);
}

// ------------------------------------------------------------- 背景

function drawBackground(ctx) {
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, COLORS.bg0);
  g.addColorStop(1, COLORS.bg1);
  ctx.fillStyle = g;
  ctx.fillRect(-40, -40, W + 80, H + 80);

  // 网格
  ctx.strokeStyle = 'rgba(255,255,255,0.032)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = ARENA.left; x <= ARENA.right; x += 64) {
    ctx.moveTo(x, ARENA.top);
    ctx.lineTo(x, GROUND_Y);
  }
  for (let y = ARENA.top; y <= GROUND_Y; y += 64) {
    ctx.moveTo(ARENA.left, y);
    ctx.lineTo(ARENA.right, y);
  }
  ctx.stroke();

  // 镜面轴
  ctx.save();
  ctx.setLineDash([8, 12]);
  ctx.strokeStyle = hexToRgba(COLORS.env, 0.16);
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(MIRROR_X, ARENA.top);
  ctx.lineTo(MIRROR_X, GROUND_Y);
  ctx.stroke();
  ctx.restore();

  // 地面
  ctx.fillStyle = COLORS.bg2;
  ctx.fillRect(-40, GROUND_Y, W + 80, H - GROUND_Y + 40);
  ctx.fillStyle = hexToRgba(COLORS.env, 0.30);
  ctx.fillRect(0, GROUND_Y, W, 2);
  ctx.fillStyle = 'rgba(255,255,255,0.05)';
  ctx.fillRect(0, GROUND_Y + 2, W, 1);
}

// ------------------------------------------------------------- BOSS

function hexPath(ctx, x, y, r, rot) {
  ctx.beginPath();
  for (let i = 0; i < 6; i++) {
    const a = -Math.PI / 2 + (i * Math.PI) / 3 + rot;
    const px = x + Math.cos(a) * r;
    const py = y + Math.sin(a) * r;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
}

function drawBossHex(ctx, x, y, r, rot, alpha) {
  ctx.save();
  ctx.globalAlpha = alpha === undefined ? 1 : alpha;

  hexPath(ctx, x, y, r, rot);
  ctx.fillStyle = COLORS.bg3;
  ctx.fill();
  ctx.strokeStyle = COLORS.env;
  ctx.lineWidth = 2;
  ctx.stroke();

  hexPath(ctx, x, y, r * 0.62, -rot * 1.6);
  ctx.strokeStyle = hexToRgba(COLORS.env, 0.35);
  ctx.lineWidth = 1;
  ctx.stroke();

  glowCircle(ctx, x, y, r * 0.20, COLORS.hazard, 3.4, 0.9);
  ctx.restore();
}

function drawBoss(ctx) {
  const b = Game.boss;

  // 镜像幽灵：提示「另一边也会开火」
  drawBossHex(ctx, mirrorX(b.x), b.y, b.r * 0.82, Game.frame * 0.004, 0.16);

  const pop = b.flash > 0 ? 1 + b.flash * 0.014 : 1;
  const r = b.r * pop;
  const rot = -Game.frame * 0.004;
  drawBossHex(ctx, b.x, b.y, r, rot, 1);

  // 命中反馈全部收在 BOSS 本体上：闪白 + 外扩冲击环，不污染整个屏幕
  if (b.flash > 0) {
    const a = b.flash / 4;
    ctx.save();
    hexPath(ctx, b.x, b.y, r, rot);
    ctx.fillStyle = 'rgba(255,255,255,' + (a * 0.55).toFixed(3) + ')';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,' + (a * 0.85).toFixed(3) + ')';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(b.x, b.y, r + 10 + (1 - a) * 26, 0, TAU);
    ctx.strokeStyle = 'rgba(255,255,255,' + (a * 0.45).toFixed(3) + ')';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.restore();
  }
}

// ------------------------------------------------------------- 弹幕

function drawBullets(ctx) {
  const list = Game.bullets;
  for (let i = 0; i < list.length; i++) {
    const b = list[i];
    glowCircle(ctx, b.x, b.y, b.r, COLORS.hazard, 2.2, 0.95);
    ctx.beginPath();
    ctx.arc(b.x, b.y, b.r * 0.34, 0, TAU);
    ctx.fillStyle = 'rgba(255,255,255,0.92)';
    ctx.fill();
  }
}

function drawShots(ctx) {
  const list = Game.shots;
  for (let i = 0; i < list.length; i++) {
    const s = list[i];
    glowCircle(ctx, s.x, s.y, s.r, COLORS.player, 2.6, 0.95);
  }
}

// ------------------------------------------------------------- 玩家

function drawPlayer(ctx) {
  const p = Game.player;
  const P = CFG.player;

  // 冲刺残影
  for (let i = 0; i < p.trail.length; i++) {
    const t = p.trail[i];
    const a = (t.life / t.max) * 0.28;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.translate(t.x, t.y);
    ctx.rotate(Math.PI / 4);
    ctx.fillStyle = COLORS.player;
    const s = P.visualR * 1.1;
    ctx.fillRect(-s / 2, -s / 2, s, s);
    ctx.restore();
  }

  const blink = p.invT > 0 && !p.ball && Math.floor(Game.frame / 4) % 2 === 0;
  ctx.save();
  if (blink) ctx.globalAlpha = 0.40;

  if (p.ball) {
    // 球形态：外环 + 旋转弧
    glowCircle(ctx, p.x, p.y, P.visualR * 1.05, COLORS.player, 2.2, 0.5);
    ctx.strokeStyle = hexToRgba(COLORS.env, 0.85);
    ctx.lineWidth = 2;
    for (let k = 0; k < 3; k++) {
      const a0 = Game.frame * 0.12 + (k * TAU) / 3;
      ctx.beginPath();
      ctx.arc(p.x, p.y, P.visualR * 1.35, a0, a0 + 0.9);
      ctx.stroke();
    }
    ctx.beginPath();
    ctx.arc(p.x, p.y, P.visualR * 0.55, 0, TAU);
    ctx.fillStyle = hexToRgba(COLORS.player, 0.30);
    ctx.fill();
  } else {
    // 常态：菱形冰晶
    ctx.translate(p.x, p.y);
    ctx.rotate(Math.PI / 4);
    const s = P.visualR * 1.5;
    ctx.fillStyle = hexToRgba(COLORS.player, 0.22);
    ctx.fillRect(-s / 2, -s / 2, s, s);
    ctx.strokeStyle = COLORS.player;
    ctx.lineWidth = 2;
    ctx.strokeRect(-s / 2, -s / 2, s, s);
    ctx.rotate(-Math.PI / 4);
    ctx.translate(-p.x, -p.y);
  }

  if (p.hurtFlash > 0) {
    ctx.strokeStyle = hexToRgba(COLORS.hazard, p.hurtFlash / 12);
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(p.x, p.y, P.visualR * 2.1, 0, TAU);
    ctx.stroke();
  }
  ctx.restore();

  // 判定点（永远显示的小白点：这是玩家唯一需要真正躲避的东西）
  ctx.beginPath();
  ctx.arc(p.x, p.y, 2.2, 0, TAU);
  ctx.fillStyle = 'rgba(255,255,255,0.95)';
  ctx.fill();

  if (Game.debug.hitbox) {
    ctx.save();
    ctx.setLineDash([3, 3]);
    ctx.strokeStyle = 'rgba(255,255,255,0.85)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(p.x, p.y, P.hitR, 0, TAU);
    ctx.stroke();

    ctx.strokeStyle = hexToRgba(COLORS.player, 0.55);
    ctx.beginPath();
    ctx.arc(p.x, p.y, P.grazeR, 0, TAU);
    ctx.stroke();
    ctx.restore();
  }

  // 擦弹脉冲：贴着弹幕掠过时向外扩散的一圈
  if (Game.grazePulse > 0) {
    const ga = Game.grazePulse / 10;
    ctx.beginPath();
    ctx.arc(p.x, p.y, P.grazeR + (1 - ga) * 20, 0, TAU);
    ctx.strokeStyle = hexToRgba(COLORS.player, ga * 0.8);
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  // 球形态体力条
  if (p.ball) {
    const w = 52;
    bar(ctx, p.x - w / 2, p.y - P.visualR * 2.2, w, 4, p.stamina / 100, COLORS.player);
  }
}

function drawParticles(ctx) {
  for (let i = 0; i < Game.particles.length; i++) {
    const q = Game.particles[i];
    const a = q.life / q.max;
    ctx.beginPath();
    ctx.arc(q.x, q.y, q.r * a, 0, TAU);
    ctx.fillStyle = hexToRgba(q.color, a * 0.9);
    ctx.fill();
  }
}

function drawDmgTexts(ctx) {
  for (let i = 0; i < Game.dmgTexts.length; i++) {
    const t = Game.dmgTexts[i];
    const a = Math.min(1, t.life / (t.max * 0.65));
    ctx.save();
    ctx.globalAlpha = a;
    label(ctx, t.text, t.x, t.y, t.small ? 13 : 18, t.color, 'center', 700);
    ctx.restore();
  }
}

// 全屏反馈：只保留受伤时的四周品红渐晕；命中不再全屏闪白（太刺眼，改为 BOSS 本体闪）
function drawScreenEffects(ctx) {
  if (Game.screenHurt > 0) {
    const a = Game.screenHurt / 18;
    const g = ctx.createRadialGradient(
      W / 2, H / 2, Math.min(W, H) * 0.22,
      W / 2, H / 2, Math.max(W, H) * 0.74
    );
    g.addColorStop(0, 'rgba(255,0,0,0)');
    g.addColorStop(1, 'rgba(255,0,0,' + (a * 0.62).toFixed(3) + ')');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
  }
}

// ------------------------------------------------------------- HUD

function drawDiamond(ctx, x, y, r, color, filled) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(Math.PI / 4);
  if (filled) {
    ctx.fillStyle = color;
    ctx.fillRect(-r, -r, r * 2, r * 2);
  } else {
    ctx.strokeStyle = hexToRgba(color, 0.35);
    ctx.lineWidth = 1.5;
    ctx.strokeRect(-r, -r, r * 2, r * 2);
  }
  ctx.restore();
}

function drawHUD(ctx) {
  const b = Game.boss;
  const P = CFG.player;

  // BOSS 血条
  const bw = 520;
  const bx = W / 2 - bw / 2;
  bar(ctx, bx, 28, bw, 7, b.hp / b.maxHp, COLORS.hazard);
  mono(ctx, 'BOSS', bx - 12, 35, 11, COLORS.dim, 'right');
  mono(ctx, 'PHASE ' + (b.phase + 1) + ' / ' + PHASES.length, bx + bw + 12, 35, 11, COLORS.dim, 'left');

  // 阶段刻度
  for (let i = 1; i < PHASES.length; i++) {
    const x = bx + bw * PHASES[i].at;
    ctx.fillStyle = hexToRgba(COLORS.ink, 0.35);
    ctx.fillRect(x - 0.5, 25, 1, 13);
  }

  // 生命
  for (let i = 0; i < P.lives; i++) {
    drawDiamond(ctx, 68 + i * 22, 38, 6, COLORS.player, i < Game.lives);
  }

  // 勇气
  bar(ctx, 60, 660, 240, 8, Game.courage / P.courageMax, COLORS.player);
  mono(ctx, '勇气 ' + Math.floor(Game.courage) + '%', 60, 654, 11, COLORS.dim);
  if (Game.courage >= P.courageMax) {
    mono(ctx, 'L / X 释放冰封', 312, 668, 12, COLORS.env);
  }

  // 擦弹连击：数字 + 剩余窗口
  const pl = Game.player;
  if (pl && pl.grazeChain > 0) {
    mono(ctx, '擦弹 x' + pl.grazeChain, 60, 638, 12, COLORS.player);
    bar(ctx, 130, 628, 120, 5, pl.grazeTimer / P.grazeChainWindow, COLORS.player);
  }

  // 状态提示（右下）
  mono(ctx, '点按冲刺=冲刺 · 按住冲刺=球形态 · 落地取消', W - 60, 668, 11, COLORS.dim, 'right');

  // 调试：真实输入延迟（按键到画面提交的平均值）
  if (Game.debug.hitbox && Game.debug.latencyMs > 0) {
    mono(ctx, '输入延迟 ' + Game.debug.latencyMs.toFixed(1) + ' ms', W - 60, 54, 11, COLORS.dim, 'right');
    mono(ctx, Math.round(1000 / Math.max(1, Game.debug.frameMs || 16.7)) + ' fps', W - 60, 70, 11, COLORS.dim, 'right');
  }
}

function drawBanner(ctx) {
  if (Game.bannerT <= 0) return;
  const a = Math.min(1, Game.bannerT / 30);
  ctx.save();
  ctx.globalAlpha = a * 0.9;
  label(ctx, Game.banner, W / 2, 200, 40, COLORS.ink, 'center', 700);
  ctx.restore();
}

// ------------------------------------------------------------- 覆盖层

function dim(ctx, alpha) {
  ctx.fillStyle = 'rgba(6,9,13,' + alpha + ')';
  ctx.fillRect(0, 0, W, H);
}

function drawOverlay(ctx) {
  if (Game.mode === 'title') {
    dim(ctx, 0.78);

    label(ctx, '镜', W / 2, 196, 88, COLORS.ink, 'center', 700);
    label(ctx, 'M I R R O R   ·   弹幕闪避原型', W / 2, 236, 16, COLORS.env, 'center', 500);

    const lines = [
      ['移动', 'A / D  或  ← / →'],
      ['跳跃', 'Space'],
      ['冲刺（点按）', 'Shift 或 K'],
      ['球形态（长按，无敌，落地取消）', '按住冲刺'],
      ['射击（自动瞄准）', 'J 或 Z'],
      ['冰封（勇气满）', 'L 或 X'],
      ['静音 / 暂停 / 重开', 'M / P / R']
    ];
    let y = 320;
    for (let i = 0; i < lines.length; i++) {
      label(ctx, lines[i][0], W / 2 - 24, y, 15, COLORS.dim, 'right', 400);
      label(ctx, lines[i][1], W / 2 + 12, y, 15, COLORS.ink, 'left', 500);
      y += 34;
    }

    const pulse = 0.55 + 0.45 * Math.sin(Game.frame * 0.08);
    ctx.save();
    ctx.globalAlpha = pulse;
    label(ctx, '按 Enter 开始', W / 2, y + 40, 20, COLORS.player, 'center', 600);
    ctx.restore();
    return;
  }

  if (Game.mode === 'dead') {
    dim(ctx, 0.66);
    label(ctx, '再来一次', W / 2, H / 2 - 10, 44, COLORS.player, 'center', 700);
    label(ctx, '按 R 重开', W / 2, H / 2 + 42, 17, COLORS.ink, 'center', 500);
  }

  if (Game.mode === 'win') {
    dim(ctx, 0.66);
    label(ctx, '通关', W / 2, H / 2 - 10, 44, COLORS.env, 'center', 700);
    label(ctx, '按 R 再来一次', W / 2, H / 2 + 42, 17, COLORS.ink, 'center', 500);
  }

  if (Game.paused && Game.mode === 'play') {
    dim(ctx, 0.55);
    label(ctx, '暂停', W / 2, H / 2, 40, COLORS.ink, 'center', 700);
    label(ctx, '按 P 继续', W / 2, H / 2 + 46, 15, COLORS.dim, 'center', 500);
  }
}
