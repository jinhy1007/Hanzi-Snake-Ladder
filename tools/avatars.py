# -*- coding: utf-8 -*-
"""玩家头像：12 只原创「混搭」小神兽（两种动物各取一个特征拼在一起），圆滚滚、彩色、3D 动画电影里的活生物感：全身同一种发光半透明的软材质，颜色按整体设计过渡，不按动物部位拼接：主体动物的身形 + 另一种动物的配色和部件 + 头上一个小装饰。

第一只画好后当风格参考，其余 11 只照着它的画风画，保证一整套风格统一。
输出：art-src/avatars/<名字>.png（透明背景）和 overview.png。
运行：IMAGE_PROVIDER=kie .venv/bin/python tools/avatars.py [名字…] [--force]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import gen_art as G

OUT = os.path.join(G.ROOT, 'art-src', 'avatars')

STYLE = ('An ORIGINAL fantasy creature for a kids\' mobile game (not any existing game or movie character). It is a LIVING '
         'CREATURE, rendered like a character in a modern 3D animated feature film — NOT a plush toy, NOT a stuffed animal, no fabric, '
         'no felt, no seams or stitching, no vinyl or plastic. Chubby rounded body standing upright on short stubby legs, small arms, a '
         'soft round belly. MATERIAL: the WHOLE creature is made of ONE uniform material — a soft, glowing, slightly translucent body with '
         'gentle inner glow and subsurface light, covered all over with a very fine, short, soft velvety fuzz (like peach skin or '
         'velvet) so it looks squishy, warm and huggable; MATTE and diffuse — no glossy shine, no sharp specular highlights, nothing '
         'that looks like glass, ceramic, porcelain, plastic or candy; soft diffuse studio lighting; no long fur, no fabric. Every body part (head, body, limbs, tail, gills, fins, wings, shell, ears) uses this same '
         'material, so it reads as ONE single creature, never stitched together from different animals. Frilly or thin parts are '
         'simply more translucent. Big glossy lifelike eyes with reflections and a lively, curious, happy expression; a natural, alive pose. '
         'The design blends creatures into one believable animal: the body of one, body parts of the other, plus one small natural '
         'feature on the head. COLOR BALANCE: colors flow across the creature as one design, NOT by which animal a part came from: a bright '
         'main color, a lighter belly and muzzle, and a clearly contrasting second color that appears in several places (e.g. tips of '
         'gills and ears, tail tip, cheeks, a stripe on the back) with smooth gradients between them, plus one small accent on the '
         'head. Bright but not neon. Fresh, light and airy overall. Full body, centered, front '
         'three-quarter view, whole creature visible with space around it. Plain flat white background, no ground, no shadow, no other '
         'objects, no text, letters or numbers.')
REF = (' The attached image shows another character from the SAME collectible set: match its uniform soft, matte, velvety glowing translucent material, living-creature 3D film rendering '
       'style, proportions, eye style, lighting, color vividness and level of detail exactly, but this is a completely different '
       'creature with its own different bright colors. ')

CREATURES = [
    ('axolittle', 'A kitten mixed with an axolotl: clearly a KITTEN — a kitten face with two pointy cat ears, a little pink cat nose and '
                  'a cat smile — with a fresh mint-green body, white muzzle and cream belly, the axolotl\'s frilly translucent pink gills '
                  'on both sides of its head, little webbed paws and a smooth axolotl tail; one small orange starfish on its head.'),
    ('hippofly', 'A baby hippo mixed with a butterfly: a round lavender hippo with big colorful butterfly wings with rainbow patterns on its '
                 'back and two little curly antennae.'),
    ('seacoon', 'A raccoon mixed with a seahorse: a raccoon with its black mask and striped face, but with a seahorse\'s curled spiral '
                'tail and a small fin along its back, in teal and coral colors.'),
    ('jellysquirrel', 'A squirrel mixed with a jellyfish: a chubby orange squirrel whose big fluffy tail is a glowing translucent pink-'
                      'and-blue jellyfish bell with flowing ribbon tentacles.'),
    ('dragoink', 'A piglet mixed with a dragon: a round pink piglet with small leathery mint-green dragon wings, two little horns, a row of '
                 'soft spikes on its back, and a tiny friendly flame at the tip of its curly tail.'),
    ('octowl', 'An owl mixed with an octopus: a fluffy round owl with huge eyes and a feather tuft, standing on soft purple octopus '
               'tentacles with little suckers instead of feet.'),
    ('poodlefish', 'A poodle mixed with a clownfish: a curly fluffy poodle with bright orange-and-white clownfish stripes outlined in '
                   'black, little fish fins on its sides and a fish tail.'),
    ('shellpup', 'A puppy mixed with a turtle: a floppy-eared golden puppy carrying a shiny green patterned turtle shell on its back, '
                 'with small turtle-like front flippers.'),
    ('unicwhale', 'A baby whale mixed with a unicorn: a round sky-blue baby whale with a golden spiral unicorn horn, a flowing pastel '
                  'rainbow mane, and a little water spout sparkle.'),
    ('ladyfrog', 'A frog mixed with a ladybug: a chubby green frog wearing a shiny red ladybug wing-case with black spots on its back and '
                 'two tiny antennae.'),
    ('snoala', 'A koala mixed with a snail: a fluffy grey koala with big round ears carrying a colorful spiral snail-shell house on its '
               'back, with two little snail eye-stalks peeking above its ears.'),
    ('mantotter', 'A sea otter mixed with a manta ray: a cuddly brown sea otter with wide navy-and-white manta ray wing fins spreading '
                  'from its sides and a thin manta tail.'),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    force = '--force' in sys.argv
    want = [a for a in sys.argv[1:] if not a.startswith('--')]
    anchor_path = os.path.join(OUT, CREATURES[0][0] + '-raw.png')
    for i, (name, desc) in enumerate(CREATURES):
        if want and name not in want: continue
        raw = os.path.join(OUT, name + '-raw.png'); out = os.path.join(OUT, name + '.png')
        if os.path.exists(out) and not force:
            print('跳过', name); continue
        if not os.path.exists(raw) or force:
            print(f'  画 {name} …')
            refs = [] if i == 0 else [Image.open(anchor_path).convert('RGB')]
            im = G.kie_image(desc + ' ' + STYLE + (REF if refs else ''), '1:1', images=refs, label=f'av-{name}')
            im.convert('RGB').save(raw)
        cut = G.kie_remove_bg(Image.open(raw).convert('RGB'), f'av-{name}')
        box = cut.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
        if box: cut = cut.crop(box)
        cut.save(out); print('完成', name)
    sheet()


def sheet():
    T = 260; cols = 4; rows = 3
    s = Image.new('RGB', (cols * (T + 10) + 10, rows * (T + 40) + 10), 'white'); d = ImageDraw.Draw(s)
    for i, (name, _) in enumerate(CREATURES):
        p = os.path.join(OUT, name + '.png')
        if not os.path.exists(p): continue
        x = 10 + (i % cols) * (T + 10); y = 10 + (i // cols) * (T + 40)
        d.ellipse([x, y, x + T, y + T], fill=(238, 232, 250))
        im = Image.open(p).convert('RGBA'); im.thumbnail((T - 30, T - 30))
        s.paste(im, (x + (T - im.width) // 2, y + (T - im.height) // 2), im)
        d.text((x + 8, y + T + 8), f'{i + 1}. {name}', fill=(60, 50, 90))
    s.save(os.path.join(OUT, 'overview.png'))


if __name__ == '__main__' and not {'--anchor-edit', '--edit2', '--edit3', '--new-ref', '--edit4', '--octowl-redesign', '--edit5'} & set(sys.argv):
    main()


# 用户挑定的第一只：在 art-src/avatars/creature1/axolittle-raw.png 上局部修改，再作为整套的风格参考
ANCHOR_EDIT = ('Edit this character, keeping its exact design, shape, proportions, pose, face, eyes, colors, color gradients, '
               'glow and translucency exactly the same. Change ONLY the surface finish: it currently looks too glossy, like glass or '
               'ceramic. Make the whole body MATTE and soft: cover it with a very fine, short, soft velvety fuzz (like peach skin or '
               'soft velvet) over the gentle inner glow, remove the shiny reflections and sharp specular highlights on the head, belly, '
               'limbs and tail, use soft diffuse lighting, so it looks squishy, warm and huggable while still softly glowing and '
               'slightly translucent. The eyes may stay glossy. Plain flat white background, no text.')

if __name__ == '__main__' and '--anchor-edit' in sys.argv:
    src = os.path.join(OUT, 'creature4', 'axolittle-raw.png')
    im = G.kie_image(ANCHOR_EDIT, '1:1', images=[Image.open(src).convert('RGB')], label='av-anchor-edit')
    im.convert('RGB').save(os.path.join(OUT, 'axolittle-raw.png'))
    print('完成 anchor edit')


# 第二轮：用户看过整套后的修改（在各自现有的图上改，保留画风、脸和配色）。旧版本备份在 art-src/avatars/v1/
EDIT_KEEP = ('Edit this creature. Keep the same soft, matte, velvety, softly glowing translucent material all over, the same cute '
             'face and big glossy eyes, the same 3D animated-film style, lighting and front three-quarter view. Plain flat white '
             'background, no text. Changes: ')
EDITS2 = {
    'seacoon': 'Turn it into a cute LIZARD (like a chubby baby gecko or chameleon) standing on four short splayed lizard legs, '
               'body low and long like a lizard, a lizard head with a wide lizard mouth, and a long curled lizard tail — it must clearly '
               'be a lizard, not a raccoon: no raccoon ears, no raccoon body. Only the COLORS come from the raccoon: grey-brown body, a '
               'dark raccoon mask around the eyes, dark rings on the tail — plus bright turquoise accents on the back crest, toes and '
               'tail rings.',
    'dragoink': 'Change its skin to green, covered with soft rounded dragon scales (cute and soft, matte, not hard or shiny); keep its '
                'shape, wings, horns, piggy snout and tail flame.',
    'octowl': 'Remove the wings completely. Right under the owl head, the whole lower body is an octopus: several big, prominent, '
              'curling octopus tentacles with suckers start directly under the head — no owl body, no owl legs. Keep the tentacles '
              'their current purple color, and make the owl head pink.',
    'poodlefish': 'The fish body below the poodle head must NOT have its own face: remove the fish eyes and fish mouth from the body, '
                  'so there is only ONE face — the white poodle face on the head. Keep everything else exactly the same: the white curly '
                  'poodle head and big fluffy hair, the orange-and-white clownfish stripes on the body, the side fins and the big fish tail.',
    'unicwhale': 'Remove the legs: it is a whale with a round whale body that ends in a big whale tail. Make the flowing rainbow '
                 'unicorn mane much larger and make the whale tail much larger. Keep the golden horn and the face.',
    'ladyfrog': 'Change the arms and legs to real frog limbs: long bent frog hind legs with webbed feet and thin frog arms with round '
                'toe pads. Make the shiny red ladybug wing-case with black spots on its back bigger and more prominent, keeping its '
                'color and texture.',
    'snoala': 'Make the koala nose bigger, a large dark oval koala nose. Remove the koala body: below the koala head is a snail body — '
              'a soft slug-like foot gliding forward with the colorful spiral snail shell on its back — no koala arms or legs.',
}


FROM_CURRENT = {'poodlefish'}   # 在已经改过一次的图上继续改


def edit2(names):
    os.makedirs(os.path.join(OUT, 'v1'), exist_ok=True)
    for name in names:
        raw = os.path.join(OUT, name + '-raw.png'); bak = os.path.join(OUT, 'v1', name + '-raw.png')
        if not os.path.exists(bak):
            Image.open(raw).save(bak)
        print(f'  改 {name} …')
        src = raw if name in FROM_CURRENT else bak
        im = G.kie_image(EDIT_KEEP + EDITS2[name], '1:1', images=[Image.open(src).convert('RGB')], label=f'av2-{name}')
        im.convert('RGB').save(raw)
        cut = G.kie_remove_bg(im.convert('RGB'), f'av2-{name}')
        box = cut.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
        if box: cut = cut.crop(box)
        cut.save(os.path.join(OUT, name + '.png')); print('完成', name)
    sheet()


if __name__ == '__main__' and '--edit2' in sys.argv:
    edit2([a for a in sys.argv[1:] if a in EDITS2] or list(EDITS2))


# 第三轮：进游戏的 8 只全部更开心；喷火猪猪另外加颜色对比、粉鼻子、大尾巴火焰。旧版备份在 art-src/avatars/v2/
IN_GAME = ['axolittle', 'hippofly', 'seacoon', 'dragoink', 'octowl', 'unicwhale', 'ladyfrog', 'snoala', 'squirrot', 'poodlephant']
CHEER = ('Make it look much more CHEERFUL: a big happy open-mouth smile, bright sparkling eyes, rosy cheeks, and a lively, bouncy, '
         'joyful pose (for example waving one arm or fin, or a happy little hop). Keep its design, body parts, colors and soft, matte, '
         'softly glowing material exactly the same.')
EXTRA3 = {
    'dragoink': ' Also: give the body more color contrast — a bright fresh green body with a clearly contrasting warm cream-yellow '
                'belly and a contrasting coral-orange color on the back spikes, horns and wing membranes; make the piggy snout PINK; '
                'make the flame on the tip of the tail much bigger and livelier (bright orange-yellow, cute, not scary).',
}


def edit3(names):
    os.makedirs(os.path.join(OUT, 'v2'), exist_ok=True)
    for name in names:
        raw = os.path.join(OUT, name + '-raw.png'); bak = os.path.join(OUT, 'v2', name + '-raw.png')
        if not os.path.exists(bak):
            Image.open(raw).save(bak)
        print(f'  改 {name} …')
        im = G.kie_image(EDIT_KEEP + CHEER + EXTRA3.get(name, ''), '1:1', images=[Image.open(bak).convert('RGB')], label=f'av3-{name}')
        im.convert('RGB').save(raw)
        cut = G.kie_remove_bg(im.convert('RGB'), f'av3-{name}')
        box = cut.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
        if box: cut = cut.crop(box)
        cut.save(os.path.join(OUT, name + '.png')); print('完成', name)
    export_web()
    sheet()


def export_web():
    """导出游戏用的头像：images/avatars/<名字>.webp，256×256 透明背景。"""
    dst = os.path.join(G.ROOT, 'images', 'avatars'); os.makedirs(dst, exist_ok=True)
    for n in IN_GAME:
        im = Image.open(os.path.join(OUT, n + '.png')).convert('RGBA')
        box = im.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox(); im = im.crop(box)
        s = max(im.size); c = Image.new('RGBA', (round(s * 1.04), round(s * 1.04)), (0, 0, 0, 0))
        c.alpha_composite(im, ((c.width - im.width) // 2, (c.height - im.height) // 2))
        c.resize((256, 256), Image.LANCZOS).save(os.path.join(dst, n + '.webp'), 'WEBP', quality=88, method=6)


if __name__ == '__main__' and '--edit3' in sys.argv:
    edit3([a for a in sys.argv[1:] if a in IN_GAME] or IN_GAME)


# 用户给了设计参考图的两只新角色：第一张图给设计，第二张图（开心版喵喵螈）给画风
NEW_FROM_REF = {
    'squirrot': ('A squirrel mixed with a parrot (the FIRST image shows the design): a chubby scarlet-red parrot body with a cream face, a '
                 'curved grey parrot beak, a yellow chest, rainbow wing feathers (yellow, green, blue), a bright feather crest on the '
                 'head, little parrot feet, and a huge curly fluffy orange squirrel tail.'),
    'poodlephant': ('A poodle mixed with an elephant and a dragonfly (the FIRST image shows the design): a cream poodle body with big '
                    'curly pink-and-lavender poodle fur puffs (head, ears, chest, ankles, tail pom-pom), a small cute elephant trunk '
                    'instead of a snout, two little pink bows, and two pairs of sparkly translucent iridescent dragonfly wings.'),
}
NEW_STYLE = (' Render it in EXACTLY the style of the SECOND image (do not copy that creature, only its style): the same cute 3D '
             'animated-film look, the same soft, matte, velvety, softly glowing slightly translucent material all over the body in one '
             'uniform texture (no realistic feathers or hair strands, no glossy shine), the same big glossy eyes and proportions, chubby '
             'and round. Very cheerful: big happy open-mouth smile, rosy cheeks, a lively bouncy pose. Full body, front three-quarter '
             'view, plain flat white background, no text.')


def new_from_ref(names):
    style = Image.open(os.path.join(OUT, 'axolittle-raw.png')).convert('RGB')
    for name in names:
        ref = Image.open(os.path.join(OUT, 'refs', name + '-ref.webp')).convert('RGB')
        print(f'  画 {name} …')
        im = G.kie_image(NEW_FROM_REF[name] + NEW_STYLE, '1:1', images=[ref, style], label=f'avnew-{name}')
        im.convert('RGB').save(os.path.join(OUT, name + '-raw.png'))
        cut = G.kie_remove_bg(im.convert('RGB'), f'avnew-{name}')
        box = cut.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
        if box: cut = cut.crop(box)
        cut.save(os.path.join(OUT, name + '.png')); print('完成', name)


if __name__ == '__main__' and '--new-ref' in sys.argv:
    new_from_ref([a for a in sys.argv[1:] if a in NEW_FROM_REF] or list(NEW_FROM_REF))


# 第四轮：每只有自己的个性（在当前图上改）。旧版备份在 art-src/avatars/v3/
PERSONA = {
    'seacoon': 'Give it a GOOFY personality: instead of waving, it gives us a big playful WINK with one eye closed, a silly lopsided grin '
               'with the tip of its tongue sticking out, head tilted; one front foot can rest casually on the ground.',
    'dragoink': 'It is fast asleep and SNORING: eyes closed peacefully, mouth slightly open, a cute little "Zzz" sleep bubble floating '
                'above its head (drawn as soft cloud shapes, not letters) near its pink snout and a tiny puff of smoke, curled up sitting on its bottom with wings folded and the tail flame still glowing '
                'warmly. Keep the pink snout, the color contrast and the big tail flame.',
    'unicwhale': 'Make it CALM and friendly rather than excited: a gentle, soft closed-mouth smile with NO teeth at all (whales have no '
                 'teeth), relaxed happy eyes. Make the water spout spraying from the top of its head much bigger and more playful, a '
                 'tall sparkly fountain.',
    'ladyfrog': 'Instead of waving, it does something FUNNY: it is going cross-eyed trying to catch a tiny cartoon fly with its long '
                'stretchy pink tongue, one leg kicked up in the air, a silly surprised expression.',
    'snoala': 'It is BEGGING FOR A HUG: both little arms stretched out wide toward us, big pleading puppy-dog eyes, a sweet hopeful '
              'smile, head tilted, maybe a tiny heart floating above.',
    'squirrot': 'Show it from BEHIND: the creature has its back turned to us — we see the back of its red body, its folded rainbow '
                'wings from behind and the huge curly orange squirrel tail facing us in the foreground. Its head is turned over its '
                'shoulder looking back at us with a guilty, caught-in-the-act face (wide surprised eyes, sheepish embarrassed grin). In '
                'front of its body, partly hidden from us, it clutches an acorn it was secretly hiding; only the top of the acorn peeks '
                'out beside its tail.',
    'octowl': 'Make it look WISE and scholarly: it wears small round glasses perched on its beak and is happily reading an open '
              'storybook held in two of its tentacles, with a thoughtful, pleased little smile and one tentacle raised as if '
              'explaining something clever. Keep the pink owl head and purple octopus tentacles.',
    'poodlephant': 'Make its curly hair and its skin much whiter: snow-white fluffy curls with only a faint pink-lavender tint at the '
                   'tips, and creamy-white skin. Keep the pose, trunk, bows and dragonfly wings.',
}


def edit4(names):
    os.makedirs(os.path.join(OUT, 'v3'), exist_ok=True)
    for name in names:
        raw = os.path.join(OUT, name + '-raw.png'); bak = os.path.join(OUT, 'v3', name + '-raw.png')
        if not os.path.exists(bak):
            Image.open(raw).save(bak)
        print(f'  改 {name} …')
        im = G.kie_image(EDIT_KEEP + PERSONA[name], '1:1', images=[Image.open(bak).convert('RGB')], label=f'av4-{name}')
        im.convert('RGB').save(raw)
        cut = G.kie_remove_bg(im.convert('RGB'), f'av4-{name}')
        box = cut.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
        if box: cut = cut.crop(box)
        cut.save(os.path.join(OUT, name + '.png')); print('完成', name)
    export_web()


if __name__ == '__main__' and '--edit4' in sys.argv:
    edit4([a for a in sys.argv[1:] if a in PERSONA] or list(PERSONA))


# 八爪咕咕重新设计：更成熟、更聪明。出两个配色版本，从 v3 里的原图（没戴眼镜前）改
OCTOWL_REDESIGN = ('Redesign this owl-octopus creature to look WISE, mature and scholarly while staying cute, in the same soft, matte, '
    'velvety, softly glowing 3D animated-film style. Character: an owl head on an octopus body (no wings, the lower body is all '
    'octopus tentacles). Face: slightly smaller, calm, half-lidded thoughtful eyes (not huge baby eyes), two prominent feathery '
    '"eyebrow" tufts and tall ear tufts that give a wise, slightly old-soul look, a small confident closed-mouth smile. Pose: sitting '
    'upright and composed, one tentacle thoughtfully touching its chin, another tentacle holding an open book. Props: small round GOLD '
    'wire glasses perched on the beak; the book is drawn in the SAME soft stylized 3D style as the creature — a chunky rounded '
    'hardcover with gold trim and clean cream pages showing only simple soft shapes and lines, absolutely NO text, letters or old '
    'engraved illustrations. A little scholar-like feather "cape" on the chest with a few tiny gold star and crescent-moon markings. ')
OCTOWL_COLORS = {
    'octowl-a': 'COLORS: deep midnight-indigo head and back, warm cream face disc and chest, tentacles in a deep plum-to-teal gradient, '
                'gold accents (suckers, eyebrow tips, glasses, book trim). Plain flat white background, no text.',
    'octowl-b': 'COLORS: warm chestnut-brown head and back with soft caramel feather tips, cream face disc and chest, tentacles in a '
                'deep forest-green-to-teal gradient, gold accents (suckers, eyebrow tips, glasses, book trim), the book cover deep '
                'burgundy. Plain flat white background, no text.',
}

if __name__ == '__main__' and '--octowl-redesign' in sys.argv:
    src = Image.open(os.path.join(OUT, 'v3', 'octowl-raw.png')).convert('RGB')
    for k, c in OCTOWL_COLORS.items():
        print(f'  画 {k} …')
        im = G.kie_image(OCTOWL_REDESIGN + c, '1:1', images=[src], label=f'av-{k}')
        im.convert('RGB').save(os.path.join(OUT, k + '-raw.png')); print('完成', k)


# 第五轮小修（在当前图上改）
EDITS5 = {
    'seacoon': 'Change only the tongue: replace the human-like tongue with a long, thin, pink LIZARD tongue (like a gecko\'s) that '
               'curls up and is licking its own winking closed eye, the way geckos lick their eyes. Keep the wink, the goofy grin, the '
               'pose, the colors and everything else exactly the same.',
    'snoala': 'Make the little heart floating above its head much BIGGER (about the size of its head), a soft glowing red-pink heart. '
              'Keep everything else exactly the same.',
    'dragoink': 'Keep its sleeping face and expression EXACTLY the same. Remove the puff of smoke and the "Zzz" bubble; instead, a big '
                'shiny translucent SNOT BUBBLE is blowing out of one nostril of its pink snout as it sleeps (a classic cute cartoon '
                'sleeping bubble). Keep everything else exactly the same.',
}


def edit5(names):
    os.makedirs(os.path.join(OUT, 'v4'), exist_ok=True)
    for name in names:
        raw = os.path.join(OUT, name + '-raw.png'); bak = os.path.join(OUT, 'v4', name + '-raw.png')
        if not os.path.exists(bak):
            Image.open(raw).save(bak)
        print(f'  改 {name} …')
        im = G.kie_image(EDITS5[name] + ' Same soft, matte 3D style. Plain flat white background, no text.', '1:1',
                         images=[Image.open(bak).convert('RGB')], label=f'av6-{name}')
        im.convert('RGB').save(raw)
        cut = G.kie_remove_bg(im.convert('RGB'), f'av6-{name}')
        box = cut.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox()
        if box: cut = cut.crop(box)
        cut.save(os.path.join(OUT, name + '.png')); print('完成', name)
    export_web()


if __name__ == '__main__' and '--edit5' in sys.argv:
    edit5([a for a in sys.argv[1:] if a in EDITS5] or list(EDITS5))
