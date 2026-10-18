# -*- coding: utf-8 -*-
"""动物城运动会主题的道具样图（长棋盘用）：三张卡片 + 三个透明角标。

卡片：落水（回起点）、排队买冰淇淋（停一轮）、蹦床（前进两格）
角标：能量果汁（读对飞三格）、滑翔伞起飞点、滑翔伞降落点（同号成对）

风格样本用 art-src/samples/style-swatch.png（从地图中段样图裁出的几小块）。
输出到 art-src/samples/props/。运行：IMAGE_PROVIDER=kie .venv/bin/python tools/sports_props.py [名字…] [--force]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import gen_art as G

OUT = os.path.join(G.ROOT, 'art-src', 'samples', 'props')
SWATCH = os.path.join(G.ROOT, 'art-src', 'samples', 'style-swatch.png')

STYLE = ('Match the rendering style of the attached style swatch exactly: a modern 3D-animated family movie look like a detailed 3D '
         'miniature diorama — fully three-dimensional rounded characters with volume, soft shading and gentle shadows (never flat or '
         'outlined), bright cheerful colors, warm sunny light, charming and funny for a 6-year-old. Use the swatch only for style; do '
         'not copy its buildings or scene. Original anthropomorphic animal characters, not any existing movie characters. '
         'Absolutely no text, letters or numbers anywhere.')
CARD = (' Square storybook card illustration filling the whole frame edge to edge; the subject drawn LARGE in the upper three '
        'quarters; the bottom quarter a calm plain area of the soft background color (a label goes there). No border or frame. ')
BADGE = (' A single isolated object, large and centered, simple bold silhouette that stays recognizable when shown very small; '
         'on a plain flat white background, no ground, no shadow, nothing else in the picture. ')

ITEMS = {
    'splash': ('card', 'A funny ACCIDENT caught mid-fall: a little fennec fox athlete in a sporty tank top and running shoes was '
               'running along the edge of a city canal, stepped on a banana peel and is slipping — feet flying up in the air, body '
               'tipping backwards, arms flailing, about to fall into the water with a big splash starting below. Clearly startled and '
               'flustered: wide surprised eyes, mouth open in an "oh no!" shout, ears flung back — comical, not scary. The banana peel '
               'is shooting away from under its foot. NO life ring, NO swim gear — this is not a swim, it is an accident. Soft '
               'aqua-blue background.'),
    'splash-b': ('card', 'A funny ACCIDENT: a little fennec fox athlete in a sporty tank top has just slipped on a banana peel at the '
                 'edge of a city canal and is falling head-first into the water — splash flying, legs kicking up in the air, a look '
                 'of total panic and surprise on its face (wide eyes, open mouth), a running shoe flying off, the banana peel '
                 'spinning on the edge behind it. Comical slapstick, not scary. NO life ring, NO swim gear. Soft aqua-blue background.'),
    'icecream': ('card', 'A cheerful little panda athlete in running clothes has stopped racing to wait in line at a pastel ice-cream '
                 'truck, holding up a big colorful ice-cream cone with three scoops, smiling happily, a couple of other animals in '
                 'line behind. Soft lilac background.'),
    'trampoline': ('card', 'A joyful little kangaroo athlete bouncing very high above a round blue trampoline, arms up, ears flying, '
                   'motion lines and little stars showing the big jump forward. Soft warm peach-orange background.'),
    'juice': ('badge', 'A magical energy juice: a tall clear cup of glowing orange-yellow fruit juice with a striped straw, a lemon '
              'slice on the rim, a small lightning bolt and a few sparkles around it. Only the cup — NO animals, NO characters, NO '
              'people anywhere in the picture.'),
    'glide-up': ('badge', 'A bright multicolored paraglider wing (rainbow stripes) flying upward, with a small brave cheetah in a '
                 'helmet hanging underneath in the harness, little wind swooshes.'),
    'glide-down': ('badge', 'A round landing target pad with red and white rings like a bullseye, seen at a slight angle, with a small '
                   'triangular orange flag on a pole at its edge and a little puff of wind.'),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    sw = Image.open(SWATCH).convert('RGB')
    names = [a for a in sys.argv[1:] if a in ITEMS] or list(ITEMS)
    for k in names:
        kind, text = ITEMS[k]
        out = os.path.join(OUT, f'{k}.png')
        if os.path.exists(out) and '--force' not in sys.argv:
            print('跳过', out); continue
        print(f'  画 {k} …')
        im = G.kie_image(text + (CARD if kind == 'card' else BADGE) + STYLE, '1:1', images=[sw], label=f'sp-{k}')
        if kind == 'badge':
            im.save(os.path.join(OUT, f'{k}-uncut.png'))
            im = G.kie_remove_bg(im, f'sp-{k}')
            box = im.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
            if box: im = im.crop(box)
        im.save(out)
        print('完成', out)


if __name__ == '__main__' and '--fix' not in sys.argv:
    main()


# 小修：去掉冰淇淋车上的英文字，去掉果汁杯旁边的小动物（只保留杯子、柠檬片、闪电、星光）
FIXES = {
    'icecream': ('icecream.png', 'Edit this image: remove the words written on the ice-cream truck (no letters or text anywhere — keep the '
                 'sign as a plain colorful shape or a cute ice-cream cone picture). Keep everything else exactly the same.'),
    'juice': ('juice-uncut.png', 'Edit this image: remove all the little animals (bears and bunnies) around the cup. Keep only the '
              'cup of glowing juice, the striped straw, the lemon slice, the lightning bolt and the sparkles, exactly as they are, on '
              'the plain white background.'),
}


def fix(names):
    for k in names:
        src, text = FIXES[k]
        im = Image.open(os.path.join(OUT, src)).convert('RGB')
        print(f'  修 {k} …')
        new = G.kie_image(text, '1:1', images=[im], label=f'spfix-{k}')
        if ITEMS[k][0] == 'badge':
            new.save(os.path.join(OUT, f'{k}-uncut.png'))
            new = G.kie_remove_bg(new, f'spfix-{k}')
            box = new.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
            if box: new = new.crop(box)
        new.save(os.path.join(OUT, f'{k}.png'))
        print('完成', k)


if __name__ == '__main__' and '--fix' in sys.argv:
    fix([a for a in sys.argv[1:] if a in FIXES])
