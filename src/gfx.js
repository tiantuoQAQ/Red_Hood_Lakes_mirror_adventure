'use strict';

// 绘制工具：全部程序化生成，不加载任何图片资源。

function hexToRgba(hex, alpha) {
  const h = hex.replace('#', '');
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
}

// 双层圆：外层低透明度散光 + 内层实心核心（用两层代替 shadowBlur，性能更稳）
//
// 散光默认用**白色**：彩色半透明光晕叠在另一个色相上会混出第三种颜色
// （绿光压在红色玩家上就是橙色），直接违反「不多于 3 个色相」。
// 白色是无色相的灰阶，叠加只改变明度，不影响色相。
function glowCircle(ctx, x, y, r, color, glowScale, coreAlpha, glowColor) {
  const gs = glowScale === undefined ? 2.4 : glowScale;
  const ca = coreAlpha === undefined ? 1 : coreAlpha;
  const gc = glowColor || '#ffffff';

  ctx.beginPath();
  ctx.arc(x, y, r * gs, 0, Math.PI * 2);
  ctx.fillStyle = hexToRgba(gc, 0.07);
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x, y, r * 1.5, 0, Math.PI * 2);
  ctx.fillStyle = hexToRgba(gc, 0.12);
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = hexToRgba(color, ca);
  ctx.fill();
}

function roundRectPath(ctx, x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.lineTo(x + w - rr, y);
  ctx.arcTo(x + w, y, x + w, y + rr, rr);
  ctx.lineTo(x + w, y + h - rr);
  ctx.arcTo(x + w, y + h, x + w - rr, y + h, rr);
  ctx.lineTo(x + rr, y + h);
  ctx.arcTo(x, y + h, x, y + h - rr, rr);
  ctx.lineTo(x, y + rr);
  ctx.arcTo(x, y, x + rr, y, rr);
  ctx.closePath();
}

function bar(ctx, x, y, w, h, ratio, color, bgColor) {
  const r = Math.max(0, Math.min(1, ratio));
  roundRectPath(ctx, x, y, w, h, h / 2);
  ctx.fillStyle = bgColor || 'rgba(255,255,255,0.10)';
  ctx.fill();

  if (r > 0.001) {
    roundRectPath(ctx, x, y, Math.max(h, w * r), h, h / 2);
    ctx.fillStyle = color;
    ctx.fill();
  }
}

function label(ctx, text, x, y, size, color, align, weight) {
  ctx.font = (weight || 400) + ' ' + size + 'px "Segoe UI", "Microsoft YaHei", system-ui, sans-serif';
  ctx.textAlign = align || 'left';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
}

function mono(ctx, text, x, y, size, color, align) {
  ctx.font = size + 'px "Cascadia Mono", "Consolas", monospace';
  ctx.textAlign = align || 'left';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
}
