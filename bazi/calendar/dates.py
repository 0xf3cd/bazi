# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import NamedTuple

from ..common import check_declared_types
from ..defines import Dizhi, Jieqi

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
    check_declared_types(self)

  def __str__(self) -> str:
    return f'({self.year}-{self.month}-{self.day}, {self.date_type.name})'

  def __repr__(self) -> str:
    return f'CalendarDate({self.year}, {self.month}, {self.day}, {self.date_type.name})'

  def __ymd(self, other: object) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    if not isinstance(other, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(other)}')
    if self.date_type != other.date_type:
      raise TypeError(f'Expected {self.date_type}, got {other.date_type}')
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


@dataclass(frozen=True, order=True)
class GanzhiYearMonth:
  '''干支年月坐标，以立春起年，月序为 1（寅）至 12（丑）。

  Note:
  - 坐标本身不限定历法表范围，也不指定出生、日期或时刻的归属粒度。
  - 按年、月序排序；不与公历年月或 0-based 月偏移混用。
  '''
  year: int
  month: int

  def __post_init__(self) -> None:
    check_declared_types(self)
    if not 1 <= self.month <= 12:
      raise ValueError(f'Unsupported Ganzhi month: {self.month}')

  @property
  def dizhi(self) -> Dizhi:
    '''此干支月的月支。'''
    return Dizhi.from_index((Dizhi.寅.index + self.month - 1) % 12)

  @property
  def opening_jie(self) -> tuple[int, Jieqi]:
    '''开月节的公历年与节名；丑月由下一公历年的小寒开启。'''
    return self.year + (self.month == 12), Jieqi.jies()[self.month - 1]

  @classmethod
  def from_dizhi(cls, year: int, dizhi: Dizhi) -> 'GanzhiYearMonth':
    '''从干支年与月支构造坐标，不接受公历月份。'''
    if not isinstance(dizhi, Dizhi):
      raise TypeError(f'Expected Dizhi, got {type(dizhi)}')
    return cls(year, (dizhi.index - Dizhi.寅.index) % 12 + 1)

  @classmethod
  def from_jie(cls, jie: JieqiTime) -> 'GanzhiYearMonth':
    '''真实节所开启的干支年月；中气不能开启干支月。'''
    if not isinstance(jie, JieqiTime):
      raise TypeError(f'Expected JieqiTime, got {type(jie)}')
    if not isinstance(jie.jieqi, Jieqi):
      raise TypeError(f'Expected Jieqi, got {type(jie.jieqi)}')
    if not isinstance(jie.moment, datetime):
      raise TypeError(f'Expected datetime, got {type(jie.moment)}')
    jies = Jieqi.jies()
    if jie.jieqi not in jies:
      raise ValueError(f'Unsupported opening Jie: {jie.jieqi}')
    return cls(jie.moment.year - (jie.jieqi is Jieqi.小寒), jies.index(jie.jieqi) + 1)
