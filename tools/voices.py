# -*- coding: utf-8 -*-
"""试听：用 Kie.ai 上的 Gemini 配音读 12 个字，两种声音（亲切的年轻女声、清晰的小女孩声）。
每种声音只生成一次（12 个字一口气读完、中间停顿），再按停顿切成 12 段：art-src/voices/<声音>/<字>.wav
运行：.venv/bin/python tools/voices.py [young|girl]
"""
import io, json, os, struct, sys, time, urllib.request, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_art as G

OUT = os.path.join(G.ROOT, 'art-src', 'voices')
CHARS = '水山大小长好乐鱼飞花我爸'
# 多音字用读音提示，保证读对（只给配音员看，不会读出来）
NOTE = '长 is read cháng (as in 长短). 乐 is read lè (as in 快乐).'
VOICES = {
    'young': dict(voice_name='Aoede', audio_profile='A warm, gentle, friendly young Chinese woman in her twenties, like a kind kindergarten '
                  'teacher, speaking clear standard Mandarin (Putonghua) with perfect tones.', style='Vocal Smile'),
    'girl': dict(voice_name='Leda', audio_profile='A cheerful, bright little Chinese girl about 8 years old, speaking very clear, crisp '
                 'standard Mandarin (Putonghua) with perfect tones.', style='Vocal Smile'),
}


def gen(key):
    v = VOICES[key]
    body = {'model': os.environ.get('VOICE_MODEL', 'google/gemini-3-1-flash-tts'), 'input': {
        'temperature': 0.7,
        'scene': 'A child-friendly Chinese reading game. Read the list of single Chinese characters one by one, slowly, '
                 'loudly and clearly, with a clear pause at every comma. ' + NOTE,
        'sample_context': 'Teaching single Chinese characters to young children: clear, warm, a little slow, every tone exact.',
        'speakers': [{'speaker_id': 'Speaker 1', 'voice_name': v['voice_name'], 'accent': 'Neutral',
                      'audio_profile': v['audio_profile'], 'style': v['style'], 'pace': 'Natural'}],
        'dialogue_turns': [{'speaker_id': 'Speaker 1', 'text': '，'.join(CHARS) + '。'}]}}
    task = G.kie_call('/api/v1/jobs/createTask', body, f'voice-{key}')['taskId']
    wait = 5
    while True:
        time.sleep(wait); wait = min(wait + 3, 15)
        d = G.kie_call(f'/api/v1/jobs/recordInfo?taskId={task}', None, f'voice-{key}')
        if d.get('state') == 'success':
            url = json.loads(d['resultJson'])['resultUrls'][0]; break
        if d.get('state') == 'fail':
            sys.exit(f"{key}: 失败 {d.get('failCode')} {d.get('failMsg')}")
    os.makedirs(os.path.join(OUT, key), exist_ok=True)
    full = os.path.join(OUT, key, '_all.wav')
    with urllib.request.urlopen(url, timeout=300) as r, open(full, 'wb') as f: f.write(r.read())
    split(full, key)


