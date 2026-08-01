# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import dataclass
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
  '''Representing the Dayun of a bazi chart. 八字命盘的某步大运。'''
  ganzhi_year: int
  ganzhi:      Ganzhi


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
