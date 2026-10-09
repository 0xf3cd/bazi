# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import math
import random

from enum import Enum
from numbers import Real
from dataclasses import dataclass
from collections.abc import Mapping
from datetime import UTC, date, time, datetime, timedelta, timezone, tzinfo
from typing import Final, TypedDict

from .defines import Tiangan, Dizhi, Ganzhi
from .calendar import (
  CalendarDate, CalendarUtilsProtocol, CalendarBackend, calendar_utils_of, JieqiTime,
)
from .school import BaziPrecision, BaziConfig, DEFAULT_CONFIG

from .utils.bazi_utils import (
  month_tiangan, hour_tiangan, ganzhi_of_year,
  _ganzhi_of_day_at_moment, _ganzhi_year_month_of_jie, _ganzhi_month_dizhi,
)


_UTC8: Final[timezone] = timezone(timedelta(hours=8))


@dataclass(frozen=True)
class _Location:
  '''Frozen absolute birth instant, civil offset and longitude.
  冻结的绝对出生时刻、民用偏移及经度。'''
  instant: datetime
  civil_offset: timedelta
  longitude: float


def _apparent_datetime(civil_instant: datetime, longitude: float) -> datetime:
  '''Load EOT only for location-aware projections. / 仅在地点盘投影时加载 EOT。'''
  from .calendar.solar_time import apparent_solar_datetime
  return apparent_solar_datetime(civil_instant, longitude)


class BaziGender(Enum):
  '''
  BaziGender is used to specify the gender of the person.
  '''
  YANG = '男'
  YIN = '女'

  # Aliases
  MALE = YANG
  FEMALE = YIN

  男 = YANG # noqa: PIE796 # deliberate alias
  女 = YIN # noqa: PIE796 # deliberate alias

  阳 = YANG # noqa: PIE796 # deliberate alias
  阴 = YIN # noqa: PIE796 # deliberate alias

  乾 = YANG # noqa: PIE796 # deliberate alias
  坤 = YIN # noqa: PIE796 # deliberate alias

  def __str__(self) -> str:
    if self is self.MALE:
      return 'male'
    else:
      assert self is self.FEMALE
      return 'female'



def _truncated(dt: datetime, precision: BaziPrecision) -> datetime:
  '''
  Truncate `dt` to the start of `precision`'s granularity unit, so that two truncated values
  compare per the `BaziPrecision` rule (`birth >= jieqi`, ties go new).
  把时刻截断到 `precision` 粒度单位的起点，截断后的两个时刻即可按 `BaziPrecision` 规则比较。

  Note:
  - HOUR truncates to the start of the 时辰 (the odd clock hours: 23, 1, 3, ..., 21). The
    start is a full datetime, not a (date, 时辰-index) pair: 子时 spans midnight, so a 23:30
    birth must order *after* the same day's 亥时 -- an in-day index would order it first.
  - MINUTE drops seconds and below.
  - DAY is deliberately unsupported here: it compares dates via the `to_ganzhi` channel.

  Args:
  - dt: (datetime) The moment to truncate.
  - precision: (BaziPrecision) `HOUR` or `MINUTE`.

  Return: (datetime) The start of the granularity unit containing `dt`.
  '''

  assert isinstance(dt, datetime)
  assert precision in (BaziPrecision.HOUR, BaziPrecision.MINUTE)

  if precision is BaziPrecision.MINUTE:
    return dt.replace(second=0, microsecond=0)

  # Shift by 1 hour so 时辰 starts land on the even-hour grid, floor, then shift back.
  shifted: Final[datetime] = dt + timedelta(hours=1)
  return datetime.combine(shifted.date(), time(shifted.hour - (shifted.hour % 2))) - timedelta(hours=1)


