'use strict';

// 角色贴图系统：单图 + 少量分件（cape / hair / body 三层）。
//
// 契约（给美术）：
//   - 三张 PNG 画布尺寸完全相同（CFG.sprite.w / h）
//   - 角色「脚底中心」对齐画布底部中央，三张图的站位必须一致
//   - 顺序：cape 在最下层，hair 中间，body 最上层
//   - 缺图不会崩，会自动退回程序化图形

const Sprites = (function () {
  const cache = Object.create(null);

  function load(id, dir) {
    if (cache[id]) return cache[id];
    const entry = { id: id, layers: {}, loaded: 0, need: 0 };
    cache[id] = entry;

    const names = ['cape', 'hair', 'body'];
    entry.need = names.length;

    for (let i = 0; i < names.length; i++) {
      const name = names[i];
      const img = new Image();
      img.onload = function () { entry.loaded++; };
      img.onerror = function () { entry.loaded++; };  // 缺图也算「处理完了」，避免永远等不到
      img.src = dir + '/' + name + '.png';
      entry.layers[name] = img;
    }
    return entry;
  }

  function ready(id) {
    const e = cache[id];
    if (!e) return false;
    if (e.loaded < e.need) return false;
    const body = e.layers.body;
    return !!(body && body.naturalWidth > 0);
  }

  return { load: load, ready: ready, cache: cache };
})();

// 把角色画到屏幕上。返回 true 表示用了贴图，false 表示退回程序化图形。
function drawCharacterSprite(ctx, p) {
  const S = CFG.sprite;
  if (!Sprites.ready(S.id)) return false;

  const ent = Sprites.cache[S.id];
  const body = ent.layers.body;

  const t = Game.frame;
  const moving = Math.abs(p.vx) > 30;
  const dashing = p.dashT > 0;
  const airborne = !p.onGround;

  // 待机呼吸：站着时浮动更明显，移动时收敛，避免抖
  const bob = Math.sin(t * 0.08) * (moving ? 1.2 : 2.0);
  // 冲刺前倾 + 挤压拉伸
  const tilt = dashing ? 0.20 : (moving ? 0.04 : 0);
  const stretchX = dashing ? 1.12 : 1.0;
  const stretchY = dashing ? 0.92 : (airborne ? 1.04 : 1.0);

  const w = body.naturalWidth * S.scale;
  const h = body.naturalHeight * S.scale;
  const footY = p.y + CFG.player.visualR;

  ctx.save();
  ctx.translate(p.x, footY + bob);
  ctx.rotate(tilt * p.facing);
  ctx.scale(stretchX * p.facing, stretchY);

  function layer(img, dx, dy, rot) {
    if (!img || !img.naturalWidth) return;
    ctx.save();
    ctx.translate(dx, dy);
    ctx.rotate(rot);
    ctx.drawImage(img, -w / 2, -h, w, h);
    ctx.restore();
  }

  // 斗篷甩得最晚、幅度最大；后发次之；身体不动
  const dashBoost = dashing ? 0.10 : 0;
  layer(ent.layers.cape, S.capeDx, S.capeDy,
        Math.sin(t * 0.11 + 0.6) * 0.05 + dashBoost);
  layer(ent.layers.hair, S.hairDx, S.hairDy,
        Math.sin(t * 0.13) * 0.04 + dashBoost * 1.2);
  layer(ent.layers.body, 0, 0, 0);

  ctx.restore();
  return true;
}
