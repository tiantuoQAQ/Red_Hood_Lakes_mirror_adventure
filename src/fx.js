'use strict';

// 光球形态的表现层：脉动球体 + 粒子拖尾。
//
// 贴图契约：art/fx/particle_strip.png
//   - 8 帧横排，每帧 256×256，透明背景
//   - 只允许红 #FF0000 + 中性白/灰（由 tools/_fix_fx_palette.py 保证）
//   - 缺图不会崩：自动退回程序化小圆点
//
// 注意：这里只负责「画」。粒子的生成与推进在 game.js（逻辑层），
// 这样 node 端的逻辑测试不需要 canvas 也能跑。

const FX_TAU = Math.PI * 2;

const Fx = (function () {
  const tex = new Image();
  let texOk = false;
  const FRAMES = 8;
  const CELL = 256;

  tex.onload = function () { texOk = (tex.naturalWidth >= CELL * FRAMES); };
  tex.onerror = function () { texOk = false; };
  tex.src = 'art/fx/particle_strip.png';

  function ready() { return texOk; }

  // ---- 球体本身 ----
  function drawBall(ctx, p) {
    const R = CFG.player.visualR;
    const t = Game.frame;
    const pulse = 1 + Math.sin(t * 0.22) * 0.07;
    const r = R * 1.18 * pulse;

    // 外层光晕：白 → 红 → 透明。
    // 中心用纯白（灰阶）而不是浅红，叠加时不会混出新色相。
    const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, r * 2.6);
    g.addColorStop(0.00, 'rgba(255,255,255,0.95)');
    g.addColorStop(0.30, hexToRgba(COLORS.player, 0.55));
    g.addColorStop(0.58, hexToRgba(COLORS.player, 0.20));
    g.addColorStop(1.00, 'rgba(255,0,0,0)');
    ctx.beginPath();
    ctx.arc(p.x, p.y, r * 2.6, 0, FX_TAU);
    ctx.fillStyle = g;
    ctx.fill();

    // 旋转弧：用青（环境色）区分「形态」和「伤害」，三色之内
    ctx.strokeStyle = hexToRgba(COLORS.env, 0.7);
    ctx.lineWidth = 2;
    for (let k = 0; k < 3; k++) {
      const a0 = t * 0.12 + (k * FX_TAU) / 3;
      ctx.beginPath();
      ctx.arc(p.x, p.y, r * 1.32, a0, a0 + 0.85);
      ctx.stroke();
    }

    // 内核
    ctx.beginPath();
    ctx.arc(p.x, p.y, r * 0.5, 0, FX_TAU);
    ctx.fillStyle = 'rgba(255,255,255,0.92)';
    ctx.fill();

    // 冲击波：每 26 帧向外扩一圈，读完即消失
    const ph = (t % 26) / 26;
    ctx.beginPath();
    ctx.arc(p.x, p.y, r * (1.2 + ph * 1.9), 0, FX_TAU);
    ctx.strokeStyle = 'rgba(255,255,255,' + (0.42 * (1 - ph)).toFixed(3) + ')';
    ctx.lineWidth = 2.5 * (1 - ph) + 0.5;
    ctx.stroke();
  }

  // ---- 粒子拖尾 ----
  // 粒子数据在 Game.particles 里，kind === 'fx' 的由这里画。
  function drawBallParticles(ctx) {
    const list = Game.particles;
    for (let i = 0; i < list.length; i++) {
      const q = list[i];
      if (q.kind !== 'fx') continue;

      const k = 1 - q.life / q.max;          // 0 → 1 存活进度
      const alpha = Math.min(1, Math.pow(1 - k, 0.75) * 1.15);   // 先亮后淡，拖尾才连得上
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';   // 叠加发光，不会混出新色相
      ctx.globalAlpha = alpha;
      ctx.translate(q.x, q.y);
      ctx.rotate(q.rot);

      if (ready()) {
        const f = Math.min(FRAMES - 1, Math.floor(k * FRAMES));
        const s = q.size * (0.7 + k * 0.8);  // 存活期间略微放大
        ctx.drawImage(tex, f * CELL, 0, CELL, CELL, -s / 2, -s / 2, s, s);
      } else {
        ctx.beginPath();
        ctx.arc(0, 0, 2.6 * (1 - k), 0, FX_TAU);
        ctx.fillStyle = hexToRgba(COLORS.player, 1 - k);
        ctx.fill();
      }
      ctx.restore();
    }
  }

  return { ready: ready, drawBall: drawBall, drawBallParticles: drawBallParticles, FRAMES: FRAMES };
})();
