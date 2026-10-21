# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''神煞查法函数。

各函数按传入的天干、地支或干支判断所定义的神煞；有分歧的查法由相应参数选择。'''

from enum import Enum
from typing import TypeVar

from ..common import frozendict
from ..defines import Tiangan, Dizhi, Ganzhi
from ..rules import ShenshaRules


'''
神煞判断函数。多数函数按锚查地支神煞；整柱规则直接检查干支，所需锚另行传入。
'''


_TableKey = TypeVar('_TableKey', Tiangan, Dizhi)
_Definition = TypeVar('_Definition', bound=Enum)
_TableValue = TypeVar('_TableValue', bound=Dizhi | frozenset[Dizhi] | None)


def xunkong(ganzhi: Ganzhi) -> frozenset[Dizhi]:
  '''返回干支所在旬的空亡二支；只实现六甲旬空，不含单支筛选或吉凶解释。

  Args:
  - ganzhi: (Ganzhi) 完整查法锚。外层或内部干支字段错型抛 TypeError，阴阳不配抛 ValueError。

  Return: (frozenset[Dizhi]) 所在旬未配天干的二支；取锚柱由调用方决定。
  '''
  if not isinstance(ganzhi, Ganzhi):
    raise TypeError(f'Expected Ganzhi, got {type(ganzhi)}')
  if not isinstance(ganzhi.tiangan, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(ganzhi.tiangan)}')
  if not isinstance(ganzhi.dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(ganzhi.dizhi)}')
  if ganzhi not in ShenshaRules.KONGWANG:
    raise ValueError(f'Unsupported sexagenary Ganzhi: {ganzhi}')
  return ShenshaRules.KONGWANG[ganzhi]


def kongwang(anchor_ganzhi: Ganzhi, target_dizhi: Dizhi) -> bool:
  '''检查目标支是否落入锚柱的六甲旬空二支，不附加目标天干、纳音或冲合条件。

  Args:
  - anchor_ganzhi: (Ganzhi) 完整锚柱，校验与 xunkong 相同。
  - target_dizhi: (Dizhi) 待查地支；错型抛 TypeError。

  Return: (bool) 目标支是否在该旬二支中。
  '''
  absent = xunkong(anchor_ganzhi)
  if not isinstance(target_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(target_dizhi)}')
  return target_dizhi in absent


def _table_shensha(
  table: frozendict[_TableKey, Dizhi],
  key: _TableKey,
  dizhi: Dizhi,
  key_type: type[_TableKey],
) -> bool:
  if not isinstance(key, key_type):
    raise TypeError(f'Expected {key_type.__name__}, got {type(key)}')
  if not isinstance(dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(dizhi)}')
  return table[key] is dizhi


def _defined_shensha(
  tables: frozendict[_Definition, frozendict[Tiangan, _TableValue]],
  key: Tiangan,
  dizhi: Dizhi,
  definition: _Definition,
  definition_type: type[_Definition],
) -> bool:
  '''先校验输入，再查所选定义的表。
  '''
  if not isinstance(key, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(key)}')
  if not isinstance(dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(dizhi)}')
  if not isinstance(definition, definition_type):
    raise TypeError(f'Expected {definition_type.__name__}, got {type(definition)}')
  target = tables[definition][key]
  return dizhi in target if isinstance(target, frozenset) else target is dizhi


def taohua(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查某个地支是否是年支或日支的桃花。

  Args:
  - year_or_day_dizhi: (Dizhi) 年支或日支。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为锚支的桃花。

  Examples:
  - taohua(Dizhi.申, Dizhi.酉)
    - return: True
  - taohua(Dizhi.申, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.TAOHUA, year_or_day_dizhi, other_dizhi, Dizhi)


def hongyan(key_tiangan: Tiangan, dizhi: Dizhi) -> bool:
  '''
  检查输入的地支是否是 `key_tiangan` 的红艳星。

  Args:
  - key_tiangan: (Tiangan) 查法锚干，由调用方决定取哪一柱。
  - dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为锚干的红艳。

  Examples:
  - hongyan(Tiangan.癸, Dizhi.申)
    - return: True
  - hongyan(Tiangan.癸, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.HONGYAN, key_tiangan, dizhi, Tiangan)


