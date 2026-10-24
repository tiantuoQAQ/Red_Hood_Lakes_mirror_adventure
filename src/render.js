'use strict';

const TAU = Math.PI * 2;

function render(ctx) {
  // 剧情演出：完全接管画面（背景/立绘/对话框都在 Cutscene 里画）
  if (Game.mode === 'story') {
    Cutscene.draw(ctx);
    return;
  }

  ctx.save();
  if (Game.shake > 0) {
    // 用衰减正弦而不是随机抖动：震动更「有力」，也不会让画面糊掉
    const s = Game.shake;
    const t = Game.frame * 0.85;
    ctx.translate(Math.sin(t) * s * 0.75, Math.cos(t * 1.37) * s * 0.55);
  }

  if (Game.mode === 'walk' && Game.walk && Game.walk.bg === 'void') {
    drawVoidBackground(ctx);
  } else {
    drawBackground(ctx);
  }
  if (Game.player) {
    if (Game.boss) {
      drawWarnings(ctx);
      drawBeams(ctx);
      drawBoss(ctx);
      drawBullets(ctx);
      drawShots(ctx);
    }
    drawPlayer(ctx);
  }
  // 镜中世界：先画地面，再把角色倒影叠在地面上
  if (Game.theme === 'mirror') {
    drawMirrorGround(ctx);
    drawReflections(ctx);
  }
  drawParticles(ctx);
  drawDmgTexts(ctx);
  ctx.restore();

  // 濒死演出：把画面去饱和（灰阶属于允许色板），再叠受伤渐晕
  if (Game.dying || Game.slowT > 0) {
    ctx.save();
    ctx.globalCompositeOperation = 'saturation';
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, W, H);
    ctx.restore();
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fillRect(0, 0, W, H);
  }

  drawScreenEffects(ctx);
  if (Game.player && Game.boss) drawHUD(ctx);
  if (Game.mode === 'walk') drawWalkNpc(ctx);
  drawBanner(ctx);
  drawOverlay(ctx);
}

// ------------------------------------------------------------- 背景

// 镜中世界的背景图：黑白、倒立的森林。加载不到就退回渐变。
const BG_IMG = {};
function getBgImg(key, path) {
  if (!BG_IMG[key]) {
    if (typeof Image === 'undefined') return null;
    BG_IMG[key] = new Image();
    BG_IMG[key].src = path;
  }
  const img = BG_IMG[key];
  return (img.complete && img.naturalWidth > 0) ? img : null;
}

// 镜中世界的地面 + 倒影
function drawMirrorGround(ctx) {
  const g = ctx.createLinearGradient(0, GROUND_Y, 0, H);
  g.addColorStop(0, 'rgba(18,18,18,0.96)');
  g.addColorStop(1, 'rgba(6,6,6,0.99)');
  ctx.fillStyle = g;
  ctx.fillRect(0, GROUND_Y, W, H - GROUND_Y);

  // 地面高光线：把「地面」和「倒影区」分开
  ctx.fillStyle = 'rgba(255,255,255,0.30)';
  ctx.fillRect(0, GROUND_Y, W, 1.5);

  // 一条淡淡的镜面反光，暗示这不是普通地面
  const rg = ctx.createLinearGradient(0, GROUND_Y, 0, H);
  rg.addColorStop(0, 'rgba(255,255,255,0.10)');
  rg.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = rg;
  ctx.fillRect(0, GROUND_Y + 2, W, H - GROUND_Y);
}

// 倒影：把角色沿地面线翻转、压暗，只在地面区域里显示
function drawReflections(ctx) {
  ctx.save();
  ctx.beginPath();
  ctx.rect(0, GROUND_Y, W, H - GROUND_Y);
  ctx.clip();

  ctx.globalAlpha = 0.26;
  ctx.translate(0, GROUND_Y * 2);
  ctx.scale(1, -1);

  if (Game.boss) drawBoss(ctx);
  if (Game.player) drawPlayer(ctx);

  ctx.restore();
}

