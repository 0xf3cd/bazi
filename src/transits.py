# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import random

from dataclasses import dataclass
from datetime import date
from enum import unique, IntFlag
from functools import reduce
from itertools import combinations
from typing import Final
from collections.abc import Generator

from .common import DayunTuple, frozendict
from .defines import Ganzhi, Dizhi
from .utils.bazi_utils import ganzhi_of_year
from .bazi_chart import BaziChart


class DayunDatabase:
  '''A database that figures out a given Ganzhi year falls into which Dayun (大运).'''
  def __init__(self, chart: BaziChart) -> None:
    self._gen: Final[Generator[DayunTuple, None, None]] = chart.dayun
    self._first_dayun: Final[DayunTuple] = next(self._gen)
    self._cache: Final[dict[int, Ganzhi]] = {
      self._first_dayun.ganzhi_year : self._first_dayun.ganzhi,
    }

  def __getitem__(self, gz_year: int) -> DayunTuple:
    assert isinstance(gz_year, int)
    assert gz_year >= self._first_dayun.ganzhi_year

    dayun_idx: int = (gz_year - self._first_dayun.ganzhi_year) // 10
    expected_gz_year: int = self._first_dayun.ganzhi_year + 10 * dayun_idx

    while expected_gz_year not in self._cache:
      next_dayun: DayunTuple = next(self._gen)
      self._cache[next_dayun.ganzhi_year] = next_dayun.ganzhi

    return DayunTuple(expected_gz_year, self._cache[expected_gz_year])


@dataclass(frozen=True)
class TransitMoment:
  '''
  The moment that a transit refers to (运作用的时刻).

  Only the year granularity is supported for now -- pass `gz_year` only.
  `gz_month` (for 流月) and `solar_date` (for 流日) are reserved for #48.
  目前仅支持年粒度——只传 `gz_year` 即可。`gz_month`（流月用）和 `solar_date`（流日用）为 #48 预留。

  Invariant (unchecked here): `gz_year` is always the Ganzhi year (立春分界), and when
  `solar_date` is set, `gz_year` must be the Ganzhi year that `solar_date` falls in.
  The caller is responsible for now; `TransitDatabase` will enforce this when #48 lands
  (it has calendar access; this value type must not).
  不变量（此处不校验）：`gz_year` 始终是干支年（立春分界）；传入 `solar_date` 时，`gz_year`
  必须是 `solar_date` 所属的干支年。暂时由调用方负责；#48 落地时由 `TransitDatabase` 强制
  （它能访问历法，而本值类型不应绑定历法后端）。
  '''
  gz_year:    int
  gz_month:   Dizhi | None = None # The month's Dizhi (月支; 节气月, 正月建寅), for 流月.
  solar_date: date | None = None  # The solar date (公历日期), for 流日.

  def __post_init__(self) -> None:
    # Type check at runtime. Note `datetime` is a subclass of `date` but breaks the value
    # semantics (a `datetime` never equals a `date`, and their hashes differ), so require
    # the exact type here. 运行时类型检查。datetime 是 date 的子类但破坏值语义（不相等、
    # hash 不同），故此处要求精确类型。
    assert isinstance(self.gz_year, int)
    assert self.gz_month is None or isinstance(self.gz_month, Dizhi)
    assert self.solar_date is None or type(self.solar_date) is date
    # The month and day granularities are mutually exclusive: a day's Ganzhi is fully
    # determined by `solar_date`, no `gz_month` needed. 月粒度与日粒度互斥（日柱由 solar_date 唯一确定）。
    assert not (self.gz_month is not None and self.solar_date is not None)


def _ensure_year_moment(moment: TransitMoment) -> None:
  '''Only the year granularity is supported before #48 lands; reject the other granularities explicitly. / #48 落地前仅支持年粒度，其余粒度显式拒绝。'''
  if moment.gz_month is not None or moment.solar_date is not None:
    raise NotImplementedError(f'Only year-granularity transits are supported for now (目前仅支持年粒度的运): {moment}')


@unique
class TransitOptions(IntFlag):
  '''Specifies whether Dayun / Xiaoyun / Liunian transits should be considered. 用于指定是否考虑大运流年、小运、流年等。'''
  XIAOYUN         = 0x1
  DAYUN           = 0x2
  LIUNIAN         = 0x4
  XIAOYUN_LIUNIAN = XIAOYUN | LIUNIAN
  DAYUN_LIUNIAN   = DAYUN   | LIUNIAN

  @staticmethod
  def random() -> 'TransitOptions':
    '''Mainly for testing purpose.'''
    return random.choice(_ALL_OPTIONS)


def _all_options() -> list[TransitOptions]:
  '''
  All non-empty combinations of the single-bit `TransitOptions` members.
  The enumeration follows new transit kinds (e.g. 流月/流日 in #48) automatically --
  but wiring up their semantics in `support`/`ganzhis` is still required separately.
  单 bit 成员的全部非空组合——枚举随新增运种类（如 #48 的流月/流日）自动跟随，但语义接线仍需同步修改 `support`/`ganzhis`。
  '''
  # `list(TransitOptions)` only yields single-bit members on Python 3.11+,
  # silently dropping the composite options. Filter defensively anyway.
  singles: list[TransitOptions] = [opt for opt in TransitOptions if opt.value.bit_count() == 1]
  return [
    reduce(lambda acc, opt: acc | opt, combo)
    for r in range(1, len(singles) + 1)
    for combo in combinations(singles, r)
  ]


