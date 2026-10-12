# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import calendar  # 标准库模块，不是本文件所在的 bazi.calendar 包。
import functools
import itertools

from datetime import date, time, datetime, timedelta
from typing import Final

from .dates import CalendarType, CalendarDate, JieqiTime
from .hko_data import DecodedJieqiDates, DecodedLunarYears, LunarYearInfo

from ..defines import Jieqi


# 模块级节气日期与农历年数据库。
jieqi_dates_db: Final[DecodedJieqiDates] = DecodedJieqiDates()
lunar_years_db: Final[DecodedLunarYears] = DecodedLunarYears()

def get_min_supported_date(date_type: CalendarType) -> CalendarDate:
  if not isinstance(date_type, CalendarType):
    raise TypeError(f'Expected CalendarType, got {type(date_type)}')
  return __get_min_supported_date(date_type)


@functools.lru_cache(maxsize=512)
def __get_min_supported_date(date_type: CalendarType) -> CalendarDate:
  # 农历 1901 年首日为公历 1901-02-19。
  if date_type == CalendarType.SOLAR:
    return CalendarDate(1901, 2, 19, CalendarType.SOLAR)
  elif date_type == CalendarType.LUNAR:
    return CalendarDate(1901, 1, 1, CalendarType.LUNAR)
  elif date_type == CalendarType.GANZHI:
    return CalendarDate(1901, 1, 16, CalendarType.GANZHI)
  else:
    raise ValueError(f'Unsupported date_type: {date_type}') # pragma: no cover # 上方已处理全部 CalendarType 成员。
  

def get_max_supported_date(date_type: CalendarType) -> CalendarDate:
  if not isinstance(date_type, CalendarType):
    raise TypeError(f'Expected CalendarType, got {type(date_type)}')
  return __get_max_supported_date(date_type)


@functools.lru_cache(maxsize=512)
def __get_max_supported_date(date_type: CalendarType) -> CalendarDate:
  # solar_to_lunar 先按公历年查表，支持的末公历日为 2099-12-31。
  if date_type == CalendarType.SOLAR:
    return CalendarDate(2099, 12, 31, CalendarType.SOLAR)
  elif date_type == CalendarType.LUNAR:
    return CalendarDate(2099, 12, 20, CalendarType.LUNAR) # 农历 2099 年有闰月。
  elif date_type == CalendarType.GANZHI:
    return CalendarDate(2099, 11, 25, CalendarType.GANZHI)
  else:
    raise ValueError(f'Unsupported date_type: {date_type}') # pragma: no cover # 上方已处理全部 CalendarType 成员。


def is_valid_solar_date(d: CalendarDate) -> bool:
  '''
  检查公历日期是否合法且在支持范围内。

  Args: 
  - d: (CalendarDate) 待查公历日期，类型应为 `CalendarType.SOLAR`。

  Return: (bool) 合法且受支持时为 True，否则为 False。
  '''

  if not isinstance(d, CalendarDate):
    raise TypeError(f'Expected CalendarDate, got {type(d)}')
  return __is_valid_solar_date(d)


@functools.lru_cache(maxsize=512)
def __is_valid_solar_date(d: CalendarDate) -> bool:
  if d.date_type != CalendarType.SOLAR:
    return False
  if d < get_min_supported_date(CalendarType.SOLAR):
    return False
  if d > get_max_supported_date(CalendarType.SOLAR):
    return False

  if d.month < 1 or d.month > 12:
    return False
  return 1 <= d.day <= calendar.monthrange(d.year, d.month)[1]


def is_valid_lunar_date(d: CalendarDate) -> bool:
  '''
  检查农历日期是否合法且在支持范围内。

  Args: 
  - d: (CalendarDate) 待查农历日期，类型应为 `CalendarType.LUNAR`。

  Return: (bool) 合法且受支持时为 True，否则为 False。
  '''

  if not isinstance(d, CalendarDate):
    raise TypeError(f'Expected CalendarDate, got {type(d)}')
  return __is_valid_lunar_date(d)


