# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum


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

天干关系 = TianganRelation # Alias


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

地支关系 = DizhiRelation # Alias
