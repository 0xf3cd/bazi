# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum


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
