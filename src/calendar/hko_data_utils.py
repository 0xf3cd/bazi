# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import calendar  # the stdlib module -- NOT the `src.calendar` package this file lives in
import functools
import itertools

from datetime import date, time, datetime, timedelta
from typing import Final

from .dates import CalendarType, CalendarDate, JieqiTime
from .hko_data import DecodedJieqiDates, DecodedLunarYears, LunarYearInfo

from ..defines import Jieqi


# Two databases as module-level constants, where we can query the Jieqi and Lunar year info.
jieqi_dates_db: Final[DecodedJieqiDates] = DecodedJieqiDates()
lunar_years_db: Final[DecodedLunarYears] = DecodedLunarYears()

@functools.lru_cache(maxsize=512)
def get_min_supported_date(date_type: CalendarType) -> CalendarDate:
  # 1901-02-19 is the first day (in solar) in lunar year 1901.
  if date_type == CalendarType.SOLAR:
    return CalendarDate(1901, 2, 19, CalendarType.SOLAR)
  elif date_type == CalendarType.LUNAR:
    return CalendarDate(1901, 1, 1, CalendarType.LUNAR)
  elif date_type == CalendarType.GANZHI:
    return CalendarDate(1901, 1, 16, CalendarType.GANZHI)
  else:
    raise ValueError(f'Unsupported date_type: {date_type}')
  

@functools.lru_cache(maxsize=512)
def get_max_supported_date(date_type: CalendarType) -> CalendarDate:
  # Because of the implementation of `solar_to_lunar`, the last supported solar date will be 2099-12-31.
  if date_type == CalendarType.SOLAR:
    return CalendarDate(2099, 12, 31, CalendarType.SOLAR)
  elif date_type == CalendarType.LUNAR:
    return CalendarDate(2099, 12, 20, CalendarType.LUNAR) # 2099 is a leap year on lunar calendar.
  elif date_type == CalendarType.GANZHI:
    return CalendarDate(2099, 11, 25, CalendarType.GANZHI)
  else:
    raise ValueError(f'Unsupported date_type: {date_type}')


@functools.lru_cache(maxsize=512)
def is_valid_solar_date(d: CalendarDate) -> bool:
  '''
  Check if the input date is valid.
  Will also check if the date is in the supported range. If not, return False.

  Args: 
    - d: CalendarDate object, expected to be of `CalendarType.SOLAR`.

  Return: True if valid, False otherwise.
  '''

  if d.date_type != CalendarType.SOLAR:
    return False
  if d < get_min_supported_date(CalendarType.SOLAR):
    return False
  if d > get_max_supported_date(CalendarType.SOLAR):
    return False

  if d.year <= 0:
    return False # pragma: no cover # Already returning False in above "< min_supported_date" check.
  if d.month < 1 or d.month > 12:
    return False
  
  if d.month in [1, 3, 5, 7, 8, 10, 12]:
    if d.day < 1 or d.day > 31:
      return False
  elif d.month in [4, 6, 9, 11]:
    if d.day < 1 or d.day > 30:
      return False
  else:
    assert d.month == 2
    if calendar.isleap(d.year):
      if d.day < 1 or d.day > 29:
        return False
    else:
      if d.day < 1 or d.day > 28:
        return False

  return True


@functools.lru_cache(maxsize=512)
def is_valid_lunar_date(d: CalendarDate) -> bool:
  '''
  Check if the input date is valid.
  Will also check if the date is in the supported range. If not, return False.

  Args: 
    - d: CalendarDate object, expected to be of `CalendarType.LUNAR`.

  Return: True if valid, False otherwise.
  '''

  if d.date_type != CalendarType.LUNAR:
    return False
  if d < get_min_supported_date(CalendarType.LUNAR):
    return False
  if d > get_max_supported_date(CalendarType.LUNAR):
    return False
  
  info: LunarYearInfo = lunar_years_db.get(d.year)
  
  if d.year <= 0:
    return False # pragma: no cover # Already returning False in above "< min_supported_date" check.
  if d.month < 1 or d.month > len(info['days_counts']):
    return False 
  if d.day < 1 or d.day > 30:
    return False
  
  days_in_month: int = info['days_counts'][d.month - 1]
  return d.day <= days_in_month


