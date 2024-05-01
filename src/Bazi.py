# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import random
from enum import Enum
from datetime import date, time, datetime, timedelta
from typing import Type, Sequence, Iterator, Optional, Generic, TypeVar, Union, TypedDict, cast

from .Rules import TraitTuple, HiddenTianganDict
from .Defines import Jieqi, Tiangan, Dizhi, Ganzhi, Shishen, ShierZhangsheng
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

T = TypeVar('T')
class BaziData(Generic[T]):
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


class Bazi:
  '''
  Bazi (八字) is not aware of the timezone. We don't care abot the timezone when creating a Bazi object.
  Timezone should be well-processed outside of this class.

  ATTENTION: this class does not know anything about timezone. 
  '''

  # Save the Jieqi data as a class variable.
  __jieqi_db: hkodata.DecodedJieqiDates = hkodata.DecodedJieqiDates()
  __lunar_db: hkodata.DecodedLunarYears = hkodata.DecodedLunarYears()

  def __init__(self, birth_time: datetime, gender: BaziGender, precision: BaziPrecision) -> None:
    '''
    Input the birth time. We don't care about the timezone.
    
    Args:
    - birth_time: (datetime) The birth date (in Georgian calendar) and time. Note that no timezone should be set.
    - gender: (BaziGender) The gender of the person.
    - precision: (BaziPrecision) The precision of the birth time.
    '''

    assert isinstance(birth_time, datetime)
    self._birth_time: datetime = copy.deepcopy(birth_time)
    assert self._birth_time.tzinfo is None, 'Timezone should be well-processed outside of this class.'

    self._solar_birth_date: CalendarDate = CalendarUtils.to_solar(self._birth_time)
    assert CalendarUtils.is_valid_solar_date(self._solar_birth_date) # Here we are also checking if the date falls into the supported range.

    self._hour: int = self._birth_time.hour
    assert self._hour >= 0 and self._hour < 24

    self._minute: int = self._birth_time.minute
    assert self._minute >= 0 and self._minute < 60

    assert isinstance(gender, BaziGender)
    self._gender: BaziGender = copy.deepcopy(gender)

    assert isinstance(precision, BaziPrecision)
    self._precision: BaziPrecision = copy.deepcopy(precision)

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


class FourPillars(TypedDict):
  '''Not expected to be accessed directly. Used in `BaziChartJson`.'''
  year:  str
  month: str
  day:   str
  hour:  str

class TgShishens(TypedDict):
  '''Not expected to be accessed directly. Used in `BaziChartJson`.'''
  year:  str
  month: str
  day:   None
  hour:  str

class DzHiddenTiangans(TypedDict):
  '''Not expected to be accessed directly. Used in `BaziChartJson`.'''
  year:  dict[str, int]
  month: dict[str, int]
  day:   dict[str, int]
  hour:  dict[str, int]

class BaziChartJson(TypedDict):
  birth_time: str
  gender: str
  precision: str
  pillars: FourPillars
  nayins: FourPillars
  shier_zhangshengs: FourPillars
  tiangan_traits: FourPillars
  tiangan_shishens: TgShishens
  dizhi_traits: FourPillars
  dizhi_shishens: TgShishens
  hidden_tiangans: DzHiddenTiangans


TianganDataType = TypeVar('TianganDataType')
DizhiDataType = TypeVar('DizhiDataType')

