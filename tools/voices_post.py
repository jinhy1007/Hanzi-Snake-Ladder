# -*- coding: utf-8 -*-
"""把 art-src/voices/girl300/<字>.wav 处理成游戏用的 sounds/zi/<码位>.m4a：
去掉前后静音、音量统一调大（峰值 -1 dB）、转 AAC。时长异常的字会列出来，方便人工检查。
运行：.venv/bin/python tools/voices_post.py [--new]（--new：只处理还没有 m4a 的字）
"""
import os, struct, subprocess, sys, tempfile, wave
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'art-src', 'voices', 'girl300')
DST = os.path.join(ROOT, 'sounds', 'zi')


def process(ch):
    w = wave.open(os.path.join(SRC, f'{ch}.wav')); sr = w.getframerate(); n = w.getnframes()
    x = list(struct.unpack('<%dh' % n, w.readframes(n))); w.close()
    peak = max(abs(v) for v in x) or 1; thr = peak * 0.04
    a = next(i for i, v in enumerate(x) if abs(v) > thr); b = len(x) - next(i for i, v in enumerate(reversed(x)) if abs(v) > thr)
    a = max(0, a - int(sr * 0.04)); b = min(len(x), b + int(sr * 0.12))
    x = x[a:b]; g = 32767 * 0.89 / peak
    fi, fo = int(sr * 0.01), int(sr * 0.06)
    y = [int(v * g * min(1, i / fi, (len(x) - i) / fo)) for i, v in enumerate(x)]
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
    o = wave.open(tmp, 'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(struct.pack('<%dh' % len(y), *y)); o.close()
    out = os.path.join(DST, f'{ord(ch):x}.m4a')
    subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '64000', tmp, out], check=True); os.remove(tmp)
    return len(y) / sr


if __name__ == '__main__':
    os.makedirs(DST, exist_ok=True)
    chars = sorted(f[:-4] for f in os.listdir(SRC) if f.endswith('.wav') and len(f) == 5)
    if '--new' in sys.argv:
        chars = [c for c in chars if not os.path.exists(os.path.join(DST, f'{ord(c):x}.m4a'))]
    lens = {}
    for c in chars:
        lens[c] = process(c)
    odd = {c: round(t, 2) for c, t in lens.items() if t < 0.35 or t > 1.6}
    print(len(lens), '个字；平均', round(sum(lens.values()) / len(lens), 2), '秒；最短', min(lens.values()).__round__(2), '最长', max(lens.values()).__round__(2))
    print('时长异常（可能读多了或没读出来）：', odd or '没有')