function drawBackground(ctx) {
  if (Game.theme === 'mirror') {
    const img = getBgImg('mirror', 'art/bg/mirror.jpg');
    if (img) {
      const s = Math.max(W / img.naturalWidth, H / img.naturalHeight);
      const dw = img.naturalWidth * s;
      const dh = img.naturalHeight * s;
      // 轻微视差：玩家往右走，背景往左挪一点，画面不板
      const par = Game.player ? (Game.player.x - MIRROR_X) * 0.03 : 0;
      ctx.drawImage(img, (W - dw) / 2 - par, (H - dh) / 2, dw, dh);
      // 压暗：白底背景上绿色弹幕/红色主角会看不清，先压成深灰
      ctx.fillStyle = 'rgba(0,0,0,0.52)';
      ctx.fillRect(-40, -40, W + 80, H + 80);
      return;
    }
  }

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

// 五角星路径：弹幕用星形而不用圆点。形状语言更锐利，
// 也能帮「绿色=危险」这条反直觉设定（圆润的形状容易被读成补给品）。
function starPath(ctx, x, y, r, points, innerRatio, rot) {
  const n = points * 2;
  ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const rad = i % 2 === 0 ? r : r * innerRatio;
    const a = -Math.PI / 2 + (i * Math.PI) / points + rot;
    const px = x + Math.cos(a) * rad;
    const py = y + Math.sin(a) * rad;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
}

// ------------------------------------------------------------- 预警与光束

function drawWarnings(ctx) {
  const list = Game.warnings;
  for (let i = 0; i < list.length; i++) {
    const w = list[i];
    const k = w.life / w.max;                 // 1 → 0
    const pulse = 0.35 + 0.45 * Math.abs(Math.sin(Game.frame * 0.25));
    const x2 = w.x + Math.cos(w.a) * w.len;
    const y2 = w.y + Math.sin(w.a) * w.len;

    ctx.save();
    ctx.setLineDash([14, 10]);
    ctx.lineWidth = 1 + (1 - k) * 2;
    ctx.strokeStyle = hexToRgba(COLORS.hazard, pulse * 0.85);
    ctx.beginPath();
    ctx.moveTo(w.x, w.y);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.restore();
  }
}

function drawBeams(ctx) {
  const list = Game.beams;
  for (let i = 0; i < list.length; i++) {
    const bm = list[i];
    const elapsed = bm.max - bm.life;
    const x2 = bm.x + Math.cos(bm.a) * CFG.beam.len;
    const y2 = bm.y + Math.sin(bm.a) * CFG.beam.len;

    if (elapsed < bm.warmup) {
      // 蓄力：越来越亮的细线
      const k = elapsed / bm.warmup;
      ctx.strokeStyle = hexToRgba(COLORS.hazard, 0.25 + 0.6 * k);
      ctx.lineWidth = 1 + 3 * k;
      ctx.beginPath();
      ctx.moveTo(bm.x, bm.y);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    } else {
      // 实体光束：白色外壳 + 实体绿核 + 白色亮心（外壳用白，避免与红色混出橙色）
      const left = (bm.max - elapsed) / (bm.max - bm.warmup);
      const w = CFG.beam.width * (0.75 + 0.35 * left);
      ctx.strokeStyle = 'rgba(255,255,255,0.16)';
      ctx.lineWidth = w * 2.1;
      ctx.beginPath();
      ctx.moveTo(bm.x, bm.y);
      ctx.lineTo(x2, y2);
      ctx.stroke();

      ctx.strokeStyle = COLORS.hazard;
      ctx.lineWidth = w;
      ctx.beginPath();
      ctx.moveTo(bm.x, bm.y);
      ctx.lineTo(x2, y2);
      ctx.stroke();

      ctx.strokeStyle = 'rgba(255,255,255,0.92)';
      ctx.lineWidth = Math.max(2, w * 0.28);
      ctx.beginPath();
      ctx.moveTo(bm.x, bm.y);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
  }
}

function drawBullets(ctx) {
  const list = Game.bullets;
  const spin = Game.frame * 0.05;
  for (let i = 0; i < list.length; i++) {
    const b = list[i];
    glowCircle(ctx, b.x, b.y, b.r * 1.2, COLORS.hazard, 2.4, 0.14);
    starPath(ctx, b.x, b.y, b.r * 1.5, 5, 0.46, spin);
    ctx.fillStyle = COLORS.hazard;
    ctx.fill();
    // 白色细描边：绿色弹幕压在红色玩家上时，抗锯齿会混出橙色。
    // 用 1px 灰阶描边把它们隔开，这是「不同色相不得直接相邻」的执行办法。
    ctx.strokeStyle = 'rgba(255,255,255,0.85)';
    ctx.lineWidth = 1.2;
    ctx.stroke();

    // 追踪弹多一圈旋转环，让玩家一眼分辨「这个会转弯」
    if (b.kind === 'homing') {
      ctx.strokeStyle = hexToRgba(COLORS.hazard, 0.9);
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.arc(b.x, b.y, b.r * 2.2, Game.frame * 0.18, Game.frame * 0.18 + 2.2);
      ctx.stroke();
    }

    ctx.beginPath();
    ctx.arc(b.x, b.y, b.r * 0.42, 0, TAU);
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
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

  // 球形态：球体由 Fx 负责（脉动 + 旋转弧 + 冲击波 + 粒子拖尾），
  // 不再画角色贴图——否则会看到「人形球」。
  const usingSprite = p.ball ? false : drawCharacterSprite(ctx, p);
  if (p.ball) {
    Fx.drawBall(ctx, p);
  } else if (!usingSprite) {
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

  // 受伤冲击环：用白（灰阶）而不是危险色。
  // 绿色是「会杀我的」的专属语义，套在玩家身上会让"我"和"威胁"混掉。
  if (p.hurtFlash > 0) {
    ctx.strokeStyle = 'rgba(255,255,255,' + (p.hurtFlash / 12).toFixed(3) + ')';
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
  Fx.drawBallParticles(ctx);
  for (let i = 0; i < Game.particles.length; i++) {
    const q = Game.particles[i];
    if (q.kind === 'fx') continue;   // 拖尾粒子已由 Fx 画过
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
    // 用黑色渐晕而不是红色：红色半透明叠在绿色弹幕上会混出橙色，
    // 那是第四种色相。黑色只压暗明度，不改变任何色相。
    const g = ctx.createRadialGradient(
      W / 2, H / 2, Math.min(W, H) * 0.22,
      W / 2, H / 2, Math.max(W, H) * 0.74
    );
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(1, 'rgba(0,0,0,' + (a * 0.72).toFixed(3) + ')');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
  }
}

// ------------------------------------------------------------- 走位段

// 空白世界：剧情醒来后用的场景，只有地面
function drawVoidBackground(ctx) {
  ctx.fillStyle = '#ececec';
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(0,0,0,0.06)';
  ctx.fillRect(0, GROUND_Y, W, H - GROUND_Y);
  ctx.fillStyle = 'rgba(0,0,0,0.20)';
  ctx.fillRect(0, GROUND_Y, W, 2);
}

function drawWalkNpc(ctx) {
  const w = Game.walk;
  if (!w) return;

  if (!w.target) {
    label(ctx, '→ 向前走', W - 40, H - 24, 16, 'rgba(255,255,255,0.42)', 'right', 400);
    return;
  }

  const x = w.target.x || 0;
  const y = GROUND_Y;
  const kind = w.target.kind || '';

  if (kind === 'mirror') {
    // 镜子占位：竖椭圆镜框 + 反光；等 art/obj/mirror.png 到位再换
    ctx.save();
    const mw = 74;
    const mh = 210;
    ctx.beginPath();
    ctx.ellipse(x, y - mh / 2 - 10, mw / 2, mh / 2, 0, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.10)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.65)';
    ctx.lineWidth = 3;
    ctx.stroke();
    // 镜面反光
    const g = ctx.createLinearGradient(x - mw / 2, y - mh - 10, x + mw / 2, y - 10);
    g.addColorStop(0, 'rgba(255,255,255,0.05)');
    g.addColorStop(0.5, 'rgba(255,255,255,0.22)');
    g.addColorStop(1, 'rgba(255,255,255,0.02)');
    ctx.beginPath();
    ctx.ellipse(x, y - mh / 2 - 10, mw / 2 - 4, mh / 2 - 4, 0, 0, Math.PI * 2);
    ctx.fillStyle = g;
    ctx.fill();
    ctx.restore();
    label(ctx, '镜子', x, y - mh - 26, 16, 'rgba(0,0,0,0.5)', 'center', 500);
  } else {
    // 诺登占位：亮红身体 + 两只长耳（等立绘/分件到位后替换）
    ctx.save();
    ctx.fillStyle = hexToRgba(COLORS.player, 0.9);
    ctx.fillRect(x - 20, y - 96, 40, 96);
    ctx.fillRect(x - 18, y - 158, 8, 62);
    ctx.fillRect(x + 10, y - 158, 8, 62);
    ctx.restore();
    label(ctx, '诺登', x, y - 176, 16, 'rgba(0,0,0,0.55)', 'center', 500);
  }

  const near = Game.player && Math.abs(Game.player.x - x) < 120;
  if (near) {
    label(ctx, '按 W 交互', x, y - 236, 18, '#111111', 'center', 700);
  } else {
    label(ctx, '→ 靠近它', W - 40, H - 24, 16, 'rgba(0,0,0,0.35)', 'right', 400);
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

  // 顶部压暗，保证血条/文字在亮背景上也读得清
  const scrim = ctx.createLinearGradient(0, 0, 0, 96);
  scrim.addColorStop(0, 'rgba(0,0,0,0.55)');
  scrim.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = scrim;
  ctx.fillRect(0, 0, W, 96);

  // ---------------- BOSS 血条（右上角） ----------------
  const def = bossDef(b);
  const phases = (def && def.phases) || PHASES;
  const hideTotal = !!(def && def.hideTotal);
  const bw = 380;
  const bx = W - 60 - bw;
  const by = 34;

  // 名字
  label(ctx, b.name || 'BOSS', W - 60, by - 12, 15, COLORS.ink, 'right', 700);

  // 条底 + 血：一根条 = 一个阶段，进新阶段自动补满再掉
  const top = phases[b.phase].at;
  const bot = (b.phase + 1 < phases.length) ? phases[b.phase + 1].at : 0;
  let seg = (b.hp / b.maxHp - bot) / Math.max(0.0001, top - bot);
  seg = Math.max(0, Math.min(1, seg));

  ctx.fillStyle = 'rgba(255,255,255,0.10)';
  ctx.fillRect(bx, by, bw, 8);
  bar(ctx, bx, by, bw, 8, seg, COLORS.hazard);

  // 阶段分隔小点（最终 BOSS 不显示总数，所以点也一起藏掉）
  if (!hideTotal) {
    for (let i = 0; i < phases.length; i++) {
      const px = W - 60 - (phases.length - 1 - i) * 12;
      ctx.fillStyle = i <= b.phase ? hexToRgba(COLORS.hazard, 0.9) : 'rgba(255,255,255,0.18)';
      ctx.fillRect(px - 4, by + 16, 6, 3);
    }
  }

  // 阶段文字
  const phaseLabel = hideTotal
    ? 'PHASE ' + (b.phase + 1)
    : 'PHASE ' + (b.phase + 1) + ' / ' + phases.length;
  mono(ctx, phaseLabel, W - 60, by + 38, 11, COLORS.dim, 'right');

  // 右侧小菱形（BOSS 标记）
  drawDiamond(ctx, W - 40, by + 4, 7, COLORS.hazard, true);

  // 生命
  for (let i = 0; i < P.lives; i++) {
    drawDiamond(ctx, 68 + i * 22, 38, 6, COLORS.player, i < Game.lives);
  }

  // 勇气
  bar(ctx, 60, 660, 240, 8, Game.courage / P.courageMax, COLORS.player);
  mono(ctx, '勇气 ' + Math.floor(Game.courage) + '%', 60, 654, 11, COLORS.dim);
  if (Game.courage >= P.courageMax) {
    const hasTragedy = Game.skills && Game.skills.red_tragedy;
    mono(ctx, hasTragedy ? 'L / X 红之惨剧' : 'L / X 释放冰封', 312, 668, 12,
         hasTragedy ? COLORS.player : COLORS.env);
  }

  // 擦弹连击：数字 + 剩余窗口
  const pl = Game.player;
  if (pl && pl.grazeChain > 0) {
    mono(ctx, '擦弹 x' + pl.grazeChain, 60, 638, 12, COLORS.player);
    bar(ctx, 130, 628, 120, 5, pl.grazeTimer / P.grazeChainWindow, COLORS.player);
  }

  // 状态提示（右下）
  mono(ctx, '空中 按住↑ + 冲刺 变球 · 松开冲刺变回', W - 60, 668, 11, COLORS.dim, 'right');

  // 调试：真实输入延迟（按键到画面提交的平均值）
  if (Game.debug.hitbox && Game.debug.latencyMs > 0) {
    mono(ctx, '输入延迟 ' + Game.debug.latencyMs.toFixed(1) + ' ms', W - 60, 692, 11, COLORS.dim, 'right');
    mono(ctx, Math.round(1000 / Math.max(1, Game.debug.frameMs || 16.7)) + ' fps', W - 170, 692, 11, COLORS.dim, 'right');
  }
}

// 取当前 BOSS 的配置（BOSSES 表），取不到就用 CFG.boss
function bossDef(b) {
  if (!b || typeof BOSSES === 'undefined') return null;
  return BOSSES[b.id] || null;
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
  ctx.fillStyle = 'rgba(0,0,0,' + alpha + ')';
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
      ['冲刺', 'Shift 或 K'],
      ['球形态（无敌）', '空中 按住↑ + 冲刺'],
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