class BaziChart:
  class PillarData(Generic[TianganDataType, DizhiDataType]):
    '''
    A helper class for storing the data of a Pillar.
    '''
    def __init__(self, tg: TianganDataType, dz: DizhiDataType) -> None:
      self._tg = copy.deepcopy(tg)
      self._dz = copy.deepcopy(dz)

    @property
    def tiangan(self) -> TianganDataType:
      return copy.deepcopy(self._tg)
    
    @property
    def dizhi(self) -> DizhiDataType:
      return copy.deepcopy(self._dz)

  def __init__(self, bazi: Bazi) -> None:
    assert isinstance(bazi, Bazi)
    self._bazi: Bazi = copy.deepcopy(bazi)

  @staticmethod
  def __parse_bazi_args(
    birth_time: Union[datetime, str],
    gender: Union[BaziGender, str], 
    precision: Union[BaziPrecision, str]
  ) -> tuple[datetime, BaziGender, BaziPrecision]:
    if isinstance(birth_time, datetime):
      _birth_time: datetime = birth_time
    else:
      assert isinstance(birth_time, str)
      _birth_time: datetime = datetime.fromisoformat(birth_time)

    assert _birth_time.tzinfo is None, 'Timezone should be well-processed outside of this class.'

    if isinstance(gender, BaziGender):
      _gender: BaziGender = gender
    else:
      assert isinstance(gender, str)
      if gender.lower() in ['男', 'male']:
        _gender: BaziGender = BaziGender.MALE
      elif gender.lower() in ['女', 'female']:
        _gender: BaziGender = BaziGender.FEMALE
      else:
        raise ValueError(f'Currently not support gender: {gender}')

    if isinstance(precision, BaziPrecision):
      _precision: BaziPrecision = precision
    else:
      assert isinstance(precision, str)
      if precision.lower() in ['分', '分钟', 'm', 'min', 'minute']:
        _precision: BaziPrecision = BaziPrecision.MINUTE
      elif precision.lower() in ['时', '小时', 'h', 'hour']:
        _precision: BaziPrecision = BaziPrecision.HOUR
      elif precision.lower() in ['天', '日', 'd', 'day']:
        _precision: BaziPrecision = BaziPrecision.DAY
      else:
        raise ValueError(f'Unsupported precision: {precision}')
      
    return _birth_time, _gender, _precision
  
  @classmethod
  def create(cls, 
             birth_time: Union[datetime, str],
             gender: Union[BaziGender, str], 
             precision: Union[BaziPrecision, str]
  ) -> 'BaziChart':
    '''
    Classmethod that creates a `BaziChart` object from the inputs.

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

    _birth_time, _gender, _precision = cls.__parse_bazi_args(birth_time, gender, precision)
    bazi: Bazi = Bazi(
      birth_time=_birth_time,
      gender=_gender,
      precision=_precision,
    )
    return cls(bazi)
  
  @classmethod
  def random(cls) -> 'BaziChart':
    '''
    Classmethod that creates a random `BaziChart` object.

    Note that the precision is currently set to `BaziPrecision.DAY`.
    Note that the year is in [1902, 2098], and day is in [1, 28].
    '''
    return BaziChart.create(
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
  
  @property
  def hidden_tiangans(self) -> BaziData[HiddenTianganDict]:
    '''
    The hidden Tiangans in all Dizhis of current bazi.
    当前八字的所有地支中的藏干。

    Usage:
    ```
    hidden = chart.hidden_tiangans

    print(hidden.year)  # Print the hidden tiangans of Year
    print(hidden.month) # Print the hidden tiangans of Month
    print(hidden.day)   # Print the hidden tiangans of Day
    print(hidden.hour)  # Print the hidden tiangans of Hour

    for h in hidden: # Iterate in the order of "Year, Month, Day, and Hour"
      pass
    ```
    '''
    dizhi_hidden_tiangans: list[HiddenTianganDict] = [BaziUtils.get_hidden_tiangans(dz) for dz in self._bazi.four_dizhis]
    return BaziData[HiddenTianganDict](HiddenTianganDict, dizhi_hidden_tiangans)
  
  PillarShishens = PillarData[Optional[Shishen], Shishen]
  @property
  def shishens(self) -> BaziData[PillarShishens]:
    '''
    The Shishens of all Tiangans and Dizhis of Year, Month, Day, and Hour.
    Notice that Day Master is not classified into any Shishen, as per the rules.
    年、月、日、时柱的天干地支所对应的十神。注意，日主没有十神。

    Usage:
    ```
    shishens = chart.shishens

    print(shishens.year.tiangan) # Print the Shishen of Year's Tiangan
    print(shishens.hour.dizhi)   # Print the Shishen of Hour's Dizhi

    for idx, pillar_shishens in enumerate(shishens):
      print(pillar_shishens.dizhi) # Print the Shishen of Dizhi of current pillar

      if idx == 2: # Skip the Day Master
        assert pillar_shishens.tiangan is None
        continue
      print(pillar_shishens.tiangan) # Print the Shishen of Tiangan of current pillar
    ```
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
  
  @property
  def nayins(self) -> BaziData[str]:
    '''
    The Nayins of the pillars of Year, Month, Day, and Hour.
    年、月、日、时柱的纳音。

    Usage:
    ```
    nayins = chart.nayins

    print(nayins.year) # Print the Nayin of the Year pillar

    for nayin in nayins: # Iterate in the order of "Year, Month, Day, and Hour"
      print(nayin)
    ```
    '''

    nayin_list: list[str] = [BaziUtils.get_nayin_str(gz) for gz in self._bazi.pillars]
    return BaziData(str, nayin_list)
  
  @property
  def shier_zhangshengs(self) -> BaziData[ShierZhangsheng]:
    '''
    The Shier Zhangshengs (i.e. 12 stages of growth) of 4 pillars of Year, Month, Day, and Hour.
    年、月、日、时柱的十二长生。

    Usage:
    ```
    zhangshengs = chart.shier_zhangshengs

    print(zhangshengs.day) # Print the Zhangsheng of the Day pillar

    for zs in zhangshengs: # Interate in the order of "Year, Month, Day, and Hour"
      pass
    ```
    '''

    day_master: Tiangan = self._bazi.day_master

    zhangsheng_list: list[ShierZhangsheng] = [BaziUtils.get_12zhangsheng(day_master, gz.dizhi) for gz in self._bazi.pillars]
    return BaziData(ShierZhangsheng, zhangsheng_list)
  
  @property
  def json(self) -> BaziChartJson:
    d: date = self._bazi.solar_birth_date
    dt: datetime = datetime.combine(d, time(self._bazi.hour, self._bazi._minute))

    gender_strs: dict[BaziGender, str] = {
      BaziGender.男: 'male',
      BaziGender.女: 'female',
    }

    precision_strs: dict[BaziPrecision, str] = {
      BaziPrecision.DAY: 'day',
      BaziPrecision.HOUR: 'hour',
      BaziPrecision.MINUTE: 'minute',
    }

    def __prep_hidden_tiangans(h: HiddenTianganDict) -> dict[str, int]:
      return { str(k) : v for k, v in h.items() }

    keys: list[str] = ['year', 'month', 'day', 'hour']
    return cast(BaziChartJson, { # TODO: Fix this type casting. It's ugly.
      'birth_time': dt.isoformat(),
      'gender': gender_strs[self._bazi.gender],
      'precision': precision_strs[self._bazi.precision],
      'pillars': { k : str(p) for k, p in zip(keys, self._bazi.pillars) },
      'tiangan_traits': { k : str(t.tiangan) for k, t in zip(keys, self.traits) },
      'dizhi_traits': { k : str(t.dizhi) for k, t in zip(keys, self.traits) },
      'hidden_tiangans': { k : __prep_hidden_tiangans(h) for k, h in zip(keys, self.hidden_tiangans) },
      'tiangan_shishens': { k : str(s.tiangan) if s.tiangan is not None else None for k, s in zip(keys, self.shishens) },
      'dizhi_shishens': { k : str(s.dizhi) for k, s in zip(keys, self.shishens) },
      'nayins': { k : n for k, n in zip(keys, self.nayins) },
      'shier_zhangshengs': { k : str(z) for k, z in zip(keys, self.shier_zhangshengs) },
    })

命盘 = BaziChart