@functools.lru_cache(maxsize=512)
def is_valid_ganzhi_date(d: CalendarDate) -> bool:
  '''
  Check if the input date is valid.
  Will also check if the date is in the supported range. If not, return False.

  Args: 
    - d: CalendarDate object, expected to be of `CalendarType.GANZHI`.

  Return: True if valid, False otherwise.
  '''

  if d.date_type != CalendarType.GANZHI:
    return False
  if d < get_min_supported_date(CalendarType.GANZHI):
    return False
  if d > get_max_supported_date(CalendarType.GANZHI):
    return False
  
  if d.year <= 0:
    return False # pragma: no cover # Already returning False in above "< min_supported_date" check.
  if d.month < 1 or d.month > 12:
    return False 
  if d.day < 1 or d.day > 32: # Max gap between Ganzhi months is 32 days.
    return False
  
  days_counts: list[int] = days_counts_in_ganzhi_year(d.year)
  return d.day <= days_counts[d.month - 1]


@functools.lru_cache(maxsize=512)
def is_valid(d: CalendarDate) -> bool:
  if d.date_type not in [CalendarType.SOLAR, CalendarType.LUNAR, CalendarType.GANZHI]:
    return False

  if d.date_type == CalendarType.SOLAR:
    return is_valid_solar_date(d)
  elif d.date_type == CalendarType.LUNAR:
    return is_valid_lunar_date(d)
  else:
    assert d.date_type == CalendarType.GANZHI
    return is_valid_ganzhi_date(d)


def days_counts_in_ganzhi_year(ganzhi_year: int) -> list[int]:
  # A fresh list per call, from a cache that holds a tuple: returning the cached list
  # itself would let a caller's in-place edit poison every later answer.
  return list(__days_counts_in_ganzhi_year(ganzhi_year))


@functools.lru_cache(maxsize=512)
def __days_counts_in_ganzhi_year(ganzhi_year: int) -> tuple[int, ...]:
  if ganzhi_year > get_max_supported_date(CalendarType.GANZHI).year:
    raise ValueError(f'Ganzhi year {ganzhi_year} is out of the supported range '
                     f'[{get_min_supported_date(CalendarType.GANZHI).year}, {get_max_supported_date(CalendarType.GANZHI).year}]')

  jieqi_list: list[Jieqi] = Jieqi.as_list()[::2] # Pick the Jieqis when new months start.
  assert jieqi_list[0] == Jieqi.立春 # The first jieqi in every year should be 立春.
  assert len(jieqi_list) == 12

  start_dates: list[date] = []
  for jq in jieqi_list[:11]: # First 11 jieqis are in solar year `ganzhi_year`.
    start_dates.append(jieqi_dates_db.get(ganzhi_year, jq))
  for jq in jieqi_list[11:]: # Last 1 jieqis are in solar year `ganzhi_year + 1`.
    start_dates.append(jieqi_dates_db.get(ganzhi_year + 1, jq))
  
  end_dates: list[date] = start_dates[1:] + [jieqi_dates_db.get(ganzhi_year + 1, Jieqi.立春)]
  days_counts: tuple[int, ...] = tuple((end - start).days for start, end in zip(start_dates, end_dates))
  assert len(days_counts) == 12

  return days_counts


@functools.lru_cache(maxsize=512)
def lunar_to_solar(lunar_date: CalendarDate) -> CalendarDate:
  if lunar_date.date_type != CalendarType.LUNAR:
    raise ValueError(f'Expected a LUNAR date, got {lunar_date}')
  if not is_valid(lunar_date):
    raise ValueError(f'"{lunar_date}" is not a valid {lunar_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(lunar_date.date_type)}, {get_max_supported_date(lunar_date.date_type)}]')
  info: LunarYearInfo = lunar_years_db.get(lunar_date.year)

  passed_days_count: int = -1
  for month_idx in range(lunar_date.month - 1):
    passed_days_count += info['days_counts'][month_idx]
  passed_days_count += lunar_date.day

  first_solar_date: date = info['first_solar_day']
  cur_solar_date: date = first_solar_date + timedelta(days=passed_days_count)
  return CalendarDate(cur_solar_date.year, cur_solar_date.month, cur_solar_date.day, CalendarType.SOLAR)


