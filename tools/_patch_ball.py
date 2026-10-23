# 球形态改为：空中(按住上 + 按冲刺)进入，松开冲刺退出，落地不退出
import io

ROOT = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam'
ok = True

def patch(rel, pairs):
    global ok
    p = ROOT + '\\' + rel
    t = io.open(p, encoding='utf-8').read()
    for old, new in pairs:
        if old not in t:
            print('!! 锚点缺失 %s: %r' % (rel, old[:60]))
            ok = False
            continue
        t = t.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
    print('%s patched' % rel)

# ---------------- config：去掉长按帧数，加落地是否退出
patch('src/config.js', [
("""    ballHoldFrames: 10,  // 空中长按冲刺多少帧后变成球
    ballLaunchFrames: 5, // 进入球形态后强制上冲的帧数""",
 """    ballLaunchFrames: 5, // 进入球形态后强制上冲的帧数
    ballExitOnLand: false, // 落地是否退出球形态（当前设计：不退出，松开冲刺才退出）"""),
])

# ---------------- game：进入 / 退出逻辑
patch('src/game.js', [
("""  // ---- 进入球形态：长按冲刺（点按只冲刺，按住才转球）----
  // 按下瞬间无法预知是点按还是长按，所以冲刺必须立刻执行、长按再升级为球形态。
  if (!p.ball) {
    if (!Input.held('dash')) p.ballLock = false;   // 松开后重新解锁
    if (Input.held('dash') && !p.ballLock) p.dashHold++;
    else p.dashHold = 0;

    if (p.dashHold >= P.ballHoldFrames && !p.ballLock && p.stamina > P.ballMinStamina) {
      p.ball = true;
      p.dashHold = 0;
      p.ballLaunch = P.ballLaunchFrames; // 起手强制上冲，避免贴地进入瞬间被地面取消
      p.dashT = 0;
      p.vx *= 0.4;
      p.vy = -P.ballSpeed;
    burst(p.x, p.y, COLORS.player, 14);
      Sfx.ballOn();
    }
  } else {
    p.dashHold = 0;
  }""",
 """  // ---- 球形态：空中「按住 ↑ + 按冲刺」进入 ----
  // 必须离地：地面上按组合键只算普通冲刺，否则会变成站桩无敌。
  if (!p.ball) {
    if (!p.onGround && up && Input.pressed('dash') && p.stamina > P.ballMinStamina) {
      Input.consume('dash');           // 吃掉这次按下，不再额外触发一次普通冲刺
      p.ball = true;
      p.ballLaunch = P.ballLaunchFrames;
      p.dashT = 0;
      p.vx *= 0.4;
      p.vy = -P.ballSpeed;
      burst(p.x, p.y, COLORS.player, 14);
      Sfx.ballOn();
    }
  } else if (!Input.held('dash')) {
    // 松开冲刺立刻变回人——这才是玩家期待的控制感
    endBall(false);
  }"""),

# 落地：默认不退出，贴地悬浮等玩家松手
("""    if (p.ball) {
      endBall(true);           // 落地即取消球形态（核心设计）
    } else {""",
 """    if (p.ball) {
      if (P.ballExitOnLand) endBall(true);
      else p.vy = 0;           // 贴地悬浮，等玩家松开冲刺
    } else {"""),

# endBall 不再需要 ballLock
("""  p.ball = false;
  p.vx = 0;
  p.vy = 0;
  // 落地时如果还按着冲刺，不应该立刻又变回球——必须松开再按
  p.ballLock = true;
  p.dashHold = 0;""",
 """  p.ball = false;
  p.vx = 0;
  p.vy = 0;
  p.ballLaunch = 0;"""),

# 玩家字段清理
("""    ball: false,
    ballLaunch: 0,
    ballLock: false,
    dashHold: 0,""",
 """    ball: false,
    ballLaunch: 0,"""),
])

# ---------------- 面板：删掉长按帧数滑块
patch('index.html', [
("""    <div class="row">
      <label>球形态长按帧数 <output data-out="player.ballHoldFrames"></output></label>
      <input type="range" data-cfg="player.ballHoldFrames" min="2" max="30" step="1">
    </div>
""", ""),
])

# ---------------- 画面提示文案
patch('src/render.js', [
("""      ['冲刺（点按）', 'Shift 或 K'],
      ['球形态（长按，无敌，落地取消）', '按住冲刺'],""",
 """      ['冲刺', 'Shift 或 K'],
      ['球形态（无敌）', '空中 按住↑ + 冲刺'],"""),
("""  mono(ctx, '点按冲刺=冲刺 · 按住冲刺=球形态 · 落地取消', W - 60, 668, 11, COLORS.dim, 'right');""",
 """  mono(ctx, '空中 按住↑ + 冲刺 变球 · 松开冲刺变回', W - 60, 668, 11, COLORS.dim, 'right');"""),
])

print('OK' if ok else 'HAS MISSES')