@functools.lru_cache(maxsize=512)
def __is_valid_lunar_date(d: CalendarDate) -> bool:
  if d.date_type != CalendarType.LUNAR:
    return False
  if d < get_min_supported_date(CalendarType.LUNAR):
    return False
  if d > get_max_supported_date(CalendarType.LUNAR):
    return False
  
  info: LunarYearInfo = lunar_years_db.get(d.year)
  
  if d.month < 1 or d.month > len(info['days_counts']):
    return False 
  if d.day < 1 or d.day > 30:
    return False
  
  days_in_month: int = info['days_counts'][d.month - 1]
  return d.day <= days_in_month


def is_valid_ganzhi_date(d: CalendarDate) -> bool:
  '''
  检查干支历日期是否合法且在支持范围内。

  Args: 
  - d: (CalendarDate) 待查干支历日期，类型应为 `CalendarType.GANZHI`。

  Return: (bool) 合法且受支持时为 True，否则为 False。
  '''

  if not isinstance(d, CalendarDate):
    raise TypeError(f'Expected CalendarDate, got {type(d)}')
  return __is_valid_ganzhi_date(d)


@functools.lru_cache(maxsize=512)
def __is_valid_ganzhi_date(d: CalendarDate) -> bool:
  if d.date_type != CalendarType.GANZHI:
    return False
  if d < get_min_supported_date(CalendarType.GANZHI):
    return False
  if d > get_max_supported_date(CalendarType.GANZHI):
    return False
  
  if d.month < 1 or d.month > 12:
    return False 
  if d.day < 1 or d.day > 32: # 干支月长最多三十二日。
    return False
  
  days_counts: list[int] = days_counts_in_ganzhi_year(d.year)
  return d.day <= days_counts[d.month - 1]


def is_valid(d: CalendarDate) -> bool:
  if not isinstance(d, CalendarDate):
    raise TypeError(f'Expected CalendarDate, got {type(d)}')
  return __is_valid(d)


@functools.lru_cache(maxsize=512)
def __is_valid(d: CalendarDate) -> bool:
  if d.date_type == CalendarType.SOLAR:
    return is_valid_solar_date(d)
  elif d.date_type == CalendarType.LUNAR:
    return is_valid_lunar_date(d)
  else:
    assert d.date_type == CalendarType.GANZHI
    return is_valid_ganzhi_date(d)


def days_counts_in_ganzhi_year(ganzhi_year: int) -> list[int]:
  if not isinstance(ganzhi_year, int):
    raise TypeError(f'Expected int, got {type(ganzhi_year)}')
  # 缓存持有元组，每次返回独立列表，避免调用方修改后影响后续结果。
  return list(__days_counts_in_ganzhi_year(ganzhi_year))


@functools.lru_cache(maxsize=512)
def __days_counts_in_ganzhi_year(ganzhi_year: int) -> tuple[int, ...]:
  if ganzhi_year > get_max_supported_date(CalendarType.GANZHI).year:
    raise ValueError(f'Ganzhi year {ganzhi_year} is out of the supported range '
                     f'[{get_min_supported_date(CalendarType.GANZHI).year}, {get_max_supported_date(CalendarType.GANZHI).year}]')

  jieqi_list = Jieqi.jies()

  start_dates: list[date] = []
  for jq in jieqi_list[:11]: # 前十一节在 ganzhi_year 公历年。
    start_dates.append(jieqi_dates_db.get(ganzhi_year, jq))
  for jq in jieqi_list[11:]: # 末节在下一公历年。
    start_dates.append(jieqi_dates_db.get(ganzhi_year + 1, jq))
  
  end_dates: list[date] = start_dates[1:] + [jieqi_dates_db.get(ganzhi_year + 1, Jieqi.立春)]
  days_counts: tuple[int, ...] = tuple((end - start).days for start, end in zip(start_dates, end_dates))
  assert len(days_counts) == 12

  return days_counts


