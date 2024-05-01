# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum
from typing import NamedTuple


class Tiangan(Enum):
  '''Tiangan / Stem / 天干'''
  JIA  = '甲'
  YI   = '乙'
  BING = '丙'
  DING = '丁'
  WU   = '戊'
  JI   = '己'
  GENG = '庚'
  XIN  = '辛'
  REN  = '壬'
  GUI  = '癸'

  # Aliases
  甲  =  JIA
  乙  =   YI
  丙  = BING
  丁  = DING
  戊  =   WU
  己  =   JI
  庚  = GENG
  辛  =  XIN
  壬  =  REN
  癸  =  GUI

  @classmethod
  def from_str(cls, s: str) -> 'Tiangan':
    assert isinstance(s, str)
    return cls(s)
  
  @classmethod
  def as_list(cls) -> list['Tiangan']:
    return list(cls)
  
  def __str__(self) -> str:
    return str(self.value)
  
  @property
  def index(self) -> int:
    return Tiangan.as_list().index(self)
  
  @staticmethod
  def from_index(i: int) -> 'Tiangan':
    return Tiangan.as_list()[i]

天干 = Tiangan # Alias


class Dizhi(Enum):
  '''Dizhi / Branch / 地支'''
  ZI   = '子'
  CHOU = '丑'
  YIN  = '寅'
  MAO  = '卯'
  CHEN = '辰'
  SI   = '巳'
  WU   = '午'
  WEI  = '未'
  SHEN = '申'
  YOU  = '酉'
  XU   = '戌'
  HAI  = '亥'

  # Aliases
  子   =   ZI
  丑   = CHOU
  寅   =  YIN
  卯   =  MAO
  辰   = CHEN
  巳   =   SI
  午   =   WU
  未   =  WEI
  申   = SHEN
  酉   =  YOU
  戌   =   XU
  亥   =  HAI

  @classmethod
  def from_str(cls, s: str) -> 'Dizhi':
    assert isinstance(s, str)
    return cls(s)
  
  @classmethod
  def as_list(cls) -> list['Dizhi']:
    return list(cls)
  
  def __str__(self) -> str:
    return str(self.value)
  
  @property
  def index(self) -> int:
    return Dizhi.as_list().index(self)
  
  @staticmethod
  def from_index(i: int) -> 'Dizhi':
    return Dizhi.as_list()[i]

地支 = Dizhi  # Alias


class Ganzhi(NamedTuple):
  '''Ganzhi / Stem-branch / 干支'''
  tiangan: Tiangan
  dizhi: Dizhi

  @classmethod
  def from_strs(cls, tiangan_str: str, dizhi_str: str) -> 'Ganzhi':
    return cls(Tiangan.from_str(tiangan_str), Dizhi.from_str(dizhi_str))
  
  @classmethod
  def from_str(cls, tiangan_dizhi_str: str) -> 'Ganzhi':
    assert len(tiangan_dizhi_str) == 2
    return cls(Tiangan.from_str(tiangan_dizhi_str[0]), Dizhi.from_str(tiangan_dizhi_str[1]))
  
  def __str__(self) -> str:
    return f'{self.tiangan}{self.dizhi}'
  
  @staticmethod
  def list_sexagenary_cycle() -> list['Ganzhi']:
    '''
    Return a list of all 60 `Ganzhi` pairs in the sexagenary cycle.
    列出所有 60 甲子中的所有天干地支组合。

    Return: a list of `Ganzhi` tuples representing the 60 ganzhi pairs.
    '''
    tiangan_list: list[Tiangan] = Tiangan.as_list() * 6
    dizhi_list: list[Dizhi] = Dizhi.as_list() * 5
    assert len(tiangan_list) == len(dizhi_list)
    assert len(tiangan_list) == 60 # 60 甲子
    return [Ganzhi(tg, dz) for tg, dz in zip(tiangan_list, dizhi_list)]

  @staticmethod
  def list_sexagenary_cycle_strs() -> list[str]:
    '''
    Return a list of all 60 `Ganzhi` pairs in the sexagenary cycle as strings.
    列出所有 60 甲子中的所有天干地支组合（以字符串形式）。

    Return: a list of strings representing the 60 ganzhi pairs.
    '''
    return [str(gz) for gz in Ganzhi.list_sexagenary_cycle()]

干支 = Ganzhi # Alias