@functools.lru_cache(maxsize=512)
def solar_to_lunar(solar_date: CalendarDate) -> CalendarDate:
  if solar_date.date_type != CalendarType.SOLAR:
    raise ValueError(f'Expected a SOLAR date, got {solar_date}')
  if not is_valid(solar_date):
    raise ValueError(f'"{solar_date}" is not a valid {solar_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(solar_date.date_type)}, {get_max_supported_date(solar_date.date_type)}]')

  # First, figure out the solar date falls into which lunar year.
  lunar_year: int = solar_date.year
  info: LunarYearInfo = lunar_years_db.get(lunar_year)
  first_solar_day: date = info['first_solar_day']
  if first_solar_day > date(solar_date.year, solar_date.month, solar_date.day):
    lunar_year -= 1
    info = lunar_years_db.get(lunar_year)
    first_solar_day = info['first_solar_day']

  # Compute how many days have passed since `first_solar_day`.
  passed_days_count: int = (date(solar_date.year, solar_date.month, solar_date.day) - first_solar_day).days

  # Then, figure out the solar date falls into which lunar month.
  days_counts: list[int] = info['days_counts']
  month_idx: int = 0
  while passed_days_count >= days_counts[month_idx]:
    passed_days_count -= days_counts[month_idx]
    month_idx += 1
  assert passed_days_count < days_counts[month_idx]

  return CalendarDate(lunar_year, month_idx + 1, passed_days_count + 1, CalendarType.LUNAR)


@functools.lru_cache(maxsize=512)
def ganzhi_to_solar(ganzhi_date: CalendarDate) -> CalendarDate:
  if ganzhi_date.date_type != CalendarType.GANZHI:
    raise ValueError(f'Expected a GANZHI date, got {ganzhi_date}')
  if not is_valid(ganzhi_date):
    raise ValueError(f'"{ganzhi_date}" is not a valid {ganzhi_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(ganzhi_date.date_type)}, {get_max_supported_date(ganzhi_date.date_type)}]')

  # Figure out how many days have passed in the ganzhi year.
  days_counts: list[int] = days_counts_in_ganzhi_year(ganzhi_date.year)
  passed_days_count: int = 0
  for month_idx in range(ganzhi_date.month - 1):
    passed_days_count += days_counts[month_idx]
  passed_days_count += ganzhi_date.day - 1

  # Figure out the solar date.
  first_solar_date: date = jieqi_dates_db.get(ganzhi_date.year, Jieqi.立春)
  cur_solar_date: date = first_solar_date + timedelta(days=passed_days_count)
  return CalendarDate(cur_solar_date.year, cur_solar_date.month, cur_solar_date.day, CalendarType.SOLAR)


@functools.lru_cache(maxsize=512)
def solar_to_ganzhi(solar_date: CalendarDate) -> CalendarDate:
  if solar_date.date_type != CalendarType.SOLAR:
    raise ValueError(f'Expected a SOLAR date, got {solar_date}')
  if not is_valid(solar_date):
    raise ValueError(f'"{solar_date}" is not a valid {solar_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(solar_date.date_type)}, {get_max_supported_date(solar_date.date_type)}]')

  # Figure out the ganzhi date falls into which ganzhi year.
  ganzhi_year: int = solar_date.year
  first_solar_day: date = jieqi_dates_db.get(ganzhi_year, Jieqi.立春)
  if first_solar_day > date(solar_date.year, solar_date.month, solar_date.day): # Falls into the previous ganzhi year.
    ganzhi_year -= 1
    first_solar_day = jieqi_dates_db.get(ganzhi_year, Jieqi.立春)

  # Compute how many days have passed in the ganzhi year.
  passed_days_count: int = (date(solar_date.year, solar_date.month, solar_date.day) - first_solar_day).days

  # Then, figure out the ganzhi date falls into which ganzhi month.
  days_counts: list[int] = days_counts_in_ganzhi_year(ganzhi_year)
  month_idx: int = 0
  while passed_days_count >= days_counts[month_idx]:
    passed_days_count -= days_counts[month_idx]
    month_idx += 1
  assert passed_days_count < days_counts[month_idx]

  return CalendarDate(ganzhi_year, month_idx + 1, passed_days_count + 1, CalendarType.GANZHI)


