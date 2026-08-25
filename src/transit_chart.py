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
from .transits import TransitSet, TransitDatabase


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

  def _transits(
    self,
    gz_year: int,
    gz_month: Dizhi | None = None,
    solar_date: date | None = None,
  ) -> TransitSet:
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

  def at_year(self, gz_year: int) -> TransitSet | None:
    '''Return transits for a Ganzhi-year coordinate, or `None` before birth. Dayun
    lookup follows the chart's configured year-label view.
    返回干支年坐标下的流运，出生前返回 `None`；大运按命盘所选年份标签视图解释。'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    if gz_year < self._bazi_chart.bazi.ganzhi_year:
      return None
    return self._transits(gz_year)

  def at_month(self, gz_year: int, gz_month: Dizhi) -> TransitSet | None:
    '''Return transits for a Ganzhi-month coordinate, or `None` before birth.
    返回干支月坐标下的流运，出生前返回 `None`。'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    if not isinstance(gz_month, Dizhi):
      raise TypeError(f'Expected Dizhi, got {type(gz_month)}')

    bazi = self._bazi_chart.bazi
    query_key = (gz_year, _ganzhi_month_offset(gz_month))
    birth_key = (bazi.ganzhi_year, _ganzhi_month_offset(bazi.month_commander))
    if query_key < birth_key:
      return None
    return self._transits(gz_year, gz_month)

  def at_date(self, solar_date: date) -> TransitSet | None:
    '''Return transits for a solar date, or `None` before birth or outside the calendar
    range. 返回公历日期下的流运，出生前或历法范围外返回 `None`。'''
    if type(solar_date) is not date:
      raise TypeError(f'Expected date (not datetime), got {type(solar_date)}')
    if solar_date < self._bazi_chart.bazi.solar_date:
      return None
    try:
      ganzhi_date = self._utils.to_ganzhi(solar_date)
    except ValueError:
      return None
    month_dizhi = _ganzhi_month_dizhi(ganzhi_date.month)
    return self._transits(ganzhi_date.year, month_dizhi, solar_date)


流年大运 = TransitChart
