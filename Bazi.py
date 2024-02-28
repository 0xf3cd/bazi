# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
from enum import Enum
from datetime import date
from bazi import CalendarDate, CalendarUtils


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


class Bazi:
  '''
  Bazi (八字) is not aware of the timezone. We don't care abot the timezone when creating a Bazi object.
  Timezone should be well-processed outside of this class.

  ATTENTION: this class does not know anything about timezone. 
  '''
  def __init__(self, d: date | CalendarDate, hour: int, gender: BaziGender) -> None:
    '''
    Input the birth time. We don't care about the timezone.
    
    Args:
    - d: (date | CalendarDate) The birth date.
      - If `d` is of `date` type, it will be interpreted as a solar date.
      - Otherwise, it will be converted to `CalendarDate` with `SOLAR` type.
    - hour: (int) The hour of the birth time.
    - gender: (BaziGender) The gender of the person.
    '''

    self._solar_date: CalendarDate = CalendarUtils.to_solar(d)
    assert CalendarUtils.is_valid_solar_date(self._solar_date)

    assert isinstance(hour, int)
    assert hour >= 0 and hour < 24
    self._hour: int = hour

    assert isinstance(gender, BaziGender)
    self._gender: BaziGender = gender

  @property
  def solar_date(self) -> CalendarDate:
    return copy.deepcopy(self._solar_date)

  @property
  def hour(self) -> int:
    return self._hour
  
  @property
  def gender(self) -> BaziGender:
    return self._gender
  
八字 = Bazi
