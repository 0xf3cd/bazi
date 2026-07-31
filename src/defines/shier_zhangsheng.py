# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum


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

十二长生 = ShierZhangsheng # Alias
