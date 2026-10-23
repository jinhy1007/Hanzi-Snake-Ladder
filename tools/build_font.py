# -*- coding: utf-8 -*-
"""汉字卡用的楷体：文鼎 PL 中楷 CN（AR PL UKai CN，Arphic Public License），所有设备都显示一样的字体。

原字体太大（十几 MB），只留游戏要用的字，分两个文件：
  fonts/ukai-core.woff2  内置 1000 字、它们的组词，以及复习卡组词和造句里出现的字（几乎每局都用到）
  fonts/ukai-more.woff2  GB2312 一级常用字里剩下的字（上传自己的字库时才可能用到）
CSS 里用 unicode-range，浏览器只下载页面上真的用到的那个文件。不在里面的生僻字用设备自带字体。
原字体：art-src/fonts/ukai-deb/…/ukai.ttc（Debian fonts-arphic-ukai 包）。
运行：.venv/bin/python tools/build_font.py
"""
import json, os, re
from fontTools.ttLib import TTCollection
from fontTools import subset

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'art-src', 'fonts', 'ukai-deb', 'usr', 'share', 'fonts', 'truetype', 'arphic', 'ukai.ttc')
OUT = os.path.join(ROOT, 'fonts')


def ranges(cps):
    """unicode-range 写法：连续的码位合并成 U+4E00-4E05。"""
    cps = sorted(cps); out = []; i = 0
    while i < len(cps):
        j = i
        while j + 1 < len(cps) and cps[j + 1] == cps[j] + 1: j += 1
        out.append(f'U+{cps[i]:X}' + (f'-{cps[j]:X}' if j > i else '')); i = j + 1
    return ','.join(out)


def main():
    hints = open(os.path.join(ROOT, 'js', 'hints.js'), encoding='utf-8').read()
    game = open(os.path.join(ROOT, 'js', 'game.js'), encoding='utf-8').read()
    han = lambda t: {c for c in t if '一' <= c <= '鿿'}
    core = han(hints) | han(re.search(r"const LIB300 = '([^']*)'", game).group(1))
    # 复习卡（js/study.js）里的组词和造句也用楷体；字义用普通字体，不算
    study = json.loads('{' + open(os.path.join(ROOT, 'js', 'study.js'), encoding='utf-8').read().split('const STUDY = {', 1)[1].rsplit('};', 1)[0] + '}')
    for v in study.values(): core |= han(' '.join(w for w, _ in v[2]) + v[3])
    gb1 = set()
    for hi in range(0xB0, 0xD8):
        for lo in range(0xA1, 0xFF):
            try: gb1.add(bytes([hi, lo]).decode('gb2312'))
            except UnicodeDecodeError: pass
    more = han(''.join(gb1)) - core
    font = [f for f in TTCollection(SRC).fonts if 'CN' in f['name'].getDebugName(1)][0]
    cmap = font.getBestCmap()
    tmp = os.path.join(OUT, '_ukai-cn.ttf'); font.save(tmp)
    css = []
    for name, chars in (('core', core), ('more', more)):
        cps = [ord(c) for c in chars if ord(c) in cmap]
        miss = [c for c in chars if ord(c) not in cmap]
        opts = subset.Options(); opts.flavor = 'woff2'; opts.layout_features = []; opts.name_IDs = ['*']; opts.notdef_outline = True
        f = subset.load_font(tmp, opts); s = subset.Subsetter(opts); s.populate(unicodes=cps); s.subset(f)
        path = os.path.join(OUT, f'ukai-{name}.woff2'); subset.save_font(f, path, opts)
        print(f'{name}: {len(cps)} 字，{os.path.getsize(path) // 1024} KB' + (f'，字体里没有：{"".join(miss)}' if miss else ''))
        css.append(f"@font-face{{font-family:'UKai CN';src:url('../fonts/ukai-{name}.woff2') format('woff2');font-display:swap;unicode-range:{ranges(cps)}}}")
    os.remove(tmp)
    with open(os.path.join(ROOT, 'css', 'fonts.css'), 'w', encoding='utf-8') as fo:
        fo.write('/* 汉字卡楷体：文鼎 PL 中楷 CN（Arphic Public License，见 fonts/ARPHIC-LICENSE.txt）。由 tools/build_font.py 生成。 */\n' + '\n'.join(css) + '\n')


if __name__ == '__main__':
    main()