@functools.lru_cache(maxsize=512)
def lunar_to_ganzhi(lunar_date: CalendarDate) -> CalendarDate:
  if lunar_date.date_type != CalendarType.LUNAR:
    raise ValueError(f'Expected a LUNAR date, got {lunar_date}')
  if not is_valid(lunar_date):
    raise ValueError(f'"{lunar_date}" is not a valid {lunar_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(lunar_date.date_type)}, {get_max_supported_date(lunar_date.date_type)}]')

  solar_date: CalendarDate = lunar_to_solar(lunar_date)
  return solar_to_ganzhi(solar_date)
  

@functools.lru_cache(maxsize=512)
def ganzhi_to_lunar(ganzhi_date: CalendarDate) -> CalendarDate:
  if ganzhi_date.date_type != CalendarType.GANZHI:
    raise ValueError(f'Expected a GANZHI date, got {ganzhi_date}')
  if not is_valid(ganzhi_date):
    raise ValueError(f'"{ganzhi_date}" is not a valid {ganzhi_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(ganzhi_date.date_type)}, {get_max_supported_date(ganzhi_date.date_type)}]')

  solar_date: CalendarDate = ganzhi_to_solar(ganzhi_date)
  return solar_to_lunar(solar_date)


@functools.lru_cache(maxsize=512)
def __to_calendardate(d: date | CalendarDate) -> CalendarDate:
  if isinstance(d, date):
    ret = CalendarDate(d.year, d.month, d.day, CalendarType.SOLAR)
  elif isinstance(d, CalendarDate):
    ret = d
  else:
    raise TypeError(f'Expected date or CalendarDate, got {type(d)}')

  if not is_valid(ret):
    raise ValueError(f'"{ret}" is not a valid {ret.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(ret.date_type)}, {get_max_supported_date(ret.date_type)}]')
  return ret


@functools.lru_cache(maxsize=512)
def to_solar(d: date | CalendarDate) -> CalendarDate:
  '''
  Convert the input date to a `CalendarDate` with `SOLAR` type.
  
  Args:
  - d: (date | CalendarDate) The input date.
    - If `d` is of `date` type, it will be interpreted as a solar date.

  Return: (CalendarDate) a converted date with `SOLAR` type.
  '''

  calendardate: CalendarDate = __to_calendardate(d) # `calendardate` is already validated.

  if calendardate.date_type == CalendarType.SOLAR:
    return calendardate
  elif calendardate.date_type == CalendarType.LUNAR:
    return lunar_to_solar(calendardate)
  else:
    assert calendardate.date_type == CalendarType.GANZHI
    return ganzhi_to_solar(calendardate)


@functools.lru_cache(maxsize=512)
def to_lunar(d: date | CalendarDate) -> CalendarDate:
  '''
  Convert the input date to a `CalendarDate` with `LUNAR` type.

  Args:
  - d: (date | CalendarDate) The input date.
    - If `d` is of `date` type, it will be interpreted as a solar date.

  Return: (CalendarDate) a converted date with `LUNAR` type.
  '''

  calendardate: CalendarDate = __to_calendardate(d) # `calendardate` is already validated.

  if calendardate.date_type == CalendarType.LUNAR:
    return calendardate
  elif calendardate.date_type == CalendarType.SOLAR:
    return solar_to_lunar(calendardate)
  else:
    assert calendardate.date_type == CalendarType.GANZHI
    return ganzhi_to_lunar(calendardate)
  

@functools.lru_cache(maxsize=512)
def to_ganzhi(d: date | CalendarDate) -> CalendarDate:
  '''
  Convert the input date to a `CalendarDate` with `GANZHI` type.

  Args:
  - d: (date | CalendarDate) The input date.
    - If `d` is of `date` type, it will be interpreted as a solar date.

  Return: (CalendarDate) a converted date with `GANZHI` type.
  '''

  calendardate: CalendarDate = __to_calendardate(d) # `calendardate` is already validated.

  if calendardate.date_type == CalendarType.GANZHI:
    return calendardate
  elif calendardate.date_type == CalendarType.SOLAR:
    return solar_to_ganzhi(calendardate)
  else:
    assert calendardate.date_type == CalendarType.LUNAR
    return lunar_to_ganzhi(calendardate)


