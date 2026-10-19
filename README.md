# 识字蛇形棋

给小朋友认汉字的蛇形棋网页游戏：从森林出发，读着汉字走到公主城堡。纯静态网页，直接用浏览器打开 `index.html`（或部署到 GitHub Pages）就能玩。

## 目录

```
index.html            页面
css/style.css         样式
js/game.js            游戏逻辑（字库、棋盘、道具、读音判断）
js/hints.js           提示卡数据：1000 个内置字的拼音和常用组词，以及 500 / 1000 字库的字表（由 tools/build_hints.py 生成）
images/maps/          地图背景：map-short、map-mid（森林城堡），map-long-sports（长棋盘：动物城运动会）
images/props/         森林主题的道具卡片和角标；images/props/sports/ 是运动会主题的道具和从地图上裁的小图
js/map-paths.js       长棋盘运动会地图上画出来的跑道中线（tools/build_sports.py 生成），格子沿着它摆
images/avatars/       玩家头像：10 只原创混搭小神兽（tools/avatars.py 生成），表情和名字在 js/game.js 的 CREATURES 里
sounds/               事件卡和道具的音效（m4a）；js/game.js 里 SOUND_FILES 和每个主题的 sfx 决定哪张卡用哪个，加载失败时退回代码合成的声音
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
字库是一个下拉框：常用 300 字（默认）、500 字、1000 字。常用 300 字的数据在 `tools/build_hints.py` 里，
另外 700 个字在 `tools/hints_more.txt`（按先易后难排，前 200 个组成 500 字库）。改完运行 `.venv/bin/python tools/build_hints.py` 重新生成 `js/hints.js`。
自己上传的字库里如果有不在这 1000 个字里的字，提示卡会临时加载 pinyin-pro，只显示拼音。

更新 css/js 文件后，把 `index.html` 里的 `?v=` 数字加一，手机和电脑上就不会用到旧的缓存文件。

## 音效

| 卡片 | 森林城堡 | 动物城运动会 |
|---|---|---|
| 回起点 | dragon（恶龙喷火、怪叫逃跑） | splash（落水） |
| 停一轮 / 休息一轮 | poison（肚子咕咕叫） | icecream（冰淇淋车，关卡片时淡出）/ queue（排队） |
| 往前两格 | carriage（魔法棒＋马蹄） | boing（弹簧） |
| 读对飞三格 | unicorn | juice（吸管） |
| 读对两个字跳过去 | portal | glide（wee～） |
| 第二个字没读出来 | gust（失望喇叭） | gust |
| 获胜 | castle（号角＋烟花） | cheer（庆祝音乐＋小动物欢呼） |

来源：dragon、poison、unicorn、portal、castle、queue、cheer 用 Kie.ai 上的 Suno「生成声音」做（tools/sounds.py）；
carriage 由两段生成结果拼接；splash、boing、glide、gust（Universfield / floraphonic）和 icecream、juice（freesound_community）
来自 Pixabay 免费音效（Pixabay 内容许可，可免费商用、不需署名）。截取和转码用 tools/trim_sound.py（需要 macOS 的 afconvert）。

## 英文版

设置页和游戏页右上角小喇叭前面的「EN / 中文」按钮切换语言，选择会保存。英文模式下说明、规则、事件卡、道具、提示按钮、状态栏都是英文；
汉字卡、拼音和组词、读音仍是中文。小神兽玩家如果用的是默认名字，会显示英文名（比如 喵喵螈 → Axolo-meow）。
文字都在 js/game.js：主题文字在 THEMES 的 t（中文）和 en（英文），其他地方用 L('中文', 'English')。
英文字体：标题和按钮 Fredoka，说明文字 Andika（为初学认字的孩子设计），见 css/style.css 的 html[lang="en"]。

## 汉字发音

1000 个内置字的发音都是一个小女孩的声音（Kie.ai 上的 Gemini 3.1 Flash 配音，每个字单独生成，多音字按 js/hints.js 的拼音读），
存在 sounds/zi/<字的 Unicode 码位>.m4a（比如「水」是 6c34.m4a），一共约 12 MB。
生成：tools/voices.py --all（已有的会跳过）；后期处理（去静音、统一音量、转码）：tools/voices_post.py。
不在这 1000 个里的字（比如上传的字库）用设备自带的语音。

## 意见反馈和访问统计

- **意见反馈**：设置页右上角 💬 和页面底部「意见反馈」打开 Tally 表单（https://tally.so/r/PRjZ5x），
  玩家不用注册，可以上传一个截图或视频（每个文件最大 10 MB）。反馈在 Tally 后台看，新反馈会发邮件通知。
  表单的隐藏字段 `info` 由游戏自动填写：语言 · 字库 · 棋盘格数 · 手机/电脑 · 版本。
- **访问统计**：GoatCounter，后台 https://shizifun.goatcounter.com 。不用 cookie，不收集个人信息。
  本地预览（127.0.0.1 / localhost）不统计。除了页面访问，还记录这些事件：

  | 事件 | 意思 |
  |---|---|
  | start/c300/28 | 开始一局（字库 c300/c500/c1000/mine，棋盘 20/28/36 格） |
  | win/again、win/home | 有人走到终点后，选了「再玩一局」或「返回主页」 |
  | lang/en、lang/zh | 切换语言 |
  | mylist/upload | 上传了自己的字库表格 |
  | feedback | 打开了意见反馈 |

- 链接和代码在 js/game.js 的 `FEEDBACK_URL`、`STATS_CODE`，换成别的表单或统计账号改这两行就行。

## 汉字字体

汉字卡和棋盘上的字都用文鼎 PL 中楷 CN（AR PL UKai CN，Arphic Public License，见 fonts/ARPHIC-LICENSE.txt），
所以 iPhone、iPad、安卓、Windows、Mac 上看到的楷体都一样（以前 iPhone 没有楷体，会变成宋体）。
字体只留了要用的字：fonts/ukai-core.woff2（内置 1000 字和组词，约 280 KB）、fonts/ukai-more.woff2（GB2312 一级里其余的常用字，
上传自己的字库时才会下载）。生僻字用设备自带字体。改了字库后运行 `.venv/bin/python tools/build_font.py` 重新生成（需要 fonttools、brotli）。

## 游戏来听（读音识别）

设置里「谁来听读得对不对？」选「🎤 游戏来听」时，读字卡上点 🎤 读出来，浏览器的语音识别（Safari 用 Apple，Chrome 用 Google）
听写出汉字，再转成拼音和这个字比较：字一样或同音 → 读对；拼音对、声调或相近的音（zh/z、ch/c、sh/s、n/l、-ng/-n）不同 → 🟡 差不多，
算对并播放标准读音；其他 → 再读一次，还不对就回到上次的位置。「🤔 我不会」直接显示学字卡并播放读音。
Chrome/Edge 上另外看麦克风音量，读完 0.6 秒就停止，不用等背景噪音。浏览器不支持或麦克风不能用时，自动换成家长点「读对了 / 没读出来」。
测试页：lab/voice-test.html。
