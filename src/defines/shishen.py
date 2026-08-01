# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import Self

from .enum_base import BaziEnum


class Shishen(BaziEnum):
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

  @classmethod
  def from_str(cls, s: str) -> Self:
    # Overrides the base: also accepts the single-char aliases (e.g. '比' -> 比肩).
    # 覆盖基类：额外接受单字别名。
    assert isinstance(s, str)
    assert len(s) in [1, 2]

    if len(s) == 1:
      t: dict[str, str] = Shishen.str_mapping_table()
      assert s in t
      s = t[s]

    return cls(s)

  @property
  def abbr(self) -> str:
    '''
    The short version of this Shishen. For example, "比" for "比肩", "财" for "正财", etc.
    '''
    t = Shishen.str_mapping_table()
    reversed_t = { v : k for k, v in t.items() }
    return reversed_t[str(self)]

十神 = Shishen # Alias
