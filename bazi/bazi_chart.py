# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''命盘派生信息与命盘 JSON。

BaziChart 在 Bazi 上提供十神、藏干、纳音、十二长生与运限等信息；
from_json 使用当前实现重算并核对记录，不是历史结果的冻结恢复。'''

import copy
import functools
import itertools
from random import Random

from calendar import monthrange
from datetime import datetime, timedelta
from typing import Final, TypeAlias, TypedDict, cast
from collections.abc import Generator, Mapping, Sequence

from .data_types import (
  TraitTuple, DayunTuple, XiaoyunTuple, LiunianTuple,
  HiddenTianganDict, BaziData, GanzhiData,
)
from .defines import Tiangan, Dizhi, Ganzhi, Shishen, ShierZhangsheng, Yinyang
from .bazi import Bazi, BaziGender, LocationTimeJson, _parse_location
from .school import DayunYearRule, BaziConfig, BaziSchool, PeiouXingDef, DEFAULT_CONFIG, _config_json

from .calendar import CalendarUtilsProtocol, calendar_utils_of
from .calendar.dates import GanzhiYearMonth
from .utils.bazi_utils import (
  traits, hidden_tiangans, shier_zhangsheng, shishen, nayin_str, ganzhi_of_year,
)


def _dayun_year_label(raw_year: int, first_year_label: int,
                      index: int, rule: DayunYearRule) -> int:
  '''把物理大运边界投影到所选年份标签视图。'''
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
  命盘 JSON 的字段类型及内部构造辅助函数。
  '''

  class FourPillars(TypedDict):
    '''供 `BaziChartJsonDict` 使用的四柱字段，不作为独立访问入口。'''
    year:  str
    month: str
    day:   str
    hour:  str

  @staticmethod
  def gen_fourpillars(data: Sequence[str]) -> 'BaziJson.FourPillars':
    assert len(data) == 4
    return { 'year': data[0], 'month': data[1], 'day': data[2], 'hour': data[3] }

  class TianganShishens(TypedDict):
    '''供 `BaziChartJsonDict` 使用的天干十神字段，不作为独立访问入口。
    日主自身所在的 `day` 没有十神，存为 None（JSON null）。'''
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
    '''供 `Transits` 使用的一步大运记录，不作为独立访问入口。'''
    ganzhi: str
    # 地点盘采用东八区无时区物理区间边界；默认路径采用民用标签。
    start_time: str
    end_time: str

  class Transits(TypedDict):
    '''供 `BaziChartJsonDict` 使用的运限字段，不作为独立访问入口。'''
    # 与 Dayun.start_time 使用相同时间坐标。
    dayun_start_time: str

    # 键为虚岁，值为对应小运。
    xiaoyun: dict[str, str]

    # 键为所选规则下的起运年份标签，不表示该步大运占据整个标签年；值为大运干支与物理区间。
    dayun: dict[str, 'BaziJson.Dayun']

  class School(TypedDict):
    '''供 `BaziChartJsonDict` 使用的流派档案，不作为独立访问入口。
    各读法存为枚举成员名；键为 `BaziSchool` 字段，按 dataclass 声明序排列。
    序列化与 `BaziSchool.from_json` 均由该声明推导，并须满足本类型契约。'''
    day_rollover: str
    anhe_def: str
    xing_def: str
    gong_def: str
    yangren_def: str
    feiren_def: str
    hongyan_anchor: str
    tianyi_anchor: str
    tianyi_def: str
    yima_anchor: str
    huagai_anchor: str
    jiangxing_anchor: str
    jiesha_anchor: str
    wangshen_anchor: str
    jinyu_anchor: str
    zaisha_anchor: str
    wenchang_anchor: str
    wenchang_def: str
    taiji_anchor: str
    taiji_def: str
    guoyin_anchor: str
    guoyin_def: str
    peiou_xing_def: str

  class _CommonChartJsonDict(TypedDict):
    '''默认盘与地点盘 JSON 的共同字段。'''
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

  class DefaultBaziChartJsonDict(_CommonChartJsonDict):
    '''默认盘 JSON，出生时刻为截断到分钟的民用标签。'''
    birth_time: str

  class LocationBaziChartJsonDict(_CommonChartJsonDict, LocationTimeJson):
    '''地点盘 JSON；时间字符串须使用输出端的规范 ISO 8601 拼写。'''

  '''默认盘或地点盘 JSON 的完整字段类型。'''
  BaziChartJsonDict: TypeAlias = DefaultBaziChartJsonDict | LocationBaziChartJsonDict


