# art/char —— 地图内「待机立绘」（站桩小人）

> 注意：**这里放的不是对话立绘**。对话用的半身立绘在 `art/portrait/`。

## 命名约定

```
art/char/<角色id>_idle.png
```

| 角色 id | 文件 | 状态 |
| --- | --- | --- |
| `mabel` | `mabel_idle.png` | ⏳ 待补（GPT 在跑），现在临时用 `art/portrait/mabel.png` 顶替 |
| `norden` | `norden_idle.png` | ✅ 已补（兔耳补全 + 红瞳版，2026-10-24） |

## 规格要求

- **单张 PNG，透明底**
- 画布高度建议 600~900px（游戏内按高度缩放到 300px 显示，出图越大越清晰）
- **脚底对齐画布底部**，人物水平居中
- 朝向：默认**面向右**（朝玩家走来的方向）；如果要左右翻转，另存 `_idle_flip.png`
- 配色遵守三色规则：红 `#FF0000` / 绿 `#82FF00` / 青 `#00BAFF` + 中性灰（R=G=B）
- 出图后跑一遍：
  ```powershell
  python tools/unify_palette.py art/char/<id>_idle.png
  python tools/force_palette.py art/char/<id>_idle.png
  python tools/check_palette.py art/char        # 必须 0.00% 越界
  ```

## 代码接入位置

- 载入与回退：`src/render.js` 的 `getCharIdle()` / `drawCharIdle()`
- 使用点：`drawWalkNpc()` 里的 `kind === 'mabel'` 与诺登分支
- 只要把 `art/char/<id>_idle.png` 放进来，**重启页面即自动生效**，不用改代码

## 和玩家战斗小人的区别

玩家（蕾克）在战斗里用的是 `art/rek/` 下的**四层分件**（cape / hair / body / head），
那是另一套系统，由 `src/sprites.js` 处理，和本目录的单张待机立绘互不影响。
