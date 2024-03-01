# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum
from typing import NamedTuple


class Tiangan(Enum):
  '''Tiangan / 天干'''
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
  '''Dizhi / 地支'''
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
  '''Ganzhi / 干支'''
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
