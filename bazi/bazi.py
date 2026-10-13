# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import math
import random
from random import Random

from enum import Enum
from dataclasses import dataclass
from collections.abc import Mapping
from datetime import UTC, date, time, datetime, timedelta, timezone, tzinfo
from typing import Final, NamedTuple, TypedDict

from .common import frozendict
from .defines import Tiangan, Dizhi, Ganzhi
from .calendar import (
  CalendarDate, CalendarType, CalendarUtilsProtocol, CalendarBackend, calendar_utils_of, JieqiTime,
)
from .calendar.celestial_data.loader import _EquationOfTimeRangeError
from .calendar.dates import GanzhiYearMonth
from .calendar import solar_time
from .school import BaziPrecision, BaziConfig, DEFAULT_CONFIG

from .utils.bazi_utils import (
  month_tiangan, hour_tiangan, ganzhi_of_year,
  _ganzhi_of_day_at_moment,
)


_UTC8: Final[timezone] = timezone(timedelta(hours=8))


@dataclass(frozen=True)
class _Location:
  '''冻结的绝对出生时刻、民用偏移及经度。'''
  instant: datetime
  civil_offset: timedelta
  longitude: float

  @property
  def civil(self) -> datetime:
    return self.instant.astimezone(timezone(self.civil_offset))

  def apparent(self, instant: datetime) -> datetime:
    '''把带时区瞬间投到同一经度及冻结的出生地区偏移。'''
    return solar_time.apparent_solar_datetime(instant.astimezone(timezone(self.civil_offset)), self.longitude)


class BaziGender(Enum):
  '''
  排盘使用的性别。
  '''
  YANG = '男'
  YIN = '女'

  MALE = YANG
  FEMALE = YIN

  男 = YANG # noqa: PIE796 # 有意保留中文别名。
  女 = YIN # noqa: PIE796 # 有意保留中文别名。

  阳 = YANG # noqa: PIE796 # 有意保留中文别名。
  阴 = YIN # noqa: PIE796 # 有意保留中文别名。

  乾 = YANG # noqa: PIE796 # 有意保留中文别名。
  坤 = YIN # noqa: PIE796 # 有意保留中文别名。

  def __str__(self) -> str:
    if self is self.MALE:
      return 'male'
    else:
      assert self is self.FEMALE
      return 'female'



_GENDER_ALIASES: Final[frozendict[str, BaziGender]] = frozendict({
  '男': BaziGender.MALE,   'male': BaziGender.MALE,
  '女': BaziGender.FEMALE, 'female': BaziGender.FEMALE,
})


def _truncated(dt: datetime, precision: BaziPrecision) -> datetime:
  '''
  把时刻截断到 `precision` 粒度单位的起点，按 `BaziPrecision` 比较（`birth >= jieqi`，相等归新）。

  Note:
  - HOUR 截到时辰起点（23、1、3、…、21 点），保留完整日期时刻。子时跨午夜，
    当日 23:30 应排在亥时之后，不能用日内时辰序号比较。
  - MINUTE 去掉秒及更细部分。
  - 此处不支持 DAY；DAY 经 `to_ganzhi` 按日期比较。

  Args:
  - dt: (datetime) 待截断时刻。
  - precision: (BaziPrecision) `HOUR` 或 `MINUTE`。

  Return: (datetime) `dt` 所属粒度单位的起点。
  '''

  assert isinstance(dt, datetime)
  assert precision in (BaziPrecision.HOUR, BaziPrecision.MINUTE)

  if precision is BaziPrecision.MINUTE:
    return dt.replace(second=0, microsecond=0)

  # 先加一小时，使时辰起点落在偶数小时上，向下取整后再移回。
  shifted: Final[datetime] = dt + timedelta(hours=1)
  return datetime.combine(shifted.date(), time(shifted.hour - (shifted.hour % 2))) - timedelta(hours=1)


