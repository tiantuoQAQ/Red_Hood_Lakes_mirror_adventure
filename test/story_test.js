'use strict';

// 剧情/演出系统的逻辑测试（不需要浏览器）：
//   1) 序章能一路播到第一场战斗
//   2) 打完魔姬能接到 crimson_fall，并解锁「红之惨剧」
//   3) 打完玛丽苏能接到结局
//   4) Tab 跳过能直接落到战斗
// 运行： node test/story_test.js

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
  'src/story.js',
  'src/game.js',
  'src/cutscene.js'
];

const sandbox = {
  console: console,
  Math: Math,
  Object: Object,
  Array: Array,
  JSON: JSON,
  window: { addEventListener: function () {} },
  setTimeout: setTimeout
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
files.forEach(function (f) {
  vm.runInContext(fs.readFileSync(path.join(root, f), 'utf8'), sandbox, { filename: f });
});

const Game = vm.runInContext('Game', sandbox);
const Cutscene = vm.runInContext('Cutscene', sandbox);
const STORY = vm.runInContext('STORY', sandbox);
const Input = vm.runInContext('Input', sandbox);

let failed = 0;
function check(name, cond, extra) {
  if (cond) console.log('PASS  ' + name + (extra ? '   (' + extra + ')' : ''));
  else { failed++; console.log('FAIL  ' + name + (extra ? '   (' + extra + ')' : '')); }
}

// 一直按「继续」，直到离开 story 模式
function playThrough(maxFrames) {
  let n = 0;
  const limit = maxFrames || 20000;
  while (Game.mode === 'story' && n < limit) {
    Cutscene.forceAdvance = true;
    Cutscene.update(1 / 60);
    Input.tick();
    n++;
  }
  return n;
}

// ---------------- 1. 章节表完整性 ----------------
const ids = Object.keys(STORY);
check('章节表非空', ids.length >= 5, 'chapters=' + ids.length);

let battleTargets = [];
ids.forEach(function (id) {
  STORY[id].cmds.forEach(function (c) {
    if (c.t === 'battle') battleTargets.push(c.boss);
    if (c.t === 'next') {
      if (!STORY[c.chapter]) { failed++; console.log('FAIL  章节引用不存在: ' + id + ' -> ' + c.chapter); }
    }
    if (c.t === 'battle' && c.after && !STORY[c.after]) {
      failed++; console.log('FAIL  after 章节不存在: ' + id + ' -> ' + c.after);
    }
  });
});
check('两场战斗：魔姬 + 玛丽苏', battleTargets.join(',') === 'crimson,marysue', battleTargets.join(','));

// ---------------- 2. 序章推进 ----------------
Game.mode = 'title';
Cutscene.start('prologue');
check('开场进演出模式', Game.mode === 'story', Game.mode);

const frames1 = playThrough();
check('序章能播到第一场战斗', Game.mode === 'play', 'mode=' + Game.mode + ' frames=' + frames1);
check('第一场是魔姬', Game.boss && Game.boss.id === 'crimson', Game.boss && Game.boss.id);
check('魔姬血量来自 BOSSES 表', Game.boss && Game.boss.hp === 240, Game.boss && String(Game.boss.hp));
check('打完接 crimson_fall', Game.afterBattle === 'crimson_fall', String(Game.afterBattle));

// ---------------- 3. 魔姬战败 -> 传承 -> 最终战 ----------------
Game.boss.hp = 0;
vm.runInContext('checkBossDeath()', sandbox);
check('魔姬战败切回演出', Game.mode === 'story', Game.mode);

const frames2 = playThrough();
check('传承章节能播到最终战', Game.mode === 'play', 'mode=' + Game.mode + ' frames=' + frames2);
check('技能「红之惨剧」已解锁', !!(Game.skills && Game.skills.red_tragedy), JSON.stringify(Game.skills));
check('最终 BOSS 是玛丽苏', Game.boss && Game.boss.id === 'marysue', Game.boss && Game.boss.id);

// ---------------- 4. 结局 ----------------
Game.boss.hp = 0;
vm.runInContext('checkBossDeath()', sandbox);
const frames3 = playThrough();
check('打完玛丽苏进结局', Game.mode === 'win', 'mode=' + Game.mode + ' frames=' + frames3);

// ---------------- 5. Tab 跳过 ----------------
Cutscene.start('mirror');
Cutscene.skip();
check('跳过直接落到战斗', Game.mode === 'play' && Game.boss.id === 'crimson',
      'mode=' + Game.mode + ' boss=' + (Game.boss && Game.boss.id));

console.log('');
if (failed) {
  console.log('失败 ' + failed + ' 项');
  process.exit(1);
}
console.log('全部通过');
