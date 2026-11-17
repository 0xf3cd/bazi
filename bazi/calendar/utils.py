# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''
读取预生成 celestial-calendar 表的历法工具，数据契约见 `celestial_data/SCHEMA.md`。

`jieqi_moment` 提供秒级真实时刻。CalendarDate 只表示日期，干支历正月初一为立春日；
时刻的四柱归属由调用方决定（#72）。农历月号按年内实际月序编号，闰月占独立序号。
'''

import functools

from datetime import date, datetime, timedelta

from .dates import CalendarType, CalendarDate, JieqiTime
from .celestial_data.loader import JieqiMomentTable, LunarYearTable
from ..defines import Jieqi


@functools.cache
def _jieqi_table() -> JieqiMomentTable:
  return JieqiMomentTable()


@functools.cache
def _lunar_table() -> LunarYearTable:
  return LunarYearTable()


#region 支持范围

def get_min_supported_date(date_type: CalendarType) -> CalendarDate:
  '''返回指定历法的首个支持日期。三种历法共用同一公历窗口。'''
  if not isinstance(date_type, CalendarType):
    raise TypeError(f'Expected CalendarType, got {type(date_type)}')
  return _get_min_supported_date(date_type)


@functools.lru_cache(maxsize=512)
def _get_min_supported_date(date_type: CalendarType) -> CalendarDate:
  if date_type == CalendarType.SOLAR:
    # 公历转农历先按公历年查表，因此以首个农历年的首日为起点。
    first = _lunar_table().get(min(_lunar_table().supported_year_range())).first_solar_day
    return CalendarDate(first.year, first.month, first.day, CalendarType.SOLAR)
  elif date_type == CalendarType.LUNAR:
    return _solar_to_lunar(get_min_supported_date(CalendarType.SOLAR))
  elif date_type == CalendarType.GANZHI:
    return _solar_to_ganzhi(get_min_supported_date(CalendarType.SOLAR))
  else:
    raise ValueError(f'Unsupported date_type: {date_type}') # pragma: no cover # 上方已处理全部 CalendarType 成员。


def get_max_supported_date(date_type: CalendarType) -> CalendarDate:
  '''返回指定历法的最后一个支持日期。'''
  if not isinstance(date_type, CalendarType):
    raise TypeError(f'Expected CalendarType, got {type(date_type)}')
  return _get_max_supported_date(date_type)


@functools.lru_cache(maxsize=512)
def _get_max_supported_date(date_type: CalendarType) -> CalendarDate:
  if date_type == CalendarType.SOLAR:
    # 末农历年即使延伸到下一公历年，下一公历年也没有可查的农历记录。
    last_year = max(_lunar_table().supported_year_range())
    return CalendarDate(last_year, 12, 31, CalendarType.SOLAR)
  elif date_type == CalendarType.LUNAR:
    return _solar_to_lunar(get_max_supported_date(CalendarType.SOLAR))
  elif date_type == CalendarType.GANZHI:
    return _solar_to_ganzhi(get_max_supported_date(CalendarType.SOLAR))
  else:
    raise ValueError(f'Unsupported date_type: {date_type}') # pragma: no cover # 上方已处理全部 CalendarType 成员。

#endregion


#region 日期有效性与月长

@functools.lru_cache(maxsize=512)
def _is_valid(d: CalendarDate) -> bool:
  if d < get_min_supported_date(d.date_type) or d > get_max_supported_date(d.date_type):
    return False

  if d.date_type == CalendarType.SOLAR:
    try:
      # 公历月长与闰年由标准库检查。
      date(d.year, d.month, d.day)
    except ValueError:
      return False
    return True
  elif d.date_type == CalendarType.LUNAR:
    days_counts = _lunar_table().get(d.year).days_counts
  else:
    assert d.date_type == CalendarType.GANZHI
    days_counts = _days_counts_in_ganzhi_year(d.year)

  if d.month < 1 or d.month > len(days_counts):
    return False
  return 1 <= d.day <= days_counts[d.month - 1]


@functools.lru_cache(maxsize=512)
def _days_counts_in_ganzhi_year(ganzhi_year: int) -> tuple[int, ...]:
  '''按连续节日期之差计算十二个干支月长。'''
  # 末干支月须以下一公历年立春作为终点。
  years = _jieqi_table().supported_year_range()
  if ganzhi_year not in years:
    raise ValueError(f'Ganzhi year {ganzhi_year} is out of the supported range {years}')
  if ganzhi_year + 1 not in years:
    raise ValueError(f'Ganzhi year {ganzhi_year} needs jieqi data of year {ganzhi_year + 1}, '
                     f'which is out of the supported range {years}')

  jies = Jieqi.jies()
  # 前十一节在 ganzhi_year 公历年，末节小寒在下一公历年。
  start_dates = [_jieqi_date(ganzhi_year, jq) for jq in jies[:11]]
  start_dates += [_jieqi_date(ganzhi_year + 1, jq) for jq in jies[11:]]
  end_dates = start_dates[1:] + [_jieqi_date(ganzhi_year + 1, Jieqi.立春)]
  return tuple((end - start).days for start, end in zip(start_dates, end_dates))

#endregion


#region 历法换算

# 定向换算只接收已校验且类型相符的 CalendarDate；支持范围推导也使用这些函数。
@functools.lru_cache(maxsize=512)
def _lunar_to_solar(lunar_date: CalendarDate) -> CalendarDate:
  info = _lunar_table().get(lunar_date.year)
  passed_days = sum(info.days_counts[:lunar_date.month - 1]) + lunar_date.day - 1
  solar = info.first_solar_day + timedelta(days=passed_days)
  return CalendarDate(solar.year, solar.month, solar.day, CalendarType.SOLAR)


@functools.lru_cache(maxsize=512)
def _solar_to_lunar(solar_date: CalendarDate) -> CalendarDate:
  solar = date(solar_date.year, solar_date.month, solar_date.day)
  # 公历年初日期可仍属于上一农历年。
  lunar_year = solar_date.year
  info = _lunar_table().get(lunar_year)
  if info.first_solar_day > solar:
    lunar_year -= 1
    info = _lunar_table().get(lunar_year)

  month_idx, day_idx = _walk_months((solar - info.first_solar_day).days, info.days_counts)
  return CalendarDate(lunar_year, month_idx + 1, day_idx + 1, CalendarType.LUNAR)


@functools.lru_cache(maxsize=512)
def _ganzhi_to_solar(ganzhi_date: CalendarDate) -> CalendarDate:
  days_counts = _days_counts_in_ganzhi_year(ganzhi_date.year)
  passed_days = sum(days_counts[:ganzhi_date.month - 1]) + ganzhi_date.day - 1
  solar = _jieqi_date(ganzhi_date.year, Jieqi.立春) + timedelta(days=passed_days)
  return CalendarDate(solar.year, solar.month, solar.day, CalendarType.SOLAR)


@functools.lru_cache(maxsize=512)
def _solar_to_ganzhi(solar_date: CalendarDate) -> CalendarDate:
  solar = date(solar_date.year, solar_date.month, solar_date.day)
  # 立春前的公历日期仍属于上一干支年。
  ganzhi_year = solar_date.year
  if _jieqi_date(ganzhi_year, Jieqi.立春) > solar:
    ganzhi_year -= 1

  passed_days = (solar - _jieqi_date(ganzhi_year, Jieqi.立春)).days
  month_idx, day_idx = _walk_months(passed_days, _days_counts_in_ganzhi_year(ganzhi_year))
  return CalendarDate(ganzhi_year, month_idx + 1, day_idx + 1, CalendarType.GANZHI)


def _walk_months(passed_days: int, days_counts: tuple[int, ...]) -> tuple[int, int]:
  '''把距年初的日偏移拆为月序号与日序号。'''
  month_idx = 0
  while passed_days >= days_counts[month_idx]:
    passed_days -= days_counts[month_idx]
    month_idx += 1
  return month_idx, passed_days


def _to_calendardate(d: date | CalendarDate) -> CalendarDate:
  # 缓存前先投影民用年月日；相等的带时区 datetime 可有不同民用日期。
  if isinstance(d, date):
    ret = CalendarDate(d.year, d.month, d.day, CalendarType.SOLAR)
  elif isinstance(d, CalendarDate):
    ret = d
  else:
    raise TypeError(f'Expected date or CalendarDate, got {type(d)}')

  if not _is_valid(ret):
    raise ValueError(f'"{ret}" is not a valid {ret.date_type.name} date in the supported range '
                     f'[{get_min_supported_date(ret.date_type)}, {get_max_supported_date(ret.date_type)}]')
  return ret


def to_solar(d: date | CalendarDate) -> CalendarDate:
  '''
  把输入转换为公历 CalendarDate。

  Args:
  - d: (date | CalendarDate) 输入日期；date 按公历解释，datetime 只取民用年月日。

  Return: (CalendarDate) SOLAR 类型日期。
  '''
  return _to_solar(_to_calendardate(d))


@functools.lru_cache(maxsize=512)
def _to_solar(calendardate: CalendarDate) -> CalendarDate:
  if calendardate.date_type == CalendarType.SOLAR:
    return calendardate
  elif calendardate.date_type == CalendarType.LUNAR:
    return _lunar_to_solar(calendardate)
  else:
    assert calendardate.date_type == CalendarType.GANZHI
    return _ganzhi_to_solar(calendardate)


def to_lunar(d: date | CalendarDate) -> CalendarDate:
  '''
  把输入转换为农历 CalendarDate。

  Args:
  - d: (date | CalendarDate) 输入日期；date 按公历解释，datetime 只取民用年月日。

  Return: (CalendarDate) LUNAR 类型日期，月号按年内实际月序编号，闰月占独立序号。
  '''
  return _to_lunar(_to_calendardate(d))


@functools.lru_cache(maxsize=512)
def _to_lunar(calendardate: CalendarDate) -> CalendarDate:
  if calendardate.date_type == CalendarType.LUNAR:
    return calendardate
  return _solar_to_lunar(_to_solar(calendardate))


def to_ganzhi(d: date | CalendarDate) -> CalendarDate:
  '''
  把输入转换为干支历 CalendarDate。

  Args:
  - d: (date | CalendarDate) 输入日期；date 按公历解释。

  Return: (CalendarDate) GANZHI 类型日期。

  Note: datetime 是 date 子类，此处接受但丢弃日内时刻，同日各时刻的结果相同。
  此入口只按日期归属；出生比较粒度由 BaziPrecision 决定。
  '''
  return _to_ganzhi(_to_calendardate(d))


@functools.lru_cache(maxsize=512)
def _to_ganzhi(calendardate: CalendarDate) -> CalendarDate:
  if calendardate.date_type == CalendarType.GANZHI:
    return calendardate
  return _solar_to_ganzhi(_to_solar(calendardate))


def to_date(d: date | CalendarDate) -> date:
  '''
  把输入转换为公历 date。

  Args:
  - d: (date | CalendarDate) 输入日期；datetime 为 date 子类，接受但丢弃日内时刻。

  Return: (date) 公历日期。
  '''
  solar = to_solar(d)
  return date(solar.year, solar.month, solar.day)

#endregion


#region 节气

@functools.lru_cache(maxsize=512)
def _jieqi_date(solar_year: int, jieqi: Jieqi) -> date:
  return jieqi_moment(solar_year, jieqi).date()


def jieqi_moment(solar_year: int, jieqi: Jieqi) -> datetime:
  '''
  输入公历年份和节气，返回节气的具体时刻。

  Args:
  - solar_year: (int) 公历年。
  - jieqi: (Jieqi) 节气。

  Note:
  - 时刻为东八区（北京时间），精度到秒（截断）。1929 年前同样按东八区表达，
    而非北京地方平时，见 issue #118。

  Return: (datetime) 指定公历年的节气时刻。
  '''
  if not isinstance(solar_year, int):
    raise TypeError(f'Expected int, got {type(solar_year)}')
  if not isinstance(jieqi, Jieqi):
    raise TypeError(f'Expected Jieqi, got {type(jieqi)}')
  if solar_year not in _jieqi_table().supported_year_range():
    raise ValueError(f'Year {solar_year} is out of the supported range {_jieqi_table().supported_year_range()}')
  return _jieqi_table().get(solar_year, jieqi)


@functools.cache
def supported_jie_boundaries() -> tuple[datetime, datetime]:
  '''
  返回首末支持节的时刻。prev_jie / next_jie 的输入须位于半开区间
  `[returned_tuple[0], returned_tuple[1])`，含首端、不含末端。
  '''
  years = _jieqi_table().supported_year_range()
  return (
    jieqi_moment(min(years), Jieqi.小寒), # 公历年首节。
    jieqi_moment(max(years), Jieqi.大雪), # 公历年末节。
  )


def _check_jie_range(dt: datetime) -> None:
  first, last = supported_jie_boundaries()
  if dt < first:
    raise ValueError(f'"{dt}" is out of the supported range. The first available Jie is "{first}"')
  if dt >= last:
    raise ValueError(f'"{dt}" is out of the supported range. The last available Jie is "{last}"')


def prev_jie(dt: datetime) -> JieqiTime:
  '''
  返回不晚于输入公历时刻的最近一节及其时刻，不含中气；恰交节归该节（比较为 >=）。

  Args:
  - dt: (datetime) 待查时刻。

  Return: (JieqiTime) 所属节及其公历时刻。
  '''
  if not isinstance(dt, datetime):
    raise TypeError(f'Expected datetime, got {type(dt)}')
  return _prev_jie(dt)


@functools.lru_cache(maxsize=512)
def _prev_jie(dt: datetime) -> JieqiTime:
  _check_jie_range(dt)
  # 逆序查本年节，取起点不晚于 dt 的最后一个区间。
  for jie in reversed(Jieqi.jies(ganzhi_year=False)):
    moment = jieqi_moment(dt.year, jie)
    if moment <= dt:
      return JieqiTime(jie, moment)

  # dt 在本年小寒前，前节为上年大雪。
  last_daxue = jieqi_moment(dt.year - 1, Jieqi.大雪)
  assert last_daxue <= dt
  return JieqiTime(Jieqi.大雪, last_daxue)


def next_jie(dt: datetime) -> JieqiTime:
  '''
  返回严格晚于输入公历时刻的最近一节及其时刻，不含中气；恰交节时继续查下一节（比较为 >）。

  Args:
  - dt: (datetime) 待查时刻。

  Return: (JieqiTime) 下一节及其公历时刻。
  '''
  if not isinstance(dt, datetime):
    raise TypeError(f'Expected datetime, got {type(dt)}')
  return _next_jie(dt)


@functools.lru_cache(maxsize=512)
def _next_jie(dt: datetime) -> JieqiTime:
  _check_jie_range(dt)
  for jie in Jieqi.jies(ganzhi_year=False):
    moment = jieqi_moment(dt.year, jie)
    if moment > dt:
      return JieqiTime(jie, moment)

  # dt 不早于本年大雪，下一节为次年小寒。
  next_xiaohan = jieqi_moment(dt.year + 1, Jieqi.小寒)
  assert dt < next_xiaohan
  return JieqiTime(Jieqi.小寒, next_xiaohan)

#endregion
