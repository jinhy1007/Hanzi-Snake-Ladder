# 识字蛇形棋

给小朋友认汉字的蛇形棋网页游戏：从森林出发，读着汉字走到公主城堡。纯静态网页，直接用浏览器打开 `index.html`（或部署到 GitHub Pages）就能玩。

## 目录

```
index.html            页面
css/style.css         样式
js/game.js            游戏逻辑（字库、棋盘、道具、读音判断）
images/maps/          三张地图背景：map-short / map-mid / map-long
images/props/         道具卡片（coach、mush、dragon）和角标（unicorn、door-open、door-closed），以及城堡、森林小图
tools/gen_art.py      用画图 API 生成上面这些图片的脚本
```

棋盘格子数 = 字数 + 道具数 + 2，游戏按格子数自动选地图：≤31 格用 short，32–39 格用 mid，≥40 格用 long。格子均匀排在画好的道路上。

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
