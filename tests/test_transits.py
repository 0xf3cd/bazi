# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transits.py

import random
import itertools
from datetime import date, datetime

import pytest

from src.data_types import DayunTuple
from src.defines import Ganzhi, Dizhi
from src.utils import bazi_utils

from src.bazi import Bazi, BaziGender
from src.school import BaziConfig
from src.bazi_chart import BaziChart
from src.calendar import calendar_utils_of
from src.transits import DayunDatabase, TransitMoment, TransitOptions, TransitDatabase, _ALL_OPTIONS


def _dayun_start_gz_year(chart: BaziChart) -> int:
  # Independent recomputation, not a mirror of `next(chart.dayun).ganzhi_year` -- the very
  # expression `TransitDatabase` consumes: the day-level label of `dayun_start_moment`
  # through the chart's own backend, floored at `Bazi.ganzhi_year`.
  return max(
    calendar_utils_of(chart.bazi.config.backend).to_ganzhi(chart.dayun_start_moment).year,
    chart.bazi.ganzhi_year,
  )


def test_simple() -> None:
  bazi: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE)
  chart: BaziChart = BaziChart(bazi)
  db = DayunDatabase(chart)

  first_dayun: DayunTuple = next(chart.dayun)
  for year in range(first_dayun.ganzhi_year, first_dayun.ganzhi_year + 10):
    assert db[year] == DayunTuple(first_dayun.ganzhi_year, Ganzhi.from_str('己卯'))
  for year in range(first_dayun.ganzhi_year + 10, first_dayun.ganzhi_year + 20):
    assert db[year] == DayunTuple(first_dayun.ganzhi_year + 10, Ganzhi.from_str('庚辰'))
  for year in range(first_dayun.ganzhi_year + 20, first_dayun.ganzhi_year + 30):
    assert db[year] == DayunTuple(first_dayun.ganzhi_year + 20, Ganzhi.from_str('辛巳'))


def test_dayun_database() -> None:
  chart: BaziChart = BaziChart.random()

  expected: dict[int, DayunTuple] = {}
  for start_year, dayun_ganzhi in itertools.islice(chart.dayun, 100):
    for year in range(start_year, start_year + 10): # A dayun lasts for 10 years.
      expected[year] = DayunTuple(start_year, dayun_ganzhi)

  db: DayunDatabase = DayunDatabase(chart)
  with pytest.raises(TypeError):
    db['2000'] # type: ignore
  with pytest.raises(ValueError): # Test the year before the start of the dayun.
    db[next(chart.dayun).ganzhi_year - 1]

  years: list[int] = list(expected.keys())

  for year in random.sample(years, 100):
    assert db[year] == expected[year]

  for year in random.sample(years, 100):
    assert db[year] == expected[year]

  random.shuffle(years)
  for year in years:
    assert db[year] == expected[year]


