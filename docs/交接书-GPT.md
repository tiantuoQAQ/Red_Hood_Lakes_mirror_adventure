# 《镜》(MIRROR) 项目交接书

> 交付对象：接手的 GPT（下一任代码/剧情负责人）
> 项目根目录：`E:\UserDATAxtmr\Documents\DSH\mirror-jam`
> 交接时间：2026-10-24
> 赛事：CODEJAM 2026 / SUDA CEA
> 截止：**2026-10-25 17:00 提交**，18:00 答辩

---

## 0. 一句话说明

一个 HTML5 Canvas + 原生 JS、**零依赖、零构建**的横版 Boss Rush 小游戏。玩家操纵「小红帽 蕾克」，进入镜中世界，依次击败「猩红魔姬 · 雷帝」与「幕后黑手 玛丽苏」，最后被白之兔诺登送出镜面，回到森林。

**当前状态：从主菜单可以一路打到结局，剧情全部写完，美术立绘全部成套，测试全绿。**

---

## 1. 怎么跑起来

### 直接双击
```
index.html
```
（因为用了 `file://` 读图，本地双击即可；若浏览器拦截，用下一条）

### 起本地服务器（推荐）
```powershell
cd E:\UserDATAxtmr\Documents\DSH\mirror-jam
python -m http.server 8000
# 打开 http://127.0.0.1:8000/index.html
```

### 调试 / 验收用 URL 参数（非常重要，验收答辩时也用得上）

| 参数 | 作用 |
| --- | --- |
| `?chapter=<章节名>` | 直接从某一章剧情开始，例：`?chapter=mirror_meet` |
| `?auto=1&boss=crimson&ff=900` | 自动战斗跑指定 Boss 900 帧（截图/验收用） |
| `?px=1200` | 调试时把玩家初始位置放到 x=1200 |
| `?walk=1&ff=160` | 直接进「森林走位段」 |
| `?throne=1&px=1150&ff=80` | 直接进「王座走位段」 |
| `?story=0` | 跳过剧情直接进战斗 |
| `?theme=mirror` | 强制镜中世界主题 |

### 测试命令
```powershell
node test/logic_test.js     # 38 项，逻辑/状态机/Boss/技能
node test/story_test.js     # 13 项，章节连通性、能否打到结局
node test/fx_smoke.js       # 9 项，特效冒烟
node test/config_check.js   # 31 项滑条常量范围
```
当前：**全部通过**。

---

## 2. 目录结构与文件职责

```
mirror-jam/
├── index.html              入口，按顺序引入所有脚本（无模块系统，全是全局函数）
├── README.md               简版说明
├── src/
│   ├── config.js           常量：W/H、GROUND_Y、WORLD_W、COLORS、CFG、PHASES、BOSSES
│   ├── game.js             Game 状态对象、update 主循环分派、Boss 生成、技能、走位、镜头
│   ├── story.js            ★ 全部剧情数据（10 个章节，命令数组）
│   ├── cutscene.js         ★ 剧情引擎：解释命令、打字机、立绘、双人构图、闪白、竖幅
│   ├── render.js           渲染：背景视差、地面、倒影、子弹、HUD、走位道具（王座）
│   ├── sprites.js          玩家四层分件（cape/hair/body/head）
│   ├── patterns.js         Boss 弹幕模式
│   ├── fx.js               粒子/球体特效
│   ├── gfx.js              图形工具（star 路径、roundRect 等）
│   ├── audio.js            音效/音乐桩（WebAudio，未接入正式曲目）
│   ├── input.js            键鼠输入，鼠标坐标 → Game.mouse
│   └── main.js             启动、URL 参数、固定步长 1/60 循环、截图辅助
├── art/
│   ├── portrait/           ★ 对话立绘（21 张，已全部压色 + 肤色统一）
│   ├── obj/throne.png      王座贴图（走位段用）
│   ├── cg/cutin_*.png      ★ 必杀演出大特写（Boss 最后阶段切入）
│   ├── bg/mirror.jpg       镜中世界背景（+ mirror_alt.jpg 备用）
│   ├── fx/particle_strip.png
│   ├── ref/                出图参考（AI 生成原图，不需要进游戏）
│   └── rek/                玩家战斗小人分件（目前是占位）
├── tools/                  ★ 美术管线脚本（Python）
│   ├── check_palette.py    色相检查（最重要，见第 6 节）
│   ├── force_palette.py    强制压色（去色/归位）
│   ├── unify_palette.py    统一色相（红/绿/青三通道）
│   ├── prep_portrait.py    白底→透明、裁边、缩放、底部对齐（512×768）
│   ├── despeckle.py        清除压色后残留的绿色斑点（皮肤上的脏点）
│   ├── match_skin.py       把各张立绘的肤色灰阶对齐到统一值
│   └── recolor.py          改色工具
├── test/                   四个 node 测试
├── art_preview/            验收图（cast.png / marysue_check.jpg / throne.png / meet.png …）
├── docs/                   简报、文案、出图提示词、交接书（本文件）
└── _verify*.html           单页验收器（分别验收剧情、特效、立绘）
```

