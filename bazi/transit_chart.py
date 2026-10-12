# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import date, datetime, timedelta
from typing import Final

from .defines import Ganzhi, Dizhi
from .bazi_chart import BaziChart
from .calendar import CalendarBackend, calendar_utils_of
from .calendar.utils_protocol import CalendarUtilsProtocol
from .calendar.dates import GanzhiYearMonth
from .school import BaziPrecision
from .utils.bazi_utils import (
  ganzhi_of_day, ganzhi_of_year, month_tiangan,
  _ganzhi_of_day_at_moment,
)
from .transits import TransitSet, TransitDatabase


class TransitChart:
  '''
  查询命盘流运与历法流运的统一入口。

  小运、大运来自 `TransitDatabase`；流年、流月、流日由历法推导。
  '''

  def __init__(self, bazi_chart: BaziChart) -> None:
    '''
    接受一个 `BaziChart` 作为输入。

    Args:
    - bazi_chart: (BaziChart) 查询所依据的原盘。
    '''

    if not isinstance(bazi_chart, BaziChart):
      raise TypeError(f'Expected BaziChart, got {type(bazi_chart)}')
    self._bazi_chart: Final[BaziChart] = bazi_chart
    self._transit_db: Final[TransitDatabase] = TransitDatabase(self._bazi_chart)
    self._utils: Final[CalendarUtilsProtocol] = calendar_utils_of(self._bazi_chart.bazi.config.backend)

  @property
  def bazi_chart(self) -> BaziChart:
    '''直接共享的只读原盘；命盘自身已隔离非 frozen 的 Bazi，无需再复制。'''
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
    '''返回干支年坐标下的流运，出生前返回 `None`；大运按命盘所选年份标签视图解释。'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    if gz_year < self._bazi_chart.bazi.ganzhi_year:
      return None
    return self._transits(
      gz_year,
      dayun=self._transit_db.dayun(gz_year),
    )

  def at_month(self, gz_year: int, gz_month: Dizhi) -> TransitSet | None:
    '''返回干支月坐标下的流运，
    出生前或节令表范围外返回 `None`；大运按物理交运月边界解释。'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    if not isinstance(gz_month, Dizhi):
      raise TypeError(f'Expected Dizhi, got {type(gz_month)}')

    query_key = GanzhiYearMonth.from_dizhi(gz_year, gz_month)

    first, last = self._utils.supported_jie_boundaries()
    supported_first_key = GanzhiYearMonth.from_jie(self._utils.prev_jie(first))
    last_supported = last - timedelta(microseconds=1)
    supported_last_key = GanzhiYearMonth.from_jie(
      self._utils.next_jie(last_supported)
    )
    if query_key < max(self._bazi_chart.bazi.ganzhi_year_month, supported_first_key) or query_key >= supported_last_key:
      return None
    return self._transits(
      gz_year,
      dayun=self._transit_db._dayun_at_month(gz_year, gz_month),
      gz_month=gz_month,
    )

  def at_date(self, solar_date: date) -> TransitSet | None:
    '''返回东八区无时区公历日期下的流运，出生前或历法范围外返回 `None`；地点盘出生
    下界取规范绝对日期，不取真太阳时日期；大运按物理交运日边界解释。'''
    if type(solar_date) is not date:
      raise TypeError(f'Expected date (not datetime), got {type(solar_date)}')
    if solar_date < self._bazi_chart.bazi.reference_datetime.date():
      return None
    try:
      ganzhi_date = self._utils.to_ganzhi(solar_date)
    except ValueError:
      return None
    year_month = GanzhiYearMonth(ganzhi_date.year, ganzhi_date.month)
    return self._transits(
      ganzhi_date.year,
      dayun=self._transit_db._dayun_at_date(solar_date),
      gz_month=year_month.dizhi,
      liuri=ganzhi_of_day(solar_date),
    )

  def at_moment(self, solar_moment: datetime) -> TransitSet | None:
    '''返回东八区无时区公历标签下的流运；后端或命盘精度不支持、出生前、节令表范围外时返回 `None`。
    地点盘出生下界取规范绝对时刻；查询时刻不做地点修正。
    查询、出生与大运边界均截到秒比较，相等归新。

    Note:
    - 年/月按时刻所属节归属，流日按所选换日点解释；同一公历日可与 `at_date()` 结果不同。
    - HOUR 原盘归属与秒级时刻流运是两种粒度；相等时辰窗口内可落在不同干支年。'''
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
    birth_moment = bazi.reference_datetime.replace(microsecond=0)
    first, last = self._utils.supported_jie_boundaries()
    if moment < birth_moment or not first <= moment < last:
      return None

    year_month = GanzhiYearMonth.from_jie(self._utils.prev_jie(moment))
    return self._transits(
      year_month.year,
      dayun=self._transit_db._dayun_at_moment(moment),
      gz_month=year_month.dizhi,
      liuri=_ganzhi_of_day_at_moment(moment, config.school.day_rollover),
    )


流年大运 = TransitChart
