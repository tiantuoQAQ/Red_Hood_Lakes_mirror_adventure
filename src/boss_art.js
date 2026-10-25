'use strict';

// Boss 战斗美术系统：立绘 + 法环动画

const BossArt = (function () {
  const cache = Object.create(null);

  // 加载单个 Boss 的所有资源（立绘 + 法环）
  function load(bossId) {
    if (cache[bossId]) return cache[bossId];

    const entry = {
      id: bossId,
      portraits: {},     // 姿态立绘
      ring: [],          // 法环帧序列
      loaded: 0,
      need: 0,
      ringFrame: 0,      // 当前法环帧索引
      ringTime: 0        // 法环动画计时（20fps）
    };
    cache[bossId] = entry;

    // 根据 Boss ID 确定资源路径和姿态映射
    if (bossId === 'crimson') {
      // 猩红魔姬：4 种姿态
      const poses = {
        idle: 'art/battle/scarlet/scarlet-action-red-eyes-02-cutout.png',
        dive: 'art/battle/scarlet/scarlet-action-red-eyes-01-cutout.png',
        slash: 'art/battle/scarlet/scarlet-action-red-eyes-03-cutout.png',
        thrust: 'art/battle/scarlet/scarlet-action-red-eyes-04-cutout.png'
      };
      entry.need += Object.keys(poses).length;
      for (const key in poses) {
        const img = new Image();
        img.onload = () => entry.loaded++;
        img.onerror = () => entry.loaded++;
        img.src = poses[key];
        entry.portraits[key] = img;
      }
      // 法环：40 帧
      entry.need += 40;
      for (let i = 0; i < 40; i++) {
        const img = new Image();
        img.onload = () => entry.loaded++;
        img.onerror = () => entry.loaded++;
        img.src = `art/battle/scarlet/ring/frame_${String(i).padStart(2, '0')}.png`;
        entry.ring.push(img);
      }
    } else if (bossId === 'marysue') {
      // 玛丽苏：3 种姿态
      const poses = {
        idle: 'art/battle/marysue/marysue-battle-01.png',
        charge: 'art/battle/marysue/marysue-battle-02.png',
        burst: 'art/battle/marysue/marysue-battle-03.png'
      };
      entry.need += Object.keys(poses).length;
      for (const key in poses) {
        const img = new Image();
        img.onload = () => entry.loaded++;
        img.onerror = () => entry.loaded++;
        img.src = poses[key];
        entry.portraits[key] = img;
      }
      // 法环：40 帧
      entry.need += 40;
      for (let i = 0; i < 40; i++) {
        const img = new Image();
        img.onload = () => entry.loaded++;
        img.onerror = () => entry.loaded++;
        img.src = `art/battle/marysue/ring/frame_${String(i).padStart(2, '0')}.png`;
        entry.ring.push(img);
      }
    }

    return entry;
  }

  function ready(bossId) {
    const e = cache[bossId];
    if (!e) return false;
    return e.loaded >= e.need;
  }

  // 更新法环动画（20fps = 每 3 帧更新一次）
  function updateRing(bossId) {
    const e = cache[bossId];
    if (!e || e.ring.length === 0) return;
    e.ringTime++;
    if (e.ringTime >= 3) {  // 60fps / 3 = 20fps
      e.ringTime = 0;
      e.ringFrame = (e.ringFrame + 1) % e.ring.length;
    }
  }

  // 获取当前应该显示的姿态
  function getPose(bossId, state) {
    const e = cache[bossId];
    if (!e || !ready(bossId)) return null;

    if (bossId === 'crimson') {
      // 猩红魔姬状态映射
      if (state === 'slash') return e.portraits.slash;
      if (state === 'thrust') return e.portraits.thrust;
      if (state === 'dive') return e.portraits.dive;
      return e.portraits.idle;
    } else if (bossId === 'marysue') {
      // 玛丽苏状态映射
      if (state === 'burst') return e.portraits.burst;
      if (state === 'charge') return e.portraits.charge;
      return e.portraits.idle;
    }
    return null;
  }

  // 获取当前法环帧
  function getRingFrame(bossId) {
    const e = cache[bossId];
    if (!e || e.ring.length === 0) return null;
    const img = e.ring[e.ringFrame];
    return (img && img.complete && img.naturalWidth > 0) ? img : null;
  }

  // 计算立绘可见高度（基于 alpha 边界）
  function measureHeight(img) {
    if (!img || !img.complete || !img.naturalWidth) return 0;
    // 简化：直接使用图片高度（精确测量需要读像素，这里用整图高度作为基准）
    return img.naturalHeight;
  }

  return {
    load: load,
    ready: ready,
    updateRing: updateRing,
    getPose: getPose,
    getRingFrame: getRingFrame,
    measureHeight: measureHeight,
    cache: cache
  };
})();
