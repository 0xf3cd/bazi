# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Generic, NamedTuple
from collections.abc import Iterator

from .common import frozendict
from .defines import Wuxing, Yinyang, Tiangan, Ganzhi


'''
Immutable domain value shapes shared across layers (rules / utils / chart / transits).
跨层共享的不可变领域值类型。Split out of `common.py` (issue #99), which now keeps the
infrastructure primitives only.
'''


class TraitTuple(NamedTuple):
  '''Representing the Wuxing and Yinyang of a Tiangan or Dizhi. 某天干或地支的五行和阴阳。'''
  wuxing:  Wuxing
  yinyang: Yinyang

  def __str__(self) -> str:
    return str(self.yinyang) + str(self.wuxing)


class DayunTuple(NamedTuple):
  '''
  A Dayun (大运) with its projected year label and complete physical interval.
  带年份投影标签与完整物理区间的一步大运。

  Note:
  `ganzhi_year` is the start-year label under the selected `DayunYearRule`. Under
  `JIE_PROJECTED`, except for the first-label floor, it is also the Ganzhi year containing
  `start_moment`; under `FIXED_DECADE`, it is a table position instead. The physical interval
  is always `[start_moment, end_moment)` and never changes with the rule. A start-year label
  does not mean that the Dayun occupies that entire label year.
  `ganzhi_year` 是所选规则下的起运年份标签。除首步下限外，`JIE_PROJECTED` 下它也是
  `start_moment` 所属干支年；`FIXED_DECADE` 下它只是年表位次。物理区间始终为
  `[start_moment, end_moment)`，不随规则改变；起运年份标签不表示该步大运占据整个标签年。
  '''
  ganzhi_year:  int
  ganzhi:       Ganzhi
  start_moment: datetime
  end_moment:   datetime


class XiaoyunTuple(NamedTuple):
  '''Representing the Xiaoyun of a bazi chart. 八字命盘的某个小运。'''
  xusui:  int    # 虚岁
  ganzhi: Ganzhi


class LiunianTuple(NamedTuple):
  '''Representing a Liunian. 流年。'''
  ganzhi_year: int
  ganzhi:      Ganzhi


class HiddenTianganDict(frozendict[Tiangan, int]):
  '''
  `HiddenTianganDict` reveals the hidden Tiangans info.
  The dict represents the hidden Tiangans (i.e. Stems / 天干) and their percentages in the given Dizhi (Branch / 地支).
  A `HiddenTianganDict` is simply a `frozendict` with a customized `__str__` function.

  `HiddenTianganDict` 代表了某个地支的藏干和藏干各自所占的百分比。
  '''
  def __str__(self) -> str:
    sorted_kv = sorted(self.items(), key=lambda kv : kv[1], reverse=True)
    return ','.join([f'{k}:{v}' for k, v in sorted_kv])


PillarDataType = TypeVar('PillarDataType')
@dataclass(frozen=True)
class BaziData(Generic[PillarDataType]):
  '''
  A generic class for storing Bazi data.
  A `BaziData` object stores 4 `PillarDataType` objects for year, month, day, and hour.
  '''
  year: PillarDataType
  month: PillarDataType
  day: PillarDataType
  hour: PillarDataType

  def __iter__(self) -> Iterator[PillarDataType]:
    return iter((self.year, self.month, self.day, self.hour))


TianganDataType = TypeVar('TianganDataType')
DizhiDataType = TypeVar('DizhiDataType')
@dataclass(frozen=True)
class GanzhiData(Generic[TianganDataType, DizhiDataType]):
  '''
  A helper class for storing the data of a Pillar/Ganzhi.
  Can be used with `BaziData` class.
  '''
  tiangan: TianganDataType
  dizhi: DizhiDataType
