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
    cg: null,             // CG 大图：{ art, label, t }
    flash: null,          // 闪白/闪黑：{ seq, i, f }
    portrait: null,       // 对话时右侧的说话者立绘：{ who, expr }
    shake: null,          // 画面震动：{ t, amp }
    leaving: false,       // 正在播「丝滑退出」
    leaveT: 0,
    title: null,          // 称号竖幅：{ who, title, t }
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

  // 表情差分：有 art/portrait/<id>_<expr>.png 就用它，没有就继续用基础立绘 / 占位块
  // 约定的 expr：eyes_closed（闭眼） / eyes_open（睁眼） / ready（备战） / shock（震惊） / shadow（黑影）
  const EXPR_LABEL = {
    '': '', eyes_closed: '闭眼', eyes_open: '睁眼', ready: '备战', shock: '震惊', shadow: '黑影',
    seated_closed: '坐·闭眼', seated_open: '坐·睁眼', stand_ready: '备战', stand: '起身',
    look_back: '回眸'
  };

  function artPathOf(c, expr) {
    if (!c.art) return null;
    if (!expr) return c.art;
    return c.art.replace(/\.png$/, '_' + expr + '.png');
  }

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
    S.cg = null;
    S.flash = null;
    S.shake = null;
    S.title = null;
    S.heroExpr = '';        // 蕾克常驻左侧，默认常态
    S.lastOther = null;     // 当前对话对象
    S.speaker = 'rek';
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
        S.text = {
          mode: 'say', who: c.who || '', text: c.text || '', shown: 0, acc: 0, pause: 0, t: 0,
          expr: c.expr || '', style: c.style || '', shake: !!c.shake, bump: !!c.bump
        };
        if (c.screenshake) S.shake = { t: c.screenshake, amp: c.shakeAmp || 6 };
        // show:true 时把说话者登记到舞台（蕾克常驻左侧，对方在右侧）
        if (c.show && c.who) {
          S.speaker = c.who;
          if (c.who === 'rek') S.heroExpr = c.expr || '';
          else S.lastOther = { who: c.who, expr: c.expr || '' };
        } else if (c.who && !c.show) {
          S.speaker = c.who;
        }
        break;
      case 'pose':
        // 只切表情，不说话
        if (c.who === 'rek') S.heroExpr = c.expr || '';
        else S.lastOther = { who: c.who, expr: c.expr || '' };
        S.speaker = c.who;
        S.framesLeft = c.frames || 30;
        break;
      case 'title':
        // 称号竖幅：出现 → 停留 → 滑出（比如「白之女王 · 观察者」）
        S.title = { who: c.who || '', title: c.title || '', t: 0 };
        S.framesLeft = c.frames || 150;
        break;
      case 'cg':
        S.cg = { art: c.art || null, label: c.label || 'CG', t: 0 };
        S.framesLeft = c.frames || 120;
        break;
      case 'flash':
        S.flash = {
          seq: c.seq || [{ c: 'white', f: 6 }, { c: 'black', f: 9 }, { c: 'white', f: 6 }],
          i: 0, f: 0
        };
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
        // 场景主题同步给战斗渲染：进了镜中世界，战斗背景也换成黑白森林
        Game.theme = (S.bg === 'mirror') ? 'mirror' : 'normal';
        break;
      case 'walk':
        // 交给玩家操控走一段，走到 untilX（或靠近 target 按 W）后回演出
        if (c.playerX != null && Game.player) Game.player.x = c.playerX;
        startWalk({
          untilX: c.untilX,
          next: c.next,
          target: c.target,
          npc: c.npc,
          npcX: c.npcX,
          bg: c.bg,
          cam: c.cam,
          props: c.props
        });
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
      case 'music':
        // 战斗曲：进 Boss 战之前的对话里就开始放
        if (typeof Music !== 'undefined') {
          if (c.name === 'stop') Music.stop(c.fade || 600);
          else Music.play(c.name);
        }
        break;
      case 'mirrorfx':
        // 镜之碎片：主题「镜」的视觉母题（玛丽苏被击败、梅贝尔升华等节点）
        if (typeof MirrorFx !== 'undefined') {
          MirrorFx.start({
            dur: c.dur || 110,
            count: c.count || 26,
            power: c.power || 1,
            x: c.x, y: c.y
          });
        }
        if (c.shake) {
          S.shake = { t: 12, amp: c.shake };
        }
        break;
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

  function skip(depth) {
    const d = depth || 0;
    if (!S.cmds || d > 30) return;
    // 本章剩下的指令里找战斗
    for (let i = S.idx; i < S.cmds.length; i++) {
      if (S.cmds[i].t === 'battle') { S.idx = i - 1; step(); return; }
    }
    // 找不到就跳到下一章继续找（可能隔着走位段）
    for (let i = S.idx; i < S.cmds.length; i++) {
      const c = S.cmds[i];
      if (c.t === 'next') { start(c.chapter); if (Game.mode === 'story') skip(d + 1); return; }
      if (c.t === 'walk' && c.next) { start(c.next); if (Game.mode === 'story') skip(d + 1); return; }
      if (c.t === 'end') { S.finished = true; Game.mode = 'win'; return; }
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
    S.cg = null;
    S.flash = null;
    S.shake = null;
    S.title = null;
    step();
  }

  // ------------------------------------------------------------ 更新

  function update(dt) {
    if (typeof MirrorFx !== 'undefined') MirrorFx.update();
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
    if (S.cg) S.cg.t++;
    if (S.shake && S.shake.t > 0) S.shake.t--;

    // 闪屏序列：白 → 黑 → 白，播完自动往下走
    if (S.flash) {
      S.flash.f++;
      if (S.flash.f >= S.flash.seq[S.flash.i].f) {
        S.flash.f = 0;
        S.flash.i++;
        if (S.flash.i >= S.flash.seq.length) { S.flash = null; step(); }
      }
      return;
    }
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
        if (cc && (cc.t === 'card' || cc.t === 'intro' || cc.t === 'bossIntro' || cc.t === 'pose' || cc.t === 'title')) requestLeave();
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
    const art = getArt(artPathOf(c, o.expr));

    const k = easeOutCubic(prog(S.t, o.inFrames || PORTRAIT_IN));
    const fromX = o.fromX || 0;
    const alpha = k;
    // 极轻的呼吸：只在立绘就位后叠加，幅度 2px
    const bob = Math.sin((Game.frame + (o.phase || 0) * 37) * 0.035) * 2;

    ctx.save();
    // 叠加在外层 alpha 上（非说话者会先被压暗，这里不能覆盖掉）
    ctx.globalAlpha = ctx.globalAlpha * alpha;
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
      const ex = EXPR_LABEL[o.expr || ''] || o.expr || '';
      label(ctx, c.name + (ex ? ' · ' + ex : ''), 0, 10, Math.min(42, h * 0.2), c.color, 'center', 700);
      label(ctx, '立绘占位', 0, 44, 15, 'rgba(255,255,255,0.3)', 'center', 400);
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

  // 说话者背后的一团柔光：不靠"提亮立绘"，改用背光区分
  function focusGlow(ctx, x, y, r) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, 'rgba(255,255,255,0.11)');
    g.addColorStop(0.55, 'rgba(255,255,255,0.045)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  // 双人对话构图：蕾克永远在左，对方在右；说话的一方亮，另一方压暗
  function drawSpeakerPortrait(ctx) {
    const heroExpr = S.heroExpr || '';
    const other = S.lastOther;          // { who, expr }
    const speaker = S.speaker || 'rek';

    // 说话者背光
    if (speaker === 'rek') focusGlow(ctx, W * 0.26, H * 0.5, 300);
    else focusGlow(ctx, W * 0.74, H * 0.5, 300);

    if (heroExpr !== null && heroExpr !== undefined) {
      const dim = speaker !== 'rek';
      ctx.save();
      ctx.globalAlpha = dim ? 0.60 : 1;
      portrait(ctx, 'rek', W * 0.26, H * 0.52, 380, 540,
               { expr: heroExpr, inFrames: 1, phase: 3 });
      ctx.restore();
    }

    if (other) {
      const dim = speaker === 'rek';
      const bump = S.text && S.text.bump ? Math.sin(Game.frame * 2.4) * 5 : 0;
      ctx.save();
      ctx.globalAlpha = dim ? 0.60 : 1;
      portrait(ctx, other.who, W * 0.74, H * 0.52 + bump, 380, 540,
               { expr: other.expr, inFrames: 1, flip: true, phase: 3 });
      ctx.restore();
    }
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

    // 名字签（表情差分标在名字后面，方便之后接立绘）
    if (S.text.who) {
      const c = charOf(S.text.who);
      const ex = EXPR_LABEL[S.text.expr || ''] || S.text.expr || '';
      const tag = c.name + (ex ? ' · ' + ex : '');
      ctx.font = '22px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
      const tagW = Math.max(140, ctx.measureText(tag).width + 36);
      roundRectPath(ctx, x + 24, y - 20, tagW, 40, 10);
      ctx.fillStyle = 'rgba(8,8,10,0.96)';
      ctx.fill();
      ctx.strokeStyle = hexToRgba(colorOf(S.text.who), 0.9);
      ctx.lineWidth = 2;
      ctx.stroke();
      label(ctx, tag, x + 24 + tagW / 2, y + 7, 22, colorOf(S.text.who), 'center', 700);
    }

    // 正文：红色台词 + 抖动
    const red = S.text.style === 'red';
    const shake = S.text.shake ? Math.sin(Game.frame * 1.9) * 2.2 : 0;
    ctx.font = '24px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
    const lines = wrapText(ctx, typedText(), w - 80);
    for (let i = 0; i < lines.length; i++) {
      label(ctx, lines[i], x + 40 + shake, y + 54 + i * 38, 24,
            red ? COLORS.player : '#f2f2f2', 'left', red ? 700 : 400);
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

  // CG 大图：有 art/cg/*.png 就整张铺满，没有就画占位（红法环）
  function drawCG(ctx) {
    const k = easeOutCubic(prog(S.cg.t, 14));
    const g = getArt(S.cg.art);

    ctx.save();
    ctx.globalAlpha = k;

    if (g) {
      const s = Math.max(W / g.naturalWidth, H / g.naturalHeight);
      const dw = g.naturalWidth * s;
      const dh = g.naturalHeight * s;
      ctx.drawImage(g, (W - dw) / 2, (H - dh) / 2, dw, dh);
    } else {
      ctx.fillStyle = '#050505';
      ctx.fillRect(0, 0, W, H);

      // 占位：一圈红色法环
      const cx = W / 2;
      const cy = H / 2;
      ctx.strokeStyle = hexToRgba(COLORS.player, 0.55);
      ctx.lineWidth = 3;
      for (let r = 120; r <= 260; r += 46) {
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();
      }
      // 环上刻度
      for (let i = 0; i < 24; i++) {
        const a = (i / 24) * Math.PI * 2 + Game.frame * 0.004;
        const r0 = 250;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0);
        ctx.lineTo(cx + Math.cos(a) * (r0 + 26), cy + Math.sin(a) * (r0 + 26));
        ctx.stroke();
      }
      // 中心一点白
      ctx.beginPath();
      ctx.arc(cx, cy, 6, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      ctx.fill();

      label(ctx, 'CG 占位 · ' + S.cg.label, W / 2, H - 36, 16, 'rgba(255,255,255,0.45)', 'center', 400);
    }
    ctx.restore();
  }

  function drawFlash(ctx) {
    if (!S.flash) return;
    const seg = S.flash.seq[S.flash.i];
    const rgb = seg.c === 'white' ? '255,255,255'
              : seg.c === 'green' ? '130,255,0'
              : '0,0,0';
    ctx.fillStyle = 'rgba(' + rgb + ',1)';
    ctx.fillRect(0, 0, W, H);
  }

  // 称号竖幅：只显示称号（例如「白之女王 · 观察者」），出现后停留再滑出
  function drawTitleBanner(ctx) {
    if (!S.title) return;
    const inK = easeOutCubic(prog(S.t, 16));
    const outK = S.leaving ? easeInOutQuad(prog(S.leaveT, LEAVE_OUT)) : 0;
    const slide = (1 - inK) * 200 + outK * 200;
    const alpha = inK * (1 - outK);

    const bw = 92;
    const bx = W - 60 - bw + slide;
    const by = 80;
    const bh = Math.max(150, 70 + (S.title.title || '').length * 44);

    ctx.save();
    ctx.globalAlpha = alpha;

    roundRectPath(ctx, bx, by, bw, bh, 10);
    ctx.fillStyle = 'rgba(8,8,10,0.86)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,0.75)';
    ctx.lineWidth = 2;
    ctx.stroke();

    vtext(ctx, S.title.title || '', bx + bw / 2, by + 34, 26, '#f0f0f0', 700);
    ctx.restore();
  }

  function draw(ctx) {
    if (Game.mode !== 'story') return;
    drawBackground(ctx);

    const outK = S.leaving ? easeInOutQuad(prog(S.leaveT, LEAVE_OUT)) : 0;
    // 画面震动（衰减正弦，比随机抖动更「有力」）
    let sx = 0, sy = 0;
    if (S.shake && S.shake.t > 0) {
      const k = S.shake.t / 12;
      sx = Math.sin(Game.frame * 2.3) * S.shake.amp * k;
      sy = Math.cos(Game.frame * 1.7) * S.shake.amp * 0.6 * k;
    }

    ctx.save();
    ctx.globalAlpha = 1 - outK;
    ctx.translate(sx, sy + outK * 10);

    if (S.card) drawCard(ctx);
    if (S.cg) drawCG(ctx);
    if (S.intro) drawIntro(ctx);
    if (S.title) drawTitleBanner(ctx);
    if (S.bossIntro) drawBossIntro(ctx);
    drawSpeakerPortrait(ctx);
    if (S.text) {
      if (S.text.mode === 'bubble') drawBubble(ctx);
      else if (S.text.mode === 'duel') drawDuel(ctx);
      else if (S.text.mode === 'letter') drawLetter(ctx);
      else drawSay(ctx);
    }

    ctx.restore();

    // 镜之碎片（主题「镜」）：盖在角色之上、UI 之下
    if (typeof MirrorFx !== 'undefined') MirrorFx.draw(ctx);

    label(ctx, 'Enter / 空格 继续    Tab 跳过', W - 30, H - 16, 13,
          'rgba(255,255,255,0.35)', 'right', 400);

    if (S.black > 0.001) {
      ctx.fillStyle = 'rgba(0,0,0,' + S.black.toFixed(3) + ')';
      ctx.fillRect(0, 0, W, H);
    }

    // 闪屏盖在所有东西上面（包括黑场）
    drawFlash(ctx);
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