---

## 3. 架构说明

### 3.1 全局状态
```js
Game = {
  mode: 'title' | 'story' | 'walk' | 'play' | 'dead' | 'win',
  player, boss, shots, bullets,
  cam: { x },          // 镜头（世界 2400 宽，屏幕 1280）
  mouse: { x, y },     // 世界坐标，用于瞄准
  theme,               // 背景主题
  walk: { untilX, next, target, bg, cam, props },
  afterBattle,         // 战斗结束进哪一章
  skills,              // 已解锁技能
  currentBossId
}
```

### 3.2 剧情引擎（`cutscene.js`）
`STORY[章节id] = { cmds: [ 命令对象... ] }`，`Cutscene.start(id)` 逐条执行。

**支持的命令（全部已实现）**：

| t | 说明 |
| --- | --- |
| `scene` | 换背景 |
| `fade` | 黑场淡入淡出 `{to:'black'|'clear', frames}` |
| `wait` | 停顿 |
| `card` | 章节卡（大标题 + 副标） |
| `say` | **主力命令**：`{who, text, expr, show, style, shake, bump, screenshake}` |
| `bubble` | 气泡台词 |
| `duel` | 左右对峙横幅 |
| `letter` | 信件（已实现但当前剧情未用） |
| `intro` | 角色登场竖幅 |
| `title` | 称号竖幅（「猩红魔姬 · 雷帝」用的这个） |
| `bossIntro` | 战斗前 Boss 名条 |
| `cg` | 插入 CG |
| `flash` | 闪屏 `{seq:[{c:'white'|'black'|'green', f}]}` |
| `pose` | 只切表情不说话 `{who, expr, frames}` |
| `walk` | 交还玩家走位 `{untilX, next, bg, cam, props}` |
| `battle` | 开战 `{boss, after}` |
| `grant` | 解锁技能 `{skill, banner}` |
| `next` | 跳下一章 |
| `end` | 结束（进 win） |

**双人对话构图（后期加的重要特性）**：
- 蕾克**永远在左**（`W*0.26`），对方**在右边**（`W*0.74`，水平翻转，脸朝左）
- 谁说话谁亮（100%），另一方压到 **60% 不透明度**
- 说话者背后有一团柔光 `focusGlow()`
- 表情通过文件名自动解析：`art/portrait/<角色>_<expr>.png`，找不到就退回基础图，再找不到画占位块

### 3.2.1 必杀演出（cutin）
Boss 血量掉到**最后一个阶段**时冻结战场，在画面中央插入一块**斜切的漫画分镜**（约 62% 宽 / 74% 高，轻微旋转），
里面是黑白漫画风大特写 + 巨大感叹号；四周仍能看到被压暗的战场与 HUD（**不是全屏覆盖**）。
从右侧滑入 → 白闪 → 停留 → 淡出，全程约 156 帧（2.6 秒）。

- 触发：src/game.js 的 updateBoss() 里，ph === phases.length - 1 时调用 startCutin(b.id)
- 冻结：update() 开头检测 Game.cutin，只推进计时、不更新任何实体
- 绘制：src/render.js 的 drawCutin()，图片路径固定为 rt/cg/cutin_<bossId>.png
- 每个 Boss 只放一次（oss.cutinDone）
- **技名**：src/game.js 顶部的 CUTIN_NAMES 表（红之惨剧 / 断罪；箱庭终演 / 无救赎的童话），
  由 drawCutinName() 逐字绘制（斜切 + 粗描边 + 手写字距），改名字只改这张表
- 缺图时画占位提示，不会崩

### 3.2.2 战斗 BGM
两首战斗曲随包放在 udio/（都是 mp4 容器里的 AAC 音轨，浏览器原生解码）：