class Bazi:
  '''
  `Bazi` (八字) is the class that only stores very basic information.
  A `Bazi` object stores 4 pillars of year, month, day, and hour.
  For all other information (transits / shishen / ...), please see `bazi/bazi_chart.py` (e.g. `BaziChart`).

  八字是仅存储基本信息的类。一个 `Bazi` 对象存储着年、月、日、时的四柱八个字。
  对于其他信息（流年大运 / 十神等），请参阅 `bazi/bazi_chart.py`（例如 `BaziChart`）。

  Note:
  - The default path takes a naive civil time exactly as before. Passing `longitude`
    opts into apparent-solar conversion from a caller-supplied aware instant.
  - The year pillar turns at 立春, not at 正月初一 (this library follows the 立春 school).
  - 默认路径仍直接采用无时区民用时刻；传入 `longitude` 才会从调用方给定的带时区时刻换算真太阳时。
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
    `Bazi` (i.e. 八字, which means eight characters in Chinese) takes the birth time and gender as input, 
    and figures out the pillars of year, month, day, and hour.
    `Bazi` 接受出生时间和性别作为输入，计算年、月、日、时的八字。
    
    Note:
    - Without `longitude`, `birth_time` must be naive and follows the legacy path.
    - With `longitude`, `birth_time` must be aware. Its timezone, DST fold and historical
      offset are caller-owned. Seconds and microseconds are retained for conversion,
      identity and JSON; HOUR/MINUTE attribution compares apparent-solar buckets.
    - 不传 `longitude` 时，`birth_time` 必须是不带时区的时刻，并沿用原有路径。
    - 传入 `longitude` 时，`birth_time` 必须带时区；时区、夏令时折叠与历史偏移由调用方负责，
      换算、身份与 JSON 保留秒及微秒，HOUR/MINUTE 归属按真太阳时精度桶比较。
    
    Args:
    - birth_time: (datetime) A naive legacy civil time, or an aware absolute instant when
      `longitude` is provided.
    - gender: (BaziGender) The gender of the person.
    - config: (BaziConfig) The chart-level configuration: birth-time precision, calendar
      backend, school profile (流派档案), and default Dayun year projection.
    - longitude: (float | None) East-positive degrees in `[-180, 180]`. This opt-in path
      supports only `CalendarBackend.CELESTIAL` with `HOUR` or `MINUTE` precision.
    - civil_timezone: (tzinfo | None) Birth-region basis, defaulting to the input timezone.
      Its actual offset at birth is frozen; region rules and validity are caller-owned.
      出生地民用时区基准，默认采用输入时区；冻结出生瞬间的实际偏移，时区规则与有效性由调用方负责。
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

    longitude_value: float | None = None
    if longitude is not None:
      longitude_input: object = longitude
      if isinstance(longitude_input, bool) or not isinstance(longitude_input, Real):
        raise TypeError(f'Expected real longitude, got {type(longitude)}')
      try:
        longitude_value = float(longitude_input)
      except OverflowError as error:
        raise ValueError('Longitude is outside [-180, 180].') from error
      if not math.isfinite(longitude_value):
        raise ValueError(f'Longitude must be finite, got {longitude}')
      if not -180 <= longitude_value <= 180:
        raise ValueError(f'Longitude is outside [-180, 180]: {longitude}')
      if longitude_value == 0:
        # JSON has one zero spelling, including when the input is -0.0.
        longitude_value = 0.0
      if longitude_value == 180:
        longitude_value = -180.0

    if longitude_value is None:
      if birth_time.tzinfo is not None:
        raise ValueError('Timezone should be well-processed outside of this class.')
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
      canonical_utc = birth_time.astimezone(UTC)
      selected = canonical_utc.astimezone(birth_time.tzinfo if civil_timezone is None else civil_timezone)
      offset = selected.utcoffset()
      if offset is None:
        raise ValueError('civil_timezone requires a UTC offset at birth.')
      location = _Location(canonical_utc, offset, longitude_value)
      civil_datetime = canonical_utc.astimezone(timezone(offset))
      clock_datetime = _apparent_datetime(civil_datetime, longitude_value)

    self._config: Final[BaziConfig] = config
    self._location: Final[_Location | None] = location
    self._clock_datetime: Final[datetime] = clock_datetime

    utils: Final[CalendarUtilsProtocol] = calendar_utils_of(config.backend)
    # `to_solar` is also the window gate: an out-of-window birth time raises ValueError here.
    self._solar_date: Final[CalendarDate] = utils.to_solar(self._clock_datetime)

    self._gender: Final[BaziGender] = gender

    # Which ganzhi year / month owns the birth, compared per `BaziPrecision`
    # (`birth >= jieqi` at the known granularity, ties go new).
    ganzhi_year: int
    ganzhi_month: int
    bracketing_jies: tuple[JieqiTime, JieqiTime] | None = None
    if self._config.precision is BaziPrecision.DAY:
      # DAY compares dates: the `to_ganzhi` channel drops the time, so a jieqi's whole day
      # falls on its new side. `bracketing_jies` stays moment-level for DAY (see the property).
      ganzhi_calendardate: CalendarDate = utils.to_ganzhi(self._solar_date)
      ganzhi_year = ganzhi_calendardate.year
      ganzhi_month = ganzhi_calendardate.month # `ganzhi_calendardate` is already at `DAY`-level precision.
    else:
      if self._config.backend is CalendarBackend.HKO:
        raise ValueError(
          f'{self._config.precision} needs real jieqi moments, which the HKO backend cannot provide '
          '(its `jieqi_moment` is a midnight placeholder). Use `CalendarBackend.CELESTIAL`.'
        )

      # The truncated birth can never exceed the truncated next jie (truncation is monotone),
      # so `>=` can only hit as a tie -- in which case the next jie owns the birth month, and
      # its true moment may be up to one granularity unit after the birth (子时 spans midnight,
      # so for HOUR the tie window may even start on the previous civil day).
      birth_moment: Final[datetime] = self._reference_datetime
      prev_j: Final[JieqiTime] = utils.prev_jie(birth_moment)
      next_j: Final[JieqiTime] = utils.next_jie(birth_moment)

      attribution_birth: datetime = birth_moment
      attribution_jie: datetime = next_j.moment
      if location is not None:
        attribution_birth = self._clock_datetime
        attribution_jie = _apparent_datetime(
          next_j.moment.replace(tzinfo=_UTC8).astimezone(self._canonical_civil.tzinfo),
          location.longitude,
        )

      if _truncated(attribution_birth, self._config.precision) >= _truncated(attribution_jie, self._config.precision):
        bracketing_jies = (next_j, utils.next_jie(next_j.moment))
      else:
        bracketing_jies = (prev_j, next_j)

      # Derive the ganzhi year / month from the owning jie -- the same source `BaziChart`
      # consumes via `bracketing_jies`, so the chart cannot contradict itself. 小寒 opens the
      # last month of the *previous* ganzhi year (立春 has not come yet in its solar year).
      owning: Final[JieqiTime] = bracketing_jies[0]
      ganzhi_year, ganzhi_month = _ganzhi_year_month_of_jie(owning)

    self._bracketing_jies: Final[tuple[JieqiTime, JieqiTime] | None] = bracketing_jies

    # The Year Ganzhi / Year Pillar (年柱).
    self._ganzhi_year: Final[int] = ganzhi_year
    self._year_pillar: Final[Ganzhi] = ganzhi_of_year(self._ganzhi_year)

    # The ganzhi month and the Month Dizhi (月令).
    self._ganzhi_month: Final[int] = ganzhi_month
    assert 1 <= self._ganzhi_month <= 12
    self._month_dizhi: Final[Dizhi] = _ganzhi_month_dizhi(self._ganzhi_month)

    # The day pillar follows the configured 换日点; year/month attribution above remains
    # independent and follows `BaziPrecision`.
    self._day_pillar: Final[Ganzhi] = _ganzhi_of_day_at_moment(
      self._clock_datetime,
      self._config.school.day_rollover,
    )

    # Finally, find out the Hour Dizhi (时柱地支).
    self._hour_dizhi: Final[Dizhi] = Dizhi.from_index((self._clock_datetime.hour + 1) // 2 % 12)

  @staticmethod
  def __parse_bazi_args(
    birth_time: datetime | str,
    gender: BaziGender | str,
  ) -> tuple[datetime, BaziGender]:

    assert isinstance(birth_time, (datetime, str))
    _birth_time: datetime = birth_time if isinstance(birth_time, datetime) else datetime.fromisoformat(birth_time)

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
    Staticmethod that creates a `Bazi` object from the inputs.

    Args:
    - birth_time: (datetime | str) The birth date. It must be naive unless `longitude`
      opts into the aware-input path.
      - if `datetime` type: it will be interpreted as a solar date to feed to `Bazi`.
      - if `str` type: it will be converted by `datetime.fromisoformat`.
    - gender: (BaziGender | str) The gender of the person.
      - if `BaziGender` type: it will be directly fed to `Bazi`.
      - if `str` type: it will be converted by `BaziGender`. 
        - Supported values: "男"/"女"/"male"/"female" (case insensitive).
    - config: (BaziConfig) The chart-level configuration
      (precision / backend / school / Dayun year projection).
      Use `BaziConfig.from_values` to build one from string spellings -- the same
      acceptance face this method parsed here before #69.
    - longitude: (float | None) East-positive longitude for the opt-in aware-input
      apparent-solar path. Latitude is not used by this correction.
    - civil_timezone: (tzinfo | None) Explicit birth-region basis, frozen at birth.
      显式出生地民用时区基准，冻结出生瞬间的实际偏移。
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
  def random(config: BaziConfig = DEFAULT_CONFIG) -> 'Bazi':
    '''
    Staticmethod that creates a random `Bazi` object. Mainly for testing purpose.
    随机生成一个 `Bazi`，主要用于测试。

    Note:
    - The year is in [1902, 2080], and day is in [1, 28].
      年份范围为 [1902, 2080]，日期范围为 [1, 28]。

    Args:
    - config: (BaziConfig) The chart-level configuration, passed to `Bazi.create`.
      命盘级配置，传给 `Bazi.create`。

    Return: (Bazi) The generated Bazi / 随机八字。
    '''
    return Bazi.create(
      birth_time=datetime(
        year=random.randint(1902, 2080),
        month=random.randint(1, 12),
        day=random.randint(1, 28),
        hour=random.randint(0, 23),
        minute=random.randint(0, 59),
      ),
      gender=random.choice(list(BaziGender)),
      config=config,
    )

  @property
  def solar_date(self) -> date:
    '''The apparent-solar birth date for a location-aware chart; otherwise the legacy
    civil date. 地点盘返回真太阳时公历出生日期；默认路径仍返回原民用日期。'''
    return self._utils.to_date(self._solar_date)
  
  @property
  def ganzhi_date(self) -> CalendarDate:
    '''
    The birth date (in ganzhi calendar) / 干支历出生日期

    Note: this is a day-level channel by definition -- its input is a date. Under `HOUR` /
    `MINUTE` precision it can disagree with `ganzhi_year` / the year and month pillars inside
    a jieqi's tie window; precision-attributed consumers should use `ganzhi_year` instead.
    '''
    return self._utils.to_ganzhi(self._solar_date)

  @property
  def ganzhi_year(self) -> int:
    '''
    The ganzhi year the birth belongs to, attributed at `self.config.precision` -- the year
    pillar is `ganzhi_of_year` of exactly this. 按 `self.config.precision` 粒度归属的出生干支年，年柱即由它推出。
    '''
    return self._ganzhi_year

  @property
  def bracketing_jies(self) -> tuple[JieqiTime, JieqiTime]:
    '''
    The two Jies (节) bracketing the birth, per `self.config.precision`. This is the single source
    that the year/month attribution and `BaziChart`'s dayun counting share, so a chart cannot
    contradict itself about which jie owns the birth month.
    按 `self.config.precision` 归属的出生前后两节。年/月柱归属与大运数节共用此单一来源，保证盘面自洽。

    Note:
    - HOUR / MINUTE: `[0]` is the jie owning the birth month (granularity-aware, ties go new --
      so its true moment may be up to one granularity unit *after* the birth), `[1]` the jie
      after it.
    - DAY: moment-level `prev_jie` / `next_jie` of the birth moment -- unchanged pre-existing
      behaviour. The DAY month pillar compares dates while these compare moments, so on a
      jieqi's day they legitimately disagree; that trade-off is pinned by `test_bazi` and
      documented in `CalendarUtilsProtocol`.
    '''
    if self._bracketing_jies is not None:
      return self._bracketing_jies
    return (self._utils.prev_jie(self._reference_datetime), self._utils.next_jie(self._reference_datetime))

  @property
  def hour(self) -> int:
    return self._clock_datetime.hour

  @property
  def minute(self) -> int:
    return self._clock_datetime.minute

  @property
  def longitude(self) -> float | None:
    '''The east-positive longitude of a location-aware chart, otherwise `None`.
    地点盘采用的东经为正经度；默认路径返回 `None`。'''
    return None if self._location is None else self._location.longitude

  @property
  def solar_datetime(self) -> datetime:
    '''The apparent-solar birth time for a location-aware chart, otherwise the legacy
    civil time, truncated to the minute for display. Legacy identity uses this value;
    location-aware identity uses the exact instant, civil offset, longitude, gender and config.
    地点盘返回真太阳时，默认路径返回原民用时刻，均截断到分钟显示。默认路径以此值参与身份判断；
    地点盘身份使用精确绝对时刻、民用偏移、经度、性别及配置。'''
    return self._clock_datetime.replace(second=0, microsecond=0)

  @property
  def _reference_datetime(self) -> datetime:
    '''The Jie/Dayun/transit coordinate: exact naive UTC+08:00 for location-aware
    charts, otherwise the legacy minute-truncated civil label.'''
    if self._location is None:
      return self.solar_datetime
    return self._location.instant.astimezone(_UTC8).replace(tzinfo=None)

  @property
  def _canonical_instant(self) -> datetime:
    '''The canonical aware UTC instant of a location-aware chart.'''
    assert self._location is not None
    return self._location.instant

  @property
  def _canonical_civil(self) -> datetime:
    '''Exact birth-region civil datetime with its fixed offset resolved at birth.'''
    assert self._location is not None
    return self._location.instant.astimezone(timezone(self._location.civil_offset))
  
  @property
  def gender(self) -> BaziGender:
    return self._gender
  
  @property
  def config(self) -> BaziConfig:
    '''The chart-level configuration of this `Bazi`
    (precision / backend / school / Dayun year projection).
    此命盘的配置（出生时间精度 / 历法后端 / 流派档案 / 默认大运年份投影）。'''
    return self._config

  @property
  def _utils(self) -> CalendarUtilsProtocol:
    '''
    The resolved calendar utils of `self.config.backend`. Resolved on each access, so the resolved
    utils -- the HKO module or a celestial singleton -- is never stored on the instance.
    当前历法后端对应的实际工具。每次访问时现解析，实例上不存解析结果，保证 `Bazi` 可安全 deepcopy。

    Do NOT turn this into a `cached_property` -- that would write the resolved utils into
    the instance dict, where the module breaks `deepcopy` loudly and a singleton would be
    silently duplicated, forking its caches.
    '''
    return calendar_utils_of(self._config.backend)
  
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
    return (self._year_pillar.tiangan, month_tiangan(self._year_pillar.tiangan, self._month_dizhi), 
            self._day_pillar.tiangan, hour_tiangan(self._day_pillar.tiangan, self._hour_dizhi))
  
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
    tg: Tiangan = month_tiangan(self._year_pillar.tiangan, self._month_dizhi)
    return Ganzhi(tg, self._month_dizhi)
  
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
    tg: Tiangan = hour_tiangan(self._day_pillar.tiangan, self._hour_dizhi)
    return Ganzhi(tg, self._hour_dizhi)
  
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
  
  @property
  def _identity(self) -> tuple[datetime | _Location, BaziGender, BaziConfig]:
    return (self.solar_datetime if self._location is None else self._location, self.gender, self.config)

  def __eq__(self, other: object) -> bool:
    return isinstance(other, Bazi) and self._identity == other._identity

  def __hash__(self) -> int:
    return hash(self._identity)


class _LocationTimeJson(TypedDict):
  '''Canonical location inputs and the untruncated computed apparent clock.
  规范地点输入及未截断的计算真太阳时。'''
  time_basis: str
  civil_time: str
  canonical_instant: str
  longitude: float
  apparent_time: str


def _location_json(bazi: Bazi) -> _LocationTimeJson:
  assert bazi.longitude is not None
  return {
    'time_basis': 'apparent_solar',
    'civil_time': bazi._canonical_civil.isoformat(),
    'canonical_instant': bazi._canonical_instant.isoformat(),
    'longitude': bazi.longitude,
    'apparent_time': bazi._clock_datetime.isoformat(),
  }


def _parse_location(data: Mapping[str, object]) -> tuple[datetime, float]:
  '''Validate canonical fields independently; the caller validates the complete roster.
  逐项验证规范字段；完整名册由调用方验证。

  Charts reconstruct and compare; observation records do not recalculate.
  命盘会重建及核对，观察记录不重算。
  '''
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
