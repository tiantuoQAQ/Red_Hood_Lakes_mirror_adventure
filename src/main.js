'use strict';

// 入口：固定步长循环、画布适配、调参面板绑定。

const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d', { alpha: false });

function fitCanvas() {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  // 让后端像素尺寸和 CSS 显示尺寸一致：否则浏览器会重采样整幅画面，
  // 相邻像素插值会凭空造出中间色相（红色玩家压上绿色弹幕 → 橙色边缘）。
  const cssW = canvas.clientWidth || W;
  const cssH = canvas.clientHeight || H;
  canvas.width = Math.max(1, Math.round(cssW * dpr));
  canvas.height = Math.max(1, Math.round(cssH * dpr));
  ctx.setTransform(canvas.width / W, 0, 0, canvas.height / H, 0, 0);
}

fitCanvas();
window.addEventListener('resize', fitCanvas);

// 浏览器要求音频在用户交互之后才能启动
window.addEventListener('keydown', function () { Sfx.unlock(); });
window.addEventListener('pointerdown', function () { Sfx.unlock(); });

// 输入延迟测量：从按键事件到该帧真正画到屏幕上，这段时间才是玩家体感到的延迟
let pendingKeyStamp = null;
window.addEventListener('keydown', function () {
  if (pendingKeyStamp === null) pendingKeyStamp = performance.now();
});

// ------------------------------------------------------------ 调参面板

const panelEl = document.getElementById('panel');

function togglePanel() {
  if (panelEl) panelEl.classList.toggle('hidden');
}

function getByPath(obj, path) {
  const parts = path.split('.');
  let o = obj;
  for (let i = 0; i < parts.length; i++) {
    if (o === null || o === undefined) return undefined;
    o = o[parts[i]];
  }
  return o;
}

function setByPath(obj, path, value) {
  const parts = path.split('.');
  let o = obj;
  for (let i = 0; i < parts.length - 1; i++) o = o[parts[i]];
  o[parts[parts.length - 1]] = value;
}

function fmt(v) {
  return Number.isInteger(v) ? String(v) : Number(v).toFixed(2);
}

(function bindPanel() {
  const sliders = document.querySelectorAll('#panel input[data-cfg]');
  for (let i = 0; i < sliders.length; i++) {
    const el = sliders[i];
    const path = el.getAttribute('data-cfg');
    const out = document.querySelector('[data-out="' + path + '"]');
    const initial = getByPath(CFG, path);
    el.value = initial;
    if (out) out.textContent = fmt(initial);

    el.addEventListener('input', function () {
      const val = parseFloat(el.value);
      setByPath(CFG, path, val);
      if (out) out.textContent = fmt(val);

      // BOSS 血量需要同步到当前这一场
      if (path === 'boss.hp' && Game.boss) {
        const ratio = Game.boss.hp / Game.boss.maxHp;
        Game.boss.maxHp = val;
        Game.boss.hp = Math.max(1, Math.min(val, val * ratio));
      }
    });
  }

  const btnRestart = document.getElementById('btn-restart');
  if (btnRestart) btnRestart.addEventListener('click', function () { resetGame(); });

  const btnJson = document.getElementById('btn-json');
  if (btnJson) {
    btnJson.addEventListener('click', function () {
      const txt = JSON.stringify(CFG, null, 2);
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).then(function () {
          btnJson.textContent = '已复制';
          setTimeout(function () { btnJson.textContent = '导出 JSON'; }, 1200);
        }, function () { console.log(txt); });
      } else {
        console.log(txt);
      }
    });
  }
})();

// ------------------------------------------------------------ 主循环

function stepOnce() {
  if (Input.pressed('toggleHitbox')) Game.debug.hitbox = !Game.debug.hitbox;
  if (Input.pressed('togglePanel')) togglePanel();
  if (Input.pressed('mute')) Sfx.toggleMute();

  if (Game.mode === 'title') {
    Game.frame++;
    if (Input.pressed('start')) Cutscene.start('prologue');
  } else if (Game.mode === 'story') {
    Game.frame++;
    Cutscene.update(STEP);
  } else if (Game.mode === 'walk') {
    if (Input.pressed('pause')) Game.paused = !Game.paused;
    if (Game.paused) Game.frame++;
    else update(STEP);
  } else if (Game.mode === 'play') {
    if (Input.pressed('pause')) Game.paused = !Game.paused;
    if (Game.paused) Game.frame++;
    else update(STEP);
  } else {
    Game.frame++;
    if (Input.pressed('restart') || Input.pressed('start')) resetGame(Game.currentBossId);
  }

  Input.tick();
}

let acc = 0;
let last = performance.now();

function frameLoop(now) {
  const dt = Math.min(0.25, (now - last) / 1000);
  last = now;
  acc += dt;

  // 帧时间平滑，用于 HUD 显示的实际帧率
  Game.debug.frameMs = Game.debug.frameMs ? Game.debug.frameMs * 0.9 + dt * 1000 * 0.1 : dt * 1000;

  let guard = 0;
  while (acc >= STEP && guard < 6) {
    stepOnce();
    acc -= STEP;
    guard++;
  }
  if (guard >= 6) acc = 0;   // 掉帧时丢弃积压，避免「越卡越快」

  render(ctx);

  // 画面已经提交，此时计算「按键 → 画面」的真实延迟
  if (pendingKeyStamp !== null) {
    const ms = performance.now() - pendingKeyStamp;
    Game.debug.latencyMs = Game.debug.latencyMs === 0 ? ms : Game.debug.latencyMs * 0.85 + ms * 0.15;
    pendingKeyStamp = null;
  }

  // 载入角色贴图（缺图不影响运行，会退回程序化图形）
Sprites.load(CFG.sprite.id, CFG.sprite.dir);

requestAnimationFrame(frameLoop);
}

// 调试用：?auto=1 直接开局（跳过剧情），?ff=N 预跑 N 帧（用于截图验证）
// ?story=0 回标题画面；默认直接从序章开始播
(function boot() {
  const params = new URLSearchParams(location.search);
  if (params.get('auto') === '1') {
    resetGame();
    const ff = parseInt(params.get('ff') || '0', 10);
    for (let i = 0; i < ff; i++) {
      update(STEP);
      Input.tick();
    }
    return;
  }
  if (params.get('story') === '0') {
    Game.mode = 'title';
    return;
  }
  // 调试：?chapter=wake 直接从某一章开始；?walk=1 直接进走位段
  const ch = params.get('chapter');
  if (ch) { Cutscene.start(ch); return; }
  if (params.get('walk') === '1') {
    startWalk({ untilX: 1040, next: 'ambush' });
    const ff = parseInt(params.get('ff') || '0', 10);
    for (let i = 0; i < ff; i++) { update(STEP); Input.tick(); }
    return;
  }
  Cutscene.start('prologue');
})();

requestAnimationFrame(frameLoop);
