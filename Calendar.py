# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum
from datetime import date, timedelta

from bazi import Ganzhi
from bazi.hkodata import DecodedJieqiDates, DecodedLunarYears, LunarYearInfo

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


class SolarDate:
  '''
  SolarDate represents a date in the solar calendar / gregorian calendar.
  '''
  def __init__(self, year: int, month: int, day: int) -> None:
    # Type check at runtime.
    assert isinstance(year, int)
    assert isinstance(month, int)
    assert isinstance(day, int)

    # Range check at runtime.
    assert 1 <= month <= 12
    assert 1 <= day <= 31

    self._year = year
    self._month = month
    self._day = day

  @property
  def year(self) -> int:
    return self._year

  @property
  def month(self) -> int:
    return self._month

  @property
  def day(self) -> int:
    return self._day

  def to_date(self) -> date:
    return date(self.year, self.month, self.day)
  
  @classmethod
  def from_date(cls, d: date) -> 'SolarDate':
    return cls(d.year, d.month, d.day)

  def __eq__(self, other: object) -> bool:
    if isinstance(other, (date, SolarDate)): # Notice that `datetime` is a subclass of `date`.
      return self.year == other.year and self.month == other.month and self.day == other.day
    return False
  
  def __ne__(self, other: object) -> bool:
    return not self.__eq__(other)


class LunarDate:
  '''
  LunarDate represents a date in the lunar calendar.
  '''
  def __init__(self, year: int, month: int, day: int, is_leap_month: bool, year_ganzhi: Ganzhi) -> None:
    # Type check at runtime.
    assert isinstance(year, int)
    assert isinstance(month, int)
    assert isinstance(day, int)
    assert isinstance(is_leap_month, bool)
    assert isinstance(year_ganzhi, Ganzhi)

    # Range check at runtime.
    assert 1 <= month <= 12
    assert 1 <= day <= 30 # Lunar months only contain 29 or 30 days.

    self._year = year
    self._month = month
    self._day = day
    self._is_leap_month = is_leap_month
    self._year_ganzhi = year_ganzhi

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
  def is_leap_month(self) -> bool:
    return self._is_leap_month

  @property
  def year_ganzhi(self) -> Ganzhi:
    return self._year_ganzhi

  def __eq__(self, other: object) -> bool:
    if not isinstance(other, LunarDate):
      return False
    if self.year != other.year or self.month != other.month or self.day != other.day:
      return False
    if self.is_leap_month != other.is_leap_month:
      return False
    if self.year_ganzhi != other.year_ganzhi:
      return False
    return True
  
  def __ne__(self, other: object) -> bool:
    return not self.__eq__(other)


class GanzhiDate:
  '''
  GanzhiDate represents a date in the ganzhi calendar.
  '''
  def __init__(self, year: int, month: int, day: int, year_ganzhi: Ganzhi, month_ganzhi: Ganzhi, day_ganzhi: Ganzhi) -> None:
    # Type check at runtime.
    assert isinstance(year, int)
    assert isinstance(month, int)
    assert isinstance(day, int)
    assert isinstance(year_ganzhi, Ganzhi)
    assert isinstance(month_ganzhi, Ganzhi)
    assert isinstance(day_ganzhi, Ganzhi)

    # Range check at runtime.
    assert 1 <= month <= 12
    # assert 1 <= day <= 30 # TODO: Range check on the `day`?

    self._year = year
    self._month = month
    self._day = day
    self._year_ganzhi = year_ganzhi
    self._month_ganzhi = month_ganzhi
    self._day_ganzhi = day_ganzhi

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
  def year_ganzhi(self) -> Ganzhi:
    return self._year_ganzhi

  @property
  def month_ganzhi(self) -> Ganzhi:
    return self._month_ganzhi

  @property
  def day_ganzhi(self) -> Ganzhi:
    return self._day_ganzhi

  def __eq__(self, other: object) -> bool:
    if not isinstance(other, GanzhiDate):
      return False
    if self.year != other.year or self.month != other.month or self.day != other.day:
      return False
    if self.year_ganzhi != other.year_ganzhi:
      return False
    if self.month_ganzhi != other.month_ganzhi:
      return False
    if self.day_ganzhi != other.day_ganzhi:
      return False
    return True
  
  def __ne__(self, other: object) -> bool:
    return not self.__eq__(other)


class CalendarUtils:
  # Create two databases as class variables, where we can query the Jieqi and Lunar year info.
  jieqi_dates_db: DecodedJieqiDates = DecodedJieqiDates()
  lunar_years_db: DecodedLunarYears = DecodedLunarYears()

  # Store the sexagenary cycle as a class variable.
  sexagenary_cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()

  def __init__(self) -> None:
    raise NotImplementedError('Please use static methods.')
  
  @staticmethod
  def lunar_to_solar(lunar_date: LunarDate) -> SolarDate:
    assert isinstance(lunar_date, LunarDate)
    assert lunar_date.year in CalendarUtils.lunar_years_db.supported_year_range(), f'Year {lunar_date.year} is not supported.'
    info: LunarYearInfo = CalendarUtils.lunar_years_db.get(lunar_date.year)

    # Sanity check.
    if lunar_date.is_leap_month:
      assert info['leap']
      assert info['leap_month'] == lunar_date.month
      assert len(info['days_counts']) == 13
    
    raise NotImplementedError('Please use static methods.')
  