# -*- coding: utf-8 -*-
"""截取 AI 生成的音效：从 start 到 end 秒，开头 20ms 淡入、结尾淡出，转成游戏用的 AAC（sounds/<名字>.m4a）。
用法：.venv/bin/python tools/trim_sound.py <源mp3> <开始秒> <结束秒> <输出名字> [淡出秒=0.25]
需要 macOS 自带的 afconvert。
"""
import os, struct, subprocess, sys, tempfile, wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def trim(src, start, end, name, fade=0.25):
    tmp = tempfile.mkdtemp()
    w1, w2 = os.path.join(tmp, 'a.wav'), os.path.join(tmp, 'b.wav')
    subprocess.run(['afconvert', '-f', 'WAVE', '-d', 'LEI16@48000', src, w1], check=True)
    w = wave.open(w1); ch, sw, sr = w.getnchannels(), w.getsampwidth(), w.getframerate()
    w.setpos(int(sr * start)); frames = w.readframes(int(sr * (end - start))); w.close()
    v = list(struct.unpack('<%dh' % (len(frames) // 2), frames)); n = len(v) // ch
    fi, fo = int(sr * 0.02), int(sr * fade)
    for i in range(n):
        g = min(1.0, i / fi if fi else 1.0, (n - i) / fo if fo else 1.0)
        if g < 1.0:
            for c in range(ch): v[i * ch + c] = int(v[i * ch + c] * g)
    o = wave.open(w2, 'wb'); o.setnchannels(ch); o.setsampwidth(sw); o.setframerate(sr)
    o.writeframes(struct.pack('<%dh' % len(v), *v)); o.close()
    out = os.path.join(ROOT, 'sounds', name + '.m4a'); os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '96000', w2, out], check=True)
    print(f'{name}: {os.path.basename(src)} {start}–{end}s → sounds/{name}.m4a ({os.path.getsize(out) // 1024} KB)')


if __name__ == '__main__':
    a = sys.argv[1:]
    trim(a[0], float(a[1]), float(a[2]), a[3], float(a[4]) if len(a) > 4 else 0.25)
