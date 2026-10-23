'use strict';

// 逻辑层回归测试（不需要浏览器）：加载游戏脚本，模拟按键逐帧推进，断言核心手感机制。
// 运行： node test/logic_test.js

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const files = [
  'src/config.js',
  'src/input.js',
  'src/gfx.js',
  'src/patterns.js',
  'src/audio.js',
  'src/game.js'
];

// 最小 window 桩：把事件处理器收集到 node 侧，方便模拟按键
const handlers = { keydown: [], keyup: [], blur: [] };
globalThis.window = {
  addEventListener: function (type, fn) {
    if (!handlers[type]) handlers[type] = [];
    handlers[type].push(fn);
  }
};

function keydown(code) {
  handlers.keydown.forEach(function (fn) {
    fn({ code: code, repeat: false, preventDefault: function () {} });
  });
}
function keyup(code) {
  handlers.keyup.forEach(function (fn) { fn({ code: code }); });
}
function releaseAll() {
  ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'ShiftLeft', 'Space', 'KeyJ', 'KeyL']
    .forEach(keyup);
}
function mousedown(button) {
  (handlers.mousedown || []).forEach(function (fn) { fn({ button: button }); });
}
function mouseup(button) {
  (handlers.mouseup || []).forEach(function (fn) { fn({ button: button }); });
}

