# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import random
from datetime import date, time, datetime
from typing import (
  Optional, Generic, TypeVar, 
  Union, TypedDict, Final,
)

from ..Common import TraitTuple, HiddenTianganDict
from ..Defines import Tiangan, Shishen, ShierZhangsheng
from ..Bazi import Bazi, BaziGender, BaziPrecision, BaziData
from ..Utils import BaziUtils


TianganDataType = TypeVar('TianganDataType')
DizhiDataType = TypeVar('DizhiDataType')

class BaziChart:
  class PillarData(Generic[TianganDataType, DizhiDataType]):
    '''
    A helper class for storing the data of a Pillar.
    '''
    def __init__(self, tg: TianganDataType, dz: DizhiDataType) -> None:
      self._tg: Final[TianganDataType] = copy.deepcopy(tg)
      self._dz: Final[DizhiDataType] = copy.deepcopy(dz)

    @property
    def tiangan(self) -> TianganDataType:
      return copy.deepcopy(self._tg)
    
    @property
    def dizhi(self) -> DizhiDataType:
      return copy.deepcopy(self._dz)

  def __init__(self, bazi: Bazi) -> None:
    assert isinstance(bazi, Bazi)
    self._bazi: Final[Bazi] = copy.deepcopy(bazi)

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
  
  
  class FourPillars(TypedDict):
    '''Not expected to be accessed directly. Used in `BaziChartJson`.'''
    year:  str
    month: str
    day:   str
    hour:  str

  class JsonDict(TypedDict):
    birth_time: str
    gender: str
    precision: str
    pillars: 'BaziChart.FourPillars'
    nayins: 'BaziChart.FourPillars'
    shier_zhangshengs: 'BaziChart.FourPillars'
    tiangan_traits: 'BaziChart.FourPillars'
    dizhi_traits: 'BaziChart.FourPillars'
    tiangan_shishens: 'BaziChart.FourPillars'
    dizhi_shishens: 'BaziChart.FourPillars'
    hidden_tiangans: 'BaziChart.FourPillars'

  @property
  def json(self) -> JsonDict:
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

    def __prep_hidden_tiangans(h: HiddenTianganDict) -> str:
      str_list: list[str] = [f'{k}:{v}' for k, v in h.items()]
      str_list = sorted(str_list, key=lambda s: int(s.split(':')[1]), reverse=True)
      return ','.join(str_list)
    
    def __gen_fourpillars(data: list[str]) -> BaziChart.FourPillars:
      assert len(data) == 4
      return { 'year': data[0], 'month': data[1], 'day': data[2], 'hour': data[3] }
    
    return {
      'birth_time': dt.isoformat(),
      'gender': gender_strs[self._bazi.gender],
      'precision': precision_strs[self._bazi.precision],
      'pillars': __gen_fourpillars([str(p) for p in self._bazi.pillars]),
      'nayins': __gen_fourpillars([str(p) for p in self.nayins]),
      'shier_zhangshengs': __gen_fourpillars([str(sz) for sz in self.shier_zhangshengs]),
      'tiangan_traits': __gen_fourpillars([str(t.tiangan) for t in self.traits]),
      'dizhi_traits': __gen_fourpillars([str(t.dizhi) for t in self.traits]),
      'tiangan_shishens': __gen_fourpillars([str(s.tiangan) for s in self.shishens]),
      'dizhi_shishens': __gen_fourpillars([str(s.dizhi) for s in self.shishens]),
      'hidden_tiangans': __gen_fourpillars([__prep_hidden_tiangans(h) for h in self.hidden_tiangans]),
    }

命盘 = BaziChart
