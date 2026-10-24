'use strict';

// 演出系统（过场）：读 STORY 里的指令，播三种表现形式。
//
//   ① 章节卡 card  —— 背景 + 大立绘 + 底部两行字幕
//   ② 场景气泡 bubble —— 小人站在场上，头顶带名字的对话框
//   ③ 双立绘对峙 duel —— 左右各一张大立绘，中间偏下一条对话
//   另有通用底部对话框 say。
//
// 设计原则：不让代码依赖美术资源。立绘还没出，就先画占位色块，
// 之后只要把 art 路径填进 CHARS[id].art，同一段代码自动换成真图。

const Cutscene = (function () {
  const CPS = 0.75;          // 每秒打出的字数（以 60 帧计）

  // 角色表：place = 占位色块颜色；art = 立绘路径（有就画图，没有就画块）
  const CHARS = {
    rek:         { name: '蕾克',   color: '#ff0000', dark: '#7a0000', art: 'art/portrait/rek.png' },
    rek_crimson: { name: '猩红魔姬', color: '#b30000', dark: '#4a0000', art: 'art/portrait/crimson.png' },
    norden:      { name: '诺登',   color: '#ff4d4d', dark: '#8a1f1f', art: 'art/portrait/norden.png' },
    marysue:     { name: '玛丽苏',  color: '#00baff', dark: '#004a66', art: 'art/portrait/marysue.png' },
    mabel:       { name: '梅贝尔',  color: '#cfcfcf', dark: '#5a5a5a', art: 'art/portrait/mabel.png' }
  };

  const S = {
    chapterId: null,
    cmds: null,
    idx: -1,
    t: 0,
    black: 0,
    blackTarget: 0,
    blackSpeed: 1 / 30,
    bg: 'night',
    text: null,        // { who, text, shown, mode:'say'|'bubble'|'duel', chars }
    card: null,        // { line1, line2 }
    framesLeft: 0,     // 自动推进的剩余帧
    battleNext: null,
    finished: false
  };

  const BGS = {
    night:  ['#0b0b0b', '#141414'],
    forest: ['#0d0d0d', '#171a17'],
    mirror: ['#05070b', '#0d1420']
  };

  function colorOf(id) {
    const c = CHARS[id];
    return c ? c.color : '#888888';
  }

  function charOf(id) {
    return CHARS[id] || { name: id, color: '#888888', art: null };
  }

  function start(chapterId) {
    const ch = STORY[chapterId];
    if (!ch) { console.warn('未知章节: ' + chapterId); return false; }
    S.chapterId = chapterId;
    S.cmds = ch.cmds;
    S.idx = -1;
    S.t = 0;
    S.text = null;
    S.card = null;
    S.framesLeft = 0;
    S.battleNext = null;
    S.finished = false;
    Game.mode = 'story';
    step();
    return true;
  }

  function current() {
    return S.cmds && S.idx >= 0 && S.idx < S.cmds.length ? S.cmds[S.idx] : null;
  }

  function step() {
    S.idx++;
    S.t = 0;
    const c = current();
    if (!c) { finishChapter(); return; }

    switch (c.t) {
      case 'fade':
        S.blackTarget = c.to === 'black' ? 1 : 0;
        S.blackSpeed = 1 / Math.max(1, c.frames || 30);
        break;
      case 'wait':
        S.framesLeft = c.frames || 30;
        break;
      case 'card':
        S.card = { line1: c.line1 || '', line2: c.line2 || '' };
        S.framesLeft = c.frames || 160;
        break;
      case 'say':
        S.text = { mode: 'say', who: c.who || '', text: c.text || '', shown: 0, chars: 0 };
        break;
      case 'bubble':
        S.text = { mode: 'bubble', who: c.who || '', text: c.text || '', shown: 0, chars: 0 };
        break;
      case 'duel':
        S.text = {
          mode: 'duel', who: '', text: c.text || '', shown: 0, chars: 0,
          left: c.left, right: c.right, hint: c.hint || '按 Enter 继续'
        };
        break;
      case 'scene':
        S.bg = c.bg || 'night';
        break;
      case 'battle':
        startBattle(c.boss || 'marysue', c.after || null);
        return;
      case 'grant':
        Game.skills = Game.skills || {};
        Game.skills[c.skill] = true;
        Game.banner = c.banner || '获得新技能';
        Game.bannerT = 150;
        S.text = {
          mode: 'say', who: '', shown: 0, chars: 0,
          text: '【获得技能】' + (c.banner || c.skill)
        };
        break;
      case 'next':
        start(c.chapter);
        return;
      case 'end':
        S.finished = true;
        Game.mode = 'win';
        Game.deadT = 0;
        return;
      default:
        console.warn('未知指令: ' + c.t);
        break;
    }
  }

  function startBattle(bossId, after) {
    Game.afterBattle = after || null;
    resetGame(bossId);
  }

  function finishChapter() {
    // 没有 next 也没有 battle：直接回标题，避免卡死
    Game.mode = 'title';
  }

  function textDone() {
    return !S.text || S.text.shown >= S.text.text.length;
  }

  // 跳过整段演出：直接跳到本章的 battle（有的话）
  function skip() {
    if (!S.cmds) return;
    for (let i = S.idx; i < S.cmds.length; i++) {
      if (S.cmds[i].t === 'battle') {
        S.idx = i - 1;   // step() 会自增，这里退一格才是「执行战斗」
        step();
        return;
      }
    }
    // 没有战斗就直接结束本章
    for (let i = S.idx; i < S.cmds.length; i++) {
      if (S.cmds[i].t === 'next') { start(S.cmds[i].chapter); return; }
      if (S.cmds[i].t === 'end') { S.finished = true; Game.mode = 'win'; return; }
    }
    Game.mode = 'title';
  }

  function wantsAdvance(force) {
    if (force) return true;
    return Input.pressed('start') || Input.pressed('jump') || Input.pressed('fire');
  }

  function update(dt) {
    const adv = wantsAdvance(Cutscene.forceAdvance);
    Cutscene.forceAdvance = false;

    if (Input.pressed('skip')) { skip(); return; }

    // 黑场匀速过渡
    if (S.black < S.blackTarget) S.black = Math.min(S.blackTarget, S.black + S.blackSpeed);
    else if (S.black > S.blackTarget) S.black = Math.max(S.blackTarget, S.black - S.blackSpeed);

    S.t++;

    // 打字机
    if (S.text && S.text.shown < S.text.text.length) {
      S.text.chars += CPS * dt * 60;
      const n = Math.floor(S.text.chars);
      if (n > S.text.shown) S.text.shown = Math.min(S.text.text.length, n);
    }

    // 自动推进的指令
    if (S.framesLeft > 0) {
      S.framesLeft--;
      if (S.framesLeft === 0 && (S.card || (current() && current().t === 'wait'))) {
        S.card = null;
        step();
      }
      return;
    }

    // 画面还在变黑/亮时，等它到位再推进
    if (Math.abs(S.black - S.blackTarget) > 0.001) return;
    if (!textDone()) return;

    if (adv) {
      S.text = null;
      step();
    }
  }

  // ---------------------------------------------------------------- 绘制

  function drawBackground(ctx) {
    const pair = BGS[S.bg] || BGS.night;
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, pair[0]);
    g.addColorStop(1, pair[1]);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    // 镜中世界：画一条中轴反光，暗示「镜」
    if (S.bg === 'mirror') {
      const rg = ctx.createLinearGradient(MIRROR_X - 120, 0, MIRROR_X + 120, 0);
      rg.addColorStop(0, 'rgba(255,255,255,0)');
      rg.addColorStop(0.5, 'rgba(255,255,255,0.05)');
      rg.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = rg;
      ctx.fillRect(MIRROR_X - 120, 0, 240, GROUND_Y);
    }

    ctx.fillStyle = 'rgba(255,255,255,0.06)';
    ctx.fillRect(0, GROUND_Y, W, 2);
  }

  // 立绘：有图就画图，没有就画带名字的色块
  // flip 只翻转真图（右侧角色镜像站位），占位色块的文字不跟着翻。
  const PORTRAITS = {};

  function getArt(path) {
    if (!path || typeof Image === 'undefined') return null;
    let img = PORTRAITS[path];
    if (!img) {
      img = new Image();
      img.src = path;
      PORTRAITS[path] = img;
    }
    return (img.complete && img.naturalWidth > 0) ? img : null;
  }

  function portrait(ctx, id, cx, cy, w, h, flip) {
    const c = charOf(id);
    const art = getArt(c.art);

    if (art) {
      // 等比缩放到 h 高，底部对齐
      const scale = h / art.naturalHeight;
      const dw = art.naturalWidth * scale;
      ctx.save();
      ctx.translate(cx, 0);
      if (flip) ctx.scale(-1, 1);
      ctx.drawImage(art, -dw / 2, cy + h / 2 - h, dw, h);
      ctx.restore();
      return;
    }

    // 色块占位
    roundRectPath(ctx, cx - w / 2, cy - h / 2, w, h, 18);
    ctx.fillStyle = hexToRgba(c.color, 0.14);
    ctx.fill();
    ctx.strokeStyle = hexToRgba(c.color, 0.5);
    ctx.lineWidth = 3;
    ctx.stroke();

    label(ctx, c.name, cx, cy + 10, Math.min(46, h * 0.22), c.color, 'center', 700);
    label(ctx, '立绘占位', cx, cy + 46, 16, 'rgba(255,255,255,0.35)', 'center', 400);
  }

  function drawCard(ctx) {
    if (!S.card) return;
    // 大立绘（居中偏上）
    portrait(ctx, 'rek', W / 2, H * 0.36, 300, 380, false);
    // 两行字幕
    label(ctx, S.card.line1, W / 2, H * 0.78, 40, 'rgba(255,255,255,0.95)', 'center', 700);
    label(ctx, S.card.line2, W / 2, H * 0.78 + 46, 32, 'rgba(255,255,255,0.75)', 'center', 500);
  }

  function bubbleBox(ctx, who, shownText, x, y) {
    const padX = 22;
    const padY = 18;
    const maxW = 620;
    ctx.font = '22px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
    const lines = wrapText(ctx, shownText, maxW);
    const lineH = 32;
    const w = Math.min(maxW, Math.max(220, maxLineWidth(ctx, lines) + padX * 2));
    const h = lines.length * lineH + padY * 2 + 34;

    // 名字签
    roundRectPath(ctx, x, y - h - 44, 120, 34, 8);
    ctx.fillStyle = '#111111';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.85)';
    ctx.lineWidth = 2;
    ctx.stroke();
    label(ctx, charOf(who).name, x + 60, y - h - 20, 20, '#ffffff', 'center', 700);

    // 正文框
    roundRectPath(ctx, x, y - h, w, h, 12);
    ctx.fillStyle = 'rgba(10,10,10,0.92)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.85)';
    ctx.lineWidth = 2;
    ctx.stroke();

    for (let i = 0; i < lines.length; i++) {
      label(ctx, lines[i], x + padX, y - h + padY + 26 + i * lineH, 22, '#f0f0f0', 'left', 400);
    }
    return { w: w, h: h };
  }

  function wrapText(ctx, text, maxW) {
    const out = [];
    let line = '';
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (ch === '\n') { out.push(line); line = ''; continue; }
      if (ctx.measureText(line + ch).width > maxW) { out.push(line); line = ch; }
      else line += ch;
    }
    if (line) out.push(line);
    return out.length ? out : [''];
  }

  function maxLineWidth(ctx, lines) {
    let m = 0;
    for (let i = 0; i < lines.length; i++) m = Math.max(m, ctx.measureText(lines[i]).width);
    return m;
  }

  function drawSay(ctx) {
    const boxH = 150;
    const y = H - boxH - 34;
    const x = 120;
    const w = W - 240;

    roundRectPath(ctx, x, y, w, boxH, 14);
    ctx.fillStyle = 'rgba(8,8,10,0.92)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.75)';
    ctx.lineWidth = 2;
    ctx.stroke();

    if (S.text.who) {
      roundRectPath(ctx, x + 24, y - 20, 140, 40, 10);
      ctx.fillStyle = 'rgba(8,8,10,0.95)';
      ctx.fill();
      ctx.strokeStyle = hexToRgba(colorOf(S.text.who), 0.9);
      ctx.lineWidth = 2;
      ctx.stroke();
      label(ctx, charOf(S.text.who).name, x + 94, y + 8, 22, colorOf(S.text.who), 'center', 700);
    }

    const shown = S.text.text.substring(0, S.text.shown);
    ctx.font = '24px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
    const lines = wrapText(ctx, shown, w - 80);
    for (let i = 0; i < lines.length; i++) {
      label(ctx, lines[i], x + 40, y + 52 + i * 38, 24, '#f2f2f2', 'left', 400);
    }
  }

  function drawBubble(ctx) {
    // 小人站在场上（还没有贴图，先画占位）
    const px = 360;
    const py = GROUND_Y;
    const bodyH = 110;
    ctx.fillStyle = hexToRgba(COLORS.player, 0.9);
    roundRectPath(ctx, px - 26, py - bodyH, 52, bodyH, 10);
    ctx.fill();
    label(ctx, charOf(S.text.who).name, px, py - bodyH - 8, 16, 'rgba(255,255,255,0.7)', 'center', 400);

    const shown = S.text.text.substring(0, S.text.shown);
    bubbleBox(ctx, S.text.who, shown, px + 40, py - bodyH - 30);
  }

  function drawDuel(ctx) {
    portrait(ctx, S.text.left, W * 0.24, H * 0.5, 300, 420, false);
    portrait(ctx, S.text.right, W * 0.76, H * 0.5, 300, 420, true);

    const shown = S.text.text.substring(0, S.text.shown);
    const boxW = 720;
    const x = W / 2 - boxW / 2;
    const y = H - 170;
    roundRectPath(ctx, x, y, boxW, 110, 12);
    ctx.fillStyle = 'rgba(240,240,240,0.94)';
    ctx.fill();

    ctx.font = '24px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
    const lines = wrapText(ctx, shown, boxW - 60);
    for (let i = 0; i < lines.length; i++) {
      label(ctx, lines[i], x + 30, y + 48 + i * 34, 24, '#101010', 'left', 600);
    }
  }

  function draw(ctx) {
    if (Game.mode !== 'story') return;
    drawBackground(ctx);

    if (S.card) drawCard(ctx);
    if (S.text) {
      if (S.text.mode === 'bubble') drawBubble(ctx);
      else if (S.text.mode === 'duel') drawDuel(ctx);
      else drawSay(ctx);
    }

    // 操作提示
    label(ctx, 'Enter / 空格 继续    Tab 跳过', W - 30, H - 18, 14,
          'rgba(255,255,255,0.45)', 'right', 400);

    // 黑场
    if (S.black > 0.001) {
      ctx.fillStyle = 'rgba(0,0,0,' + S.black.toFixed(3) + ')';
      ctx.fillRect(0, 0, W, H);
    }
  }

  return {
    start: start,
    update: update,
    draw: draw,
    skip: skip,
    state: S,
    forceAdvance: false,
    CHARS: CHARS
  };
})();
