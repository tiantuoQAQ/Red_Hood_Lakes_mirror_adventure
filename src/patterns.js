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
      spawnBullet(G.bullets, x, ARENA.top - 12, Math.PI / 2, CFG.bullets.rainSpeed, CFG.bullets.r, 'rain');
    }
  },

  // 预警穿刺：先画 30 帧预警线，再沿该线打出高速弹。
  // 这是唯一「有明确前摇」的招式，用来教玩家读预警。
  lances: {
    dur: 270,
    fire: function (G, boss, t) {
      const cycle = 96;
      const ph = t % cycle;

      if (ph === 0) {
        const p = G.player;
        const base = aimAngle(boss.x, boss.y, p.x, p.y);
        const offs = [-0.20, 0, 0.20];
        boss.pending = [];
        for (let i = 0; i < offs.length; i++) {
          const a = base + offs[i];
          const m = Math.PI - a;
          G.warnings.push({ x: boss.x, y: boss.y, a: a, life: 30, max: 30, len: 1600 });
          G.warnings.push({ x: mirrorX(boss.x), y: boss.y, a: m, life: 30, max: 30, len: 1600 });
          boss.pending.push({ x: boss.x, y: boss.y, a: a });
          boss.pending.push({ x: mirrorX(boss.x), y: boss.y, a: m });
        }
        Sfx.warn();
      }

      if (ph === 30 && boss.pending) {
        for (let i = 0; i < boss.pending.length; i++) {
          const s = boss.pending[i];
          spawnBullet(G.bullets, s.x, s.y, s.a, 640, CFG.bullets.r * 0.85, 'lance');
        }
        boss.pending = null;
        Sfx.lance();
      }
    }
  },

  // 双旋臂：两条缓慢旋转的弹链，形成会压过来的「墙」
  orbit: {
    dur: 280,
    fire: function (G, boss, t) {
      const step = 4;
      if (t % step !== 0) return;
      const a = t * 0.055;
      spawnBullet(G.bullets, boss.x, boss.y, a, 190, CFG.bullets.r);
      spawnBullet(G.bullets, mirrorX(boss.x), boss.y, Math.PI - a, 190, CFG.bullets.r);
    }
  },

  // 四角汇聚：从场地四角向中心偏斜射出，制造夹击感
  crossfire: {
    dur: 260,
    fire: function (G, boss, t) {
      const cycle = 84;
      if (t % cycle !== 0) return;
      const targetX = MIRROR_X + (Math.random() - 0.5) * 240;
      const targetY = 320 + (Math.random() - 0.5) * 180;
      const corners = [
        [ARENA.left + 24, ARENA.top + 24],
        [ARENA.right - 24, ARENA.top + 24],
        [ARENA.left + 24, GROUND_Y - 24],
        [ARENA.right - 24, GROUND_Y - 24]
      ];
      for (let i = 0; i < corners.length; i++) {
        const c = corners[i];
        const a = aimAngle(c[0], c[1], targetX, targetY) + (Math.random() - 0.5) * 0.22;
        spawnBullet(G.bullets, c[0], c[1], a, 320, CFG.bullets.r);
      }
    }
  },

  // 激光：蓄力 45 帧（细线预警），然后实体光束 34 帧。成对镜像。
  laser: {
    dur: 300,
    fire: function (G, boss, t) {
      const cycle = 140;
      const ph = t % cycle;
      const B = CFG.beam;
      if (ph === 0) {
        const p = G.player;
        const base = aimAngle(boss.x, boss.y, p.x, p.y);
        G.beams.push({
          x: boss.x, y: boss.y, a: base, hit: false,
          warmup: B.warmup, max: B.warmup + B.active, life: B.warmup + B.active
        });
        G.beams.push({
          x: mirrorX(boss.x), y: boss.y, a: Math.PI - base, hit: false,
          warmup: B.warmup, max: B.warmup + B.active, life: B.warmup + B.active
        });
        Sfx.warn();
      }
      if (ph === B.warmup) {
        Sfx.lance();
        Game.shake = Math.max(Game.shake, 5);
      }
    }
  },

  // BOSS 冲刺：位移到玩家上方再打一圈，逼玩家换位置
  bossDash: {
    dur: 220,
    fire: function (G, boss, t) {
      const cycle = 110;
      if (t % cycle !== 0) return;
      if (boss.dashT > 0) return;
      const p = G.player;
      boss.dashTo = {
        x: Math.max(ARENA.left + 140, Math.min(ARENA.right - 140, p.x)),
        y: Math.max(ARENA.top + 120, Math.min(GROUND_Y - 220, p.y - 190))
      };
      boss.dashT = CFG.bossDash.frames;
      Sfx.warn();
    }
  },

  // 追踪弹：慢速但会转向，靠横移可以绕开
  homing: {
    dur: 280,
    fire: function (G, boss, t) {
      if (t % 44 !== 0) return;
      const p = G.player;
      const a1 = aimAngle(boss.x, boss.y, p.x, p.y);
      const a2 = aimAngle(mirrorX(boss.x), boss.y, p.x, p.y);
      spawnBullet(G.bullets, boss.x, boss.y, a1, CFG.bullets.homingSpeed, CFG.bullets.r * 1.1, 'homing');
      spawnBullet(G.bullets, mirrorX(boss.x), boss.y, a2, CFG.bullets.homingSpeed, CFG.bullets.r * 1.1, 'homing');
    }
  }
};
