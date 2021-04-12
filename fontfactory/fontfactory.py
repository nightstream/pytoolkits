# coding=utf-8
"""
fonttools==4.18.2
pip3 install fonttools[ufo,lxml,woff,unicode,interpolatable,plot,symfont,type1,pathops]

fontforge
https://www.jianshu.com/p/5438076cc18e
https://www.cnblogs.com/eastonliu/p/9925652.html

Rpi ELK: https://www.raspberrypi.org/forums/viewtopic.php?f=29&p=1730296
fonttools curveTo NotImplementedError
"""

import os
import io
import re
import random
import string
from collections import OrderedDict

import emoji
from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont


class FontNameTable:

    def __init__(self, family_name='CustomAwesomeFont', style_name='Regular', **kwargs):
        """
        see setupNameTable
        @param family_name:
        @param style_name:
        @param kwargs:
        """
        self.family_name = family_name
        self.style_name = style_name
        self.kwargs = kwargs

    def get_name_strings(self):
        return {
            'familyName': self.family_name,
            'styleName': self.style_name,
            'psName': self.family_name + '-' + self.style_name,
            **self.kwargs,
        }


def _pre_deal_obfuscator_input_str(s: str) -> str:
    """
    Pre Deal Input Strings, to deduplicate string & remove all whitespace & remove emoji.
    @param s:
    @return:
    """
    s = "".join(OrderedDict.fromkeys(s))
    s = emoji.demojize(s)
    pattern = re.compile(r'\s+')
    return re.sub(pattern, '', s)


def _check_str_include_emoji(s: str) -> bool:
    for character in s:
        if character in emoji.UNICODE_EMOJI:
            return True
    return False


def _check_cmap_include_all_text(cmap: dict, s: str) -> bool:
    for character in s:
        if ord(character) not in cmap:
            raise Exception(f'{character} Not in Font Lib!')
    return True


def makeFont(showtext, srcfont, tgtfont):
    """制作字体"""
    source_font = TTFont(srcfont)
    source_cmap = source_font.getBestCmap()

    plain_text = _pre_deal_obfuscator_input_str(showtext)
    obfuscator_code_list = random.sample(range(0xE000, 0xF8FF), len(plain_text))
    _check_cmap_include_all_text(source_cmap, plain_text)

    glyphs, metrics, cmap = {}, {}, {}

    glyph_set = source_font.getGlyphSet()
    pen = TTGlyphPen(glyph_set)
    glyph_order = source_font.getGlyphOrder()

    final_shadow_text: list = []
    _map = {}

    if 'null' in glyph_order:
        glyph_set['null'].draw(pen)
        glyphs['null'] = pen.glyph()
        metrics['null'] = source_font['hmtx']['null']

        final_shadow_text += ['null']

    if '.notdef' in glyph_order:
        glyph_set['.notdef'].draw(pen)
        glyphs['.notdef'] = pen.glyph()
        metrics['.notdef'] = source_font['hmtx']['.notdef']

        final_shadow_text += ['.notdef']

    for index, character in enumerate(plain_text):
        obfuscator_code = obfuscator_code_list[index]
        _hex = hex(obfuscator_code)
        code_cmap_name = _hex.replace('0x', 'uni')
        html_code = _hex.replace('0x', '&#x') + ';'
        _map[character] = (html_code, code_cmap_name, _hex)

        _ord = ord(character)
        final_shadow_text.append(code_cmap_name)
        glyph_set[source_cmap[_ord]].draw(pen)
        glyphs[code_cmap_name] = pen.glyph()
        metrics[code_cmap_name] = source_font['hmtx'][source_cmap[_ord]]
        cmap[obfuscator_code] = code_cmap_name

    horizontal_header = {'ascent': source_font['hhea'].ascent,
                         'descent': source_font['hhea'].descent}

    fb = FontBuilder(source_font['head'].unitsPerEm, isTTF=True)
    fb.setupGlyphOrder(final_shadow_text)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(**horizontal_header)
    fb.setupNameTable(FontNameTable().get_name_strings())
    fb.setupOS2()
    fb.setupPost()

    buf = io.BytesIO()
    buf.name = os.path.basename(tgtfont)
    flavor = buf.name.rsplit(".", 1)[-1]
    fb.save(buf)

    options = subset.Options()
    font = subset.load_font(buf, options)
    options.flavor = flavor
    subset.save_font(font, tgtfont, options)

    return _map


def test():
    """测试"""
    srcfont = "./font/hwxk.ttf"
    srcfont = "./font/littlemingzhaoBold.otf"
    tgtfont = "./font/build/mingz.woff2"
    showtext = """
在做移动开发的时候，UI设计师会提供一些定制字体，来提高产品的视觉效果。对于前端开发来说，就需要考虑字体文件的兼容性和文件的大小，在尽量保证UI效果的情况下，兼容更多的浏览器，减少资源体积，使UI效果、兼容性、性能三者达到平衡。由于中文字体字符集的限制，最终字体包文件都会很大，这里不做讨论。下面主要介绍英文、数字符号场景下几种常见的字体格式。

.ttf
TrueType，是Type 1(Adobe公司开发)的竞品，由苹果公司和微软一起开发，是mac系统和window系统用的最广泛的字体，一般从网上下载的字体文件都是ttf格式，点击就能安装到系统上。

.otf
OpenType，TrueType是OpenType的前身，90年代微软寻求苹果的GX排版技术授权失败，被逼自创武功取名为TrueType Open，后来随着计算机的发展，排版技术上需要更加具有表现力的字体，Adobe和微软合作开发了一款新的字体糅合了Type 1和TrueType Open的底层技术，取名为OpenType。后来OpenType被ISO组织接受为标准，称之为Open Font Format（off）。

.eot
Embedded Open Type，主要用于早期版本的IE，微软根据OpenType做了压缩，重新取名为Embedded OpenType，是其专有格式，带有版权保护和压缩。ttf和otf字体在web端来说兼容相对较好，除IE和早期的ios safari和Android不怎么支持外，其他浏览器都兼容都不错。但是由于ttf和otf体积过大，在桌面浏览器的时代还可以满足需求，到了移动浏览器的时代，动辄5MB、10MB的字体文件就显得过于庞大了。因此微软在OpenType的基础上进行了优化压缩，相比OpenType大大减少了体积，但是除了IE以外的浏览器都不太支持，因此也没有成为行业标准。


.woff
Web Open Font Format，可以看作是ttf的再封装，加入了压缩和字体来源信息，通常比ttf小40%。在2010年4月8日，Mozilla基金会、Opera软件公司和微软提交WOFF之后，万维网联盟发表评论指，希望WOFF不久能成为所有浏览器都支持的、“单一、可互操作的（字体）格式”。2010年7月27日，万维网联盟将WOFF作为工作草案发布。也是当前web字体的主流格式。
————————————————
版权声明：本文为CSDN博主「black-heart」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。
原文链接：https://blog.csdn.net/mrqingyu/article/details/96995760
    """
    return makeFont(showtext, srcfont, tgtfont)