def lunar_to_solar(lunar_date: CalendarDate) -> CalendarDate:
  if not isinstance(lunar_date, CalendarDate):
    raise TypeError(f'Expected CalendarDate, got {type(lunar_date)}')
  return __lunar_to_solar(lunar_date)


@functools.lru_cache(maxsize=512)
def __lunar_to_solar(lunar_date: CalendarDate) -> CalendarDate:
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


def solar_to_lunar(solar_date: CalendarDate) -> CalendarDate:
  if not isinstance(solar_date, CalendarDate):
    raise TypeError(f'Expected CalendarDate, got {type(solar_date)}')
  return __solar_to_lunar(solar_date)


@functools.lru_cache(maxsize=512)
def __solar_to_lunar(solar_date: CalendarDate) -> CalendarDate:
  if solar_date.date_type != CalendarType.SOLAR:
    raise ValueError(f'Expected a SOLAR date, got {solar_date}')
  if not is_valid(solar_date):
    raise ValueError(f'"{solar_date}" is not a valid {solar_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(solar_date.date_type)}, {get_max_supported_date(solar_date.date_type)}]')

  # 定位所属农历年。
  lunar_year: int = solar_date.year
  info: LunarYearInfo = lunar_years_db.get(lunar_year)
  first_solar_day: date = info['first_solar_day']
  if first_solar_day > date(solar_date.year, solar_date.month, solar_date.day):
    lunar_year -= 1
    info = lunar_years_db.get(lunar_year)
    first_solar_day = info['first_solar_day']

  # 计算距农历年首日的日数。
  passed_days_count: int = (date(solar_date.year, solar_date.month, solar_date.day) - first_solar_day).days

  # 定位所属农历月。
  days_counts: list[int] = info['days_counts']
  month_idx: int = 0
  while passed_days_count >= days_counts[month_idx]:
    passed_days_count -= days_counts[month_idx]
    month_idx += 1
  assert passed_days_count < days_counts[month_idx]

  return CalendarDate(lunar_year, month_idx + 1, passed_days_count + 1, CalendarType.LUNAR)


def ganzhi_to_solar(ganzhi_date: CalendarDate) -> CalendarDate:
  if not isinstance(ganzhi_date, CalendarDate):
    raise TypeError(f'Expected CalendarDate, got {type(ganzhi_date)}')
  return __ganzhi_to_solar(ganzhi_date)


@functools.lru_cache(maxsize=512)
def __ganzhi_to_solar(ganzhi_date: CalendarDate) -> CalendarDate:
  if ganzhi_date.date_type != CalendarType.GANZHI:
    raise ValueError(f'Expected a GANZHI date, got {ganzhi_date}')
  if not is_valid(ganzhi_date):
    raise ValueError(f'"{ganzhi_date}" is not a valid {ganzhi_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(ganzhi_date.date_type)}, {get_max_supported_date(ganzhi_date.date_type)}]')

  # 计算距干支年首日的日数。
  days_counts: list[int] = days_counts_in_ganzhi_year(ganzhi_date.year)
  passed_days_count: int = 0
  for month_idx in range(ganzhi_date.month - 1):
    passed_days_count += days_counts[month_idx]
  passed_days_count += ganzhi_date.day - 1

  # 从立春日推公历日期。
  first_solar_date: date = jieqi_dates_db.get(ganzhi_date.year, Jieqi.立春)
  cur_solar_date: date = first_solar_date + timedelta(days=passed_days_count)
  return CalendarDate(cur_solar_date.year, cur_solar_date.month, cur_solar_date.day, CalendarType.SOLAR)


def solar_to_ganzhi(solar_date: CalendarDate) -> CalendarDate:
  if not isinstance(solar_date, CalendarDate):
    raise TypeError(f'Expected CalendarDate, got {type(solar_date)}')
  return __solar_to_ganzhi(solar_date)


