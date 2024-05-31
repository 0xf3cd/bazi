# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from ..Defines import Tiangan, Dizhi
from ..Rules import ShenshaRules


'''
Functions in this file are used to find all possible Dizhi combos that satisfy different `DizhiRelation`s.
All methods' returns are expected to be immutable.
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

  assert isinstance(year_or_day_dizhi, Dizhi)
  assert isinstance(other_dizhi, Dizhi)
  return ShenshaRules.TAOHUA[year_or_day_dizhi] is other_dizhi


def hongyan(day_master: Tiangan, dizhi: Dizhi) -> bool:
  '''
  Check if the input `dizhi` is the HONGYAN (红艳) of `day_master`. If so, return `True`. If not, return `False`.
  检查输入的地支是否是日主的红艳星。如果是，返回 `True`。如果不是，返回 `False`。

  Args:
  - day_master: (Tiangan) The Tiangan of day pillar.
  - dizhi: (Dizhi) The Dizhi.

  Returns: (bool) Whether the `dizhi` is the HONGYAN (红艳) of `day_master`.

  Examples:
  - hongyan(Tiangan.癸, Dizhi.申)
    - return: True
  - hongyan(Tiangan.癸, Dizhi.子)
    - return: False
  '''

  assert isinstance(day_master, Tiangan)
  assert isinstance(dizhi, Dizhi)
  return ShenshaRules.HONGYAN[day_master] is dizhi


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

  assert isinstance(year_dizhi, Dizhi)
  assert isinstance(other_dizhi, Dizhi)
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

  assert isinstance(year_dizhi, Dizhi)
  assert isinstance(other_dizhi, Dizhi)
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

  assert isinstance(year_or_day_dizhi, Dizhi)
  assert isinstance(other_dizhi, Dizhi)
  return ShenshaRules.YIMA[year_or_day_dizhi] is other_dizhi
