# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NamedTuple

from ..defines import Jieqi

class CalendarType(Enum):
  '''
  CallendarType is an enum class. It contains 3 types of calendars.
  '''

  '''
  0: SOLAR / 公历
     - New years start on the first days of each year (Jan 1).
     - 公历新年在每年一月一号。
  '''
  SOLAR = 0
  公历 = SOLAR

  '''
  1: LUNAR / 农历 / 阴历
     - New years start on the first days on Zhengyues (正月). There are 13 months in a leap lunar year, and 12 months in a normal year.
     - 农历新年在每年正月初一。农历每个月的划定基于对月亮的观测。农历中的闰年有 13 个月，普通年有 12 个月。
  '''
  LUNAR = 1
  农历 = LUNAR

  '''
  2: GANZHI / 干支历
     - New years start on the days of Start of Spring (立春).
     - When generating Bazi (八字) for a person, we use 24 Chinese Jieqis (24 solar terms / 24 节气) to determine the starts of new years and months.
     - GANZHI is a solar calendar, as 24 Chinese Jieqis are based on the observations of the Sun.
     - 干支历新年在每年立春。干支历不存在闰月。
     - 当进行八字排盘时，人们以 24 节气中的 12 节来划分年、月。
       - 每一年的开始在于立春。每一年也叫“岁”（每一“岁”为立春到下一个立春前一天）
       - 每一个月的开始在于交节日（从立春开始，每两个节气为一个月，如立春、惊蛰、清明、立夏...）。
     - 干支历是一种太阳历，因为 24 节气基于太阳观测。
  '''
  GANZHI = 2
  干支历 = GANZHI


@dataclass(frozen=True)
class CalendarDate:
  '''
  CalendarDate is a thin wrapper of the date.
  ATTENTION: No validity check when instantiating.

  Cross-type comparison semantics follow Python's own convention: `==`/`!=` against a
  non-`CalendarDate` is `False`/`True` (dataclass-generated `__eq__`), while ordering
  against one raises `TypeError`. Ordering across different `CalendarType`s also raises --
  dates on different calendars are incomparable.
  '''
  year: int
  month: int
  day: int
  date_type: CalendarType

  def __post_init__(self) -> None:
    # Type check at runtime.
    if not isinstance(self.year, int):
      raise TypeError(f'Expected int, got {type(self.year)}')
    if not isinstance(self.month, int):
      raise TypeError(f'Expected int, got {type(self.month)}')
    if not isinstance(self.day, int):
      raise TypeError(f'Expected int, got {type(self.day)}')
    if not isinstance(self.date_type, CalendarType):
      raise TypeError(f'Expected CalendarType, got {type(self.date_type)}')

  def __str__(self) -> str:
    return f'({self.year}-{self.month}-{self.day}, {self.date_type.name})'

  def __repr__(self) -> str:
    return f'CalendarDate({self.year}, {self.month}, {self.day}, {self.date_type.name})'

  def __ymd(self, other: object) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    if not isinstance(other, CalendarDate):
      raise TypeError('Not a CalendarDate object.')
    if self.date_type != other.date_type:
      raise TypeError('objects not of the same CalendarType.')
    return (self.year, self.month, self.day), (other.year, other.month, other.day)

  def __lt__(self, other: object) -> bool:
    lhs, rhs = self.__ymd(other)
    return lhs < rhs

  def __le__(self, other: object) -> bool:
    lhs, rhs = self.__ymd(other)
    return lhs <= rhs

  def __gt__(self, other: object) -> bool:
    lhs, rhs = self.__ymd(other)
    return lhs > rhs

  def __ge__(self, other: object) -> bool:
    lhs, rhs = self.__ymd(other)
    return lhs >= rhs


class JieqiTime(NamedTuple):
  '''Representing a Jieqi and its accurate time (datetime). 节气及其精确时间。'''
  jieqi:  Jieqi
  moment: datetime