@functools.lru_cache(maxsize=512)
def __solar_to_ganzhi(solar_date: CalendarDate) -> CalendarDate:
  if solar_date.date_type != CalendarType.SOLAR:
    raise ValueError(f'Expected a SOLAR date, got {solar_date}')
  if not is_valid(solar_date):
    raise ValueError(f'"{solar_date}" is not a valid {solar_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(solar_date.date_type)}, {get_max_supported_date(solar_date.date_type)}]')

  # 定位所属干支年。
  ganzhi_year: int = solar_date.year
  first_solar_day: date = jieqi_dates_db.get(ganzhi_year, Jieqi.立春)
  if first_solar_day > date(solar_date.year, solar_date.month, solar_date.day): # 属于上一干支年。
    ganzhi_year -= 1
    first_solar_day = jieqi_dates_db.get(ganzhi_year, Jieqi.立春)

  # 计算距干支年首日的日数。
  passed_days_count: int = (date(solar_date.year, solar_date.month, solar_date.day) - first_solar_day).days

  # 定位所属干支月。
  days_counts: list[int] = days_counts_in_ganzhi_year(ganzhi_year)
  month_idx: int = 0
  while passed_days_count >= days_counts[month_idx]:
    passed_days_count -= days_counts[month_idx]
    month_idx += 1
  assert passed_days_count < days_counts[month_idx]

  return CalendarDate(ganzhi_year, month_idx + 1, passed_days_count + 1, CalendarType.GANZHI)


def lunar_to_ganzhi(lunar_date: CalendarDate) -> CalendarDate:
  if not isinstance(lunar_date, CalendarDate):
    raise TypeError(f'Expected CalendarDate, got {type(lunar_date)}')
  return __lunar_to_ganzhi(lunar_date)


@functools.lru_cache(maxsize=512)
def __lunar_to_ganzhi(lunar_date: CalendarDate) -> CalendarDate:
  if lunar_date.date_type != CalendarType.LUNAR:
    raise ValueError(f'Expected a LUNAR date, got {lunar_date}')
  if not is_valid(lunar_date):
    raise ValueError(f'"{lunar_date}" is not a valid {lunar_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(lunar_date.date_type)}, {get_max_supported_date(lunar_date.date_type)}]')

  solar_date: CalendarDate = lunar_to_solar(lunar_date)
  return solar_to_ganzhi(solar_date)
  

def ganzhi_to_lunar(ganzhi_date: CalendarDate) -> CalendarDate:
  if not isinstance(ganzhi_date, CalendarDate):
    raise TypeError(f'Expected CalendarDate, got {type(ganzhi_date)}')
  return __ganzhi_to_lunar(ganzhi_date)


@functools.lru_cache(maxsize=512)
def __ganzhi_to_lunar(ganzhi_date: CalendarDate) -> CalendarDate:
  if ganzhi_date.date_type != CalendarType.GANZHI:
    raise ValueError(f'Expected a GANZHI date, got {ganzhi_date}')
  if not is_valid(ganzhi_date):
    raise ValueError(f'"{ganzhi_date}" is not a valid {ganzhi_date.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(ganzhi_date.date_type)}, {get_max_supported_date(ganzhi_date.date_type)}]')

  solar_date: CalendarDate = ganzhi_to_solar(ganzhi_date)
  return solar_to_lunar(solar_date)


def __to_calendardate(d: date | CalendarDate) -> CalendarDate:
  # 缓存前先投影民用年月日；相等的带时区 datetime 可有不同民用日期。
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


def to_solar(d: date | CalendarDate) -> CalendarDate:
  '''
  把输入转换为公历 CalendarDate。
  
  Args:
  - d: (date | CalendarDate) 输入日期；date 按公历解释。

  Return: (CalendarDate) SOLAR 类型日期。
  '''

  return __to_solar(
    __to_calendardate(d),
  )


@functools.lru_cache(maxsize=512)
def __to_solar(calendardate: CalendarDate) -> CalendarDate:
  if calendardate.date_type == CalendarType.SOLAR:
    return calendardate
  elif calendardate.date_type == CalendarType.LUNAR:
    return lunar_to_solar(calendardate)
  else:
    assert calendardate.date_type == CalendarType.GANZHI
    return ganzhi_to_solar(calendardate)