const harness = `
globalThis.__run = function (keydown, keyup, releaseAll, mousedown, mouseup) {
  const out = {};

  // 推进一帧：update 之后必须 tick，否则「本帧按下」的判定窗口永远不关闭，
  // 上一个用例按下的键会污染下一个用例。
  const step = function () { update(STEP); Input.tick(); };

  // 1. 冲刺必须给出无敌帧
  resetGame();
  keydown('ShiftLeft');
  step();
  out.dashIframes = Game.player.invT;
  out.dashIframesExpected = CFG.player.dashIFrames;
  out.dashActive = Game.player.dashT > 0;
  releaseAll();

  // 球形态：必须在空中长按冲刺才进入，按一下不够
  resetGame();
  const startY = Game.player.y;
  keydown('Space');
  step();
  keyup('Space');
  for (let i = 0; i < 6; i++) step();
  out.wasAirborne = Game.player.onGround === false;

  keydown('ShiftLeft');
  step();
  out.ballNotImmediate = Game.player.ball === false;   // 按一下不应该立刻变球
  out.airDashFired = Game.player.dashT > 0;            // 但空中按下仍然会先冲刺

  let ballFrame = -1;
  for (let i = 0; i < 40; i++) {
    step();
    if (Game.player.ball) { ballFrame = i + 1; break; }
  }
  out.ballEnteredByHold = ballFrame >= 0;
  out.ballHoldFrames = ballFrame;
  out.ballHoldExpected = CFG.player.ballHoldFrames;
  out.ballRose = Game.player.y < startY - 20;
  out.ballStillActive = Game.player.ball === true;

  // 球形态免疫伤害
  Game.bullets.push({
    x: Game.player.x, y: Game.player.y, vx: 0, vy: 0,
    r: CFG.bullets.r, kind: 'hazard', grazed: true, life: 60
  });
  const livesInBall = Game.lives;
  step();
  out.ballImmuneToDamage = Game.lives === livesInBall;

  // 球形态：向下飞，落地必须自动取消（核心设计），且不是瞬间取消
  keyup('ArrowUp');
  keydown('ArrowDown');
  let groundFrame = -1;
  for (let i = 0; i < 180; i++) {
    step();
    if (!Game.player.ball) { groundFrame = i; break; }
  }
  out.ballExitByGround = groundFrame >= 3;
  out.ballExitFrame = groundFrame;
  out.ballGrounded = Math.abs(Game.player.y + CFG.player.visualR - GROUND_Y) < 1.5;
  releaseAll();

  // 点按冲刺只冲刺，不变成球
  resetGame();
  keydown('ShiftLeft');
  step();
  const tapDashed = Game.player.dashT > 0;
  keyup('ShiftLeft');
  for (let i = 0; i < 30; i++) step();
  out.tapDashOnly = tapDashed && Game.player.ball === false;

  // 地面上长按冲刺也能变成球（体力是唯一的成本）
  resetGame();
  keydown('ShiftLeft');
  let groundBall = -1;
  for (let i = 0; i < 40; i++) {
    step();
    if (Game.player.ball) { groundBall = i + 1; break; }
  }
  out.ballFromGround = groundBall >= 0;
  out.ballFromGroundFrame = groundBall;

  // 落地取消后若仍按住冲刺，不应立刻又变成球（必须松开再按）
  keydown('ArrowDown');
  let firstExit = -1;
  for (let i = 0; i < 220; i++) {
    step();
    if (!Game.player.ball) { firstExit = i; break; }
  }
  let reentered = false;
  for (let i = 0; i < 30; i++) {
    step();
    if (Game.player.ball) { reentered = true; break; }
  }
  out.noInstaReenter = firstExit >= 0 && reentered === false;
  keyup('ArrowDown');
  keyup('ShiftLeft');
  step();

  // 松开后重新长按，应该又能成球
  keydown('ShiftLeft');
  let reBall = -1;
  for (let i = 0; i < 40; i++) {
    step();
    if (Game.player.ball) { reBall = i + 1; break; }
  }
  out.reenterAfterRelease = reBall >= 0;
  releaseAll();

  // 球形态：体力耗尽也必须退出
  resetGame();
  keydown('Space');
  step();
  keyup('Space');
  for (let i = 0; i < 6; i++) step();
  keydown('ShiftLeft');
  let gotBall = false;
  for (let i = 0; i < 40; i++) {
    step();
    if (Game.player.ball) { gotBall = true; break; }
  }
  keyup('ShiftLeft');
  let staminaFrame = -1;
  for (let i = 0; i < 600; i++) {
    step();
    if (!Game.player.ball) { staminaFrame = i; break; }
  }
  out.ballExitByStamina = gotBall && staminaFrame >= 0;
  out.ballStaminaFrames = staminaFrame;
  releaseAll();

  // 5. 判定点必须远小于视觉半径
  out.hitR = CFG.player.hitR;
  out.visualR = CFG.player.visualR;
  out.hitboxRatio = +(CFG.player.hitR / CFG.player.visualR).toFixed(3);

  // 6. 擦弹加勇气 / 中弹扣命扣勇气
  resetGame();
  Game.courage = 0;
  const p = Game.player;
  Game.bullets.push({
    x: p.x + CFG.player.grazeR - 2, y: p.y, vx: 0, vy: -300,
    r: CFG.bullets.r, kind: 'hazard', grazed: false, life: 40
  });
  step();
  out.grazeCourage = Game.courage;

  const livesBefore = Game.lives;
  Game.bullets.push({
    x: p.x, y: p.y, vx: 0, vy: 0,
    r: CFG.bullets.r, kind: 'hazard', grazed: true, life: 40
  });
  step();
  out.livesLost = livesBefore - Game.lives;
  out.invulnAfterHit = Game.player.invT;
  out.invulnExpected = CFG.player.hurtIFrames;

  // 7. 阶段推进：越过阈值后切阶段并清屏
  resetGame();
  for (let i = 0; i < 200; i++) update(STEP);
  out.bulletsBeforePhase = Game.bullets.length;
  Game.boss.hp = Game.boss.maxHp * 0.5;
  step();
  out.phaseAfterDrop = Game.boss.phase;
  out.bulletsClearedOnPhase = Game.bullets.length;

  // 8. 弹幕确实会生成，并且会飞出边界被回收
  resetGame();
  let peak = 0;
  for (let i = 0; i < 900; i++) {
    step();
    if (Game.bullets.length > peak) peak = Game.bullets.length;
  }
  out.peakBullets = peak;
  out.after900 = Game.bullets.length;

  // 9. 弹药上限保护：连打 900 帧不释放也不会无限增长
  out.peakUnder1000 = peak < 1000;

  // 10. 鼠标左键射击
  resetGame();
  mousedown(0);
  step();
  out.mouseFireShots = Game.shots.length;
  mouseup(0);

  // 11. 鼠标右键冲刺
  resetGame();
  mousedown(2);
  step();
  out.mouseDashIframes = Game.player.invT;
  out.mouseDashActive = Game.player.dashT > 0;
  mouseup(2);

  // 12. 鼠标不应影响移动
  resetGame();
  const xBefore = Game.player.x;
  mousedown(0);
  for (let i = 0; i < 20; i++) update(STEP);
  out.mouseNoMove = Math.abs(Game.player.x - xBefore) < 0.001;
  mouseup(0);

  return out;
};
`;