| 文件 | 用在 |
| --- | --- |
| udio/crimson_bgm.mp4 | 猩红魔姬战（黑之裁判 · 金属翻弹版，黑骑士琳达梅尔） |
| udio/marysue_bgm.mp4 | 玛丽苏战（BlackSouls2 - 玛丽·安） |

- 播放入口：src/audio.js 的 Music.play('crimson'|'marysue') / Music.stop(fade)
- 触发方式：剧情命令 { t:'music', name:'crimson' }，插在**战斗前的对话开头**，
  即 mirror_meet（魔姬）与 crimson_fall（玛丽苏登场）两章的第一条
- 结局第一章用 { t:'music', name:'stop', fade:1200 } 淡出
- 自动播放策略：首次按键/点击会重试播放（Music.retry 挂了 keydown/pointerdown 监听）
- 调试：?mtest=crimson 直接试播
- 缺音量条：目前固定 0.55，想加设置项可接 Music.toggleMute() / Sfx.toggleMute()

### 3.2.3 镜之碎片特效（主题「镜」）

主题是「镜」，所以在两个情绪高点加了**碎裂镜面**演出：白色裂纹从一点放射 + 半透明镜片飞散。

- 文件：`src/mirrorfx.js`，暴露 `MirrorFx.start({dur,count,power,x,y})` / `update()` / `draw(ctx)` / `reset()`
- 剧情命令：`{ t:'mirrorfx', dur, count, power, shake, x, y }`
  - `dur` 持续帧数、`count` 碎片数量、`power` 尺寸与速度倍率、`shake` 附带屏幕震动
- 绘制层级：在角色立绘**之上**、对话框与 UI **之下**（`cutscene.js` 的 `draw()` 里调用）

**当前用在 4 个位置（`src/story.js`）**

| 章节 | 时机 | 参数 |
| --- | --- | --- |
| `marysue_defeat` | 玛丽苏被击败、喊「这不可能……！」之前 | `dur:120, count:34, power:1.25, shake:10` |
| `marysue_defeat` | 她放完狠话、绿光逃走那一刻 | `dur:90, count:22, power:0.9` |
| `mabel_talk` | 梅贝尔说「大部分人，看到第一面镜子就走了哦」 | `dur:70, count:14, power:0.6` |
| `mabel_talk` | 升华收尾、她说「我们一定还会再见的」 | `dur:150, count:42, power:1.45, shake:8` |

**调参**：`power` 控制碎片大小与速度；想更「重」把 `count` 提到 60+、`power` 1.8；
想更「轻」用 `count` 12~16、`power` 0.5。裂纹条数写死在 `start()` 里（9~13 条）。

**可扩展**：也能给「进入镜中世界」的转场用（`enter_mirror` 目前是纯黑场），
或在 Boss 最后一阶段 cutin 之后补一次碎裂。

### 3.3 渲染
- 世界宽 `WORLD_W = 2400`，屏幕 1280×720，地面 `GROUND_Y = 574`
- 镜头平滑跟随 `1 - Math.pow(0.0001, dt)`，Boss 出场时会把双方框进画面
- 镜中世界背景：缩放 1.35W + 视差 0.25 + 52% 压暗 + 地面倒影（alpha 0.26）
- 子弹按 `kind`（hazard / homing / rain / lance）分层，预渲染辉光精灵缓存

---

## 4. 完整剧情线（10 章）

> 全部在 `src/story.js`。改文案只改这个文件，改完跑 `node test/story_test.js`。

| # | 章节 id | 内容 |
| --- | --- | --- |
| 1 | `prologue` | 蕾克读信（写给格林）；章节卡「悲愤交加的勇者 / 踏上了寻回珍视之人的旅途」；走位进森林 |
| 2 | `ambush` | 玛丽苏黑影现身；蕾克「在砍下你的头颅之前，我是不会死的。」；玛丽苏「人家可是……从来没有把你当成敌人哦。」→ 陷阱「啪嗒。」→ 闪白 + CG → 走位坠入虚空 |
| 3 | `wake_talk` | 白之女王 · 诺登（观察者）与蕾克对话；称号竖幅；指引进入镜子 |
| 4 | `enter_mirror` | 过场 |
| 5 | `mirror` | 镜中世界：无回声、倒着长的树、干净得像没人来过；**走位到王座前**（`?throne=1` 可单独看） |
| 6 | `mirror_meet` | 雷帝坐王座登场：闭眼「……」→ 蕾克震惊 → 「哟，终于来了？」→ 起身 → 称号「猩红魔姬 · 雷帝」→ 自我介绍 → 「此即，汝葬身之地。」→ 开战 |
| 7 | `crimson_fall` | **魔姬战败 → 真相 → 传承**（见下） |
| 8 | `final` | 最终战前玛丽苏狂言 → 开战 |
| 9 | `marysue_defeat` | 玛丽苏战败 → 诺登收回箱庭权能 → 玛丽苏放狠话逃走 → 诺登送蕾克出镜 |
| 10 | `ending` | 天亮、回森林、叫格林；结尾两行「空地上站着一个人。她没有见过她。」（梅贝尔伏笔）→ 结局卡「主线 · 终」 |

