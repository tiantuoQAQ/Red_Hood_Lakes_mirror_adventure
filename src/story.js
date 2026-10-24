'use strict';

// 剧情脚本（数据层）：只写数据，不放逻辑。
//
// 指令一览（详见 docs/剧情脚本.md）：
//   { t:'scene',  bg:'night'|'forest'|'mirror' }   切场景（只切背景，不换地图）
//   { t:'fade',   to:'black'|'clear', frames }     黑场
//   { t:'wait',   frames }                         空等
//   { t:'card',   line1, line2, frames }           章节卡：大字 + 底部两行字幕（图1形式）
//   { t:'bubble', who, text }                      场景内气泡：小人在场上说话（图2形式）
//   { t:'duel',   left, right, text, hint }        双立绘对峙 + 对话条（图3形式）
//   { t:'say',    who, text }                      通用底部对话框
//   { t:'battle', boss, after }                    开打，after 是打完接哪章
//   { t:'grant',  skill, banner }                  解锁技能
//   { t:'next',   chapter }                        接下一章
//   { t:'end',    kind:'win' }                     结局
//
// 台词一律先写占位；正式文案由制作人替换。who 留空表示旁白。

const STORY = {

  // ---------------------------------------------------------------- 序章
  // 开场是蕾克留给格林的最后一封信——不画信纸，直接让她念出来。
  // 念完进入玩家操控的走位段，走到路的尽头触发「黑影」。
  prologue: {
    cmds: [
      { t: 'scene', bg: 'night' },
      { t: 'fade', to: 'black', frames: 1 },

      { t: 'say', who: '', text: '这封信，是在她走了三天之后被找到的。' },
      { t: 'say', who: '', text: '桌子上留着它。压在水杯底下，压得很平。' },

      { t: 'say', who: '蕾克', text: '格林。' },
      { t: 'say', who: '蕾克', text: '我要走了。' },
      { t: 'say', who: '蕾克', text: '这一次，我不知道自己还能不能回来。' },
      { t: 'say', who: '蕾克', text: '我知道，这只是我的任性。' },
      { t: 'say', who: '蕾克', text: '请你原谅我。' },
      { t: 'say', who: '蕾克', text: '我不想把你卷进这件事里来。' },
      { t: 'say', who: '蕾克', text: '你总说，让我等你。' },
      { t: 'say', who: '蕾克', text: '可这一次，我不能再等了。' },
      { t: 'say', who: '蕾克', text: '我不会让这个世界如她所愿。' },
      { t: 'say', who: '蕾克', text: '只要我还没有死，这个故事就永远不会结束。' },
      { t: 'say', who: '蕾克', text: '所以，别难过。' },
      { t: 'say', who: '蕾克', text: '等我回来——我们还有很多话，没来得及说完。' },

      { t: 'say', who: '', text: '信就断在这里。' },
      { t: 'say', who: '', text: '最后一个字写得很重，像是写的人后来不敢再往下写。' },

      { t: 'fade', to: 'clear', frames: 40 },
      { t: 'scene', bg: 'forest' },
      { t: 'say', who: '', text: '她把信压在桌上，一个人走进森林。' },

      { t: 'card', line1: '悲愤交加的勇者', line2: '踏上了寻回珍视之人的旅途', frames: 170 },

      // ↓ 玩家接管，走到路的尽头
      { t: 'walk', untilX: 1040, next: 'ambush' }
    ]
  },

  // ---------------------------------------------------------------- 黑影 · 遭遇
  // 玛丽苏此时是「黑影」状态，不露脸，用 shadow 表情差分占位（art/portrait/marysue_shadow.png）。
  // 蕾克的表情差分：eyes_closed / eyes_open / ready / shock，对应
  //   art/portrait/rek_eyes_closed.png 等；没有图时代码自动退回基础立绘或占位块。
  ambush: {
    cmds: [
      { t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '库嘻嘻……' },
      { t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '沉浸在人家赐予你的美好里，迎来属于自己的结局，不好吗？' },
      { t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '为什么这么急着，跳出人家的童话呢～' },

      { t: 'say', who: 'rek', show: true, text: '……真让人恶心。' },
      { t: 'say', who: 'rek', expr: 'eyes_closed', show: true, text: '在你写的故事里，主角等到的，永远只有悲惨结局。' },
      { t: 'say', who: 'rek', expr: 'eyes_open', show: true, text: '我，不认可这样的结局。' },
      { t: 'say', who: 'rek', style: 'red', shake: true, show: true, text: '玛丽苏……' },
      { t: 'say', who: 'rek', style: 'red', shake: true, show: true, text: '在砍下你的头颅之前，我是不会死的。' },

      { t: 'pose', who: 'rek', expr: 'ready', frames: 40 },

      { t: 'say', who: 'marysue', show: true, text: '哎呀呀，人家好怕啊～' },
      { t: 'say', who: 'marysue', expr: 'eyes_closed', show: true, text: '你真觉得……' },
      { t: 'say', who: 'marysue', show: true, text: '人家可是……从来没有把你当成敌人哦。' },
      { t: 'say', who: 'marysue', expr: 'eyes_open', show: true, text: '你能碰到我吗？' },

      { t: 'say', who: '', text: '「啪嗒。」' },
      { t: 'say', who: 'rek', expr: 'shock', show: true, bump: true, screenshake: 12, shakeAmp: 7, text: '！？' },
      { t: 'wait', frames: 26 },

      // CG：玛丽苏身后浮现法环陷阱（art/cg/trap.png；没有图就画占位法环）
      { t: 'cg', art: 'art/cg/trap.png', label: '法环陷阱', frames: 130 },

      // 一白、一黑、一白
      { t: 'flash', seq: [{ c: 'white', f: 7 }, { c: 'black', f: 10 }, { c: 'white', f: 7 }, { c: 'black', f: 14 }] },

      // 醒来：一片空白，只有地面和诺登；玩家自己走过去，靠近按 W 交互
      { t: 'walk', bg: 'void', npc: 'norden', npcX: 980, next: 'wake_talk' }
    ]
  },

  // ---------------------------------------------------------------- 醒来 · 诺登
  // 文案待填：玩家按 W 交互之后才进来。
  wake_talk: {
    cmds: [
      { t: 'say', who: 'norden', show: true, text: '【待填】你醒了。' },
      { t: 'say', who: 'norden', show: true, text: '【待填】是我把你捡回来的。' },
      { t: 'next', chapter: 'wake' }
    ]
  },

  // ---------------------------------------------------------------- 醒来 · 诺登
  wake: {
    cmds: [
      { t: 'fade', to: 'clear', frames: 40 },
      { t: 'scene', bg: 'night' },
      { t: 'bubble', who: '蕾克', text: '【待填】……这里是？' },
      { t: 'intro', id: 'norden' },
      { t: 'duel', left: '蕾克', right: '诺登', text: '【待填】诺登：你醒了。是我把你捡回来的。' },
      { t: 'say', who: '诺登', text: '【待填】玛丽苏已经不在这个世界了。她躲进了「镜中世界」。' },
      { t: 'say', who: '诺登', text: '【待填】……我以为你会问「为什么」。' },
      { t: 'bubble', who: '蕾克', text: '【待填】带路。' },
      { t: 'next', chapter: 'mirror' }
    ]
  },

  // ---------------------------------------------------------------- 镜中世界
  mirror: {
    cmds: [
      { t: 'fade', to: 'black', frames: 35 },
      { t: 'scene', bg: 'mirror' },
      { t: 'fade', to: 'clear', frames: 45 },
      { t: 'say', who: '', text: '镜面之后，是一整片被倒置的世界。' },
      { t: 'say', who: '', text: '而在路的尽头，站着另一个「她」。' },
      { t: 'intro', id: 'rek_crimson' },
      { t: 'duel', left: '蕾克', right: '猩红魔姬', text: '【待填】魔姬：姐姐，你终于来陪我了。' },
      { t: 'bossIntro', id: 'rek_crimson', frames: 170 },
      { t: 'battle', boss: 'crimson', after: 'crimson_fall' }
    ]
  },

  // ---------------------------------------------------------------- 魔姬战败 · 玛丽苏登场 · 传承
  crimson_fall: {
    cmds: [
      { t: 'fade', to: 'black', frames: 45 },
      { t: 'fade', to: 'clear', frames: 45 },
      { t: 'intro', id: 'marysue' },
      { t: 'say', who: '玛丽苏', text: '【待填】没用的孩子。你已经没有价值了。' },
      { t: 'duel', left: '玛丽苏', right: '猩红魔姬', text: '【待填】魔姬：……不要，别丢下我。' },
      { t: 'say', who: '玛丽苏', text: '【待填】镜子里多的是替代品。' },
      { t: 'bubble', who: '猩红魔姬', text: '【待填】——那就把它拿去吧，姐姐。' },
      { t: 'say', who: '', text: '红色的力量，顺着裂隙流进了蕾克的身体。' },
      { t: 'grant', skill: 'red_tragedy', banner: '红之惨剧' },
      { t: 'card', line1: '红之惨剧', line2: '夺回被夺走的一切', frames: 150 },
      { t: 'next', chapter: 'final' }
    ]
  },

  // ---------------------------------------------------------------- 最终战
  final: {
    cmds: [
      { t: 'scene', bg: 'mirror' },
      { t: 'duel', left: '蕾克', right: '玛丽苏', text: '【待填】玛丽苏：就凭你，也想照亮这面镜子？' },
      { t: 'say', who: '玛丽苏', text: '【待填】你以为你在追谁？' },
      { t: 'say', who: '蕾克', text: '我知道自己在追谁。' },
      { t: 'say', who: '蕾克', text: '我是不会死的。' },
      { t: 'say', who: '蕾克', text: '在斩下你的头颅之前。' },
      { t: 'bossIntro', id: 'marysue', frames: 180 },
      { t: 'battle', boss: 'marysue', after: 'ending' }
    ]
  },

  // ---------------------------------------------------------------- 结局
  ending: {
    cmds: [
      { t: 'fade', to: 'black', frames: 60 },
      { t: 'card', line1: '镜面碎成了千万片', line2: '每一片里都有她', frames: 190 },
      { t: 'say', who: '蕾克', text: '【待填】……回去了。' },
      { t: 'end', kind: 'win' }
    ]
  }
};