// runInThisContext 里的脚本看不到模块作用域，需要显式挂到全局
globalThis.__keydown = keydown;
globalThis.__keyup = keyup;
globalThis.__releaseAll = releaseAll;
globalThis.__mousedown = mousedown;
globalThis.__mouseup = mouseup;

const code = files
  .map(function (f) { return fs.readFileSync(path.join(root, f), 'utf8'); })
  .join('\n') + '\n' + harness +
  '\nglobalThis.__out = globalThis.__run(globalThis.__keydown, globalThis.__keyup, ' +
  'globalThis.__releaseAll, globalThis.__mousedown, globalThis.__mouseup);';

vm.runInThisContext(code, { filename: 'game-bundle.js' });

const out = globalThis.__out;

const checks = [
  ['冲刺给出无敌帧', out.dashIframes >= out.dashIframesExpected, out.dashIframes + ' 帧 / 期望 ≥ ' + out.dashIframesExpected],
  ['冲刺期间处于冲刺状态', out.dashActive === true, ''],
  ['点按冲刺只冲刺不变球', out.tapDashOnly === true, ''],
  ['长按冲刺变球（空中）', out.ballEnteredByHold && out.wasAirborne, '第 ' + out.ballHoldFrames + ' 帧成球'],
  ['长按冲刺变球（地面也算）', out.ballFromGround === true, '第 ' + out.ballFromGroundFrame + ' 帧成球'],
  ['落地取消后不会立刻再次成球', out.noInstaReenter === true, ''],
  ['松开再长按可以再次成球', out.reenterAfterRelease === true, ''],
  ['空中按冲刺仍会先触发冲刺', out.airDashFired === true, ''],
  ['球形态起手强制上冲', out.ballRose === true, ''],
  ['球形态不会立刻被地面取消', out.ballStillActive === true, ''],
  ['球形态免疫伤害', out.ballImmuneToDamage === true, ''],
  ['球形态落地自动取消（非瞬间）', out.ballExitByGround && out.ballGrounded, '第 ' + out.ballExitFrame + ' 帧落地'],
  ['球形态体力耗尽自动取消', out.ballExitByStamina && out.ballStaminaFrames > 0, '第 ' + out.ballStaminaFrames + ' 帧耗尽'],
  ['判定点远小于视觉半径', out.hitboxRatio <= 0.3, 'hitR=' + out.hitR + ' visualR=' + out.visualR + ' 比例=' + out.hitboxRatio],
  ['擦弹增加勇气', out.grazeCourage > 0, '勇气=' + out.grazeCourage],
  ['中弹扣一条命', out.livesLost === 1, ''],
  ['中弹后进入无敌', out.invulnAfterHit >= out.invulnExpected, out.invulnAfterHit + ' 帧 / 期望 ≥ ' + out.invulnExpected],
  ['弹幕会生成', out.bulletsBeforePhase > 0, '200 帧时场上 ' + out.bulletsBeforePhase + ' 颗'],
  ['血量过阈值切换阶段', out.phaseAfterDrop === 1, 'phase=' + out.phaseAfterDrop],
  ['换阶段清屏', out.bulletsClearedOnPhase === 0, ''],
  ['弹幕峰值可控', out.peakUnder1000, '峰值 ' + out.peakBullets + ' 颗，900 帧后剩 ' + out.after900 + ' 颗'],
  ['鼠标左键可射击', out.mouseFireShots > 0, '出膛 ' + out.mouseFireShots + ' 发'],
  ['鼠标右键可冲刺', out.mouseDashActive && out.mouseDashIframes >= out.dashIframesExpected, out.mouseDashIframes + ' 帧无敌'],
  ['鼠标不会让角色移动', out.mouseNoMove === true, '']
];

let failed = 0;
console.log('');
checks.forEach(function (c) {
  const mark = c[1] ? 'PASS' : 'FAIL';
  if (!c[1]) failed++;
  console.log(mark + '  ' + c[0] + (c[2] ? '   (' + c[2] + ')' : ''));
});
console.log('');
console.log(failed === 0 ? '全部 ' + checks.length + ' 项通过' : failed + ' 项失败');
process.exitCode = failed === 0 ? 0 : 1;