### 4.1 关键设定（**极重要，别写歪**）

- **玛丽苏**：真正的幕后黑手。她**创造了**猩红魔姬，并且**控制魔姬的亲人朋友背叛、欺负她**，最后假惺惺地「拯救」魔姬、赐予力量，引导她霸占镜中世界。她享受的是「看别人挣扎、被背叛、迎来没有救赎的结局」。
- **猩红魔姬 · 雷帝**：和蕾克同一副面孔（蕾克的暗色版本）。她的核心悲剧是——**连恨都是别人安排的**。她最后选择把力量交给蕾克，是她人生第一次自己做决定。她**不叫蕾克「姐姐」**，只叫「蕾克」。
- **蕾克**：红之勇者。嘴上很硬，心里一直在意格林。拿到「红之惨剧」。
- **诺登**：白之兔，白之女王，观察者。结尾收回「箱庭」权能，说「以后还会再见的」。
- **梅贝尔**：虚无少女，结尾在森林空地登场，**菜单对话留待后续**（本次未写）。

### 4.2 传承段台词（这段是重点，改的时候注意语气）

```
旁白：玛丽苏抬起手，绿色的东西在她掌心聚成一根针。
雷帝：……原来如此。
雷帝：我这一生，连恨都是别人给的。
蕾克：雷帝！
雷帝（闭眼）：蕾克。
雷帝（闭眼）：这次，换我自己选一次。
雷帝（闭眼）：把我的力量拿去吧——它本来就不该属于我。
旁白：红色的东西从她胸口流出来。很烫，像有人把手按在胸口。
【解锁：红之惨剧】章节卡「红之惨剧 / 夺回被夺走的一切」
蕾克（睁眼）：……我接住了。
```

### 4.3 玛丽苏狂言（最终战前）

```
玛丽苏（渗人）：我最喜欢的故事，是那种——
玛丽苏（渗人）：去厮杀、去侵犯、被欺骗、被背叛，
玛丽苏（渗人）：最后迎来没有救赎的结局的故事。
玛丽苏（渗人）：越是挣扎，结尾就越难看哦。
玛丽苏（渗人）：而你迄今为止所积累的一切——
玛丽苏（渗人）：由我来全部毁掉。
```

---

## 5. 角色与立绘资产表

### 5.1 对话立绘文件（全部在 `art/portrait/`，512×768 PNG，透明底）

| 角色 | 文件 | 用途 |
| --- | --- | --- |
| 蕾克 | `rek.png` | 常态 |
| | `rek_eyes_closed.png` | 闭眼（读信/忍耐） |
| | `rek_eyes_open.png` | 睁眼（决心） |
| | `rek_wary.png` | 警惕 |
| | `rek_ready.png` | 备战（当前兼作「愤怒」用） |
| | `rek_shock.png` | 震惊 |
| 猩红魔姬 | `crimson_stand.png` | 起身站直 |
| | `crimson_seated_open.png` | 坐王座·睁眼（蔑视） |
| | `crimson_seated_closed.png` | 坐王座·闭眼 |
| | `crimson_stand_ready.png` | 备战（持刀压低重心） |
| | `crimson_defeated.png` | **战损**（单膝跪地、捂胸、斗篷破损） |
| 玛丽苏 | `marysue.png` | 得意 |
| | `marysue_tease.png` | 调戏/挑衅 |
| | `marysue_fake.png` | 假惺惺（假哭） |
| | `marysue_scheming.png` | 得逞 |
| | `marysue_star.png` | 星芒瞳（兴奋） |
| | `marysue_mock.png` | 大小眼嘲笑（一只眼眯缝露瞳） |
| | `marysue_creepy.png` | 渗人的笑（最终战狂言专用） |
| | `marysue_shock.png` | 战败惊讶 |
| 诺登 | `norden.png` | 唯一一张（温柔安静） |
| 梅贝尔 | `mabel.png` | 唯一一张（小恶魔式打量） |

