'use strict';

// 输入层：统一「按住」与「本帧按下」两种查询，并保留按键帧号用于输入缓冲判定。
const Input = (function () {
  const codes = {
    left: ['ArrowLeft', 'KeyA'],
    right: ['ArrowRight', 'KeyD'],
    up: ['ArrowUp', 'KeyW'],
    down: ['ArrowDown', 'KeyS'],
    jump: ['Space'],
    dash: ['ShiftLeft', 'ShiftRight', 'KeyK'],
    fire: ['KeyJ', 'KeyZ'],
    skill: ['KeyL', 'KeyX'],
    start: ['Enter'],
    restart: ['KeyR'],
    pause: ['KeyP'],
    toggleHitbox: ['F1'],
    togglePanel: ['F2'],
    mute: ['KeyM']
  };

  const held = Object.create(null);
  const pressedAt = Object.create(null);
  const reserved = Object.create(null);
  let frame = 0;

  for (const action in codes) {
    for (const code of codes[action]) reserved[code] = true;
  }

  window.addEventListener('keydown', function (e) {
    if (reserved[e.code]) e.preventDefault();
    if (!e.repeat) pressedAt[e.code] = frame;
    held[e.code] = true;
  });

  window.addEventListener('keyup', function (e) {
    held[e.code] = false;
  });

  // 失焦时清空，避免「角色自己一直往左跑」
  window.addEventListener('blur', function () {
    for (const code in held) held[code] = false;
  });

  function isHeld(action) {
    const list = codes[action];
    if (!list) return false;
    for (let i = 0; i < list.length; i++) {
      if (held[list[i]]) return true;
    }
    return false;
  }

  // within: 判定窗口帧数，1 = 仅本帧
  function wasPressed(action, within) {
    const list = codes[action];
    if (!list) return false;
    const window_ = within === undefined ? 1 : within;
    for (let i = 0; i < list.length; i++) {
      const t = pressedAt[list[i]];
      if (t !== undefined && frame - t < window_) return true;
    }
    return false;
  }

  function consume(action) {
    const list = codes[action];
    if (!list) return;
    for (let i = 0; i < list.length; i++) delete pressedAt[list[i]];
  }

  function tick() {
    frame++;
  }

  function now() {
    return frame;
  }

  return { held: isHeld, pressed: wasPressed, consume: consume, tick: tick, frame: now };
})();
