# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
from enum import Enum
from datetime import date, datetime, timedelta
from typing import (
  Type, Sequence, Iterator, Generic, TypeVar, Final,
)

from .Defines import Jieqi, Tiangan, Dizhi, Ganzhi
from .Calendar import CalendarDate, HkoDataCalendarUtils
from .Utils import BaziUtils


class BaziGender(Enum):
  '''
  BaziGender is used to specify the gender of the person.
  '''
  YANG = '男'
  YIN = '女'

  # Aliases
  MALE = YANG
  FEMALE = YIN

  男 = YANG
  女 = YIN

  阳 = YANG
  阴 = YIN

  乾 = YANG
  坤 = YIN

  def __str__(self) -> str:
    return str(self.value)


class BaziPrecision(Enum):
  '''
  BaziPrecision is used to specify the precision when generating the Bazi chart.

  As per the rules of Bazi system, new years start on the days of Start of Spring (LICHUN / 立春), and new months start
  on the days of 12 Jieqis (LICHUN, JINGZHE, QINGMING, LIXIA... / 立春, 惊蛰, 清明, 立夏...).

  So, even born on the same day, two persons can have different Year Ganzhi (年柱) and Month Ganzhi (月柱).

  There are 3 levels of precision: DAY, HOUR, and MINUTE. 
  Different levels apply different rules to determine the starts of years and months. 
  That is to say, even the same birth time can have different Year Ganzhis and Month Ganzhis on 3 different levels.

  For example, say the day of LICHUN / 立春 in 2000 is 2000-02-04 (in solar / gregorian calendar), and the exact time is 8:35 PM.
  - DAY:
    - People born on 2000-02-03 will have "己卯" as the Year Ganzhi, and Month Dizhi is "丑".
    - However, people born on 2000-02-04 will have "庚辰" as the Year Ganzhi, and Month Dizhi is "寅".
      - This means even people born before 8:35 PM on 2000-02-04 will be falling into "庚辰" and "寅".
  - HOUR:
    - People born in range [2000-02-04 12:00 AM (i.e. 00:00), 2000-02-04 7:59 PM (i.e. 19:59)] will have "己卯" as the Year Ganzhi, and Month Dizhi is "丑".
    - People born in range [2000-02-04 8:00 PM (i.e. 20:00), 2000-02-04 11:59 PM (i.e. 23:59)] will have "庚辰" as the Year Ganzhi, and Month Dizhi is "寅".
  - MINUTE:
    - People born in range [2000-02-04 12:00 AM (i.e. 00:00), 2000-02-04 8:34 PM (i.e. 20:34)] will have "己卯" as the Year Ganzhi, and Month Dizhi is "丑".
    - People born in range [2000-02-04 8:35 PM (i.e. 20:35), 2000-02-04 11:59 PM (i.e. 23:59)] will have "庚辰" as the Year Ganzhi, and Month Dizhi is "寅".
  '''
  DAY    = 0
  HOUR   = 1
  MINUTE = 2

T = TypeVar('T')
class BaziData(Generic[T]):
  '''
  A generic class for storing Bazi data.
  T is the type of the data. And a `BaziData` object stores 4 T objects for year, month, day, and hour.
  '''
  def __init__(self, generic_type: Type[T], data: Sequence[T]) -> None:
    self._type: Type[T] = generic_type
    
    assert len(data) == 4
    self._year: Final[T] = copy.deepcopy(data[0])
    self._month: Final[T] = copy.deepcopy(data[1])
    self._day: Final[T] = copy.deepcopy(data[2])
    self._hour: Final[T] = copy.deepcopy(data[3])

  @property
  def year(self) -> T:
    return copy.deepcopy(self._year)

  @property
  def month(self) -> T:
    return copy.deepcopy(self._month)

  @property
  def day(self) -> T:
    return copy.deepcopy(self._day)

  @property
  def hour(self) -> T:
    return copy.deepcopy(self._hour)
  
  def __iter__(self) -> Iterator[T]:
    return iter((self._year, self._month, self._day, self._hour))


