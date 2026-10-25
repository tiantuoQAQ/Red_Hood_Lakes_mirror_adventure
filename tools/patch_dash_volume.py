# -*- coding: utf-8 -*-
"""冲刺音效音量：单独给 dash 提 +7dB（其它音效保持 -8dB）。"""
import io

# 1) sfx_player：按 id 覆盖音量
p = 'godot/sfx_player.gd'
s = io.open(p, encoding='utf-8').read()
if 'VOLUME_OVERRIDES' not in s:
    s = s.replace('const POOL_SIZE := 4  # Max concurrent playback per SFX',
                  'const POOL_SIZE := 4  # Max concurrent playback per SFX\n'
                  '# 个别音效单独调音量（dB），不在表里就用默认 SFX_VOLUME_DB\n'
                  'const VOLUME_OVERRIDES := {\n'
                  '\t"dash": -1.0,\n'
                  '\t"graze": -5.0,\n'
                  '}', 1)
    s = s.replace('\t\t\tplayer.volume_db = SFX_VOLUME_DB',
                  '\t\t\tplayer.volume_db = float(VOLUME_OVERRIDES.get(id, SFX_VOLUME_DB))', 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('per-id volume added')
else:
    s = s.replace('const VOLUME_OVERRIDES := {\n\t"dash": -1.0,',
                  'const VOLUME_OVERRIDES := {\n\t"dash": 0.0,', 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('dash volume bumped')

# 2) 重新生成 dash.wav，峰值更高（gain 0.95）
p2 = 'tools/make_dash_sfx2.py'
t = io.open(p2, encoding='utf-8').read()
t = t.replace("save('dash.wav', x, 0.5)", "save('dash.wav', x, 0.95)")
io.open(p2, 'w', encoding='utf-8').write(t)
print('dash gain -> 0.95')
