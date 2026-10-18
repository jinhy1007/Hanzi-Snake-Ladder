# -*- coding: utf-8 -*-
"""试做「动物城运动会」主题的地图样板（不改游戏）：用长棋盘的真实路线画起点、终点两段 2:3 样图，
以第一版中段样图（sports-middle.png）里裁出的几小块为风格样本。

输出到 art-src/samples/。运行：IMAGE_PROVIDER=kie .venv/bin/python tools/theme_samples.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import gen_art as G

OUT = os.path.join(G.ROOT, 'art-src', 'samples')
TRACK = (214, 108, 72)

STYLE = ('Modern 3D-animated family movie look, rendered like a detailed 3D miniature city diorama seen from above: every animal is a '
         'fully three-dimensional rounded character with volume, soft shading and cast shadows (never flat or cartoon-outlined), '
         'bright cheerful saturated colors, warm sunny light, charming and funny, suitable for a 6-year-old. An ORIGINAL city of '
         'anthropomorphic animals of every size wearing simple sporty or everyday clothes — not any existing movie characters. '
         'Absolutely no text, letters, numbers, signs or logos anywhere.')
REF = ('The SECOND attached image is only a small STYLE SWATCH: match its rendering style exactly (3D miniature-diorama look, rounded '
       '3D animals, modern pastel architecture, lighting, colors, level of detail), but do NOT copy any of its buildings, objects or '
       'arrangement — invent new, different buildings and scenes. The layout comes ONLY from the first image: the track must follow '
       'the sketch exactly, and no animal or object may stand on the track. Fill the whole frame with scenery: wherever the sketch is '
       'plain pale green, paint city streets, plazas, buildings, canals and parks — leave nothing empty. ')
ANIMALS = ('Include many different species: fennec foxes, moles, yaks, cheetahs, antelopes, pandas, koalas, kangaroos, ostriches, '
           'snakes, lizards, plus elephants, giraffes, rabbits, beavers and more. ')
ROAD = ('The FIRST attached image is a layout sketch for a board-game map seen from a high, gentle top-down angle. The orange-red band is '
        'the race course: paint it as a smooth terracotta running track with faint white lane lines, in EXACTLY the same position, '
        'width and curves as the sketch. Keep the track completely empty — no animals, objects or shadows on it — because game pieces '
        'will be placed on it. Everything else is the city around the track. ')
SECTIONS = {
    'start': ('bottom', 'This section is the START of the animal city sports-day race. Right where the track begins at the bottom, a white '
              'starting line is painted across it; beside the track a tall giraffe referee in a striped shirt with a whistle raises a '
              'checkered starting flag. Animal athletes warming up and stretching on the grass beside the track (not on it). Around '
              'the track: a modern city with varied buildings — a round glass dome greenhouse full of plants, a little canal with an '
              'arched bridge and small boats, apartment balconies where animals lean out to watch and cheer, little bleachers of fans. '
              'Everyday city life along the sidewalks: pedestrians strolling, an ice-cream truck with animals lining up to buy cones, '
              'a police officer animal keeping order and directing the crowd, and animal kids playing with hula hoops. '),
    'finish': ('top', 'This section is the FINISH of the race, at the top. The track ends at a finish line: a ribbon stretched across the '
               'track under a festive balloon arch — with NO runner crossing it and no animal on the track, because the winner is not '
               'known yet. Beside the finish line an excited crowd of spectators: some chatting excitedly with each other, some '
               'pointing down the track at the runners still on their way, waving pom-poms and flags; an EMPTY winners podium beside '
               'the track. Around: the same modern varied city architecture, a canal with a bridge and boats, animals watching from '
               'balconies, a few pedestrians and an ice-cream cart, colorful streamers and fireworks in a bright sky. '),
}
def guide(g):
    Hpx = round(g['H'] * G.S)
    im = Image.new('RGB', (G.W, Hpx), (226, 232, 214)); d = ImageDraw.Draw(im)
    for pts, w in ((g['road'], 72), (g['conn'], 50)):
        d.line([G.P(p) for p in pts], fill=TRACK, width=round(w * G.S), joint='curve')
        for p in (pts[0], pts[-1]):
            x, y = G.P(p); r = w * G.S / 2; d.ellipse([x - r, y - r, x + r, y + r], fill=TRACK)
    return im


def style_swatch():
    """从用户最喜欢的中段样图里裁四小块拼成风格样本：只给风格，不给构图，避免 AI 照抄整张图。"""
    m = Image.open(os.path.join(OUT, 'sports-middle.png')).convert('RGB')   # 1024x1536
    boxes = [(700, 150, 1024, 474), (560, 900, 884, 1224), (1, 520, 325, 844), (380, 520, 704, 844)]  # 阳台楼、植物园、楼群、加油的动物
    sw = Image.new('RGB', (648, 648), 'white')
    for i, b in enumerate(boxes):
        sw.paste(m.crop(b), ((i % 2) * 324, (i // 2) * 324))
    sw.save(os.path.join(OUT, 'style-swatch.png'))
    return sw


def main():
    os.makedirs(OUT, exist_ok=True)
    g = G.map_geo(G.MAPS['long']); gd = guide(g); Hpx = gd.height
    tops = {'bottom': Hpx - G.WIN_H, 'middle': (Hpx - G.WIN_H) // 2, 'top': 0}
    ref = style_swatch()
    for name, (where, text) in SECTIONS.items():
        out = os.path.join(OUT, f'sports-{name}-v3.png')
        if os.path.exists(out) and '--force' not in sys.argv:
            print('跳过', out); continue
        top = tops[where]
        print(f'  画 {name} …')
        im = G.kie_image(ROAD + REF + text + ANIMALS + STYLE, '2:3', images=[gd.crop((0, top, G.W, top + G.WIN_H)), ref], label=f'sample-{name}')
        im.convert('RGB').resize((G.W, G.WIN_H), Image.LANCZOS).save(out)
        print('完成', out)


if __name__ == '__main__':
    main()
