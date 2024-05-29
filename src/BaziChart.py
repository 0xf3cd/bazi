# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import functools
import itertools

from enum import IntFlag, unique
from datetime import datetime, timedelta
from typing import Optional, Final, Generator

from .Common import (
  frozendict,
  TraitTuple, DayunTuple, XiaoyunTuple, LiunianTuple,
  HiddenTianganDict, BaziData, GanzhiData, BaziJson,
)
from .Defines import Tiangan, Dizhi, Ganzhi, Shishen, ShierZhangsheng, Yinyang
from .Bazi import Bazi, BaziGender

from .Calendar.HkoDataCalendarUtils import prev_jie, next_jie, to_ganzhi
from .Calendar.CalendarDefines import CalendarDate
from .Utils.BaziUtils import (
  traits, hidden_tiangans, shier_zhangsheng, shishen, nayin_str, ganzhi_of_year
)


class BaziChart:
  '''
  `BaziChart` is a class that reveals the basic information of a given `Bazi`,
  for example, the traits (i.e. Wuxing and Yinyang), Shishens, ShierZhangshengs, and HiddenTiangans...

  `BaziChart` 提供原盘中的一些信息，如天干地支的阴阳和五行、十神、十二长生、纳音、地支藏干等。
  '''

  def __init__(self, bazi: Bazi) -> None:
    assert isinstance(bazi, Bazi)
    self._bazi: Final[Bazi] = copy.deepcopy(bazi)

  @classmethod
  def random(cls) -> 'BaziChart':
    '''Mainly for testing purpose.'''
    return cls(Bazi.random())

  @property
  def bazi(self) -> Bazi:
    return copy.deepcopy(self._bazi)
  
  @property
  def house_of_relationship(self) -> Dizhi:
    '''House of Partnership / House of Relationship / 婚姻宫 / 配偶宫, which is simply the day pillar's Dizhi.'''
    return self._bazi.day_pillar.dizhi
  
  @property
  def relationship_stars(self) -> GanzhiData[Tiangan, tuple[Dizhi, ...]]:
    '''Relationship Star / 夫妻星 / 配偶星.
    
    Usage:
    ```
    stars = chart.relationship_stars

    print(stars.tiangan) # Print the Tiangan that represents the Relationship Star

    print(stars.dizhi)   # Print the Dizhi tuple that represent the Relationship Star
    assert 1 <= len(stars.dizhi) <= 2 # There can be 1 or 2 representations of Relationship Star in Dizhis
    ```
    '''
    expected_shishen: Final[Shishen] = Shishen.正官 if self._bazi.gender is BaziGender.FEMALE else Shishen.正财

    f = functools.partial(shishen, self._bazi.day_master)
    found_tg = tuple(filter(lambda tg : f(tg) is expected_shishen, Tiangan))
    found_dz = tuple(filter(lambda dz : f(dz) is expected_shishen, Dizhi))

    assert len(found_tg) == 1
    assert 1 <= len(found_dz) <= 2
    return GanzhiData(found_tg[0], found_dz)

  PillarTraits = GanzhiData[TraitTuple, TraitTuple]
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
    tiangan_traits: list[TraitTuple] = [traits(tg) for tg in self._bazi.four_tiangans]
    dizhi_traits: list[TraitTuple] = [traits(dz) for dz in self._bazi.four_dizhis]
    pillar_data: list = [BaziChart.PillarTraits(tg_traits, dz_traits) for tg_traits, dz_traits in zip(tiangan_traits, dizhi_traits)]
    return BaziData(BaziChart.PillarTraits, pillar_data)
  
  @property
  def hidden_tiangan(self) -> BaziData[HiddenTianganDict]:
    '''
    The hidden Tiangans in all Dizhis of current bazi.
    当前八字的所有地支中的藏干。

    Usage:
    ```
    hidden = chart.hidden_tiangan

    print(hidden.year)  # Print the hidden tiangans of Year
    print(hidden.month) # Print the hidden tiangans of Month
    print(hidden.day)   # Print the hidden tiangans of Day
    print(hidden.hour)  # Print the hidden tiangans of Hour

    for h in hidden: # Iterate in the order of "Year, Month, Day, and Hour"
      pass
    ```
    '''
    dizhi_hidden_tiangans: list[HiddenTianganDict] = [hidden_tiangans(dz) for dz in self._bazi.four_dizhis]
    return BaziData[HiddenTianganDict](HiddenTianganDict, dizhi_hidden_tiangans)
  
  PillarShishens = GanzhiData[Optional[Shishen], Shishen]
  @property
  def shishen(self) -> BaziData[PillarShishens]:
    '''
    The Shishens of all Tiangans and Dizhis of Year, Month, Day, and Hour.
    Notice that Day Master is not classified into any Shishen, as per the rules.
    年、月、日、时柱的天干地支所对应的十神。注意，日主没有十神。

    Usage:
    ```
    shishens = chart.shishen

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
      tg_shishen: Optional[Shishen] = shishen(day_master, tg)
      # Remember to set the Day Master's position to `None`.
      if pillar_idx == 2:
        tg_shishen = None

      dz_shishen: Shishen = shishen(day_master, dz)
      shishen_list.append(BaziChart.PillarShishens(tg_shishen, dz_shishen))

    assert len(shishen_list) == 4
    return BaziData(self.PillarShishens, shishen_list)
  
  @property
  def nayin(self) -> BaziData[str]:
    '''
    The nayins of the pillars of Year, Month, Day, and Hour.
    年、月、日、时柱的纳音。

    Usage:
    ```
    nayins = chart.nayin

    print(nayins.year) # Print the Nayin of the Year pillar

    for nayin in nayins: # Iterate in the order of "Year, Month, Day, and Hour"
      print(nayin)
    ```
    '''

    nayin_list: list[str] = [nayin_str(gz) for gz in self._bazi.pillars]
    return BaziData(str, nayin_list)
  
  @property
  def shier_zhangsheng(self) -> BaziData[ShierZhangsheng]:
    '''
    The Shier Zhangshengs (i.e. 12 stages of growth) of 4 pillars of Year, Month, Day, and Hour.
    年、月、日、时柱的十二长生。

    Usage:
    ```
    zhangshengs = chart.shier_zhangsheng

    print(zhangshengs.day) # Print the Zhangsheng of the Day pillar

    for zs in zhangshengs: # Interate in the order of "Year, Month, Day, and Hour"
      pass
    ```
    '''

    day_master: Tiangan = self._bazi.day_master

    zhangsheng_list: list[ShierZhangsheng] = [shier_zhangsheng(day_master, gz.dizhi) for gz in self._bazi.pillars]
    return BaziData(ShierZhangsheng, zhangsheng_list)
  
  @property
  def dayun_order(self) -> bool:
    '''
    `True` if the Ganzhis of Dayuns are in a forward order.
    `False` if the Ganzhis of Dayuns are in a backward order.

    `True` 代表大运是顺排的，`False` 代表大运是逆排的。
    '''
    is_male: bool = (self._bazi.gender is BaziGender.男)
    is_year_dz_yang: bool = (traits(self._bazi.year_pillar.dizhi).yinyang is Yinyang.阳)
    return is_male == is_year_dz_yang
  
  @property
  def dayun_start_moment(self) -> datetime:
    '''
    The moment when first Dayun (大运) starts (solar/gregorian calendar).
    大运开始的时间 / 交运时间（公历）。
    '''
    birthtime: Final[datetime] = self._bazi.solar_datetime

    def __gap() -> timedelta:
      if self.dayun_order:
        return next_jie(birthtime).moment - birthtime
      return birthtime - prev_jie(birthtime).moment
    
    def __diff() -> timedelta:
      gap: Final[timedelta] = __gap()
      years: Final[float] = gap / timedelta(days=3) # 3 days in gap = 1 year.
      return years * timedelta(days=365) # Assume 1 year = 365 days.
    
    return birthtime + __diff()
  
  @property
  def dayun(self) -> Generator[DayunTuple, None, None]:
    '''
    A generator that produces the Ganzhis for Dayuns (大运). Each dayun lasts for 10 years.
    用于排大运的生成器。

    Usage: 
    ```
    chart: BaziChart = BaziChart(bazi)

    gen = chart.dayun
    first_ten_dayuns: list[DayunTuple] = [next(gen) for _ in range(10)]

    next_ten_dayuns: list[DayunTuple] = list(itertools.islice(gen, 10))

    for start_time, gz in chart.dayun: # Infinite loop...
      print(start_time, gz) # Print the start time and Ganzhi of the dayun
    ``` 
    '''

    def __dayun_generator() -> Generator[DayunTuple, None, None]:
      step: Final[int] = 1 if self.dayun_order else -1
      ganzhi_year: int = to_ganzhi(self.dayun_start_moment).year
      gz: Ganzhi = self._bazi.month_pillar.next(step)

      while True:
        yield DayunTuple(ganzhi_year, gz)
        ganzhi_year += 10
        gz = gz.next(step)

    return __dayun_generator()

  @property
  def xiaoyun(self) -> tuple[XiaoyunTuple, ...]:
    '''
    A tuple containing all Xiaoyuns (小运).
    一个包含所有小运的元组。

    Usage:
    ```
    chart: BaziChart = BaziChart(bazi)

    for xusui_age, ganzhi in chart.xiaoyun:
      print(f'虚岁: {xusui_age}, 小运: {ganzhi}')
    ```
    '''

    step: Final[int] = 1 if self.dayun_order else -1
    until_xusui_age: Final[int] = 1 + to_ganzhi(self.dayun_start_moment).year - to_ganzhi(self._bazi.solar_datetime).year

    def __xiaoyun_at_age(age: int) -> XiaoyunTuple:
      return XiaoyunTuple(age, self._bazi.hour_pillar.next(age * step))

    return tuple(__xiaoyun_at_age(age) for age in range(1, until_xusui_age + 1))
  
  @property
  def liunian(self) -> Generator[LiunianTuple, None, None]:
    '''
    A generator that produces the Liunians (流年).
    一个生成器，用于生成流年。

    Usage:
    ```
    chart: BaziChart = BaziChart(bazi)

    for year, ganzhi in chart.liunian: # Infinite loop...
      print(year, ganzhi) # Prints something like "2024 甲辰"
    ```
    '''

    def __liunian_generator() -> Generator[LiunianTuple, None, None]:
      year: int = self._bazi.ganzhi_date.year
      while True:
        yield LiunianTuple(year, ganzhi_of_year(year))
        year += 1
    return __liunian_generator()
  
  @property
  def transit_db(self) -> 'TransitDatabase':
    '''
    The database used to query transit Ganzhis.
    用于查询运（大运、小运、流年等的）干支的数据库。
    '''
    return TransitDatabase(self)

  @property
  def json(self) -> BaziJson.BaziChartJsonDict:
    '''
    A json dict representing the `BaziChart`.
    代表此 `BaziChart` 的 json 字典。
    '''

    transits: BaziJson.Transits = {
      'dayun_start_time': self.dayun_start_moment.isoformat(),
      'xiaoyun': { str(age) : str(xiaoyun) for age, xiaoyun in self.xiaoyun },
      'dayun': { str(year) : str(dayun) for year, dayun in itertools.islice(self.dayun, 10) },
    }

    f = BaziJson.gen_fourpillars
    return {
      'birth_time': self._bazi.solar_datetime.isoformat(),
      'gender': str(self._bazi.gender),
      'precision': str(self._bazi.precision),
      'pillars': f([str(p) for p in self._bazi.pillars]),
      'nayin': f([str(ny) for ny in self.nayin]),
      'shier_zhangsheng': f([str(sz) for sz in self.shier_zhangsheng]),
      'tiangan_traits': f([str(t.tiangan) for t in self.traits]),
      'dizhi_traits': f([str(t.dizhi) for t in self.traits]),
      'tiangan_shishen': f([str(s.tiangan) for s in self.shishen]),
      'dizhi_shishen': f([str(s.dizhi) for s in self.shishen]),
      'hidden_tiangan': f([str(h) for h in self.hidden_tiangan]),
      'transits': transits,
    }

命盘 = BaziChart


class DayunDatabase:
  '''A database that figures out a given Ganzhi year falls into which Dayun (大运).'''
  def __init__(self, chart: BaziChart) -> None:
    self._gen: Final[Generator[DayunTuple, None, None]] = chart.dayun
    self._cache: Final[dict[int, Ganzhi]] = {}

    self._first_dayun: DayunTuple = next(self._gen)
    self._cache[self._first_dayun.ganzhi_year] = self._first_dayun.ganzhi

  def __getitem__(self, gz_year: int) -> DayunTuple:
    assert isinstance(gz_year, int)
    assert gz_year >= self._first_dayun.ganzhi_year

    dayun_idx: int = (gz_year - self._first_dayun.ganzhi_year) // 10
    expected_gz_year: int = self._first_dayun.ganzhi_year + 10 * dayun_idx

    while expected_gz_year not in self._cache:
      next_dayun: DayunTuple = next(self._gen)
      self._cache[next_dayun.ganzhi_year] = next_dayun.ganzhi

    return DayunTuple(expected_gz_year, self._cache[expected_gz_year])


@unique
class TransitOptions(IntFlag):
  '''Specifies whether Dayun / Xiaoyun / Liunian transits should be considered. 用于指定是否考虑大运流年、小运、流年等。'''
  XIAOYUN         = 0x1
  DAYUN           = 0x2
  LIUNIAN         = 0x4
  XIAOYUN_LIUNIAN = XIAOYUN | LIUNIAN
  DAYUN_LIUNIAN   = DAYUN   | LIUNIAN


class TransitDatabase:
  '''A database that figures out the Ganzhis of transits.'''
  def __init__(self, chart: BaziChart) -> None:
    self._birth_ganzhi_date: CalendarDate = chart.bazi.ganzhi_date

    birth_gz_year: Final[int] = chart.bazi.ganzhi_date.year
    self._xiaoyun_ganzhis: Final[frozendict[int, Ganzhi]] = frozendict({
      birth_gz_year + age - 1 : gz
      for age, gz in chart.xiaoyun
    })

    self._first_dayun_start_gz_year: Final[int] = next(chart.dayun).ganzhi_year
    self._dayun_db: Final[DayunDatabase] = DayunDatabase(chart)

  def support(self, gz_year: int, options: TransitOptions) -> bool:
    '''
    Return whether the given `gz_year` and `option` are supported by this `TransitDatabase`.

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `options`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Return: (bool) Whether the given `gz_year` and `options` are supported by this `TransitDatabase`.
    '''

    assert isinstance(gz_year, int)
    assert isinstance(options, TransitOptions)
    assert options in TransitOptions

    if options.value & TransitOptions.XIAOYUN.value:
      if gz_year not in self._xiaoyun_ganzhis:
        return False
    if options.value & TransitOptions.DAYUN.value:
      if gz_year < self._first_dayun_start_gz_year:
        return False
    if options.value & TransitOptions.LIUNIAN.value:
      if gz_year < self._birth_ganzhi_date.year:
        return False

    return True

  def ganzhis(self, gz_year: int, options: TransitOptions) -> tuple[Ganzhi, ...]:
    '''
    Return the Ganzhis of the selected transits for the given `gz_year` and `option`.

    返回所选中的小运、大运或流年等对应的干支。

    Args:
    - `gz_year`: The year in Ganzhi calendar, mainly used to compute the transit pillars. 干支纪年法中的年，主要用于计算运（小运/大运/流年）的天干地支。
    - `options`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Return: (tuple[Ganzhi, ...]) The Ganzhis of the selected transits for the given `gz_year` and `options`.
    '''

    assert isinstance(gz_year, int)
    assert isinstance(options, TransitOptions) and options in TransitOptions

    if not self.support(gz_year, options):
      raise ValueError(f'Inputs not supported. Year: {gz_year}, option: {options}')

    transit_ganzhis: list[Ganzhi] = []
    if options.value & TransitOptions.XIAOYUN.value:
      assert gz_year in self._xiaoyun_ganzhis
      transit_ganzhis.append(self._xiaoyun_ganzhis[gz_year])
    if options.value & TransitOptions.DAYUN.value:
      assert gz_year >= self._first_dayun_start_gz_year
      transit_ganzhis.append(self._dayun_db[gz_year].ganzhi)
    if options.value & TransitOptions.LIUNIAN.value:
      assert gz_year >= self._birth_ganzhi_date.year
      transit_ganzhis.append(ganzhi_of_year(gz_year))

    return tuple(transit_ganzhis)
