# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum


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
    The short version of this Shishen. For example, "比" for "比肩", "财" for "正财", etc.
    '''
    t = Shishen.str_mapping_table()
    reversed_t = { v : k for k, v in t.items() }
    return reversed_t[str(self)]

十神 = Shishen # Alias
