# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import random

from enum import Enum
from datetime import date, time, datetime, timedelta
from typing import Final, Union

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
    if self is self.MALE:
      return 'male'
    else:
      assert self is self.FEMALE
      return 'female'



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

  def __str__(self) -> str:
    if self is self.DAY:
      return 'day'
    elif self is self.HOUR:
      return 'hour'
    else:
      assert self is self.MINUTE
      return 'minute'


class Bazi:
  '''
  `Bazi` (八字) is the class that only stores very basic information.
  A `Bazi` object stores 4 pillars of year, month, day, and hour.
  For all other information (transits / shishen / ...), please see `src/Charts` (e.g. `BaziChart`).

  八字是仅存储基本信息的类。一个 `Bazi` 对象存储着年、月、日、时的四柱八个字。
  对于其他信息（流年大运 / 十神等），请参阅 `src/Charts`（例如 `BaziChart`）。

  Note:
  - We don't care about the timezone. `Bazi` knows nothing about timezone.
  - We don't care about the true solar time / daylight saving time - it should be well-processed outside of this class.
  - `Bazi` 不考虑时差。时差需要在外部处理。
  - `Bazi` 不考虑真太阳时和夏令时。这些时间需要在外部处理。
  '''

  def __init__(self, birth_time: datetime, gender: BaziGender, precision: BaziPrecision) -> None:
    '''
    `Bazi` (i.e. 八字, which means eight characters in Chinese) takes the birt time and gender as input, 
    and figures out the pillars of year, month, day, and hour.
    `Bazi` 接受出生时间和性别作为输入，计算年、月、日、时的八字。
    
    Note:
    - We don't care about the timezone. `Bazi` knows nothing about timezone.
    - We don't care about the true solar time / daylight saving time - it should be well-processed outside of this class.
    - `Bazi` 不考虑时差。时差需要在外部处理。
    - `Bazi` 不考虑真太阳时和夏令时。这些时间需要在外部处理。
    
    Args:
    - birth_time: (datetime) The birth date (in Georgian calendar) and time. Note that no timezone should be set.
    - gender: (BaziGender) The gender of the person.
    - precision: (BaziPrecision) The precision of the birth time.
    '''

    assert isinstance(birth_time, datetime)
    self._birth_time: Final[datetime] = copy.deepcopy(birth_time)
    assert self._birth_time.tzinfo is None, 'Timezone should be well-processed outside of this class.'

    self._solar_date: Final[CalendarDate] = HkoDataCalendarUtils.to_solar(self._birth_time)
    assert HkoDataCalendarUtils.is_valid_solar_date(self._solar_date) # Here we are also checking if the date falls into the supported range.

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

    ganzhi_calendardate: CalendarDate = HkoDataCalendarUtils.to_ganzhi(self._solar_date)

    # Figure out the solar date falls into which ganzhi year.
    # Also figure out the Year Ganzhi / Year Pillar (年柱).
    solar_year: int = self._solar_date.year
    lichun_date: date = HkoDataCalendarUtils.query_jieqi_date(solar_year, Jieqi.立春)
    self._ganzhi_year: Final[int] = solar_year if HkoDataCalendarUtils.to_date(self._solar_date) >= lichun_date else solar_year - 1
    self._year_pillar: Final[Ganzhi] = BaziUtils.ganzhi_of_year(self._ganzhi_year)

    # Figure out the ganzhi month. Also find out the Month Dizhi (月令).
    self._ganzhi_month: Final[int] = ganzhi_calendardate.month # `ganzhi_calendardate` is already at `DAY`-level precision.
    assert 1 <= self._ganzhi_month <= 12
    self._month_dizhi: Final[Dizhi] = Dizhi.from_index((2 + self._ganzhi_month - 1) % 12)

    # Figure out the ganzhi day, as well as the Day Ganzhi / Day Pillar (日柱).
    day_offset: int = 0 if self._birth_time.hour < 23 else 1
    self._day_pillar: Final[Ganzhi] = BaziUtils.ganzhi_of_day(timedelta(days=day_offset) + self._birth_time)

    # Finally, find out the Hour Dizhi (时柱地支).
    self._hour_dizhi: Final[Dizhi] = Dizhi.from_index(int((self._hour + 1) / 2) % 12)

  @staticmethod
  def __parse_bazi_args(
    birth_time: Union[datetime, str],
    gender: Union[BaziGender, str], 
    precision: Union[BaziPrecision, str]
  ) -> tuple[datetime, BaziGender, BaziPrecision]:
    
    assert isinstance(birth_time, (datetime, str))
    _birth_time: datetime = birth_time if isinstance(birth_time, datetime) else datetime.fromisoformat(birth_time)

    assert _birth_time.tzinfo is None, 'Timezone should be well-processed outside of this class.'

    _gender: BaziGender
    if isinstance(gender, BaziGender):
      _gender = gender
    else:
      assert isinstance(gender, str)
      if gender.lower() in ['男', 'male']:
        _gender = BaziGender.MALE
      elif gender.lower() in ['女', 'female']:
        _gender = BaziGender.FEMALE
      else:
        raise ValueError(f'Currently not support gender: {gender}')

    _precision: BaziPrecision
    if isinstance(precision, BaziPrecision):
      _precision = precision
    else:
      assert isinstance(precision, str)
      if precision.lower() in ['分', '分钟', 'm', 'min', 'minute']:
        _precision = BaziPrecision.MINUTE
      elif precision.lower() in ['时', '小时', 'h', 'hour']:
        _precision = BaziPrecision.HOUR
      elif precision.lower() in ['天', '日', 'd', 'day']:
        _precision = BaziPrecision.DAY
      else:
        raise ValueError(f'Unsupported precision: {precision}')
      
    return _birth_time, _gender, _precision

  @staticmethod
  def create(
    birth_time: Union[datetime, str],
    gender: Union[BaziGender, str], 
    precision: Union[BaziPrecision, str]
  ) -> 'Bazi':
    '''
    Staticmethod that creates a `Bazi` object from the inputs.

    Args:
    - birth_time: (Union[datetime, str]) The birth date. Note that no timezone should be set.
      - if `datetime` type: it will be interpreted as a solar date to feed to `Bazi`.
      - if `str` type: it will be converted by `datetime.fromisoformat`.
    - gender: (Union[BaziGender, str]) The gender of the person.
      - if `BaziGender` type: it will be directly fed to `Bazi`.
      - if `str` type: it will be converted by `BaziGender`. 
        - Supported values: "男"/"女"/"male"/"female" (case insensitive).
    - precision: (Union[BaziPrecision, str]) The precision of the birth time.
      - if `BaziPrecision` type: it will be directly fed to `Bazi`.
      - if `str` type: it will be converted by `BaziPrecision`. 
        - Supported values: "分"/"分钟"/"时"/"小时"/"天"/"日"/"m"/"min"/"minute"/"h"/"hour"/"d"/"day" (case insensitive).
    '''

    assert isinstance(birth_time, (datetime, str))
    assert isinstance(gender, (BaziGender, str))
    assert isinstance(precision, (BaziPrecision, str))

    _birth_time, _gender, _precision = Bazi.__parse_bazi_args(birth_time, gender, precision)
    bazi: Bazi = Bazi(
      birth_time=_birth_time,
      gender=_gender,
      precision=_precision,
    )
    return bazi
  
  @staticmethod
  def random() -> 'Bazi':
    '''
    Classmethod that creates a random `Bazi` object. Mainly for testing purpose.

    Note that the precision is currently set to `BaziPrecision.DAY`.
    Note that the year is in [1902, 2098], and day is in [1, 28].
    '''
    return Bazi.create(
      birth_time=datetime(
        year=random.randint(1902, 2098),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
      ),
      gender=random.choice(list(BaziGender)),
      precision=BaziPrecision.DAY,
    )

  @property
  def solar_date(self) -> date:
    return HkoDataCalendarUtils.to_date(self._solar_date)

  @property
  def hour(self) -> int:
    return self._hour
  
  @property
  def minute(self) -> int:
    return self._minute
  
  @property
  def solar_datetime(self) -> datetime:
    return datetime.combine(self.solar_date, time(self.hour, self.minute))
  
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
    return (self._year_pillar.tiangan, BaziUtils.month_tiangan(self._year_pillar.tiangan, self._month_dizhi), 
            self._day_pillar.tiangan, BaziUtils.hour_tiangan(self._day_pillar.tiangan, self._hour_dizhi))
  
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
    month_tiangan: Tiangan = BaziUtils.month_tiangan(self._year_pillar.tiangan, self._month_dizhi)
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
    hour_tiangan: Tiangan = BaziUtils.hour_tiangan(self._day_pillar.tiangan, self._hour_dizhi)
    return Ganzhi(hour_tiangan, self._hour_dizhi)
  
  @property
  def pillars(self) -> tuple[Ganzhi, Ganzhi, Ganzhi, Ganzhi]:
    '''
    Return the 4 Ganzhis (i.e. pillars) of Year, Month, Day, and Hour.
    返回年、月、日、时的天干地支（即返回八字）。
    '''
    tgs: tuple[Tiangan, Tiangan, Tiangan, Tiangan] = self.four_tiangans
    dzs: tuple[Dizhi, Dizhi, Dizhi, Dizhi] = self.four_dizhis
    return (
      Ganzhi(tgs[0], dzs[0]),
      Ganzhi(tgs[1], dzs[1]),
      Ganzhi(tgs[2], dzs[2]),
      Ganzhi(tgs[3], dzs[3]),
    )
  
  def __eq__(self, other: object) -> bool:
    if not isinstance(other, Bazi):
      return False
    if self.solar_datetime != other.solar_datetime:
      return False
    if self.gender != other.gender:
      return False
    if self.precision != other.precision:
      return False
    return True
  
  def __ne__(self, other: object) -> bool:
    return not self.__eq__(other)

八字 = Bazi
