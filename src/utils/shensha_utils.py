# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from typing import TypeVar

from ..common import frozendict
from ..defines import Tiangan, Dizhi
from ..rules import ShenshaRules


'''
Predicates for Shensha (神煞) detection.
Each function checks whether a Dizhi forms the Shensha against its anchor (the year/day Dizhi, or a key Tiangan).
'''


_TableKey = TypeVar('_TableKey', Tiangan, Dizhi)


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


def taohua(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  Check if the input Dizhi of year pillar or day pillar and other Dizhi form a TAOHUA (桃花).
  检查某个地支是否是年支或日支的桃花。

  Args:
  - year_or_day_dizhi: (Dizhi) The Dizhi of year pillar or day pillar.
  - other_dizhi: (Dizhi) The other Dizhi.

  Returns: (bool) Whether the `other_dizhi` is a TAOHUA of `year_or_day_dizhi`.

  Examples:
  - taohua(Dizhi.申, Dizhi.酉)
    - return: True
  - taohua(Dizhi.申, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.TAOHUA, year_or_day_dizhi, other_dizhi, Dizhi)


def hongyan(key_tiangan: Tiangan, dizhi: Dizhi) -> bool:
  '''
  Check if the input `dizhi` is the HONGYAN (红艳) of `key_tiangan`. If so, return `True`. If not, return `False`.
  检查输入的地支是否是 `key_tiangan` 的红艳星。如果是，返回 `True`。如果不是，返回 `False`。

  Args:
  - key_tiangan: (Tiangan) The anchor Tiangan the lookup keys on (查法锚干) -- the day master under
    the 《三命通会》 reading, or the year tiangan; the caller decides which.
    查法所锚的天干——《三命通会》口径查日干，也可查年干；锚哪个干由调用方决定。
  - dizhi: (Dizhi) The Dizhi.

  Returns: (bool) Whether the `dizhi` is the HONGYAN (红艳) of `key_tiangan`.

  Examples:
  - hongyan(Tiangan.癸, Dizhi.申)
    - return: True
  - hongyan(Tiangan.癸, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.HONGYAN, key_tiangan, dizhi, Tiangan)


def hongluan(year_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  Check if the input `other_dizhi` is the HONGLUAN (红鸾) of `year_dizhi`. If so, return `True`. If not, return `False`.
  检查输入的地支是否是年支的红鸾星。如果是，返回 `True`。如果不是，返回 `False`。

  Args:
  - year_dizhi: (Dizhi) The Dizhi of year pillar.
  - other_dizhi: (Dizhi) The other Dizhi.

  Returns: (bool) Whether the `other_dizhi` is the HONGLUAN (红鸾) of `year_dizhi`.

  Examples:
  - hongluan(Dizhi.申, Dizhi.未)
    - return: True
  - hongluan(Dizhi.申, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.HONGLUAN, year_dizhi, other_dizhi, Dizhi)


def tianxi(year_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  Check if the input `other_dizhi` is the TIANXI (天喜) of `year_dizhi`. If so, return `True`. If not, return `False`.
  检查输入的地支是否是年支的天喜星。如果是，返回 `True`。如果不是，返回 `False`。

  Args:
  - year_dizhi: (Dizhi) The Dizhi of year pillar.
  - other_dizhi: (Dizhi) The other Dizhi.

  Returns: (bool) Whether the `other_dizhi` is the TIANXI (天喜) of `year_dizhi`.

  Examples:
  - tianxi(Dizhi.寅, Dizhi.未)
    - return: True
  - tianxi(Dizhi.寅, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.TIANXI, year_dizhi, other_dizhi, Dizhi)


def yima(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  Check if the input `other_dizhi` is the YIMA (驿马) of `year_or_day_dizhi`. If so, return `True`. If not, return `False`.
  检查输入的地支是否是年支或日支的驿马星。如果是，返回 `True`。如果不是，返回 `False`。

  Args:
  - year_or_day_dizhi: (Dizhi) The Dizhi of year or day pillar.
  - other_dizhi: (Dizhi) The other Dizhi.

  Returns: (bool) Whether the `other_dizhi` is the YIMA (驿马) of `year_or_day_dizhi`.

  Examples:
  - yima(Dizhi.申, Dizhi.寅)
    - return: True
  - yima(Dizhi.申, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.YIMA, year_or_day_dizhi, other_dizhi, Dizhi)


def huagai(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  Check if the input `other_dizhi` is the HUAGAI (华盖) of `year_or_day_dizhi`.
  检查输入的地支是否是年支或日支的华盖星。

  Args:
  - year_or_day_dizhi: (Dizhi) The Dizhi of year or day pillar.
  - other_dizhi: (Dizhi) The other Dizhi.

  Returns: (bool) Whether the `other_dizhi` is the HUAGAI (华盖) of `year_or_day_dizhi`.

  Examples:
  - huagai(Dizhi.申, Dizhi.辰)
    - return: True
  - huagai(Dizhi.申, Dizhi.子)
    - return: False
  '''

  return _table_shensha(ShenshaRules.HUAGAI, year_or_day_dizhi, other_dizhi, Dizhi)


def jiangxing(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  Check if the input `other_dizhi` is the JIANGXING (将星) of `year_or_day_dizhi`.
  检查输入的地支是否是年支或日支的将星。

  Args:
  - year_or_day_dizhi: (Dizhi) The Dizhi of year or day pillar.
  - other_dizhi: (Dizhi) The other Dizhi.

  Returns: (bool) Whether the `other_dizhi` is the JIANGXING (将星) of `year_or_day_dizhi`.

  Examples:
  - jiangxing(Dizhi.申, Dizhi.子)
    - return: True
  - jiangxing(Dizhi.申, Dizhi.酉)
    - return: False
  '''

  return _table_shensha(ShenshaRules.JIANGXING, year_or_day_dizhi, other_dizhi, Dizhi)


def jiesha(year_or_day_dizhi: Dizhi, other_dizhi: Dizhi) -> bool:
  '''
  Check if the input `other_dizhi` is the JIESHA (劫煞) of `year_or_day_dizhi`.
  检查输入的地支是否是年支或日支的劫煞。

  Args:
  - year_or_day_dizhi: (Dizhi) The Dizhi of year or day pillar.
  - other_dizhi: (Dizhi) The other Dizhi.

  Returns: (bool) Whether the `other_dizhi` is the JIESHA (劫煞) of `year_or_day_dizhi`.

  Examples:
  - jiesha(Dizhi.申, Dizhi.巳)
    - return: True
  - jiesha(Dizhi.申, Dizhi.亥)
    - return: False
  '''

  return _table_shensha(ShenshaRules.JIESHA, year_or_day_dizhi, other_dizhi, Dizhi)


def yangren(
  day_master: Tiangan,
  dizhi: Dizhi,
  *,
  definition: ShenshaRules.YangrenDef = ShenshaRules.YangrenDef.ZIPING,
) -> bool:
  '''
  Check whether `dizhi` is the YANGREN (羊刃 / 阳刃) of `day_master` under the
  selected definition. 按所选定义检查地支是否为日干的羊刃（阳刃）。

  Args:
  - day_master: (Tiangan) The Day Master used as the lookup key.
  - dizhi: (Dizhi) The branch to inspect.
  - definition: (ShenshaRules.YangrenDef) The definition to use; defaults to
    ZIPING, where only Yang Tiangans have 阳刃. 所用定义；默认子平五阳干专有口径。

  Returns: (bool) Whether `dizhi` is the Yangren of `day_master` under `definition`.

  Examples:
  - yangren(Tiangan.甲, Dizhi.卯)
    - return: True
  - yangren(Tiangan.乙, Dizhi.寅)
    - return: False
  - yangren(Tiangan.乙, Dizhi.寅, definition=ShenshaRules.YangrenDef.DIWANG)
    - return: True
  '''

  if not isinstance(day_master, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(day_master)}')
  if not isinstance(dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(dizhi)}')
  if not isinstance(definition, ShenshaRules.YangrenDef):
    raise TypeError(f'Expected YangrenDef, got {type(definition)}')
  return ShenshaRules.YANGREN[definition][day_master] is dizhi


def tianyi(
  key_tiangan: Tiangan,
  dizhi: Dizhi,
  *,
  definition: ShenshaRules.TianyiDef = ShenshaRules.TianyiDef.GENG_WITH_JIA_WU,
) -> bool:
  '''
  Check whether `dizhi` is a TIANYI GUIREN (天乙贵人) branch of `key_tiangan`
  under the selected source profile. 按所选出处 profile 检查地支是否为锚干的天乙贵人。

  Args:
  - key_tiangan: (Tiangan) The year or day stem used as the lookup key. The caller
    decides which anchor(s) to inspect. 查法锚干；查年干、日干或兼查由调用方决定。
  - dizhi: (Dizhi) The branch to inspect.
  - definition: (ShenshaRules.TianyiDef) The source profile to use; defaults to the
    traditional merged「甲戊庚牛羊……六辛逢马虎」table.
    所用出处 profile；默认传统牛羊/马虎合并表。

  Returns: (bool) Whether `dizhi` is Tianyi of `key_tiangan` under `definition`.

  Examples:
  - tianyi(Tiangan.甲, Dizhi.丑)
    - return: True
  - tianyi(Tiangan.庚, Dizhi.午)
    - return: False
  - tianyi(Tiangan.庚, Dizhi.午, definition=ShenshaRules.TianyiDef.GENG_WITH_XIN)
    - return: True
  '''

  if not isinstance(key_tiangan, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(key_tiangan)}')
  if not isinstance(dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(dizhi)}')
  if not isinstance(definition, ShenshaRules.TianyiDef):
    raise TypeError(f'Expected TianyiDef, got {type(definition)}')
  return dizhi in ShenshaRules.TIANYI[definition][key_tiangan]
