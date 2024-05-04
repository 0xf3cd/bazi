# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum

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


class CalendarDate:
  '''
  CalendarDate is a thin wrapper of the date.
  ATTENTION: No validity check when instantiating.
  '''

  def __init__(self, year: int, month: int, day: int, date_type: CalendarType) -> None:
    # Type check at runtime.
    assert isinstance(year, int)
    assert isinstance(month, int)
    assert isinstance(day, int)
    assert isinstance(date_type, CalendarType)

    self._year = year
    self._month = month
    self._day = day
    self._date_type = date_type

  @property
  def year(self) -> int:
    return self._year

  @property
  def month(self) -> int:
    return self._month

  @property
  def day(self) -> int:
    return self._day

  @property
  def date_type(self) -> CalendarType:
    return self._date_type
  
  def __str__(self) -> str:
    return f'({self.year}-{self.month}-{self.day}, {self.date_type.name})'
  
  def __repr__(self) -> str:
    return f'CalendarDate({self.year}, {self.month}, {self.day}, {self.date_type.name})'
  
  def __eq__(self, other: object) -> bool:
    if not isinstance(other, CalendarDate):
      raise TypeError('Not a CalendarDate object.')
    if self.date_type != other.date_type:
      return False
    if self.year != other.year or self.month != other.month or self.day != other.day:
      return False
    return True
  
  def __ne__(self, other: object) -> bool:
    if not isinstance(other, CalendarDate):
      raise TypeError('Not a CalendarDate object.')
    return not self.__eq__(other)
  
  def __lt__(self, other: object) -> bool:
    if not isinstance(other, CalendarDate):
      raise TypeError('Not a CalendarDate object.')
    if self.date_type != other.date_type:
      raise TypeError('objects not of the same CalenderType.')
    if self.year != other.year:
      return self.year < other.year
    if self.month != other.month:
      return self.month < other.month
    if self.day != other.day:
      return self.day < other.day
    return False
  
  def __le__(self, other: object) -> bool:
    if not isinstance(other, CalendarDate):
      raise TypeError('Not a CalendarDate object.')
    if self.date_type != other.date_type:
      raise TypeError('objects not of the same CalenderType.')
    if self.year != other.year:
      return self.year < other.year
    if self.month != other.month:
      return self.month < other.month
    if self.day != other.day:
      return self.day < other.day
    return True
  
  def __gt__(self, other: object) -> bool:
    if not isinstance(other, CalendarDate):
      raise TypeError('Not a CalendarDate object.')
    if self.date_type != other.date_type:
      raise TypeError('objects not of the same CalenderType.')
    if self.year != other.year:
      return self.year > other.year
    if self.month != other.month:
      return self.month > other.month
    if self.day != other.day:
      return self.day > other.day
    return False
  
  def __ge__(self, other: object) -> bool:
    if not isinstance(other, CalendarDate):
      raise TypeError('Not a CalendarDate object.')
    if self.date_type != other.date_type:
      raise TypeError('objects not of the same CalenderType.')
    if self.year != other.year:
      return self.year > other.year
    if self.month != other.month:
      return self.month > other.month
    if self.day != other.day:
      return self.day > other.day
    return True
