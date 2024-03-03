# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
from enum import Enum
from datetime import date, datetime, timedelta
from typing import TypedDict, Unpack, Type, Sequence, Iterator, Optional

from .Rules import TraitTuple, HiddenTianganDict
from .Defines import Jieqi, Tiangan, Dizhi, Ganzhi, Shishen
from .Calendar import CalendarDate, CalendarUtils
from .Utils import BaziUtils
from . import hkodata


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


class BaziData[T]:
  '''
  A generic class for storing Bazi data.
  T is the type of the data. And a `BaziData` object stores 4 T objects for year, month, day, and hour.
  '''
  def __init__(self, generic_type: Type[T], data: Sequence[T]) -> None:
    self._type: Type[T] = generic_type
    
    assert len(data) == 4
    self._year: T = copy.deepcopy(data[0])
    self._month: T = copy.deepcopy(data[1])
    self._day: T = copy.deepcopy(data[2])
    self._hour: T = copy.deepcopy(data[3])

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
  __lunar_db: hkodata.DecodedLunarYears = hkodata.DecodedLunarYears()

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
      # Also figure out the Year Ganzhi / Year Pillar (年柱).
      solar_year: int = self._solar_birth_date.year
      lichun_date: date = self.__jieqi_db.get(solar_year, Jieqi.立春)
      self._ganzhi_year: int = solar_year if self._solar_birth_date.to_date() >= lichun_date else solar_year - 1
      self._year_pillar: Ganzhi = self.__lunar_db.get(self._ganzhi_year)['ganzhi']

      # Figure out the ganzhi month. Also find out the Month Dizhi (月令).
      self._ganzhi_month: int = ganzhi_calendardate.month # `ganzhi_calendardate` is already at `DAY`-level precision.
      assert 1 <= self._ganzhi_month <= 12
      self._month_dizhi: Dizhi = Dizhi.from_index((2 + self._ganzhi_month - 1) % 12)

      # Figure out the ganzhi day, as well as the Day Ganzhi / Day Pillar (日柱).
      day_offset: int = 0 if self._birth_time.hour < 23 else 1
      self._day_pillar: Ganzhi = BaziUtils.get_day_ganzhi(timedelta(days=day_offset) + self._birth_time)

      # Finally, find out the Hour Dizhi (时柱地支).
      self._hour_dizhi: Dizhi = Dizhi.from_index(int((self._hour + 1) / 2) % 12)

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


class BaziChart:
  class PillarData[T, U]:
    '''
    A helper class for storing the data of a Pillar.
    '''
    def __init__(self, tg: T, dz: U) -> None:
      self._tg = copy.deepcopy(tg)
      self._dz = copy.deepcopy(dz)

    @property
    def tiangan(self) -> T:
      return copy.deepcopy(self._tg)
    
    @property
    def dizhi(self) -> U:
      return copy.deepcopy(self._dz)

  def __init__(self, bazi: Bazi) -> None:
    assert isinstance(bazi, Bazi)
    self._bazi: Bazi = copy.deepcopy(bazi)
  
  @classmethod
  def create(cls, birth_time: datetime, gender: BaziGender, precision: BaziPrecision) -> 'BaziChart':
    bazi: Bazi = Bazi(
      birth_time=birth_time,
      gender=gender,
      precision=precision,
    )
    return cls(bazi)
  
  def is_day_master(self, tg: Tiangan) -> bool:
    '''
    Return True if the input Tiangan is the Tiangan of the Day Pillar (i.e. Day Master / 日主).
    '''
    return tg == self.bazi.day_master

  @property
  def bazi(self) -> Bazi:
    return copy.deepcopy(self._bazi)

  PillarTraits = PillarData[TraitTuple, TraitTuple]
  @property
  def traits(self) -> BaziData[PillarTraits]:
    '''
    The traits (i.e. Yinyang and Wuxing) of Tiangans and Dizhis in pillars of Year, Month, Day, and Hour.
    年、月、日、时的天干地支的阴阳和五行。

    Usage:
    ```
    traits = chart.traits
    
    print(traits.year.tiangan) # Print the trait of Year's Tiangan (年柱天干)
    assert traits.hour.dizhi == TraitTuple(Wuxing.木, Yinyang.阳) # Access the trait of Hour's Dizhi (时柱地支)

    for pillar_traits in traits: # Iterate all pillars in the order of "Year, Month, Day, and Hour"
      print(pillar_traits.tiangan) # Print the trait of Tiangan of the Pillar
      print(pillar_traits.dizhi)   # Print the trait of Dizhi of the Pillar
    ```
    '''
    # Get the traits of the four tiangans and four dizhis
    tiangan_traits: list[TraitTuple] = [BaziUtils.get_tiangan_traits(tg) for tg in self._bazi.four_tiangans]
    dizhi_traits: list[TraitTuple] = [BaziUtils.get_dizhi_traits(dz) for dz in self._bazi.four_dizhis]
    pillar_data: list = [BaziChart.PillarTraits(tg_traits, dz_traits) for tg_traits, dz_traits in zip(tiangan_traits, dizhi_traits)]
    return BaziData(BaziChart.PillarTraits, pillar_data)
  
  PillarHiddenTiangans = PillarData[None, HiddenTianganDict]
  @property
  def hidden_tiangans(self) -> BaziData[PillarHiddenTiangans]:
    '''
    The hidden Tiangans in all Dizhis of current bazi.
    当前八字的所有地支中的藏干。

    Usage:
    ```
    hidden = chart.hidden_tiangans

    print(hidden.year.dizhi)  # Print the hidden tiangans of Year
    print(hidden.month.dizhi) # Print the hidden tiangans of Month
    print(hidden.day.dizhi)   # Print the hidden tiangans of Day
    print(hidden.hour.dizhi)  # Print the hidden tiangans of Hour

    for pillar_data in hidden: # Iterate in the order of "Year, Month, Day, and Hour"
      assert pillar_data.tiangan is None # The hidden Tiangans are in Dizhis, so there's no data for the Tiangans.
      assert isinstance(pillar_data.dizhi, HiddenTianganDict)
    ```
    '''
    dizhi_hidden_tiangans: list[HiddenTianganDict] = [BaziUtils.get_hidden_tiangans(dz) for dz in self._bazi.four_dizhis]
    pillar_data: list = [BaziChart.PillarHiddenTiangans(None, hidden) for hidden in dizhi_hidden_tiangans]
    return BaziData(BaziChart.PillarHiddenTiangans, pillar_data)
  
  PillarShishens = PillarData[Optional[Shishen], Shishen]
  @property
  def shishens(self) -> BaziData[PillarShishens]:
    '''
    The Shishens of all Tiangans and Dizhis of Year, Month, Day, and Hour.
    Notice that Day Master is not classified into any Shishen, as per the rules.
    年、月、日、时柱的天干地支所对应的十神。注意，日主没有十神。
    '''

    day_master: Tiangan = self._bazi.day_master

    shishen_list: list[BaziChart.PillarShishens] = []
    for pillar_idx, (tg, dz) in enumerate(self._bazi.pillars):
      tg_shishen: Optional[Shishen] = BaziUtils.get_shishen(day_master, tg)
      # Remember to set the Day Master's position to `None`.
      if pillar_idx == 2:
        tg_shishen = None

      dz_shishen: Shishen = BaziUtils.get_shishen(day_master, dz)
      shishen_list.append(BaziChart.PillarShishens(tg_shishen, dz_shishen))

    assert len(shishen_list) == 4
    return BaziData(self.PillarShishens, shishen_list)

命盘 = BaziChart