def _peiou_xing_target(day_master: Tiangan, gender: BaziGender, definition: PeiouXingDef) -> Tiangan:
  '''
  按取法定义选出配偶星的目标天干；同一（日主，性别，取法）恰有一个目标。

  - 默认读法：十神为正财（男）／正官（女）的天干。
  - 阴阳干读法（《三命通会·论六亲》，单源类推）：男取十神属正财、偏财且为阴干者，
    女取十神属正官、七杀且为阳干者。

  目标恒不等于日主：财／官杀与日主五行不同，比肩不在候选内。
  '''
  assert isinstance(day_master, Tiangan)
  assert isinstance(gender, BaziGender)
  assert isinstance(definition, PeiouXingDef)

  expected: tuple[Shishen, ...]
  if definition is PeiouXingDef.ZHENGCAI_ZHENGGUAN:
    expected = (Shishen.正官,) if gender is BaziGender.FEMALE else (Shishen.正财,)
  else:
    assert definition is PeiouXingDef.YINYANGGAN
    expected = (Shishen.正官, Shishen.七杀) if gender is BaziGender.FEMALE else (Shishen.正财, Shishen.偏财)

  f = functools.partial(shishen, day_master)
  found_tg = tuple(filter(
    lambda tg: f(tg) in expected and (
      definition is PeiouXingDef.ZHENGCAI_ZHENGGUAN
      or traits(tg).yinyang is (Yinyang.阳 if gender is BaziGender.FEMALE else Yinyang.阴)
    ),
    Tiangan,
  ))

  assert len(found_tg) == 1
  return found_tg[0]