def to_lunar(d: date | CalendarDate) -> CalendarDate:
  '''
  把输入转换为农历 CalendarDate。

  Args:
  - d: (date | CalendarDate) 输入日期；date 按公历解释。

  Return: (CalendarDate) LUNAR 类型日期。
  '''

  return __to_lunar(
    __to_calendardate(d),
  )


@functools.lru_cache(maxsize=512)
def __to_lunar(calendardate: CalendarDate) -> CalendarDate:
  if calendardate.date_type == CalendarType.LUNAR:
    return calendardate
  elif calendardate.date_type == CalendarType.SOLAR:
    return solar_to_lunar(calendardate)
  else:
    assert calendardate.date_type == CalendarType.GANZHI
    return ganzhi_to_lunar(calendardate)
  

def to_ganzhi(d: date | CalendarDate) -> CalendarDate:
  '''
  把输入转换为干支历 CalendarDate。

  Args:
  - d: (date | CalendarDate) 输入日期；date 按公历解释。

  Return: (CalendarDate) GANZHI 类型日期。
  '''

  return __to_ganzhi(
    __to_calendardate(d),
  )


@functools.lru_cache(maxsize=512)
def __to_ganzhi(calendardate: CalendarDate) -> CalendarDate:
  if calendardate.date_type == CalendarType.GANZHI:
    return calendardate
  elif calendardate.date_type == CalendarType.SOLAR:
    return solar_to_ganzhi(calendardate)
  else:
    assert calendardate.date_type == CalendarType.LUNAR
    return lunar_to_ganzhi(calendardate)


def to_date(d: date | CalendarDate) -> date:
  '''
  把输入转换为公历 date。

  Args:
  - d: (date | CalendarDate) 输入日期；datetime 丢弃日内时刻，转换为日期。

  Return: (date) 公历日期。
  '''

  return __to_date(
    __to_calendardate(d),
  )


@functools.lru_cache(maxsize=512)
def __to_date(calendardate: CalendarDate) -> date:
  solar_date: CalendarDate = to_solar(calendardate)
  return date(solar_date.year, solar_date.month, solar_date.day)


@functools.lru_cache(maxsize=512)
def __jieqi_date(solar_year: int, jieqi: Jieqi) -> date:
  return jieqi_dates_db.get(solar_year, jieqi)


def jieqi_date(solar_year: int, jieqi: Jieqi) -> date:
  '''
  输入公历年份和节气，返回节气日期。

  Args:
  - solar_year: (int) 公历年。
  - jieqi: (Jieqi) 节气。

  Return: (date) 指定公历年的节气日期。
  '''

  if not isinstance(solar_year, int):
    raise TypeError(f'Expected int, got {type(solar_year)}')
  if not isinstance(jieqi, Jieqi):
    raise TypeError(f'Expected Jieqi, got {type(jieqi)}')

  if solar_year not in jieqi_dates_db.supported_year_range():
    raise ValueError(f'Year {solar_year} is out of the supported range {jieqi_dates_db.supported_year_range()}')
  return __jieqi_date(solar_year, jieqi)


@functools.lru_cache(maxsize=512)
def __jieqi_moment(solar_year: int, jieqi: Jieqi) -> datetime:
  dt: date = jieqi_dates_db.get(solar_year, jieqi)
  return datetime.combine(dt, time(0, 0, 0))


def jieqi_moment(solar_year: int, jieqi: Jieqi) -> datetime:
  '''
  输入公历年份和节气，返回节气当日的午夜占位时刻。

  Args:
  - solar_year: (int) 公历年。
  - jieqi: (Jieqi) 节气。

  Note:
  - 香港天文台只提供精度到日的数据。所以返回值是节气当日的 00:00:00。

  Return: (datetime) 指定公历年节气当日的 00:00:00。
  '''

  if not isinstance(solar_year, int):
    raise TypeError(f'Expected int, got {type(solar_year)}')
  if not isinstance(jieqi, Jieqi):
    raise TypeError(f'Expected Jieqi, got {type(jieqi)}')

  if solar_year not in jieqi_dates_db.supported_year_range():
    raise ValueError(f'Year {solar_year} is out of the supported range {jieqi_dates_db.supported_year_range()}')
  return __jieqi_moment(solar_year, jieqi)


