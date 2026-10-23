# -*- coding: utf-8 -*-
"""生成 js/study.js：复习卡用的字义、组词和造句（内置 1000 个字）。

数据在 tools/study_data.txt，每行一个字：
  字|字义（给小朋友的简单解释）|English meaning|组词（1～3 个，空格分开）|造句|English sentence
组词和造句的拼音用 pypinyin 自动加，字的读音以 js/hints.js 为准（多音字检查组词里的读音对不对）。
复习页打开时才加载 js/study.js，不影响游戏的加载速度。
运行：.venv/bin/pip install pypinyin && .venv/bin/python tools/build_study.py
"""
import json, os, re
from pypinyin import lazy_pinyin, Style, load_phrases_dict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TONES = str.maketrans('āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ', 'aaaaeeeeiiiioooouuuuüüüü')
HAN = re.compile(r'[一-鿿]')
# pypinyin 读错的词，在这里改正（发现一个加一个）
FIX = {'很长': 'hěn cháng', '最长': 'zuì cháng', '长耳朵': 'cháng ěr duo', '母子': 'mǔ zǐ', '瓜子': 'guā zǐ', '鸡爪': 'jī zhuǎ', '切开': 'qiē kāi', '照片': 'zhào piàn', '大汗': 'dà hàn', '吹倒': 'chuī dǎo',
       '两只': 'liǎng zhī', '干干': 'gān gān', '围着': 'wéi zhe', '教我': 'jiāo wǒ', '教我们': 'jiāo wǒ men'}


def py_of(text):
    """整句的拼音：汉字一个音节，标点和其他字符原样保留。"""
    out = lazy_pinyin(text, style=Style.TONE, errors=lambda s: list(s))
    # 结构助词：跑得快 de、慢慢地 de（得到 dé、草地 dì 不变）
    for i, c in enumerate(text):
        if len(out) != len(text): break
        nxt, prv = text[i + 1:i + 2], text[i - 1:i]
        if c == '得' and nxt not in '到分奖了': out[i] = 'de'
        elif c == '地' and nxt and nxt not in '上方铁毯面下图球' and prv not in '草大土陆扫': out[i] = 'de'
    # 「一」「不」变调按课本标（一个 yí gè、不要 bú yào）；三声连读不标
    for i, c in enumerate(text[:-1]):
        nxt = out[i + 1] if len(out) == len(text) else ''
        tone4 = any(t in nxt for t in 'àèìòùǜ')
        if c == '不' and tone4: out[i] = 'bú'
        elif c == '一' and HAN.match(text[i + 1]) and (i == 0 or text[i - 1] not in '第十') and text[i + 1] not in '月日号年':
            out[i] = 'yí' if tone4 else 'yì'
    return out


def main():
    hints = open(os.path.join(ROOT, 'js', 'hints.js'), encoding='utf-8').read()
    # 提示卡组词的拼音是人工核对过的（有轻声），先教给 pypinyin
    known = {w: p for w, p in re.findall(r'"[^"]*", "([^"]{2,})", "([^"]*)"', hints) if len(p.split(' ')) == len(w)}
    load_phrases_dict({k: [[s] for s in v.split(' ')] for k, v in {**known, **FIX}.items()})
    reading = dict(re.findall(r'"(.)":\["([^"]*)"', hints))
    data, errs, warns = {}, [], []
    for n, line in enumerate(open(os.path.join(ROOT, 'tools', 'study_data.txt'), encoding='utf-8'), 1):
        line = line.strip()
        if not line or line.startswith('#'): continue
        parts = line.split('|')
        if len(parts) != 6: errs.append(f'第 {n} 行应该有 6 段：{line}'); continue
        ch, mzh, men, words, sent, sen = (p.strip() for p in parts)
        if ch in data: errs.append(f'重复 {ch}')
        if ch not in reading: errs.append(f'{ch} 不在 js/hints.js 里')
        want = reading.get(ch, '').translate(TONES)
        ws = []
        for w in words.split():
            if ch not in w: errs.append(f'{ch}：组词 {w} 里没有这个字'); continue
            p = py_of(w)
            if want and want != 'yi' and want != 'bu' and p[w.index(ch)].translate(TONES) != want:
                errs.append(f'{ch} {reading[ch]}：组词 {w} 读成了 {" ".join(p)}')
            ws.append([w, ' '.join(p)])
        if not ws: errs.append(f'{ch}：没有组词')
        if ch not in sent: errs.append(f'{ch}：造句里没有这个字')
        sp = py_of(sent)
        han_py = [s for c, s in zip(sent, sp) if HAN.match(c)] if len(sp) == len(sent) else None
        if han_py is None: warns.append(f'{ch}：造句拼音对不上字数')
        elif want not in ('yi', 'bu') and want not in {s.translate(TONES) for c, s in zip(sent, sp) if c == ch}:
            warns.append(f'{ch} {reading.get(ch)}：造句里读成 {[s for c, s in zip(sent, sp) if c == ch]}')
        data[ch] = [mzh, men, ws, sent, ' '.join(s for c, s in zip(sent, sp) if HAN.match(c)), sen]
    missing = [c for c in reading if c not in data]
    print(f'{len(data)} 个字；还没写的 {len(missing)} 个' + (f'：{"".join(missing[:60])}' if missing else ''))
    print('\n'.join(errs) or '检查通过')
    if warns: print('请看一下：\n' + '\n'.join(warns))
    lines = ',\n'.join(f'  "{k}":{json.dumps(v, ensure_ascii=False)}' for k, v in data.items())
    with open(os.path.join(ROOT, 'js', 'study.js'), 'w', encoding='utf-8') as fo:
        fo.write('/* 复习卡数据（由 tools/build_study.py 生成）：字 → [字义, English, [[组词, 拼音], …], 造句, 造句拼音（只有汉字的音节）, English sentence]。 */\n'
                 'const STUDY = {\n' + lines + '\n};\n')


if __name__ == '__main__':
    main()
