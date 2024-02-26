# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from enum import Enum
from datetime import datetime

# Expect to support these features in Calendar class.
# - Conversions between Solar, Lunar, and Agricultural times
# - Chinese Jieqi queries
# - True Solar time based on latitude and longitude

class CalendarType(Enum):
  '''
  CallendarType is an enum class. It contains 3 types of calendars.
  '''

  '''
  0: GREGORIAN / 公历
     - New years start on the first days of each year (Jan 1).
     - GREGORIAN is a solar calendar.
     - 公历新年在每年一月一号。
     - 公历是一种太阳历。
  '''
  GREGORIAN = 0
  公历 = GREGORIAN

  '''
  1: XIALI / 夏历
     - New years start on the first days on Zhengyues.
     - XIALI is a lunisolar calendar.
     - 夏历新年在每年正月初一。夏历每个月的划定基于对月亮的观测。夏历存在闰月。
     - 夏历是一种阴阳历。
  '''
  XIALI = 1
  夏历 = XIALI

  '''
  2: GANZHILI / 干支历
     - New years start on the days of Start of Spring (立春).
     - When generating Bazi (八字) for a person, we use 24 Chinese Jieqis (24 solar terms / 24 节气) to determine the starts of new years and months.
     - BAZI is a solar calendar, as 24 Chinese Jieqis are based on the observations of the Sun.
     - 干支历新年在每年立春。干支历不存在闰月。
     - 当进行八字排盘时，人们以 24 节气中的 12 节来划分年、月。
       - 每一年的开始在于立春。每一年也叫“岁”（每一“岁”为立春到下一个立春前一天）
       - 每一个月的开始在于交节日（从立春开始，每两个节气为一个月，如立春、惊蛰、清明、立夏...）。
     - 干支历是一种太阳历，因为 24 节气基于太阳观测。
  '''
  GANZHILI = 2
  干支历 = GANZHILI


class Date:
  def __init__(self, dt: datetime) -> None:
    pass


class Calendar:
  def __init__(self) -> None:
    raise NotImplementedError('Please use static methods.')
  
  @staticmethod
  def now() -> Date:
    now = datetime.now()
    return Date(now)

  @staticmethod
  def from_datetime(dt: datetime, calendar_type: CalendarType) -> Date:
    return Date(dt)  

  @staticmethod
  def from_ymd(
    year: int, month: int, day: int, calendar_type: CalendarType, 
    *, hour: int = 0, minute: int = 0, second: int = 0, microsecond: int = 0
  ) -> Date:
    return Date(datetime(year, month, day, hour, minute, second, microsecond))
  