@functools.cache
def supported_jie_boundaries() -> tuple[datetime, datetime]:
  '''
  返回首末支持节的时刻。prev_jie / next_jie 的输入须位于半开区间
  `[returned_tuple[0], returned_tuple[1])`，含首端、不含末端。
  '''
  supported_first_year: int = jieqi_dates_db.start_year
  supported_last_year: int = jieqi_dates_db.end_year
  return (
    jieqi_moment(supported_first_year, Jieqi.小寒), # 公历年首节。
    jieqi_moment(supported_last_year, Jieqi.大雪), # 公历年末节。
  )


def __check_jie_range(dt: datetime) -> None:
  first_jie, last_jie = supported_jie_boundaries()
  if dt < first_jie:
    raise ValueError(f'"{dt}" is out of the supported range. The first available Jie is "{first_jie}"')
  if dt >= last_jie:
    raise ValueError(f'"{dt}" is out of the supported range. The last available Jie is "{last_jie}"')


def prev_jie(dt: datetime) -> JieqiTime:
  '''
  返回不晚于输入公历时刻的最近一节及其时刻，不含中气，恰交节归该节。

  Args:
  - dt: (datetime) 待查时刻。

  Return: (JieqiTime) 所属节及其公历时刻。

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
  return __prev_jie(dt)


@functools.lru_cache(maxsize=512)
def __prev_jie(dt: datetime) -> JieqiTime:
  __check_jie_range(dt)

  daxue_dt: datetime = jieqi_moment(dt.year, Jieqi.大雪)
  if dt >= daxue_dt:
    return JieqiTime(Jieqi.大雪, daxue_dt)

  reversed_jies = tuple(reversed(Jieqi.jies(ganzhi_year=False)))
  for jie1, jie2 in zip(reversed_jies[1:], reversed_jies):
    jie1_dt: datetime = jieqi_moment(dt.year, jie1)
    jie2_dt: datetime = jieqi_moment(dt.year, jie2)
    if jie1_dt <= dt < jie2_dt:
      return JieqiTime(jie1, jie1_dt)

  last_daxue_dt: datetime = jieqi_moment(dt.year - 1, Jieqi.大雪)
  assert last_daxue_dt <= dt
  return JieqiTime(Jieqi.大雪, last_daxue_dt)


def next_jie(dt: datetime) -> JieqiTime:
  '''
  返回严格晚于输入公历时刻的最近一节及其时刻，不含中气。

  Args:
  - dt: (datetime) 待查时刻。

  Return: (JieqiTime) 下一节及其公历时刻。

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
  return __next_jie(dt)


@functools.lru_cache(maxsize=512)
def __next_jie(dt: datetime) -> JieqiTime:
  __check_jie_range(dt)

  xiaohan_dt: datetime = jieqi_moment(dt.year, Jieqi.小寒)
  if dt < xiaohan_dt:
    return JieqiTime(Jieqi.小寒, xiaohan_dt)
  
  jies = Jieqi.jies(ganzhi_year=False)
  for jie1, jie2 in itertools.pairwise(jies):
    jie1_dt: datetime = jieqi_moment(dt.year, jie1)
    jie2_dt: datetime = jieqi_moment(dt.year, jie2)
    if jie1_dt <= dt < jie2_dt:
      return JieqiTime(jie2, jie2_dt)

  next_xiaohan_dt: datetime = jieqi_moment(dt.year + 1, Jieqi.小寒)
  assert dt < next_xiaohan_dt
  return JieqiTime(Jieqi.小寒, next_xiaohan_dt)