class Bazi:
  '''
  Bazi (八字) is not aware of the timezone. We don't care abot the timezone when creating a Bazi object.
  Timezone should be well-processed outside of this class.

  ATTENTION: this class does not know anything about timezone. 
  '''

  def __init__(self, birth_time: datetime, gender: BaziGender, precision: BaziPrecision) -> None:
    '''
    Input the birth time. We don't care about the timezone.
    
    Args:
    - birth_time: (datetime) The birth date (in Georgian calendar) and time. Note that no timezone should be set.
    - gender: (BaziGender) The gender of the person.
    - precision: (BaziPrecision) The precision of the birth time.
    '''

    assert isinstance(birth_time, datetime)
    self._birth_time: Final[datetime] = copy.deepcopy(birth_time)
    assert self._birth_time.tzinfo is None, 'Timezone should be well-processed outside of this class.'

    self._solar_birth_date: Final[CalendarDate] = HkoDataCalendarUtils.to_solar(self._birth_time)
    assert HkoDataCalendarUtils.is_valid_solar_date(self._solar_birth_date) # Here we are also checking if the date falls into the supported range.

    self._hour: Final[int] = self._birth_time.hour
    assert self._hour >= 0 and self._hour < 24

    self._minute: Final[int] = self._birth_time.minute
    assert self._minute >= 0 and self._minute < 60

    assert isinstance(gender, BaziGender)
    self._gender: Final[BaziGender] = copy.deepcopy(gender)

    assert isinstance(precision, BaziPrecision)
    self._precision: Final[BaziPrecision] = copy.deepcopy(precision)

    # Generate ganzhi-related info.
    # TODO: Currently only supports `DAY` precision.
    assert self._precision == BaziPrecision.DAY, 'see https://github.com/0xf3cd/bazi/issues/6'

    ganzhi_calendardate: CalendarDate = HkoDataCalendarUtils.to_ganzhi(self._solar_birth_date)

    # Figure out the solar date falls into which ganzhi year.
    # Also figure out the Year Ganzhi / Year Pillar (年柱).
    solar_year: int = self._solar_birth_date.year
    lichun_date: date = BaziUtils.get_jieqi_date_in_solar_year(solar_year, Jieqi.立春)
    self._ganzhi_year: Final[int] = solar_year if HkoDataCalendarUtils.to_date(self._solar_birth_date) >= lichun_date else solar_year - 1
    self._year_pillar: Final[Ganzhi] = BaziUtils.get_ganzhi_year_ganzhi(self._ganzhi_year)

    # Figure out the ganzhi month. Also find out the Month Dizhi (月令).
    self._ganzhi_month: Final[int] = ganzhi_calendardate.month # `ganzhi_calendardate` is already at `DAY`-level precision.
    assert 1 <= self._ganzhi_month <= 12
    self._month_dizhi: Final[Dizhi] = Dizhi.from_index((2 + self._ganzhi_month - 1) % 12)

    # Figure out the ganzhi day, as well as the Day Ganzhi / Day Pillar (日柱).
    day_offset: int = 0 if self._birth_time.hour < 23 else 1
    self._day_pillar: Final[Ganzhi] = BaziUtils.get_day_ganzhi(timedelta(days=day_offset) + self._birth_time)

    # Finally, find out the Hour Dizhi (时柱地支).
    self._hour_dizhi: Final[Dizhi] = Dizhi.from_index(int((self._hour + 1) / 2) % 12)

  @property
  def solar_birth_date(self) -> date:
    return HkoDataCalendarUtils.to_date(self._solar_birth_date)

  @property
  def hour(self) -> int:
    return self._hour
  
  @property
  def minute(self) -> int:
    return self._minute
  
  @property
  def gender(self) -> BaziGender:
    return self._gender
  
  @property
  def precision(self) -> BaziPrecision:
    return self._precision
  
  @property
  def four_dizhis(self) -> tuple[Dizhi, Dizhi, Dizhi, Dizhi]:
    '''
    Return the 4 Dizhis of Year, Month, Day, and Hour pillars (in that order!).
    返回年、月、日、时的地支。
    '''
    return (self._year_pillar.dizhi, self._month_dizhi, 
            self._day_pillar.dizhi, self._hour_dizhi,)
  
  @property
  def four_tiangans(self) -> tuple[Tiangan, Tiangan, Tiangan, Tiangan]:
    '''
    Return the 4 Tiangans of Year, Month, Day, and Hour pillars (in that order!).
    返回年、月、日、时的天干。
    '''
    return (self._year_pillar.tiangan, BaziUtils.find_month_tiangan(self._year_pillar.tiangan, self._month_dizhi), 
            self._day_pillar.tiangan, BaziUtils.find_hour_tiangan(self._day_pillar.tiangan, self._hour_dizhi))
  
  @property
  def day_master(self) -> Tiangan:
    '''
    Day Master is the Tiangan of the Day Pillar (日主).
    '''
    return self._day_pillar.tiangan

  @property
  def month_commander(self) -> Dizhi:
    '''
    Month Commander is the Dizhi of the Month Pillar (月令 / 月柱地支).
    '''
    return self._month_dizhi

  @property
  def year_pillar(self) -> Ganzhi:
    '''
    Year Pillar is the Ganzhi of the Year (年柱).
    '''
    return self._year_pillar
  
  @property
  def month_pillar(self) -> Ganzhi:
    '''
    Month Pillar is the Ganzhi of the Month (月柱).
    '''
    month_tiangan: Tiangan = BaziUtils.find_month_tiangan(self._year_pillar.tiangan, self._month_dizhi)
    return Ganzhi(month_tiangan, self._month_dizhi)
  
  @property
  def day_pillar(self) -> Ganzhi:
    '''
    Day Pillar is the Ganzhi of the Day (日柱).
    '''
    return self._day_pillar
  
  @property
  def hour_pillar(self) -> Ganzhi:
    '''
    Hour Pillar is the Ganzhi of the Hour (时柱).
    '''
    hour_tiangan: Tiangan = BaziUtils.find_hour_tiangan(self._day_pillar.tiangan, self._hour_dizhi)
    return Ganzhi(hour_tiangan, self._hour_dizhi)
  
  @property
  def pillars(self) -> BaziData[Ganzhi]:
    '''
    Return the 4 Ganzhis (i.e. pillars) of Year, Month, Day, and Hour.
    返回年、月、日、时的天干地支（即返回八字）。
    '''
    pillars: list[Ganzhi] = [Ganzhi(tg, dz) for tg, dz in zip(self.four_tiangans, self.four_dizhis)]
    return BaziData(Ganzhi, pillars)

八字 = Bazi
