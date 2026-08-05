# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from ..defines import Tiangan, Dizhi
from ..rules import ShenshaRules


'''
Predicates for Shensha (神煞) detection: 桃花 / 红艳 / 红鸾 / 天喜 / 驿马.
Each function checks whether a Dizhi forms the Shensha against its anchor (the year/day Dizhi, or a key Tiangan).
'''


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

  if not isinstance(year_or_day_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(year_or_day_dizhi)}')
  if not isinstance(other_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(other_dizhi)}')
  return ShenshaRules.TAOHUA[year_or_day_dizhi] is other_dizhi


def hongyan(key_tiangan: Tiangan, dizhi: Dizhi) -> bool:
  '''
  Check if the input `dizhi` is the HONGYAN (红艳) of `key_tiangan`. If so, return `True`. If not, return `False`.
  检查输入的地支是否是 `key_tiangan` 的红艳星。如果是，返回 `True`。如果不是，返回 `False`。

  Args:
  - key_tiangan: (Tiangan) The anchor Tiangan the lookup keys on (查法锚干) -- the day master under
    the 《三命通会》 reading, or the year tiangan; the caller decides (see `BaziSchool.hongyan_key`, issue #69).
    查法所锚的天干——《三命通会》口径查日干，也可查年干；锚哪个干由调用方决定。
  - dizhi: (Dizhi) The Dizhi.

  Returns: (bool) Whether the `dizhi` is the HONGYAN (红艳) of `key_tiangan`.

  Examples:
  - hongyan(Tiangan.癸, Dizhi.申)
    - return: True
  - hongyan(Tiangan.癸, Dizhi.子)
    - return: False
  '''

  if not isinstance(key_tiangan, Tiangan):
    raise TypeError(f'Expected Tiangan, got {type(key_tiangan)}')
  if not isinstance(dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(dizhi)}')
  return ShenshaRules.HONGYAN[key_tiangan] is dizhi


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

  if not isinstance(year_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(year_dizhi)}')
  if not isinstance(other_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(other_dizhi)}')
  return ShenshaRules.HONGLUAN[year_dizhi] is other_dizhi


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

  if not isinstance(year_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(year_dizhi)}')
  if not isinstance(other_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(other_dizhi)}')
  return ShenshaRules.TIANXI[year_dizhi] is other_dizhi


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

  if not isinstance(year_or_day_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(year_or_day_dizhi)}')
  if not isinstance(other_dizhi, Dizhi):
    raise TypeError(f'Expected Dizhi, got {type(other_dizhi)}')
  return ShenshaRules.YIMA[year_or_day_dizhi] is other_dizhi
