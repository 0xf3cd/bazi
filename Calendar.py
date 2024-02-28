# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import calendar
from enum import Enum
from datetime import date, timedelta

from bazi import Ganzhi, Jieqi
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


class CalendarUtils:
  def __init__(self) -> None:
    raise NotImplementedError('Please use static methods.')
  
  # Create two databases as class variables, where we can query the Jieqi and Lunar year info.
  jieqi_dates_db: DecodedJieqiDates = DecodedJieqiDates()
  lunar_years_db: DecodedLunarYears = DecodedLunarYears()

  # Store the sexagenary cycle as a class variable.
  sexagenary_cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()

  @staticmethod
  def get_min_supported_date(date_type: CalendarType) -> CalendarDate:
    # TODO: This is hardcoded. Change it?
    # 1901-02-19 is the first day (in solar) in lunar year 1901.
    if date_type == CalendarType.SOLAR:
      return CalendarDate(1901, 2, 19, CalendarType.SOLAR)
    elif date_type == CalendarType.LUNAR:
      return CalendarDate(1901, 1, 1, CalendarType.LUNAR)
    else:
      assert date_type == CalendarType.GANZHI
      return CalendarDate(1901, 1, 16, CalendarType.GANZHI)
    
  @staticmethod
  def get_max_supported_date(date_type: CalendarType) -> CalendarDate:
    # TODO: This is hardcoded. Change it?
    # Because of the validity check in `is_valid_ganzhi_date`, we can only support 2099-12-30 (in ganzhi calendar).
    # 2099-12-30 is also the last day (in ganzhi calendar) in ganzhi year 2099.
    if date_type == CalendarType.SOLAR:
      return CalendarDate(2100, 2, 3, CalendarType.SOLAR)
    elif date_type == CalendarType.LUNAR:
      return CalendarDate(2099, 13, 25, CalendarType.LUNAR) # 2099 is a leap year on lunar calendar.
    else:
      assert date_type == CalendarType.GANZHI
      return CalendarDate(2099, 12, 30, CalendarType.GANZHI)
  
  @staticmethod
  def is_valid_solar_date(d: CalendarDate) -> bool:
    '''
    Check if the input date is valid.
    Will also check if the date is in the supported range. If not, return False.

    Args: 
      - d: CalendarDate object, expected to be of `CalendarType.SOLAR`.

    Return: True if valid, False otherwise.
    '''

    if d.date_type != CalendarType.SOLAR:
      return False
    if d < CalendarUtils.get_min_supported_date(CalendarType.SOLAR):
      return False
    if d > CalendarUtils.get_max_supported_date(CalendarType.SOLAR):
      return False

    if d.year <= 0:
      return False # pragma: no cover # Already returning False in above "< min_supported_date" check.
    if d.month < 1 or d.month > 12:
      return False
    
    if d.month in [1, 3, 5, 7, 8, 10, 12]:
      if d.day < 1 or d.day > 31:
        return False
    elif d.month in [4, 6, 9, 11]:
      if d.day < 1 or d.day > 30:
        return False
    else:
      assert d.month == 2
      if calendar.isleap(d.year):
        if d.day < 1 or d.day > 29:
          return False
      else:
        if d.day < 1 or d.day > 28:
          return False

    return True

  @staticmethod
  def is_valid_lunar_date(d: CalendarDate) -> bool:
    '''
    Check if the input date is valid.
    Will also check if the date is in the supported range. If not, return False.

    Args: 
      - d: CalendarDate object, expected to be of `CalendarType.LUNAR`.

    Return: True if valid, False otherwise.
    '''

    if d.date_type != CalendarType.LUNAR:
      return False
    if d < CalendarUtils.get_min_supported_date(CalendarType.LUNAR):
      return False
    if d > CalendarUtils.get_max_supported_date(CalendarType.LUNAR):
      return False
    
    info: LunarYearInfo = CalendarUtils.lunar_years_db.get(d.year)
    
    if d.year <= 0:
      return False # pragma: no cover # Already returning False in above "< min_supported_date" check.
    if d.month < 1 or d.month > len(info['days_counts']):
      return False 
    if d.day < 1 or d.day > 30:
      return False
    
    days_in_month: int = info['days_counts'][d.month - 1]
    if d.day > days_in_month:
      return False

    return True
  
  @staticmethod
  def is_valid_ganzhi_date(d: CalendarDate) -> bool:
    '''
    Check if the input date is valid.
    Will also check if the date is in the supported range. If not, return False.

    Args: 
      - d: CalendarDate object, expected to be of `CalendarType.GANZHI`.

    Return: True if valid, False otherwise.
    '''

    if d.date_type != CalendarType.GANZHI:
      return False
    if d < CalendarUtils.get_min_supported_date(CalendarType.GANZHI):
      return False
    if d > CalendarUtils.get_max_supported_date(CalendarType.GANZHI):
      return False
    
    if d.year <= 0:
      return False # pragma: no cover # Already returning False in above "< min_supported_date" check.
    if d.month < 1 or d.month > 12:
      return False 
    if d.day < 1 or d.day > 32: # Max gap between Ganzhi months is 32 days.
      return False
    
    days_counts: list[int] = CalendarUtils.days_counts_in_ganzhi_year(d.year)
    if d.day > days_counts[d.month - 1]:
      return False

    return True

  @staticmethod
  def is_valid(d: CalendarDate) -> bool:
    if d.date_type not in [CalendarType.SOLAR, CalendarType.LUNAR, CalendarType.GANZHI]:
      return False

    if d.date_type == CalendarType.SOLAR:
      return CalendarUtils.is_valid_solar_date(d)
    elif d.date_type == CalendarType.LUNAR:
      return CalendarUtils.is_valid_lunar_date(d)
    else:
      assert d.date_type == CalendarType.GANZHI
      return CalendarUtils.is_valid_ganzhi_date(d)

  @staticmethod
  def days_counts_in_ganzhi_year(ganzhi_year: int) -> list[int]:
    assert ganzhi_year <= CalendarUtils.get_max_supported_date(CalendarType.GANZHI).year

    jieqi_list: list[Jieqi] = Jieqi.as_list()[::2] # Pick the Jieqis when new months start.
    assert jieqi_list[0] == Jieqi.立春 # The first jieqi in every year should be 立春.
    assert len(jieqi_list) == 12

    start_dates: list[date] = []
    for jq in jieqi_list[:11]: # First 11 jieqis are in solar year `ganzhi_year`.
      start_dates.append(CalendarUtils.jieqi_dates_db.get(ganzhi_year, jq))
    for jq in jieqi_list[11:]: # Last 1 jieqis are in solar year `ganzhi_year + 1`.
      start_dates.append(CalendarUtils.jieqi_dates_db.get(ganzhi_year + 1, jq))
    
    end_dates: list[date] = start_dates[1:] + [CalendarUtils.jieqi_dates_db.get(ganzhi_year + 1, Jieqi.立春)]
    days_counts: list[int] = [(end - start).days for start, end in zip(start_dates, end_dates)]
    assert len(days_counts) == 12

    return days_counts
  
  @staticmethod
  def lunar_to_solar(lunar_date: CalendarDate) -> CalendarDate:
    assert CalendarUtils.is_valid_lunar_date(lunar_date)
    info: LunarYearInfo = CalendarUtils.lunar_years_db.get(lunar_date.year)

    passed_days_count: int = -1
    for month_idx in range(lunar_date.month - 1):
      passed_days_count += info['days_counts'][month_idx]
    passed_days_count += lunar_date.day

    first_solar_date: date = info['first_solar_day']
    cur_solar_date: date = first_solar_date + timedelta(days=passed_days_count)
    return CalendarDate(cur_solar_date.year, cur_solar_date.month, cur_solar_date.day, CalendarType.SOLAR)