def test_support() -> None:
  for _ in range(4):
    chart: BaziChart = BaziChart.random()
    db: TransitDatabase = TransitDatabase(chart)

    with pytest.raises(TypeError):
      db.support('1999', TransitOptions.XIAOYUN) # type: ignore
    with pytest.raises(TypeError):
      db.support(1999, TransitOptions.XIAOYUN) # type: ignore # int no longer accepted; `TransitMoment` required.
    with pytest.raises(TypeError):
      db.support(TransitMoment(1999), 'XIAOYUN') # type: ignore
    with pytest.raises(TypeError):
      db.support(TransitMoment(1999), 0x1 | 0x4) # type: ignore
    # Zero-value and unknown-bit flags are rejected on all Python versions (3.12+'s `in` used to let them through).
    with pytest.raises(ValueError):
      db.support(TransitMoment(1999), TransitOptions(0))
    with pytest.raises(ValueError):
      db.support(TransitMoment(1999), TransitOptions(0x8))

    # Ganzhi years before the birth year are not supported. The birth-side channel is the
    # precision-attributed `ganzhi_year` -- the field `TransitDatabase` actually reads --
    # not the day-level `ganzhi_date.year` (they agree at DAY but diverge on HOUR ties).
    for gz_year in range(chart.bazi.ganzhi_year - 10, chart.bazi.ganzhi_year):
      for option in TransitOptions:
        assert not db.support(TransitMoment(gz_year), option)

    # Xiaoyun / 小运.
    first_dayun_gz_year: int = _dayun_start_gz_year(chart)
    for gz_year in range(chart.bazi.ganzhi_year, chart.bazi.ganzhi_year + len(chart.xiaoyun)):
      assert db.support(TransitMoment(gz_year), TransitOptions.XIAOYUN)
      assert db.support(TransitMoment(gz_year), TransitOptions.LIUNIAN)
      assert db.support(TransitMoment(gz_year), TransitOptions.XIAOYUN_LIUNIAN)

      # The last Xiaoyun year may also be the first Dayun year - this is the only expected overlap.
      if db.support(TransitMoment(gz_year), TransitOptions.DAYUN):
        assert gz_year == first_dayun_gz_year
      else:
        assert gz_year < first_dayun_gz_year

    # Dayun / 大运. Each dayun lasts 10 years, stepping from the independently recomputed
    # first dayun year above -- not from `chart.dayun`, which is what the database reads.
    for start_gz_year in range(first_dayun_gz_year, first_dayun_gz_year + 100, 10): # Expect the first 10 dayuns to be supported anyways...
      for gz_year in range(start_gz_year, start_gz_year + 10):
        assert db.support(TransitMoment(gz_year), TransitOptions.DAYUN)
        assert db.support(TransitMoment(gz_year), TransitOptions.LIUNIAN)
        assert db.support(TransitMoment(gz_year), TransitOptions.DAYUN_LIUNIAN)


def test_ganzhis() -> None:
  for _ in range(4):
    chart = BaziChart.random()
    db: TransitDatabase = TransitDatabase(chart)

    with pytest.raises(TypeError):
      db.ganzhis('1999', TransitOptions.XIAOYUN) # type: ignore
    with pytest.raises(TypeError):
      db.ganzhis(TransitMoment(1999), 'XIAOYUN') # type: ignore
    with pytest.raises(ValueError):
      db.ganzhis(TransitMoment(1999), TransitOptions(0))

    xiaoyun_ganzhis: dict[int, Ganzhi] = {
      chart.bazi.ganzhi_year + age - 1 : xy
      for age, xy in chart.xiaoyun
    }

    dayun_start_gz_year: int = _dayun_start_gz_year(chart)
    dayun_ganzhis: list[Ganzhi] = [dy.ganzhi for dy in itertools.islice(chart.dayun, 50)]

    # Randomly select 20 ganzhi years to test...
    random_liunians = random.sample(list(itertools.islice(chart.liunian, 200)), 20)
    random.shuffle(random_liunians)

    with pytest.raises(ValueError):
      db.ganzhis(TransitMoment(dayun_start_gz_year - 1), TransitOptions.DAYUN)

    for gz_year, _ in random_liunians:
      # `_ALL_OPTIONS`, not `TransitOptions`: on Python 3.11+ the enum iterates single-bit
      # members only, and single-bit queries can never observe the append order.
      for option in _ALL_OPTIONS:
        if not db.support(TransitMoment(gz_year), option):
          with pytest.raises(ValueError):
            db.ganzhis(TransitMoment(gz_year), option)
          continue

        transit_ganzhis: list[Ganzhi] = []
        if option.value & TransitOptions.XIAOYUN.value:
          transit_ganzhis.append(xiaoyun_ganzhis[gz_year])
        if option.value & TransitOptions.DAYUN.value:
          dayun_index: int = (gz_year - dayun_start_gz_year) // 10
          transit_ganzhis.append(dayun_ganzhis[dayun_index])
        if option.value & TransitOptions.LIUNIAN.value:
          transit_ganzhis.append(bazi_utils.ganzhi_of_year(gz_year))

        # Exact tuple equality pins the order too: 小运 -> 大运 -> 流年.
        actual = db.ganzhis(TransitMoment(gz_year), option)
        assert actual == tuple(transit_ganzhis)