### 5.2 其它美术
| 文件 | 说明 |
| --- | --- |
| `art/obj/throne.png` | 巴洛克王座，3/4 视角，走位段用 |
| `art/bg/mirror.jpg` | 镜中世界背景（倒生树 + 灰雾 + 地面） |
| `art/fx/particle_strip.png` | 8 帧粒子条 |

> **换图后看不到变化**：地图立绘的图片地址带了版本号（`src/render.js` 的 `ART_VER`），
> 替换 `art/char/*_idle.png` 后把 `ART_VER` 加 1 即可强制刷新缓存。

### 5.3 两种「立绘」，别搞混（**重点**）

项目里有**三套角色图**，用途完全不同，放错目录就不会显示：

| 类型 | 目录 / 命名 | 规格 | 用在哪 | 现状 |
| --- | --- | --- | --- | --- |
| **对话立绘** | `art/portrait/<角色id>_<表情>.png` | 512×768，半身（头顶到大腿），透明底，底部对齐 | 对话框左右两侧（`Cutscene` 的 `say`） | ✅ **24 张全部完成** |
| **地图内待机立绘** | `art/char/<角色id>_idle.png` | 单张 PNG，脚底对齐画布底部、四周留安全边距（游戏内按高度缩放到 300~340px） | 走位段里站着的 NPC（梅贝尔 / 诺登） | ✅ **2 张已完成**（诺登/梅贝尔）；缺图时代码会临时用对话立绘代替 |
| **玩家战斗小人** | `art/rek/{cape,hair,body,head}.png` | 四层分件，同尺寸同站位 | 战斗中的蕾克 | ⏳ 占位 |

补充说明：

- 对话立绘的表情差分靠**文件名后缀**自动匹配：`say` 里写 `expr:'look_back'` 就找
  `art/portrait/mabel_look_back.png`，找不到退回 `mabel.png`，再找不到画占位块。
- 地图待机立绘的接入点在 `src/render.js`：`getCharIdle()` / `drawCharIdle()`，
  文件放进去**刷新即生效**，不用改代码。
- 两者的配色要求相同（三色 + 中性灰），都要跑 `check_palette.py` 到 **0.00%**。
- 出图规格与命名详见 `art/char/README.md`。

### 5.3 画风 / 比例基准
- 画风：**粗黑描边 + 高对比赛璐璐平涂 + 两段阴影**
- 头身比：**统一约 5 头身**（蕾克为基准；诺登/梅贝尔/魔姬/玛丽苏都已对齐重画过）
- 出图参考在 `art/ref/`，其中 `chibi.png` 是**画风基准图**，重新出图时用它当参考最稳

---

## 6. 三色硬规则（**不可违反，评委会查**）

> 简报硬性要求：**最终画面最多 3 个色相**，灰度允许。

允许的色相（全部已经固化成工具常量）：

| 颜色 | HEX | 用途 |
| --- | --- | --- |
| 红 | `#FF0000` | 我方 / 蕾克 / 魔姬 |
| 黄绿 | `#82FF00` | 危险 / 玛丽苏 |
| 青蓝 | `#00BAFF` | 环境 / 中立 / 诺登·梅贝尔 |
| 中性灰 | R=G=B | 一切低彩度部分（皮肤、白发、背景） |

### 检查与修正工具
```powershell
python tools/check_palette.py art/portrait        # 逐张报越界百分比，必须 0.00%
python tools/unify_palette.py <png>               # 统一色相（红/绿/青三通道）
python tools/force_palette.py <png>               # 最后一道：残余杂色去色
python tools/despeckle.py <png>                   # 清绿斑（压色后皮肤上的脏点）
python tools/match_skin.py <png...> --target 0.70 # 统一肤色灰阶（只动低彩度像素）
```
**正确顺序**：`prep_portrait.py` → `unify_palette.py` → `force_palette.py` → `despeckle.py` → `match_skin.py` → `check_palette.py`

