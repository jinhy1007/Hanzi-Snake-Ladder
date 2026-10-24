# -*- coding: utf-8 -*-
"""复习卡的组词和造句录小女孩的声音（和字卡同一个声音：tools/voices.py 的 girl / Leda）。
一段一次：只读这一个词或这一句，拼音写在说明里帮配音读对（多音字、轻声）。
  录音：art-src/voices/ci/<词>.wav、art-src/voices/ju/<字>.wav（已经有的跳过，再跑一次不会重复花钱）
  游戏用：sounds/ci/<码位_码位>.m4a、sounds/ju/<字的码位>.m4a（去掉前后静音、音量统一，结尾留够不剪）
运行：zsh -i -c '.venv/bin/python tools/voices_study.py --sample'   先录几段试听
      zsh -i -c '.venv/bin/python tools/voices_study.py --all'      全部
      .venv/bin/python tools/voices_study.py --post                 转成 m4a
"""
import json, os, re, struct, subprocess, sys, tempfile, time, urllib.request, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_art as G
from voices import VOICES

SRC = os.path.join(G.ROOT, 'art-src', 'voices')
DST = os.path.join(G.ROOT, 'sounds')
SAMPLE_WORDS = '头发 长短 快乐 睡觉 午觉 看着 为什么 自行车 还是 你好'.split()
SAMPLE_SENTS = '发长觉了为'


def load_study():
    """js/study.js：字 → [字义, English, [[组词, 拼音], …], 造句, 造句拼音, English sentence]"""
    txt = open(os.path.join(G.ROOT, 'js', 'study.js'), encoding='utf-8').read()
    return {m.group(1): json.loads(m.group(2)) for m in re.finditer(r'^\s*"(.)":(\[.*\]),?\s*$', txt, re.M)}


def name(text):
    return '_'.join(f'{ord(c):x}' for c in text)


def record(text, py, path, kind):
    if os.path.exists(path):
        return f'{text} 已有'
    what = ('Say only this Chinese word, once.' if kind == 'ci'
            else 'Read this one Chinese sentence once, naturally, like telling a young child.')
    v = VOICES['girl']
    body = {'model': 'google/gemini-3-1-flash-tts', 'input': {
        'temperature': 0.6,
        'scene': f'A Chinese reading game for young children. {what} (It is pronounced: {py}.)',
        'sample_context': 'Clear, warm, a little slow, loud enough, every tone exact. Only this text, nothing else.',
        'speakers': [{'speaker_id': 'Speaker 1', 'voice_name': v['voice_name'], 'accent': 'Neutral',
                      'audio_profile': v['audio_profile'], 'style': v['style'], 'pace': 'Natural'}],
        'dialogue_turns': [{'speaker_id': 'Speaker 1', 'text': text if kind == 'ju' else f'{text}。'}]}}
    for attempt in range(3):
        task = G.kie_call('/api/v1/jobs/createTask', body, f'{kind}-{text}')['taskId']
        wait = 4
        while True:
            time.sleep(wait); wait = min(wait + 2, 12)
            d = G.kie_call(f'/api/v1/jobs/recordInfo?taskId={task}', None, f'{kind}-{text}')
            if d.get('state') in ('success', 'fail'): break
        if d.get('state') == 'success':
            url = json.loads(d['resultJson'])['resultUrls'][0]
            with urllib.request.urlopen(url, timeout=300) as r, open(path, 'wb') as f: f.write(r.read())
            return f'{text} ok'
    return f'{text} 失败 {d.get("failMsg")}'


def jobs(study, sample):
    words, sents = {}, {}
    for ch, s in study.items():
        for w, py in s[2]:
            words.setdefault(w, py)
        sents[ch] = (s[3], s[4])
    if sample:
        words = {w: words[w] for w in SAMPLE_WORDS}
        sents = {c: sents[c] for c in SAMPLE_SENTS}
    out = [(w, py, os.path.join(SRC, 'ci', f'{w}.wav'), 'ci') for w, py in words.items()]
    out += [(t, py, os.path.join(SRC, 'ju', f'{c}.wav'), 'ju') for c, (t, py) in sents.items()]
    return out


def process(src, out):
    """去掉前后静音（开头留 0.04 秒，结尾留 0.12 秒再淡出），峰值 -1 dB，转 AAC。返回秒数。"""
    w = wave.open(src); sr = w.getframerate(); n = w.getnframes()
    x = list(struct.unpack('<%dh' % n, w.readframes(n))); w.close()
    peak = max(abs(v) for v in x) or 1; thr = peak * 0.04
    a = next(i for i, v in enumerate(x) if abs(v) > thr); b = len(x) - next(i for i, v in enumerate(reversed(x)) if abs(v) > thr)
    a = max(0, a - int(sr * 0.04)); b = min(len(x), b + int(sr * 0.12))
    x = x[a:b]; g = 32767 * 0.89 / peak
    fi, fo = int(sr * 0.01), int(sr * 0.06)
    y = [int(v * g * min(1, i / fi, (len(x) - i) / fo)) for i, v in enumerate(x)]
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
    o = wave.open(tmp, 'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes(struct.pack('<%dh' % len(y), *y)); o.close()
    subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '64000', tmp, out], check=True); os.remove(tmp)
    return len(y) / sr


if __name__ == '__main__' and ('--sample' in sys.argv or '--all' in sys.argv):
    from concurrent.futures import ThreadPoolExecutor
    js = jobs(load_study(), '--sample' in sys.argv)
    for k in ('ci', 'ju'): os.makedirs(os.path.join(SRC, k), exist_ok=True)
    print(len(js), '段')
    done = 0
    with ThreadPoolExecutor(8) as ex:
        for r in ex.map(lambda j: record(*j), js):
            done += 1
            if 'ok' not in r and '已有' not in r or done % 50 == 0 or len(js) < 50: print(done, r, flush=True)
    print('完成')

if __name__ == '__main__' and '--post' in sys.argv:
    study = load_study(); lens = {}
    for kind in ('ci', 'ju'):
        os.makedirs(os.path.join(DST, kind), exist_ok=True)
        for f in sorted(os.listdir(os.path.join(SRC, kind))):
            if not f.endswith('.wav'): continue
            key = f[:-4]; text = key if kind == 'ci' else study[key][3]
            out = os.path.join(DST, kind, f'{name(key)}.m4a')
            if os.path.exists(out) and '--redo' not in sys.argv: continue
            lens[(kind, text)] = process(os.path.join(SRC, kind, f), out)
    print(len(lens), '段')
    # 时长异常：词每个字约 0.3～0.9 秒，句子每个字约 0.15～0.5 秒
    odd = {t: round(s, 2) for (k, t), s in lens.items()
           if not (0.3 * len(t) <= s + 0.3 <= 0.9 * len(t) + 0.6 if k == 'ci' else 0.15 * len(t) <= s <= 0.5 * len(t) + 1)}
    print('时长异常（可能读多了或没读出来）：', odd or '没有')