class Jieqi(Enum):
  '''Jieqi / 节气'''
  LICHUN      = '立春'
  YUSHUI      = '雨水'
  JINGZHE     = '惊蛰'
  CHUNFEN     = '春分'
  QINGMING    = '清明'
  GUYU        = '谷雨'
  LIXIA       = '立夏'
  XIAOMAN     = '小满'
  MANGZHONG   = '芒种'
  XIAZHI      = '夏至'
  XIAOSHU     = '小暑'
  DASHU       = '大暑'
  LIQIU       = '立秋'
  CHUSHU      = '处暑'
  BAILU       = '白露'
  QIUFEN      = '秋分'
  HANLU       = '寒露'
  SHUANGJIANG = '霜降'
  LIDONG      = '立冬'
  XIAOXUE     = '小雪'
  DAXUE       = '大雪'
  DONGZHI     = '冬至'
  XIAOHAN     = '小寒'
  DAHAN       = '大寒'

  # Aliases
  立春 = LICHUN
  雨水 = YUSHUI
  惊蛰 = JINGZHE
  春分 = CHUNFEN
  清明 = QINGMING
  谷雨 = GUYU
  立夏 = LIXIA
  小满 = XIAOMAN
  芒种 = MANGZHONG
  夏至 = XIAZHI
  小暑 = XIAOSHU
  大暑 = DASHU
  立秋 = LIQIU
  处暑 = CHUSHU
  白露 = BAILU
  秋分 = QIUFEN
  寒露 = HANLU
  霜降 = SHUANGJIANG
  立冬 = LIDONG
  小雪 = XIAOXUE
  大雪 = DAXUE
  冬至 = DONGZHI
  小寒 = XIAOHAN
  大寒 = DAHAN

  @classmethod
  def from_str(cls, s: str) -> 'Jieqi':
    assert isinstance(s, str)
    assert len(s) == 2
    return cls(s)
  
  @classmethod
  def as_list(cls) -> list['Jieqi']:
    return list(cls)

  def __str__(self) -> str:
    return str(self.value)

节气 = Jieqi # Alias


class Wuxing(Enum):
  '''Wuxing / 五行'''
  WOOD  = '木'
  FIRE  = '火'
  EARTH = '土'
  METAL = '金'
  WATER = '水'

  # Aliases
  木 = WOOD
  火 = FIRE
  土 = EARTH
  金 = METAL
  水 = WATER

  @classmethod
  def from_str(cls, s: str) -> 'Wuxing':
    assert isinstance(s, str)
    assert len(s) == 1
    return cls(s)

  @classmethod
  def as_list(cls) -> list['Wuxing']:
    return list(cls)

  def __str__(self) -> str:
    return str(self.value)
  
  def generates(self, wx: 'Wuxing') -> bool:
    '''
    Check if the input wuxing can be generated from the current.
    检查五行的相生关系，如果当前的五行可以生出输入的五行，则返回 True，否则返回 False。

    Args:
    - self: Wuxing object
    - wx: Wuxing object

    Returns:
    - True if the input wuxing can be generated from the current.
    - False otherwise

    Examples:
    - Wuxing.水.generates(Wuxing.木) -> True  # Water nourishes Wood / 水生木
    - Wuxing.木.generates(Wuxing.火) -> True  # Wood feeds Fire / 木生火
    - Wuxing.火.generates(Wuxing.木) -> False # Fire does not generate Wood / 火不生木
    '''
    if self is Wuxing.木:
      return wx is Wuxing.火
    elif self is Wuxing.火:
      return wx is Wuxing.土
    elif self is Wuxing.土:
      return wx is Wuxing.金
    elif self is Wuxing.金:
      return wx is Wuxing.水
    else:
      assert self is Wuxing.水
      return wx is Wuxing.木
    
  def destructs(self, wx: 'Wuxing') -> bool:
    '''
    Check if the input wuxing can be destroyed by the current.
    检查五行的相克关系，如果当前的五行克输入的五行，则返回 True，否则返回 False。

    Args:
    - self: Wuxing object
    - wx: Wuxing object

    Returns:
    - True if the input wuxing can be destroyed by the current.
    - False otherwise

    Examples:
    - Wuxing.金.destructs(Wuxing.木) -> True  # Metal destroys Wood / 金克木
    - Wuxing.土.destructs(Wuxing.水) -> True  # Earth destroys Water / 土克水
    - Wuxing.水.destructs(Wuxing.土) -> False # Water does not destroy Earth / 水不克土
    '''
    if self is Wuxing.木:
      return wx is Wuxing.土
    elif self is Wuxing.火:
      return wx is Wuxing.金
    elif self is Wuxing.土:
      return wx is Wuxing.水
    elif self is Wuxing.金:
      return wx is Wuxing.木
    else:
      assert self is Wuxing.水
      return wx is Wuxing.火

五行 = Wuxing # Alias


class Yinyang(Enum):
  '''Yinyang / 阴阳'''
  YANG = '阳'
  YIN  = '阴'

  # Aliases
  阳 = YANG
  阴 = YIN

  @classmethod
  def from_str(cls, s: str) -> 'Yinyang':
    assert isinstance(s, str)
    assert len(s) == 1
    return cls(s)
  
  @classmethod
  def as_list(cls) -> list['Yinyang']:
    return list(cls)
  
  def __str__(self) -> str:
    return str(self.value)

  @property
  def opposite(self) -> 'Yinyang':
    return Yinyang.YIN if self is Yinyang.YANG else Yinyang.YANG

阴阳 = Yinyang # Alias


