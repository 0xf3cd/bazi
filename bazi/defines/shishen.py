# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''十神枚举 Shishen 及中文名称十神。'''

from typing import Final, Self

from .enum_base import BaziEnum
from ..common import frozendict


class Shishen(BaziEnum):
  '''十神（Shishen）。'''
  BIJIAN    = '比肩'
  JIECAI    = '劫财'
  SHISHEN   = '食神' # 食神是十神之一，不是十神的总称。
  SHANGGUAN = '伤官'
  ZHENGCAI  = '正财'
  PIANCAI   = '偏财'
  ZHENGGUAN = '正官'
  QISHA     = '七杀'
  ZHENGYIN  = '正印'
  PIANYIN   = '偏印'

  # 中文别名
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

  @classmethod
  def from_str(cls, s: str) -> Self:
    # 覆盖基类：额外接受单字别名，如 '比' 对应比肩。
    if not isinstance(s, str):
      raise TypeError(f'Expected str, got {type(s)}')
    if len(s) not in [1, 2]:
      raise ValueError(f'Unsupported Shishen string: {s}')

    if len(s) == 1:
      try:
        s = _ABBR_TO_NAME[s]
      except KeyError:
        raise ValueError(f'Unsupported Shishen string: {s}') from None

    return cls(s)

  @property
  def abbr(self) -> str:
    '''此十神的单字简称，如比肩为比、正财为财、偏财为才。'''
    return _NAME_TO_ABBR[str(self)]


_ABBR_TO_NAME: Final[frozendict[str, str]] = frozendict({
  '比': '比肩', '劫': '劫财', '食': '食神', '伤': '伤官', '财': '正财',
  '才': '偏财', '官': '正官', '杀': '七杀', '印': '正印', '枭': '偏印',
})
_NAME_TO_ABBR: Final[frozendict[str, str]] = frozendict({name: abbr for abbr, name in _ABBR_TO_NAME.items()})

十神 = Shishen # 中文别名
