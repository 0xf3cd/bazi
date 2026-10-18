# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''阴阳枚举 Yinyang 及中文名称阴阳。'''

from .enum_base import BaziEnum


class Yinyang(BaziEnum):
  '''阴阳（Yinyang）。'''
  YANG = '阳'
  YIN  = '阴'

  # 中文别名
  阳 = YANG
  阴 = YIN

  @classmethod
  def _str_len(cls) -> int | None:
    return 1

  @property
  def opposite(self) -> 'Yinyang':
    return Yinyang.YIN if self is Yinyang.YANG else Yinyang.YANG

阴阳 = Yinyang # 中文别名
