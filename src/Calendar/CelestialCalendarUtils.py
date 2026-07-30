# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''
Calendar utils backed by the pre-generated celestial-calendar tables (see
`CelestialData/SCHEMA.md`).  Conforms to `CalendarUtilsProtocol`, with no dependency on
`HkoDataCalendarUtils` -- the two backends are independent implementations, and their
agreement is a test result rather than a shared code path.

What this backend adds over HKO is `jieqi_moment`: real second-level moments instead of
day-level placeholders.  Everything that a `CalendarDate` can express stays day-level,
because the GANZHI calendar itself is a date-level construct (day 1 of ganzhi month 1 is
the 立春 *date*).  Attributing a *moment* to a pillar is the caller's job -- that is what
issue #72 is about, and it is deliberately not done here.

Unlike the HKO backend, this one is a class with module-level singletons rather than a
module of functions.  The lunar calendar has two algorithms and the caches must not be
shared between them: a mutable module-level switch plus `functools.lru_cache` would let a
switch silently return results computed under the previous algorithm.  Two instances make
the choice part of the identity of the utils object instead.
'''

import copy
import functools

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Final, Union

from .CalendarDefines import CalendarType, CalendarDate
from .CelestialData.Loader import (
  DATA_DIR, JieqiMomentTable, LunarYearTable, LunarYearInfo,
)

from ..Defines import Jieqi
from ..Common import JieqiTime


_JIEQI_TABLE: Final[JieqiMomentTable] = JieqiMomentTable()
'''Shared by every algorithm: only the lunar tables differ between them.'''


class CelestialCalendarUtils:
  '''
  Calendar utils reading the celestial-calendar tables.  Use the module-level singletons
  `ALGO1` / `ALGO2` instead of constructing this directly.
  '''

  def __init__(self, lunar_table_path: Path) -> None:
    self._jieqi_table: Final[JieqiMomentTable] = _JIEQI_TABLE
    self._lunar_table: Final[LunarYearTable] = LunarYearTable(lunar_table_path)

  # -- Supported range -------------------------------------------------------------
  #
  # Derived from the tables rather than hardcoded.  The three date types are three
  # expressions of the same physical window, so the solar bounds are the anchor and the
  # other four are conversions of them -- which is also why they compare equal to HKO's
  # own constants (asserted by the parity suite).

  @functools.lru_cache(maxsize=512)
  def get_min_supported_date(self, date_type: CalendarType) -> CalendarDate:
    if date_type == CalendarType.SOLAR:
      # The first day of the earliest lunar year the table covers.
      first: date = self._lunar_table.get(min(self._lunar_table.supported_year_range()))['first_solar_day']
      return CalendarDate(first.year, first.month, first.day, CalendarType.SOLAR)
    elif date_type == CalendarType.LUNAR:
      return self.solar_to_lunar(self.get_min_supported_date(CalendarType.SOLAR))
    else:
      assert date_type == CalendarType.GANZHI
      return self.solar_to_ganzhi(self.get_min_supported_date(CalendarType.SOLAR))

  @functools.lru_cache(maxsize=512)
  def get_max_supported_date(self, date_type: CalendarType) -> CalendarDate:
    if date_type == CalendarType.SOLAR:
      # `solar_to_lunar` looks the lunar year up by the solar year first, so a solar date
      # may not outlive the lunar table's last year -- even though that lunar year runs
      # into the next Gregorian one.
      last_year: int = max(self._lunar_table.supported_year_range())
      return CalendarDate(last_year, 12, 31, CalendarType.SOLAR)
    elif date_type == CalendarType.LUNAR:
      return self.solar_to_lunar(self.get_max_supported_date(CalendarType.SOLAR))
    else:
      assert date_type == CalendarType.GANZHI
      return self.solar_to_ganzhi(self.get_max_supported_date(CalendarType.SOLAR))

  # -- Validity --------------------------------------------------------------------

  @functools.lru_cache(maxsize=512)
  def is_valid_solar_date(self, d: CalendarDate) -> bool:
    '''
    Check if the input date is valid, including whether it is in the supported range.

    Args:
    - d: CalendarDate object, expected to be of `CalendarType.SOLAR`.

    Return: True if valid, False otherwise.
    '''

    if d.date_type != CalendarType.SOLAR:
      return False
    if d < self.get_min_supported_date(CalendarType.SOLAR):
      return False
    if d > self.get_max_supported_date(CalendarType.SOLAR):
      return False

    try:
      # Let the standard library be the authority on Gregorian month lengths and leap years.
      date(d.year, d.month, d.day)
    except ValueError:
      return False
    return True

  @functools.lru_cache(maxsize=512)
  def is_valid_lunar_date(self, d: CalendarDate) -> bool:
    '''
    Check if the input date is valid, including whether it is in the supported range.

    Args:
    - d: CalendarDate object, expected to be of `CalendarType.LUNAR`.

    Return: True if valid, False otherwise.
    '''

    if d.date_type != CalendarType.LUNAR:
      return False
    if d < self.get_min_supported_date(CalendarType.LUNAR):
      return False
    if d > self.get_max_supported_date(CalendarType.LUNAR):
      return False

    days_counts: list[int] = self._lunar_table.get(d.year)['days_counts']
    if d.month < 1 or d.month > len(days_counts):
      return False
    if d.day < 1 or d.day > days_counts[d.month - 1]:
      return False

    return True

  @functools.lru_cache(maxsize=512)
  def is_valid_ganzhi_date(self, d: CalendarDate) -> bool:
    '''
    Check if the input date is valid, including whether it is in the supported range.

    Args:
    - d: CalendarDate object, expected to be of `CalendarType.GANZHI`.

    Return: True if valid, False otherwise.
    '''

    if d.date_type != CalendarType.GANZHI:
      return False
    if d < self.get_min_supported_date(CalendarType.GANZHI):
      return False
    if d > self.get_max_supported_date(CalendarType.GANZHI):
      return False

    if d.month < 1 or d.month > 12:
      return False

    days_counts: list[int] = self.days_counts_in_ganzhi_year(d.year)
    if d.day < 1 or d.day > days_counts[d.month - 1]:
      return False

    return True

  @functools.lru_cache(maxsize=512)
  def is_valid(self, d: CalendarDate) -> bool:
    if d.date_type == CalendarType.SOLAR:
      return self.is_valid_solar_date(d)
    elif d.date_type == CalendarType.LUNAR:
      return self.is_valid_lunar_date(d)
    else:
      assert d.date_type == CalendarType.GANZHI
      return self.is_valid_ganzhi_date(d)

  # -- Ganzhi month lengths --------------------------------------------------------

  def days_counts_in_ganzhi_year(self, ganzhi_year: int) -> list[int]:
    '''
    The length in days of each of the 12 ganzhi months of `ganzhi_year`, measured between
    consecutive 节 *dates* (the ganzhi calendar is date-level, see the module docstring).
    '''
    # A fresh list per call, from a cache that holds a tuple.  Returning the cached list
    # itself would let a caller's in-place edit poison every later answer -- and the poison
    # spreads rather than staying put: `is_valid_ganzhi_date` caches verdicts derived from
    # this, so undoing the edit does not undo the damage, and no `cache_clear` recovers it.
    return list(self.__days_counts_in_ganzhi_year(ganzhi_year))

  @functools.lru_cache(maxsize=512)
  def __days_counts_in_ganzhi_year(self, ganzhi_year: int) -> tuple[int, ...]:
    # A ganzhi year needs the 立春 of the next solar year to close its last month.
    assert ganzhi_year in self._jieqi_table.supported_year_range()
    assert ganzhi_year + 1 in self._jieqi_table.supported_year_range()

    jies: list[Jieqi] = Jieqi.as_list()[::2] # Pick the Jieqis when new months start.
    assert jies[0] is Jieqi.立春
    assert len(jies) == 12

    # The first 11 节 are in solar year `ganzhi_year`, the last one (小寒) in the next.
    start_dates: list[date] = [self.jieqi_date(ganzhi_year, jq) for jq in jies[:11]]
    start_dates += [self.jieqi_date(ganzhi_year + 1, jq) for jq in jies[11:]]
    end_dates: list[date] = start_dates[1:] + [self.jieqi_date(ganzhi_year + 1, Jieqi.立春)]

    days_counts: tuple[int, ...] = tuple((end - start).days
                                         for start, end in zip(start_dates, end_dates))
    assert len(days_counts) == 12
    return days_counts

  # -- Conversions -----------------------------------------------------------------

  @functools.lru_cache(maxsize=512)
  def lunar_to_solar(self, lunar_date: CalendarDate) -> CalendarDate:
    assert lunar_date.date_type == CalendarType.LUNAR
    assert self.is_valid(lunar_date)

    info: LunarYearInfo = self._lunar_table.get(lunar_date.year)
    passed_days: int = sum(info['days_counts'][:lunar_date.month - 1]) + lunar_date.day - 1
    solar: date = info['first_solar_day'] + timedelta(days=passed_days)
    return CalendarDate(solar.year, solar.month, solar.day, CalendarType.SOLAR)

  @functools.lru_cache(maxsize=512)
  def solar_to_lunar(self, solar_date: CalendarDate) -> CalendarDate:
    assert solar_date.date_type == CalendarType.SOLAR
    assert self.is_valid(solar_date)
    solar: date = date(solar_date.year, solar_date.month, solar_date.day)

    # A solar date early in the year still belongs to the previous lunar year.
    lunar_year: int = solar_date.year
    info: LunarYearInfo = self._lunar_table.get(lunar_year)
    if info['first_solar_day'] > solar:
      lunar_year -= 1
      info = self._lunar_table.get(lunar_year)

    month_idx, day_idx = self.__walk_months((solar - info['first_solar_day']).days, info['days_counts'])
    return CalendarDate(lunar_year, month_idx + 1, day_idx + 1, CalendarType.LUNAR)

  @functools.lru_cache(maxsize=512)
  def ganzhi_to_solar(self, ganzhi_date: CalendarDate) -> CalendarDate:
    assert ganzhi_date.date_type == CalendarType.GANZHI
    assert self.is_valid(ganzhi_date)

    days_counts: list[int] = self.days_counts_in_ganzhi_year(ganzhi_date.year)
    passed_days: int = sum(days_counts[:ganzhi_date.month - 1]) + ganzhi_date.day - 1
    solar: date = self.jieqi_date(ganzhi_date.year, Jieqi.立春) + timedelta(days=passed_days)
    return CalendarDate(solar.year, solar.month, solar.day, CalendarType.SOLAR)

  @functools.lru_cache(maxsize=512)
  def solar_to_ganzhi(self, solar_date: CalendarDate) -> CalendarDate:
    assert solar_date.date_type == CalendarType.SOLAR
    assert self.is_valid(solar_date)
    solar: date = date(solar_date.year, solar_date.month, solar_date.day)

    # A solar date before 立春 still belongs to the previous ganzhi year.
    ganzhi_year: int = solar_date.year
    if self.jieqi_date(ganzhi_year, Jieqi.立春) > solar:
      ganzhi_year -= 1

    passed_days: int = (solar - self.jieqi_date(ganzhi_year, Jieqi.立春)).days
    month_idx, day_idx = self.__walk_months(passed_days, self.days_counts_in_ganzhi_year(ganzhi_year))
    return CalendarDate(ganzhi_year, month_idx + 1, day_idx + 1, CalendarType.GANZHI)

  @functools.lru_cache(maxsize=512)
  def lunar_to_ganzhi(self, lunar_date: CalendarDate) -> CalendarDate:
    assert lunar_date.date_type == CalendarType.LUNAR
    assert self.is_valid(lunar_date)
    return self.solar_to_ganzhi(self.lunar_to_solar(lunar_date))

  @functools.lru_cache(maxsize=512)
  def ganzhi_to_lunar(self, ganzhi_date: CalendarDate) -> CalendarDate:
    assert ganzhi_date.date_type == CalendarType.GANZHI
    assert self.is_valid(ganzhi_date)
    return self.solar_to_lunar(self.ganzhi_to_solar(ganzhi_date))

  @staticmethod
  def __walk_months(passed_days: int, days_counts: list[int]) -> tuple[int, int]:
    '''Split a day offset from the start of a year into a (month index, day index) pair.'''
    month_idx: int = 0
    while passed_days >= days_counts[month_idx]:
      passed_days -= days_counts[month_idx]
      month_idx += 1
    return month_idx, passed_days

  # -- `to_*` family ---------------------------------------------------------------

  @functools.lru_cache(maxsize=512)
  def __to_calendardate(self, d: Union[date, CalendarDate]) -> CalendarDate:
    if isinstance(d, date):
      ret = CalendarDate(d.year, d.month, d.day, CalendarType.SOLAR)
    else:
      assert isinstance(d, CalendarDate)
      ret = copy.deepcopy(d)

    assert self.is_valid(ret)
    return ret

  @functools.lru_cache(maxsize=512)
  def to_solar(self, d: Union[date, CalendarDate]) -> CalendarDate:
    '''
    Convert the input date to a `CalendarDate` with `SOLAR` type.

    Args:
    - d: (Union[date, CalendarDate]) The input date.
      - If `d` is of `date` type, it will be interpreted as a solar date.

    Return: (CalendarDate) a converted date with `SOLAR` type.
    '''

    calendardate: CalendarDate = self.__to_calendardate(d) # Already validated.

    if calendardate.date_type == CalendarType.SOLAR:
      return copy.deepcopy(calendardate)
    elif calendardate.date_type == CalendarType.LUNAR:
      return self.lunar_to_solar(calendardate)
    else:
      assert calendardate.date_type == CalendarType.GANZHI
      return self.ganzhi_to_solar(calendardate)

  @functools.lru_cache(maxsize=512)
  def to_lunar(self, d: Union[date, CalendarDate]) -> CalendarDate:
    '''
    Convert the input date to a `CalendarDate` with `LUNAR` type.

    Args:
    - d: (Union[date, CalendarDate]) The input date.
      - If `d` is of `date` type, it will be interpreted as a solar date.

    Return: (CalendarDate) a converted date with `LUNAR` type.
    '''

    calendardate: CalendarDate = self.__to_calendardate(d) # Already validated.

    if calendardate.date_type == CalendarType.LUNAR:
      return copy.deepcopy(calendardate)
    elif calendardate.date_type == CalendarType.SOLAR:
      return self.solar_to_lunar(calendardate)
    else:
      assert calendardate.date_type == CalendarType.GANZHI
      return self.ganzhi_to_lunar(calendardate)

  @functools.lru_cache(maxsize=512)
  def to_ganzhi(self, d: Union[date, CalendarDate]) -> CalendarDate:
    '''
    Convert the input date to a `CalendarDate` with `GANZHI` type.

    Args:
    - d: (Union[date, CalendarDate]) The input date.
      - If `d` is of `date` type, it will be interpreted as a solar date.

    Return: (CalendarDate) a converted date with `GANZHI` type.
    '''

    calendardate: CalendarDate = self.__to_calendardate(d) # Already validated.

    if calendardate.date_type == CalendarType.GANZHI:
      return copy.deepcopy(calendardate)
    elif calendardate.date_type == CalendarType.SOLAR:
      return self.solar_to_ganzhi(calendardate)
    else:
      assert calendardate.date_type == CalendarType.LUNAR
      return self.lunar_to_ganzhi(calendardate)

  @functools.lru_cache(maxsize=512)
  def to_date(self, d: Union[date, CalendarDate]) -> date:
    '''
    Convert the input date to a `date` type.

    Args:
    - d: (Union[date, CalendarDate]) The input date.
      - If `d` is of `datetime` type, it will be casted to `date`.

    Return: (date) a converted date with `date` type.
    '''

    solar: CalendarDate = self.to_solar(self.__to_calendardate(d))
    return date(solar.year, solar.month, solar.day)

  # -- Jieqi -----------------------------------------------------------------------

  @functools.lru_cache(maxsize=512)
  def jieqi_date(self, solar_year: int, jieqi: Jieqi) -> date:
    '''
    Find out the date of the given Jieqi in the given solar/gregorian year.
    输入公历年份和节气，返回节气日期。

    Args:
    - solar_year: (int) The solar year.
    - jieqi: (Jieqi) The Jieqi.

    Return: (date) The date of the Jieqi in the given solar/gregorian year.
    '''

    return self.jieqi_moment(solar_year, jieqi).date()

  @functools.lru_cache(maxsize=512)
  def jieqi_moment(self, solar_year: int, jieqi: Jieqi) -> datetime:
    '''
    Find out the accurate moment (datetime) of the given Jieqi in the given solar year.
    输入公历年份和节气，返回节气的具体时刻。

    Args:
    - solar_year: (int) The solar year.
    - jieqi: (Jieqi) The Jieqi.

    Note:
    - The moment is in UTC+08:00 (China standard time), at second granularity, truncated.
      Times before 1929 are still expressed in UTC+08:00 rather than Beijing local mean
      time -- see issue #69, which is an input-side policy question, not a table one.
    - 时刻为东八区（北京时间），精度到秒（截断）。1929 年前同样按东八区表达，
      而非北京地方平时，见 issue #69。

    Return: (datetime) The accurate moment of the Jieqi in the given solar year.
    '''

    assert isinstance(solar_year, int)
    assert isinstance(jieqi, Jieqi)
    assert solar_year in self._jieqi_table.supported_year_range()
    return self._jieqi_table.get(solar_year, jieqi)

  # maxsize=2, not 1: the cache is class-level, so `ALGO1` and `ALGO2` are two distinct
  # keys and a size of 1 would make the two singletons evict each other on every call.
  @functools.lru_cache(maxsize=2)
  def supported_jie_boundaries(self) -> tuple[datetime, datetime]:
    '''
    Return a tuple of datetimes representing the first and last supported Jie accurate time.
    When using methods `prev_jie` and `next_jie`, the input datetime should be in:
    `[returned_tuple[0], returned_tuple[1])` (`returned_tuple[0]` included, `returned_tuple[1]` not).
    '''
    years: range = self._jieqi_table.supported_year_range()
    return (
      self.jieqi_moment(min(years), Jieqi.小寒), # 小寒 is the first Jie of any solar year.
      self.jieqi_moment(max(years), Jieqi.大雪), # 大雪 is the last Jie of any solar year.
    )

  def __check_jie_range(self, dt: datetime) -> None:
    first, last = self.supported_jie_boundaries()
    if dt < first:
      raise ValueError(f'"{dt}" is out of the supported range. The first available Jie is "{first}"')
    if dt >= last:
      raise ValueError(f'"{dt}" is out of the supported range. The last available Jie is "{last}"')

  @functools.lru_cache(maxsize=512)
  def prev_jie(self, dt: datetime) -> JieqiTime:
    '''
    Find out the previous Jie (节), not Jieqi, for the given solar datetime.
    输入某时间点，返回这个时间点之前的一个节令（不包含中气），以及对应的时间点。

    A moment exactly on a Jie belongs to that Jie (the comparison is `>=`).
    恰好落在节令时刻上的时间点，归属该节令。

    Args:
    - dt: (datetime) The datetime.

    Return: (JieqiTime) The previous Jie (节), and its solar datetime.
    '''

    assert isinstance(dt, datetime)
    self.__check_jie_range(dt)

    # Walk the year's 节 backwards; `dt` sits in the last interval whose start is <= it.
    for jie in reversed(Jieqi.as_list(ganzhi_year=False)[::2]):
      moment: datetime = self.jieqi_moment(dt.year, jie)
      if moment <= dt:
        return JieqiTime(jie, moment)

    # `dt` precedes 小寒 of its own year, so the previous Jie is last year's 大雪.
    last_daxue: datetime = self.jieqi_moment(dt.year - 1, Jieqi.大雪)
    assert last_daxue <= dt
    return JieqiTime(Jieqi.大雪, last_daxue)

  @functools.lru_cache(maxsize=512)
  def next_jie(self, dt: datetime) -> JieqiTime:
    '''
    Find out the next Jie (节), not Jieqi, for the given solar datetime.
    输入某时间点，返回这个时间点之后的一个节令（不包含中气），以及对应的时间点。

    A moment exactly on a Jie belongs to that Jie, so the *next* one is the following
    Jie (the comparison is `>`).
    恰好落在节令时刻上的时间点归属该节令，故下一个节令是再往后的那一个。

    Args:
    - dt: (datetime) The datetime.

    Return: (JieqiTime) The next Jie (节), and its solar datetime.
    '''

    assert isinstance(dt, datetime)
    self.__check_jie_range(dt)

    for jie in Jieqi.as_list(ganzhi_year=False)[::2]:
      moment: datetime = self.jieqi_moment(dt.year, jie)
      if moment > dt:
        return JieqiTime(jie, moment)

    # `dt` is on or after 大雪 of its own year, so the next Jie is next year's 小寒.
    next_xiaohan: datetime = self.jieqi_moment(dt.year + 1, Jieqi.小寒)
    assert dt < next_xiaohan
    return JieqiTime(Jieqi.小寒, next_xiaohan)


ALGO1: Final[CelestialCalendarUtils] = CelestialCalendarUtils(DATA_DIR / 'lunar_years_algo1.txt')
'''The default: the lunar surface follows the HKO official almanac lineage.'''

ALGO2: Final[CelestialCalendarUtils] = CelestialCalendarUtils(DATA_DIR / 'lunar_years_algo2.txt')
'''Opt-in: leap-second aware UTC+8 lunar months. Differs from ALGO1 on 6 years, see SCHEMA.md.'''
