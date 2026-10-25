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

// 鼠标位置 → 画布坐标（射击朝鼠标，不再自动瞄准 BOSS）
const MOUSE = { x: W / 2, y: H / 2, active: false };
canvas.addEventListener('mousemove', function (e) {
  const r = canvas.getBoundingClientRect();
  MOUSE.x = (e.clientX - r.left) / Math.max(1, r.width) * W;
  MOUSE.y = (e.clientY - r.top) / Math.max(1, r.height) * H;
  MOUSE.active = true;
  Game.mouse = MOUSE;
});

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
  // 预载必杀技名用的毛笔体，避免第一次演出时字体还没到
  if (document.fonts && document.fonts.load) {
    document.fonts.load('80px CutinBrush');
  }
  const params = new URLSearchParams(location.search);
  if (params.get('theme')) Game.theme = params.get('theme');
  if (params.get('auto') === '1') {
    resetGame(params.get('boss') || undefined);
    const px = params.get('px');
    if (px && Game.player && Game.cam) {
      Game.player.x = parseFloat(px);
      Game.cam.x = Math.max(0, Math.min(WORLD_W - W, Game.player.x - W / 2));
    }
    const ff = parseInt(params.get('ff') || '0', 10);
    for (let i = 0; i < ff; i++) {
      update(STEP);
      Input.tick();
    }
    // 调试：?shots=1 手动塞几发我方子弹，方便截图看弹道表现
    if (params.get('shots') === '1' && Game.player) {
      const p = Game.player;
      for (let i = 0; i < 6; i++) {
        const a = -0.55 + i * 0.12;
        Game.shots.push({
          x: p.x + Math.cos(a) * (70 + i * 26),
          y: p.y + Math.sin(a) * (70 + i * 26),
          vx: Math.cos(a) * 900, vy: Math.sin(a) * 900, r: 5, dmg: 3
        });
      }
    }
    // 调试：?ball=1 让玩家直接进入球形态（截图用）
    if (params.get('ball') === '1' && Game.player) {
      const p = Game.player;
      p.ball = true;
      p.y = 380;
      p.vy = -60;
      p.ballLaunch = 0;
      p.stamina = 78;
    }
    return;
  }
  // 调试：?mtest=crimson 检查战斗曲能否加载/播放
  if (params.get('mtest')) {
    const nm = params.get('mtest');
    Music.play(nm === 'true' ? 'crimson' : nm);
    setTimeout(function () {
      const el = document.querySelector('audio');
      document.title = 'MUSIC ' + (typeof Music !== 'undefined' ? Music.name() : '?');
    }, 1200);
  }
  if (params.get('story') === '0') {
    Game.mode = 'title';
    return;
  }
  // 调试：?cutinf=crimson 直接看必杀演出大特写
  const cine = params.get('cutinf');
  if (cine) {
    const cid = (cine === 'true' ? 'crimson' : cine);
    resetGame(cid);
    startCutin(cid);
    Game.cutin.t = 40;
    Game.cutin.dur = 9999;
    const cff = parseInt(params.get('ff') || '0', 10);
    for (let i = 0; i < cff; i++) { update(STEP); Input.tick(); }
    return;
  }
  // 调试：?intro=norden 直接看登场竖幅（称号按 titleColor 上色）
  const dbgIntro = params.get('intro');
  if (dbgIntro && typeof STORY !== 'undefined') {
    STORY._dbg_intro = { cmds: [
      { t: 'fade', to: 'clear', frames: 1 },
      { t: 'intro', id: dbgIntro },
      { t: 'wait', frames: 9999 }
    ] };
    Cutscene.start('_dbg_intro');
    const iff = parseInt(params.get('ff') || '0', 10);
    for (let i = 0; i < iff; i++) { Cutscene.update(STEP); }
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
  // 调试：?nordenscene=1 直接进诺登走位段（检查待机立绘有没有被裁）
  if (params.get('nordenscene') === '1') {
    Game.mode = 'walk';
    startWalk({ cam: true, target: { kind: 'norden', x: 1180, label: '诺登' }, next: 'wake_talk' });
    if (Game.player) Game.player.x = 1000;
    const nff = parseInt(params.get('ff') || '0', 10);
    for (let i = 0; i < nff; i++) { update(STEP); Input.tick(); }
    return;
  }
  // 调试：?mabelscene=1 直接进「走向梅贝尔」的走位段
  if (params.get('mabelscene') === '1') {
    Game.mode = 'walk';
    startWalk({ cam: true, target: { kind: 'mabel', x: 1180, label: '梅贝尔' }, next: 'mabel_talk' });
    if (Game.player) Game.player.x = 1000;
    const mff = parseInt(params.get('ff') || '0', 10);
    for (let i = 0; i < mff; i++) { update(STEP); Input.tick(); }
    return;
  }
  // 调试：?throne=1 直接进王座走位段
  if (params.get('throne') === '1') {
    startWalk({
      bg: 'mirror', cam: true, untilX: 1180, next: 'mirror_meet',
      props: [{ kind: 'throne', x: 1620, char: 'rek_crimson' }]
    });
    const tpx = params.get('px');
    if (tpx && Game.player) Game.player.x = parseFloat(tpx);
    const ff = parseInt(params.get('ff') || '0', 10);
    for (let i = 0; i < ff; i++) { update(STEP); Input.tick(); }
    return;
  }
  Cutscene.start('prologue');
})();

requestAnimationFrame(frameLoop);