@functools.lru_cache(maxsize=512)
def to_date(d: date | CalendarDate) -> date:
  '''
  Convert the input date to a `date` type.

  Args:
  - d: (date | CalendarDate) The input date.
    - If `d` is of `datetime` type, it will be casted to `date`.

  Return: (date) a converted date with `date` type.
  '''

  calendardate: CalendarDate = __to_calendardate(d) # `calendardate` is already validated.
  solar_date: CalendarDate = to_solar(calendardate)
  return date(solar_date.year, solar_date.month, solar_date.day)


@functools.lru_cache(maxsize=512)
def jieqi_date(solar_year: int, jieqi: Jieqi) -> date:
  '''
  Find out the date of the given Jieqi in the given solar/gregorian year.
  输入公历年份和节气，返回节气日期。

  Args:
  - solar_year: (int) The solar year.
  - jieqi: (Jieqi) The Jieqi.

  Return: (date) The date of the Jieqi in the given solar/gregorian year.
  '''

  if not isinstance(solar_year, int):
    raise TypeError(f'Expected int, got {type(solar_year)}')
  if not isinstance(jieqi, Jieqi):
    raise TypeError(f'Expected Jieqi, got {type(jieqi)}')

  if solar_year not in jieqi_dates_db.supported_year_range():
    raise ValueError(f'Year {solar_year} is out of the supported range {jieqi_dates_db.supported_year_range()}')
  return jieqi_dates_db.get(solar_year, jieqi)


@functools.lru_cache(maxsize=512)
def jieqi_moment(solar_year: int, jieqi: Jieqi) -> datetime:
  '''
  Find out the accurate moment (datetime) of the given Jieqi in the given solar/gregorian year.
  输入公历年份和节气，返回节气的具体时刻。

  Args:
  - solar_year: (int) The solar year.
  - jieqi: (Jieqi) The Jieqi.

  Note:
  - Hongkong Observatory's data is only at day-level precision.
  - So the returned moment is always at the beginning of the day.
  - 香港天文台只提供精度到日的数据。所以返回值是节气当日的 00:00:00。

  Return: (datetime) The accurate moment of the Jieqi in the given solar/gregorian year.
  '''

  if not isinstance(solar_year, int):
    raise TypeError(f'Expected int, got {type(solar_year)}')
  if not isinstance(jieqi, Jieqi):
    raise TypeError(f'Expected Jieqi, got {type(jieqi)}')

  if solar_year not in jieqi_dates_db.supported_year_range():
    raise ValueError(f'Year {solar_year} is out of the supported range {jieqi_dates_db.supported_year_range()}')
  dt: date = jieqi_dates_db.get(solar_year, jieqi)
  return datetime.combine(dt, time(0, 0, 0))


@functools.cache
def supported_jie_boundaries() -> tuple[datetime, datetime]:
  '''
  Return a tuple of datetimes representing the first and last supported Jie accurate time.
  When using methods `prev_jie` and `next_jie`, the input datetime should be in: 
  `[returned_tuple[0], returned_tuple[1])` (`returned_tuple[0]` included, `returned_tuple[1]` not).
  '''
  supported_first_year: int = jieqi_dates_db.start_year
  supported_last_year: int = jieqi_dates_db.end_year
  return (
    jieqi_moment(supported_first_year, Jieqi.小寒), # 小寒 is the first Jie of any solar year.
    jieqi_moment(supported_last_year, Jieqi.大雪), # 大雪 is the last Jie of any solar year.
  )


