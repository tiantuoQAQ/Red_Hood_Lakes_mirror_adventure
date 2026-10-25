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

      { t: 'say', who: '', text: '她离开三天后，这封信才被人发现。' },
      { t: 'say', who: '', text: '桌子上留着它。压在水杯底下，压得很平。' },

      { t: 'say', who: '蕾克', text: '格林。' },
      { t: 'say', who: '蕾克', text: '我要走了。' },
      { t: 'say', who: '蕾克', text: '这一次，我不知道自己还能不能回来。' },
      { t: 'say', who: '蕾克', text: '我知道，这只是我的任性。' },
      { t: 'say', who: '蕾克', text: '请你原谅我。' },
      { t: 'say', who: '蕾克', text: '我不想把你卷进这件事里来。' },
      { t: 'say', who: '蕾克', text: '你总说，让我等你。' },
      { t: 'say', who: '蕾克', text: '可这一次，我不能再等了。' },
      { t: 'say', who: '蕾克', text: '我不会让玛丽苏如愿。' },
      { t: 'say', who: '蕾克', text: '只要我还活着，就不会让她写下结局。' },
      { t: 'say', who: '蕾克', text: '所以，别难过。' },
      { t: 'say', who: '蕾克', text: '等我回来——我们还有话没说完。' },

      { t: 'say', who: '', text: '信就断在这里。' },
      { t: 'say', who: '', text: '最后一个字写得很重，像是写的人后来不敢再往下写。' },

      { t: 'fade', to: 'clear', frames: 40 },
      { t: 'scene', bg: 'forest' },
      { t: 'say', who: '', text: '她把信压在桌上，一个人走进森林。' },


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
      { t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '……' },
      { t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '库嘻嘻……' },
      { t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '沉浸在人家赐你的美好里，走向注定的结局，不好吗？' },
      { t: 'say', who: 'marysue', expr: 'shadow', show: true, text: '为什么这么急着，跳出人家的童话呢～' },

      { t: 'say', who: 'rek', show: true, text: '……真让人恶心。' },
      { t: 'say', who: 'rek', expr: 'eyes_closed', show: true, text: '你的故事里，主角等来的永远是悲惨结局。' },
      { t: 'say', who: 'rek', expr: 'eyes_open', show: true, text: '我，不认可这样的结局。' },
      { t: 'say', who: 'rek', style: 'red', shake: true, show: true, text: '玛丽苏……' },
      { t: 'say', who: 'rek', style: 'red', shake: true, show: true, text: '在砍下你的头颅前，我绝不会倒下。' },

      { t: 'pose', who: 'rek', expr: 'ready', frames: 40 },

      { t: 'say', who: 'marysue', show: true, text: '哎呀呀，人家真是怕极了呢～' },
      { t: 'say', who: 'marysue', show: true, text: '人家可是……从来没有把你当成敌人哦。' },
      { t: 'say', who: 'marysue', expr: 'eyes_closed', show: true, text: '而且……你真觉得……' },
      { t: 'say', who: 'marysue', expr: 'eyes_open', show: true, text: '你能碰到我吗？' },

      { t: 'say', who: '', text: '「啪嗒。」' },
      { t: 'say', who: 'rek', expr: 'shock', show: true, bump: true, screenshake: 12, shakeAmp: 7, text: '！？' },
      { t: 'wait', frames: 26 },

      // CG：玛丽苏身后浮现法环陷阱（art/cg/trap.png；没有图就画占位法环）
      { t: 'cg', art: 'art/cg/trap.png', label: '法环陷阱', frames: 130 },

      // 闪屏昏迷，停留黑场后逐渐醒来；此段演出不能被继续键打断。
      { t: 'flash', locked: true, seq: [{ c: 'white', f: 7 }, { c: 'black', f: 10 }, { c: 'white', f: 7 }, { c: 'black', f: 14 }] },
      { t: 'fade', to: 'black', frames: 1, locked: true },
      { t: 'scene', bg: 'void', clear: true },
      { t: 'wait', frames: 150, locked: true },
      { t: 'fade', to: 'clear', frames: 60, locked: true },
      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '……这是哪里？' },

      // 起点看不到诺登，向右走、镜头延伸后才遇见她。
      { t: 'walk', bg: 'void', cam: true, playerX: 180, target: { kind: 'norden', x: 1700 }, next: 'wake_talk' }
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
      { t: 'say', who: 'norden', show: true, text: '情况复杂，先记住一件事——' },
      { t: 'say', who: 'norden', show: true, text: '我奉格林大人之命，暂且助您。' },

      { t: 'say', who: 'rek', show: true, text: '……我不能相信你。' },
      { t: 'say', who: 'rek', show: true, text: '你的意图是——' },
      { t: 'say', who: 'norden', show: true, text: '此刻不必追问我的意图。' },
      { t: 'say', who: 'norden', show: true, text: '我救您，是为了格林大人。' },
      { t: 'say', who: 'norden', show: true, text: '您被玛丽苏偷袭了。是我，从她手上把您救下来的。' },
      { t: 'say', who: 'rek', show: true, text: '……' },

      { t: 'say', who: 'norden', show: true, text: '我们都想阻止玛丽苏的狂妄之举。' },
      { t: 'say', who: 'norden', show: true, text: '既然目标相同，暂且合作吧。' },

      { t: 'say', who: 'norden', expr: 'eyes_closed', show: true, text: '玛丽苏现在正在「镜中世界」，筹划她自己的计划。' },
      { t: 'say', who: 'norden', expr: 'eyes_open', show: true, text: '请入镜中世界，阻止玛丽苏。' },

      { t: 'say', who: 'rek', show: true, text: '……你为什么不自己去。' },
      { t: 'say', who: 'norden', show: true, text: '因为我是「观察者」。' },
      { t: 'title', who: 'norden', title: '白之女王 · 观察者', frames: 150 },
      { t: 'say', who: 'norden', show: true, text: '我是观察者，不能直接干涉她。' },
      { t: 'say', who: 'norden', show: true, text: '所以只能请您入镜。为了格林大人。' },

      { t: 'say', who: 'rek', show: true, text: '……我好像，没有别的选择。' },
      { t: 'say', who: 'norden', show: true, text: '感谢您的理解。' },
      { t: 'say', who: 'norden', show: true, text: '现在，请触摸那边的镜子吧。' },
      { t: 'say', who: 'norden', show: true, text: '它会带您进入镜中世界。' },
      { t: 'say', who: 'norden', show: true, text: '……那个世界，非常混乱。' },
      { t: 'wait', frames: 30 },
      { t: 'say', who: 'norden', show: true, text: '……' },
      { t: 'say', who: 'norden', show: true, text: '祝您好运。' },

      // 说完才出现镜子：玩家自己走过去，按 W 交互
      { t: 'walk', bg: 'void', cam: true, target: { kind: 'mirror', x: 1040 }, next: 'enter_mirror' }
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
      { t: 'say', who: '', text: '这片森林空无一人，像被镜子抹去痕迹。' },
      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '……这里什么都没有。' },
      { t: 'say', who: '', text: '除了路尽头那张王座。' },

      // 玩家自己走过去，靠近王座自动触发下一段
      {
        t: 'walk', bg: 'mirror', cam: true, untilX: 1180,
        props: [{ kind: 'throne', x: 1620, char: 'rek_crimson' }],
        next: 'mirror_meet'
      }
    ]
  },

  // ---------------------------------------------------------------- 王座 · 蕾帝
  mirror_meet: {
    cmds: [
      { t: 'music', name: 'crimson' },
      { t: 'say', who: 'rek_crimson', expr: 'seated_closed', show: true, text: '……' },
      { t: 'say', who: 'rek', expr: 'shock', show: true, text: '！？' },
      { t: 'say', who: 'rek', show: true, text: '（她怎么……和我长得一模一样。）' },
      { t: 'say', who: 'rek_crimson', expr: 'seated_open', show: true, text: '哟，终于来了？' },
      { t: 'say', who: 'rek', show: true, text: '……' },

      { t: 'say', who: 'rek_crimson', expr: 'stand_ready', show: true, text: '吾乃猩红魔姬·雷帝。' },
      { t: 'title', who: 'rek_crimson', title: '猩红魔姬 · 雷帝', frames: 150 },
      { t: 'pose', who: 'rek_crimson', expr: 'stand', frames: 45 },
      { t: 'say', who: 'rek_crimson', expr: 'stand', show: true, text: '我是玛丽苏大人最得意的作品。' },
      { t: 'say', who: 'rek_crimson', expr: 'stand', show: true, text: '从前，没有人愿意救我。' },
      { t: 'say', who: 'rek_crimson', expr: 'stand', show: true, text: '只有玛丽苏大人。' },
      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '……被救，和被造出来，是两回事。' },
      { t: 'say', who: 'rek_crimson', expr: 'stand', show: true, text: '你胡说什么。' },
      { t: 'say', who: 'rek_crimson', expr: 'stand', show: true, text: '听说你背弃亲友，换来了力量。' },
      { t: 'say', who: 'rek_crimson', expr: 'stand', show: true, text: '而你，小红帽蕾克——' },
      { t: 'say', who: 'rek_crimson', expr: 'stand', show: true, text: '你不过是玛丽苏随手丢弃的失败样本。' },
      { t: 'say', who: 'rek_crimson', expr: 'stand', show: true, text: '玛丽苏大人命吾在此，将你击溃。' },

      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '……失败样本。' },
      { t: 'say', who: 'rek', expr: 'eyes_open', show: true, text: '那就让这个样本，看看你有多成功。' },

      { t: 'pose', who: 'rek_crimson', expr: 'stand_ready', frames: 40 },
      { t: 'say', who: 'rek_crimson', expr: 'stand_ready', show: true, text: '此即，汝葬身之地。' },

      { t: 'bossIntro', id: 'rek_crimson', frames: 170 },
      { t: 'battle', boss: 'crimson', after: 'crimson_fall' }
    ]
  },

  // ---------------------------------------------------------------- 魔姬战败 · 真相 · 传承
  crimson_fall: {
    cmds: [
      { t: 'music', name: 'marysue' },
      { t: 'say', who: 'rek_crimson', expr: 'defeated', show: true, text: '怎么可能！……你的力量，怎么会这么强？' },
      { t: 'say', who: 'rek', expr: 'ready', show: true, text: '你以为力量是救赎，其实她操纵了你。' },
      { t: 'say', who: 'rek', expr: 'ready', show: true, text: '到了这一步，你还不肯看清吗？' },

      { t: 'say', who: 'rek_crimson', expr: 'defeated', show: true, text: '不可能！' },
      { t: 'say', who: 'rek_crimson', expr: 'defeated', show: true, text: '亲人背叛我时，是玛丽苏大人给了我力量——' },
      { t: 'say', who: 'rek_crimson', expr: 'defeated', show: true, text: '足以摧毁一切的力量！' },

      { t: 'say', who: 'rek', expr: 'ready', show: true, text: '你的所有经历——背叛、无助，甚至这次失败——' },
      { t: 'say', who: 'rek', expr: 'ready', show: true, text: '早就被玛丽苏预定好了。' },
      { t: 'say', who: 'rek', expr: 'ready', show: true, text: '你的一生，只是她满足恶趣味的一环。' },

      { t: 'say', who: 'rek_crimson', expr: 'defeated', show: true, text: '怎么可能！玛丽苏大——' },

      { t: 'say', who: '', text: '——小雷帝，蕾克说得没错哦～' },
      { t: 'say', who: 'rek', expr: 'shock', show: true, text: '！？' },
      { t: 'say', who: 'rek_crimson', expr: 'shock', show: true, text: '！？' },

      { t: 'say', who: '', text: '脚下的地面亮起一圈绿色的法阵。' },
      { t: 'flash', seq: [{ c: 'white', f: 5 }, { c: 'black', f: 8 }] },
      { t: 'intro', id: 'marysue' },

      { t: 'say', who: 'marysue', show: true, text: '是我哦。' },
      { t: 'say', who: 'marysue', show: true, text: '你父母离开你，也是我安排的。' },
      { t: 'say', who: 'marysue', show: true, text: '那些欺负你的“朋友”，也是人家安排的。' },
      { t: 'say', who: 'marysue', expr: 'smug', show: true, text: '你哭着求救时，人家就安排了那场相遇——' },
      { t: 'say', who: 'marysue', expr: 'smug', show: true, text: '多完美的剧本呀。' },

      { t: 'say', who: 'rek_crimson', expr: 'defeated', show: true, text: '你！！！……咳咳！' },

      { t: 'say', who: 'marysue', expr: 'fake', show: true, text: '哎呀呀……' },
      { t: 'say', who: 'marysue', expr: 'mock', show: true, text: '真是难看呢。' },
      { t: 'say', who: 'marysue', expr: 'fake', show: true, text: '人家给你的舞台，可不是让你这样收场的哦。' },
      { t: 'say', who: 'marysue', expr: 'star', show: true, text: '没用的孩子，是要被换掉的。' },

      // 醒悟
      { t: 'say', who: '', text: '玛丽苏抬起手，绿色的东西在她掌心聚成一根针。' },
      { t: 'say', who: 'rek_crimson', expr: 'defeated', show: true, text: '……原来如此。' },
      { t: 'say', who: 'rek_crimson', expr: 'defeated', show: true, text: '我这一生，连恨都是别人给的。' },

      { t: 'say', who: 'rek', expr: 'ready', show: true, text: '雷帝！' },
      { t: 'say', who: 'rek_crimson', expr: 'eyes_closed', show: true, text: '蕾克。' },
      { t: 'say', who: 'rek_crimson', expr: 'eyes_closed', show: true, text: '这次，换我自己选一次。' },
      { t: 'say', who: 'rek_crimson', expr: 'eyes_closed', show: true, text: '把我的力量拿去吧——它本来就不该属于我。' },

      { t: 'pose', who: 'rek', expr: 'ready', frames: 40 },
      { t: 'say', who: '', text: '红光自她胸口流出，烫得像一只手。' },
      { t: 'grant', skill: 'red_tragedy', banner: '红之惨剧' },
      { t: 'card', line1: '红之惨剧', line2: '夺回被夺走的一切', frames: 150 },

      { t: 'say', who: 'rek', expr: 'eyes_open', show: true, text: '……我接住了。' },

      { t: 'say', who: 'marysue', expr: 'smug', show: true, text: '真是感人呢。' },
      { t: 'say', who: 'marysue', expr: 'smug', show: true, text: '可惜，蕾克，加上你的力量也不够看哦。' },
      { t: 'say', who: 'marysue', expr: 'mock', show: true, text: '来吧——让这场童话，有个像样的结尾。' },

      { t: 'next', chapter: 'final' }
    ]
  },

  // ---------------------------------------------------------------- 最终战
  final: {
    cmds: [
      { t: 'scene', bg: 'mirror' },
      { t: 'duel', left: '蕾克', right: '玛丽苏', text: '玛丽苏：就凭你，也想照亮这面镜子？' },

      { t: 'say', who: 'marysue', show: true, text: '镜子已经记住过你的气息。' },
      { t: 'say', who: 'marysue', show: true, text: '第二次，可不会那么客气哦。' },
      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '上次交手，我还没学会如何击败你。' },
      { t: 'say', who: 'marysue', show: true, text: '……' },
      { t: 'say', who: 'marysue', show: true, text: '你不该回来的。' },
      { t: 'say', who: 'marysue', show: true, text: '人家把门关上，是为了你好。' },
      { t: 'say', who: 'rek', expr: 'eyes_open', show: true, text: '我不需要别人替我把门关上。' },
      { t: 'say', who: 'rek', expr: 'ready', show: true, text: '我也不会，死在你的故事里。' },

      // 玛丽苏的狂言
      { t: 'say', who: 'marysue', expr: 'creepy', show: true, text: '我最喜欢的故事，是那种——' },
      { t: 'say', who: 'marysue', expr: 'creepy', show: true, text: '去厮杀、去侵犯、被欺骗、被背叛，' },
      { t: 'say', who: 'marysue', expr: 'creepy', show: true, text: '最后迎来没有救赎的结局的故事。' },
      { t: 'say', who: 'marysue', expr: 'creepy', show: true, text: '越是挣扎，结尾就越难看哦。' },
      { t: 'say', who: 'marysue', expr: 'creepy', show: true, text: '而你迄今为止所积累的一切——' },
      { t: 'say', who: 'marysue', expr: 'creepy', show: true, text: '由我来全部毁掉。' },

      { t: 'bossIntro', id: 'marysue', frames: 180 },
      { t: 'battle', boss: 'marysue', after: 'marysue_defeat' }
    ]
  },

  // ---------------------------------------------------------------- 玛丽苏战败 · 诺登收场
  marysue_defeat: {
    cmds: [
      { t: 'mirrorfx', dur: 120, count: 34, power: 1.25, shake: 10 },
      { t: 'say', who: 'marysue', expr: 'shock', show: true, text: '这不可能……！' },
      { t: 'say', who: 'marysue', expr: 'shock', show: true, text: '我怎么会……输给一个样本……' },
      { t: 'say', who: 'rek', expr: 'ready', show: true, text: '到此为止了。' },

      { t: 'say', who: '', text: '空间里，响起另一个声音。' },
      { t: 'intro', id: 'norden' },
      { t: 'say', who: 'norden', show: true, text: '玛丽苏。' },
      { t: 'say', who: 'norden', show: true, text: '我要收回你掌中的箱庭权能。' },

      { t: 'say', who: 'marysue', expr: 'shock', show: true, text: '原来是你！？' },
      { t: 'say', who: 'marysue', expr: 'shock', show: true, text: '我就知道，蕾克不可能赢我……！' },
      { t: 'say', who: 'marysue', expr: 'smug', show: true, text: '给我等着！' },
      { t: 'say', who: 'marysue', expr: 'smug', show: true, text: '我们没完，诺登——白之女王！' },

      { t: 'mirrorfx', dur: 90, count: 22, power: 0.9 },
      { t: 'flash', seq: [{ c: 'green', f: 6 }, { c: 'white', f: 4 }, { c: 'black', f: 12 }] },
      { t: 'say', who: '', text: '绿色的光炸开，又迅速熄灭。' },

      { t: 'say', who: 'norden', show: true, text: '……很可惜，让她跑了。' },
      { t: 'say', who: 'norden', show: true, text: '也好。剩下的，就交给时间吧。' },
      { t: 'say', who: 'norden', show: true, text: '就此别过吧，蕾克小姐。' },

      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '诺登。' },
      { t: 'say', who: 'norden', show: true, text: '以后还会再见的。' },
      { t: 'say', who: 'norden', show: true, text: '——回去吧。' },

      { t: 'flash', seq: [{ c: 'white', f: 8 }, { c: 'black', f: 14 }] },
      { t: 'next', chapter: 'ending' }
    ]
  },

  // ---------------------------------------------------------------- 结局
  ending: {
    cmds: [
      { t: 'music', name: 'stop', fade: 1200 },
      { t: 'fade', to: 'clear', frames: 45 },
      { t: 'say', who: '', text: '她走出镜子的时候，天已经亮了。' },
      { t: 'say', who: '', text: '森林还是那片森林。' },
      { t: 'say', who: 'rek', expr: 'eyes_closed', show: true, text: '……累死了。' },
      { t: 'say', who: 'rek', expr: 'eyes_open', show: true, text: '格林。' },
      { t: 'say', who: 'rek', show: true, text: '我回来了。' },
      { t: 'say', who: '', text: '空地上，站着一个陌生人。' },
      { t: 'say', who: '', text: '蕾克从未见过那个人。' },
      {
        t: 'walk',
        playerX: 780,
        cam: true,
        target: { kind: 'mabel', x: 1180, label: '梅贝尔' },
        next: 'mabel_talk'
      }
    ]
  },

  // ---------------------------------------------------------------- 梅贝尔 · 打破第四面墙
  mabel_talk: {
    cmds: [
      { t: 'say', who: 'mabel', expr: 'eyes_closed', show: true, text: '哼哼～' },
      { t: 'say', who: '', text: '（她自顾自地哼着小曲，像在等什么人。）' },
      { t: 'say', who: 'mabel', expr: 'look_back', show: true, text: '哎呀呀，看来我们的女主角回来了？' },
      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '……' },
      { t: 'say', who: 'mabel', expr: 'eyes_open', show: true, text: '别用那种眼神看着我啦。' },
      { t: 'say', who: 'mabel', expr: 'eyes_open', show: true, text: '一个无足轻重的少女，有什么好警惕的？' },
      { t: 'say', who: 'mabel', expr: 'eyes_open', show: true, text: '我叫梅贝尔，一个戏份空白的少女。' },
      { t: 'say', who: 'mabel', expr: 'eyes_open', show: true, text: '在这个故事里，没有属于我的戏份……' },
      { t: 'say', who: 'mabel', expr: 'eyes_closed', show: true, text: '这段故事真的很枯燥呢，不是吗？' },
      { t: 'say', who: 'rek', expr: 'wary', show: true, text: '……你想表达些什么。' },
      { t: 'say', who: 'mabel', expr: 'eyes_open', show: true, text: '嘛，毕竟是作者一个人写出来的嘛。' },
      { t: 'say', who: 'mabel', expr: 'eyes_open', show: true, text: '故事大概也和本少女一样空虚吧。' },

      { t: 'say', who: 'mabel', expr: 'eyes_closed', show: true, text: '不过——恭喜你，见证了这个故事。' },
      { t: 'say', who: 'mabel', expr: 'eyes_open', show: true, text: '你知道走到这里意味着什么吗？' },
      { t: 'say', who: 'mabel', expr: 'eyes_open', show: true, text: '意味着你没有在半路关掉它。' },
      { t: 'mirrorfx', dur: 70, count: 14, power: 0.6 },
      { t: 'say', who: 'mabel', expr: 'look_back', show: true, text: '大部分人，看到第一面镜子就走了哦。' },

      { t: 'say', who: 'mabel', expr: 'look_back', show: true, text: '所以，替本少女谢谢那个写故事的人吧。' },
      { t: 'say', who: 'mabel', expr: 'look_back', show: true, text: '他写得确实很贫瘠——但他写完了。' },
      { t: 'say', who: 'rek', expr: 'eyes_closed', show: true, text: '……你也是他写的？' },
      { t: 'say', who: 'mabel', expr: 'eyes_closed', show: true, text: '谁知道呢。' },
      { t: 'say', who: 'mabel', expr: 'eyes_closed', show: true, text: '说不定，我只是留在这里的一句旁白。' },

      { t: 'say', who: 'mabel', expr: 'eyes_open', show: true, text: '好了，回到你的森林去吧，女主角。' },
      { t: 'say', who: 'mabel', expr: 'look_back', show: true, text: '毕竟你的故事已经演完了。' },
      { t: 'say', who: 'mabel', expr: 'look_back', show: true, text: '而我的故事，连第一页都还没有。' },

      { t: 'mirrorfx', dur: 150, count: 42, power: 1.45, shake: 8 },
      { t: 'say', who: 'mabel', expr: 'eyes_closed', show: true, text: '我们一定还会再见的。' },
      { t: 'say', who: '', text: '她转过身，像从来没出现过一样。' },
      { t: 'card', line1: '主线 · 终', line2: '镜面碎成了千万片，每一片里都有她', frames: 200 },
      { t: 'end', kind: 'win' }
    ]
  }
};