def test_valid_shapes() -> None:
  '''The three granularities / 三种粒度：年、月、日。'''
  year_moment = TransitMoment(1990)
  assert year_moment.gz_year == 1990
  assert year_moment.gz_month is None
  assert year_moment.solar_date is None

  month_moment = TransitMoment(1990, gz_month=Dizhi.寅)
  assert month_moment.gz_year == 1990
  assert month_moment.gz_month == Dizhi.寅
  assert month_moment.solar_date is None

  day_moment = TransitMoment(1990, solar_date=date(1990, 5, 20))
  assert day_moment.gz_year == 1990
  assert day_moment.gz_month is None
  assert day_moment.solar_date == date(1990, 5, 20)


def test_value_semantics() -> None:
  '''Equality and hash -- the contract that the exact-type check defends / 相等性与 hash——精确类型检查所捍卫的契约。'''
  assert TransitMoment(1990) == TransitMoment(1990)
  assert hash(TransitMoment(1990)) == hash(TransitMoment(1990))
  assert TransitMoment(1990) != TransitMoment(1990, gz_month=Dizhi.寅)
  assert 1 == len({TransitMoment(1990), TransitMoment(1990)})


def test_invalid() -> None:
  with pytest.raises(TypeError):
    TransitMoment('1990') # type: ignore
  with pytest.raises(TypeError):
    TransitMoment(1990, gz_month=3) # type: ignore
  with pytest.raises(TypeError):
    TransitMoment(1990, solar_date='1990-05-20') # type: ignore
  # `datetime` is a `date` subclass but breaks the value semantics / datetime 是 date 子类，但破坏值语义（与 date 不相等、hash 不同）。
  with pytest.raises(TypeError):
    TransitMoment(1990, solar_date=datetime(1990, 5, 20, 12, 0))
  # The month and day granularities are mutually exclusive / 月粒度与日粒度互斥。
  with pytest.raises(ValueError):
    TransitMoment(1990, gz_month=Dizhi.寅, solar_date=date(1990, 5, 20))


def test_granularity_rejection() -> None:
  '''Month/day granularities are explicitly rejected before #48 lands / #48 落地前，月/日粒度显式拒绝。'''
  chart: BaziChart = BaziChart.random()
  db: TransitDatabase = TransitDatabase(chart)
  gz_year: int = chart.bazi.ganzhi_date.year

  moments = [
    TransitMoment(gz_year, gz_month=Dizhi.寅),
    TransitMoment(gz_year, solar_date=date(gz_year, 5, 20)),
  ]
  for moment in moments:
    with pytest.raises(NotImplementedError):
      db.support(moment, TransitOptions.LIUNIAN)
    with pytest.raises(NotImplementedError):
      db.ganzhis(moment, TransitOptions.LIUNIAN)


def test_enumeration() -> None:
  '''`_ALL_OPTIONS` enumerates all non-empty combos of the single-bit members / 枚举单 bit 成员的全部非空组合（扩位自动跟随）。'''
  singles = [opt for opt in TransitOptions if opt.value > 0 and opt.value & (opt.value - 1) == 0]

  assert len(_ALL_OPTIONS) == 2 ** len(singles) - 1
  # The unnamed combo that the old hand-listed `random()` never returned.
  assert TransitOptions.XIAOYUN | TransitOptions.DAYUN in _ALL_OPTIONS
  # Every enumerated option is non-zero and composed of known bits only.
  # (Do NOT assert `opt in TransitOptions` here -- on Python 3.11 the enum `in`
  # rejects unnamed composites, which is exactly what this test enumerates.)
  full_mask = sum(opt.value for opt in singles)
  for opt in _ALL_OPTIONS:
    assert opt.value > 0
    assert full_mask == opt.value | full_mask


# HOUR / MINUTE charts (issue #6): the database's birth-side year must be the chart's own
# precision-attributed `Bazi.ganzhi_year`, not the day-level `ganzhi_date.year`.


