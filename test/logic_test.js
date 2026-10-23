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

  // 球形态：空中「按住上 + 按冲刺」立刻进入（不需要长按）
  resetGame();
  Game.boss.gap = 100000;
  const startY = Game.player.y;
  keydown('Space');
  step();
  keyup('Space');
  for (let i = 0; i < 6; i++) step();
  out.wasAirborne = Game.player.onGround === false;

  keydown('ArrowUp');
  keydown('ShiftLeft');
  step();
  out.ballEnteredByCombo = Game.player.ball === true;
  out.ballRose = Game.player.y < startY - 20;

  // 松开冲刺立刻变回人
  keyup('ShiftLeft');
  step();
  out.ballExitsOnRelease = Game.player.ball === false;
  releaseAll();

  // 地面上按组合键不会变球（否则等于站桩无敌）
  resetGame();
  Game.boss.gap = 100000;
  keydown('ArrowUp');
  keydown('ShiftLeft');
  for (let i = 0; i < 30; i++) step();
  out.noBallOnGround = Game.player.ball === false;
  releaseAll();

  // 按住冲刺期间落地，不会变回人
  resetGame();
  Game.boss.gap = 100000;
  keydown('Space');
  step();
  keyup('Space');
  for (let i = 0; i < 6; i++) step();
  keydown('ArrowUp');
  keydown('ShiftLeft');
  step();
  keyup('ArrowUp');
  keydown('ArrowDown');
  let touchedGround = false;
  for (let i = 0; i < 240; i++) {
    step();
    if (Math.abs(Game.player.y + CFG.player.visualR - GROUND_Y) < 2) {
      touchedGround = true;
      out.ballStillOnAtGround = Game.player.ball === true;
      break;
    }
  }
  out.ballSurvivesLanding = touchedGround && out.ballStillOnAtGround === true;
  keyup('ArrowDown');
  keyup('ShiftLeft');
  step();
  out.ballExitsAfterRelease = Game.player.ball === false;
  releaseAll();

  // 球形态免疫伤害
  resetGame();
  Game.boss.gap = 100000;
  keydown('Space'); step(); keyup('Space');
  for (let i = 0; i < 6; i++) step();
  keydown('ArrowUp');
  keydown('ShiftLeft');
  step();
  Game.bullets.push({
    x: Game.player.x, y: Game.player.y, vx: 0, vy: 0,
    r: CFG.bullets.r, kind: 'hazard', grazed: true, life: 60
  });
  const livesInBall = Game.lives;
  step();
  out.ballImmuneToDamage = Game.lives === livesInBall;

  // 体力耗尽自动退出
  let staminaFrame = -1;
  for (let i = 0; i < 900; i++) {
    step();
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
  step();
  out.grazeCourage = Game.courage;

  const livesBefore = Game.lives;
  Game.bullets.push({
    x: p.x, y: p.y, vx: 0, vy: 0,
    r: CFG.bullets.r, kind: 'hazard', grazed: true, life: 40
  });
  step();
  out.livesLost = livesBefore - Game.lives;

  // 受击不击飞：速度与位置不能被系统改写，只给无敌帧
  resetGame();
  Game.boss.gap = 100000;
  Game.player.vx = 0;
  Game.player.vy = 0;
  const px0 = Game.player.x;
  const py0 = Game.player.y;
  Game.bullets.push({
    x: px0, y: py0, vx: 0, vy: 0,
    r: CFG.bullets.r, kind: 'hazard', grazed: true, life: 40
  });
  step();
  out.hurtNoKnockback = (Game.player.vx === 0 && Game.player.vy === 0 &&
                         Math.abs(Game.player.x - px0) < 0.001 &&
                         Math.abs(Game.player.y - py0) < 0.001);
  out.hurtStillInvuln = Game.player.invT >= CFG.player.hurtIFrames - 1;
  out.invulnAfterHit = Game.player.invT;
  out.invulnExpected = CFG.player.hurtIFrames;

  // 擦弹连击：连续擦弹勇气倍率上升
  resetGame();
  Game.boss.gap = 100000;          // 关掉 BOSS 弹幕，隔离测试
  Game.courage = 0;
  const gp = Game.player;
  const gains = [];
  for (let k = 0; k < 6; k++) {
    const before = Game.courage;
    Game.bullets.push({
      x: gp.x + CFG.player.grazeR - 2, y: gp.y, vx: 0, vy: -300,
      r: CFG.bullets.r, kind: 'hazard', grazed: false, life: 40
    });
    step();
    gains.push(+(Game.courage - before).toFixed(2));
  }
  out.grazeChain = gp.grazeChain;
  out.grazeGains = gains;
  out.grazeGainRises = gains[gains.length - 1] > gains[0];

  // 连击窗口超时后归零
  for (let i = 0; i < CFG.player.grazeChainWindow + 6; i++) step();
  out.chainExpired = gp.grazeChain === 0;

  // 中弹清空擦弹连击
  resetGame();
  Game.boss.gap = 100000;
  Game.player.grazeChain = 7;
  Game.player.grazeTimer = 50;
  Game.bullets.push({
    x: Game.player.x, y: Game.player.y, vx: 0, vy: 0,
    r: CFG.bullets.r, kind: 'hazard', grazed: true, life: 30
  });
  step();
  out.chainClearedOnHit = Game.player.grazeChain === 0;

  // 擦弹返还冲刺冷却
  resetGame();
  Game.boss.gap = 100000;
  Game.player.dashCd = 20;
  const cdBefore = Game.player.dashCd;
  Game.bullets.push({
    x: Game.player.x + CFG.player.grazeR - 2, y: Game.player.y, vx: 0, vy: -300,
    r: CFG.bullets.r, kind: 'hazard', grazed: false, life: 40
  });
  step();
  out.dashRefund = cdBefore - Game.player.dashCd;

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
  for (let i = 0; i < 20; i++) step();
  out.mouseNoMove = Math.abs(Game.player.x - xBefore) < 0.001;
  mouseup(0);


  // 预警线：穿刺招式先给提示
  resetGame();
  Game.boss.gap = 100000;
  PATTERNS.lances.fire(Game, Game.boss, 0);
  out.warningsCreated = Game.warnings.length;

  // 激光：蓄力阶段不伤血，生效后才判定
  resetGame();
  Game.boss.gap = 100000;
  PATTERNS.laser.fire(Game, Game.boss, 0);
  out.beamCreated = Game.beams.length;
  const livesBeam = Game.lives;
  const bm = Game.beams[0];
  Game.player.x = bm.x + Math.cos(bm.a) * 200;
  Game.player.y = bm.y + Math.sin(bm.a) * 200;
  Game.player.invT = 0;
  step();
  out.beamSafeDuringWarmup = Game.lives === livesBeam;
  for (let i = 0; i < CFG.beam.warmup + 4; i++) {
    Game.player.x = bm.x + Math.cos(bm.a) * 200;
    Game.player.y = bm.y + Math.sin(bm.a) * 200;
    Game.player.vy = 0;
    step();
  }
  out.beamHitsWhenActive = Game.lives < livesBeam;

  // 追踪弹会转向
  resetGame();
  Game.boss.gap = 100000;
  PATTERNS.homing.fire(Game, Game.boss, 0);
  const homes = Game.bullets.filter(function (b) { return b.kind === 'homing'; });
  out.homingCreated = homes.length;
  const hb = homes[0];
  const a0 = Math.atan2(hb.vy, hb.vx);
  Game.player.x = hb.x + 420;
  Game.player.y = hb.y - 260;
  for (let i = 0; i < 20; i++) step();
  const a1 = Math.atan2(hb.vy, hb.vx);
  out.homingTurns = Math.abs(a1 - a0) > 0.08;

  // BOSS 冲刺会位移
  resetGame();
  Game.boss.gap = 100000;
  PATTERNS.bossDash.fire(Game, Game.boss, 0);
  out.dashStarted = Game.boss.dashT > 0;
  const bossX0 = Game.boss.x;
  for (let i = 0; i < 6; i++) step();
  out.bossMoves = Math.abs(Game.boss.x - bossX0) > 1;

  // 濒死演出：先慢动作再进死亡界面
  resetGame();
  Game.boss.gap = 100000;
  Game.lives = 1;
  Game.bullets.push({
    x: Game.player.x, y: Game.player.y, vx: 0, vy: 0,
    r: CFG.bullets.r, kind: 'hazard', grazed: true, life: 30
  });
  step();
  out.dyingStarted = Game.dying === true && Game.slowT > 0;
  out.slowFrames = Game.slowT;
  out.stayInPlayDuringSlowmo = Game.mode === 'play';
  for (let i = 0; i < 45; i++) step();
  out.deadAfterSlowmo = Game.mode === 'dead';

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
  ['空中按住上+冲刺立刻变球', out.ballEnteredByCombo && out.wasAirborne, ''],
  ['球形态起手强制上冲', out.ballRose === true, ''],
  ['松开冲刺立刻变回人', out.ballExitsOnRelease === true, ''],
  ['地面上按组合键不变球', out.noBallOnGround === true, ''],
  ['按住冲刺时落地不变人', out.ballSurvivesLanding === true, ''],
  ['松手后正常退出', out.ballExitsAfterRelease === true, ''],
  ['球形态免疫伤害', out.ballImmuneToDamage === true, ''],
  ['球形态体力耗尽自动退出', out.ballExitByStamina && out.ballStaminaFrames > 0, '第 ' + out.ballStaminaFrames + ' 帧耗尽'],
  ['判定点远小于视觉半径', out.hitboxRatio <= 0.3, 'hitR=' + out.hitR + ' visualR=' + out.visualR + ' 比例=' + out.hitboxRatio],
  ['擦弹增加勇气', out.grazeCourage > 0, '勇气=' + out.grazeCourage],
  ['连续擦弹勇气倍率上升', out.grazeGainRises === true, '依次 ' + out.grazeGains.join(' / ')],
  ['连击窗口超时归零', out.chainExpired === true, ''],
  ['中弹清空擦弹连击', out.chainClearedOnHit === true, ''],
  ['擦弹返还冲刺冷却', out.dashRefund >= 3, '-' + out.dashRefund + ' 帧'],
  ['中弹扣一条命', out.livesLost === 1, ''],
  ['受击不击飞（速度与位置不变）', out.hurtNoKnockback === true, ''],
  ['受击仍给足无敌帧', out.hurtStillInvuln === true, ''],
  ['中弹后进入无敌', out.invulnAfterHit >= out.invulnExpected, out.invulnAfterHit + ' 帧 / 期望 ≥ ' + out.invulnExpected],
  ['弹幕会生成', out.bulletsBeforePhase > 0, '200 帧时场上 ' + out.bulletsBeforePhase + ' 颗'],
  ['血量过阈值切换阶段', out.phaseAfterDrop === 1, 'phase=' + out.phaseAfterDrop],
  ['换阶段清屏', out.bulletsClearedOnPhase === 0, ''],
  ['弹幕峰值可控', out.peakUnder1000, '峰值 ' + out.peakBullets + ' 颗，900 帧后剩 ' + out.after900 + ' 颗'],
  ['鼠标左键可射击', out.mouseFireShots > 0, '出膛 ' + out.mouseFireShots + ' 发'],
  ['鼠标右键可冲刺', out.mouseDashActive && out.mouseDashIframes >= out.dashIframesExpected, out.mouseDashIframes + ' 帧无敌'],
  ['鼠标不会让角色移动', out.mouseNoMove === true, ''],
  ['穿刺招式生成预警线', out.warningsCreated > 0, out.warningsCreated + ' 条'],
  ['激光生成光束', out.beamCreated === 2, out.beamCreated + ' 条（镜像成对）'],
  ['激光蓄力阶段不伤血', out.beamSafeDuringWarmup === true, ''],
  ['激光生效后命中', out.beamHitsWhenActive === true, ''],
  ['追踪弹生成且会转向', out.homingCreated > 0 && out.homingTurns === true, out.homingCreated + ' 颗'],
  ['BOSS 冲刺启动并位移', out.dashStarted === true && out.bossMoves === true, ''],
  ['濒死先慢动作后进死界', out.dyingStarted && out.stayInPlayDuringSlowmo && out.deadAfterSlowmo,
   '慢动作 ' + out.slowFrames + ' 帧']
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
