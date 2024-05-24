# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from ..Defines import Dizhi
from ..Rules import RelationshipRules


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
  return RelationshipRules.TAOHUA[year_or_day_dizhi] is other_dizhi