> 肤色规范：皮肤只能是**中性灰（R=G=B）**，这是「最多 3 个色相」的直接结果，
> 所以立绘天生带一点“石像感”。能调的只有**明度**，目前全员统一到脸部灰阶 **0.70**。
> 如果觉得某张偏暗/偏白，用 `match_skin.py <png> --target 0.70` 重跑即可，不要手动调色。

### 踩过的坑（已经在工具里修好，改动工具时注意）
1. **肤色被判成红色** → 红通道门槛现在是「彩度 ≥ 0.42」，否则皮肤会变粉红。
2. **黄绿与青的色相重叠带（151°–167°）** → 判定顺序必须**绿在前、青在后**，否则绿泳衣上会冒青斑。
3. **浅色头发丢掉绿色** → 绿通道条件改成「彩度 ≥ 0.16 且亮度 ≤ 0.88」。
4. **force_palette 不要「拧」色相**：高彩度错色一律去色，拧会把肤色拧成红色。
5. **绿/青重叠带（151°–167°）** 会让绿衣服上冒青斑 → 判定顺序必须**绿在前、青在后**；绿通道门槛现在是「彩度 ≥ 0.20 且亮度 ≤ 0.86」，太松会把皮肤染绿，太紧会丢头发。
6. **肤色深浅不统一**：出图批次不同，脸亮度会从 0.49 飘到 0.85 → 一律用 `match_skin.py` 拉回 0.70。
7. `unify_palette.py` 目前只认红/绿/青三通道，加新色相要同时改 `check_palette.py`。
8. `despeckle.py` 的判定是「孤立绿像素转灰」，窗口默认 9×9、阈值 0.35，改小会把头发的细边啃掉。

---

## 7. 已完成清单

### 工程 / 系统
- [x] 固定步长 1/60 主循环、`mode` 状态机（title/story/walk/play/dead/win）
- [x] 世界宽 2400 + 平滑镜头跟随 + Boss 双目标构图
- [x] 鼠标瞄准射击（无自动瞄准）、弱磁吸、子弹按类型分层 + 辉光预渲染
- [x] 玩家四层分件（cape/hair/body/head，头部绕颈部旋转）
- [x] 技能：冰封 36 伤；**红之惨剧**（清屏 + 200 帧无敌 + 80 伤）
- [x] 两个 Boss 的分阶段血条（魔姬 240HP/5 阶段，玛丽苏 420HP/6 阶段且总血条隐藏）
- [x] 走位段系统（`untilX` 触发 / `target` + W 交互 / 场景道具 props / 可选镜头跟随）
- [x] **必杀演出 cutin**：最后阶段切入大特写 + 冻结 + 白闪 + 电影黑边
- [x] 剧情引擎全部 19 条命令；双人构图 + 说话者高亮 + 10 帧平滑退场 + 防连点
- [x] 打字机文本（句号 14 帧、逗号 7 帧、CPS 0.9）
- [x] 绿色闪光（`flash` 的 `green`）供玛丽苏逃跑使用

### 剧情
- [x] 10 章全部写完，能从标题打到结局
- [x] 魔姬「连恨都是别人给的」传承段
- [x] 玛丽苏狂言、诺登收场、梅贝尔伏笔

### 美术
- [x] 21 张立绘，全部统一到同一画风 / 5 头身 / 三色规范
- [x] 王座贴图、镜中世界背景、粒子条
- [x] 调色管线三件套 + 修完所有已知 bug

### 测试
- [x] logic 38 / story 13 / fx 9 / config 31 全绿

---

## 8. 剩余任务（按优先级）

### P0 · 交付必需
1. **战斗内的小人分件**（`art/rek/` 目前是占位）
   - 玩家四层分件已定好接口：`cape / hair / body / head`，画布尺寸与锚点见 `src/sprites.js`
   - 需要即梦出图：奔跑、起跳、射击、受击、蓄力五组姿势（或单张 + 程序变换）
   - 落点：`src/sprites.js` 的 `drawLayer`，以及 `art/rek/*.png`

2. **战斗手感与演出**
   - 受击星芒、Boss 出场演出、死亡爆炸
   - 落点：`src/fx.js`、`src/render.js`

3. **音效 / BGM 接入**
   - `src/audio.js` 已经是 WebAudio 桩，有 `playSfx(name)` 结构
   - **用户手里有魔姬与玛丽苏的专属战斗曲**，要留好接口：`Config.MUSIC = { crimson: '...', marysue: '...' }`
   - 落点：`src/audio.js`、`src/game.js` 的 `startBattle`

