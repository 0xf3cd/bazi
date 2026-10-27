# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''天干与明藏层次枚举，保留中文名称。'''

from .enum_base import BaziEnum, IndexedBaziEnum


class Tiangan(IndexedBaziEnum):
  '''天干（Tiangan）。'''
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

  # 中文别名
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

天干 = Tiangan # 中文别名


class TianganLayer(BaziEnum):
  '''天干在一柱中的明干／藏干层次。'''
  MINGGAN = '明干'
  CANGGAN = '藏干'

  # 中文别名
  明干 = MINGGAN
  藏干 = CANGGAN


天干层次 = TianganLayer # 中文别名