@functools.lru_cache(maxsize=512)
def prev_jie(dt: datetime) -> JieqiTime:
  '''
  Find out the previous Jie (节), not Jieqi, for the given solar datetime.
  输入某时间点，返回这个时间点之前的一个节令（不包含中气），以及对应的时间点。

  Args:
  - dt: (datetime) The datetime.

  Return: (JieqiTime) The previous Jie (节), and its solar datetime.

  Examples:
  - prev_jie(jieqi_moment(2024, Jieqi.小寒))
    - return: (Jieqi.小寒, jieqi_moment(2024, Jieqi.小寒))
  - prev_jie(jieqi_moment(2024, Jieqi.小寒) + timedelta(seconds=1))
    - return: (Jieqi.小寒, jieqi_moment(2024, Jieqi.小寒))
  - prev_jie(jieqi_moment(2024, Jieqi.小寒) - timedelta(seconds=1))
    - return: (Jieqi.大雪, jieqi_moment(2023, Jieqi.大雪))
  '''

  if not isinstance(dt, datetime):
    raise TypeError(f'Expected datetime, got {type(dt)}')

  supported_jie_range: tuple[datetime, datetime] = supported_jie_boundaries()
  if dt < supported_jie_range[0]:
    raise ValueError(f'"{dt}" is out of the supported range. The first available Jie is "{supported_jie_range[0]}"')
  if dt >= supported_jie_range[1]:
    raise ValueError(f'"{dt}" is out of the supported range. The last available Jie is "{supported_jie_range[1]}"')

  daxue_dt: datetime = jieqi_moment(dt.year, Jieqi.大雪)
  if dt >= daxue_dt:
    return JieqiTime(Jieqi.大雪, daxue_dt)

  reversed_jies: list[Jieqi] = list(reversed(Jieqi.as_list(ganzhi_year=False)[::2]))
  for jie1, jie2 in zip(reversed_jies[1:], reversed_jies):
    jie1_dt: datetime = jieqi_moment(dt.year, jie1)
    jie2_dt: datetime = jieqi_moment(dt.year, jie2)
    if jie1_dt <= dt < jie2_dt:
      return JieqiTime(jie1, jie1_dt)

  last_daxue_dt: datetime = jieqi_moment(dt.year - 1, Jieqi.大雪)
  assert last_daxue_dt <= dt
  return JieqiTime(Jieqi.大雪, last_daxue_dt)


@functools.lru_cache(maxsize=512)
def next_jie(dt: datetime) -> JieqiTime:
  '''
  Find out the next Jie (节), not Jieqi, for the given solar datetime.
  输入某时间点，返回这个时间点之后的一个节令（不包含中气），以及对应的时间点。

  Args:
  - dt: (datetime) The datetime.

  Return: (JieqiTime) The next Jie (节), and its solar datetime.

  Examples:
  - next_jie(jieqi_moment(2024, Jieqi.小寒))
    - return: (Jieqi.立春, jieqi_moment(2024, Jieqi.立春))
  - next_jie(jieqi_moment(2024, Jieqi.小寒) + timedelta(seconds=1))
    - return: (Jieqi.立春, jieqi_moment(2024, Jieqi.立春))
  - next_jie(jieqi_moment(2024, Jieqi.小寒) - timedelta(seconds=1))
    - return: (Jieqi.小寒, jieqi_moment(2024, Jieqi.小寒))
  '''

  if not isinstance(dt, datetime):
    raise TypeError(f'Expected datetime, got {type(dt)}')

  supported_jie_range: tuple[datetime, datetime] = supported_jie_boundaries()
  if dt < supported_jie_range[0]:
    raise ValueError(f'"{dt}" is out of the supported range. The first available Jie is "{supported_jie_range[0]}"')
  if dt >= supported_jie_range[1]:
    raise ValueError(f'"{dt}" is out of the supported range. The last available Jie is "{supported_jie_range[1]}"')

  xiaohan_dt: datetime = jieqi_moment(dt.year, Jieqi.小寒)
  if dt < xiaohan_dt:
    return JieqiTime(Jieqi.小寒, xiaohan_dt)
  
  jies: list[Jieqi] = Jieqi.as_list(ganzhi_year=False)[::2]
  for jie1, jie2 in itertools.pairwise(jies):
    jie1_dt: datetime = jieqi_moment(dt.year, jie1)
    jie2_dt: datetime = jieqi_moment(dt.year, jie2)
    if jie1_dt <= dt < jie2_dt:
      return JieqiTime(jie2, jie2_dt)

  next_xiaohan_dt: datetime = jieqi_moment(dt.year + 1, Jieqi.小寒)
  assert dt < next_xiaohan_dt
  return JieqiTime(Jieqi.小寒, next_xiaohan_dt)
