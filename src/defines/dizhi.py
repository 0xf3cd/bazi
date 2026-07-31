# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum


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

地支 = Dizhi # Alias
