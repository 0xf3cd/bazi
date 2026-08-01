# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from .enum_base import IndexedBaziEnum


class Tiangan(IndexedBaziEnum):
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

天干 = Tiangan # Alias
