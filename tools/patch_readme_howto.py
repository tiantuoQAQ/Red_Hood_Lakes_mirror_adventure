# -*- coding: utf-8 -*-
"""给 README 顶部补「如何游玩」章节 + 更新操作表（对齐当前版本键位）。"""
import io

p = 'README.md'
s = io.open(p, encoding='utf-8').read()

howto = '''# 镜 / MIRROR — 弹幕闪避原型

> CODEJAM 2026 参赛作品 · 红之镜 DEMO
> 玩法参考《东方冰之勇者记》，机制复刻与再设计，美术与关卡完全原创。

## 怎么玩（下载后 3 种方式，任选其一）

### ✅ 方式 1：网页版（最省事）

```bash
# 1) 下载/克隆本仓库
git clone https://github.com/tiantuoQAQ/Red_Hood_Lakes_mirror_adventure.git
cd Red_Hood_Lakes_mirror_adventure

# 2) 起一个本地静态服务器（ES Module 需要 HTTP，不能直接双击 index.html）
python -m http.server 8000

# 3) 浏览器打开
#    Chrome / Edge 最新版访问 http://localhost:8000/
```

> 有 Python 用 Python；没有的话 `npx serve` 也可以。

### ✅ 方式 2：Godot 版（完整体验，推荐）

1. 下载 **Godot 4.7.2（标准版，不需要 .NET）**：https://godotengine.org/download
2. 打开 Godot → `Import` → 选择本仓库根目录的 **`project.godot`**
3. 按 **F5** 运行（或直接双击 `godot/Main.tscn`）

> Godot 版包含全部 5+6 阶段 Boss 战、剧情、音效与后续补丁，是本作主版本。

### ✅ 方式 3：直接下带游戏包的 Release（如果作者发了）

仓库右侧 **Releases** → 下载对应平台的压缩包 → 解压即玩，无需安装引擎。

---

## 操作

| 动作 | 按键 |
| --- | --- |
| 移动 | `A` / `D` 或 `←` / `→` |
| 跳跃 | `Space` |
| 射击（自动瞄准） | `J` / `Z` / 鼠标左键 |
| 冲刺（0.2 秒无敌） | `Shift` / `K` / 鼠标右键 |
| 光球形态（无敌、穿弹幕） | **空中**按住 `W` + 冲刺 |
| 枪火击溃（2 MP，鼠标处范围伤害） | `C` |
| 业火（2 MP，全屏伤害） | `V` |
| 红之惨剧（2 MP，清弹 + 大伤害，击败魔姬后解锁） | `E` |
| 红之惨剧（演示用，免费无解锁） | `L` |
| 暂停 / 继续 | `P` / `Esc`，或面板点击 |
| 回标题 | `R` |
| 静音 / 全屏 / 放大窗口 | `M` / `F11` / `F10` |

> MP 通过**命中敌人**和**擦弹**（贴近弹幕但不被击中）回复。

'''

# 替换旧标题段（从文件开头到旧的「## Godot 垂直切片」之前）
idx = s.find('## Godot 垂直切片')
if idx > 0:
    s = howto + s[idx:]
else:
    s = howto + s

# 更新过时的 Godot 描述
s = s.replace('Godot 版本目前包含标题、蕾克移动/跳跃/冲刺、红色冲刺拖尾、猩红魔姬五阶段战斗，以及击败魔姬后进入玛丽苏战斗预览。',
              'Godot 版本包含完整流程：标题 → 序章 → 诺登对话 → 操作教程 → 镜中世界 → 猩红魔姬五阶段 → 红之惨剧解锁 → 玛丽苏六阶段 → 结局。')
s = s.replace('零依赖、零构建、零素材（全部图形由代码绘制）。\n\n**直接双击 `index.html`** 即可用浏览器打开。\n\n如果浏览器对本地文件限制过严，用任意静态服务器：',
              '网页版零依赖、零构建（图形由代码绘制，贴图资源随仓库提供）。\n\n**需要用 HTTP 服务器打开**（ES Module 不能 file:// 直开），见上方「怎么玩」。')

io.open(p, 'w', encoding='utf-8').write(s)
print('README updated')
