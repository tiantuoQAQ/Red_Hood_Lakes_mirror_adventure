'use strict';

// 演出系统（过场）：读 STORY 里的指令，播三种表现形式。
//
//   ① 章节卡 card     —— 立绘 + 底部两行字幕，带缓慢推近
//   ② 场景气泡 bubble —— 小人站在场上，头顶带名字的对话框（弹入 + 尾巴）
//   ③ 双立绘对峙 duel —— 左右立绘从两侧滑入，对话条从下浮起
//   另有通用底部对话框 say。
//
// 手感原则（这块是卖点，别写回去了）：
//   - 任何演出元素都要「动起来」，不做硬切：滑入 + 淡入 + 缓动
//   - 输入 0 延迟：打字中按键立刻补完当前句，再按才翻页
//   - 标点有停顿，读起来才有节奏
//   - 立绘有极轻微的呼吸浮动，画面不死
//
// 立绘还没出时画占位色块；把图丢进 art/portrait/ 就自动替换。

const Cutscene = (function () {
  // ---- 节奏参数（想调手感改这里）----
  const CPS = 0.9;              // 每帧打几个字（60 帧 ≈ 54 字/秒）
  const PAUSE = {               // 标点停顿帧数
    '。': 14, '，': 7, '、': 5, '！': 14, '？': 14, '…': 9, '—': 7, '：': 8, '；': 9
  };
  const BOX_IN = 9;             // 对话框浮起帧数
  const PORTRAIT_IN = 14;       // 立绘滑入帧数
  const CARD_LINE1_IN = 18;
  const CARD_LINE2_IN = 16;

  const CHARS = {
    rek:         { name: '蕾克',   title: '小红帽',        color: '#ff0000', art: 'art/portrait/rek.png' },
    rek_crimson: { name: '猩红魔姬', title: '另一个她',      color: '#c00000', art: 'art/portrait/crimson.png' },
    norden:      { name: '诺登',   title: '白之兔',        color: '#ff5050', art: 'art/portrait/norden.png' },
    marysue:     { name: '玛丽苏',  title: '幕后黑手',      color: '#00baff', art: 'art/portrait/marysue.png' },
    mabel:       { name: '梅贝尔',  title: '虚空少女',      color: '#cfcfcf', art: 'art/portrait/mabel.png' }
  };

  const BGS = {
    night:  ['#0b0b0b', '#141414'],
    forest: ['#0d0d0d', '#171a17'],
    mirror: ['#05070b', '#0d1420']
  };

  const S = {
    chapterId: null,
    cmds: null,
    idx: -1,
    t: 0,                 // 当前指令已经过的帧
    black: 0,             // 当前黑场不透明度
    fade: null,           // { from, to, dur, t }
    bg: 'night',
    text: null,
    card: null,
    intro: null,          // 角色登场介绍：{ id }
    bossIntro: null,      // 战斗前的放大特写：{ id }
    leaving: false,       // 正在播「丝滑退出」
    leaveT: 0,
    framesLeft: 0,
    battleNext: null,
    finished: false,
    lastAdvanceFrame: -99 // 防连点：两次推进之间至少隔几帧
  };

  // ------------------------------------------------------------ 缓动

  function clamp01(v) { return v < 0 ? 0 : (v > 1 ? 1 : v); }
  function easeOutCubic(v) { return 1 - Math.pow(1 - v, 3); }
  function easeInOutQuad(v) { return v < 0.5 ? 2 * v * v : 1 - Math.pow(-2 * v + 2, 2) / 2; }
  function easeOutBack(v) {
    const c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * Math.pow(v - 1, 3) + c1 * Math.pow(v - 1, 2);
  }
  function prog(t, dur) { return clamp01(t / dur); }

  function charOf(id) { return CHARS[id] || { name: id, color: '#888888', art: null }; }
  function colorOf(id) { return charOf(id).color; }

  // ------------------------------------------------------------ 立绘

  const PORTRAITS = {};
  function getArt(path) {
    if (!path || typeof Image === 'undefined') return null;
    let img = PORTRAITS[path];
    if (!img) { img = new Image(); img.src = path; PORTRAITS[path] = img; }
    return (img.complete && img.naturalWidth > 0) ? img : null;
  }

  // ------------------------------------------------------------ 流程

  function start(chapterId) {
    const ch = STORY[chapterId];
    if (!ch) { console.warn('未知章节: ' + chapterId); return false; }
    S.chapterId = chapterId;
    S.cmds = ch.cmds;
    S.idx = -1;
    S.t = 0;
    S.text = null;
    S.card = null;
    S.intro = null;
    S.bossIntro = null;
    S.leaving = false;
    S.leaveT = 0;
    S.framesLeft = 0;
    S.battleNext = null;
    S.finished = false;
    S.fade = null;
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
        S.fade = {
          from: S.black,
          to: c.to === 'black' ? 1 : 0,
          dur: Math.max(1, c.frames || 30),
          t: 0
        };
        break;
      case 'wait':
        S.framesLeft = c.frames || 30;
        break;
      case 'card':
        S.card = { line1: c.line1 || '', line2: c.line2 || '', t: 0 };
        S.framesLeft = c.frames || 160;
        break;
      case 'say':
        S.text = { mode: 'say', who: c.who || '', text: c.text || '', shown: 0, acc: 0, pause: 0, t: 0 };
        break;
      case 'bubble':
        S.text = { mode: 'bubble', who: c.who || '', text: c.text || '', shown: 0, acc: 0, pause: 0, t: 0 };
        break;
      case 'duel':
        S.text = {
          mode: 'duel', who: '', text: c.text || '', shown: 0, acc: 0, pause: 0, t: 0,
          left: c.left, right: c.right, hint: c.hint || ''
        };
        break;
      case 'letter':
        // 信件：浅色纸面，多行，逐字打出；按键翻到下一句（整段打完再按键继续）
        S.text = {
          mode: 'letter', who: '',
          text: (c.lines || []).join('\n'),
          shown: 0, acc: 0, pause: 0, t: 0
        };
        break;
      case 'scene':
        S.bg = c.bg || 'night';
        break;
      case 'walk':
        // 交给玩家操控走一段，走到 untilX 后回演出
        startWalk({ untilX: c.untilX, next: c.next });
        return;
      case 'intro':
        // 新角色登场：竖幅「称号 + 名字」，丝滑滑入，按键后再丝滑滑出
        S.intro = { id: c.id };
        if (c.frames) S.framesLeft = c.frames;
        break;
      case 'bossIntro':
        // 战斗前特写：镜头推近 + BATTLE START! + 名字
        S.bossIntro = { id: c.id };
        S.framesLeft = c.frames || 165;
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
          mode: 'say', who: '', shown: 0, acc: 0, pause: 0, t: 0,
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

  function finishChapter() { Game.mode = 'title'; }

  function textDone() { return !S.text || S.text.shown >= S.text.text.length; }

  function skip() {
    if (!S.cmds) return;
    for (let i = S.idx; i < S.cmds.length; i++) {
      if (S.cmds[i].t === 'battle') { S.idx = i - 1; step(); return; }
    }
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

  const LEAVE_OUT = 10;   // 丝滑退出帧数

  function requestLeave() {
    if (S.leaving) return;
    S.leaving = true;
    S.leaveT = 0;
  }

  function finishLeave() {
    S.leaving = false;
    S.leaveT = 0;
    S.text = null;
    S.card = null;
    S.intro = null;
    S.bossIntro = null;
    step();
  }

  // ------------------------------------------------------------ 更新

  function update(dt) {
    const adv = wantsAdvance(Cutscene.forceAdvance);
    Cutscene.forceAdvance = false;

    if (Input.pressed('skip')) { skip(); return; }

    // 退出动画优先：播完才进入下一条
    if (S.leaving) {
      S.leaveT++;
      if (S.leaveT >= LEAVE_OUT) finishLeave();
      return;
    }

    S.frame = (S.frame || 0) + 1;
    S.t++;
    if (S.card) S.card.t++;

    // 黑场：缓动过渡，不是线性
    if (S.fade) {
      S.fade.t++;
      const k = easeInOutQuad(prog(S.fade.t, S.fade.dur));
      S.black = S.fade.from + (S.fade.to - S.fade.from) * k;
      if (S.fade.t >= S.fade.dur) {
        S.black = S.fade.to;
        S.fade = null;
      }
    }

    // 打字机：标点会停一下
    if (S.text && S.text.shown < S.text.text.length) {
      S.text.t++;
      if (S.text.pause > 0) {
        S.text.pause--;
      } else {
        S.text.acc += CPS * dt * 60;
        while (S.text.acc >= 1 && S.text.shown < S.text.text.length) {
          S.text.acc -= 1;
          const ch = S.text.text[S.text.shown];
          S.text.shown++;
          if (PAUSE[ch]) { S.text.pause = PAUSE[ch]; break; }
        }
      }
    }

    // 自动推进的指令
    if (S.framesLeft > 0) {
      S.framesLeft--;
      if (S.framesLeft === 0) {
        const cc = current();
        if (cc && (cc.t === 'card' || cc.t === 'intro' || cc.t === 'bossIntro')) requestLeave();
        else if (cc && cc.t === 'wait') step();
      }
      return;
    }

    // 黑场还没到位、字还没打完，都先等着
    if (S.fade) return;

    // 纯转场指令（黑场、切场景）不需要玩家按键，播完自动走
    const c = current();
    if (c && (c.t === 'fade' || c.t === 'scene')) { S.text = null; step(); return; }

    if (!textDone()) return;

    // 防连点：一次推进至少隔 4 帧，避免手滑跳两页
    if (adv && S.frame - S.lastAdvanceFrame > 4) {
      S.lastAdvanceFrame = S.frame;
      requestLeave();
    }
  }

  // ------------------------------------------------------------ 绘制

  function drawBackground(ctx) {
    const pair = BGS[S.bg] || BGS.night;
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, pair[0]);
    g.addColorStop(1, pair[1]);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    if (S.bg === 'mirror') {
      const rg = ctx.createLinearGradient(MIRROR_X - 140, 0, MIRROR_X + 140, 0);
      rg.addColorStop(0, 'rgba(255,255,255,0)');
      rg.addColorStop(0.5, 'rgba(255,255,255,0.055)');
      rg.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = rg;
      ctx.fillRect(MIRROR_X - 140, 0, 280, GROUND_Y);
    }

    ctx.fillStyle = 'rgba(255,255,255,0.05)';
    ctx.fillRect(0, GROUND_Y, W, 2);

    // 四周渐晕：把注意力压到中间
    const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95);
    vg.addColorStop(0, 'rgba(0,0,0,0)');
    vg.addColorStop(1, 'rgba(0,0,0,0.55)');
    ctx.fillStyle = vg;
    ctx.fillRect(0, 0, W, H);
  }

  // 立绘：滑入 + 淡入 + 呼吸浮动；没图就画占位块
  function portrait(ctx, id, cx, cy, w, h, opt) {
    const o = opt || {};
    const c = charOf(id);
    const art = getArt(c.art);

    const k = easeOutCubic(prog(S.t, o.inFrames || PORTRAIT_IN));
    const fromX = o.fromX || 0;
    const alpha = k;
    // 极轻的呼吸：只在立绘就位后叠加，幅度 2px
    const bob = Math.sin((Game.frame + (o.phase || 0) * 37) * 0.035) * 2;

    ctx.save();
    ctx.globalAlpha = alpha;
    ctx.translate(cx + fromX * (1 - k), cy + bob);

    if (art) {
      const scl = h / art.naturalHeight;
      const dw = art.naturalWidth * scl;
      if (o.flip) ctx.scale(-1, 1);
      ctx.drawImage(art, -dw / 2, -h / 2, dw, h);
    } else {
      roundRectPath(ctx, -w / 2, -h / 2, w, h, 18);
      ctx.fillStyle = hexToRgba(c.color, 0.13);
      ctx.fill();
      ctx.strokeStyle = hexToRgba(c.color, 0.45);
      ctx.lineWidth = 3;
      ctx.stroke();
      label(ctx, c.name, 0, 10, Math.min(46, h * 0.22), c.color, 'center', 700);
      label(ctx, '立绘占位', 0, 46, 16, 'rgba(255,255,255,0.3)', 'center', 400);
    }
    ctx.restore();
  }

  // 打字机文本
  function typedText() {
    if (!S.text) return '';
    return S.text.text.substring(0, S.text.shown);
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

  // 对话框里的「继续」箭头：呼吸 + 上下浮动
  function nextArrow(ctx, x, y) {
    const a = 0.45 + 0.35 * (0.5 + 0.5 * Math.sin(Game.frame * 0.18));
    const dy = Math.sin(Game.frame * 0.18) * 3;
    ctx.beginPath();
    ctx.moveTo(x - 8, y + dy);
    ctx.lineTo(x + 8, y + dy);
    ctx.lineTo(x, y + 10 + dy);
    ctx.closePath();
    ctx.fillStyle = 'rgba(255,255,255,' + a.toFixed(2) + ')';
    ctx.fill();
  }

  function drawCard(ctx) {
    if (!S.card) return;
    const t = S.card.t;

    // 立绘缓慢推近 1.00 → 1.02
    const zoom = 1 + 0.02 * easeOutCubic(prog(t, 200));
    ctx.save();
    ctx.translate(W / 2, H * 0.38);
    ctx.scale(zoom, zoom);
    ctx.translate(-W / 2, -H * 0.38);
    portrait(ctx, 'rek', W / 2, H * 0.38, 300, 380, { inFrames: 22, phase: 1 });
    ctx.restore();

    const a1 = easeOutCubic(prog(t, CARD_LINE1_IN));
    const a2 = easeOutCubic(prog(t - 8, CARD_LINE2_IN));
    const rise = (1 - a1) * 10;

    ctx.save();
    ctx.globalAlpha = a1;
    label(ctx, S.card.line1, W / 2, H * 0.79 + rise, 42, 'rgba(255,255,255,0.96)', 'center', 700);
    ctx.restore();

    ctx.save();
    ctx.globalAlpha = a2;
    label(ctx, S.card.line2, W / 2, H * 0.79 + 48 + (1 - a2) * 8, 30,
          'rgba(255,255,255,0.72)', 'center', 500);
    ctx.restore();
  }

  function drawBubble(ctx) {
    const k = easeOutBack(prog(S.t, 10));
    const px = 360;
    const py = GROUND_Y;

    // 小人（占位）轻微上下呼吸
    const bob = Math.sin(Game.frame * 0.05) * 1.5;
    ctx.save();
    ctx.globalAlpha = clamp01(S.t / 12);
    ctx.fillStyle = hexToRgba(COLORS.player, 0.9);
    roundRectPath(ctx, px - 26, py - 110 + bob, 52, 110, 10);
    ctx.fill();
    ctx.restore();

    ctx.save();
    ctx.translate(px + 40, py - 150);
    ctx.scale(0.92 + 0.08 * k, 0.92 + 0.08 * k);
    ctx.globalAlpha = clamp01(S.t / 8);
    bubbleBox(ctx, S.text.who, typedText(), 0, 0, px);
    ctx.restore();

    if (textDone()) nextArrow(ctx, px + 40 + 40, py - 150 - 6);
  }

  // 气泡框：左上角是名字标签，左下角带一个指向角色的尾巴
  function bubbleBox(ctx, who, shownText, x, y, tailToX) {
    const padX = 22;
    const padY = 16;
    const maxW = 560;
    ctx.font = '22px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
    const lines = wrapText(ctx, shownText, maxW);
    const lineH = 34;
    const w = Math.min(maxW + padX * 2, Math.max(240, maxLineWidth(ctx, lines) + padX * 2));
    const h = lines.length * lineH + padY * 2;

    // 尾巴
    ctx.beginPath();
    ctx.moveTo(6, y);
    ctx.lineTo(30, y);
    ctx.lineTo(-8, y + 26);
    ctx.closePath();
    ctx.fillStyle = 'rgba(8,8,10,0.94)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.8)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 正文框
    roundRectPath(ctx, x, y - h, w, h, 12);
    ctx.fillStyle = 'rgba(8,8,10,0.94)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.8)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 名字签（压在框左上角）
    ctx.font = '18px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
    const nw = Math.max(84, ctx.measureText(charOf(who).name).width + 28);
    roundRectPath(ctx, x, y - h - 26, nw, 34, 8);
    ctx.fillStyle = '#0a0a0c';
    ctx.fill();
    ctx.strokeStyle = hexToRgba(colorOf(who), 0.85);
    ctx.lineWidth = 2;
    ctx.stroke();
    label(ctx, charOf(who).name, x + nw / 2, y - h - 2, 19, colorOf(who), 'center', 700);

    for (let i = 0; i < lines.length; i++) {
      label(ctx, lines[i], x + padX, y - h + padY + 24 + i * lineH, 22, '#f0f0f0', 'left', 400);
    }
    void tailToX;
  }

  function drawSay(ctx) {
    const k = easeOutCubic(prog(S.text.t, BOX_IN));
    const boxH = 156;
    const yBase = H - boxH - 34;
    const y = yBase + (1 - k) * 26;
    const x = 120;
    const w = W - 240;

    ctx.save();
    ctx.globalAlpha = k;

    // 框
    roundRectPath(ctx, x, y, w, boxH, 14);
    ctx.fillStyle = 'rgba(8,8,10,0.93)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.22)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 顶部一条角色色高光，比纯白框更「有身份」
    if (S.text.who) {
      const g = ctx.createLinearGradient(x, y, x + w, y);
      g.addColorStop(0, hexToRgba(colorOf(S.text.who), 0.85));
      g.addColorStop(0.35, hexToRgba(colorOf(S.text.who), 0.15));
      g.addColorStop(1, hexToRgba(colorOf(S.text.who), 0));
      ctx.fillStyle = g;
      ctx.fillRect(x + 2, y + 2, w - 4, 3);
    }

    // 名字签
    if (S.text.who) {
      roundRectPath(ctx, x + 24, y - 20, 140, 40, 10);
      ctx.fillStyle = 'rgba(8,8,10,0.96)';
      ctx.fill();
      ctx.strokeStyle = hexToRgba(colorOf(S.text.who), 0.9);
      ctx.lineWidth = 2;
      ctx.stroke();
      label(ctx, charOf(S.text.who).name, x + 94, y + 7, 22, colorOf(S.text.who), 'center', 700);
    }

    // 正文
    ctx.font = '24px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
    const lines = wrapText(ctx, typedText(), w - 80);
    for (let i = 0; i < lines.length; i++) {
      label(ctx, lines[i], x + 40, y + 54 + i * 38, 24, '#f2f2f2', 'left', 400);
    }
    ctx.restore();

    if (textDone()) nextArrow(ctx, x + w - 34, y + boxH - 26);
  }

  function drawDuel(ctx) {
    const lk = easeOutCubic(prog(S.t, 16));
    const rk = easeOutCubic(prog(S.t - 4, 16));

    ctx.save();
    ctx.globalAlpha = lk;
    ctx.translate((1 - lk) * -70, 0);
    portrait(ctx, S.text.left, W * 0.25, H * 0.5, 300, 430, { inFrames: 1, phase: 0 });
    ctx.restore();

    ctx.save();
    ctx.globalAlpha = rk;
    ctx.translate((1 - rk) * 70, 0);
    portrait(ctx, S.text.right, W * 0.75, H * 0.5, 300, 430, { inFrames: 1, flip: true, phase: 2 });
    ctx.restore();

    const bk = easeOutCubic(prog(S.t, 14));
    const boxW = 760;
    const x = W / 2 - boxW / 2;
    const y = H - 176 + (1 - bk) * 30;

    ctx.save();
    ctx.globalAlpha = bk;
    roundRectPath(ctx, x, y, boxW, 112, 14);
    ctx.fillStyle = 'rgba(240,240,240,0.95)';
    ctx.fill();

    ctx.font = '24px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
    const lines = wrapText(ctx, typedText(), boxW - 64);
    for (let i = 0; i < lines.length; i++) {
      label(ctx, lines[i], x + 32, y + 50 + i * 34, 24, '#101010', 'left', 600);
    }
    ctx.restore();

    if (textDone()) nextArrow(ctx, x + boxW - 30, y + 112 - 24);
  }

  // 竖排文字（称号用）
  function vtext(ctx, text, x, y, size, color, weight) {
    ctx.font = (weight || 700) + ' ' + size + 'px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = color;
    for (let i = 0; i < text.length; i++) {
      ctx.fillText(text[i], x, y + i * (size + 8));
    }
  }

  // 新角色登场：右侧竖幅「名字 + 称号」，滑入 / 滑出
  function drawIntro(ctx) {
    const c = charOf(S.intro.id);
    const inK = easeOutCubic(prog(S.t, 16));
    const outK = S.leaving ? easeInOutQuad(prog(S.leaveT, LEAVE_OUT)) : 0;
    const slide = (1 - inK) * 190 + outK * 190;
    const alpha = inK * (1 - outK);

    const bw = 100;
    const bx = W - 52 - bw + slide;
    const by = 64;
    const bodyLen = Math.max(c.name.length, (c.title || '').length);
    const bh = Math.max(140, 74 + bodyLen * 42);

    ctx.save();
    ctx.globalAlpha = alpha;

    // 竖幅底
    roundRectPath(ctx, bx, by, bw, bh, 10);
    ctx.fillStyle = 'rgba(8,8,10,0.86)';
    ctx.fill();
    ctx.strokeStyle = hexToRgba(c.color, 0.9);
    ctx.lineWidth = 2;
    ctx.stroke();

    // 名字（竖排，主色）
    vtext(ctx, c.name, bx + bw / 2, by + 34, 32, c.color, 700);
    // 称号（竖排，左侧，淡一点）
    if (c.title) vtext(ctx, c.title, bx - 26, by + 26, 19, 'rgba(255,255,255,0.7)', 500);

    ctx.restore();
  }

  // 战斗前特写：镜头推近 + BATTLE START! + 名字
  function drawBossIntro(ctx) {
    const c = charOf(S.bossIntro.id);
    const t = S.t;
    const inK = easeOutCubic(prog(t, 18));
    const zoom = 0.88 + 0.22 * easeOutCubic(prog(t, 70));
    const outK = S.leaving ? easeInOutQuad(prog(S.leaveT, LEAVE_OUT)) : 0;

    // 立绘推近（略微偏上，给底部文字留位置）
    ctx.save();
    ctx.globalAlpha = inK * (1 - outK);
    ctx.translate(W / 2, H * 0.38);
    ctx.scale(zoom + outK * 0.1, zoom + outK * 0.1);
    ctx.translate(-W / 2, -H * 0.38);
    portrait(ctx, S.bossIntro.id, W / 2, H * 0.38, 360, 520, { inFrames: 1 });
    ctx.restore();

    // 底部压暗，保证文字可读
    const gg = ctx.createLinearGradient(0, H * 0.58, 0, H);
    gg.addColorStop(0, 'rgba(0,0,0,0)');
    gg.addColorStop(1, 'rgba(0,0,0,0.9)');
    ctx.fillStyle = gg;
    ctx.fillRect(0, H * 0.58, W, H * 0.42);

    // BATTLE START!
    const sK = easeOutBack(prog(t - 12, 14));
    ctx.save();
    ctx.globalAlpha = clamp01((t - 12) / 10) * (1 - outK);
    ctx.translate(W / 2, H * 0.78);
    ctx.scale(0.86 + 0.14 * sK, 0.86 + 0.14 * sK);
    ctx.font = '800 64px "Segoe UI", system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.lineWidth = 12;
    ctx.strokeStyle = 'rgba(0,0,0,0.9)';
    ctx.strokeText('BATTLE START!', 0, 0);
    ctx.fillStyle = '#ffffff';
    ctx.fillText('BATTLE START!', 0, 0);
    ctx.restore();

    // 名字
    const nK = clamp01((t - 24) / 12) * (1 - outK);
    ctx.save();
    ctx.globalAlpha = nK;
    label(ctx, c.name, W / 2, H * 0.89, 36, c.color, 'center', 700);
    ctx.restore();
  }

  function drawLetter(ctx) {
    const k = easeOutCubic(prog(S.text.t, 14));
    const w = 720;
    const h = 540;
    const x = W / 2 - w / 2;
    const y = 110 + (1 - k) * 22;

    ctx.save();
    ctx.globalAlpha = k;

    // 纸
    roundRectPath(ctx, x, y, w, h, 8);
    ctx.fillStyle = 'rgba(233,233,233,0.97)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(0,0,0,0.25)';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 左上角一点压痕，别让纸太干净
    ctx.fillStyle = 'rgba(0,0,0,0.05)';
    ctx.fillRect(x + 24, y + 20, 120, 2);

    ctx.font = '24px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
    const lines = wrapText(ctx, typedText(), w - 96);
    for (let i = 0; i < lines.length; i++) {
      label(ctx, lines[i], x + 48, y + 76 + i * 44, 24, '#1a1a1a', 'left', 400);
    }
    ctx.restore();

    if (textDone()) nextArrow(ctx, x + w - 34, y + h - 30);
  }

  function draw(ctx) {
    if (Game.mode !== 'story') return;
    drawBackground(ctx);

    const outK = S.leaving ? easeInOutQuad(prog(S.leaveT, LEAVE_OUT)) : 0;

    ctx.save();
    ctx.globalAlpha = 1 - outK;
    ctx.translate(0, outK * 10);

    if (S.card) drawCard(ctx);
    if (S.intro) drawIntro(ctx);
    if (S.bossIntro) drawBossIntro(ctx);
    if (S.text) {
      if (S.text.mode === 'bubble') drawBubble(ctx);
      else if (S.text.mode === 'duel') drawDuel(ctx);
      else if (S.text.mode === 'letter') drawLetter(ctx);
      else drawSay(ctx);
    }

    ctx.restore();

    label(ctx, 'Enter / 空格 继续    Tab 跳过', W - 30, H - 16, 13,
          'rgba(255,255,255,0.35)', 'right', 400);

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
