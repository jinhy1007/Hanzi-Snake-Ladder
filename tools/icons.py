# -*- coding: utf-8 -*-
"""网站小图标的 4 个版本（喷火猪猪＋「识」字卡）。输出 art-src/icons/icon-<1..4>.png（512×512）和对比图。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import thumbnail as T

ROOT = T.ROOT; OUT = os.path.join(ROOT, 'art-src', 'icons'); S = 512
pig = Image.open(os.path.join(ROOT, 'art-src', 'avatars', 'dragoink.png')).convert('RGBA')
head = pig.crop((260, 0, 1346, 840))            # 头、角和鼻涕泡泡
body = pig.crop(pig.getchannel('A').getbbox())


def fit(im, w=None, h=None):
    if w: return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def base(color, shape='round'):
    c = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    if shape == 'circle': d.ellipse([0, 0, S - 1, S - 1], fill=color)
    else: d.rounded_rectangle([0, 0, S - 1, S - 1], 110, fill=color)
    return c


def clip(c, shape='round'):
    m = Image.new('L', (S, S), 0); d = ImageDraw.Draw(m)
    if shape == 'circle': d.ellipse([0, 0, S - 1, S - 1], fill=255)
    else: d.rounded_rectangle([0, 0, S - 1, S - 1], 110, fill=255)
    out = Image.new('RGBA', (S, S), (0, 0, 0, 0)); out.paste(c, (0, 0), m); return out


def v1():   # 小猪的大脸
    c = base((255, 214, 102, 255), 'circle'); h = fit(head, w=470)
    c.alpha_composite(h, ((S - h.width) // 2 + 10, S - h.height + 10)); return clip(c, 'circle')


def v2():   # 「识」字卡＋整只小猪坐在旁边
    c = base((190, 230, 200, 255)); t = T.tile('识', 300, -6); T.shadowed(c, t, (24, 120), 10, (0, 10), 80)
    p = fit(body, h=330); T.shadowed(c, p, (S - p.width - 6, S - p.height - 14), 8, (0, 6), 60); return clip(c)


def v3():   # 小猪从「识」字卡上面探出头
    c = base((255, 205, 225, 255)); t = T.tile('识', 300, 0); T.shadowed(c, t, ((S - t.width) // 2, 190), 10, (0, 10), 80)
    h = fit(head, w=300); c.alpha_composite(h.crop((0, 0, h.width, round(h.height * 0.66))), ((S - h.width) // 2 + 12, 34)); return clip(c)


def v4():   # 粉色徽章，大大的白色「识」，右下角贴一个小猪头
    c = base((217, 84, 155, 255)); d = ImageDraw.Draw(c)
    f = T.font('wawa', 330); d.text((S // 2 - 40, S // 2 - 20), '识', font=f, fill='white', anchor='mm')
    h = fit(head, w=250); T.shadowed(c, h, (S - h.width - 18, S - h.height - 14), 6, (0, 4), 70); return clip(c)


def v5(lean=12, ph=300):
    """版本 2 的排版，粉色背景；小猪往左歪，靠在「识」字卡上睡着了，影子投在卡片上。"""
    c = base((255, 196, 214, 255)); t = T.tile('识', 262, -6); T.shadowed(c, t, (18, 96), 12, (4, 14), 95)
    p = fit(body, h=ph).rotate(lean, resample=Image.BICUBIC, expand=True)
    x = S - p.width - 6; y = S - p.height - 6
    T.shadowed(c, p, (x, y), 10, (-16, 12), 120)   # 影子偏左下，像压在卡片上
    return clip(c)


if __name__ == '__main__' and '--lean' in sys.argv:
    os.makedirs(OUT, exist_ok=True)
    ims = [v5(10, 300), v5(16, 320)]
    for i, im in enumerate(ims): im.save(os.path.join(OUT, f'icon-5{"ab"[i]}.png'))
    sheet = Image.new('RGBA', (2 * 300 + 40, 330), (246, 242, 251, 255)); d = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        x = 20 + i * 310
        sheet.alpha_composite(im.resize((200, 200), Image.LANCZOS), (x, 20))
        sheet.alpha_composite(im.resize((64, 64), Image.LANCZOS), (x, 240)); sheet.alpha_composite(im.resize((32, 32), Image.LANCZOS), (x + 90, 256))
        d.text((x + 150, 262), 'AB'[i], font=T.font('round', 30), fill=(46, 42, 74))
    sheet.convert('RGB').save(os.path.join(OUT, 'icons-lean.png')); print('ok')


if __name__ == '__main__' and '--lean' not in sys.argv:
    os.makedirs(OUT, exist_ok=True)
    ims = [f() for f in (v1, v2, v3, v4)]
    for i, im in enumerate(ims, 1): im.save(os.path.join(OUT, f'icon-{i}.png'))
    sheet = Image.new('RGBA', (4 * 230 + 50, 330), (246, 242, 251, 255)); d = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        x = 20 + i * 235
        sheet.alpha_composite(im.resize((180, 180), Image.LANCZOS), (x, 20))
        sheet.alpha_composite(im.resize((64, 64), Image.LANCZOS), (x, 230))           # 手机主屏幕大约这么大
        sheet.alpha_composite(im.resize((32, 32), Image.LANCZOS), (x + 90, 246))     # 浏览器标签页
        d.text((x + 150, 255), str(i + 1), font=T.font('round', 30), fill=(46, 42, 74))
    sheet.convert('RGB').save(os.path.join(OUT, 'icons-compare.png')); print('ok')
