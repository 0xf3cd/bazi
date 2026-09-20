# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from .enum_base import BaziEnum


class Jieqi(BaziEnum):
  '''Jieqi / 节气'''
  LICHUN      = '立春'
  YUSHUI      = '雨水'
  JINGZHE     = '惊蛰'
  CHUNFEN     = '春分'
  QINGMING    = '清明'
  GUYU        = '谷雨'
  LIXIA       = '立夏'
  XIAOMAN     = '小满'
  MANGZHONG   = '芒种'
  XIAZHI      = '夏至'
  XIAOSHU     = '小暑'
  DASHU       = '大暑'
  LIQIU       = '立秋'
  CHUSHU      = '处暑'
  BAILU       = '白露'
  QIUFEN      = '秋分'
  HANLU       = '寒露'
  SHUANGJIANG = '霜降'
  LIDONG      = '立冬'
  XIAOXUE     = '小雪'
  DAXUE       = '大雪'
  DONGZHI     = '冬至'
  XIAOHAN     = '小寒'
  DAHAN       = '大寒'

  # Aliases
  立春 = LICHUN
  雨水 = YUSHUI
  惊蛰 = JINGZHE
  春分 = CHUNFEN
  清明 = QINGMING
  谷雨 = GUYU
  立夏 = LIXIA
  小满 = XIAOMAN
  芒种 = MANGZHONG
  夏至 = XIAZHI
  小暑 = XIAOSHU
  大暑 = DASHU
  立秋 = LIQIU
  处暑 = CHUSHU
  白露 = BAILU
  秋分 = QIUFEN
  寒露 = HANLU
  霜降 = SHUANGJIANG
  立冬 = LIDONG
  小雪 = XIAOXUE
  大雪 = DAXUE
  冬至 = DONGZHI
  小寒 = XIAOHAN
  大寒 = DAHAN

  @classmethod
  def _str_len(cls) -> int | None:
    return 2

  @classmethod
  def as_list(cls, ganzhi_year: bool = True) -> list['Jieqi']:
    '''
    If `ganzhi_year` is True (which is the default case), returning the Jieqis
    starting from "立春", as "立春" is the first Jieqi in any ganzhi year.

    If `ganzhi_year` is False, returning the Jieqis starting from "小寒",
    as "小寒" is the first Jieqi in any solar year.
    '''
    if ganzhi_year:
      return list(cls)
    else: # Return in the order that Jieqis appear in a solar year.
      return list(cls)[-2:] + list(cls)[:-2]

节气 = Jieqi # Alias