def split(path, key):
    """按停顿切成 12 段，每段前后留 0.15 秒。"""
    w = wave.open(path); sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    raw = w.readframes(w.getnframes()); w.close()
    x = struct.unpack('<%dh' % (len(raw) // 2), raw)[::ch]
    win = int(sr * 0.02); env = [max(abs(v) for v in x[i:i + win]) for i in range(0, len(x), win)]
    thr = max(env) * 0.06; on = [e > thr for e in env]
    segs, i = [], 0
    while i < len(on):
        if on[i]:
            j = i; gap = 0
            while j < len(on) and gap < 9:           # 0.18 秒静音就算一个字结束（逗号的停顿）
                gap = 0 if on[j] else gap + 1; j += 1
            segs.append((i, j - gap)); i = j
        else:
            i += 1
    segs = [s for s in segs if (s[1] - s[0]) * 0.02 > 0.12]
    print(key, '找到', len(segs), '段', [round((b - a) * 0.02, 2) for a, b in segs])
    pad = int(0.15 / 0.02)
    for c, (a, b) in zip(CHARS, segs):
        s0 = max(0, (a - pad) * win); s1 = min(len(x), (b + pad) * win)
        o = wave.open(os.path.join(OUT, key, f'{c}.wav'), 'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
        o.writeframes(struct.pack('<%dh' % (s1 - s0), *x[s0:s1])); o.close()


PINYIN = dict(zip(CHARS, ['shuǐ', 'shān', 'dà', 'xiǎo', 'cháng', 'hǎo', 'lè', 'yú', 'fēi', 'huā', 'wǒ', 'bà']))


def one(key, c):
    """一个字一次：只读这个字，读一遍。拼音只写在说明里，帮配音读对声调。"""
    v = VOICES[key]
    body = {'model': os.environ.get('VOICE_MODEL', 'google/gemini-3-1-flash-tts'), 'input': {
        'temperature': 0.6,
        'scene': f'A Chinese reading game for young children. Say only the single Chinese character, once. (It is pronounced {PINYIN[c]}.)',
        'sample_context': 'Clear, warm, a little slow, loud enough, every tone exact. Only the one character, nothing else.',
        'speakers': [{'speaker_id': 'Speaker 1', 'voice_name': v['voice_name'], 'accent': 'Neutral',
                      'audio_profile': v['audio_profile'], 'style': v['style'], 'pace': 'Natural'}],
        'dialogue_turns': [{'speaker_id': 'Speaker 1', 'text': f'{c}。'}]}}
    task = G.kie_call('/api/v1/jobs/createTask', body, f'voice-{key}-{c}')['taskId']
    wait = 4
    while True:
        time.sleep(wait); wait = min(wait + 2, 12)
        d = G.kie_call(f'/api/v1/jobs/recordInfo?taskId={task}', None, f'voice-{key}-{c}')
        if d.get('state') == 'success':
            url = json.loads(d['resultJson'])['resultUrls'][0]; break
        if d.get('state') == 'fail':
            return f'{key}-{c} 失败 {d.get("failMsg")}'
    os.makedirs(os.path.join(OUT, key), exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r, open(os.path.join(OUT, key, f'{c}.wav'), 'wb') as f: f.write(r.read())
    return f'{key}-{c} ok'


def load_hints():
    """js/hints.js 里的拼音：字 → 拼音（多音字按提示卡的读音）。"""
    import re
    txt = open(os.path.join(G.ROOT, 'js', 'hints.js'), encoding='utf-8').read()
    return {m.group(1): m.group(2) for m in re.finditer(r'"(.)":\["([^"]+)"', txt)}


def one_to(key, c, py, out_dir):
    """生成一个字，存到 out_dir/<字>.wav；已经有的跳过（再跑一次不会重复花钱）。"""
    path = os.path.join(out_dir, f'{c}.wav')
    if os.path.exists(path):
        return f'{c} 已有'
    PINYIN[c] = py
    v = VOICES[key]
    body = {'model': 'google/gemini-3-1-flash-tts', 'input': {
        'temperature': 0.6,
        'scene': f'A Chinese reading game for young children. Say only the single Chinese character, once. (It is pronounced {py}.)',
        'sample_context': 'Clear, warm, a little slow, loud enough, every tone exact. Only the one character, nothing else.',
        'speakers': [{'speaker_id': 'Speaker 1', 'voice_name': v['voice_name'], 'accent': 'Neutral',
                      'audio_profile': v['audio_profile'], 'style': v['style'], 'pace': 'Natural'}],
        'dialogue_turns': [{'speaker_id': 'Speaker 1', 'text': f'{c}。'}]}}
    for attempt in range(3):
        task = G.kie_call('/api/v1/jobs/createTask', body, f'zi-{c}')['taskId']
        wait = 4
        while True:
            time.sleep(wait); wait = min(wait + 2, 12)
            d = G.kie_call(f'/api/v1/jobs/recordInfo?taskId={task}', None, f'zi-{c}')
            if d.get('state') in ('success', 'fail'): break
        if d.get('state') == 'success':
            url = json.loads(d['resultJson'])['resultUrls'][0]
            with urllib.request.urlopen(url, timeout=300) as r, open(path, 'wb') as f: f.write(r.read())
            return f'{c} ok'
    return f'{c} 失败 {d.get("failMsg")}'


if __name__ == '__main__' and '--all' in sys.argv:
    from concurrent.futures import ThreadPoolExecutor
    hints = load_hints(); out = os.path.join(OUT, 'girl300'); os.makedirs(out, exist_ok=True)
    print(len(hints), '个字')
    done = 0
    with ThreadPoolExecutor(8) as ex:
        for r in ex.map(lambda kv: one_to('girl', kv[0], kv[1], out), hints.items()):
            done += 1
            if 'ok' not in r and '已有' not in r or done % 25 == 0: print(done, r, flush=True)
    print('完成')


if __name__ == '__main__' and '--each' in sys.argv:
    from concurrent.futures import ThreadPoolExecutor
    jobs = [(k, c) for k in VOICES for c in CHARS]
    with ThreadPoolExecutor(6) as ex:
        for r in ex.map(lambda j: one(*j), jobs): print(r)


if __name__ == '__main__' and '--each' not in sys.argv and '--all' not in sys.argv:
    for k in [a for a in sys.argv[1:] if a in VOICES] or list(VOICES):
        print('  做', k, '…'); gen(k)
