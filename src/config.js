'use strict';

// ---- 舞台与全局常量 ------------------------------------------------------
const W = 1280;
const H = 720;
const GROUND_Y = 612;
const STEP = 1 / 60;

const ARENA = { left: 48, right: 1232, top: 48, bottom: GROUND_Y };
const MIRROR_X = W / 2; // 镜面轴：所有镜像弹幕以此为对称轴

// ---- 三色相 + 灰阶（唯一允许的调色板）-----------------------------------
// 冰 / 青   hue ≈ 195
// 危险 / 品红 hue ≈ 330
// 自身 / 暖橙 hue ≈ 33
// 其余全部为无饱和度灰阶
const COLORS = {
  ice: '#5fd8ff',
  hazard: '#ff3fa4',
  self: '#ffa53f',
  ink: '#e8eef6',
  dim: '#6f7d90',
  bg0: '#0b0e13',
  bg1: '#141a23',
  bg2: '#222d39',
  bg3: '#2f3d4c'
};

// ---- 可调参数（F2 面板实时修改）----------------------------------------
const CFG = {
  player: {
    speed: 340,          // px/s
    accel: 4600,         // px/s^2
    friction: 3800,      // px/s^2
    jumpVel: -700,       // px/s
    gravity: 2000,       // px/s^2
    visualR: 20,         // 视觉半径
    hitR: 4,             // 判定半径（必须远小于视觉半径）
    dashSpeed: 1020,
    dashFrames: 12,
    dashIFrames: 16,
    dashCd: 16,
    ballSpeed: 450,
    ballHoldFrames: 10,  // 空中长按冲刺多少帧后变成球
    ballLaunchFrames: 5, // 进入球形态后强制上冲的帧数
    ballDrain: 32,       // 体力/秒
    ballRegen: 26,       // 落地回复/秒
    ballMinStamina: 20,  // 进入球形态所需最低体力
    hurtIFrames: 70,
    knockback: 430,
    lives: 3,
    fireInterval: 9,
    shotSpeed: 900,
    shotDamage: 3,
    shotRadius: 5,
    grazeR: 30,
    courageMax: 100,
    couragePerHit: 2,
    couragePerGraze: 1,
    courageLoss: 18
  },
  boss: {
    hp: 420,
    x: 980,
    y: 226,
    r: 44,
    bobAmp: 46,
    bobSpeed: 0.85
  },
  bullets: {
    speedScale: 1,
    r: 7,
    ringN: 18,
    ringSpeed: 215,
    fanSpeed: 300,
    spiralSpeed: 250,
    rainSpeed: 300
  },
  skill: { damage: 36, invFrames: 130 }
};

// 阶段剧本：每个阶段按顺序循环执行这些弹幕招式
const PHASES = [
  { at: 1.0, script: ['ring', 'mirrorFan' ] },
  { at: 0.66, script: ['mirrorFan', 'spiral', 'ring'] },
  { at: 0.33, script: ['spiral', 'rain', 'mirrorFan', 'ring'] }
];
