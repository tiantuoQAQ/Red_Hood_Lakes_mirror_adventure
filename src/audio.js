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

    graze: function () {
      tone(1500, 2100, 0.05, 'triangle', 0.045);
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
