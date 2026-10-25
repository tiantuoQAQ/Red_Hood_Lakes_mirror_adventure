# -*- coding: utf-8 -*-
"""死亡流程改为：镜碎演出 → 停在「按 ENTER 复活」→ 复活时回到当前阶段开头（Boss 本阶段满血）。"""
import io

p = 'godot/main.gd'
s = io.open(p, encoding='utf-8').read()
orig = s

# 1) 新状态：等待确认复活
if 'var death_wait_confirm' not in s:
    s = s.replace('var death_count := 0', 'var death_count := 0\nvar death_wait_confirm := false', 1)

# 2) 演出结束不再自动复活，改为等待确认
old = '''	death_shards = death_shards.filter(func(x): return float(x.get("life", 0.0)) > 0.0)
	if death_timer <= 0.0:
		player_hp = PLAYER_MAX_HP
		player_pos = battle_start_pos
		player_vel = Vector2.ZERO
		player_hurt_invuln = 90
		bullets.clear()
		spikes.clear()
		whirls.clear()
		# Boss 血量不重置：死亡只让你自己重来，战斗进度保留（死几次都别想白嫖）
		banner = "……是幻觉么。（第 %d 次）" % death_count
		banner_timer = 170
		retry_flash = 1.0
		_spawn_fx_ring(player_pos, Color(1, 1, 1, 0.9), 260.0, 0.5, 5.0)'''
new = '''	death_shards = death_shards.filter(func(x): return float(x.get("life", 0.0)) > 0.0)
	if death_timer <= 0.0 and not death_wait_confirm:
		# 演出结束：停在「按 ENTER 复活」界面
		death_wait_confirm = true

## 确认复活：回到当前阶段开头，Boss 本阶段血量回满
func _respawn_after_death() -> void:
	death_wait_confirm = false
	player_hp = PLAYER_MAX_HP
	player_pos = battle_start_pos
	player_vel = Vector2.ZERO
	player_hurt_invuln = 90
	bullets.clear()
	spikes.clear()
	whirls.clear()
	beam_warning_list.clear()
	boss_hp = boss_max_hp          # 本阶段满血重打
	banner = "……是幻觉么。（第 %d 次）" % death_count
	banner_timer = 170
	retry_flash = 1.0
	_spawn_fx_ring(player_pos, Color(1, 1, 1, 0.9), 260.0, 0.5, 5.0)'''
if old in s:
    s = s.replace(old, new, 1)
    print('death -> wait confirm')
else:
    print('respawn block not found')

# 3) 等待确认时响应 ENTER / 点击
s = s.replace('\tif tutorial_timer > 0.0:',
              '\tif death_wait_confirm and (_just("confirm") or _mouse_clicked()):\n'
              '\t\t_respawn_after_death()\n'
              '\tif tutorial_timer > 0.0:', 1)

# 4) 等待界面绘制：黑屏 + 镜碎了 + 按 ENTER 复活提示
s = s.replace('''func _draw_death_overlay() -> void:
	if death_timer <= 0.0:
		return''','''func _draw_death_overlay() -> void:
	if death_wait_confirm:
		draw_rect(Rect2(Vector2.ZERO, VIEW), Color(0, 0, 0, 0.82))
		draw_string(ThemeDB.fallback_font, Vector2(500, 320), "镜 碎 了", HORIZONTAL_ALIGNMENT_LEFT, -1, 44, WHITE)
		draw_string(ThemeDB.fallback_font, Vector2(430, 386), "第 %d 次 · 本阶段重新开始" % death_count, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(1, 0.4, 0.4))
		var blink := 0.55 + 0.45 * sin(elapsed * 5.0)
		draw_string(ThemeDB.fallback_font, Vector2(492, 452), "按 ENTER / 点击 复活", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(1, 1, 1, blink))
		return
	if death_timer <= 0.0:
		return''', 1)

# 5) 死亡/等待期间禁止操作（已有死亡期间禁操作，补充等待期间）
s = s.replace('func _update_player() -> void:\n\tif death_timer > 0.0:',
              'func _update_player() -> void:\n\tif death_timer > 0.0 or death_wait_confirm:', 1)

# 6) 战斗开始/换章重置等待状态
s = s.replace('\tdeath_count = 0', '\tdeath_count = 0\n\tdeath_wait_confirm = false', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('changed' if s != orig else 'NO CHANGE')
