'use strict';

// 镜之碎片特效：主题「镜」的视觉母题。
// 用法：MirrorFx.burst({ dur, count, power }) 触发；每帧 MirrorFx.update()；绘制 MirrorFx.draw(ctx)
const MirrorFx = (function () {
  const shards = [];
  const cracks = [];
  let life = 0;

  function rnd(a, b) {
    return a + Math.random() * (b - a);
  }

  function makeShard(cx, cy, power) {
    const a = Math.random() * Math.PI * 2;
    const r = rnd(40, 280) * power;
    const size = rnd(18, 64) * power;
    const n = 3 + Math.floor(Math.random() * 2);
    const pts = [];
    for (let i = 0; i < n; i++) {
      const ang = (i / n) * Math.PI * 2 + rnd(-0.3, 0.3);
      const rr = size * rnd(0.55, 1);
      pts.push({ x: Math.cos(ang) * rr, y: Math.sin(ang) * rr });
    }
    const sr = rnd(10, 90) * power;
    return {
      x: cx + Math.cos(a) * sr, y: cy + Math.sin(a) * sr,
      vx: Math.cos(a) * rnd(90, 260) * power,
      vy: Math.sin(a) * rnd(90, 260) * power - 40,
      rot: rnd(0, Math.PI * 2),
      vr: rnd(-3.2, 3.2),
      pts: pts,
      a: 1
    };
  }

  function start(opt) {
    const o = opt || {};
    const dur = o.dur || 90;
    const count = o.count || 26;
    const power = o.power || 1;
    life = Math.max(life, dur);

    cracks.length = 0;
    // 裂纹：从画面中心（或指定点）放射
    const cx = o.x != null ? o.x : 640;
    const cy = o.y != null ? o.y : 340;
    const rays = 9 + Math.floor(Math.random() * 4);
    for (let i = 0; i < rays; i++) {
      const a = (i / rays) * Math.PI * 2 + rnd(-0.2, 0.2);
      const len = rnd(180, 420) * power;
      const seg = [];
      let px = cx, py = cy;
      const steps = 4 + Math.floor(Math.random() * 3);
      for (let s = 1; s <= steps; s++) {
        px += Math.cos(a + rnd(-0.22, 0.22)) * (len / steps);
        py += Math.sin(a + rnd(-0.22, 0.22)) * (len / steps);
        seg.push({ x: px, y: py });
      }
      cracks.push({ start: { x: cx, y: cy }, pts: seg, a: 1 });
    }

    for (let i = 0; i < count; i++) {
      shards.push(makeShard(cx, cy, power));
    }
    if (shards.length > 160) shards.splice(0, shards.length - 160);
  }

  function update() {
    for (let i = shards.length - 1; i >= 0; i--) {
      const s = shards[i];
      s.x += s.vx * 0.016;
      s.y += s.vy * 0.016;
      s.vy += 260 * 0.016;      // 轻微下坠
      s.rot += s.vr * 0.016;
      s.a -= 0.012;
      if (s.a <= 0) shards.splice(i, 1);
    }
    for (let i = cracks.length - 1; i >= 0; i--) {
      cracks[i].a -= 0.02;
      if (cracks[i].a <= 0) cracks.splice(i, 1);
    }
    if (life > 0) life--;
  }

  function draw(ctx) {
    if (!shards.length && !cracks.length) return;
    ctx.save();

    // 裂纹：白色细线 + 外发光
    for (let i = 0; i < cracks.length; i++) {
      const c = cracks[i];
      ctx.globalAlpha = Math.max(0, c.a) * 0.9;
      ctx.strokeStyle = 'rgba(255,255,255,0.85)';
      ctx.lineWidth = 2;
      ctx.shadowColor = 'rgba(255,255,255,0.8)';
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.moveTo(c.start.x, c.start.y);
      for (let j = 0; j < c.pts.length; j++) ctx.lineTo(c.pts[j].x, c.pts[j].y);
      ctx.stroke();
    }
    ctx.shadowBlur = 0;

    // 碎片：半透明镜面
    for (let i = 0; i < shards.length; i++) {
      const s = shards[i];
      if (s.a <= 0) continue;
      ctx.save();
      ctx.globalAlpha = Math.max(0, s.a);
      ctx.translate(s.x, s.y);
      ctx.rotate(s.rot);
      ctx.beginPath();
      ctx.moveTo(s.pts[0].x, s.pts[0].y);
      for (let j = 1; j < s.pts.length; j++) ctx.lineTo(s.pts[j].x, s.pts[j].y);
      ctx.closePath();
      ctx.fillStyle = 'rgba(220,235,245,0.16)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.75)';
      ctx.lineWidth = 1.4;
      ctx.stroke();
      ctx.restore();
    }

    ctx.restore();
  }

  function reset() {
    shards.length = 0;
    cracks.length = 0;
    life = 0;
  }

  return { start: start, update: update, draw: draw, reset: reset, count: function () { return shards.length; } };
})();
