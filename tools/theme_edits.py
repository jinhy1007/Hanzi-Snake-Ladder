# -*- coding: utf-8 -*-
"""按用户意见局部修改运动会主题样图（只改提到的地方，其他保持不变）。

第一轮：v3 → v4；第二轮（start2 / finish2）：v4 → v5。
运行：IMAGE_PROVIDER=kie .venv/bin/python tools/theme_edits.py [start] [finish]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import gen_art as G

OUT = os.path.join(G.ROOT, 'art-src', 'samples')
KEEP = ('Edit this image. Keep everything that is not mentioned exactly as it is: the same 3D miniature-diorama style, the same '
        'running track position, shape, width and lane lines, the same buildings, canal, boats, colors and lighting. The track itself '
        'must stay completely empty — no animals or objects on it. Absolutely no text, letters or numbers. Changes: ')
EDITS = {
    'start': ('sports-start-v3.png', 'sports-start-v4.png',
              '1) Replace the round glass dome greenhouse with a lush, very green children\'s playground: trees and bushes, a slide, '
              'swings, a climbing frame and a sandbox, with little animal kids playing. '
              '2) Move the animal kids playing with hula hoops onto that playground; there must be NO hula-hoop kids near the '
              'starting line. '
              '3) Remove the police officer animals entirely. '
              '4) Add a few small animal cheerleaders with pom-poms standing on the sidewalks beside the track. '
              '5) Add a few spectators standing on the arched bridge, pointing excitedly toward the running track. '),
    'finish': ('sports-finish-v3.png', 'sports-finish-v4.png',
               '1) Keep the balloon finish arch and the finish line exactly where they are, with exactly the same position and '
               'orientation. '
               '2) Spread the cheering crowd out on BOTH sides of the track near the finish instead of bunching them on one side; '
               'the spectators on both sides look down the track toward where the runners will be coming from, cheering, waving '
               'and pointing. '
               '3) Make the empty winners podium bigger and more eye-catching (three tiers, gold, silver and bronze colors, placed '
               'beside the track near the finish, still empty). '),
    # 第二轮：一次只改少数几处，说清楚位置
    'start2': ('sports-start-v4.png', 'sports-start-v5.png',
               '1) Remove every police officer (the animals in dark blue police uniforms and caps) — replace them with ordinary '
               'pedestrians or simply grass and pavement. '
               '2) Remove all the little animal kids with hula hoops from the bottom area near the starting line and the giraffe '
               'referee; put three or four animal kids playing with colorful hula hoops on the green playground with the slide and '
               'swings instead. '),
    'finish2': ('sports-finish-v4.png', 'sports-finish-v5.png',
                '1) Remove the small gold box that sits on the running track just below the finish arch; the track must be empty '
                'there. '
                '2) On the LEFT side of the finish arch, on the plaza beside the track, add a second excited crowd of many different '
                'animals (fennec fox, yak, cheetah, kangaroo, koala, ostrich, mole and more) looking and pointing down the track '
                'toward the coming runners and cheering — so the crowd is on both sides of the finish. '
                '3) On the grass to the right of the track below the right-hand crowd (not on the track), place a big, eye-catching, '
                'empty three-tier winners podium in gold, silver and bronze. '),
    # 第三轮（用户说明后）：从 v4 改。只删起点前面广场上那一群小朋友和跟他们在一起的那位警察，裁判和别处的警察都保留
    'start3': ('sports-start-v4.png', 'sports-start-v6.png',
               '1) At the bottom of the picture, on the paved plaza BELOW the green warm-up lawn (in front of the athletes who are '
               'warming up), there is a group of small animal kids — some with hula hoops, one small giraffe in a striped shirt — and '
               'one police officer with them. Remove that whole group and that one police officer from the plaza, and fill the space '
               'with clean pavement, a couple of round flower beds and a bench. '
               '2) KEEP the tall giraffe referee in the black-and-white striped shirt who stands at the starting line holding the '
               'checkered flag — he must stay exactly as he is, with his flag in his hand. Keep the athletes on the green lawn, the '
               'bleachers, the ice-cream truck and the police officer near the ice-cream truck exactly as they are. '
               '3) On the green playground with the slide and swings (upper part of the picture), add three or four little animal kids '
               'playing with colorful hula hoops. '),
    'finish3': ('sports-finish-v5.png', 'sports-finish-v6.png',
                '1) The small gold, silver and bronze winners podium on the right side of the track, below the right-hand crowd, '
                'is too small: make it about twice as big and more eye-catching — a shiny three-tier podium (gold in the middle and '
                'tallest, silver and bronze on the sides) with a little red carpet in front, still EMPTY, on the plaza beside the '
                'track (not on the track). '
                '2) Keep the balloon finish arch, the finish line, both crowds on the left and right of the arch, the buildings, '
                'canal and everything else exactly as they are. '),
}


def main():
    names = [a for a in sys.argv[1:] if a in EDITS] or ['start', 'finish']
    for k in names:
        src, dst, change = EDITS[k]
        out = os.path.join(OUT, dst)
        if os.path.exists(out) and '--force' not in sys.argv:
            print('跳过', out); continue
        print(f'  改 {k} …')
        im = Image.open(os.path.join(OUT, src)).convert('RGB')
        new = G.kie_image(KEEP + change, '2:3', images=[im], label=f'edit-{k}')
        new.convert('RGB').resize((G.W, G.WIN_H), Image.LANCZOS).save(out)
        print('完成', out)


if __name__ == '__main__':
    main()