class Bazi:
  '''
  存储年、月、日、时四柱及排盘基本信息。十神、大运等派生信息见 `bazi_chart.py` 的 `BaziChart`。

  Note:
  - 默认路径直接采用无时区民用时刻；传入 `longitude` 才会从调用方给定的带时区时刻换算真太阳时。
  - 本库从立春派：年柱以立春换年，不以正月初一（春节）换年。
  '''

  def __init__(
    self,
    birth_time: datetime,
    gender: BaziGender,
    config: BaziConfig = DEFAULT_CONFIG,
    *,
    longitude: float | None = None,
    civil_timezone: tzinfo | None = None,
  ) -> None:
    '''
    根据出生时间和性别计算年、月、日、时四柱。
    
    Note:
    - 不传 `longitude` 时，`birth_time` 必须是不带时区的时刻，采用默认路径。
    - 传入 `longitude` 时，`birth_time` 必须带时区；时区、夏令时折叠与历史偏移由调用方负责，
      换算、身份与 JSON 保留秒及微秒，HOUR/MINUTE 归属按截断后的真太阳时比较。
    
    Args:
    - birth_time: (datetime) 无时区民用时刻；给定 `longitude` 时为带时区的绝对瞬间。
    - gender: (BaziGender) 性别。
    - config: (BaziConfig) 出生精度、历法后端、流派档案及默认大运年份投影。
    - longitude: (float | None) 东经为正的角度，范围 `[-180, 180]`。地点路径只支持
      `CalendarBackend.CELESTIAL` 的 `HOUR` 或 `MINUTE` 精度。
    - civil_timezone: (tzinfo | None) 出生地民用时区基准，默认采用输入时区；
      冻结出生瞬间的实际偏移，时区规则与有效性由调用方负责。
    '''

    if not isinstance(birth_time, datetime):
      raise TypeError(f'Expected datetime, got {type(birth_time)}')
    if not isinstance(gender, BaziGender):
      raise TypeError(f'Expected BaziGender, got {type(gender)}')
    if not isinstance(config, BaziConfig):
      raise TypeError(f'Expected BaziConfig, got {type(config)}')
    if civil_timezone is not None:
      if not isinstance(civil_timezone, tzinfo):
        raise TypeError(f'Expected tzinfo, got {type(civil_timezone)}')
      if longitude is None:
        raise ValueError('civil_timezone requires longitude.')

    longitude_value = None if longitude is None else solar_time._canonical_longitude(longitude)

    if longitude_value is None:
      if birth_time.tzinfo is not None:
        raise ValueError('Timezone-aware birth_time requires longitude.')
    else:
      if birth_time.tzinfo is None or birth_time.utcoffset() is None:
        raise ValueError('Longitude requires a timezone-aware birth_time.')
      if config.backend is not CalendarBackend.CELESTIAL:
        raise ValueError('Longitude requires CalendarBackend.CELESTIAL.')
      if config.precision not in (BaziPrecision.HOUR, BaziPrecision.MINUTE):
        raise ValueError('Longitude requires BaziPrecision.HOUR or BaziPrecision.MINUTE.')

    location: _Location | None = None
    clock_datetime = birth_time
    if longitude_value is not None:
      try:
        canonical_utc = birth_time.astimezone(UTC)
        selected = canonical_utc.astimezone(birth_time.tzinfo if civil_timezone is None else civil_timezone)
        offset = selected.utcoffset()
        if offset is None:
          raise ValueError('civil_timezone requires a UTC offset at birth.')
        location = _Location(canonical_utc, offset, longitude_value)

        clock_datetime = location.apparent(canonical_utc)
      except (_EquationOfTimeRangeError, OverflowError) as error:
        window_utils = calendar_utils_of(config.backend)
        first = window_utils.to_date(window_utils.get_min_supported_date(CalendarType.SOLAR))
        last = window_utils.to_date(window_utils.get_max_supported_date(CalendarType.SOLAR))
        raise ValueError(f'Unsupported apparent-solar birth date: expected [{first}, {last}].') from error

    self._config: Final[BaziConfig] = config
    self._location: Final[_Location | None] = location
    self._clock_datetime: Final[datetime] = clock_datetime

    utils: Final[CalendarUtilsProtocol] = calendar_utils_of(config.backend)
    # to_solar 同时检查支持窗口；超出窗口的出生时刻在此抛 ValueError。
    self._solar_date: Final[CalendarDate] = utils.to_solar(self._clock_datetime)

    self._gender: Final[BaziGender] = gender

    # 按 BaziPrecision 判断出生干支年月：已知粒度下 birth >= jieqi，相等归新。
    year_month: GanzhiYearMonth
    month_jies: tuple[JieqiTime, JieqiTime]
    if self._config.precision is BaziPrecision.DAY:
      # DAY 的日期级年月也决定大运数节所用的节。
      ganzhi_calendardate: CalendarDate = utils.to_ganzhi(self._solar_date)
      year_month = GanzhiYearMonth(ganzhi_calendardate.year, ganzhi_calendardate.month)
      solar_year, jie = year_month.opening_jie
      owning_jie = JieqiTime(jie, utils.jieqi_moment(solar_year, jie))
      month_jies = (owning_jie, utils.next_jie(owning_jie.moment))
    else:
      if self._config.backend is CalendarBackend.HKO:
        raise ValueError(
          f'{self._config.precision} needs real jieqi moments, which the HKO backend cannot provide '
          '(its `jieqi_moment` is a midnight placeholder). Use `CalendarBackend.CELESTIAL`.'
        )

      # 截断单调，出生截断值不会超过下一节截断值，>= 只可能相等，此时归下一节。
      # 真实节时刻可晚于出生最多一个粒度单位；子时跨午夜，HOUR 的相等窗口可始于前一民用日。
      birth_moment: Final[datetime] = self.reference_datetime
      prev_j: Final[JieqiTime] = utils.prev_jie(birth_moment)
      next_j: Final[JieqiTime] = utils.next_jie(birth_moment)

      attribution_birth: datetime = birth_moment
      attribution_jie: datetime = next_j.moment
      if location is not None:
        attribution_birth = self._clock_datetime
        attribution_jie = location.apparent(next_j.moment.replace(tzinfo=_UTC8))

      if _truncated(attribution_birth, self._config.precision) >= _truncated(attribution_jie, self._config.precision):
        month_jies = (next_j, utils.next_jie(next_j.moment))
      else:
        month_jies = (prev_j, next_j)

      # 年月由所属节推出，与 BaziChart 经 month_jies 读取的来源一致。
      # 小寒开启上一干支年的末月，此公历年的立春尚未到来。
      owning: Final[JieqiTime] = month_jies[0]
      year_month = GanzhiYearMonth.from_jie(owning)

    self._month_jies: Final[tuple[JieqiTime, JieqiTime]] = month_jies
    self._ganzhi_year_month: Final[GanzhiYearMonth] = year_month

    # 年柱。
    self._ganzhi_year: Final[int] = year_month.year
    self._year_pillar: Final[Ganzhi] = ganzhi_of_year(self._ganzhi_year)

    # 干支月及月令。
    self._month_dizhi: Final[Dizhi] = year_month.dizhi

    # 日柱按所选换日点判断；年/月归属独立按 BaziPrecision 判断。
    self._day_pillar: Final[Ganzhi] = _ganzhi_of_day_at_moment(
      self._clock_datetime,
      self._config.school.day_rollover,
    )

    # 时柱地支。
    self._hour_dizhi: Final[Dizhi] = Dizhi.from_index((self._clock_datetime.hour + 1) // 2 % 12)

  @staticmethod
  def __parse_bazi_args(
    birth_time: datetime | str,
    gender: BaziGender | str,
  ) -> tuple[datetime, BaziGender]:

    assert isinstance(birth_time, (datetime, str))
    _birth_time: datetime = birth_time if isinstance(birth_time, datetime) else datetime.fromisoformat(birth_time)

    assert isinstance(gender, (BaziGender, str))
    try:
      _gender = _GENDER_ALIASES[gender.lower()] if isinstance(gender, str) else gender
    except KeyError:
      raise ValueError(f'Currently not support gender: {gender}') from None

    return _birth_time, _gender

  @staticmethod
  def create(
    birth_time: datetime | str,
    gender: BaziGender | str,
    config: BaziConfig = DEFAULT_CONFIG,
    *,
    longitude: float | None = None,
    civil_timezone: tzinfo | None = None,
  ) -> 'Bazi':
    '''
    从出生输入创建 `Bazi`。

    Args:
    - birth_time: (datetime | str) 公历出生时刻；字符串经 `datetime.fromisoformat` 解析。
      未给经度时须无时区，给定经度时须带时区。
    - gender: (BaziGender | str) 性别枚举，或 "男"/"女"/"male"/"female"（大小写不敏感）。
    - config: (BaziConfig) 出生精度、历法后端、流派档案及大运年份投影；
      可用 `BaziConfig.from_values` 从字符串构造。
    - longitude: (float | None) 东经为正的经度，显式启用带时区输入的真太阳时路径；不使用纬度。
    - civil_timezone: (tzinfo | None) 显式出生地民用时区基准，冻结出生瞬间的实际偏移。
    '''

    if not isinstance(birth_time, (datetime, str)):
      raise TypeError(f'Expected datetime or str, got {type(birth_time)}')
    if not isinstance(gender, (BaziGender, str)):
      raise TypeError(f'Expected BaziGender or str, got {type(gender)}')
    if not isinstance(config, BaziConfig):
      raise TypeError(f'Expected BaziConfig, got {type(config)}')

    _birth_time, _gender = Bazi.__parse_bazi_args(birth_time, gender)
    bazi: Bazi = Bazi(
      birth_time=_birth_time,
      gender=_gender,
      config=config,
      longitude=longitude,
      civil_timezone=civil_timezone,
    )
    return bazi
  
  @staticmethod
  def random(config: BaziConfig = DEFAULT_CONFIG, *, rng: Random | None = None) -> 'Bazi':
    '''
    随机生成一个 `Bazi`，主要用于测试。

    Note:
    - 年份范围为 [1902, 2080]，日期范围为 [1, 28]。
    - 指定局部 `rng` 可重放样本且不改变全局随机状态；省略时沿用 `random` 模块的种子语义。

    Args:
    - config: (BaziConfig) 命盘级配置，传给 `Bazi.create`。
    - rng: (Random | None) 局部随机源；`None` 使用 `random` 模块。

    Return: (Bazi) 随机八字。
    '''
    if rng is not None and not isinstance(rng, Random):
      raise TypeError(f'Expected Random, got {type(rng)}')
    source = random if rng is None else rng
    return Bazi.create(
      birth_time=datetime(
        year=source.randint(1902, 2080),
        month=source.randint(1, 12),
        day=source.randint(1, 28),
        hour=source.randint(0, 23),
        minute=source.randint(0, 59),
      ),
      gender=source.choice(list(BaziGender)),
      config=config,
    )

  @property
  def solar_date(self) -> date:
    '''地点盘的真太阳时公历出生日期；默认路径为民用日期。'''
    return self._utils.to_date(self._solar_date)
  
  @property
  def ganzhi_date(self) -> CalendarDate:
    '''
    干支历出生日期。

    Note: 此入口只按日期归属。HOUR / MINUTE 精度下，交节相等窗口内可与
    `ganzhi_year` 及年/月柱不同；需要出生精度归属时使用 `ganzhi_year`。
    '''
    return self._utils.to_ganzhi(self._solar_date)

  @property
  def ganzhi_year(self) -> int:
    '''
    按 `self.config.precision` 归属的出生干支年；年柱为此年的 `ganzhi_of_year`。
    '''
    return self._ganzhi_year

  @property
  def ganzhi_year_month(self) -> GanzhiYearMonth:
    '''按出生精度归属的干支年月；年/月柱与大运数节共同使用此坐标。'''
    return self._ganzhi_year_month

  @property
  def month_jies(self) -> tuple[JieqiTime, JieqiTime]:
    '''
    按 `self.config.precision` 归属的开月节与下一节，供年/月柱和大运数节共同使用。

    Note:
    - `[0]` 是出生月所属节，`[1]` 是其下一节，均保留后端原始节时刻。
    - DAY 的整个交节日归新；HOUR/MINUTE 按各自粒度相等归新。提前归属窗口中，
      所属节的真实时刻可以在出生之后；逆排大运的负间隔钳为零。
    - 真实出生时刻前后节仍应以 `reference_datetime` 查询历法 `prev_jie` / `next_jie`。
    '''
    return self._month_jies

  @property
  def hour(self) -> int:
    return self._clock_datetime.hour

  @property
  def minute(self) -> int:
    return self._clock_datetime.minute

  @property
  def longitude(self) -> float | None:
    '''地点盘采用的东经为正经度；默认路径返回 `None`。'''
    return None if self._location is None else self._location.longitude

  @property
  def solar_datetime(self) -> datetime:
    '''出生时刻截断到最细排盘精度（分钟）。默认盘以此民用标签参与身份、JSON 及历法坐标；
    地点盘显示由完整输入精度换算得到的真太阳时。'''
    return self._clock_datetime.replace(second=0, microsecond=0)

  @property
  def reference_datetime(self) -> datetime:
    '''节表、大运及流运查询的出生参考时刻。

    地点盘返回保留秒/微秒的 naive UTC+08 标签；默认盘返回分钟截断的民用标签。
    此坐标不是真太阳钟，也不改变出生精度的归属规则。
    '''
    if self._location is None:
      return self.solar_datetime
    return self._location.instant.astimezone(_UTC8).replace(tzinfo=None)

  @property
  def location_time(self) -> 'LocationTime | None':
    '''地点盘的只读时间事实；默认盘返回 `None`。

    包含绝对 UTC 瞬间、固定出生偏移的民用钟、经度及未截断真太阳钟；
    `solar_datetime` 仍只显示分钟，`reference_datetime` 仍用于节表坐标。
    '''
    if self._location is None:
      return None
    return LocationTime(
      self._location.instant,
      self._location.civil,
      self._location.longitude,
      self._clock_datetime,
    )

  @property
  def gender(self) -> BaziGender:
    return self._gender
  
  @property
  def config(self) -> BaziConfig:
    '''此命盘的配置：出生精度、历法后端、流派档案及默认大运年份投影。'''
    return self._config

  @property
  def _utils(self) -> CalendarUtilsProtocol:
    '''
    每次访问时解析当前后端的历法工具，实例上不存 HKO 模块或 celestial 单例。
    不能改为 `cached_property`：存模块会使 deepcopy 失败，存单例会复制实例并分裂缓存。
    '''
    return calendar_utils_of(self._config.backend)
  
  @property
  def four_dizhis(self) -> tuple[Dizhi, Dizhi, Dizhi, Dizhi]:
    '''
    按年、月、日、时顺序返回四柱地支。
    '''
    return (self._year_pillar.dizhi, self._month_dizhi, 
            self._day_pillar.dizhi, self._hour_dizhi,)
  
  @property
  def four_tiangans(self) -> tuple[Tiangan, Tiangan, Tiangan, Tiangan]:
    '''
    按年、月、日、时顺序返回四柱天干。
    '''
    return (self._year_pillar.tiangan, month_tiangan(self._year_pillar.tiangan, self._month_dizhi), 
            self._day_pillar.tiangan, hour_tiangan(self._day_pillar.tiangan, self._hour_dizhi))
  
  @property
  def day_master(self) -> Tiangan:
    '''
    日主，即日柱天干。
    '''
    return self._day_pillar.tiangan

  @property
  def month_commander(self) -> Dizhi:
    '''
    月令，即月柱地支。
    '''
    return self._month_dizhi

  @property
  def year_pillar(self) -> Ganzhi:
    '''
    年柱干支。
    '''
    return self._year_pillar
  
  @property
  def month_pillar(self) -> Ganzhi:
    '''
    月柱干支。
    '''
    tg: Tiangan = month_tiangan(self._year_pillar.tiangan, self._month_dizhi)
    return Ganzhi(tg, self._month_dizhi)
  
  @property
  def day_pillar(self) -> Ganzhi:
    '''
    日柱干支。
    '''
    return self._day_pillar
  
  @property
  def hour_pillar(self) -> Ganzhi:
    '''
    时柱干支。
    '''
    tg: Tiangan = hour_tiangan(self._day_pillar.tiangan, self._hour_dizhi)
    return Ganzhi(tg, self._hour_dizhi)
  
  @property
  def pillars(self) -> tuple[Ganzhi, Ganzhi, Ganzhi, Ganzhi]:
    '''
    按年、月、日、时顺序返回四柱干支。
    '''
    tgs: tuple[Tiangan, Tiangan, Tiangan, Tiangan] = self.four_tiangans
    dzs: tuple[Dizhi, Dizhi, Dizhi, Dizhi] = self.four_dizhis
    return (
      Ganzhi(tgs[0], dzs[0]),
      Ganzhi(tgs[1], dzs[1]),
      Ganzhi(tgs[2], dzs[2]),
      Ganzhi(tgs[3], dzs[3]),
    )
  
  @property
  def _identity(self) -> tuple[datetime | _Location, BaziGender, BaziConfig]:
    '''默认盘身份采用分钟时刻；地点盘身份采用精确瞬间、冻结民用偏移及规范经度，
    均结合性别与配置。'''
    return (self.solar_datetime if self._location is None else self._location, self.gender, self.config)

  def __eq__(self, other: object) -> bool:
    return isinstance(other, Bazi) and self._identity == other._identity

  def __hash__(self) -> int:
    # 身份派生自 `Final` 状态，在公开 API 下稳定。
    return hash(self._identity)


class LocationTimeJson(TypedDict):
  '''规范地点输入及未截断的计算真太阳时。'''
  time_basis: str
  civil_time: str
  canonical_instant: str
  longitude: float
  apparent_time: str


class LocationTime(NamedTuple):
  '''模型返回的不可变地点时间事实；时间值不经 JSON 解析或重复换算。

  `canonical_instant` 带 UTC 时区，`civil_time` 带固定出生偏移，
  `apparent_time` 为未截断的 naive 真太阳钟。直接构造此值不验证排盘输入。
  '''
  canonical_instant: datetime
  civil_time: datetime
  longitude: float
  apparent_time: datetime

  @property
  def json(self) -> LocationTimeJson:
    '''供命盘与情境记录共用的 JSON 时间字段；每次返回独立字典。'''
    return {
      'time_basis': 'apparent_solar',
      'civil_time': self.civil_time.isoformat(),
      'canonical_instant': self.canonical_instant.isoformat(),
      'longitude': self.longitude,
      'apparent_time': self.apparent_time.isoformat(),
    }


def _parse_location(data: Mapping[str, object]) -> tuple[datetime, float]:
  '''验证规范拼写及民用／UTC 表示指向同一瞬间。'''
  basis = data['time_basis']
  if type(basis) is not str:
    raise TypeError(f'Expected str at time_basis, got {type(basis)}')
  if basis != 'apparent_solar':
    raise ValueError(f'Unsupported time_basis: {basis}')

  moments: dict[str, datetime] = {}
  for key in ('civil_time', 'canonical_instant', 'apparent_time'):
    value = data[key]
    if type(value) is not str:
      raise TypeError(f'Expected str at {key}, got {type(value)}')
    moment = datetime.fromisoformat(value)
    if moment.isoformat() != value:
      raise ValueError(f'Expected canonical datetime at {key}')
    moments[key] = moment

  civil = moments['civil_time']
  if civil.utcoffset() is None:
    raise ValueError('Expected fixed-offset aware civil_time')
  instant = moments['canonical_instant']
  if instant.utcoffset() is None or instant.utcoffset() != UTC.utcoffset(instant):
    raise ValueError('Expected canonical UTC instant')
  if instant != civil:
    raise ValueError('Inconsistent civil_time and canonical_instant')
  if moments['apparent_time'].tzinfo is not None:
    raise ValueError('Expected naive apparent_time')

  longitude = data['longitude']
  if type(longitude) is not float:
    raise TypeError(f'Expected float at longitude, got {type(longitude)}')
  if (not math.isfinite(longitude) or not -180 <= longitude < 180
      or (longitude == 0 and math.copysign(1.0, longitude) < 0)):
    raise ValueError(f'Expected canonical longitude in [-180, 180), got {longitude}')

  return civil, longitude

八字 = Bazi
