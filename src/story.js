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
      { t: 'say', who: 'marysue', show: true, text: '人家可是……从来没有把你当成敌人哦。' },
      { t: 'say', who: 'marysue', expr: 'eyes_closed', show: true, text: '而且……你真觉得……' },
      { t: 'say', who: 'marysue', expr: 'eyes_open', show: true, text: '你能碰到我吗？' },

      { t: 'say', who: '', text: '「啪嗒。」' },
      { t: 'say', who: 'rek', expr: 'shock', show: true, bump: true, screenshake: 12, shakeAmp: 7, text: '！？' },
      { t: 'wait', frames: 26 },

      // CG：玛丽苏身后浮现法环陷阱（art/cg/trap.png；没有图就画占位法环）
      { t: 'cg', art: 'art/cg/trap.png', label: '法环陷阱', frames: 130 },

      // 一白、一黑、一白
      { t: 'flash', seq: [{ c: 'white', f: 7 }, { c: 'black', f: 10 }, { c: 'white', f: 7 }, { c: 'black', f: 14 }] },

      // 醒来：一片空白，只有地面和诺登；玩家自己走过去，靠近按 W 交互
      { t: 'walk', bg: 'void', target: { kind: 'norden', x: 980 }, next: 'wake_talk' }
    ]
  },

  // ---------------------------------------------------------------- 醒来 · 诺登（按 W 之后）
  // 诺登用敬语，自称「观察者」；蕾克全程警惕。
  wake_talk: {
    cmds: [
      { t: 'say', who: 'norden', show: true, text: '贵安，蕾克小姐。' },
      { t: 'say', who: 'rek', show: true, text: '……' },

      { t: 'say', who: 'norden', show: true, text: '请允许我自我介绍。' },
      { t: 'say', who: 'norden', show: true, text: '我是「白之兔」诺登。' },
      { t: 'say', who: 'norden', show: true, text: '现在的情况有些复杂。您只需要知道一件事——' },
      { t: 'say', who: 'norden', show: true, text: '我是站在格林大人这一边的。' },

      { t: 'say', who: 'rek', show: true, text: '……我不能相信你。' },
      { t: 'say', who: 'rek', show: true, text: '你的意图是——' },
      { t: 'say', who: 'norden', show: true, text: '这不重要。' },
      { t: 'say', who: 'norden', show: true, text: '我所做的一切，都是为了格林大人。' },
      { t: 'say', who: 'norden', show: true, text: '您被玛丽苏偷袭了。是我，从她手上把您救下来的。' },
      { t: 'say', who: 'rek', show: true, text: '……' },

      { t: 'say', who: 'norden', show: true, text: '我们都想阻止玛丽苏的狂妄之举。' },
      { t: 'say', who: 'norden', show: true, text: '既然如此，我们暂时互相帮助——不好吗？' },

      { t: 'say', who: 'norden', expr: 'eyes_closed', show: true, text: '玛丽苏现在正在「镜中世界」，筹划她自己的计划。' },
      { t: 'say', who: 'norden', expr: 'eyes_open', show: true, text: '您要做的，就是前往「镜中世界」，然后击败她。' },

      { t: 'say', who: 'rek', show: true, text: '……你为什么不自己去。' },
      { t: 'say', who: 'norden', show: true, text: '因为我是「观察者」。' },
      { t: 'title', who: 'norden', title: '白之女王 · 观察者', frames: 150 },
      { t: 'say', who: 'norden', show: true, text: '直接与玛丽苏爆发冲突，后果不可估量。' },
      { t: 'say', who: 'norden', show: true, text: '所以这件事，只能由您来完成。为了格林大人。' },

      { t: 'say', who: 'rek', show: true, text: '……我好像，没有别的选择。' },
      { t: 'say', who: 'norden', show: true, text: '感谢您的理解。' },
      { t: 'say', who: 'norden', show: true, text: '现在，请触摸那边的镜子吧。' },
      { t: 'say', who: 'norden', show: true, text: '它会带您进入镜中世界。' },
      { t: 'say', who: 'norden', show: true, text: '……那个世界，非常混乱。' },
      { t: 'wait', frames: 30 },
      { t: 'say', who: 'norden', show: true, text: '……' },
      { t: 'say', who: 'norden', show: true, text: '祝您好运。' },

      // 说完才出现镜子：玩家自己走过去，按 W 交互
      { t: 'walk', bg: 'void', target: { kind: 'mirror', x: 1040 }, next: 'enter_mirror' }
    ]
  },

  // ---------------------------------------------------------------- 走进镜子
  enter_mirror: {
    cmds: [
      { t: 'fade', to: 'black', frames: 55 },
      { t: 'say', who: '', text: '她伸出手。' },
      { t: 'say', who: '', text: '镜面像水一样，把她的手吞了下去。' },
      { t: 'flash', seq: [{ c: 'white', f: 8 }, { c: 'black', f: 14 }] },
      { t: 'next', chapter: 'mirror' }
    ]
  },

  // ---------------------------------------------------------------- 镜中世界
  mirror: {
    cmds: [
      { t: 'fade', to: 'black', frames: 35 },
      { t: 'scene', bg: 'mirror' },
      { t: 'fade', to: 'clear', frames: 45 },

      { t: 'say', who: '', text: '镜子里没有回声。' },
      { t: 'say', who: '', text: '树是倒着长的——根在天上，枝叶垂进地面。' },
      { t: 'say', who: '', text: '这片森林干净得像从来没有人来过。' },
      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '……这里什么都没有。' },
      { t: 'say', who: '', text: '除了路中间站着的那个人。' },

      { t: 'intro', id: 'rek_crimson' },
      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '……你是谁。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '姐姐。' },
      { t: 'say', who: 'rek', expr: 'shock', show: true, text: '你不是我。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '我是你呀。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '是被留下来的那一个。' },

      { t: 'duel', left: '蕾克', right: '猩红魔姬', text: '魔姬：你把我一个人，丢在这里。' },
      { t: 'say', who: 'rek', expr: 'eyes_closed', show: true, text: '……' },
      { t: 'say', who: 'rek_crimson', show: true, text: '没关系。我不怪你。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '玛丽苏大人说，只要待在这里，我什么都不用怕。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '她给了我一个故事。故事里，你没有走。' },

      { t: 'say', who: 'rek', expr: 'eyes_open', show: true, text: '那是假的。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '假的也很好呀。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '姐姐，留下来吧。在这里，你不用再死一次。' },

      { t: 'say', who: 'rek', expr: 'eyes_closed', show: true, text: '……我不会留下。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '那就——' },
      { t: 'say', who: 'rek_crimson', show: true, text: '让我把你留下来。' },

      { t: 'bossIntro', id: 'rek_crimson', frames: 170 },
      { t: 'battle', boss: 'crimson', after: 'crimson_fall' }
    ]
  },

  // ---------------------------------------------------------------- 魔姬战败 · 玛丽苏登场 · 传承
  crimson_fall: {
    cmds: [
      { t: 'fade', to: 'black', frames: 45 },
      { t: 'fade', to: 'clear', frames: 45 },

      { t: 'say', who: '', text: '红色的身体跪在地上，像一盏快要熄灭的灯。' },

      { t: 'intro', id: 'marysue' },
      { t: 'say', who: 'marysue', show: true, text: '哎呀呀……' },
      { t: 'say', who: 'marysue', show: true, text: '真是难看呢。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '玛丽苏大人……' },
      { t: 'say', who: 'marysue', show: true, text: '人家给你的舞台，可不是让你这样收场的哦。' },
      { t: 'say', who: 'marysue', show: true, text: '没用的孩子，是要被换掉的。' },

      { t: 'say', who: 'rek', expr: 'ready', show: true, text: '住手。' },
      { t: 'say', who: 'marysue', show: true, text: '为什么？' },
      { t: 'say', who: 'marysue', show: true, text: '她只是个替身而已呀。' },
      { t: 'say', who: 'marysue', show: true, text: '你该谢谢人家才对——人家替你，保管了她这么久。' },

      { t: 'say', who: '', text: '玛丽苏抬起了手。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '姐姐。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '……对不起。' },
      { t: 'say', who: 'rek_crimson', show: true, text: '那个东西……你拿走吧。' },

      { t: 'pose', who: 'rek', expr: 'ready', frames: 40 },
      { t: 'say', who: '', text: '红色顺着裂隙流进来。很烫，像有人把手按在胸口。' },
      { t: 'grant', skill: 'red_tragedy', banner: '红之惨剧' },
      { t: 'card', line1: '红之惨剧', line2: '夺回被夺走的一切', frames: 150 },

      { t: 'say', who: 'rek', expr: 'eyes_open', show: true, text: '……我接住了。' },
      { t: 'say', who: 'marysue', show: true, text: '……真恶心。' },
      { t: 'say', who: 'marysue', show: true, text: '那你呢？' },
      { t: 'say', who: 'marysue', show: true, text: '你要拿什么，来替她？' },

      { t: 'next', chapter: 'final' }
    ]
  },

  // ---------------------------------------------------------------- 最终战
  final: {
    cmds: [
      { t: 'scene', bg: 'mirror' },
      { t: 'duel', left: '蕾克', right: '玛丽苏', text: '玛丽苏：就凭你，也想照亮这面镜子？' },

      { t: 'say', who: 'marysue', show: true, text: '那面镜子已经把你记住了一次。' },
      { t: 'say', who: 'marysue', show: true, text: '第二次，可不会那么客气哦。' },
      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '……上一次，我还没学会怎么杀你。' },
      { t: 'say', who: 'marysue', show: true, text: '……' },
      { t: 'say', who: 'marysue', show: true, text: '你不该回来的。' },
      { t: 'say', who: 'marysue', show: true, text: '人家把门关上，是为了你好。' },
      { t: 'say', who: 'rek', expr: 'eyes_open', show: true, text: '我不需要别人替我把门关上。' },
      { t: 'say', who: 'rek', expr: 'ready', show: true, text: '我也不会，死在你的故事里。' },

      { t: 'bossIntro', id: 'marysue', frames: 180 },
      { t: 'battle', boss: 'marysue', after: 'ending' }
    ]
  },

  // ---------------------------------------------------------------- 结局
  ending: {
    cmds: [
      { t: 'fade', to: 'black', frames: 60 },
      { t: 'card', line1: '镜面碎成了千万片', line2: '每一片里都有她', frames: 190 },
      { t: 'fade', to: 'clear', frames: 45 },
      { t: 'say', who: '', text: '她走出镜子的时候，天已经亮了。' },
      { t: 'say', who: '', text: '森林还是那片森林。' },
      { t: 'say', who: 'rek', expr: 'eyes_closed', show: true, text: '……累死了。' },
      { t: 'say', who: 'rek', expr: 'eyes_open', show: true, text: '格林。' },
      { t: 'say', who: 'rek', show: true, text: '我回来了。' },
      { t: 'say', who: '', text: '——这一次，信不用再压在杯子底下了。' },
      { t: 'end', kind: 'win' }
    ]
  }
};
