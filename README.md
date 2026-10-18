# 识字蛇形棋

给小朋友认汉字的蛇形棋网页游戏：从森林出发，读着汉字走到公主城堡。纯静态网页，直接用浏览器打开 `index.html`（或部署到 GitHub Pages）就能玩。

## 目录

```
index.html            页面
css/style.css         样式
js/game.js            游戏逻辑（字库、棋盘、道具、读音判断）
js/hints.js           提示卡数据：常用 300 字的拼音和常用组词（由 tools/build_hints.py 生成）
images/maps/          地图背景：map-short、map-mid（森林城堡），map-long-sports（长棋盘：动物城运动会）
images/props/         森林主题的道具卡片和角标；images/props/sports/ 是运动会主题的道具和从地图上裁的小图
js/map-paths.js       长棋盘运动会地图上画出来的跑道中线（tools/build_sports.py 生成），格子沿着它摆
tools/gen_art.py      用画图 API 生成上面这些图片的脚本
```

棋盘格子数 = 字数 + 道具数 + 2，游戏按格子数自动选地图：≤31 格用 short，32–39 格用 mid，≥40 格用长棋盘的运动会地图。

## 两个主题

主题跟着地图走（`js/game.js` 里的 `THEMES`）：短、中棋盘是森林城堡，长棋盘是动物城运动会。道具的作用不变，只是图片和故事不同：

| 作用 | 森林城堡 | 动物城运动会 |
|---|---|---|
| 回到起点 | 恶龙 | 踩到香蕉皮掉河里 |
| 停一轮 | 毒蘑菇 | 排队买冰淇淋 |
| 往前两格 | 南瓜马车 | 蹦床 |
| 读对飞三格 | 独角兽 | 能量果汁 |
| 读对两个字跳过去 | 魔法门（入口 / 出口） | 滑翔伞（起飞点 / 降落点） |

运动会地图是三张选定的样图拼成的（`tools/theme_samples.py`、`tools/theme_edits.py` 画样图，`tools/build_sports.py --install` 拼图、描出跑道中线、裁小图），道具图由 `tools/sports_props.py` 生成。样图原图在本地的 `art-src/`，没有上传。

## 重新生成图片

```bash
python3 -m venv .venv && .venv/bin/pip install pillow
export IMAGE_PROVIDER=kie           # 或 openai / gemini
export KIE_API_KEY=...              # 或 OPENAI_API_KEY / GEMINI_API_KEY
.venv/bin/python tools/gen_art.py guides   # 先看道路草图（不花钱）：art-src/guides/
.venv/bin/python tools/gen_art.py all      # 生成全部道具和三张地图
```

API key 也可以写在项目根目录的 `.env` 文件里（一行 `KIE_API_KEY=你的key`），这个文件不会上传到 GitHub。

也可以只画一部分，例如 `tools/gen_art.py maps short`、`tools/gen_art.py props dragon`。API 返回的原图缓存在 `art-src/raw/`，重复运行不会再花钱；加 `--force` 才会重画。

如果改了 `js/game.js` 里的道路参数（`MW`、`R`、`SP` 等或 `MAPS`），要同步改 `tools/gen_art.py` 顶部的同名常量，再重画地图。

## 提示卡

设置页的「提示卡」默认打开，每位玩家每局可以选 3 次、6 次或无限次提示（默认 3 次），读字时点「💡 提示」，卡片翻过来显示拼音和一个常用组词。
常用 300 字的数据在 `tools/build_hints.py` 里，改完运行 `.venv/bin/python tools/build_hints.py` 重新生成 `js/hints.js`。
自己上传的字库里如果有不在这 300 个字里的字，提示卡会临时加载 pinyin-pro，只显示拼音。

更新 css/js 文件后，把 `index.html` 里的 `?v=` 数字加一，手机和电脑上就不会用到旧的缓存文件。
