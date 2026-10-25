# 接线：config 增加 sprite 段，main 载入，render 优先用贴图，面板加对齐滑块
import io

ROOT = r'E:\UserDATAxtmr\Documents\DSH\mirror-jam'
ok = True


def patch(rel, pairs):
    global ok
    p = ROOT + '\\' + rel
    t = io.open(p, encoding='utf-8').read()
    for old, new in pairs:
        if old not in t:
            print('!! 锚点缺失 %s: %r' % (rel, old[:70]))
            ok = False
            continue
        t = t.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='\n').write(t)
    print('%s patched' % rel)


patch('src/config.js', [
    ("""  beam: { width: 26, warmup: 45, active: 34, len: 1700 },""",
     """  // 角色贴图：单图 + 少量分件。三张图必须同尺寸同站位。
  // hairDx/capeDx 是「对齐微调」，即梦出的分件对不齐时在这里拖到对齐。
  sprite: {
    id: 'rek',
    dir: 'art/rek',
    scale: 0.5,       // 按 2 倍出图，这里缩一半
    hairDx: 0,
    hairDy: 0,
    capeDx: 0,
    capeDy: 0
  },
  beam: { width: 26, warmup: 45, active: 34, len: 1700 },"""),
])

patch('src/main.js', [
    ("""requestAnimationFrame(frameLoop);""",
     """// 载入角色贴图（缺图不影响运行，会退回程序化图形）
Sprites.load(CFG.sprite.id, CFG.sprite.dir);

requestAnimationFrame(frameLoop);"""),
])

patch('src/render.js', [
    ("""  const blink = p.invT > 0 && !p.ball && Math.floor(Game.frame / 4) % 2 === 0;
  ctx.save();
  if (blink) ctx.globalAlpha = 0.40;

  if (p.ball) {""",
     """  const blink = p.invT > 0 && !p.ball && Math.floor(Game.frame / 4) % 2 === 0;
  ctx.save();
  if (blink) ctx.globalAlpha = 0.40;

  // 有贴图就用贴图，没有就退回程序化的菱形
  if (drawCharacterSprite(ctx, p)) {
    ctx.restore();
  } else if (p.ball) {"""),
])

patch('index.html', [
    ("""  <script src="src/audio.js"></script>""",
     """  <script src="src/sprites.js"></script>
  <script src="src/audio.js"></script>"""),

    ("""    <div class="row">
      <label>输入缓冲帧 <output data-out="player.inputBuffer"></output></label>
      <input type="range" data-cfg="player.inputBuffer" min="0" max="20" step="1">
    </div>""",
     """    <div class="row">
      <label>输入缓冲帧 <output data-out="player.inputBuffer"></output></label>
      <input type="range" data-cfg="player.inputBuffer" min="0" max="20" step="1">
    </div>
    <div class="row">
      <label>后发对齐 X <output data-out="sprite.hairDx"></output></label>
      <input type="range" data-cfg="sprite.hairDx" min="-60" max="60" step="1">
    </div>
    <div class="row">
      <label>后发对齐 Y <output data-out="sprite.hairDy"></output></label>
      <input type="range" data-cfg="sprite.hairDy" min="-60" max="60" step="1">
    </div>
    <div class="row">
      <label>斗篷对齐 X <output data-out="sprite.capeDx"></output></label>
      <input type="range" data-cfg="sprite.capeDx" min="-60" max="60" step="1">
    </div>
    <div class="row">
      <label>斗篷对齐 Y <output data-out="sprite.capeDy"></output></label>
      <input type="range" data-cfg="sprite.capeDy" min="-60" max="60" step="1">
    </div>"""),
])

print('OK' if ok else 'HAS MISSES')
