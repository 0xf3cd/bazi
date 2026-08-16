# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from enum import Enum, unique
from typing import Final

from .common import frozendict
from .data_types import DayunTuple
from .defines import Ganzhi, Dizhi
from .bazi_chart import BaziChart


class DayunDatabase:
  '''Locates the Dayun (大运) that a given Ganzhi year falls into, by closed-form
  arithmetic from the first Dayun. 由首运闭式定位任一干支年所属的大运。'''
  def __init__(self, chart: BaziChart) -> None:
    self._first_dayun: Final[DayunTuple] = next(chart.dayun)
    self._step: Final[int] = 1 if chart.dayun_order else -1

  def __getitem__(self, gz_year: int) -> DayunTuple:
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    if gz_year < self._first_dayun.ganzhi_year:
      raise ValueError(f'Year {gz_year} is before the first dayun year {self._first_dayun.ganzhi_year}')

    # Dayuns are arithmetic: each lasts 10 years and steps the sexagenary cycle by one.
    # 大运是等差序列：每运十年，六十甲子进（退）一位，直接按下标闭式计算。
    dayun_idx: int = (gz_year - self._first_dayun.ganzhi_year) // 10
    return DayunTuple(self._first_dayun.ganzhi_year + 10 * dayun_idx,
                      self._first_dayun.ganzhi.next(self._step * dayun_idx))


@dataclass(frozen=True)
class TransitYear:
  '''A year-granularity transit query. 年粒度流运查询。'''
  gz_year: int

  def __post_init__(self) -> None:
    if not isinstance(self.gz_year, int):
      raise TypeError(f'Expected int, got {type(self.gz_year)}')


@dataclass(frozen=True)
class TransitMonth:
  '''A month-granularity transit query. 月粒度流运查询。'''
  gz_year: int
  gz_month: Dizhi

  def __post_init__(self) -> None:
    if not isinstance(self.gz_year, int):
      raise TypeError(f'Expected int, got {type(self.gz_year)}')
    if not isinstance(self.gz_month, Dizhi):
      raise TypeError(f'Expected Dizhi, got {type(self.gz_month)}')


@dataclass(frozen=True)
class TransitDate:
  '''A date-granularity transit query. 日粒度流运查询。'''
  solar_date: date

  def __post_init__(self) -> None:
    # `datetime` is a `date` subclass but has different equality/hash semantics.
    if type(self.solar_date) is not date:
      raise TypeError(f'Expected date (not datetime), got {type(self.solar_date)}')


'''A year-, month-, or date-granularity transit query. 年、月或日粒度的流运查询。'''
TransitQuery = TransitYear | TransitMonth | TransitDate


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
  '''The chart-derived Xiaoyun and Dayun lookups for a `BaziChart`.'''
  def __init__(self, chart: BaziChart) -> None:
    # The birth-side year is `Bazi.ganzhi_year` -- precision-attributed, same source as the
    # year pillar -- NOT the day-level `ganzhi_date.year`, which disagrees with it inside a
    # cross-midnight tie window (HOUR) and would shift every xiaoyun year by one.
    self._birth_ganzhi_year: Final[int] = chart.bazi.ganzhi_year

    self._xiaoyun_ganzhis: Final[frozendict[int, Ganzhi]] = frozendict({
      self._birth_ganzhi_year + age - 1 : gz
      for age, gz in chart.xiaoyun
    })

    self._first_dayun_start_gz_year: Final[int] = next(chart.dayun).ganzhi_year
    self._dayun_db: Final[DayunDatabase] = DayunDatabase(chart)

  def xiaoyun(self, gz_year: int) -> Ganzhi | None:
    '''Return the Xiaoyun for `gz_year`, or `None` outside the Xiaoyun year range.'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    return self._xiaoyun_ganzhis.get(gz_year)

  def dayun(self, gz_year: int) -> Ganzhi | None:
    '''Return the Dayun for `gz_year`, or `None` before the first Dayun.'''
    if not isinstance(gz_year, int):
      raise TypeError(f'Expected int, got {type(gz_year)}')
    if gz_year < self._first_dayun_start_gz_year:
      return None
    return self._dayun_db[gz_year].ganzhi
