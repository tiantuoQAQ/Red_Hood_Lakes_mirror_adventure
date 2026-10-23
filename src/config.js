'use strict';

// ---- 舞台与全局常量 ------------------------------------------------------
const W = 1280;
const H = 720;
const GROUND_Y = 612;
const STEP = 1 / 60;

const ARENA = { left: 48, right: 1232, top: 48, bottom: GROUND_Y };
const MIRROR_X = W / 2; // 镜面轴：所有镜像弹幕以此为对称轴

// ---- 三色相 + 灰阶（唯一允许的调色板）-----------------------------------
// #FF0000  hue ≈ 0°      我方：蕾克、射击、擦弹、勇气
// #82FF00  hue ≈ 89.4°   危险：弹幕、致命机关
// #00BAFF  hue ≈ 196.2°  环境与中立：镜面、冰、湖
// 灰阶必须是**中性灰**（R=G=B）。偏蓝/偏暖的深灰会带上色相，
// 按「不多于 3 个色相」规则会被判成第四色相——#222d39 的色相是 211°，就是踩线。
const COLORS = {
  player: '#ff0000',
  hazard: '#82ff00',
  env: '#00baff',
  ink: '#ececec',
  dim: '#757575',
  bg0: '#0b0b0b',
  bg1: '#141414',
  bg2: '#222222',
  bg3: '#2f2f2f'
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
    grazeChainWindow: 80,     // 两次擦弹间隔超过这么多帧，连击归零
    grazeChainCourageStep: 5, // 每 N 次连续擦弹提升一档倍率
    grazeChainMaxMult: 3,     // 勇气倍率上限
    grazeDashRefund: 2,       // 每次擦弹返还的冲刺冷却帧数
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
