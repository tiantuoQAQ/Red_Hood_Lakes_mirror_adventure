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

const harness = `
globalThis.__run = function (keydown, keyup, releaseAll) {
  const out = {};

  // 1. 冲刺必须给出无敌帧
  resetGame();
  keydown('ShiftLeft');
  update(STEP);
  out.dashIframes = Game.player.invT;
  out.dashIframesExpected = CFG.player.dashIFrames;
  out.dashActive = Game.player.dashT > 0;
  releaseAll();

  // 2. 球形态：按住上 + 冲刺进入，不触发普通冲刺，并且立刻上冲
  resetGame();
  const startY = Game.player.y;
  keydown('ArrowUp');
  keydown('ShiftLeft');
  update(STEP);
  out.ballEntered = Game.player.ball === true;
  out.ballSuppressedDash = Game.player.dashT === 0;
  keyup('ShiftLeft');
  for (let i = 0; i < 10; i++) update(STEP);
  out.ballRose = Game.player.y < startY - 20;
  out.ballStillActive = Game.player.ball === true;

  // 3. 球形态是免疫伤害的
  Game.bullets.push({
    x: Game.player.x, y: Game.player.y, vx: 0, vy: 0,
    r: CFG.bullets.r, kind: 'hazard', grazed: true, life: 60
  });
  const livesInBall = Game.lives;
  update(STEP);
  out.ballImmuneToDamage = Game.lives === livesInBall;

  // 4. 球形态：向下飞，落地必须自动取消（核心设计），且不是瞬间取消
  keyup('ArrowUp');
  keydown('ArrowDown');
  let groundFrame = -1;
  for (let i = 0; i < 180; i++) {
    update(STEP);
    if (!Game.player.ball) { groundFrame = i; break; }
  }
  out.ballExitByGround = groundFrame >= 3;
  out.ballExitFrame = groundFrame;
  out.ballGrounded = Math.abs(Game.player.y + CFG.player.visualR - GROUND_Y) < 1.5;
  releaseAll();

  // 4. 球形态：体力耗尽也必须退出
  resetGame();
  keydown('ArrowUp');
  keydown('ShiftLeft');
  update(STEP);
  keyup('ShiftLeft');
  let staminaFrame = -1;
  for (let i = 0; i < 600; i++) {
    update(STEP);
    if (!Game.player.ball) { staminaFrame = i; break; }
  }
  out.ballExitByStamina = staminaFrame >= 0;
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
  update(STEP);
  out.grazeCourage = Game.courage;

  const livesBefore = Game.lives;
  Game.bullets.push({
    x: p.x, y: p.y, vx: 0, vy: 0,
    r: CFG.bullets.r, kind: 'hazard', grazed: true, life: 40
  });
  update(STEP);
  out.livesLost = livesBefore - Game.lives;
  out.invulnAfterHit = Game.player.invT;
  out.invulnExpected = CFG.player.hurtIFrames;

  // 7. 阶段推进：越过阈值后切阶段并清屏
  resetGame();
  for (let i = 0; i < 200; i++) update(STEP);
  out.bulletsBeforePhase = Game.bullets.length;
  Game.boss.hp = Game.boss.maxHp * 0.5;
  update(STEP);
  out.phaseAfterDrop = Game.boss.phase;
  out.bulletsClearedOnPhase = Game.bullets.length;

  // 8. 弹幕确实会生成，并且会飞出边界被回收
  resetGame();
  let peak = 0;
  for (let i = 0; i < 900; i++) {
    update(STEP);
    if (Game.bullets.length > peak) peak = Game.bullets.length;
  }
  out.peakBullets = peak;
  out.after900 = Game.bullets.length;

  // 9. 弹药上限保护：连打 900 帧不释放也不会无限增长
  out.peakUnder1000 = peak < 1000;

  return out;
};
`;

// runInThisContext 里的脚本看不到模块作用域，需要显式挂到全局
globalThis.__keydown = keydown;
globalThis.__keyup = keyup;
globalThis.__releaseAll = releaseAll;

const code = files
  .map(function (f) { return fs.readFileSync(path.join(root, f), 'utf8'); })
  .join('\n') + '\n' + harness +
  '\nglobalThis.__out = globalThis.__run(globalThis.__keydown, globalThis.__keyup, globalThis.__releaseAll);';

vm.runInThisContext(code, { filename: 'game-bundle.js' });

const out = globalThis.__out;

const checks = [
  ['冲刺给出无敌帧', out.dashIframes >= out.dashIframesExpected, out.dashIframes + ' 帧 / 期望 ≥ ' + out.dashIframesExpected],
  ['冲刺期间处于冲刺状态', out.dashActive === true, ''],
  ['按住上+冲刺进入球形态', out.ballEntered === true, ''],
  ['进入球形态时抑制普通冲刺', out.ballSuppressedDash === true, ''],
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
  ['弹幕峰值可控', out.peakUnder1000, '峰值 ' + out.peakBullets + ' 颗，900 帧后剩 ' + out.after900 + ' 颗']
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
