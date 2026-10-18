# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''十二长生枚举 ShierZhangsheng 及其中文名称。'''

from .enum_base import IndexedBaziEnum


class ShierZhangsheng(IndexedBaziEnum):
  '''十二长生（ShierZhangsheng）。'''
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

  # 中文别名
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

十二长生 = ShierZhangsheng # 中文别名
