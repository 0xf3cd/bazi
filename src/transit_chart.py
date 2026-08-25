# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import date
from typing import Final

from .defines import Ganzhi, Dizhi
from .bazi_chart import BaziChart
from .calendar import calendar_utils_of
from .calendar.utils_protocol import CalendarUtilsProtocol
from .utils.bazi_utils import (
  ganzhi_of_day, ganzhi_of_year, month_tiangan,
  _ganzhi_month_dizhi, _ganzhi_month_offset,
)
from .transits import TransitDate, TransitMonth, TransitQuery, TransitSet, TransitYear, TransitDatabase


class TransitChart:
  '''
  The unified entry for querying chart-derived and calendar transits.
  查询命盘流运与历法流运的统一入口。

  Xiaoyun and Dayun come from `TransitDatabase`; Liunian, Liuyue, and Liuri are
  calendar-derived. 小运、大运来自 `TransitDatabase`；流年、流月、流日由历法推导。
  '''

  def __init__(self, bazi_chart: BaziChart) -> None:
    '''
    Takes a `BaziChart` as the input.
    接受一个 `BaziChart` 作为输入。

    Args:
    - `bazi_chart`: (BaziChart) The bazi chart (原盘) to generate the transit chart from.
    '''

    if not isinstance(bazi_chart, BaziChart):
      raise TypeError(f'Expected BaziChart, got {type(bazi_chart)}')
    self._bazi_chart: Final[BaziChart] = bazi_chart
    self._transit_db: Final[TransitDatabase] = TransitDatabase(self._bazi_chart)
    self._utils: Final[CalendarUtilsProtocol] = calendar_utils_of(self._bazi_chart.bazi.config.backend)

  @property
  def bazi_chart(self) -> BaziChart:
    '''The underlying `BaziChart` (原盘). Shared, not copied -- `BaziChart` is read-only
    (its non-frozen `Bazi` is isolated inside the chart). 直接共享——`BaziChart` 只读，
    非 frozen 的 `Bazi` 已由命盘自身隔离。'''
    return self._bazi_chart

  def _resolved(self, query: TransitQuery) -> tuple[int, Dizhi | None, date | None] | None:
    bazi = self._bazi_chart.bazi
    if isinstance(query, TransitYear):
      return (query.gz_year, None, None) if query.gz_year >= bazi.ganzhi_year else None

    if isinstance(query, TransitMonth):
      query_key = (query.gz_year, _ganzhi_month_offset(query.gz_month))
      birth_key = (bazi.ganzhi_year, _ganzhi_month_offset(bazi.month_commander))
      return (query.gz_year, query.gz_month, None) if query_key >= birth_key else None

    assert isinstance(query, TransitDate)
    if query.solar_date < bazi.solar_date:
      return None
    try:
      ganzhi_date = self._utils.to_ganzhi(query.solar_date)
    except ValueError:
      return None
    month_dizhi = _ganzhi_month_dizhi(ganzhi_date.month)
    return ganzhi_date.year, month_dizhi, query.solar_date

  @staticmethod
  def _check_query(query: object) -> None:
    if not isinstance(query, (TransitYear, TransitMonth, TransitDate)):
      raise TypeError(f'Expected TransitQuery, got {type(query)}')

  def support(self, query: TransitQuery) -> bool:
    '''
    Return whether the query is within this chart's life and calendar range.
    返回查询是否处于此命盘的人生时间线与历法支持范围内。
    '''
    self._check_query(query)
    return self._resolved(query) is not None

  def at(self, query: TransitQuery) -> TransitSet:
    '''
    Return all transits available at the requested precision. 返回查询精度下的全部可用流运。
    '''
    self._check_query(query)
    resolved = self._resolved(query)
    if resolved is None:
      raise ValueError(f'Query not supported: {query}')

    gz_year, gz_month, solar_date = resolved
    year_ganzhi: Final[Ganzhi] = ganzhi_of_year(gz_year)
    liuyue: Ganzhi | None = None
    if gz_month is not None:
      liuyue = Ganzhi(month_tiangan(year_ganzhi.tiangan, gz_month), gz_month)

    return TransitSet(
      xiaoyun=self._transit_db.xiaoyun(gz_year),
      dayun=self._transit_db.dayun(gz_year),
      liunian=year_ganzhi,
      liuyue=liuyue,
      liuri=ganzhi_of_day(solar_date) if solar_date is not None else None,
    )


流年大运 = TransitChart