'''The constant option space for `TransitOptions.random()` / `random()` 的常量选项空间。'''
_ALL_OPTIONS: Final[tuple[TransitOptions, ...]] = tuple(_all_options())


class TransitDatabase:
  '''A database that figures out the Ganzhis of transits.'''
  def __init__(self, chart: BaziChart) -> None:
    # The birth-side year is `Bazi.ganzhi_year` -- precision-attributed, same source as the
    # year pillar -- NOT the day-level `ganzhi_date.year`, which disagrees with it inside a
    # cross-midnight tie window (HOUR) and would shift every xiaoyun year by one and admit
    # liunian years the chart's own generator never produces.
    self._birth_ganzhi_year: Final[int] = chart.bazi.ganzhi_year

    self._xiaoyun_ganzhis: Final[frozendict[int, Ganzhi]] = frozendict({
      self._birth_ganzhi_year + age - 1 : gz
      for age, gz in chart.xiaoyun
    })

    self._first_dayun_start_gz_year: Final[int] = next(chart.dayun).ganzhi_year
    self._dayun_db: Final[DayunDatabase] = DayunDatabase(chart)

  def support(self, moment: TransitMoment, options: TransitOptions) -> bool:
    '''
    Return whether the given `moment` and `option` are supported by this `TransitDatabase`.

    Args:
    - `moment`: The moment in Ganzhi calendar, mainly used to compute the transit pillars. 干支历法中的时刻，主要用于计算运（小运/大运/流年）的天干地支。Only the year granularity is supported for now (目前仅支持年粒度)。
    - `options`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Return: (bool) Whether the given `moment` and `options` are supported by this `TransitDatabase`.

    Note: raises `NotImplementedError` for month/day-granularity moments until #48. / 注意：#48 落地前，月/日粒度的 moment 会抛 `NotImplementedError`。
    '''

    assert isinstance(moment, TransitMoment)
    assert isinstance(options, TransitOptions)
    # `options in TransitOptions` rejects unnamed composites (e.g. XIAOYUN|DAYUN) on
    # Python 3.11 (EnumType.__contains__ semantics), so check the enumerated space instead.
    assert options in _ALL_OPTIONS
    _ensure_year_moment(moment)

    gz_year: Final[int] = moment.gz_year
    if options & TransitOptions.XIAOYUN and gz_year not in self._xiaoyun_ganzhis:
      return False
    if options & TransitOptions.DAYUN and gz_year < self._first_dayun_start_gz_year:
      return False
    if options & TransitOptions.LIUNIAN and gz_year < self._birth_ganzhi_year: # noqa: SIM103 # symmetric guard clauses, one per option
      return False

    return True

  def ganzhis(self, moment: TransitMoment, options: TransitOptions) -> tuple[Ganzhi, ...]:
    '''
    Return the Ganzhis of the selected transits for the given `moment` and `option`.

    返回所选中的小运、大运或流年等对应的干支。

    Args:
    - `moment`: The moment in Ganzhi calendar, mainly used to compute the transit pillars. 干支历法中的时刻，主要用于计算运（小运/大运/流年）的天干地支。Only the year granularity is supported for now (目前仅支持年粒度)。
    - `options`: Specifies the pillars to be picked from transits. 用于指定是否考虑流年、小运、大运等。

    Return: (tuple[Ganzhi, ...]) The Ganzhis of the selected transits for the given `moment` and `options`.

    Note: raises `NotImplementedError` for month/day-granularity moments until #48 (via `support`). / 注意：#48 落地前，月/日粒度的 moment 会抛 `NotImplementedError`（经 `support` 冒出）。
    '''

    assert isinstance(moment, TransitMoment)
    assert isinstance(options, TransitOptions)
    # See `support` for why `_ALL_OPTIONS` instead of `options in TransitOptions` (3.11 semantics).
    assert options in _ALL_OPTIONS

    if not self.support(moment, options):
      raise ValueError(f'Inputs not supported. Moment: {moment}, options: {options}')

    gz_year: Final[int] = moment.gz_year
    transit_ganzhis: list[Ganzhi] = []
    if options & TransitOptions.XIAOYUN:
      assert gz_year in self._xiaoyun_ganzhis
      transit_ganzhis.append(self._xiaoyun_ganzhis[gz_year])
    if options & TransitOptions.DAYUN:
      assert gz_year >= self._first_dayun_start_gz_year
      transit_ganzhis.append(self._dayun_db[gz_year].ganzhi)
    if options & TransitOptions.LIUNIAN:
      assert gz_year >= self._birth_ganzhi_year
      transit_ganzhis.append(ganzhi_of_year(gz_year))

    return tuple(transit_ganzhis)
