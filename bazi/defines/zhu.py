# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''原局年、月、日、时四柱的位置与顺序。'''

from .enum_base import IndexedBaziEnum


class Zhu(IndexedBaziEnum):
  '''原局柱位，按年、月、日、时排序。'''
  NIAN = '年'
  YUE  = '月'
  RI   = '日'
  SHI  = '时'

  # 中文别名
  年 = NIAN
  月 =  YUE
  日 =   RI
  时 =  SHI


柱 = Zhu # 中文别名
