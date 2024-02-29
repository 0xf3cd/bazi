# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
from enum import Enum
from datetime import date, datetime
from typing import TypedDict, Unpack

from bazi import (
  CalendarDate, CalendarUtils, Jieqi, Tiangan, Dizhi, Ganzhi, hkodata
)


class BaziGender(Enum):
  '''
  BaziGender is used to specify the gender of the person.
  '''
  YANG = 0
  YIN = 1

  # Aliases
  MALE = YANG
  FEMALE = YIN

  男 = YANG
  女 = YIN

  阳 = YANG
  阴 = YIN

  乾 = YANG
  坤 = YIN


class BaziPrecision(Enum):
  '''
  BaziPrecision is used to specify the precision when generating the Bazi natal chart.

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


class BaziArgs(TypedDict):
  birth_time: datetime
  gender:     BaziGender
  precision:  BaziPrecision

class Bazi:
  '''
  Bazi (八字) is not aware of the timezone. We don't care abot the timezone when creating a Bazi object.
  Timezone should be well-processed outside of this class.

  ATTENTION: this class does not know anything about timezone. 
  '''

  # Save the Jieqi data as a class variable.
  __jieqi_db: hkodata.DecodedJieqiDates = hkodata.DecodedJieqiDates()

  def __init__(self, **kwargs: Unpack[BaziArgs]) -> None:
    '''
    Input the birth time. We don't care about the timezone.
    
    Args:
    - kwargs: (BaziArgs) The dictionary containing the following information:
      - birth_time: (datetime) The birth date. Note that no timezone should be set.
        - If `d` is of `date` type, it will be interpreted as a solar date.
        - Otherwise, it will be converted to `CalendarDate` with `SOLAR` type.
      - gender: (BaziGender) The gender of the person.
      - precision: (BaziPrecision) The precision of the birth time.
    '''

    assert 'birth_time' in kwargs
    assert isinstance(kwargs['birth_time'], datetime)
    self._birth_time: datetime = copy.deepcopy(kwargs['birth_time'])
    assert self._birth_time.tzinfo is None, 'Timezone should be well-processed outside of this class.'

    self._solar_birth_date: CalendarDate = CalendarUtils.to_solar(self._birth_time)
    assert CalendarUtils.is_valid_solar_date(self._solar_birth_date) # Here we are also checking if the date falls into the supported range.

    self._hour: int = self._birth_time.hour
    assert self._hour >= 0 and self._hour < 24

    self._minute: int = self._birth_time.minute
    assert self._minute >= 0 and self._minute < 60

    assert 'gender' in kwargs
    assert isinstance(kwargs['gender'], BaziGender)
    self._gender: BaziGender = copy.deepcopy(kwargs['gender'])

    assert 'precision' in kwargs
    assert isinstance(kwargs['precision'], BaziPrecision)
    self._precision: BaziPrecision = copy.deepcopy(kwargs['precision'])

    self.__gen_ganzhi_info() # Generate ganzhi-related info.

  def __gen_ganzhi_info(self) -> None:
    # TODO: Currently only supports `DAY` precision.
    assert self._precision == BaziPrecision.DAY, 'see https://github.com/0xf3cd/bazi/issues/6'

    ganzhi_calendardate: CalendarDate = CalendarUtils.to_ganzhi(self._solar_birth_date)

    if self._precision == BaziPrecision.DAY:
      # Figure out the solar date falls into which ganzhi year.
      solar_year: int = self._solar_birth_date.year
      lichun_date: date = self.__jieqi_db.get(solar_year, Jieqi.立夏)
      self._ganzhi_year: int = solar_year if self._solar_birth_date.to_date() >= lichun_date else solar_year - 1

      # Figure out the ganzhi month.
      self._ganzhi_month: int = ganzhi_calendardate.month # `ganzhi_calendardate` is already at `DAY`-level precision.

  @property
  def solar_birth_date(self) -> date:
    return self._solar_birth_date.to_date()

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
  
八字 = Bazi
