'use strict';

// 光球特效的冒烟测试（不需要浏览器）：用桩 canvas 跑一遍绘制路径，确认：
//   1) 贴图中的 8 帧能被正确切片绘制
//   2) 贴图未加载时会退回程序化圆点，而不是崩溃
//   3) 非 fx 粒子不会被 Fx 重复绘制
// 运行： node test/fx_smoke.js

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const files = ['src/config.js', 'src/gfx.js', 'src/fx.js'];

let drawImageCalls = [];
let arcCalls = 0;
let gradientStops = 0;
let imageShouldLoad = true;

function makeCtx() {
  return {
    globalAlpha: 1,
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 1,
    save: function () {},
    restore: function () {},
    translate: function () {},
    rotate: function () {},
    beginPath: function () {},
    arc: function () { arcCalls++; },
    fill: function () {},
    stroke: function () {},
    drawImage: function (img, sx, sy, sw, sh, dx, dy, dw, dh) {
      drawImageCalls.push({ sx: sx, sw: sw, dw: dw });
    },
    createRadialGradient: function () {
      return { addColorStop: function () { gradientStops++; } };
    }
  };
}

// Image 桩：赋值 src 后同步触发 onload，够用
function ImageStub() {
  const self = this;
  this.naturalWidth = 0;
  this.naturalHeight = 0;
  this._src = '';
  Object.defineProperty(this, 'src', {
    get: function () { return self._src; },
    set: function (v) {
      self._src = v;
      if (!imageShouldLoad) return;
      self.naturalWidth = 2048;
      self.naturalHeight = 256;
      if (self.onload) self.onload();
    }
  });
}

function loadFx(extra) {
  const sandbox = Object.assign({
    console: console,
    Math: Math,
    Object: Object,
    Array: Array,
    Image: ImageStub,
    window: { addEventListener: function () {} },
    setTimeout: setTimeout
  }, extra || {});
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  files.forEach(function (f) {
    vm.runInContext(fs.readFileSync(path.join(root, f), 'utf8'), sandbox, { filename: f });
  });
  return sandbox;
}

let failed = 0;
function check(name, cond, extra) {
  if (cond) {
    console.log('PASS  ' + name + (extra ? '   (' + extra + ')' : ''));
  } else {
    failed++;
    console.log('FAIL  ' + name + (extra ? '   (' + extra + ')' : ''));
  }
}

// ---------------- 场景一：贴图可用 ----------------
const box = loadFx();
vm.runInContext('var Game = { frame: 7, particles: [] };', box);
const Fx = vm.runInContext('Fx', box);
const Game = vm.runInContext('Game', box);

check('贴图加载成功（8 帧 × 256）', Fx.ready());

arcCalls = 0;
gradientStops = 0;
Fx.drawBall(makeCtx(), { x: 400, y: 300 });
check('球体绘制不抛异常', true);
check('径向渐变有 4 个色标（白→红→透明）', gradientStops === 4, 'stops=' + gradientStops);
check('球体画了光晕/旋转弧/内核/冲击波', arcCalls >= 5, 'arc=' + arcCalls);

drawImageCalls = [];
Game.particles.length = 0;
for (let i = 0; i < 3; i++) {
  Game.particles.push({
    kind: 'fx', x: 400, y: 300, vx: 0, vy: 0,
    life: 5 + i * 5, max: 20, rot: 0.5, spin: 0.1, size: 30
  });
}
// 普通粒子不应被 Fx 画
Game.particles.push({ x: 1, y: 1, vx: 0, vy: 0, life: 5, max: 10, r: 2, color: '#ff0000' });

Fx.drawBallParticles(makeCtx());
check('3 颗拖尾粒子各画一次贴图', drawImageCalls.length === 3, 'calls=' + drawImageCalls.length);
check('切片宽度是 256', drawImageCalls.every(function (c) { return c.sw === 256; }));
check('帧号随存活进度推进', drawImageCalls.some(function (c) { return c.sx > 0; }),
      'sx=' + drawImageCalls.map(function (c) { return c.sx; }).join(','));

// ---------------- 场景二：贴图缺失 ----------------
imageShouldLoad = false;
const box2 = loadFx();
vm.runInContext('var Game = { frame: 3, particles: [{ kind: "fx", x: 0, y: 0, vx: 0, vy: 0, life: 4, max: 10, rot: 0, spin: 0, size: 20 }] };', box2);
const Fx2 = vm.runInContext('Fx', box2);

drawImageCalls = [];
arcCalls = 0;
Fx2.drawBallParticles(makeCtx());
check('贴图未加载时退回圆点', drawImageCalls.length === 0 && arcCalls === 1,
      'drawImage=' + drawImageCalls.length + ' arc=' + arcCalls);

Fx2.drawBall(makeCtx(), { x: 100, y: 100 });
check('贴图未加载时球体仍能画', arcCalls > 1, 'arc=' + arcCalls);

console.log('');
if (failed) {
  console.log('失败 ' + failed + ' 项');
  process.exit(1);
}
console.log('全部通过');
