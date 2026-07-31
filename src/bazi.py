# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
import random

from enum import Enum
from datetime import date, time, datetime, timedelta
from typing import Final, Optional, Union

from .common import JieqiTime
from .defines import Tiangan, Dizhi, Ganzhi, Jieqi
from .calendar import (
  CalendarDate, CalendarUtilsProtocol, CalendarBackend, calendar_utils_of,
)

from .utils.bazi_utils import (
  month_tiangan, hour_tiangan, ganzhi_of_day, ganzhi_of_year,
)


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
    if self is self.MALE:
      return 'male'
    else:
      assert self is self.FEMALE
      return 'female'



class BaziPrecision(Enum):
  '''
  BaziPrecision is used to specify the precision when generating the Bazi chart.

  As per the rules of Bazi system, new years start on the days of Start of Spring (LICHUN / 立春), and new months start
  on the days of 12 Jieqis (LICHUN, JINGZHE, QINGMING, LIXIA... / 立春, 惊蛰, 清明, 立夏...).

  So, even born on the same day, two persons can have different Year Ganzhi (年柱) and Month Ganzhi (月柱).

  The 3 levels -- DAY, HOUR, MINUTE -- are three granularities of ONE rule, not three
  approximations of a single truth. A birth belongs to the new year / month when
  `birth >= jieqi`, compared at the granularity the birth is known to; a tie resolves to the
  NEW pillar. That tie-break is the same one the calendar layer freezes -- see
  `calendar/celestial_data/SCHEMA.md`, "Boundary convention".
  三档是同一条规则的三个粒度，不是对同一真值的三种逼近：出生按「已知的粒度」与节气时刻比较，
  `birth >= jieqi` 归新年 / 新月，相等归新。

  - DAY    -- the birth is known to the day, so dates are compared.    只知道日期，比到日。
  - HOUR   -- known to the 时辰, so (date, 时辰) is compared.           知道时辰，比到时辰。
  - MINUTE -- known to the minute, so (date, hour, minute) is compared. 知道到分，比到分。

  `HOUR` means a 时辰 (a traditional double-hour, 子时 starting at 23:00), not a clock hour:
  birth records come at day, 时辰, or minute granularity -- never "hour but not minute".

  For example, LICHUN / 立春 of 2000 falls at 2000-02-04 20:40:23 (per the celestial backend;
  the HKO backend publishes the date only). Then:
  - DAY:    everyone born on 2000-02-04 gets "庚辰" and Month Dizhi "寅", including those born
            before 20:40:23 -- at day granularity, 02-04 >= 02-04 is a tie, and ties go new.
            Those born on 2000-02-03 get "己卯" and "丑".
  - HOUR:   born in 戌时 [19:00, 21:00), the 时辰 holding the jieqi, gets "庚辰" and "寅" (a tie
            again); born in 酉时 [17:00, 19:00) or earlier that day gets "己卯" and "丑".
  - MINUTE: born at or after 20:40 gets "庚辰" and "寅"; before it, "己卯" and "丑".

  This is a rule, not an estimate, and the difference is visible at the extremes: LICHUN of
  2017 falls at 2017-02-03 23:34:03, so DAY assigns all of 02-03 to the new year even though
  98% of that day precedes the jieqi. That is what the rule says, not a defect in it -- an
  estimator would have to flip its answer based on a clock time the DAY caller is not claiming
  to know, which would also make ganzhi month lengths depend on it.

  Because 子时 spans midnight, the tie 时辰 can start on the previous civil day: LICHUN of
  2009 falls at 2009-02-04 00:49:48, in the 子时 that began at 02-03 23:00, so a HOUR birth
  at 2009-02-03 23:30 ties and belongs to the new year -- on a day that DAY assigns to the
  old side. The granularities are three readings of one rule, not nested refinements.
  子时跨午夜，tie 时辰可始于节气前一公历日——三档是同一规则的三种读法，不是嵌套细化。

  HOUR and MINUTE need real jieqi moments, so they require the celestial backend --
  `Bazi.__init__` rejects the HKO backend for them (its `jieqi_moment` is a midnight
  placeholder, see `CalendarUtilsProtocol`).
  '''
  DAY    = 0
  HOUR   = 1
  MINUTE = 2

  def __str__(self) -> str:
    if self is self.DAY:
      return 'day'
    elif self is self.HOUR:
      return 'hour'
    else:
      assert self is self.MINUTE
      return 'minute'


