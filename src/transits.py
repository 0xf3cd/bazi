# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, unique
from typing import Final

from .common import frozendict
from .data_types import DayunTuple
from .defines import Ganzhi, Dizhi
from .bazi_chart import BaziChart
from .calendar import CalendarUtilsProtocol, calendar_utils_of
from .utils.bazi_utils import _ganzhi_month_offset, _ganzhi_year_month_of_jie


'''An orderable projection of a physical Dayun boundary.'''
_DayunKey = tuple[int, ...]


class DayunDatabase:
  '''Locates the Dayun (大运) whose configured start-year label range contains a year.
  Adjacent labels delimit each range; the final range is always ten label years and can
  therefore differ from the physical `end_moment`.
  按所选规则的起运年份标签区间定位大运；相邻标签划分区间，末区间固定为十个标签年，因此可与
  物理 `end_moment` 不一致。'''
  def __init__(self, chart: BaziChart) -> None:
    self._dayuns: Final[tuple[DayunTuple, ...]] = tuple(chart.dayun)
    self._empty_timeline_error: Final[str] = chart._dayun_empty_timeline_message

  def __getitem__(self, gz_year: int) -> DayunTuple:
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    if len(self._dayuns) == 0:
      raise ValueError(self._empty_timeline_error)
    if gz_year < self._dayuns[0].ganzhi_year:
      raise ValueError(f'Year {gz_year} is before the first Dayun year {self._dayuns[0].ganzhi_year}')

    end_ganzhi_year: Final[int] = self._dayuns[-1].ganzhi_year + 10
    if gz_year >= end_ganzhi_year:
      raise ValueError(f'Year {gz_year} is on or after the end of the Dayun label range {end_ganzhi_year}')

    for dayun in reversed(self._dayuns):
      if gz_year >= dayun.ganzhi_year:
        return dayun
    raise AssertionError('Unreachable Dayun lookup state') # pragma: no cover # Lower bound checked above.


@unique
class TransitKind(Enum):
  '''A named kind of transit. 流运种类。'''
  XIAOYUN = 'xiaoyun'
  DAYUN   = 'dayun'
  LIUNIAN = 'liunian'
  LIUYUE  = 'liuyue'
  LIURI   = 'liuri'


@dataclass(frozen=True)
class TransitSet:
  '''An immutable, canonically ordered set of named transit Ganzhis. 一组不可变且顺序固定的具名流运干支。'''
  xiaoyun: Ganzhi | None = None
  dayun:   Ganzhi | None = None
  liunian: Ganzhi | None = None
  liuyue:  Ganzhi | None = None
  liuri:   Ganzhi | None = None

  def __post_init__(self) -> None:
    values = (self.xiaoyun, self.dayun, self.liunian, self.liuyue, self.liuri)
    if not any(gz is not None for gz in values):
      raise ValueError('A TransitSet cannot be empty')
    for gz in values:
      if gz is not None and not isinstance(gz, Ganzhi):
        raise TypeError(f'Expected Ganzhi, got {type(gz)}')

  @property
  def items(self) -> tuple[tuple[TransitKind, Ganzhi], ...]:
    '''The present transits in canonical order. 按固定顺序返回现有流运。'''
    pairs = (
      (TransitKind.XIAOYUN, self.xiaoyun),
      (TransitKind.DAYUN,   self.dayun),
      (TransitKind.LIUNIAN, self.liunian),
      (TransitKind.LIUYUE,  self.liuyue),
      (TransitKind.LIURI,   self.liuri),
    )
    return tuple((kind, gz) for kind, gz in pairs if gz is not None)

  def __iter__(self) -> Iterator[TransitKind]:
    return (kind for kind, _ in self.items)

  def __contains__(self, kind: object) -> bool:
    return any(current is kind for current, _ in self.items)

  @property
  def ganzhis(self) -> tuple[Ganzhi, ...]:
    '''The present Ganzhis in canonical transit order. 按固定流运顺序返回现有干支。'''
    return tuple(gz for _, gz in self.items)

  @property
  def json(self) -> dict[str, str]:
    '''A JSON-safe named representation. JSON 可序列化的具名表示。'''
    return {kind.value: str(gz) for kind, gz in self.items}

  def select(self, *kinds: TransitKind) -> 'TransitSet':
    '''Return requested kinds in canonical order; every requested kind must be present.
    按固定顺序返回指定的流运；指定的种类必须全部存在。'''
    if len(kinds) == 0:
      raise ValueError('Expected at least one TransitKind')
    for kind in kinds:
      if not isinstance(kind, TransitKind):
        raise TypeError(f'Expected TransitKind, got {type(kind)}')
    if len(set(kinds)) != len(kinds):
      raise ValueError(f'Duplicate transit kinds: {kinds}')

    available = frozenset(iter(self))
    missing = tuple(kind for kind in kinds if kind not in available)
    if len(missing) > 0:
      raise ValueError(f'Transit kinds not available: {missing}')

    selected = frozenset(kinds)
    return TransitSet(
      xiaoyun=self.xiaoyun if TransitKind.XIAOYUN in selected else None,
      dayun=self.dayun     if TransitKind.DAYUN   in selected else None,
      liunian=self.liunian if TransitKind.LIUNIAN in selected else None,
      liuyue=self.liuyue   if TransitKind.LIUYUE  in selected else None,
      liuri=self.liuri     if TransitKind.LIURI   in selected else None,
    )


