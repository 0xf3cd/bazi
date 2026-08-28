# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import functools
import itertools

from calendar import monthrange
from datetime import datetime, timedelta
from typing import Final, TypedDict
from collections.abc import Generator, Sequence

from .data_types import (
  TraitTuple, DayunTuple, XiaoyunTuple, LiunianTuple,
  HiddenTianganDict, BaziData, GanzhiData,
)
from .defines import Tiangan, Dizhi, Ganzhi, Shishen, ShierZhangsheng, Yinyang
from .bazi import Bazi, BaziGender
from .school import DayunYearRule

from .calendar import CalendarUtilsProtocol, calendar_utils_of
from .utils.bazi_utils import (
  traits, hidden_tiangans, shier_zhangsheng, shishen, nayin_str, ganzhi_of_year,
  _ganzhi_year_month_of_jie,
)


def _dayun_year_label(raw_year: int, first_year_label: int,
                      index: int, rule: DayunYearRule) -> int:
  '''Project a physical Dayun boundary to the selected year-label view.
  把物理大运边界投影到所选年份标签视图。'''
  assert isinstance(raw_year, int)
  assert isinstance(first_year_label, int)
  assert isinstance(index, int)
  assert index >= 0
  assert isinstance(rule, DayunYearRule)

  if rule is DayunYearRule.JIE_PROJECTED:
    return first_year_label if index == 0 else raw_year
  assert rule is DayunYearRule.FIXED_DECADE
  return first_year_label + 10 * index


class BaziJson:
  '''
  The class that represents bazi-related charts in JSON format.
  '''

  class FourPillars(TypedDict):
    '''Not expected to be accessed directly. Used in `JsonDict`.'''
    year:  str
    month: str
    day:   str
    hour:  str

  @staticmethod
  def gen_fourpillars(data: Sequence[str]) -> 'BaziJson.FourPillars':
    assert len(data) == 4
    return { 'year': data[0], 'month': data[1], 'day': data[2], 'hour': data[3] }

  class TianganShishens(TypedDict):
    '''Not expected to be accessed directly. Used in `JsonDict`. Entries are `None`
    (JSON null) where no Shishen exists -- i.e. `day`, the day master itself.
    没有十神的位置为 None（JSON null）——即日主自身所在的 `day`。'''
    year:  str | None
    month: str | None
    day:   str | None
    hour:  str | None

  @staticmethod
  def gen_tiangan_shishens(data: Sequence[Shishen | None]) -> 'BaziJson.TianganShishens':
    assert len(data) == 4
    strs: list[str | None] = [None if s is None else str(s) for s in data]
    return { 'year': strs[0], 'month': strs[1], 'day': strs[2], 'hour': strs[3] }

  class Dayun(TypedDict):
    '''Not expected to be accessed directly. Used in `Transits`.'''
    ganzhi: str
    # ISO 8601 boundaries of the physical interval / 物理区间边界的 ISO 8601 字符串
    start_time: str
    end_time: str

  class Transits(TypedDict):
    '''Not expected to be accessed directly. Used in `JsonDict`.'''
    # start time of the dayun (isoformat string) / 大运的开始时间 (isoformat 格式的字符串)
    dayun_start_time: str

    # key: xusui / 虚岁
    # value: xiaoyun at this xusui age / 对应虚岁的小运
    xiaoyun: dict[str, str]

    # key: start-year label under `dayun_year_rule`; it does not mean that the Dayun
    # occupies the entire label year / 所选规则下的起运年份标签，不表示该步大运占据整个标签年
    # value: Dayun Ganzhi and its physical interval / 大运干支与物理区间
    dayun: dict[str, 'BaziJson.Dayun']

  class School(TypedDict):
    '''Not expected to be accessed directly. Used in `BaziChartJsonDict`. The school
    profile (流派档案), serialized as the member name of each school reading.
    流派档案：每项流派看法各存其枚举成员名。'''
    day_rollover: str
    hongyan_key: str
    yangren_def: str
    anhe_def: str
    xing_def: str
    gong_def: str

  class BaziChartJsonDict(TypedDict):
    birth_time: str
    gender: str
    precision: str
    backend: str
    dayun_year_rule: str
    school: 'BaziJson.School'
    pillars: 'BaziJson.FourPillars'
    nayin: 'BaziJson.FourPillars'
    shier_zhangsheng: 'BaziJson.FourPillars'
    tiangan_traits: 'BaziJson.FourPillars'
    dizhi_traits: 'BaziJson.FourPillars'
    tiangan_shishen: 'BaziJson.TianganShishens'
    dizhi_shishen: 'BaziJson.FourPillars'
    hidden_tiangan: 'BaziJson.FourPillars'
    transits: 'BaziJson.Transits'


