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
  // 以「蕾克留给格林的最后一封信」开场：把情绪压进信里，再让玩家自己走进那片森林。
  prologue: {
    cmds: [
      { t: 'scene', bg: 'night' },
      { t: 'fade', to: 'black', frames: 1 },

      { t: 'say', who: '', text: '这封信，是在她走了三天之后被找到的。' },
      { t: 'say', who: '', text: '桌子上留着它。压水杯底下，压得很平。' },

      {
        t: 'letter',
        lines: [
          '格林：',
          '我要走了。',
          '这一次，我不知道自己还能不能回来。',
          '我知道，这只是我的任性。',
          '请你原谅我。',
          '我不想把你卷进这件事里来。',
          '你总说，让我等你。',
          '可这一次，我不能再等了。',
          '我不会让这个世界如她所愿。',
          '只要我还没有死，这个故事就永远不会结束。',
          '所以，别难过。',
          '等我回来——我们还有很多话，没来得及说完。'
        ]
      },

      { t: 'say', who: '', text: '信就断在这里。' },
      { t: 'say', who: '', text: '最后一个字写得很重，像是写的人后来不敢再往下写。' },

      { t: 'fade', to: 'clear', frames: 40 },
      { t: 'scene', bg: 'forest' },
      { t: 'say', who: '', text: '她把信压在桌上，一个人走进森林。' },

      { t: 'card', line1: '悲愤交加的勇者', line2: '踏上了寻回珍视之人的旅途', frames: 170 },

      { t: 'say', who: '', text: '然后，她没能走出那片森林。' },
      { t: 'fade', to: 'black', frames: 45 },
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