def hongluan(year_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查输入的地支是否是年支的红鸾星。

  Args:
  - year_dizhi: (Dizhi) 年支。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为年支的红鸾。

  Examples:
  - hongluan(Dizhi.申, Dizhi.未)
    - return: True
  - hongluan(Dizhi.申, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.HONGLUAN, year_dizhi, other_dizhi, Dizhi)


def tianxi(year_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查输入的地支是否是年支的天喜星。

  Args:
  - year_dizhi: (Dizhi) 年支。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为年支的天喜。

  Examples:
  - tianxi(Dizhi.寅, Dizhi.未)
    - return: True
  - tianxi(Dizhi.寅, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.TIANXI, year_dizhi, other_dizhi, Dizhi)


def yima(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查输入的地支是否是年支或日支的驿马星。

  Args:
  - year_or_day_dizhi: (Dizhi) 年支或日支。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为锚支的驿马。

  Examples:
  - yima(Dizhi.申, Dizhi.寅)
    - return: True
  - yima(Dizhi.申, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.YIMA, year_or_day_dizhi, other_dizhi, Dizhi)


def huagai(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查输入的地支是否是年支或日支的华盖星。

  Args:
  - year_or_day_dizhi: (Dizhi) 年支或日支。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为锚支的华盖。

  Examples:
  - huagai(Dizhi.申, Dizhi.辰)
    - return: True
  - huagai(Dizhi.申, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.HUAGAI, year_or_day_dizhi, other_dizhi, Dizhi)


def jiangxing(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查输入的地支是否是年支或日支的将星。

  Args:
  - year_or_day_dizhi: (Dizhi) 年支或日支。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为锚支的将星。

  Examples:
  - jiangxing(Dizhi.申, Dizhi.子)
    - return: True
  - jiangxing(Dizhi.申, Dizhi.酉)
    - return: False
  '''

  return _table_shensha(ShenshaRules.JIANGXING, year_or_day_dizhi, other_dizhi, Dizhi)


def zaisha(key_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查输入地支是否为锚支的灾煞。

  Args:
  - key_dizhi: (Dizhi) 年支或日支；只查年支或年日兼查由调用方决定。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为锚支的灾煞。

  Examples:
  - zaisha(Dizhi.申, Dizhi.午)
    - return: True
  - zaisha(Dizhi.申, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.ZAISHA, key_dizhi, other_dizhi, Dizhi)


def jiesha(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查输入的地支是否是年支或日支的劫煞。

  Args:
  - year_or_day_dizhi: (Dizhi) 年支或日支。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为锚支的劫煞。

  Examples:
  - jiesha(Dizhi.申, Dizhi.巳)
    - return: True
  - jiesha(Dizhi.申, Dizhi.亥)
    - return: False
  '''

  return _table_shensha(ShenshaRules.JIESHA, year_or_day_dizhi, other_dizhi, Dizhi)


def wangshen(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查输入的地支是否是年支或日支的亡神。

  Args:
  - year_or_day_dizhi: (Dizhi) 年支或日支。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为锚支的亡神。

  Examples:
  - wangshen(Dizhi.申, Dizhi.亥)
    - return: True
  - wangshen(Dizhi.申, Dizhi.巳)
    - return: False
  '''

  return _table_shensha(ShenshaRules.WANGSHEN, year_or_day_dizhi, other_dizhi, Dizhi)


def guchen(year_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查输入的地支是否是年支的孤辰。

  Args:
  - year_dizhi: (Dizhi) 年支。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为年支的孤辰。

  Examples:
  - guchen(Dizhi.子, Dizhi.寅)
    - return: True
  - guchen(Dizhi.子, Dizhi.戌)
    - return: False
  '''

  return _table_shensha(ShenshaRules.GUCHEN, year_dizhi, other_dizhi, Dizhi)


def guasu(year_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  检查输入的地支是否是年支的寡宿。

  Args:
  - year_dizhi: (Dizhi) 年支。
  - other_dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为年支的寡宿。

  Examples:
  - guasu(Dizhi.子, Dizhi.戌)
    - return: True
  - guasu(Dizhi.子, Dizhi.寅)
    - return: False
  '''

  return _table_shensha(ShenshaRules.GUASU, year_dizhi, other_dizhi, Dizhi)


def lushen(day_master: Tiangan, dizhi: Dizhi) -> bool:
  '''
  检查地支是否为日干的禄神。

  Args:
  - day_master: (Tiangan) 日主天干。
  - dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为日干的禄神。

  Examples:
  - lushen(Tiangan.甲, Dizhi.寅)
    - return: True
  - lushen(Tiangan.甲, Dizhi.卯)
    - return: False
  '''

  return _table_shensha(ShenshaRules.LUSHEN, day_master, dizhi, Tiangan)


def jinyu(key_tiangan: Tiangan, dizhi: Dizhi) -> bool:
  '''
  检查地支是否为锚干的金舆。

  Args:
  - key_tiangan: (Tiangan) 年干或日干；只查日干或年日兼查由调用方决定。
  - dizhi: (Dizhi) 待查地支。

  Return: (bool) 待查支是否为锚干的金舆。

  Examples:
  - jinyu(Tiangan.甲, Dizhi.辰)
    - return: True
  - jinyu(Tiangan.甲, Dizhi.巳)
    - return: False
  '''

  return _table_shensha(ShenshaRules.JINYU, key_tiangan, dizhi, Tiangan)


def kuigang(day_ganzhi: Ganzhi) -> bool:
  '''
  检查日柱是否为四个魁罡日之一。

  Args:
  - day_ganzhi: (Ganzhi) 原局日柱。

  Return: (bool) 是否为魁罡日柱。

  Examples:
  - kuigang(Ganzhi.from_str('庚辰'))
    - return: True
  - kuigang(Ganzhi.from_str('甲辰'))
    - return: False
  '''

  if not isinstance(day_ganzhi, Ganzhi):
    raise TypeError(f'Expected Ganzhi, got {type(day_ganzhi)}')
  return day_ganzhi in ShenshaRules.KUIGANG


def tianshe(month_dizhi: Dizhi, day_ganzhi: Ganzhi) -> bool:
  '''
  检查日柱是否为月令所属四时的天赦日。

  Args:
  - month_dizhi: (Dizhi) 原局月令。
  - day_ganzhi: (Ganzhi) 原局日柱。

  Return: (bool) 日柱是否为月令所属四时的天赦日。

  Examples:
  - tianshe(Dizhi.寅, Ganzhi.from_str('戊寅'))
    - return: True
  - tianshe(Dizhi.申, Ganzhi.from_str('戊寅'))
    - return: False
  '''

  if not isinstance(month_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(month_dizhi)}')
  if not isinstance(day_ganzhi, Ganzhi):
    raise TypeError(f'Expected Ganzhi, got {type(day_ganzhi)}')
  return ShenshaRules.TIANSHE[month_dizhi] == day_ganzhi


def yangren(
  day_master: Tiangan,
  dizhi: Dizhi,
  *,
  definition: ShenshaRules.YangrenDef = ShenshaRules.YangrenDef.ZIPING,
) -> bool:
  '''
  按所选定义检查地支是否为日干的羊刃（阳刃）。

  Args:
  - day_master: (Tiangan) 日主天干。
  - dizhi: (Dizhi) 待查地支。
  - definition: (ShenshaRules.YangrenDef) 所用定义，默认 ZIPING，仅五阳干有阳刃。

  Return: (bool) 所选定义下是否为日干的羊刃。

  Examples:
  - yangren(Tiangan.甲, Dizhi.卯)
    - return: True
  - yangren(Tiangan.乙, Dizhi.寅)
    - return: False
  - yangren(Tiangan.乙, Dizhi.寅, definition=ShenshaRules.YangrenDef.DIWANG)
    - return: True
  '''

  return _defined_shensha(
    ShenshaRules.YANGREN,
    day_master,
    dizhi,
    definition,
    ShenshaRules.YangrenDef,
  )


def feiren(
  day_master: Tiangan,
  dizhi: Dizhi,
  *,
  definition: ShenshaRules.YangrenDef = ShenshaRules.YangrenDef.ZIPING,
) -> bool:
  '''
  按所选定义检查地支是否为日干的飞刃。

  Args:
  - day_master: (Tiangan) 日主天干。
  - dizhi: (Dizhi) 待查地支。
  - definition: (ShenshaRules.YangrenDef) 所用定义，默认 ZIPING，仅五阳干有飞刃。

  Return: (bool) 所选定义下是否为日干的飞刃。

  Examples:
  - feiren(Tiangan.甲, Dizhi.酉)
    - return: True
  - feiren(Tiangan.乙, Dizhi.申)
    - return: False
  - feiren(Tiangan.乙, Dizhi.申, definition=ShenshaRules.YangrenDef.DIWANG)
    - return: True
  '''

  return _defined_shensha(
    ShenshaRules.FEIREN,
    day_master,
    dizhi,
    definition,
    ShenshaRules.YangrenDef,
  )


def tianyi(
  key_tiangan: Tiangan,
  dizhi: Dizhi,
  *,
  definition: ShenshaRules.TianyiDef = ShenshaRules.TianyiDef.GENG_WITH_JIA_WU,
) -> bool:
  '''
  按所选来源档案检查地支是否为锚干的天乙贵人。

  Args:
  - key_tiangan: (Tiangan) 年干或日干；查年干、日干或兼查由调用方决定。
  - dizhi: (Dizhi) 待查地支。
  - definition: (ShenshaRules.TianyiDef) 所用来源档案，默认传统
    「甲戊庚牛羊……六辛逢马虎」合并表。

  Return: (bool) 所选定义下是否为锚干的天乙贵人。

  Examples:
  - tianyi(Tiangan.甲, Dizhi.丑)
    - return: True
  - tianyi(Tiangan.庚, Dizhi.午)
    - return: False
  - tianyi(Tiangan.庚, Dizhi.午, definition=ShenshaRules.TianyiDef.GENG_WITH_XIN)
    - return: True
  '''

  return _defined_shensha(
    ShenshaRules.TIANYI,
    key_tiangan,
    dizhi,
    definition,
    ShenshaRules.TianyiDef,
  )


def wenchang(
  key_tiangan: Tiangan,
  dizhi: Dizhi,
  *,
  definition: ShenshaRules.WenchangDef = ShenshaRules.WenchangDef.XIN_ZI,
) -> bool:
  '''
  按所选定义检查地支是否为该天干的文昌。

  本函数查子平法的文昌；禄命法的同名近亲见 `wenchanggui`。

  Args:
  - key_tiangan: (Tiangan) 查法锚干，由调用方决定取哪一柱。
  - dizhi: (Dizhi) 待查地支。
  - definition: (ShenshaRules.WenchangDef) 所用定义，默认 XIN_ZI，辛取子。

  Return: (bool) 所选定义下是否为锚干的文昌。

  Examples:
  - wenchang(Tiangan.甲, Dizhi.巳)
    - return: True
  - wenchang(Tiangan.辛, Dizhi.子)
    - return: True
  - wenchang(Tiangan.辛, Dizhi.子, definition=ShenshaRules.WenchangDef.XIN_XU)
    - return: False
  '''

  return _defined_shensha(
    ShenshaRules.WENCHANG,
    key_tiangan,
    dizhi,
    definition,
    ShenshaRules.WenchangDef,
  )


def wenchanggui(year_tiangan: Tiangan, dizhi: Dizhi) -> bool:
  '''
  检查地支是否为该年干的文昌贵。

  本函数查禄命法的文昌贵；同名近亲中的子平法一颗见 `wenchang`。

  Args:
  - year_tiangan: (Tiangan) 查法锚年干。
  - dizhi: (Dizhi) 待查地支。

  Return: (bool) 是否为年干的文昌贵。

  Examples:
  - wenchanggui(Tiangan.乙, Dizhi.亥)
    - return: True
  - wenchanggui(Tiangan.乙, Dizhi.午)
    - return: False
  '''

  return _table_shensha(ShenshaRules.WENCHANGGUI, year_tiangan, dizhi, Tiangan)


def taiji(
  key_tiangan: Tiangan,
  dizhi: Dizhi,
  *,
  definition: ShenshaRules.TaijiDef = ShenshaRules.TaijiDef.REN_GUI_BOTH,
) -> bool:
  '''
  按所选定义检查地支是否为该天干的太极贵人。

  Note: 一个天干可对多支（戊己占四库），故判成员关系而非相等。

  Args:
  - key_tiangan: (Tiangan) 查法锚干，由调用方决定取哪一柱。
  - dizhi: (Dizhi) 待查地支。
  - definition: (ShenshaRules.TaijiDef) 所用定义，默认 REN_GUI_BOTH，壬癸各兼巳申。

  Return: (bool) 所选定义下是否为锚干的太极贵人。

  Examples:
  - taiji(Tiangan.甲, Dizhi.子)
    - return: True
  - taiji(Tiangan.戊, Dizhi.未)
    - return: True
  - taiji(Tiangan.壬, Dizhi.申)
    - return: True
  - taiji(Tiangan.壬, Dizhi.申, definition=ShenshaRules.TaijiDef.REN_SI_GUI_SHEN)
    - return: False
  '''

  return _defined_shensha(
    ShenshaRules.TAIJI,
    key_tiangan,
    dizhi,
    definition,
    ShenshaRules.TaijiDef,
  )


def guoyin(
  key_tiangan: Tiangan,
  dizhi: Dizhi,
  *,
  definition: ShenshaRules.GuoyinDef = ShenshaRules.GuoyinDef.MODERN,
) -> bool:
  '''
  按所选定义检查地支是否为该天干的国印贵人。

  Args:
  - key_tiangan: (Tiangan) 查法锚干，由调用方决定取哪一柱。
  - dizhi: (Dizhi) 待查地支。
  - definition: (ShenshaRules.GuoyinDef) 所用定义，默认 MODERN 现代通行表。

  Return: (bool) 所选定义下是否为锚干的国印贵人。

  Examples:
  - guoyin(Tiangan.甲, Dizhi.戌)
    - return: True
  - guoyin(Tiangan.甲, Dizhi.酉)
    - return: False
  - guoyin(Tiangan.甲, Dizhi.酉, definition=ShenshaRules.GuoyinDef.WUXING_JINGJI)
    - return: True
  '''

  return _defined_shensha(
    ShenshaRules.GUOYIN,
    key_tiangan,
    dizhi,
    definition,
    ShenshaRules.GuoyinDef,
  )