class TransitDatabase:
  '''The chart-derived Xiaoyun, year-label Dayun, and physical Dayun lookups for a `BaziChart`.'''
  def __init__(self, chart: BaziChart) -> None:
    bazi = chart.bazi
    # The birth-side year is `Bazi.ganzhi_year` -- precision-attributed, same source as the
    # year pillar -- NOT the day-level `ganzhi_date.year`, which disagrees with it inside a
    # cross-midnight tie window (HOUR) and would shift every xiaoyun year by one.
    self._birth_ganzhi_year: Final[int] = bazi.ganzhi_year
    self._birth_month_key: Final[tuple[int, int]] = (
      bazi.ganzhi_year,
      _ganzhi_month_offset(bazi.month_commander),
    )
    self._utils: Final[CalendarUtilsProtocol] = calendar_utils_of(bazi.config.backend)
    self._dayun_db: Final[DayunDatabase] = DayunDatabase(chart)
    self._dayuns: Final[tuple[DayunTuple, ...]] = self._dayun_db._dayuns

    # The calendar-only fallback cannot use BaziChart.xiaoyun; that property requires a first Dayun label.
    xiaoyuns = () if len(self._dayuns) == 0 else chart.xiaoyun
    self._xiaoyun_ganzhis: Final[frozendict[int, Ganzhi]] = frozendict({
      self._birth_ganzhi_year + age - 1 : gz
      for age, gz in xiaoyuns
    })

  def xiaoyun(self, gz_year: int) -> Ganzhi | None:
    '''Return the Xiaoyun for `gz_year`, or `None` outside the Xiaoyun year range.'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    return self._xiaoyun_ganzhis.get(gz_year)

  def dayun(self, gz_year: int) -> Ganzhi | None:
    '''Return the Dayun selected for the Ganzhi-year coordinate `gz_year` by the chart's
    configured year labels. The finite year view extends the final label by ten years and
    can differ from the physical final interval; return `None` outside that label view.'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    try:
      return self._dayun_db[gz_year].ganzhi
    except ValueError:
      return None

  def _physical_dayun(
    self,
    query_key: _DayunKey,
    start_key: Callable[[int, DayunTuple], _DayunKey],
  ) -> Ganzhi | None:
    assert isinstance(query_key, tuple)
    assert callable(start_key)

    for index in reversed(range(len(self._dayuns))):
      dayun = self._dayuns[index]
      if start_key(index, dayun) <= query_key:
        return dayun.ganzhi
    return None

  def _dayun_at_month(self, gz_year: int, gz_month: Dizhi) -> Ganzhi | None:
    assert isinstance(gz_year, int)
    assert isinstance(gz_month, Dizhi)

    def __start_key(index: int, dayun: DayunTuple) -> _DayunKey:
      year, month = _ganzhi_year_month_of_jie(self._utils.prev_jie(dayun.start_moment))
      key = (year, month - 1)
      return max(key, self._birth_month_key) if index == 0 else key

    return self._physical_dayun(
      (gz_year, _ganzhi_month_offset(gz_month)),
      __start_key,
    )

  def _dayun_at_date(self, solar_date: date) -> Ganzhi | None:
    assert type(solar_date) is date

    def __start_key(_index: int, dayun: DayunTuple) -> _DayunKey:
      start = dayun.start_moment.date()
      return start.year, start.month, start.day

    return self._physical_dayun(
      (solar_date.year, solar_date.month, solar_date.day),
      __start_key,
    )

  def _dayun_at_moment(self, solar_moment: datetime) -> Ganzhi | None:
    assert isinstance(solar_moment, datetime)
    assert solar_moment.tzinfo is None

    def __key(moment: datetime) -> _DayunKey:
      whole_second = moment.replace(microsecond=0)
      return (
        whole_second.year, whole_second.month, whole_second.day,
        whole_second.hour, whole_second.minute, whole_second.second,
      )

    return self._physical_dayun(
      __key(solar_moment),
      lambda _index, dayun: __key(dayun.start_moment),
    )