def test_birth_year_is_precision_attributed() -> None:
  '''
  Cross-midnight tie chart (2009-02-03 23:30 female, HOUR): the chart's year pillar is
  己丑 2009, its liunian generator starts at 2009, and its dayun starts in 2018 (虚岁 10).
  The day-level 2008 must stay out of the database: 戊子 is a ganzhi this chart's liunian
  never produces, and 虚岁 must count from 2009 so that the dayun-start year 2018 supports
  xiaoyun.
  '''
  chart: BaziChart = BaziChart(Bazi.create('2009-02-03 23:30', 'female', BaziConfig.from_values(precision='hour')))
  assert chart.bazi.ganzhi_year == 2009
  db: TransitDatabase = TransitDatabase(chart)

  for options in (TransitOptions.LIUNIAN, TransitOptions.XIAOYUN):
    assert not db.support(TransitMoment(2008), options)
    assert db.support(TransitMoment(2009), options)

  assert db.support(TransitMoment(2018), TransitOptions.XIAOYUN) # 虚岁 10, the dayun-start year.
  assert not db.support(TransitMoment(2019), TransitOptions.XIAOYUN) # Past the xiaoyun range.
  assert db.ganzhis(TransitMoment(2009), TransitOptions.LIUNIAN) == (
    chart.bazi.year_pillar, # The first liunian IS the year pillar.
  )


def test_day_precision_unchanged() -> None:
  '''At DAY the two year channels agree.'''
  chart: BaziChart = BaziChart(Bazi.create('2009-02-03 23:30', 'female'))
  assert chart.bazi.ganzhi_year == chart.bazi.ganzhi_date.year
  db: TransitDatabase = TransitDatabase(chart)
  assert db.support(TransitMoment(2008), TransitOptions.LIUNIAN)  # 戊子 2008 IS this chart's first liunian.
  assert not db.support(TransitMoment(2007), TransitOptions.LIUNIAN)


def test_dayun_year_floored_at_ganzhi_year() -> None:
  '''
  Cross-midnight tie chart (2009-02-03 23:30 male, HOUR): the backward-counted dayun
  start clamps to the birth moment itself, whose day-level label is still the OLD year
  2008 (戊子). The first dayun year must be floored up to the chart's own precision-
  attributed `Bazi.ganzhi_year` 2009 (己丑) -- otherwise 2008 would wrongly support
  dayun, and every later year would resolve one dayun step off (2018: 甲子 instead of
  乙丑).
  '''
  chart: BaziChart = BaziChart(Bazi.create('2009-02-03 23:30', 'male', BaziConfig.from_values(precision='hour')))
  assert chart.dayun_start_moment == chart.bazi.solar_datetime # The clamp: the start IS the birth.
  assert chart.bazi.ganzhi_date.year == 2008 # The bare day-level label of the clamped start.
  assert chart.bazi.ganzhi_year == 2009

  # 逆排: the first dayun steps one ganzhi back from the month pillar 丙寅 -> 乙丑.
  first_dayun: DayunTuple = next(chart.dayun)
  assert first_dayun == DayunTuple(2009, Ganzhi.from_str('乙丑'))

  db: TransitDatabase = TransitDatabase(chart)
  with pytest.raises(ValueError):
    db.ganzhis(TransitMoment(2008), TransitOptions.DAYUN) # 戊子 2008 is below the floored start.
  assert db.ganzhis(TransitMoment(2009), TransitOptions.DAYUN) == (
    Ganzhi.from_str('乙丑'),
  )
  # Xiaoyun, too, is keyed by the precision-attributed 2009, not the day-level 2008.
  assert db.ganzhis(TransitMoment(2009), TransitOptions.XIAOYUN) == (
    Ganzhi.from_str('乙亥'),
  )
  # 2018 is the last year of the first dayun (2009-2018); the unfloored start 2008 would
  # put it one step further back (甲子). 2019 opens the second dayun.
  assert db.ganzhis(TransitMoment(2018), TransitOptions.DAYUN_LIUNIAN) == (
    Ganzhi.from_str('乙丑'),
    Ganzhi.from_str('戊戌'), # The 2018 liunian.
  )
  assert db.ganzhis(TransitMoment(2019), TransitOptions.DAYUN) == (
    Ganzhi.from_str('甲子'),
  )
