# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import date, datetime, timedelta
from typing import Final

from .defines import Ganzhi, Dizhi
from .bazi_chart import BaziChart
from .calendar import CalendarBackend, calendar_utils_of
from .calendar.utils_protocol import CalendarUtilsProtocol
from .school import BaziPrecision
from .utils.bazi_utils import (
  ganzhi_of_day, ganzhi_of_year, month_tiangan,
  _ganzhi_of_day_at_moment, _ganzhi_month_dizhi, _ganzhi_month_offset,
  _ganzhi_year_month_of_jie,
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
    *,
    dayun: Ganzhi | None,
    gz_month: Dizhi | None = None,
    liuri: Ganzhi | None = None,
  ) -> TransitSet:
    year_ganzhi: Final[Ganzhi] = ganzhi_of_year(gz_year)
    liuyue: Ganzhi | None = None
    if gz_month is not None:
      liuyue = Ganzhi(month_tiangan(year_ganzhi.tiangan, gz_month), gz_month)

    return TransitSet(
      xiaoyun=self._transit_db.xiaoyun(gz_year),
      dayun=dayun,
      liunian=year_ganzhi,
      liuyue=liuyue,
      liuri=liuri,
    )

  def at_year(self, gz_year: int) -> TransitSet | None:
    '''Return transits for a Ganzhi-year coordinate, or `None` before birth. Dayun
    lookup follows the chart's configured year-label view.
    返回干支年坐标下的流运，出生前返回 `None`；大运按命盘所选年份标签视图解释。'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    if gz_year < self._bazi_chart.bazi.ganzhi_year:
      return None
    return self._transits(
      gz_year,
      dayun=self._transit_db.dayun(gz_year),
    )

  def at_month(self, gz_year: int, gz_month: Dizhi) -> TransitSet | None:
    '''Return transits for a Ganzhi-month coordinate, or `None` before birth or outside
    the Jie table. Dayun follows its physical month boundary. 返回干支月坐标下的流运，
    出生前或节令表范围外返回 `None`；大运按物理交运月边界解释。'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    if not isinstance(gz_month, Dizhi):
      raise TypeError(f'Expected Dizhi, got {type(gz_month)}')

    bazi = self._bazi_chart.bazi
    query_key = (gz_year, _ganzhi_month_offset(gz_month))
    birth_key = (bazi.ganzhi_year, _ganzhi_month_offset(bazi.month_commander))

    first, last = self._utils.supported_jie_boundaries()
    first_year, first_month = _ganzhi_year_month_of_jie(self._utils.prev_jie(first))
    last_supported = last - timedelta(microseconds=1)
    last_year, last_month = _ganzhi_year_month_of_jie(
      self._utils.next_jie(last_supported)
    )
    supported_first_key = (first_year, first_month - 1)
    supported_last_key = (last_year, last_month - 1)
    if query_key < max(birth_key, supported_first_key) or query_key >= supported_last_key:
      return None
    return self._transits(
      gz_year,
      dayun=self._transit_db._dayun_at_month(gz_year, gz_month),
      gz_month=gz_month,
    )

  def at_date(self, solar_date: date) -> TransitSet | None:
    '''Return transits for a solar date, or `None` before birth or outside the calendar
    range. Dayun follows its physical date boundary. 返回公历日期下的流运，出生前或历法
    范围外返回 `None`；大运按物理交运日边界解释。'''
    if type(solar_date) is not date:
      raise TypeError(f'Expected date (not datetime), got {type(solar_date)}')
    if solar_date < self._bazi_chart.bazi.solar_date:
      return None
    try:
      ganzhi_date = self._utils.to_ganzhi(solar_date)
    except ValueError:
      return None
    month_dizhi = _ganzhi_month_dizhi(ganzhi_date.month)
    return self._transits(
      ganzhi_date.year,
      dayun=self._transit_db._dayun_at_date(solar_date),
      gz_month=month_dizhi,
      liuri=ganzhi_of_day(solar_date),
    )

  def at_moment(self, solar_moment: datetime) -> TransitSet | None:
    '''Return transits for a naïve solar moment, or `None` when exact-moment querying is
    unsupported, before birth, or outside the Jie table. Query, birth, and Dayun boundaries
    compare at whole-second granularity, with ties on the new side.
    返回无时区公历时刻下的流运；后端或命盘精度不支持、出生前、节令表范围外时返回 `None`。
    查询、出生与大运边界均截到秒比较，相等归新。

    Note:
    - Year/month coordinates follow the moment's owning Jie; Liuri follows the configured
      `DayRollover`. `at_date()` can therefore give a different reading on the same civil day.
    - HOUR natal attribution and this second-level reading are distinct granularities; inside
      a tie Shichen, the natal pillars and moment transits can legitimately name different years.
    - 年/月按时刻所属节归属，流日按所选换日点解释；同一公历日可与 `at_date()` 结果不同。
    - HOUR 原盘归属与秒级时刻流运是两种粒度；tie 时辰内可合法地落在不同干支年。'''
    if not isinstance(solar_moment, datetime):
      raise TypeError(f'Expected datetime, got {type(solar_moment)}')
    if solar_moment.tzinfo is not None:
      raise ValueError('Timezone should be well-processed outside of this class.')

    bazi = self._bazi_chart.bazi
    config = bazi.config
    if (
      config.backend not in (CalendarBackend.CELESTIAL, CalendarBackend.CELESTIAL_ALGO2)
      or config.precision not in (BaziPrecision.HOUR, BaziPrecision.MINUTE)
    ):
      return None

    moment = solar_moment.replace(microsecond=0)
    birth_moment = bazi.solar_datetime.replace(microsecond=0)
    first, last = self._utils.supported_jie_boundaries()
    if moment < birth_moment or not first <= moment < last:
      return None

    gz_year, gz_month = _ganzhi_year_month_of_jie(self._utils.prev_jie(moment))
    month_dizhi = _ganzhi_month_dizhi(gz_month)
    return self._transits(
      gz_year,
      dayun=self._transit_db._dayun_at_moment(moment),
      gz_month=month_dizhi,
      liuri=_ganzhi_of_day_at_moment(moment, config.school.day_rollover),
    )


流年大运 = TransitChart
