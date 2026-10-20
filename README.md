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

中文版默认由家长判断，英文版默认「游戏来听」（英文版家长多半不会中文）；选过一次就按选的来。设置里「谁来听读得对不对？」改成「🎤 游戏来听」时（小朋友一个人玩，或家长不会中文），读字卡上点 🎤 读出来，浏览器的语音识别（Safari 用 Apple，Chrome 用 Google）
听写出汉字，再转成拼音和这个字比较：字一样或同音 → 读对；拼音对、声调或相近的音（zh/z、ch/c、sh/s、n/l、-ng/-n）不同 → 🟡 差不多，
算对并播放标准读音；其他 → 再读一次，还不对就回到上次的位置。「🤔 我不会」直接显示学字卡并播放读音。
Chrome/Edge 上另外看麦克风音量，读完 0.6 秒就停止，不用等背景噪音。浏览器不支持或麦克风不能用时，自动换成家长点「读对了 / 没读出来」。
测试页：lab/voice-test.html。

## 学习者和学习进度

不用注册账号：进度存在这台设备的浏览器里（localStorage `szsxq.learners.v1`）。「学习者」是一个人，不是一个座位：
设置页每个玩家名字下面可以选「📈 记录某某的进度」或「👤 不记录」（家长、朋友），所以头像和名字随便换，进度不会乱。
默认记录：一个座位第一次读字时才建学习者（不会留下空的），同名的空闲学习者会直接接着用；选了「不记录」的座位会一直记住。
一局结束后所有学习者合在一张小结卡里。
- 每次读字都记下：不用提示读对（ok）、用提示读对（hint）、没读出来（miss）、最后见到的时间。
- 不用提示读对 2 次 = 已掌握（MASTER_OK）。每局里一个字只有第一次读算数：这局已经有人读过（或学字卡念过）的字，再读对只算「有帮助」，
  所以两次读对一般来自两局不同的游戏。已掌握的字读错了，就退回「正在学」。
- 已掌握的字按间隔复习（REVIEW_DAYS）：掌握后 3 天、再 1 周、3 周、2 个月；到期的字不用帮助读对，就进入下一个间隔。
  2 个月的复习也读对 = 🏅 牢牢记住：不再复习，只有字库里别的字都用完时才拿来补棋盘。
- 摆新棋盘时，大部分是在座学习者还没掌握的字，再加上到期该复习的字（最多约 20%，REVIEW_SHARE，最过期的先上）。
- 一局结束后有一张小结卡（每个学习者这局读对的字、新掌握的字）；「📈 学习进度」页面有掌握圆环、字表格子（绿 = 已掌握，
  黄 = 正在学，灰 = 还没见过）、最近学会、常读错，可以改名字或删除学习者。

### Azure 读音评测（游戏来听的主力）

「游戏来听」先用微软 Azure 的 Pronunciation Assessment：告诉它这个字应该怎么读，它给读音打分（0–100）。
用「连续听，听到第一个结果就停」：Azure 的停顿时间设置和读音评测一起用会报错 1007，单次识别又要 6–10 秒（lab/azure-test.html 测出来的）。
打开 miscue（找出读错的字）。Azure 识别出的字总是偏向应该读的字（读成「块」也显示「吗」），所以不看识别出的字，只看错误类型和准确度：
错误类型 None → ✅；标成 Mispronunciation 但准确度 ≥ 60（AZ_HALF）→ 🟡；更低 → ❌。测试时读对是 None / 68–74 分，读错是 Mispronunciation / 10–59 分。
卡片上显示「读音评分 N / 100」方便以后调分数线。
Azure 的密钥不放在网页里：Cloudflare Worker（代码在 worker/speech-token.js，地址 SPEECH_TOKEN_URL）用密钥换 10 分钟的临时凭证，
只给本网站和本地预览用。Azure 资源：Speech services，免费 F0，区域 westus2；Worker 的变量 AZURE_KEY（Secret）、AZURE_REGION。
连不上 Azure（比如公司网络挡住 workers.dev）时自动改用浏览器自带的语音识别，再不行就换成家长判断。

**Azure 的准确度（2026-10 用 iPhone 实测）**：单字读音评测很宽松，声调读错（汤 → 糖 90 分）、相近的音（碗 → 环 85 分、半 → 八 70 分）
都会算对；完全不同的字一般能判错，但有时收不到最终结果，要等 8 秒。所以「游戏来听」只当练习，设置里有提示，准确判断请用家长判断。
以后可以试：让小朋友读字再说一个词（组词）用普通识别看有没有这个字，或者换讯飞 / 腾讯的中文口语评测。

## 多台设备同步（同步码，不用注册）

学习进度页的「☁️ 多台设备同步」：建一个 12 位的同步码（比如 ABCD-EFGH-JKMN），在另一台设备上点「输入同步码」，两台设备就共用同样的学习者和进度。
新设备在设置页「谁来玩？」下面也有「在别的设备上玩过？输入同步码」。
- 服务器：同一个 Cloudflare Worker（worker/speech-token.js）的 /sync 部分，数据存在 Cloudflare D1 数据库 hanzi-sync（Worker 里绑定成 DB，表自动建）。
  只存学习者昵称和每个字的读字记录；同步码就是钥匙。
- 同步时机：打开页面、每局结束、打开学习进度页、切到后台、改名或删除学习者之后。
- 合并：读云端 → 和本机合并 → 写回（别的设备刚写过就重来）。学习者全部保留（任何一台删掉的会记下来，其他设备也删）；
  每个字取较大的次数，掌握/复习状态用最后见到这个字的那台设备的。加入同步码时，本机和云端同名的学习者合成一个。
- 本机 localStorage：`szsxq.sync.v1`（同步码、上次同步时间）。
