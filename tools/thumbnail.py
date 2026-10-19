# -*- coding: utf-8 -*-
"""网页分享预览图（1200×630，发链接时显示的那张图）。用游戏里现成的地图、小神兽和汉字卡拼，文字用 macOS 自带字体排版。

输出 art-src/thumbs/thumb-<a..d>.png。运行：.venv/bin/python tools/thumbnail.py
"""
import glob, math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'art-src', 'thumbs')
W, H = 1200, 630


def font(name, size):
    pats = {'wawa': '**/WawaSC-Regular.otf', 'yuan': '**/Yuanti.ttc', 'kai': '**/Kaiti.ttc', 'han': '**/Hannotate.ttc'}
    if name == 'round':
        return ImageFont.truetype('/Library/Fonts/Arial Rounded Bold.ttf' if os.path.exists('/Library/Fonts/Arial Rounded Bold.ttf')
                                  else '/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf', size)
    path = glob.glob('/System/Library/AssetsV2/com_apple_MobileAsset_Font8/' + pats[name], recursive=True)[0]
    return ImageFont.truetype(path, size, index=1 if name == 'yuan' else 0)   # 圆体粗一点的那个


def img(p):
    return Image.open(os.path.join(ROOT, p)).convert('RGBA')


def cover(im, w, h, cx=0.5, cy=0.5):
    s = max(w / im.width, h / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = round((im.width - w) * cx); y = round((im.height - h) * cy)
    return im.crop((x, y, x + w, y + h))


def shadowed(canvas, im, xy, blur=10, offset=(0, 8), alpha=90):
    sh = Image.new('RGBA', im.size, (46, 42, 74, 0)); sh.putalpha(im.getchannel('A').point(lambda v: v * alpha // 255))
    pad = blur * 3; big = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0)); big.paste(sh, (pad, pad))
    big = big.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(big, (xy[0] - pad + offset[0], xy[1] - pad + offset[1])); canvas.alpha_composite(im, xy)


def tile(ch, size, rot=0, bg=(255, 253, 251), fg=(46, 42, 74)):
    t = Image.new('RGBA', (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=size * 0.16, fill=bg + (255,))
    f = font('kai', round(size * 0.68)); bb = d.textbbox((0, 0), ch, font=f)
    d.text(((size - (bb[2] - bb[0])) / 2 - bb[0], (size - (bb[3] - bb[1])) / 2 - bb[1]), ch, font=f, fill=fg)
    return t.rotate(rot, resample=Image.BICUBIC, expand=True)


def avatar(name, h):
    a = img(f'images/avatars/{name}.webp'); return a.resize((round(a.width * h / a.height), h), Image.LANCZOS)


def text(d, xy, s, f, fill, stroke=0, stroke_fill=None, anchor='la'):
    d.text(xy, s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill, anchor=anchor)


ROSE, ROSE_D, INK, INK_S, GOLD = (217, 84, 155), (166, 56, 111), (46, 42, 74), (101, 95, 134), (255, 201, 62)


def version_a():
    """故事地图：左边是森林城堡地图，右边大标题，下面一排小神兽。"""
    c = Image.new('RGBA', (W, H), (240, 233, 252, 255))
    m = cover(img('images/maps/map-short.webp').crop((0, 0, 1024, 1500)), 520, H, 0.5, 0.2)
    mask = Image.new('L', (520, H), 255); md = ImageDraw.Draw(mask)
    for i in range(80): md.line([(520 - 80 + i, 0), (520 - 80 + i, H)], fill=255 - i * 3)
    c.paste(m, (0, 0), mask)
    d = ImageDraw.Draw(c)
    text(d, (850, 70), '识字蛇形棋', font('wawa', 104), ROSE_D, 8, 'white', 'ma')
    text(d, (850, 205), '读汉字 · 掷骰子 · 一路走到城堡', font('yuan', 34), INK, anchor='ma')
    text(d, (850, 258), 'Hanzi Snakes & Ladders', font('round', 34), INK_S, anchor='ma')
    for i, (ch, r) in enumerate(zip('山水火', (-8, 5, -4))):
        t = tile(ch, 96, r); shadowed(c, t, (650 + i * 125, 315 - t.height // 2 + 40))
    for i, n in enumerate(['axolittle', 'hippofly', 'dragoink', 'octowl', 'unicwhale', 'ladyfrog']):
        a = avatar(n, 150); shadowed(c, a, (560 + i * 105 - a.width // 2 + 40, H - a.height - 12), 6, (0, 4), 60)
    return c


def version_b():
    """小神兽大集合：浅紫背景，标题五个字各写在一张汉字卡上，小神兽围在下面。"""
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    for y in range(H):
        t = y / H; d.line([(0, y), (W, y)], fill=(int(250 - 18 * t), int(236 - 10 * t), int(250 - 2 * t), 255))
    for i in range(26):
        x, y, r = (i * 211) % W, (i * 137) % 260 + 10, 4 + (i * 7) % 9
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 170))
    for i, (ch, rot) in enumerate(zip('识字蛇形棋', (-6, 4, -3, 5, -5))):
        t = tile(ch, 150, rot, bg=(255, 253, 251), fg=INK); shadowed(c, t, (150 + i * 185 - t.width // 2 + 75, 60 - (t.height - 150) // 2 + (12 if i % 2 else 0)))
    d = ImageDraw.Draw(c)
    text(d, (W // 2, 252), '可爱的认汉字棋盘游戏  ·  A cute game for learning Chinese characters', font('yuan', 30), INK, anchor='ma')
    names = ['squirrot', 'axolittle', 'hippofly', 'seacoon', 'dragoink', 'octowl', 'unicwhale', 'ladyfrog', 'snoala', 'poodlephant']
    for i, n in enumerate(names):
        a = avatar(n, 230 if i in (3, 4, 5, 6) else 200)
        x = 60 + i * 113 - a.width // 2 + 50; shadowed(c, a, (x, H - a.height + 8), 6, (0, 4), 60)
    return c


def version_c():
    """动物运动会：起跑线地图做背景，白色圆角面板写标题，裁判和运动员在旁边。"""
    bg = cover(img('images/maps/map-long-sports.webp').crop((0, 3300, 1024, 4319)), W, H, 0.5, 0.55)
    c = bg.filter(ImageFilter.GaussianBlur(2)).convert('RGBA')
    c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, 40)))
    panel = Image.new('RGBA', (640, 330), (0, 0, 0, 0)); ImageDraw.Draw(panel).rounded_rectangle([0, 0, 639, 329], 40, fill=(255, 253, 251, 238))
    shadowed(c, panel, (520, 60), 14, (0, 10), 70)
    d = ImageDraw.Draw(c)
    text(d, (840, 95), '识字蛇形棋', font('wawa', 100), ROSE_D, anchor='ma')
    text(d, (840, 225), '读对一个字，往前跑一步！', font('yuan', 36), INK, anchor='ma')
    text(d, (840, 285), 'Read a character, race ahead!', font('round', 30), INK_S, anchor='ma')
    for i, (ch, r) in enumerate(zip('跑跳飞', (-6, 4, -4))):
        t = tile(ch, 100, r); shadowed(c, t, (590 + i * 150, 420))
    for i, n in enumerate(['seacoon', 'squirrot', 'ladyfrog']):
        a = avatar(n, 180); shadowed(c, a, (40 + i * 150, H - a.height - 6), 6, (0, 4), 60)
    return c


def version_d():
    """棋盘小路：一条弯弯的格子路，格子上是汉字，小神兽站在路上，右上角是标题。"""
    c = Image.new('RGBA', (W, H), (214, 236, 196, 255)); d = ImageDraw.Draw(c)
    for i in range(40):
        x, y, r = (i * 157) % W, (i * 233) % H, 30 + (i * 13) % 60
        d.ellipse([x - r, y - r, x + r, y + r], fill=(196, 228, 176, 255) if i % 2 else (226, 242, 210, 255))
    path = [(70 + i * 105, 470 + math.sin(i * 0.75) * 70) for i in range(11)]
    d.line(path, fill=(236, 214, 176), width=96, joint='curve')
    chars = '出大小上下山水日月人终'
    for i, (x, y) in enumerate(path):
        label = '出发' if i == 0 else ('城堡' if i == len(path) - 1 else chars[i])
        if i in (0, len(path) - 1):
            t = Image.new('RGBA', (90, 90), (0, 0, 0, 0)); td = ImageDraw.Draw(t)
            td.rounded_rectangle([0, 0, 89, 89], 14, fill=(47, 143, 85) if i == 0 else ROSE)
            text(td, (45, 45), label, font('yuan', 28), 'white', anchor='mm')
        else:
            t = tile(label, 82, ((i * 53) % 9 - 4) * 1.2)
        shadowed(c, t, (round(x - t.width / 2), round(y - t.height / 2)), 6, (0, 5), 70)
    for n, k in (('axolittle', 2.5), ('dragoink', 5.5), ('unicwhale', 8.5)):   # 站在两个格子中间，路的上方
        a = avatar(n, 135); x = 70 + k * 105; y = 470 + math.sin(k * 0.75) * 70 - 46
        shadowed(c, a, (round(x - a.width / 2), round(y - a.height)), 5, (0, 4), 50)
    d = ImageDraw.Draw(c)
    text(d, (W // 2, 50), '识字蛇形棋', font('wawa', 112), ROSE_D, 8, 'white', 'ma')
    text(d, (W // 2, 192), '掷骰子、读汉字，看谁先到城堡  ·  Hanzi Snakes & Ladders', font('yuan', 32), INK, 4, 'white', 'ma')
    return c


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for k, fn in (('a', version_a), ('b', version_b), ('c', version_c), ('d', version_d)):
        fn().convert('RGB').save(os.path.join(OUT, f'thumb-{k}.png')); print('完成', k)
