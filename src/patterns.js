'use strict';

// 弹幕发射器。每个招式只负责「在时刻 t 生成哪些子弹」，不持有状态。

function spawnBullet(list, x, y, angle, speed, r, kind) {
  const s = speed * CFG.bullets.speedScale;
  list.push({
    x: x,
    y: y,
    vx: Math.cos(angle) * s,
    vy: Math.sin(angle) * s,
    r: r || CFG.bullets.r,
    kind: kind || 'hazard',
    grazed: false,
    life: 420
  });
}

function aimAngle(fromX, fromY, toX, toY) {
  return Math.atan2(toY - fromY, toX - fromX);
}

// 镜像位置：以 MIRROR_X 为轴
function mirrorX(x) {
  return MIRROR_X * 2 - x;
}

const PATTERNS = {
  // 环形弹幕：每 30 帧一圈，角度逐圈偏移，形成旋转错位
  ring: {
    dur: 240,
    fire: function (G, boss, t) {
      const step = 30;
      if (t % step !== 0) return;
      const k = t / step;
      const n = CFG.bullets.ringN;
      const offset = k * (Math.PI * 2 / n) * 0.5;
      for (let i = 0; i < n; i++) {
        const a = offset + (i * Math.PI * 2) / n;
        spawnBullet(G.bullets, boss.x, boss.y, a, CFG.bullets.ringSpeed);
      }
    }
  },

  // 镜像扇形：BOSS 与它的镜像同时打出对称的瞄准扇形
  mirrorFan: {
    dur: 240,
    fire: function (G, boss, t) {
      const step = 40;
      if (t % step !== 0) return;
      const p = G.player;
      const base = aimAngle(boss.x, boss.y, p.x, p.y);
      const spread = 0.30;
      const n = 5;
      const mx = mirrorX(boss.x);
      for (let i = 0; i < n; i++) {
        const a = base + (i - (n - 1) / 2) * spread;
        spawnBullet(G.bullets, boss.x, boss.y, a, CFG.bullets.fanSpeed);
        // 镜像方向 = 绕竖直轴翻转
        spawnBullet(G.bullets, mx, boss.y, Math.PI - a, CFG.bullets.fanSpeed);
      }
    }
  },

  // 螺旋：BOSS 与镜像反向旋转，画出对称的旋臂
  spiral: {
    dur: 260,
    fire: function (G, boss, t) {
      const step = 7;
      if (t % step !== 0) return;
      const a = t * 0.19;
      spawnBullet(G.bullets, boss.x, boss.y, a, CFG.bullets.spiralSpeed);
      spawnBullet(G.bullets, mirrorX(boss.x), boss.y, Math.PI - a, CFG.bullets.spiralSpeed);
    }
  },

  // 自上而下的弹雨，落点在玩家附近随机偏移，逼玩家横向移动
  rain: {
    dur: 240,
    fire: function (G, boss, t) {
      const step = 9;
      if (t % step !== 0) return;
      const p = G.player;
      const bias = (Math.random() - 0.5) * 420;
      const x = Math.max(ARENA.left + 20, Math.min(ARENA.right - 20, p.x + bias));
      spawnBullet(G.bullets, x, ARENA.top - 12, Math.PI / 2, CFG.bullets.rainSpeed);
    }
  }
};
