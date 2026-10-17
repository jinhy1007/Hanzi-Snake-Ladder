# -*- coding: utf-8 -*-
"""生成 js/hints.js：常用 300 字的拼音和一个常用组词（提示卡用）。

每条格式：字 字的拼音 组词 组词拼音（音节用 _ 连接）。
多音字的读音跟着组词走；避开了「一」「不」变调的词，免得拼音和单字读音对不上。
运行：.venv/bin/python tools/build_hints.py
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

T = """一 yī 第一 dì_yī|二 èr 二十 èr_shí|三 sān 三角 sān_jiǎo|四 sì 四季 sì_jì|五 wǔ 五星 wǔ_xīng|六 liù 六月 liù_yuè|七 qī 七天 qī_tiān|八 bā 八月 bā_yuè|九 jiǔ 九十 jiǔ_shí|十 shí 十分 shí_fēn|百 bǎi 百花 bǎi_huā|千 qiān 千米 qiān_mǐ|万 wàn 千万 qiān_wàn|两 liǎng 两个 liǎng_gè|半 bàn 半天 bàn_tiān|几 jǐ 几个 jǐ_gè|人 rén 大人 dà_rén|爸 bà 爸爸 bà_ba|妈 mā 妈妈 mā_ma|爷 yé 爷爷 yé_ye|奶 nǎi 奶奶 nǎi_nai|哥 gē 哥哥 gē_ge|姐 jiě 姐姐 jiě_jie|弟 dì 弟弟 dì_di|妹 mèi 妹妹 mèi_mei|儿 ér 儿子 ér_zi|子 zǐ 子女 zǐ_nǚ|女 nǚ 女儿 nǚ_ér|男 nán 男孩 nán_hái|孩 hái 孩子 hái_zi|家 jiā 大家 dà_jiā|朋 péng 朋友 péng_you|友 yǒu 好友 hǎo_yǒu|老 lǎo 老师 lǎo_shī|师 shī 老师 lǎo_shī|生 shēng 生日 shēng_rì|王 wáng 国王 guó_wáng|公 gōng 公园 gōng_yuán|主 zhǔ 公主 gōng_zhǔ|宝 bǎo 宝贝 bǎo_bèi|口 kǒu 门口 mén_kǒu|目 mù 目光 mù_guāng|耳 ěr 耳朵 ěr_duo|手 shǒu 小手 xiǎo_shǒu|足 zú 足球 zú_qiú|头 tóu 头发 tóu_fa|发 fà 头发 tóu_fa|牙 yá 牙齿 yá_chǐ|眼 yǎn 眼睛 yǎn_jing|鼻 bí 鼻子 bí_zi|心 xīn 开心 kāi_xīn|身 shēn 身体 shēn_tǐ|脚 jiǎo 小脚 xiǎo_jiǎo|脸 liǎn 笑脸 xiào_liǎn|力 lì 力气 lì_qi|日 rì 生日 shēng_rì|月 yuè 月亮 yuè_liang|天 tiān 天空 tiān_kōng|地 dì 大地 dà_dì|山 shān 高山 gāo_shān|水 shuǐ 喝水 hē_shuǐ|火 huǒ 火车 huǒ_chē|土 tǔ 泥土 ní_tǔ|石 shí 石头 shí_tou|田 tián 田野 tián_yě|风 fēng 大风 dà_fēng|雨 yǔ 下雨 xià_yǔ|云 yún 白云 bái_yún|雪 xuě 雪花 xuě_huā|电 diàn 电视 diàn_shì|星 xīng 星星 xīng_xing|光 guāng 阳光 yáng_guāng|江 jiāng 长江 cháng_jiāng|河 hé 小河 xiǎo_hé|海 hǎi 大海 dà_hǎi|林 lín 森林 sēn_lín|木 mù 木头 mù_tou|花 huā 花朵 huā_duǒ|草 cǎo 小草 xiǎo_cǎo|树 shù 大树 dà_shù|叶 yè 树叶 shù_yè|竹 zhú 竹子 zhú_zi|禾 hé 禾苗 hé_miáo|虹 hóng 彩虹 cǎi_hóng|马 mǎ 小马 xiǎo_mǎ|牛 niú 牛奶 niú_nǎi|羊 yáng 小羊 xiǎo_yáng|鸟 niǎo 小鸟 xiǎo_niǎo|鱼 yú 金鱼 jīn_yú|虫 chóng 虫子 chóng_zi|猫 māo 小猫 xiǎo_māo|狗 gǒu 小狗 xiǎo_gǒu|鸡 jī 小鸡 xiǎo_jī|鸭 yā 鸭子 yā_zi|猪 zhū 小猪 xiǎo_zhū|兔 tù 兔子 tù_zi|龙 lóng 恐龙 kǒng_lóng|虎 hǔ 老虎 lǎo_hǔ|象 xiàng 大象 dà_xiàng|熊 xióng 熊猫 xióng_māo|猴 hóu 猴子 hóu_zi|蛇 shé 小蛇 xiǎo_shé|羽 yǔ 羽毛 yǔ_máo|毛 máo 毛衣 máo_yī|红 hóng 红色 hóng_sè|黄 huáng 黄色 huáng_sè|蓝 lán 蓝天 lán_tiān|绿 lǜ 绿色 lǜ_sè|白 bái 白云 bái_yún|黑 hēi 黑板 hēi_bǎn|紫 zǐ 紫色 zǐ_sè|色 sè 颜色 yán_sè|彩 cǎi 彩虹 cǎi_hóng|金 jīn 金色 jīn_sè|米 mǐ 米饭 mǐ_fàn|饭 fàn 吃饭 chī_fàn|面 miàn 面条 miàn_tiáo|菜 cài 青菜 qīng_cài|果 guǒ 水果 shuǐ_guǒ|瓜 guā 西瓜 xī_guā|苹 píng 苹果 píng_guǒ|茶 chá 喝茶 hē_chá|蛋 dàn 鸡蛋 jī_dàn|糖 táng 糖果 táng_guǒ|汤 tāng 喝汤 hē_tāng|吃 chī 好吃 hǎo_chī|喝 hē 喝水 hē_shuǐ|饼 bǐng 饼干 bǐng_gān|豆 dòu 豆子 dòu_zi|肉 ròu 吃肉 chī_ròu|门 mén 开门 kāi_mén|车 chē 汽车 qì_chē|船 chuán 小船 xiǎo_chuán|书 shū 看书 kàn_shū|本 běn 本子 běn_zi|包 bāo 书包 shū_bāo|衣 yī 衣服 yī_fu|服 fú 衣服 yī_fu|帽 mào 帽子 mào_zi|笔 bǐ 铅笔 qiān_bǐ|刀 dāo 小刀 xiǎo_dāo|尺 chǐ 尺子 chǐ_zi|桌 zhuō 桌子 zhuō_zi|床 chuáng 起床 qǐ_chuáng|灯 dēng 电灯 diàn_dēng|球 qiú 皮球 pí_qiú|画 huà 画画 huà_huà|字 zì 写字 xiě_zì|纸 zhǐ 白纸 bái_zhǐ|杯 bēi 杯子 bēi_zi|碗 wǎn 饭碗 fàn_wǎn|窗 chuāng 窗户 chuāng_hu|房 fáng 房子 fáng_zi|玩 wán 玩具 wán_jù|上 shàng 上面 shàng_miàn|下 xià 下面 xià_miàn|左 zuǒ 左手 zuǒ_shǒu|右 yòu 右手 yòu_shǒu|前 qián 前面 qián_miàn|后 hòu 后面 hòu_miàn|里 lǐ 里面 lǐ_miàn|外 wài 外面 wài_miàn|中 zhōng 中国 zhōng_guó|东 dōng 东方 dōng_fāng|西 xī 西瓜 xī_guā|南 nán 南方 nán_fāng|北 běi 北方 běi_fāng|边 biān 旁边 páng_biān|国 guó 中国 zhōng_guó|城 chéng 城堡 chéng_bǎo|路 lù 马路 mǎ_lù|园 yuán 公园 gōng_yuán|桥 qiáo 小桥 xiǎo_qiáo|年 nián 新年 xīn_nián|今 jīn 今天 jīn_tiān|明 míng 明天 míng_tiān|早 zǎo 早上 zǎo_shang|晚 wǎn 晚上 wǎn_shang|午 wǔ 中午 zhōng_wǔ|时 shí 时间 shí_jiān|候 hòu 时候 shí_hou|春 chūn 春天 chūn_tiān|夏 xià 夏天 xià_tiān|秋 qiū 秋天 qiū_tiān|冬 dōng 冬天 dōng_tiān|夜 yè 夜晚 yè_wǎn|节 jié 节日 jié_rì|来 lái 回来 huí_lái|去 qù 出去 chū_qù|走 zǒu 走路 zǒu_lù|跑 pǎo 跑步 pǎo_bù|跳 tiào 跳舞 tiào_wǔ|飞 fēi 飞机 fēi_jī|坐 zuò 坐下 zuò_xià|站 zhàn 车站 chē_zhàn|看 kàn 看书 kàn_shū|见 jiàn 再见 zài_jiàn|听 tīng 听话 tīng_huà|说 shuō 说话 shuō_huà|话 huà 说话 shuō_huà|读 dú 读书 dú_shū|写 xiě 写字 xiě_zì|唱 chàng 唱歌 chàng_gē|歌 gē 儿歌 ér_gē|笑 xiào 笑脸 xiào_liǎn|哭 kū 哭了 kū_le|开 kāi 开门 kāi_mén|打 dǎ 打球 dǎ_qiú|拿 ná 拿走 ná_zǒu|放 fàng 放学 fàng_xué|洗 xǐ 洗手 xǐ_shǒu|跟 gēn 跟着 gēn_zhe|找 zhǎo 找到 zhǎo_dào|买 mǎi 买菜 mǎi_cài|做 zuò 做饭 zuò_fàn|给 gěi 送给 sòng_gěi|叫 jiào 叫声 jiào_shēng|想 xiǎng 想念 xiǎng_niàn|爱 ài 爱心 ài_xīn|要 yào 想要 xiǎng_yào|会 huì 学会 xué_huì|能 néng 能干 néng_gàn|出 chū 出门 chū_mén|进 jìn 进来 jìn_lái|回 huí 回家 huí_jiā|到 dào 到家 dào_jiā|起 qǐ 起床 qǐ_chuáng|用 yòng 有用 yǒu_yòng|住 zhù 住在 zhù_zài|大 dà 大小 dà_xiǎo|小 xiǎo 小鸟 xiǎo_niǎo|多 duō 很多 hěn_duō|少 shǎo 多少 duō_shǎo|长 cháng 长短 cháng_duǎn|短 duǎn 长短 cháng_duǎn|高 gāo 高山 gāo_shān|低 dī 高低 gāo_dī|远 yuǎn 远方 yuǎn_fāng|近 jìn 远近 yuǎn_jìn|快 kuài 快乐 kuài_lè|慢 màn 慢走 màn_zǒu|好 hǎo 你好 nǐ_hǎo|坏 huài 坏人 huài_rén|新 xīn 新年 xīn_nián|旧 jiù 新旧 xīn_jiù|美 měi 美丽 měi_lì|丽 lì 美丽 měi_lì|冷 lěng 冷水 lěng_shuǐ|热 rè 热水 rè_shuǐ|甜 tián 香甜 xiāng_tián|香 xiāng 香蕉 xiāng_jiāo|真 zhēn 真好 zhēn_hǎo|乐 lè 快乐 kuài_lè|喜 xǐ 喜欢 xǐ_huan|欢 huān 欢笑 huān_xiào|怕 pà 害怕 hài_pà|气 qì 生气 shēng_qì|学 xué 学校 xué_xiào|校 xiào 学校 xué_xiào|课 kè 上课 shàng_kè|文 wén 中文 zhōng_wén|问 wèn 问题 wèn_tí|答 dá 回答 huí_dá|名 míng 名字 míng_zi|同 tóng 同学 tóng_xué|我 wǒ 我们 wǒ_men|你 nǐ 你好 nǐ_hǎo|他 tā 他们 tā_men|她 tā 她们 tā_men|它 tā 它们 tā_men|们 men 我们 wǒ_men|的 de 我的 wǒ_de|了 le 好了 hǎo_le|是 shì 是的 shì_de|不 bù 不好 bù_hǎo|在 zài 现在 xiàn_zài|有 yǒu 有趣 yǒu_qù|和 hé 和平 hé_píng|也 yě 也是 yě_shì|都 dōu 都是 dōu_shì|很 hěn 很好 hěn_hǎo|吗 ma 好吗 hǎo_ma|呢 ne 你呢 nǐ_ne|吧 ba 好吧 hǎo_ba|这 zhè 这里 zhè_lǐ|那 nà 那里 nà_lǐ|什 shén 什么 shén_me|么 me 什么 shén_me|谁 shéi 是谁 shì_shéi|哪 nǎ 哪里 nǎ_lǐ|个 gè 个子 gè_zi|只 zhǐ 只有 zhǐ_yǒu|没 méi 没有 méi_yǒu|就 jiù 就是 jiù_shì|还 hái 还有 hái_yǒu|又 yòu 又大又圆 yòu_dà_yòu_yuán|再 zài 再见 zài_jiàn|把 bǎ 把手 bǎ_shǒu|对 duì 对面 duì_miàn|啊 a 好啊 hǎo_a"""

TONES = str.maketrans('āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ', 'aaaaeeeeiiiioooouuuuüüüü')


def main():
    src = open(os.path.join(ROOT, 'js', 'game.js'), encoding='utf-8').read()
    lib = [c for c in re.search(r"const LIB300 = '([^']*)'", src).group(1) if '一' <= c <= '鿿']
    data, errs = {}, []
    for e in T.split('|'):
        ch, py, w, wpy = e.split(' '); wpy = wpy.split('_')
        if ch in data: errs.append('重复 ' + ch)
        if ch not in w: errs.append(f'{ch} 不在 {w} 里')
        elif len(wpy) != len(w): errs.append(f'{w} 音节数不对 {wpy}')
        elif wpy[w.index(ch)].translate(TONES) != py.translate(TONES): errs.append(f'{ch} {py} 和 {w} 里的 {wpy[w.index(ch)]} 不一致')
        data[ch] = [py, w, ' '.join(wpy)]
    missing = [c for c in lib if c not in data]
    print(f'{len(data)} 条；缺少 {missing}；多出 {[c for c in data if c not in lib]}')
    print('\n'.join(errs) or '检查通过')
    lines = ',\n'.join(f'  "{k}":{json.dumps(v, ensure_ascii=False)}' for k, v in data.items())
    with open(os.path.join(ROOT, 'js', 'hints.js'), 'w', encoding='utf-8') as fo:
        fo.write('/* 提示卡数据（由 tools/build_hints.py 生成）：字 → [拼音, 常用组词, 组词拼音]。\n'
                 '   没有收录的字，游戏会临时加载 pinyin-pro，只显示拼音。 */\nconst HINTS = {\n' + lines + '\n};\n')


if __name__ == '__main__':
    main()
