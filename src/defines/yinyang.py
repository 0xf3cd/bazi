# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from .enum_base import BaziEnum


class Yinyang(BaziEnum):
  '''Yinyang / 阴阳'''
  YANG = '阳'
  YIN  = '阴'

  # Aliases
  阳 = YANG
  阴 = YIN

  @classmethod
  def _str_len(cls) -> int | None:
    return 1

  @property
  def opposite(self) -> 'Yinyang':
    return Yinyang.YIN if self is Yinyang.YANG else Yinyang.YANG

阴阳 = Yinyang # Alias