### P1 · 内容补完
3.5 **必杀演出的音效**：画面与技名已就位，还缺一声碎裂/爆音（接到 src/audio.js 的 Sfx.phase() 或新加 Sfx.cutin()）

4. **梅贝尔的菜单对话**（设定已给：虚无少女，结尾出现在森林空地）
   - 新章节 `mabel_talk`，在 `ending` 之后触发
   - 立绘 `mabel.png` 已有
5. **诺登的额外表情**（目前只有一张，wake_talk 里需要「微笑 / 注视」）
6. **魔姬的「战损」表情**：`crimson_fall` 段现在用 `crimson_stand` 顶替，最好补 `crimson_defeated.png`
7. **蕾克的「愤怒」表情**：`crimson_fall` 里用 `rek_ready` 顶替，可补 `rek_angry.png`

### P2 · 打磨
8. 死区镜头（`updateCamera` 里给玩家移动加 120px 死区）
9. 命中的星爆反馈、屏幕震动分级
10. 镜中世界背景地平线与 `GROUND_Y` 的对齐（现在略高）
11. `letter` 命令目前未使用，可用在序章的「信」上
12. 结局后加「再玩一次」结算面板

### P3 · 代码优化（交给 GPT 的重点）
- `src/render.js`（29KB）与 `src/cutscene.js`（33KB）偏大，可按职责拆：
  - `render/` → `background.js` / `entities.js` / `hud.js` / `walk.js`
  - `cutscene/` → `player.js`（命令解释）/ `director.js`（立绘构图）/ `text.js`（打字机）
- 剧情命令建议加一层校验（启动时扫一遍 `STORY`，检查未知 `t`、不存在的 `who`/`expr`、`next` 指向的章节是否存在）——现在只能靠 `story_test.js` 跑通验证
- 立绘加载：现在每帧 `getArt()` 查缓存，建议改成预加载表 + 加载完成回调
- 常量集中：`CFG` 已集中，但 `cutscene.js` 里还有一堆魔法数字（`W*0.74`、`H*0.52`、`380/540`），建议提到 `config.js` 的 `LAYOUT`
- 建议保持：**零依赖、零构建**。如果一定要引入打包器，必须保证 `index.html` 双击可跑（答辩现场不联网）。

---

## 9. 交接纪律（请务必遵守）

1. **不要动色相**。新图一律走 `prep → unify → force → check`，`check_palette` 必须 0.00%。
2. **改剧情只改 `src/story.js`**，改完立刻 `node test/story_test.js`。
3. **不要用 PowerShell 的 `Set-Content` / `Out-File` 写含中文的源码或数据文件**——会把 UTF-8 写成 GBK 花屏（本项目踩过两次，靠 `git checkout --` 救回）。用编辑工具或 Python 的 `io.open(..., encoding='utf-8')`。
4. 每完成一块就 `git commit`，提交信息写清「做了什么」。用户对上下文丢失很敏感，**提交哈希要报给他**。
5. 立绘替换后记得同步 `art/ref/` 的原始图，方便以后重出。
6. 验收图统一放 `art_preview/`，命名见已有文件。

---

## 10. 关键常量速查（`src/config.js`）

```js
W = 1280, H = 720, GROUND_Y = 574, WORLD_W = 2400
MIRROR_X = WORLD_W / 2
ARENA = { left: 48, right: WORLD_W - 48, top: 48, bottom: GROUND_Y }

COLORS = { player:'#FF0000', hazard:'#82FF00', env:'#00BAFF', ... }

BOSSES = {
  crimson : { name:'猩红魔姬 蕾克', hp:240, phases:[1.0,0.8,0.6,0.4,0.2] },
  marysue : { name:'幕后黑手 玛丽苏', hp:420, hideTotal:true, phases:[1,5/6,4/6,3/6,2/6,1/6] }
}

技能：冰封 { damage:36, invFrames:130 }
     红之惨剧 { 清子弹 + 200 帧无敌 + 80 伤 }
```

---

## 11. 建议的第一件事

1. 双击 `index.html`，从标题打到结局，确认体验基线（约 6~8 分钟）。
2. `node test/story_test.js` 确认交接时是绿的。
3. 从 **P0-1 战斗小人分件** 或 **P3 代码拆分** 里挑一个开始——前者影响观感，后者影响后续维护速度。

祝顺利。
