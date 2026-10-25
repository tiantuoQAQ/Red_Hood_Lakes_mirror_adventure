# -*- coding: utf-8 -*-
"""多方圆桌：把同一个问题同时发给 GPT / Claude（经 a6api 代理），收集回答并存档。

用法：
    python tools/roundtable.py <上下文文件> <问题文件> [输出文件]
"""
import io
import json
import sys
import os
import time
import urllib.request

API_URL = 'https://api.a6api.com/v1/chat/completions'
API_KEY = os.environ.get('A6API_KEY', '')  # 从环境变量读取，勿硬编码

# (显示名, 模型, 超时秒, max_tokens)
PANEL = [
    ('GPT', 'gpt-6.1-sol', 240, 1600),
    ('Claude', 'claude-sonnet-5', 480, 1600),
]

SYS = (
    '你是一位资深游戏移植工程师，精通网页 canvas 游戏与 Godot 4 的对照移植。'
    '回答要具体、可执行、只讲结论和做法，不要客套。中文回答。'
)


def ask(model, context, question, timeout, max_tokens):
    body = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': SYS},
            {'role': 'user', 'content': '【项目上下文】\n' + context + '\n\n【问题】\n' + question},
        ],
        'max_tokens': max_tokens,
        'temperature': 0.4,
    }
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(
        API_URL, data=data,
        headers={'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'},
        method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        obj = json.loads(r.read().decode('utf-8'))
    return obj['choices'][0]['message']['content']


def main():
    if len(sys.argv) < 3:
        print('用法: python tools/roundtable.py <上下文文件> <问题文件> [输出文件]')
        return 1
    ctx_p, q_p = sys.argv[1], sys.argv[2]
    out_p = sys.argv[3] if len(sys.argv) > 3 else 'docs/圆桌记录.md'

    ctx = io.open(ctx_p, encoding='utf-8').read()
    q = io.open(q_p, encoding='utf-8').read()

    lines = ['# 圆桌记录：' + os.path.basename(q_p), '', '## 问题', '', q.strip(), '', '## 各方回答', '']
    for name, model, timeout, mx in PANEL:
        ans, tag = None, ''
        for attempt in (1, 2):
            t0 = time.time()
            try:
                ans = ask(model, ctx, q, timeout, mx)
                tag = '成功'
                break
            except Exception as e:
                ans = '调用失败：' + str(e)
                tag = '失败'
                print('  重试 %d/2：%s' % (attempt, e))
                time.sleep(2)
        print('[%s/%s] %s  %.1fs  %d 字' % (name, model, tag, time.time() - t0, len(ans)))
        lines += ['### ' + name + '（' + model + '）', '', ans.strip(), '', '---', '']

    lines += ['## 结论（由 Lead 补充）', '', '（待填）', '']
    io.open(out_p, 'w', encoding='utf-8').write('\n'.join(lines))
    print('已写入', out_p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
