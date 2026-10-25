// 从 src/story.js 导出 JSON + 台本 md（给 Godot 端搬剧情用）
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'src/story.js'), 'utf8');
const fn = new Function(src + '\nreturn STORY;');
const STORY = fn();

fs.writeFileSync(path.join(root, 'docs/story_export.json'), JSON.stringify(STORY, null, 2), 'utf8');

const lines = [];
lines.push('# 剧情全表（自动生成，勿手改）');
lines.push('');
lines.push('> 由 `tools/export_story.js` 从 `src/story.js` 导出。改剧情改 `src/story.js`，然后重新跑这个脚本。');
lines.push('');
const ids = Object.keys(STORY);
lines.push(`共 **${ids.length}** 章。`);
lines.push('');

let totalSay = 0;
for (const id of ids) {
  const ch = STORY[id];
  const cmds = ch.cmds || [];
  const says = cmds.filter((c) => c.t === 'say');
  totalSay += says.length;
  lines.push(`## ${id}`);
  lines.push('');
  const kinds = {};
  cmds.forEach((c) => { kinds[c.t] = (kinds[c.t] || 0) + 1; });
  lines.push('命令数 ' + cmds.length + '：' +
    Object.keys(kinds).map((k) => `${k}×${kinds[k]}`).join('、'));
  lines.push('');
  if (says.length) {
    lines.push('| # | 角色 | 表情 | 台词 |');
    lines.push('| --- | --- | --- | --- |');
    says.forEach((s, i) => {
      const who = s.who || '旁白';
      const expr = s.expr || '';
      const text = String(s.text || '').replace(/\|/g, '\\|');
      lines.push(`| ${i + 1} | ${who} | ${expr} | ${text} |`);
    });
    lines.push('');
  }
}
lines.push('---');
lines.push('');
lines.push(`台词总数：**${totalSay}** 句。`);
fs.writeFileSync(path.join(root, 'docs/剧情全表.md'), lines.join('\n'), 'utf8');

console.log('chapters:', ids.length, 'total says:', totalSay);
console.log('wrote docs/story_export.json and docs/剧情全表.md');
