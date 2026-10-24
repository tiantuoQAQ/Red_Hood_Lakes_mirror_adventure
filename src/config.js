'use strict';

// ---- 舞台与全局常量 ------------------------------------------------------
const W = 1280;
const H = 720;
const GROUND_Y = 574;   // 地面线：不要贴屏幕底端，下方留出一段给倒影/UI
const STEP = 1 / 60;

// 世界比屏幕宽：镜头跟随玩家横向滚动
const WORLD_W = 2400;
const ARENA = { left: 48, right: WORLD_W - 48, top: 48, bottom: GROUND_Y };
const MIRROR_X = WORLD_W / 2; // 镜面轴：所有镜像弹幕以此为对称轴

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
    dashRampFrames: 3,     // 起步加速帧数：0 = 瞬间满速（手感硬、但会有"啪"的突变）
    dashOutFrames: 6,      // 冲刺结束后的滑行帧数
    dashOutKeep: 0.72,     // 滑行阶段每帧保留的速度比例
    inputBuffer: 8,        // 提前按键的缓存帧数
    ballSpeed: 450,
    ballLaunchFrames: 5, // 进入球形态后强制上冲的帧数
    ballExitOnLand: false, // 落地是否退出球形态（当前设计：不退出，松开冲刺才退出）
    ballDrain: 32,       // 体力/秒
    ballRegen: 26,       // 落地回复/秒
    ballMinStamina: 20,  // 进入球形态所需最低体力
    hurtIFrames: 70,
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
    x: WORLD_W - 320,
    y: 226,
    r: 44,
    bobAmp: 46,
    bobSpeed: 0.85
  },
  bullets: {
    speedScale: 1,
    homingSpeed: 215,
    homingTurn: 1.7,        // 追踪弹每秒最大转向（弧度）
    r: 7,
    ringN: 18,
    ringSpeed: 215,
    fanSpeed: 300,
    spiralSpeed: 250,
    rainSpeed: 300
  },
  // 角色贴图：分件动画（cape/hair/body/head 四层）。四张图必须同尺寸同站位。
  // headDx/headDy 是「对齐微调」，即梦出的分件对不齐时在这里拖到对齐。
  sprite: {
    id: 'rek',
    dir: 'art/rek',
    scale: 0.5,       // 按 2 倍出图，这里缩一半
    hairDx: 0,
    hairDy: 0,
    capeDx: 0,
    capeDy: 0,
    headDx: 0,
    headDy: 0
  },
  beam: { width: 26, warmup: 45, active: 34, len: 1700 },
  bossDash: { speed: 1500, frames: 18 },
  skill: { damage: 36, invFrames: 130 }
};

// 阶段剧本：每个阶段按顺序循环执行这些弹幕招式
// P1 教学：只有能看懂的两招
// P2 加压：加入预警穿刺（lances），开始考验反应
// P3 满配：穿刺 + 旋臂 + 四角汇聚
const PHASES = [
  { at: 1.0, script: ['ring', 'mirrorFan'] },
  { at: 0.66, script: ['mirrorFan', 'lances', 'laser'] },
  { at: 0.33, script: ['laser', 'homing', 'bossDash', 'orbit'] }
];

// ---- BOSS 表（剧情两场）--------------------------------------------------
// 同一个状态机，靠这张表区分「中段魔姬」和「最终玛丽苏」。
// 每个 BOSS 自带阶段表：at 是血量比例阈值，script 是该阶段的招式循环。
const BOSSES = {
  crimson: {
    name: '自负的暴君 猩红魔姬·雷帝',
    portrait: 'art/portrait/crimson_stand.png',
    barColor: '#FF0000',
    hp: 240,
    phases: [
      { at: 1.0, script: ['ring'],                                     name: '壹 · 试锋',       skill: '浅露' },
      { at: 0.8, script: ['ring', 'mirrorFan'],                        name: '贰 · 裂帛',       skill: '剑气' },
      { at: 0.6, script: ['mirrorFan', 'lances'],                      name: '叁 · 血雨',       skill: '连斩' },
      { at: 0.4, script: ['lances', 'laser'],                          name: '肆 · 镜刃',       skill: '突刺' },
      { at: 0.2, script: ['laser', 'homing', 'bossDash'],              name: '伍 · 红之惨剧',   skill: '断罪' }
    ]
  },
  marysue: {
    name: '扭曲的黑童话作家 玛丽苏',
    portrait: 'art/portrait/marysue.png',
    barColor: '#82FF00',
    hp: 420,
    hideTotal: true,        // 不告诉玩家一共几阶段
    phases: [
      { at: 1.0,   script: ['ring'],                                    name: '壹 · 箱庭',       skill: '开门' },
      { at: 5 / 6, script: ['ring', 'mirrorFan'],                       name: '贰 · 反语',       skill: '假笑' },
      { at: 4 / 6, script: ['mirrorFan', 'lances'],                     name: '叁 · 镜廊',       skill: '复写' },
      { at: 3 / 6, script: ['lances', 'laser'],                         name: '肆 · 断线',       skill: '操偶' },
      { at: 2 / 6, script: ['laser', 'homing', 'orbit'],                name: '伍 · 狂言',       skill: '终幕将至' },
      { at: 1 / 6, script: ['bossDash', 'lances', 'laser', 'orbit'],    name: '陆 · 天地倒悬',   skill: '镜界颠倒' }
    ]
  }
};

