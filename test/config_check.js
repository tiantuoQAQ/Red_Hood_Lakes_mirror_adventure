'use strict';

// 校验调参面板的每个滑块都指向 CFG 里真实存在的字段，
// 并且每个滑块都有对应的数值显示位。避免面板静默失效。

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const configSrc = fs.readFileSync(path.join(root, 'src/config.js'), 'utf8');

vm.runInThisContext(configSrc + '\nglobalThis.__CFG = CFG;', { filename: 'config.js' });
const CFG = globalThis.__CFG;

const cfgPaths = [...html.matchAll(/data-cfg="([^"]+)"/g)].map(function (m) { return m[1]; });
const outPaths = [...html.matchAll(/data-out="([^"]+)"/g)].map(function (m) { return m[1]; });

function resolve(obj, dotted) {
  const parts = dotted.split('.');
  let o = obj;
  for (const p of parts) {
    if (o === null || typeof o !== 'object' || !(p in o)) return undefined;
    o = o[p];
  }
  return o;
}

const problems = [];

cfgPaths.forEach(function (p) {
  const v = resolve(CFG, p);
  if (v === undefined) problems.push('滑块指向不存在的字段: ' + p);
  else if (typeof v !== 'number') problems.push('滑块指向非数值字段: ' + p + ' = ' + typeof v);
  if (!outPaths.includes(p)) problems.push('滑块缺少数值显示: ' + p);
});

outPaths.forEach(function (p) {
  if (!cfgPaths.includes(p)) problems.push('数值显示没有对应滑块: ' + p);
});

if (cfgPaths.length === 0) problems.push('没有解析到任何 data-cfg 滑块');

console.log('');
console.log('滑块数量: ' + cfgPaths.length);
problems.forEach(function (p) { console.log('FAIL  ' + p); });
console.log(problems.length === 0 ? '面板绑定全部有效' : problems.length + ' 项问题');
process.exitCode = problems.length === 0 ? 0 : 1;
