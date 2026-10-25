# 蕾克运行时贴图（2026-10-25）

这 6 张 RGBA 图由 `tools/prepare_rek_battle.py` 从 `art/ref/rek_battle_2026-10-25/` 的白底原稿派生。原稿不修改；这里是游戏实际加载的透明版本。

- `body_move.png`：无攻击移动身体，包含披风。
- `body_charge.png`：伸手蓄势身体；剑气仍由弹丸逻辑绘制。
- `head.png`：独立头部，绕颈部旋转跟随鼠标。
- `dash_01.png`、`dash_02.png`、`dash_03.png`：冲刺三张关键帧，残影/粒子由程序绘制。
- 统一画布 896×768；脚底锚点 `(550, 730)`，颈部锚点 `(610, 320)`，运行缩放 0.34。锚点记录在 `anchors.json`。

运行 `python tools/prepare_rek_battle.py` 可重新生成并输出暗底拼接预览到 `tmp/rek_art/runtime_contact.png`。原始四层占位资源 `art/rek/` 保留供 Web 版使用，新头身图未塞回四层接口。
