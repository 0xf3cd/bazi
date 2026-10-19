# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''命盘计算中共用的值类型与容器。

BaziData 按四柱保存数据，GanzhiData 按天干、地支保存数据；另有运限与属性的小型记录。'''

from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar, Generic, NamedTuple
from collections.abc import Iterator

from .common import frozendict
from .defines import Wuxing, Yinyang, Tiangan, Ganzhi


'''
rules、utils、命盘与流运层共享的不可变领域值类型；通用基础类型见 `common.py`。
'''


class TraitTuple(NamedTuple):
  '''某天干或地支的五行和阴阳。'''
  wuxing:  Wuxing
  yinyang: Yinyang

  def __str__(self) -> str:
    return str(self.yinyang) + str(self.wuxing)


class DayunTuple(NamedTuple):
  '''
  带年份投影标签与完整物理区间的一步大运。

  Note:
  `ganzhi_year` 是所选规则下的起运年份标签。除首步下限外，`JIE_PROJECTED` 下它也是
  `start_moment` 所属干支年；`FIXED_DECADE` 下它只是年表位次。物理区间始终为
  `[start_moment, end_moment)`，不随规则改变；起运年份标签不表示该步大运占据整个标签年。
  '''
  ganzhi_year:  int
  ganzhi:       Ganzhi
  start_moment: datetime
  end_moment:   datetime


class XiaoyunTuple(NamedTuple):
  '''八字命盘的某个小运。'''
  xusui:  int    # 虚岁
  ganzhi: Ganzhi


class LiunianTuple(NamedTuple):
  '''流年。'''
  ganzhi_year: int
  ganzhi:      Ganzhi


class HiddenTianganDict(frozendict[Tiangan, int]):
  '''
  某地支的藏干及各自所占百分比；在 `frozendict` 上定制 `__str__` 展示。
  '''
  def __str__(self) -> str:
    sorted_kv = sorted(self.items(), key=lambda kv : kv[1], reverse=True)
    return ','.join([f'{k}:{v}' for k, v in sorted_kv])


PillarDataType = TypeVar('PillarDataType')
@dataclass(frozen=True)
class BaziData(Generic[PillarDataType]):
  '''
  按年、月、日、时顺序存储四份 `PillarDataType` 数据的泛型容器。
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
  存储一柱天干与地支数据的容器，可作为 `BaziData` 的柱数据类型。
  '''
  tiangan: TianganDataType
  dizhi: DizhiDataType
