# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum


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
