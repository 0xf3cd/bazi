# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''
读取预生成 celestial-calendar 表的历法工具，数据契约见 `celestial_data/SCHEMA.md`。
满足 `CalendarUtilsProtocol`，不依赖 HKO 工具；两后端独立实现，一致性由测试核对。

`jieqi_moment` 提供秒级真实时刻，HKO 则用午夜占位。CalendarDate 仍只表示日期：
干支历正月初一为立春日。时刻的四柱归属由调用方决定，Bazi 按所选出生精度比较。

两种阴历算法各有一个模块级单例，缓存不能混用。若用可变模块开关配合 lru_cache，
切换后可能返回旧算法的缓存结果；独立实例把算法选择纳入工具对象身份。
'''

import functools

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Final

from .dates import CalendarType, CalendarDate, JieqiTime
from .celestial_data.loader import (
  DATA_DIR, JieqiMomentTable, LunarYearTable, LunarYearInfo,
)

from ..defines import Jieqi


_JIEQI_TABLE: Final[JieqiMomentTable] = JieqiMomentTable()
'''各算法共用节气表，只有农历表不同。'''


class CelestialCalendarUtils:
  '''
  读取 celestial-calendar 表的历法工具；使用模块级单例 `ALGO1` / `ALGO2`，不直接构造。
  '''

  def __init__(self, lunar_table_path: Path) -> None:
    self._jieqi_table: Final[JieqiMomentTable] = _JIEQI_TABLE
    self._lunar_table: Final[LunarYearTable] = LunarYearTable(lunar_table_path)

  # -- 支持范围 ---------------------------------------------------------------------
  #
  # 范围从表推导；三种日期表示同一物理窗口，以公历两端为基准，另四端由转换得到。
  # 与 HKO 常量的相等关系由差异测试验证。

  def get_min_supported_date(self, date_type: CalendarType) -> CalendarDate:
    if not isinstance(date_type, CalendarType):
      raise TypeError(f'Expected CalendarType, got {type(date_type)}')
    return self.__get_min_supported_date(date_type)

  @functools.lru_cache(maxsize=512)
  def __get_min_supported_date(self, date_type: CalendarType) -> CalendarDate:
    if date_type == CalendarType.SOLAR:
      # solar_to_lunar 先按公历年查农历年，支持的公历日期须有对应农历记录，因此以农历表为基准。
      first: date = self._lunar_table.get(min(self._lunar_table.supported_year_range()))['first_solar_day']
      return CalendarDate(first.year, first.month, first.day, CalendarType.SOLAR)
    elif date_type == CalendarType.LUNAR:
      return self.solar_to_lunar(self.get_min_supported_date(CalendarType.SOLAR))
    elif date_type == CalendarType.GANZHI:
      return self.solar_to_ganzhi(self.get_min_supported_date(CalendarType.SOLAR))
    else:
      raise ValueError(f'Unsupported date_type: {date_type}') # pragma: no cover # 上方已处理全部 CalendarType 成员。

  def get_max_supported_date(self, date_type: CalendarType) -> CalendarDate:
    if not isinstance(date_type, CalendarType):
      raise TypeError(f'Expected CalendarType, got {type(date_type)}')
    return self.__get_max_supported_date(date_type)

  @functools.lru_cache(maxsize=512)
  def __get_max_supported_date(self, date_type: CalendarType) -> CalendarDate:
    if date_type == CalendarType.SOLAR:
      # solar_to_lunar 先按公历年查表，即使末农历年延伸到下一公历年，也不能支持下一公历年。
      last_year: int = max(self._lunar_table.supported_year_range())
      return CalendarDate(last_year, 12, 31, CalendarType.SOLAR)
    elif date_type == CalendarType.LUNAR:
      return self.solar_to_lunar(self.get_max_supported_date(CalendarType.SOLAR))
    elif date_type == CalendarType.GANZHI:
      return self.solar_to_ganzhi(self.get_max_supported_date(CalendarType.SOLAR))
    else:
      raise ValueError(f'Unsupported date_type: {date_type}') # pragma: no cover # 上方已处理全部 CalendarType 成员。

  # -- 日期有效性 -------------------------------------------------------------------

  def is_valid_solar_date(self, d: CalendarDate) -> bool:
    '''
    检查公历日期是否合法且在支持范围内。

    Args:
    - d: (CalendarDate) 待查公历日期，类型应为 `CalendarType.SOLAR`。

    Return: (bool) 合法且受支持时为 True，否则为 False。
    '''

    if not isinstance(d, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(d)}')
    return self.__is_valid_solar_date(d)

  @functools.lru_cache(maxsize=512)
  def __is_valid_solar_date(self, d: CalendarDate) -> bool:
    if d.date_type != CalendarType.SOLAR:
      return False
    if d < self.get_min_supported_date(CalendarType.SOLAR):
      return False
    if d > self.get_max_supported_date(CalendarType.SOLAR):
      return False

    try:
      # 公历月长与闰年由标准库检查。
      date(d.year, d.month, d.day)
    except ValueError:
      return False
    return True

  def is_valid_lunar_date(self, d: CalendarDate) -> bool:
    '''
    检查农历日期是否合法且在支持范围内。

    Args:
    - d: (CalendarDate) 待查农历日期，类型应为 `CalendarType.LUNAR`。

    Return: (bool) 合法且受支持时为 True，否则为 False。
    '''

    if not isinstance(d, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(d)}')
    return self.__is_valid_lunar_date(d)

  @functools.lru_cache(maxsize=512)
  def __is_valid_lunar_date(self, d: CalendarDate) -> bool:
    if d.date_type != CalendarType.LUNAR:
      return False
    if d < self.get_min_supported_date(CalendarType.LUNAR):
      return False
    if d > self.get_max_supported_date(CalendarType.LUNAR):
      return False

    days_counts: list[int] = self._lunar_table.get(d.year)['days_counts']
    if d.month < 1 or d.month > len(days_counts):
      return False
    return 1 <= d.day <= days_counts[d.month - 1]

  def is_valid_ganzhi_date(self, d: CalendarDate) -> bool:
    '''
    检查干支历日期是否合法且在支持范围内。

    Args:
    - d: (CalendarDate) 待查干支历日期，类型应为 `CalendarType.GANZHI`。

    Return: (bool) 合法且受支持时为 True，否则为 False。
    '''

    if not isinstance(d, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(d)}')
    return self.__is_valid_ganzhi_date(d)

  @functools.lru_cache(maxsize=512)
  def __is_valid_ganzhi_date(self, d: CalendarDate) -> bool:
    if d.date_type != CalendarType.GANZHI:
      return False
    if d < self.get_min_supported_date(CalendarType.GANZHI):
      return False
    if d > self.get_max_supported_date(CalendarType.GANZHI):
      return False

    if d.month < 1 or d.month > 12:
      return False

    days_counts: list[int] = self.days_counts_in_ganzhi_year(d.year)
    return 1 <= d.day <= days_counts[d.month - 1]

  def is_valid(self, d: CalendarDate) -> bool:
    if not isinstance(d, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(d)}')
    return self.__is_valid(d)

  @functools.lru_cache(maxsize=512)
  def __is_valid(self, d: CalendarDate) -> bool:
    if d.date_type == CalendarType.SOLAR:
      return self.is_valid_solar_date(d)
    elif d.date_type == CalendarType.LUNAR:
      return self.is_valid_lunar_date(d)
    else:
      assert d.date_type == CalendarType.GANZHI
      return self.is_valid_ganzhi_date(d)

  # -- 干支月长 ---------------------------------------------------------------------

  def days_counts_in_ganzhi_year(self, ganzhi_year: int) -> list[int]:
    '''
    返回 `ganzhi_year` 的十二个干支月长，按连续节日期之差计算，见模块的日期级约定。
    '''
    if not isinstance(ganzhi_year, int):
      raise TypeError(f'Expected int, got {type(ganzhi_year)}')
    # 缓存持有元组，每次返回独立列表，避免调用方修改后影响后续结果。
    return list(self.__days_counts_in_ganzhi_year(ganzhi_year))

  @functools.lru_cache(maxsize=512)
  def __days_counts_in_ganzhi_year(self, ganzhi_year: int) -> tuple[int, ...]:
    # 末干支月须以下一公历年立春作为终点。
    if ganzhi_year not in self._jieqi_table.supported_year_range():
      raise ValueError(f'Ganzhi year {ganzhi_year} is out of the supported range {self._jieqi_table.supported_year_range()}')
    if ganzhi_year + 1 not in self._jieqi_table.supported_year_range():
      raise ValueError(f'Ganzhi year {ganzhi_year} needs jieqi data of year {ganzhi_year + 1}, '
                       f'which is out of the supported range {self._jieqi_table.supported_year_range()}')

    jies = Jieqi.jies()

    # 前十一节在 ganzhi_year 公历年，末节小寒在下一公历年。
    start_dates: list[date] = [self.jieqi_date(ganzhi_year, jq) for jq in jies[:11]]
    start_dates += [self.jieqi_date(ganzhi_year + 1, jq) for jq in jies[11:]]
    end_dates: list[date] = start_dates[1:] + [self.jieqi_date(ganzhi_year + 1, Jieqi.立春)]

    days_counts: tuple[int, ...] = tuple((end - start).days
                                         for start, end in zip(start_dates, end_dates))
    assert len(days_counts) == 12
    return days_counts

  # -- 历法换算 ---------------------------------------------------------------------

  def lunar_to_solar(self, lunar_date: CalendarDate) -> CalendarDate:
    if not isinstance(lunar_date, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(lunar_date)}')
    return self.__lunar_to_solar(lunar_date)

  @functools.lru_cache(maxsize=512)
  def __lunar_to_solar(self, lunar_date: CalendarDate) -> CalendarDate:
    if lunar_date.date_type != CalendarType.LUNAR:
      raise ValueError(f'Expected a LUNAR date, got {lunar_date}')
    if not self.is_valid(lunar_date):
      raise ValueError(f'"{lunar_date}" is not a valid {lunar_date.date_type.name} date in the supported range '
                       f'[{self.get_min_supported_date(lunar_date.date_type)}, {self.get_max_supported_date(lunar_date.date_type)}]')

    info: LunarYearInfo = self._lunar_table.get(lunar_date.year)
    passed_days: int = sum(info['days_counts'][:lunar_date.month - 1]) + lunar_date.day - 1
    solar: date = info['first_solar_day'] + timedelta(days=passed_days)
    return CalendarDate(solar.year, solar.month, solar.day, CalendarType.SOLAR)

  def solar_to_lunar(self, solar_date: CalendarDate) -> CalendarDate:
    if not isinstance(solar_date, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(solar_date)}')
    return self.__solar_to_lunar(solar_date)

  @functools.lru_cache(maxsize=512)
  def __solar_to_lunar(self, solar_date: CalendarDate) -> CalendarDate:
    if solar_date.date_type != CalendarType.SOLAR:
      raise ValueError(f'Expected a SOLAR date, got {solar_date}')
    if not self.is_valid(solar_date):
      raise ValueError(f'"{solar_date}" is not a valid {solar_date.date_type.name} date in the supported range '
                       f'[{self.get_min_supported_date(solar_date.date_type)}, {self.get_max_supported_date(solar_date.date_type)}]')
    solar: date = date(solar_date.year, solar_date.month, solar_date.day)

    # 公历年初日期可仍属于上一农历年。
    lunar_year: int = solar_date.year
    info: LunarYearInfo = self._lunar_table.get(lunar_year)
    if info['first_solar_day'] > solar:
      lunar_year -= 1
      info = self._lunar_table.get(lunar_year)

    month_idx, day_idx = self.__walk_months((solar - info['first_solar_day']).days, info['days_counts'])
    return CalendarDate(lunar_year, month_idx + 1, day_idx + 1, CalendarType.LUNAR)

  def ganzhi_to_solar(self, ganzhi_date: CalendarDate) -> CalendarDate:
    if not isinstance(ganzhi_date, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(ganzhi_date)}')
    return self.__ganzhi_to_solar(ganzhi_date)

  @functools.lru_cache(maxsize=512)
  def __ganzhi_to_solar(self, ganzhi_date: CalendarDate) -> CalendarDate:
    if ganzhi_date.date_type != CalendarType.GANZHI:
      raise ValueError(f'Expected a GANZHI date, got {ganzhi_date}')
    if not self.is_valid(ganzhi_date):
      raise ValueError(f'"{ganzhi_date}" is not a valid {ganzhi_date.date_type.name} date in the supported range '
                       f'[{self.get_min_supported_date(ganzhi_date.date_type)}, {self.get_max_supported_date(ganzhi_date.date_type)}]')

    days_counts: list[int] = self.days_counts_in_ganzhi_year(ganzhi_date.year)
    passed_days: int = sum(days_counts[:ganzhi_date.month - 1]) + ganzhi_date.day - 1
    solar: date = self.jieqi_date(ganzhi_date.year, Jieqi.立春) + timedelta(days=passed_days)
    return CalendarDate(solar.year, solar.month, solar.day, CalendarType.SOLAR)

  def solar_to_ganzhi(self, solar_date: CalendarDate) -> CalendarDate:
    if not isinstance(solar_date, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(solar_date)}')
    return self.__solar_to_ganzhi(solar_date)

  @functools.lru_cache(maxsize=512)
  def __solar_to_ganzhi(self, solar_date: CalendarDate) -> CalendarDate:
    if solar_date.date_type != CalendarType.SOLAR:
      raise ValueError(f'Expected a SOLAR date, got {solar_date}')
    if not self.is_valid(solar_date):
      raise ValueError(f'"{solar_date}" is not a valid {solar_date.date_type.name} date in the supported range '
                       f'[{self.get_min_supported_date(solar_date.date_type)}, {self.get_max_supported_date(solar_date.date_type)}]')
    solar: date = date(solar_date.year, solar_date.month, solar_date.day)

    # 立春前的公历日期仍属于上一干支年。
    ganzhi_year: int = solar_date.year
    if self.jieqi_date(ganzhi_year, Jieqi.立春) > solar:
      ganzhi_year -= 1

    passed_days: int = (solar - self.jieqi_date(ganzhi_year, Jieqi.立春)).days
    month_idx, day_idx = self.__walk_months(passed_days, self.days_counts_in_ganzhi_year(ganzhi_year))
    return CalendarDate(ganzhi_year, month_idx + 1, day_idx + 1, CalendarType.GANZHI)

  def lunar_to_ganzhi(self, lunar_date: CalendarDate) -> CalendarDate:
    if not isinstance(lunar_date, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(lunar_date)}')
    return self.__lunar_to_ganzhi(lunar_date)

  @functools.lru_cache(maxsize=512)
  def __lunar_to_ganzhi(self, lunar_date: CalendarDate) -> CalendarDate:
    if lunar_date.date_type != CalendarType.LUNAR:
      raise ValueError(f'Expected a LUNAR date, got {lunar_date}')
    if not self.is_valid(lunar_date):
      raise ValueError(f'"{lunar_date}" is not a valid {lunar_date.date_type.name} date in the supported range '
                       f'[{self.get_min_supported_date(lunar_date.date_type)}, {self.get_max_supported_date(lunar_date.date_type)}]')
    return self.solar_to_ganzhi(self.lunar_to_solar(lunar_date))

  def ganzhi_to_lunar(self, ganzhi_date: CalendarDate) -> CalendarDate:
    if not isinstance(ganzhi_date, CalendarDate):
      raise TypeError(f'Expected CalendarDate, got {type(ganzhi_date)}')
    return self.__ganzhi_to_lunar(ganzhi_date)

  @functools.lru_cache(maxsize=512)
  def __ganzhi_to_lunar(self, ganzhi_date: CalendarDate) -> CalendarDate:
    if ganzhi_date.date_type != CalendarType.GANZHI:
      raise ValueError(f'Expected a GANZHI date, got {ganzhi_date}')
    if not self.is_valid(ganzhi_date):
      raise ValueError(f'"{ganzhi_date}" is not a valid {ganzhi_date.date_type.name} date in the supported range '
                       f'[{self.get_min_supported_date(ganzhi_date.date_type)}, {self.get_max_supported_date(ganzhi_date.date_type)}]')
    return self.solar_to_lunar(self.ganzhi_to_solar(ganzhi_date))

  @staticmethod
  def __walk_months(passed_days: int, days_counts: list[int]) -> tuple[int, int]:
    '''把距年初的日偏移拆为月序号与日序号。'''
    month_idx: int = 0
    while passed_days >= days_counts[month_idx]:
      passed_days -= days_counts[month_idx]
      month_idx += 1
    return month_idx, passed_days

  # -- to_* 日期入口 ----------------------------------------------------------------

  def __to_calendardate(self, d: date | CalendarDate) -> CalendarDate:
    # 缓存前先投影民用年月日；相等的带时区 datetime 可有不同民用日期。
    if isinstance(d, date):
      ret = CalendarDate(d.year, d.month, d.day, CalendarType.SOLAR)
    elif isinstance(d, CalendarDate):
      ret = d
    else:
      raise TypeError(f'Expected date or CalendarDate, got {type(d)}')

    if not self.is_valid(ret):
      raise ValueError(f'"{ret}" is not a valid {ret.date_type.name} date in the supported range '
                       f'[{self.get_min_supported_date(ret.date_type)}, {self.get_max_supported_date(ret.date_type)}]')
    return ret

  def to_solar(self, d: date | CalendarDate) -> CalendarDate:
    '''
    把输入转换为公历 CalendarDate。

    Args:
    - d: (date | CalendarDate) 输入日期；date 按公历解释。

    Return: (CalendarDate) SOLAR 类型日期。
    '''

    return self.__to_solar(
      self.__to_calendardate(d),
    )

  @functools.lru_cache(maxsize=512)
  def __to_solar(self, calendardate: CalendarDate) -> CalendarDate:
    if calendardate.date_type == CalendarType.SOLAR:
      return calendardate
    elif calendardate.date_type == CalendarType.LUNAR:
      return self.lunar_to_solar(calendardate)
    else:
      assert calendardate.date_type == CalendarType.GANZHI
      return self.ganzhi_to_solar(calendardate)

  def to_lunar(self, d: date | CalendarDate) -> CalendarDate:
    '''
    把输入转换为农历 CalendarDate。

    Args:
    - d: (date | CalendarDate) 输入日期；date 按公历解释。

    Return: (CalendarDate) LUNAR 类型日期。
    '''

    return self.__to_lunar(
      self.__to_calendardate(d),
    )

  @functools.lru_cache(maxsize=512)
  def __to_lunar(self, calendardate: CalendarDate) -> CalendarDate:
    if calendardate.date_type == CalendarType.LUNAR:
      return calendardate
    elif calendardate.date_type == CalendarType.SOLAR:
      return self.solar_to_lunar(calendardate)
    else:
      assert calendardate.date_type == CalendarType.GANZHI
      return self.ganzhi_to_lunar(calendardate)

  def to_ganzhi(self, d: date | CalendarDate) -> CalendarDate:
    '''
    把输入转换为干支历 CalendarDate。

    Args:
    - d: (date | CalendarDate) 输入日期；date 按公历解释。

    Return: (CalendarDate) GANZHI 类型日期。

    Note: datetime 是 date 子类，此处接受但丢弃日内时刻，同日各时刻的结果相同。
    本后端虽有秒级节时刻，此入口仍只按日期归属；出生比较粒度由 BaziPrecision 决定。
    '''

    return self.__to_ganzhi(
      self.__to_calendardate(d),
    )

  @functools.lru_cache(maxsize=512)
  def __to_ganzhi(self, calendardate: CalendarDate) -> CalendarDate:
    if calendardate.date_type == CalendarType.GANZHI:
      return calendardate
    elif calendardate.date_type == CalendarType.SOLAR:
      return self.solar_to_ganzhi(calendardate)
    else:
      assert calendardate.date_type == CalendarType.LUNAR
      return self.lunar_to_ganzhi(calendardate)

  def to_date(self, d: date | CalendarDate) -> date:
    '''
    把输入转换为公历 date。

    Args:
    - d: (date | CalendarDate) 输入日期；datetime 为 date 子类，接受但丢弃日内时刻。

    Return: (date) 公历日期。
    '''

    return self.__to_date(
      self.__to_calendardate(d),
    )

  @functools.lru_cache(maxsize=512)
  def __to_date(self, calendardate: CalendarDate) -> date:
    solar: CalendarDate = self.to_solar(calendardate)
    return date(solar.year, solar.month, solar.day)

  # -- 节气 -------------------------------------------------------------------------

  @functools.lru_cache(maxsize=512)
  def __jieqi_date(self, solar_year: int, jieqi: Jieqi) -> date:
    return self.jieqi_moment(solar_year, jieqi).date()

  def jieqi_date(self, solar_year: int, jieqi: Jieqi) -> date:
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
    if solar_year not in self._jieqi_table.supported_year_range():
      raise ValueError(f'Year {solar_year} is out of the supported range {self._jieqi_table.supported_year_range()}')
    return self.__jieqi_date(solar_year, jieqi)

  @functools.lru_cache(maxsize=512)
  def __jieqi_moment(self, solar_year: int, jieqi: Jieqi) -> datetime:
    return self._jieqi_table.get(solar_year, jieqi)

  def jieqi_moment(self, solar_year: int, jieqi: Jieqi) -> datetime:
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
    if solar_year not in self._jieqi_table.supported_year_range():
      raise ValueError(f'Year {solar_year} is out of the supported range {self._jieqi_table.supported_year_range()}')
    return self.__jieqi_moment(solar_year, jieqi)

    # 类级缓存有 ALGO1 与 ALGO2 两个实例键；maxsize=2 避免两个单例逐次互相逐出。
  @functools.lru_cache(maxsize=2)
  def supported_jie_boundaries(self) -> tuple[datetime, datetime]:
    '''
    返回首末支持节的时刻。prev_jie / next_jie 的输入须位于半开区间
    `[returned_tuple[0], returned_tuple[1])`，含首端、不含末端。
    '''
    years: range = self._jieqi_table.supported_year_range()
    return (
      self.jieqi_moment(min(years), Jieqi.小寒), # 公历年首节。
      self.jieqi_moment(max(years), Jieqi.大雪), # 公历年末节。
    )

  def __check_jie_range(self, dt: datetime) -> None:
    first, last = self.supported_jie_boundaries()
    if dt < first:
      raise ValueError(f'"{dt}" is out of the supported range. The first available Jie is "{first}"')
    if dt >= last:
      raise ValueError(f'"{dt}" is out of the supported range. The last available Jie is "{last}"')

  def prev_jie(self, dt: datetime) -> JieqiTime:
    '''
    返回不晚于输入公历时刻的最近一节及其时刻，不含中气；恰交节归该节（比较为 >=）。

    Args:
    - dt: (datetime) 待查时刻。

    Return: (JieqiTime) 所属节及其公历时刻。
    '''

    if not isinstance(dt, datetime):
      raise TypeError(f'Expected datetime, got {type(dt)}')
    return self.__prev_jie(dt)

  @functools.lru_cache(maxsize=512)
  def __prev_jie(self, dt: datetime) -> JieqiTime:
    self.__check_jie_range(dt)

    # 逆序查本年节，取起点不晚于 dt 的最后一个区间。
    for jie in reversed(Jieqi.jies(ganzhi_year=False)):
      moment: datetime = self.jieqi_moment(dt.year, jie)
      if moment <= dt:
        return JieqiTime(jie, moment)

    # dt 在本年小寒前，前节为上年大雪。
    last_daxue: datetime = self.jieqi_moment(dt.year - 1, Jieqi.大雪)
    assert last_daxue <= dt
    return JieqiTime(Jieqi.大雪, last_daxue)

  def next_jie(self, dt: datetime) -> JieqiTime:
    '''
    返回严格晚于输入公历时刻的最近一节及其时刻，不含中气；恰交节时继续查下一节（比较为 >）。

    Args:
    - dt: (datetime) 待查时刻。

    Return: (JieqiTime) 下一节及其公历时刻。
    '''

    if not isinstance(dt, datetime):
      raise TypeError(f'Expected datetime, got {type(dt)}')
    return self.__next_jie(dt)

  @functools.lru_cache(maxsize=512)
  def __next_jie(self, dt: datetime) -> JieqiTime:
    self.__check_jie_range(dt)

    for jie in Jieqi.jies(ganzhi_year=False):
      moment: datetime = self.jieqi_moment(dt.year, jie)
      if moment > dt:
        return JieqiTime(jie, moment)

    # dt 不早于本年大雪，下一节为次年小寒。
    next_xiaohan: datetime = self.jieqi_moment(dt.year + 1, Jieqi.小寒)
    assert dt < next_xiaohan
    return JieqiTime(Jieqi.小寒, next_xiaohan)


ALGO1: Final[CelestialCalendarUtils] = CelestialCalendarUtils(DATA_DIR / 'lunar_years_algo1.txt')
'''默认阴历算法，沿 HKO 官方历书体系。'''

ALGO2: Final[CelestialCalendarUtils] = CelestialCalendarUtils(DATA_DIR / 'lunar_years_algo2.txt')
'''可选阴历算法，按考虑闰秒的 UTC+8 划月；有六年不同于 ALGO1，见 SCHEMA.md。'''
