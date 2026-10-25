# -*- coding: utf-8 -*-
"""名字揭示机制：
1) story.js：蕾克不再先喊名字；玛丽苏在自己介绍之前都用 shadow（？？？）；
   新增 { t:'reveal', who:'marysue' } 在她自报姓名处。
2) Web cutscene：支持 reveal 命令；未揭示前名牌一律「？？？」；reveal 时弹称号竖幅。
3) Godot：同样逻辑。
"""
import io

# ---------------- 1) story.js ----------------
p = 'src/story.js'
s = io.open(p, encoding='utf-8').read()

# 蕾克不再提前喊名字
s = s.replace("{ t: 'say', who: 'rek', style: 'red', shake: true, show: true, text: '玛丽苏……' },",
              "{ t: 'say', who: 'rek', style: 'red', shake: true, show: true, text: '……你到底是什么东西。' },", 1)

# 后续两句玛丽苏改成 shadow（尚未自报姓名）
s = s.replace("{ t: 'say', who: 'marysue', show: true, text: '哎呀呀，人家真是怕极了呢～' },",
              "{ t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '哎呀呀，人家真是怕极了呢～' },", 1)
s = s.replace("{ t: 'say', who: 'marysue', show: true, text: '人家可是……从来没有把你当成敌人哦。' },",
              "{ t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '人家可是……从来没有把你当成敌人哦。' },", 1)

# 插入「自报姓名」段落（在「而且……你真觉得……」之前）
anchor = "{ t: 'say', who: 'marysue', expr: 'eyes_closed', show: true, text: '而且……你真觉得……' },"
intro = ("{ t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '不过，告诉你也无妨。' },\n"
         "      { t: 'reveal', who: 'marysue' },\n"
         "      { t: 'say', who: 'marysue', expr: 'tease', show: true, text: '人家叫玛丽苏，是写故事的人。' },\n"
         "      " + anchor)
if anchor in s and "t: 'reveal'" not in s:
    s = s.replace(anchor, intro, 1)
    print('story: reveal inserted')

io.open(p, 'w', encoding='utf-8').write(s)

# ---------------- 2) Web cutscene ----------------
p2 = 'src/cutscene.js'
w = io.open(p2, encoding='utf-8').read()

if 'const KNOWN' not in w:
    w = w.replace('const EXPR_LABEL = {', 'const KNOWN = Object.create(null);   // 已自报姓名的角色\n  const EXPR_LABEL = {', 1)
    # 章节开始时清空
    w = w.replace('\tS.t = 0;', '\tS.t = 0;\n\t\tfor (const k in KNOWN) delete KNOWN[k];', 1)
    print('web: KNOWN state added')

# reveal 命令
if "case 'reveal':" not in w:
    w = w.replace("      case 'music':",
                  "      case 'reveal':\n"
                  "        if (c.who) {\n"
                  "          KNOWN[c.who] = true;\n"
                  "          S.intro = { id: c.who };\n"
                  "          S.framesLeft = 120;\n"
                  "        }\n"
                  "        break;\n"
                  "      case 'music':", 1)
    print('web: reveal command added')

# 名牌：未揭示 → ？？？
w = w.replace(
    "      const tag = S.text.expr === 'shadow' ? '？？？' : c.name + (ex ? ' · ' + ex : '');",
    "      const unknown = !KNOWN[S.text.who] || S.text.expr === 'shadow';\n"
    "      const tag = unknown ? '？？？' : c.name + (ex ? ' · ' + ex : '');", 1)

# 首次说话不再自动弹竖幅（改由 reveal 触发）
w = w.replace(
    "      if (!seenSpeakers.has(S.text.who)) {\n        seenSpeakers.add(S.text.who);\n      }\n",
    "", 1)

io.open(p2, 'w', encoding='utf-8').write(w)
print('web patched')