'''Maps each Jie (节) to the ganzhi month it opens: 立春 -> 1 (寅月), ..., 小寒 -> 12 (丑月). / 每个节到其所开干支月的映射：立春开寅月，……，小寒开丑月。'''
_GANZHI_MONTH_OF_JIE: Final[dict[Jieqi, int]] = {
  jie : month
  for month, jie in enumerate(Jieqi.as_list(ganzhi_year=True)[::2], start=1)
}


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
  For all other information (transits / shishen / ...), please see `src/BaziChart` (e.g. `BaziChart`).

  八字是仅存储基本信息的类。一个 `Bazi` 对象存储着年、月、日、时的四柱八个字。
  对于其他信息（流年大运 / 十神等），请参阅 `src/BaziChart`（例如 `BaziChart`）。

  Note:
  - We don't care about the timezone. `Bazi` knows nothing about timezone.
  - We don't care about the true solar time / daylight saving time - it should be well-processed outside of this class.
  - The year pillar turns at 立春, not at 正月初一 (this library follows the 立春 school).
  - `Bazi` 不考虑时差。时差需要在外部处理。
  - `Bazi` 不考虑真太阳时和夏令时。这些时间需要在外部处理。
  - 本库从立春派：年柱以立春换年，不以正月初一（春节）换年。
  '''

  def __init__(self, birth_time: datetime, gender: BaziGender, precision: BaziPrecision,
               backend: CalendarBackend = CalendarBackend.CELESTIAL) -> None:
    '''
    `Bazi` (i.e. 八字, which means eight characters in Chinese) takes the birth time and gender as input, 
    and figures out the pillars of year, month, day, and hour.
    `Bazi` 接受出生时间和性别作为输入，计算年、月、日、时的八字。
    
    Note:
    - We don't care about the timezone. `Bazi` knows nothing about timezone.
    - We don't care about the true solar time / daylight saving time - it should be well-processed outside of this class.
    - `Bazi` 不考虑时差。时差需要在外部处理。
    - `Bazi` 不考虑真太阳时和夏令时。这些时间需要在外部处理。
    
    Args:
    - birth_time: (datetime) The birth date (in Gregorian calendar) and time. Note that no timezone should be set.
    - gender: (BaziGender) The gender of the person.
    - precision: (BaziPrecision) The precision of the birth time.
    - backend: (CalendarBackend) The calendar backend used for all calendar conversions.
    '''

    assert isinstance(birth_time, datetime)
    assert isinstance(gender, BaziGender)
    assert isinstance(precision, BaziPrecision)
    assert isinstance(backend, CalendarBackend)

    self._backend: Final[CalendarBackend] = backend
    utils: Final[CalendarUtilsProtocol] = calendar_utils_of(backend)

    self._birth_time: Final[datetime] = copy.deepcopy(birth_time)
    assert self._birth_time.tzinfo is None, 'Timezone should be well-processed outside of this class.'

    self._solar_date: Final[CalendarDate] = utils.to_solar(self._birth_time)
    assert utils.is_valid_solar_date(self._solar_date) # Here we are also checking if the date falls into the supported range.

    self._hour: Final[int] = self._birth_time.hour
    assert self._hour >= 0 and self._hour < 24

    self._minute: Final[int] = self._birth_time.minute
    assert self._minute >= 0 and self._minute < 60

    self._gender: Final[BaziGender] = gender
    self._precision: Final[BaziPrecision] = precision

    # Which ganzhi year / month owns the birth, compared per `BaziPrecision`
    # (`birth >= jieqi` at the known granularity, ties go new).
    ganzhi_year: int
    ganzhi_month: int
    bracketing_jies: Optional[tuple[JieqiTime, JieqiTime]] = None
    if self._precision is BaziPrecision.DAY:
      # DAY compares dates: the `to_ganzhi` channel drops the time, so a jieqi's whole day
      # falls on its new side. `bracketing_jies` stays moment-level for DAY (see the property).
      ganzhi_calendardate: CalendarDate = utils.to_ganzhi(self._solar_date)
      ganzhi_year = ganzhi_calendardate.year
      ganzhi_month = ganzhi_calendardate.month # `ganzhi_calendardate` is already at `DAY`-level precision.
    else:
      if self._backend is CalendarBackend.HKO:
        raise ValueError(
          f'{self._precision} needs real jieqi moments, which the HKO backend cannot provide '
          '(its `jieqi_moment` is a midnight placeholder). Use `CalendarBackend.CELESTIAL`.'
        )

      # The truncated birth can never exceed the truncated next jie (truncation is monotone),
      # so `>=` can only hit as a tie -- in which case the next jie owns the birth month, and
      # its true moment may be up to one granularity unit after the birth (子时 spans midnight,
      # so for HOUR the tie window may even start on the previous civil day).
      birth_moment: Final[datetime] = self.solar_datetime
      prev_j: Final[JieqiTime] = utils.prev_jie(birth_moment)
      next_j: Final[JieqiTime] = utils.next_jie(birth_moment)
      if _truncated(birth_moment, self._precision) >= _truncated(next_j.moment, self._precision):
        bracketing_jies = (next_j, utils.next_jie(next_j.moment))
      else:
        bracketing_jies = (prev_j, next_j)

      # Derive the ganzhi year / month from the owning jie -- the same source `BaziChart`
      # consumes via `bracketing_jies`, so the chart cannot contradict itself. 小寒 opens the
      # last month of the *previous* ganzhi year (立春 has not come yet in its solar year).
      owning: Final[JieqiTime] = bracketing_jies[0]
      ganzhi_year = owning.moment.year - (1 if owning.jieqi is Jieqi.小寒 else 0)
      ganzhi_month = _GANZHI_MONTH_OF_JIE[owning.jieqi]

    self._bracketing_jies: Final[Optional[tuple[JieqiTime, JieqiTime]]] = bracketing_jies

    # The Year Ganzhi / Year Pillar (年柱).
    self._ganzhi_year: Final[int] = ganzhi_year
    self._year_pillar: Final[Ganzhi] = ganzhi_of_year(self._ganzhi_year)

    # The ganzhi month and the Month Dizhi (月令).
    self._ganzhi_month: Final[int] = ganzhi_month
    assert 1 <= self._ganzhi_month <= 12
    self._month_dizhi: Final[Dizhi] = Dizhi.from_index((2 + self._ganzhi_month - 1) % 12)

    # Figure out the ganzhi day, as well as the Day Ganzhi / Day Pillar (日柱).
    #
    # 晚子时换日: the day pillar rolls at 23:00 (when 子时 begins), which the year and month
    # pillars above deliberately do NOT do -- they follow `BaziPrecision`'s attribution
    # (dates at DAY, truncated moments at HOUR/MINUTE). So a 23:30 birth takes the *next*
    # day's day pillar while its year/month attribution stays put, except inside a tie
    # window. Both halves of that are variants tracked in issue #69, and a 子正换日
    # variant has to say which pillars it moves; `test_bazi` pins today's answer meanwhile.
    day_offset: int = 0 if self._birth_time.hour < 23 else 1
    self._day_pillar: Final[Ganzhi] = ganzhi_of_day(timedelta(days=day_offset) + self._birth_time)

    # Finally, find out the Hour Dizhi (时柱地支).
    self._hour_dizhi: Final[Dizhi] = Dizhi.from_index(int((self._hour + 1) / 2) % 12)

  @staticmethod
  def __parse_bazi_args(
    birth_time: Union[datetime, str],
    gender: Union[BaziGender, str], 
    precision: Union[BaziPrecision, str],
    backend: Union[CalendarBackend, str]
  ) -> tuple[datetime, BaziGender, BaziPrecision, CalendarBackend]:
    
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

    _backend: CalendarBackend
    if isinstance(backend, CalendarBackend):
      _backend = backend
    else:
      assert isinstance(backend, str)
      _backend = CalendarBackend.from_str(backend)

    return _birth_time, _gender, _precision, _backend

  @staticmethod
  def create(
    birth_time: Union[datetime, str],
    gender: Union[BaziGender, str], 
    precision: Union[BaziPrecision, str],
    backend: Union[CalendarBackend, str] = CalendarBackend.CELESTIAL
  ) -> 'Bazi':
    '''
    Staticmethod that creates a `Bazi` object from the inputs.

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
    - backend: (Union[CalendarBackend, str]) The calendar backend used for all calendar conversions.
      - if `CalendarBackend` type: it will be directly fed to `Bazi`.
      - if `str` type: it will be converted by `CalendarBackend.from_str`.
        - Supported values: the member names and values of `CalendarBackend` (e.g. "HKO"/"hko", case insensitive).
    '''

    assert isinstance(birth_time, (datetime, str))
    assert isinstance(gender, (BaziGender, str))
    assert isinstance(precision, (BaziPrecision, str))
    assert isinstance(backend, (CalendarBackend, str))

    _birth_time, _gender, _precision, _backend = Bazi.__parse_bazi_args(birth_time, gender, precision, backend)
    bazi: Bazi = Bazi(
      birth_time=_birth_time,
      gender=_gender,
      precision=_precision,
      backend=_backend,
    )
    return bazi
  
  @staticmethod
  def random() -> 'Bazi':
    '''
    Staticmethod that creates a random `Bazi` object. Mainly for testing purpose.

    Note that the precision is currently set to `BaziPrecision.DAY`.
    Note that the year is in [1902, 2080], and day is in [1, 28].
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
      precision=BaziPrecision.DAY,
    )

  @property
  def solar_date(self) -> date:
    '''The birth date (in solar/gregorian calendar) / 公历出生日期'''
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
    The ganzhi year the birth belongs to, attributed at `self.precision` -- the year pillar is
    `ganzhi_of_year` of exactly this. 按 `self.precision` 粒度归属的出生干支年，年柱即由它推出。
    '''
    return self._ganzhi_year

  @property
  def bracketing_jies(self) -> tuple[JieqiTime, JieqiTime]:
    '''
    The two Jies (节) bracketing the birth, per `self.precision`. This is the single source
    that the year/month attribution and `BaziChart`'s dayun counting share, so a chart cannot
    contradict itself about which jie owns the birth month.
    按 `self.precision` 归属的出生前后两节。年/月柱归属与大运数节共用此单一来源，保证盘面自洽。

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
    return (self._utils.prev_jie(self.solar_datetime), self._utils.next_jie(self.solar_datetime))

  @property
  def hour(self) -> int:
    return self._hour
  
  @property
  def minute(self) -> int:
    return self._minute
  
  @property
  def solar_datetime(self) -> datetime:
    '''The exact birth time (in solar/gregorian calendar) / 出生时刻（公历）'''
    return datetime.combine(self.solar_date, time(self.hour, self.minute))
  
  @property
  def gender(self) -> BaziGender:
    return self._gender
  
  @property
  def precision(self) -> BaziPrecision:
    return self._precision

  @property
  def backend(self) -> CalendarBackend:
    '''The calendar backend that this `Bazi` uses / 此命盘使用的历法后端'''
    return self._backend

  @property
  def _utils(self) -> CalendarUtilsProtocol:
    '''
    The resolved calendar utils of `self.backend`. Resolved on each access, so nothing
    non-deepcopyable (i.e. the utils module) is stored on the instance.
    当前历法后端对应的实际工具。每次访问时现解析，实例上不存模块引用，保证 `Bazi` 可 deepcopy。

    Do NOT turn this into a `cached_property` -- that would write the module into
    the instance dict and break `deepcopy`.
    '''
    return calendar_utils_of(self._backend)
  
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
  
  def __eq__(self, other: object) -> bool:
    if not isinstance(other, Bazi):
      return False
    return (
      self.solar_datetime == other.solar_datetime
      and self.gender == other.gender
      and self.precision == other.precision
      and self.backend == other.backend
    )
  
  def __ne__(self, other: object) -> bool:
    return not self.__eq__(other)

八字 = Bazi
