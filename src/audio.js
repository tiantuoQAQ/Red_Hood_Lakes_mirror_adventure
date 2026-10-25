'use strict';

// 程序化音效：全部用 WebAudio 合成，不加载任何音频文件。
// 浏览器策略要求音频在用户交互后启动，所以由首次按键调用 unlock()。

const Sfx = (function () {
  let ctx = null;
  let master = null;
  let dead = false;
  let muted = false;

  function unlock() {
    if (ctx || dead) {
      if (ctx && ctx.state === 'suspended') ctx.resume();
      return;
    }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) {
      dead = true;
      return;
    }
    try {
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = 0.30;
      master.connect(ctx.destination);
    } catch (e) {
      dead = true;
    }
  }

  function ready() {
    return ctx !== null && !muted && ctx.state !== 'closed';
  }

  // 音高可滑动的短音
  function tone(f0, f1, dur, type, gain, delay) {
    if (!ready()) return;
    const t0 = ctx.currentTime + (delay || 0);
    const o = ctx.createOscillator();
    o.type = type || 'square';
    o.frequency.setValueAtTime(f0, t0);
    if (f1 && f1 !== f0) {
      o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t0 + dur);
    }
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(gain, t0 + 0.006);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g);
    g.connect(master);
    o.start(t0);
    o.stop(t0 + dur + 0.03);
  }

  // 带通噪声，用于冲击与摩擦
  function noise(dur, gain, freq, q) {
    if (!ready()) return;
    const len = Math.max(1, Math.floor(ctx.sampleRate * dur));
    const buf = ctx.createBuffer(1, len, ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < len; i++) {
      data[i] = (Math.random() * 2 - 1) * (1 - i / len);
    }
    const src = ctx.createBufferSource();
    src.buffer = buf;

    const f = ctx.createBiquadFilter();
    f.type = 'bandpass';
    f.frequency.value = freq;
    f.Q.value = q || 1;

    const g = ctx.createGain();
    g.gain.value = gain;

    src.connect(f);
    f.connect(g);
    g.connect(master);
    src.start();
  }

  return {
    unlock: unlock,

    shoot: function () {
      tone(980, 620, 0.045, 'square', 0.055);
    },

    bossHit: function () {
      noise(0.05, 0.10, 1800, 1.2);
      tone(240, 150, 0.07, 'triangle', 0.07);
    },

    // 擦弹音高随连击升高：连击越久，声音越尖，玩家不用看 UI 也知道自己在连
    graze: function (chain) {
      const n = Math.min(chain || 1, 14);
      const base = 1500 + n * 70;
      tone(base, base * 1.35, 0.05, 'triangle', 0.045);
    },

    dash: function () {
      noise(0.13, 0.09, 2600, 0.8);
      tone(700, 320, 0.09, 'sine', 0.05);
    },

    ballOn: function () {
      tone(260, 980, 0.16, 'sine', 0.10);
      noise(0.10, 0.05, 3200, 1.5);
    },

    ballOff: function () {
      tone(980, 280, 0.13, 'sine', 0.08);
      noise(0.09, 0.07, 900, 1.0);
    },

    hurt: function () {
      noise(0.20, 0.16, 500, 0.7);
      tone(190, 55, 0.32, 'sawtooth', 0.14);
    },

    phase: function () {
      tone(110, 220, 0.45, 'square', 0.10);
      tone(165, 330, 0.45, 'sine', 0.07, 0.03);
      noise(0.30, 0.06, 1200, 0.5);
    },

    skill: function () {
      tone(200, 1400, 0.35, 'sine', 0.12);
      noise(0.28, 0.12, 2200, 0.9);
    },

    // 预警：两声上行的短提示，让玩家知道「有东西要来了」
    warn: function () {
      tone(520, 640, 0.07, 'square', 0.05);
      tone(700, 880, 0.08, 'square', 0.05, 0.10);
    },

    // 激光 / 穿刺发射：高频噪声 + 下沉音
    lance: function () {
      noise(0.22, 0.14, 3600, 0.9);
      tone(900, 180, 0.26, 'sawtooth', 0.10);
    },

    dead: function () {
      tone(240, 40, 0.7, 'sawtooth', 0.16);
      noise(0.5, 0.10, 400, 0.6);
    },

    win: function () {
      tone(523, 523, 0.12, 'triangle', 0.09, 0);
      tone(659, 659, 0.12, 'triangle', 0.09, 0.11);
      tone(784, 784, 0.22, 'triangle', 0.10, 0.22);
      tone(1046, 1046, 0.34, 'sine', 0.10, 0.34);
    },

    toggleMute: function () {
      muted = !muted;
      return muted;
    },

    isMuted: function () {
      return muted;
    }
  };
})();

// ---------------------------------------------------------------- 战斗 BGM
// 两首战斗曲随包分发（mp4 里的音轨，浏览器原生解码）。
// 由剧情命令 { t:'music', name:'crimson' } 触发：打完一段对话、进战斗前就开始响。
const Music = (function () {
  const TRACKS = {
    crimson: 'audio/crimson_bgm.mp4',    // 黑之裁判 —— 猩红魔姬
    marysue: 'audio/marysue_bgm.mp4'     // 玛丽·安 —— 玛丽苏
  };
  const VOLUME = 0.55;
  const FADE_MS = 800;

  let cur = null;
  let curName = null;
  let wantName = null;      // 记住「应该放哪首」，等用户交互后补播
  let muted = false;
  let timer = null;

  function clearTimer() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  function ramp(el, to, ms, done) {
    clearTimer();
    const from = el.volume;
    const t0 = Date.now();
    timer = setInterval(function () {
      const k = Math.min(1, (Date.now() - t0) / ms);
      el.volume = Math.max(0, Math.min(1, from + (to - from) * k));
      if (k >= 1) { clearTimer(); if (done) done(); }
    }, 40);
  }

  function make(name) {
    const el = new Audio(TRACKS[name]);
    el.loop = true;
    el.preload = 'auto';
    el.volume = 0;
    return el;
  }

  function play(name) {
    if (!TRACKS[name]) return;
    if (typeof Audio === 'undefined') return;   // node 测试环境没有 Audio
    wantName = name;
    if (curName === name && cur && !cur.paused) return;

    if (!cur) cur = make(name);
    else if (curName !== name) {
      cur.pause();
      cur.src = TRACKS[name];
      cur.load();
    }
    curName = name;
    cur.volume = 0;
    const p = cur.play();
    if (p && p.catch) {
      p.catch(function () { /* 浏览器要求用户手势，交给重试监听 */ });
    }
    if (!muted) ramp(cur, VOLUME, FADE_MS);
  }

  function stop(ms) {
    wantName = null;
    if (!cur) return;
    ramp(cur, 0, ms || 500, function () {
      if (cur) { cur.pause(); cur.currentTime = 0; }
    });
  }

  function retry() {
    if (!wantName || !cur) return;
    if (cur.paused) {
      cur.volume = 0;
      const p = cur.play();
      if (p && p.catch) p.catch(function () {});
      if (!muted) ramp(cur, VOLUME, 400);
    }
  }

  // 首次按键/点击后再尝试播放（自动播放策略）
  if (typeof window !== 'undefined') {
    window.addEventListener('keydown', retry, true);
    window.addEventListener('pointerdown', retry, true);
  }

  return {
    play: play,
    stop: stop,
    retry: retry,
    name: function () { return curName; },
    toggleMute: function () {
      muted = !muted;
      if (cur) cur.volume = muted ? 0 : VOLUME;
      return muted;
    },
    isMuted: function () { return muted; }
  };
})();