class BaziChart:
  '''
  提供原盘的阴阳五行、十神、十二长生、纳音、藏干等派生信息。
  派生量首次访问后缓存；构造后不得重绑 `_bazi`，重绑不会刷新已有缓存。
  '''

  def __init__(self, bazi: Bazi) -> None:
    if not isinstance(bazi, Bazi):
      raise TypeError(f'Expected Bazi, got {type(bazi)}')
    # Bazi 并非 frozen，私有状态可被改写，因此持有隔离副本。
    # test_malicious 验证修改调用方对象不会影响命盘。
    self._bazi: Final[Bazi] = copy.deepcopy(bazi)

  @classmethod
  def random(cls, config: BaziConfig = DEFAULT_CONFIG, *, rng: Random | None = None) -> 'BaziChart':
    '''
    用 `Bazi.random` 随机生成命盘，主要用于测试。

    Args:
    - config: (BaziConfig) 原样传递的命盘配置。
    - rng: (Random | None) 局部随机源；省略时沿用全局种子语义。

    Return: (BaziChart) 随机命盘。
    '''
    return cls(Bazi.random(config, rng=rng))

  @classmethod
  def from_json(cls, d: Mapping[str, object]) -> 'BaziChart':
    '''
    从完整记录重建命盘，并与当前 `json` 输出逐项核对。

    Args:
    - d: (Mapping[str, object]) 已解析的 `BaziChart.json` 记录，不是 JSON 文本。

    Note:
    - 根对象须严格匹配 `BaziJson.DefaultBaziChartJsonDict` 或 `BaziJson.LocationBaziChartJsonDict`，
      两者不可混用。所有字段必填；任何层级的多余键及非规范拼写均被拒绝。
      映射顺序不限，派生值只核对、不存储。
    - 键和字符串值必须是原生 `str`，不接受子类；空值为 `None`。
    - 类型错误抛 `TypeError`；缺键、多键、不支持的值及不一致抛 `ValueError`。只保证与当前版本一致。
      同时违反多个约束时，不保证先报告哪项错误。
    - 不修改或持有调用方映射；重建的大运时刻线为空时，读取 `json` 核对会抛 `ValueError`。

    Return: (BaziChart) 重建的命盘。
    '''
    if not isinstance(d, Mapping):
      raise TypeError(f'Expected Mapping at chart, got {type(d)}')
    for key in d:
      if type(key) is not str:
        raise TypeError(f'Expected str key at chart, got {type(key)}')

    default_keys = BaziJson.DefaultBaziChartJsonDict.__required_keys__
    location_keys = BaziJson.LocationBaziChartJsonDict.__required_keys__
    location_aware: bool
    if d.keys() == default_keys:
      location_aware = False
    elif d.keys() == location_keys:
      location_aware = True
    else:
      raise ValueError(
        f'Unexpected fields at chart: expected the default or location-aware roster, got {d.keys()}'
      )

    string_keys = ('gender', 'precision', 'backend', 'dayun_year_rule') + (
      () if location_aware else ('birth_time',)
    )
    for key in string_keys:
      if not isinstance(d[key], str):
        raise TypeError(f'Expected str at {key}, got {type(d[key])}')
    school = d['school']
    if not isinstance(school, Mapping):
      raise TypeError(f'Expected Mapping at school, got {type(school)}')

    birth: datetime | str
    longitude: float | None = None
    if location_aware:
      birth, longitude = _parse_location(d)
    else:
      birth = cast(str, d['birth_time'])

    config = BaziConfig.from_values(
      precision=cast(str, d['precision']),
      backend=cast(str, d['backend']),
      dayun_year_rule=cast(str, d['dayun_year_rule']),
      school=BaziSchool.from_json(school),
    )
    chart = cls(
      Bazi.create(
        birth,
        cast(str, d['gender']),
        config,
        longitude=longitude,
      ),
    )

    def __compare(actual: object, expected: object, path: str) -> None:
      if isinstance(expected, Mapping):
        if not isinstance(actual, Mapping):
          raise TypeError(f'Expected Mapping at {path}, got {type(actual)}')
        for key in actual:
          if type(key) is not str:
            raise TypeError(f'Expected str key at {path}, got {type(key)}')
        if actual.keys() != expected.keys():
          raise ValueError(f'Unexpected fields at {path}: {actual.keys() ^ expected.keys()}')
        for key, value in expected.items():
          __compare(actual[key], value, f'{path}.{key}')
      else:
        if type(actual) is not type(expected):
          raise TypeError(f'Expected {type(expected).__name__} at {path}, got {type(actual)}')
        if actual != expected:
          raise ValueError(f'Inconsistent value at {path}: {actual!r}; expected {expected!r}')

    __compare(d, chart.json, 'chart')
    return chart

  @property
  def bazi(self) -> Bazi:
    '''每次返回独立深拷贝；不使用 `cached_property`，避免调用方修改缓存中的共享 Bazi。'''
    return copy.deepcopy(self._bazi)

  @property
  def _utils(self) -> CalendarUtilsProtocol:
    '''
    每次访问时解析底层 Bazi 所用的历法工具，实例上不存 HKO 模块或 celestial 单例。
    不能改为 `cached_property`：存模块会使 deepcopy 失败，存单例会复制实例并分裂缓存。
    '''
    return calendar_utils_of(self._bazi.config.backend)
  
  @property
  def house_of_relationship(self) -> Dizhi:
    '''婚姻宫（配偶宫），即日柱地支。'''
    return self._bazi.day_pillar.dizhi
  
  @functools.cached_property
  def relationship_stars(self) -> GanzhiData[Tiangan, tuple[Dizhi, ...]]:
    '''夫妻星（配偶星）。

    目标干由 `BaziSchool.peiou_xing_def` 选定（`_peiou_xing_target`）；地支侧两读一致，
    取主气十神等于目标干十神的地支。对固定日主，`shishen` 在十干上是双射，
    「十神相等」与「主气等于目标干」等价。

    Usage:
    ```
    stars = chart.relationship_stars

    print(stars.tiangan) # 配偶星天干

    print(stars.dizhi)   # 配偶星地支元组
    assert 1 <= len(stars.dizhi) <= 2 # 对应一到两个地支
    ```
    '''
    target = _peiou_xing_target(
      self._bazi.day_master,
      self._bazi.gender,
      self._bazi.config.school.peiou_xing_def,
    )

    f = functools.partial(shishen, self._bazi.day_master)
    found_dz = tuple(filter(lambda dz : f(dz) is f(target), Dizhi))

    assert 1 <= len(found_dz) <= 2
    return GanzhiData(target, found_dz)

  PillarTraits = GanzhiData[TraitTuple, TraitTuple]
  @functools.cached_property
  def traits(self) -> BaziData[PillarTraits]:
    '''
    年、月、日、时的天干地支的阴阳和五行。

    Usage:
    ```
    traits = chart.traits
    
    print(traits.year.tiangan) # 年柱天干的阴阳五行
    assert traits.hour.dizhi == TraitTuple(Wuxing.木, Yinyang.阳) # 此例假设时支为寅

    for pillar_traits in traits: # 按年、月、日、时顺序遍历
      print(pillar_traits.tiangan) # 此柱天干的阴阳五行
      print(pillar_traits.dizhi)   # 此柱地支的阴阳五行
    ```
    '''
    # 四柱天干与地支的阴阳五行。
    tiangan_traits: list[TraitTuple] = [traits(tg) for tg in self._bazi.four_tiangans]
    dizhi_traits: list[TraitTuple] = [traits(dz) for dz in self._bazi.four_dizhis]
    pillar_data: list = [BaziChart.PillarTraits(tg_traits, dz_traits) for tg_traits, dz_traits in zip(tiangan_traits, dizhi_traits)]
    return BaziData(*pillar_data)
  
  @functools.cached_property
  def hidden_tiangan(self) -> BaziData[HiddenTianganDict]:
    '''
    当前八字的所有地支中的藏干。

    Usage:
    ```
    hidden = chart.hidden_tiangan

    print(hidden.year)  # 年支藏干
    print(hidden.month) # 月支藏干
    print(hidden.day)   # 日支藏干
    print(hidden.hour)  # 时支藏干

    for h in hidden: # 按年、月、日、时顺序遍历
      pass
    ```
    '''
    dizhi_hidden_tiangans: list[HiddenTianganDict] = [hidden_tiangans(dz) for dz in self._bazi.four_dizhis]
    return BaziData(*dizhi_hidden_tiangans)
  
  PillarShishens = GanzhiData[Shishen | None, Shishen]
  @functools.cached_property
  def shishen(self) -> BaziData[PillarShishens]:
    '''
    年、月、日、时柱的天干地支所对应的十神。注意，日主没有十神。

    Usage:
    ```
    shishens = chart.shishen

    print(shishens.year.tiangan) # 年干十神
    print(shishens.hour.dizhi)   # 时支十神

    for idx, pillar_shishens in enumerate(shishens):
      print(pillar_shishens.dizhi) # 此柱地支十神

      if idx == 2: # 跳过日主
        assert pillar_shishens.tiangan is None
        continue
      print(pillar_shishens.tiangan) # 此柱天干十神
    ```
    '''

    day_master: Tiangan = self._bazi.day_master

    shishen_list: list[BaziChart.PillarShishens] = []
    for pillar_idx, (tg, dz) in enumerate(self._bazi.pillars):
      tg_shishen: Shishen | None = shishen(day_master, tg)
      # 日主的十神位置存为 None。
      if pillar_idx == 2:
        tg_shishen = None

      dz_shishen: Shishen = shishen(day_master, dz)
      shishen_list.append(BaziChart.PillarShishens(tg_shishen, dz_shishen))

    assert len(shishen_list) == 4
    return BaziData(*shishen_list)
  
  @functools.cached_property
  def nayin(self) -> BaziData[str]:
    '''
    年、月、日、时柱的纳音。

    Usage:
    ```
    nayins = chart.nayin

    print(nayins.year) # 年柱纳音

    for nayin in nayins: # 按年、月、日、时顺序遍历
      print(nayin)
    ```
    '''

    nayin_list: list[str] = [nayin_str(gz) for gz in self._bazi.pillars]
    return BaziData(*nayin_list)
  
  @functools.cached_property
  def shier_zhangsheng(self) -> BaziData[ShierZhangsheng]:
    '''
    年、月、日、时柱的十二长生。

    Usage:
    ```
    zhangshengs = chart.shier_zhangsheng

    print(zhangshengs.day) # 日柱十二长生

    for zs in zhangshengs: # 按年、月、日、时顺序遍历
      pass
    ```
    '''

    day_master: Tiangan = self._bazi.day_master

    zhangsheng_list: list[ShierZhangsheng] = [shier_zhangsheng(day_master, gz.dizhi) for gz in self._bazi.pillars]
    return BaziData(*zhangsheng_list)
  
  @functools.cached_property
  def dayun_order(self) -> bool:
    '''
    `True` 代表大运是顺排的，`False` 代表大运是逆排的。

    Note: 传统表述以年干阴阳论「阳男阴女顺、阴男阳女逆」；本实现读年支阴阳，二者数学恒等价——
    六十甲子内干支的阴阳恒一致。
    '''
    is_male: bool = (self._bazi.gender is BaziGender.男)
    is_year_dz_yang: bool = (traits(self._bazi.year_pillar.dizhi).yinyang is Yinyang.阳)
    return is_male == is_year_dz_yang
  
  @functools.cached_property
  def dayun_start_moment(self) -> datetime:
    '''
    大运开始的时间 / 交运时间（公历）。

    地点盘返回东八区无时区标签，不是真太阳时。
    '''
    birthtime: Final[datetime] = self._bazi.reference_datetime

    def __gap() -> timedelta:
      # 各精度均从月柱所属节或下一节数起。
      prev_j, next_j = self._bazi.month_jies
      if self.dayun_order:
        return next_j.moment - birthtime
      # 相等归新，DAY/HOUR/MINUTE 的所属节真实时刻可晚于出生；逆数时将负间隔钳为零。
      return max(timedelta(0), birthtime - prev_j.moment)
    
    def __diff() -> timedelta:
      gap: Final[timedelta] = __gap()
      years: Final[float] = gap / timedelta(days=3) # 间隔三日折一年。
      return years * timedelta(days=365) # 按一年 365 日换算。
    
    return birthtime + __diff()

  def _dayun_owning_ganzhi_year(self, moment: datetime) -> int:
    '''按所属节返回 `moment` 所在的干支年。'''
    assert isinstance(moment, datetime)
    return GanzhiYearMonth.from_jie(self._utils.prev_jie(moment)).year

  @property
  def _dayun_empty_timeline_message(self) -> str:
    '''返回大运时刻线无受支持起点时的共享报错消息。'''
    first, last = self._utils.supported_jie_boundaries()
    return f'No Dayun starts within the supported Jie range [{first}, {last})'

  @functools.cached_property
  def _dayun_first_year_label(self) -> int:
    '''
    两种年份投影共用的首步大运年份标签，不受后续年份投影规则影响。
    提前归属立春的命盘已归新年，钳在出生时刻的首运却可能仍在物理旧年。
    首步标签取出生干支年为下限；JIE_PROJECTED 后续标签独立按真实起点投影，
    FIXED_DECADE 后续标签按首标签每步递增 10 年。
    '''
    first, last = self._utils.supported_jie_boundaries()
    first_start_moment: Final[datetime] = self._dayun_start_moment_at(0)
    if not first <= first_start_moment < last:
      raise ValueError(self._dayun_empty_timeline_message)
    return max(self._dayun_owning_ganzhi_year(first_start_moment), self._bazi.ganzhi_year)

  def _dayun_start_moment_at(self, index: int) -> datetime:
    '''从首运边界重算第 `index` 个边界；目标平年把 2 月 29 日压到 2 月 28 日。'''
    assert isinstance(index, int)
    assert index >= 0

    start: Final[datetime] = self.dayun_start_moment
    year: Final[int] = start.year + 10 * index
    day: Final[int] = min(start.day, monthrange(year, start.month)[1])
    return start.replace(year=year, day=day)

  @property
  def dayun(self) -> Generator[DayunTuple, None, None]:
    '''
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
    全部小运的元组。

    Usage:
    ```
    chart: BaziChart = BaziChart(bazi)

    for xusui_age, ganzhi in chart.xiaoyun:
      print(f'虚岁: {xusui_age}, 小运: {ganzhi}')
    ```
    '''

    step: Final[int] = 1 if self.dayun_order else -1
    # 小运覆盖首步大运前的虚岁；差值两端均按命盘自身归属取年，见 _dayun_first_year_label。
    # 因此小运数量不小于一。
    until_xusui_age: Final[int] = 1 + self._dayun_first_year_label - self._bazi.ganzhi_year

    def __xiaoyun_at_age(age: int) -> XiaoyunTuple:
      return XiaoyunTuple(age, self._bazi.hour_pillar.next(age * step))

    return tuple(__xiaoyun_at_age(age) for age in range(1, until_xusui_age + 1))
  
  @property
  def liunian(self) -> Generator[LiunianTuple, None, None]:
    '''
    流年生成器（无限）。

    Usage:
    ```
    chart: BaziChart = BaziChart(bazi)

    for year, ganzhi in chart.liunian: # 无限生成器
      print(year, ganzhi) # 如 "2024 甲辰"
    ```
    '''

    def __liunian_generator() -> Generator[LiunianTuple, None, None]:
      # 从按出生精度归属的 Bazi.ganzhi_year 起，与年柱同源，首个流年干支始终等于年柱。
      year: int = self._bazi.ganzhi_year
      while True:
        yield LiunianTuple(year, ganzhi_of_year(year))
        year += 1
    return __liunian_generator()

  @property
  def json(self) -> BaziJson.BaziChartJsonDict:
    '''
    此命盘的 JSON 字典。
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

    config = _config_json(self._bazi.config)
    f = BaziJson.gen_fourpillars
    common: BaziJson._CommonChartJsonDict = {
      'gender': str(self._bazi.gender),
      'precision': config['precision'],
      'backend': config['backend'],
      'dayun_year_rule': config['dayun_year_rule'],
      'school': cast(BaziJson.School, config['school']),
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
    location_time = self._bazi.location_time
    if location_time is None:
      return {
        'birth_time': self._bazi.solar_datetime.isoformat(),
        **common,
      }
    return {
      **location_time.json,
      **common,
    }

命盘 = BaziChart