class Shishen(Enum):
  '''Shishen / Ten Gods / 十神'''
  BIJIAN    = '比肩'
  JIECAI    = '劫财'
  SHISHEN   = '食神' # This is not "Ten Gods" in Chinese. This means "Eating God" instead.
  SHANGGUAN = '伤官'
  ZHENGCAI  = '正财'
  PIANCAI   = '偏财'
  ZHENGGUAN = '正官'
  QISHA     = '七杀'
  ZHENGYIN  = '正印'
  PIANYIN   = '偏印'

  # Aliases
  比肩 = BIJIAN
  劫财 = JIECAI
  食神 = SHISHEN
  伤官 = SHANGGUAN
  正财 = ZHENGCAI
  偏财 = PIANCAI
  正官 = ZHENGGUAN
  七杀 = QISHA
  正印 = ZHENGYIN
  偏印 = PIANYIN

  @staticmethod
  def str_mapping_table() -> dict[str, str]:
    '''
    Return the mapping rules (from one Chinese character to the full name) for the Shishens.
    '''
    return {
      '比': '比肩',
      '劫': '劫财',
      '食': '食神',
      '伤': '伤官',
      '财': '正财',
      '才': '偏财',
      '官': '正官',
      '杀': '七杀',
      '印': '正印',
      '枭': '偏印',
    }

  @staticmethod
  def from_str(s: str) -> 'Shishen':
    assert isinstance(s, str)
    assert len(s) in [1, 2]

    if len(s) == 1:
      t: dict[str, str] = Shishen.str_mapping_table()
      assert s in t
      s = t[s]

    return Shishen(s)
  
  @classmethod
  def as_list(cls) -> list['Shishen']:
    return list(cls)
  
  def __str__(self) -> str:
    return str(self.value)
  
  @property
  def abbr(self) -> str:
    '''
    The short version of this Shishen. For example, "比" for "比肩", "才" for "正财", etc.
    '''
    t = Shishen.str_mapping_table()
    reversed_t = { v : k for k, v in t.items() }
    return reversed_t[str(self)]

十神 = Shishen # Alias


class ShierZhangsheng(Enum):
  '''ShierZhangsheng / Twelve Stages of Growth / 十二长生'''
  ZHANGSHENG = '长生'
  MUYU       = '沐浴'
  GUANDAI    = '冠带'
  LINGUAN    = '临官'
  DIWANG     = '帝旺'
  SHUAI      = '衰'
  BING       = '病'
  SI         = '死'
  MU         = '墓'
  JUE        = '绝'
  TAI        = '胎'
  YANG       = '养'

  # Aliases
  长生 = ZHANGSHENG
  沐浴 = MUYU
  冠带 = GUANDAI
  临官 = LINGUAN
  帝旺 = DIWANG
  衰  = SHUAI
  病  = BING
  死  = SI
  墓  = MU
  绝  = JUE
  胎  = TAI
  养  = YANG

  @classmethod
  def from_str(cls, s: str) -> 'ShierZhangsheng':
    assert isinstance(s, str)
    return cls(s)
  
  @classmethod
  def as_list(cls) -> list['ShierZhangsheng']:
    return list(cls)
  
  @property
  def index(self) -> int:
    return ShierZhangsheng.as_list().index(self)
  
  @classmethod
  def from_index(cls, index: int) -> 'ShierZhangsheng':
    return ShierZhangsheng.as_list()[index]

  def __str__(self) -> str:
    return str(self.value)

十二长生 = ShierZhangsheng
 

class TianganRelation(Enum):
  '''TianganRelation / Tiangan Relations / 天干之间的关系'''
  HE    = '合'
  CHONG = '冲'
  SHENG = '生'
  KE    = '克'

  # Aliases
  合 = HE
  冲 = CHONG
  生 = SHENG
  克 = KE

  def __str__(self) -> str:
    return str(self.value)
  
  @classmethod
  def from_str(cls, s: str) -> 'TianganRelation':
    assert isinstance(s, str)
    return cls(s)

天干关系 = TianganRelation


class DizhiRelation(Enum):
  '''DizhiRelation / Dizhi Relations / 地支之间的关系'''
  SANHUI   = '三会'
  LIUHE    = '六合'
  ANHE     = '暗合'
  TONGHE   = '通合'
  TONGLUHE = '通禄合'
  SANHE    = '三合'
  BANHE    = '半合'
  XING     = '刑'
  CHONG    = '冲'
  PO       = '破'
  HAI      = '害'
  SHENG    = '生'
  KE       = '克'


  # Aliases
  三会   = SANHUI
  六合   = LIUHE
  暗合   = ANHE
  通合   = TONGHE
  通禄合 = TONGLUHE
  三合   = SANHE
  半合   = BANHE
  刑    = XING
  冲    = CHONG
  破    = PO
  害    = HAI
  生    = SHENG
  克    = KE

  def __str__(self) -> str:
    return str(self.value)
  
  @classmethod
  def from_str(cls, s: str) -> 'DizhiRelation':
    assert isinstance(s, str)
    return cls(s)

地支关系 = DizhiRelation