class BaziChart:
  '''
  `BaziChart` is a class that reveals the basic information of a given `Bazi`,
  for example, the traits (i.e. Wuxing and Yinyang), Shishens, ShierZhangshengs, and HiddenTiangans...

  Derived quantities are cached on first access: the chart assumes its `_bazi` is never
  rebound after construction (rebinding it leaves already-warmed caches stale).

  `BaziChart` 提供原盘中的一些信息，如天干地支的阴阳和五行、十神、十二长生、纳音、地支藏干等。
  盘面派生量首次访问后缓存：命盘假定构造后 `_bazi` 不再被重绑（重绑不会刷新已暖缓存）。
  '''

  def __init__(self, bazi: Bazi) -> None:
    if not isinstance(bazi, Bazi):
      raise TypeError(f'Expected Bazi, got {type(bazi)}')
    # `Bazi` is not frozen (private state can be reassigned), so keep an isolated copy --
    # `test_malicious` pins that poisoning the caller's object never reaches the chart.
    # `Bazi` 并非 frozen（私有状态可被改写），故持隔离副本；test_malicious 钉住污染不透传。
    self._bazi: Final[Bazi] = copy.deepcopy(bazi)

  @classmethod
  def random(cls) -> 'BaziChart':
    '''Mainly for testing purpose.'''
    return cls(Bazi.random())

  @property
  def bazi(self) -> Bazi:
    '''A fresh deep copy per access -- deliberately NOT a `cached_property`, since a cached
    shared `Bazi` could be mutated through the returned handle.
    每次访问深拷一份，故意不用 `cached_property`：缓存共享件会经返回句柄被改。'''
    return copy.deepcopy(self._bazi)

  @property
  def _utils(self) -> CalendarUtilsProtocol:
    '''
    The resolved calendar utils of the underlying `Bazi`'s backend. Resolved on each access,
    so the resolved utils -- the HKO module or a celestial singleton -- is never stored on
    the instance.
    底层 `Bazi` 所用历法后端对应的实际工具。每次访问时现解析，实例上不存解析结果，保证 `BaziChart` 可安全 deepcopy。

    Do NOT turn this into a `cached_property` -- that would write the resolved utils into
    the instance dict, where the module breaks `deepcopy` loudly and a singleton would be
    silently duplicated, forking its caches.
    '''
    return calendar_utils_of(self._bazi.config.backend)
  
  @property
  def house_of_relationship(self) -> Dizhi:
    '''House of Partnership / House of Relationship / 婚姻宫 / 配偶宫, which is simply the day pillar's Dizhi.'''
    return self._bazi.day_pillar.dizhi
  
  @functools.cached_property
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
  @functools.cached_property
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
    return BaziData(*pillar_data)
  
  @functools.cached_property
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
    return BaziData(*dizhi_hidden_tiangans)
  
  PillarShishens = GanzhiData[Shishen | None, Shishen]
  @functools.cached_property
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
      tg_shishen: Shishen | None = shishen(day_master, tg)
      # Remember to set the Day Master's position to `None`.
      if pillar_idx == 2:
        tg_shishen = None

      dz_shishen: Shishen = shishen(day_master, dz)
      shishen_list.append(BaziChart.PillarShishens(tg_shishen, dz_shishen))

    assert len(shishen_list) == 4
    return BaziData(*shishen_list)
  
  @functools.cached_property
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
    return BaziData(*nayin_list)
  
  @functools.cached_property
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
    return BaziData(*zhangsheng_list)
  
  @functools.cached_property
  def dayun_order(self) -> bool:
    '''
    `True` if the Ganzhis of Dayuns are in a forward order.
    `False` if the Ganzhis of Dayuns are in a backward order.

    `True` 代表大运是顺排的，`False` 代表大运是逆排的。

    Note: the traditional phrasing keys on the year Tiangan's yinyang (阳男阴女顺排，阴男阳女逆排);
    this implementation reads the year Dizhi's yinyang instead -- mathematically identical, since
    within the 60 Jiazi a Ganzhi's Tiangan and Dizhi always share the same yinyang.
    传统表述以年干阴阳论「阳男阴女顺、阴男阳女逆」；本实现读年支阴阳，二者数学恒等价——
    六十甲子内干支的阴阳恒一致。
    '''
    is_male: bool = (self._bazi.gender is BaziGender.男)
    is_year_dz_yang: bool = (traits(self._bazi.year_pillar.dizhi).yinyang is Yinyang.阳)
    return is_male == is_year_dz_yang
  
  @functools.cached_property
  def dayun_start_moment(self) -> datetime:
    '''
    The moment when first Dayun (大运) starts (solar/gregorian calendar).
    大运开始的时间 / 交运时间（公历）。
    '''
    birthtime: Final[datetime] = self._bazi.solar_datetime

    def __gap() -> timedelta:
      # Count from `Bazi.bracketing_jies`: under HOUR/MINUTE that is exactly the jie owning
      # the month pillar; under DAY it keeps the adjudicated moment-level counting, which on
      # a jieqi's day can legitimately name a different jie (see `Bazi.bracketing_jies`).
      prev_j, next_j = self._bazi.bracketing_jies
      if self.dayun_order:
        return next_j.moment - birthtime
      # Ties go new, so under HOUR/MINUTE the owning jie's true moment can fall up to one
      # granularity unit *after* the birth; the dayun then starts at the birth itself. For
      # DAY, `prev_jie(birthtime).moment <= birthtime` always holds and the clamp is inert.
      return max(timedelta(0), birthtime - prev_j.moment)
    
    def __diff() -> timedelta:
      gap: Final[timedelta] = __gap()
      years: Final[float] = gap / timedelta(days=3) # 3 days in gap = 1 year.
      return years * timedelta(days=365) # Assume 1 year = 365 days.
    
    return birthtime + __diff()

  def _dayun_owning_ganzhi_year(self, moment: datetime) -> int:
    '''Return the Ganzhi year containing `moment`, as determined by its owning Jie.
    按所属节返回 `moment` 所在的干支年。'''
    assert isinstance(moment, datetime)
    return _ganzhi_year_month_of_jie(self._utils.prev_jie(moment))[0]

  @property
  def _dayun_empty_timeline_message(self) -> str:
    '''Return the shared error message for a Dayun timeline with no supported start.
    返回大运时刻线无受支持起点时的共享报错消息。'''
    first, last = self._utils.supported_jie_boundaries()
    return f'No Dayun starts within the supported Jie range [{first}, {last})'

  @functools.cached_property
  def _dayun_first_year_label(self) -> int:
    '''
    The shared first Dayun year label, independent of the later-year projection rule.
    A HOUR chart can assign a cross-midnight 立春 tie to the new birth year while its
    clamped start moment still lies on a civil date carrying the old day-level year. The
    floor keeps that first Dayun aligned with the chart and leaves later labels untouched.
    与后续年份投影规则无关的共享首步大运年份标签。HOUR 盘在跨午夜立春 tie 中可已归新出生年，
    而压在出生时刻的首运仍落在日级旧年；首步下限使二者一致，且不向后续标签传播。
    '''
    first, last = self._utils.supported_jie_boundaries()
    first_start_moment: Final[datetime] = self._dayun_start_moment_at(0)
    if not first <= first_start_moment < last:
      raise ValueError(self._dayun_empty_timeline_message)
    return max(self._dayun_owning_ganzhi_year(first_start_moment), self._bazi.ganzhi_year)

  def _dayun_start_moment_at(self, index: int) -> datetime:
    '''Return the `index`-th Dayun boundary, recomputed from the first; clamp Feb 29 to
    Feb 28 in non-leap target years. 从首运边界重算第 `index` 个边界；目标平年把 2 月 29 日压到 2 月 28 日。'''
    assert isinstance(index, int)
    assert index >= 0

    start: Final[datetime] = self.dayun_start_moment
    year: Final[int] = start.year + 10 * index
    day: Final[int] = min(start.day, monthrange(year, start.month)[1])
    return start.replace(year=year, day=day)

  @property
  def dayun(self) -> Generator[DayunTuple, None, None]:
    '''
    A finite generator that produces Dayuns (大运) from their Gregorian start-moment
    timeline. Each Dayun covers `[start_moment, end_moment)`; only starts in the selected
    calendar backend's half-open Jie window are generated, so the result can be empty.
    从公历交运时刻线生成有限大运；每步覆盖 `[start_moment, end_moment)`，只生成落在所选历法
    后端半开节气窗口内的起点，因此结果可以为空。

    Usage: 
    ```
    chart: BaziChart = BaziChart(bazi)

    gen = chart.dayun
    first_ten_dayuns: list[DayunTuple] = list(itertools.islice(gen, 10))

    next_ten_dayuns: list[DayunTuple] = list(itertools.islice(gen, 10))

    for dayun in chart.dayun:
      print(dayun.start_moment, dayun.ganzhi)
    ``` 
    '''

    def __dayun_generator() -> Generator[DayunTuple, None, None]:
      step: Final[int] = 1 if self.dayun_order else -1
      gz: Ganzhi = self._bazi.month_pillar.next(step)
      first, last = self._utils.supported_jie_boundaries()
      index: int = 0
      start_moment: datetime = self._dayun_start_moment_at(index)

      while first <= start_moment < last:
        first_year_label: int = self._dayun_first_year_label
        raw_year: int = self._dayun_owning_ganzhi_year(start_moment)
        ganzhi_year: int = _dayun_year_label(
          raw_year,
          first_year_label,
          index,
          self._bazi.config.dayun_year_rule,
        )
        end_moment: datetime = self._dayun_start_moment_at(index + 1)
        yield DayunTuple(ganzhi_year, gz, start_moment, end_moment)
        index += 1
        start_moment = end_moment
        gz = gz.next(step)

    return __dayun_generator()

  @functools.cached_property
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
    # Xiaoyun covers the xusui ages before the first dayun starts. Both ends of the
    # subtraction live in the chart's own attribution (see `_dayun_first_year_label`),
    # so the count can never go below one.
    until_xusui_age: Final[int] = 1 + self._dayun_first_year_label - self._bazi.ganzhi_year

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
      # Start from `Bazi.ganzhi_year` (precision-attributed, same source as the year pillar),
      # so the first liunian's ganzhi always equals the year pillar.
      year: int = self._bazi.ganzhi_year
      while True:
        yield LiunianTuple(year, ganzhi_of_year(year))
        year += 1
    return __liunian_generator()

  @property
  def json(self) -> BaziJson.BaziChartJsonDict:
    '''
    A json dict representing the `BaziChart`.
    代表此 `BaziChart` 的 json 字典。
    '''

    dayuns: tuple[DayunTuple, ...] = tuple(itertools.islice(self.dayun, 10))
    transits: BaziJson.Transits = {
      'dayun_start_time': self.dayun_start_moment.isoformat(),
      'xiaoyun': { str(age) : str(xiaoyun) for age, xiaoyun in self.xiaoyun },
      'dayun': {
        str(dayun.ganzhi_year): {
          'ganzhi': str(dayun.ganzhi),
          'start_time': dayun.start_moment.isoformat(),
          'end_time': dayun.end_moment.isoformat(),
        }
        for dayun in dayuns
      },
    }

    f = BaziJson.gen_fourpillars
    return {
      'birth_time': self._bazi.solar_datetime.isoformat(),
      'gender': str(self._bazi.gender),
      'precision': str(self._bazi.config.precision),
      'backend': str(self._bazi.config.backend),
      'dayun_year_rule': str(self._bazi.config.dayun_year_rule),
      'school': {
        'day_rollover': self._bazi.config.school.day_rollover.name,
        'hongyan_key': self._bazi.config.school.hongyan_key.name,
        'yangren_def': self._bazi.config.school.yangren_def.name,
        'anhe_def': self._bazi.config.school.anhe_def.name,
        'xing_def': self._bazi.config.school.xing_def.name,
        'gong_def': self._bazi.config.school.gong_def.name,
      },
      'pillars': f([str(p) for p in self._bazi.pillars]),
      'nayin': f([str(ny) for ny in self.nayin]),
      'shier_zhangsheng': f([str(sz) for sz in self.shier_zhangsheng]),
      'tiangan_traits': f([str(t.tiangan) for t in self.traits]),
      'dizhi_traits': f([str(t.dizhi) for t in self.traits]),
      'tiangan_shishen': BaziJson.gen_tiangan_shishens([s.tiangan for s in self.shishen]),
      'dizhi_shishen': f([str(s.dizhi) for s in self.shishen]),
      'hidden_tiangan': f([str(h) for h in self.hidden_tiangan]),
      'transits': transits,
    }

命盘 = BaziChart
