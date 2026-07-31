# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transits.py

import unittest

import random
import itertools
from datetime import date, datetime

from src.common import DayunTuple
from src.defines import Ganzhi, Dizhi
from src.utils import bazi_utils

from src.calendar.hko_data_calendar_utils import to_ganzhi
from src.bazi import Bazi, BaziGender, BaziPrecision
from src.bazi_chart import BaziChart
from src.transits import DayunDatabase, TransitMoment, TransitOptions, TransitDatabase, _ALL_OPTIONS


class TestDayunDatabase(unittest.TestCase):
  def test_simple(self) -> None:
    bazi: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
    chart: BaziChart = BaziChart(bazi)
    db = DayunDatabase(chart)

    first_dayun: DayunTuple = next(chart.dayun)
    for year in range(first_dayun.ganzhi_year, first_dayun.ganzhi_year + 10):
      self.assertEqual(db[year], DayunTuple(first_dayun.ganzhi_year, Ganzhi.from_str('己卯')))
    for year in range(first_dayun.ganzhi_year + 10, first_dayun.ganzhi_year + 20):
      self.assertEqual(db[year], DayunTuple(first_dayun.ganzhi_year + 10, Ganzhi.from_str('庚辰')))
    for year in range(first_dayun.ganzhi_year + 20, first_dayun.ganzhi_year + 30):
      self.assertEqual(db[year], DayunTuple(first_dayun.ganzhi_year + 20, Ganzhi.from_str('辛巳')))

  def test_dayun_database(self) -> None:
    chart: BaziChart = BaziChart.random()

    expected: dict[int, DayunTuple] = {}
    for start_year, dayun_ganzhi in itertools.islice(chart.dayun, 100):
      for year in range(start_year, start_year + 10): # A dayun lasts for 10 years.
        expected[year] = DayunTuple(start_year, dayun_ganzhi)

    db: DayunDatabase = DayunDatabase(chart)
    self.assertRaises(AssertionError, lambda : db[next(chart.dayun).ganzhi_year - 1]) # Test the year before the start of the dayun.

    years: list[int] = list(expected.keys())

    for year in random.sample(years, 100):
      self.assertEqual(db[year], expected[year])
    
    for year in random.sample(years, 100):
      self.assertEqual(db[year], expected[year])
    
    random.shuffle(years)
    for year in years:
      self.assertEqual(db[year], expected[year])


class TestTransitDatabase(unittest.TestCase):
  def test_support(self) -> None:
    for _ in range(4):
      chart: BaziChart = BaziChart.random()
      db: TransitDatabase = TransitDatabase(chart)

      self.assertRaises(AssertionError, lambda: db.support('1999', TransitOptions.XIAOYUN)) # type: ignore
      self.assertRaises(AssertionError, lambda: db.support(1999, TransitOptions.XIAOYUN)) # type: ignore # int no longer accepted; `TransitMoment` required.
      self.assertRaises(AssertionError, lambda: db.support(TransitMoment(1999), 'XIAOYUN')) # type: ignore
      self.assertRaises(AssertionError, lambda: db.support(TransitMoment(1999), 0x1 | 0x4)) # type: ignore
      # Zero-value and unknown-bit flags are rejected on all Python versions (3.12+'s `in` used to let them through).
      self.assertRaises(AssertionError, lambda: db.support(TransitMoment(1999), TransitOptions(0)))
      self.assertRaises(AssertionError, lambda: db.support(TransitMoment(1999), TransitOptions(0x8)))

      with self.subTest('Test ganzhi years before the birth year. Expect not to support.'):
        for gz_year in range(chart.bazi.ganzhi_date.year - 10, chart.bazi.ganzhi_date.year):
          for option in TransitOptions:
            self.assertFalse(db.support(TransitMoment(gz_year), option))

      with self.subTest('Test Xiaoyun / 小运.'):
        first_dayun_gz_year: int = next(chart.dayun).ganzhi_year
        for gz_year in range(chart.bazi.ganzhi_date.year, chart.bazi.ganzhi_date.year + len(chart.xiaoyun)):
          self.assertTrue(db.support(TransitMoment(gz_year), TransitOptions.XIAOYUN))
          self.assertTrue(db.support(TransitMoment(gz_year), TransitOptions.LIUNIAN))
          self.assertTrue(db.support(TransitMoment(gz_year), TransitOptions.XIAOYUN_LIUNIAN))

          # The last Xiaoyun year may also be the first Dayun year - this is the only expected overlap.
          if db.support(TransitMoment(gz_year), TransitOptions.DAYUN):
            self.assertEqual(gz_year, first_dayun_gz_year)
          else:
            self.assertLess(gz_year, first_dayun_gz_year)

      with self.subTest('Test Dayun / 大运.'):
        for start_gz_year, _ in itertools.islice(chart.dayun, 10): # Expect the first 10 dayuns to be supported anyways...
          for gz_year in range(start_gz_year, start_gz_year + 10):
            self.assertTrue(db.support(TransitMoment(gz_year), TransitOptions.DAYUN))
            self.assertTrue(db.support(TransitMoment(gz_year), TransitOptions.LIUNIAN))
            self.assertTrue(db.support(TransitMoment(gz_year), TransitOptions.DAYUN_LIUNIAN))

  def test_ganzhis(self) -> None:
    for _ in range(4):
      chart = BaziChart.random()
      db: TransitDatabase = TransitDatabase(chart)

      xiaoyun_ganzhis: dict[int, Ganzhi] = {
        chart.bazi.ganzhi_date.year + age - 1 : xy
        for age, xy in chart.xiaoyun
      }

      dayun_start_gz_year: int = to_ganzhi(chart.dayun_start_moment).year
      dayun_ganzhis: list[Ganzhi] = [dy.ganzhi for dy in itertools.islice(chart.dayun, 50)]

      # Randomly select 20 ganzhi years to test...
      random_liunians = random.sample(list(itertools.islice(chart.liunian, 200)), 20)
      random.shuffle(random_liunians)

      self.assertRaises(ValueError, lambda: db.ganzhis(TransitMoment(dayun_start_gz_year - 1), TransitOptions.DAYUN))

      for gz_year, _ in random_liunians:
        for option in TransitOptions:
          if not db.support(TransitMoment(gz_year), option):
            self.assertRaises(ValueError, lambda: db.ganzhis(TransitMoment(gz_year), option))
            continue

          transit_ganzhis: list[Ganzhi] = []
          if option.value & TransitOptions.XIAOYUN.value:
            transit_ganzhis.append(xiaoyun_ganzhis[gz_year])
          if option.value & TransitOptions.DAYUN.value:
            dayun_index: int = (gz_year - dayun_start_gz_year) // 10
            transit_ganzhis.append(dayun_ganzhis[dayun_index])
          if option.value & TransitOptions.LIUNIAN.value:
            transit_ganzhis.append(bazi_utils.ganzhi_of_year(gz_year))

          actual = db.ganzhis(TransitMoment(gz_year), option)
          self.assertEqual(len(actual), len(transit_ganzhis))
          for gz in actual:
            self.assertIn(gz, transit_ganzhis)


class TestTransitMoment(unittest.TestCase):
  def test_valid_shapes(self) -> None:
    '''The three granularities / 三种粒度：年、月、日。'''
    year_moment = TransitMoment(1990)
    self.assertEqual(year_moment.gz_year, 1990)
    self.assertIsNone(year_moment.gz_month)
    self.assertIsNone(year_moment.solar_date)

    month_moment = TransitMoment(1990, gz_month=Dizhi.寅)
    self.assertEqual(month_moment.gz_year, 1990)
    self.assertEqual(month_moment.gz_month, Dizhi.寅)
    self.assertIsNone(month_moment.solar_date)

    day_moment = TransitMoment(1990, solar_date=date(1990, 5, 20))
    self.assertEqual(day_moment.gz_year, 1990)
    self.assertIsNone(day_moment.gz_month)
    self.assertEqual(day_moment.solar_date, date(1990, 5, 20))

  def test_value_semantics(self) -> None:
    '''Equality and hash -- the contract that the exact-type check defends / 相等性与 hash——精确类型检查所捍卫的契约。'''
    self.assertEqual(TransitMoment(1990), TransitMoment(1990))
    self.assertEqual(hash(TransitMoment(1990)), hash(TransitMoment(1990)))
    self.assertNotEqual(TransitMoment(1990), TransitMoment(1990, gz_month=Dizhi.寅))
    self.assertEqual(1, len({TransitMoment(1990), TransitMoment(1990)}))

  def test_invalid(self) -> None:
    self.assertRaises(AssertionError, lambda: TransitMoment('1990')) # type: ignore
    self.assertRaises(AssertionError, lambda: TransitMoment(1990, gz_month=3)) # type: ignore
    self.assertRaises(AssertionError, lambda: TransitMoment(1990, solar_date='1990-05-20')) # type: ignore
    # `datetime` is a `date` subclass but breaks the value semantics / datetime 是 date 子类，但破坏值语义（与 date 不相等、hash 不同）。
    self.assertRaises(AssertionError, lambda: TransitMoment(1990, solar_date=datetime(1990, 5, 20, 12, 0)))
    # The month and day granularities are mutually exclusive / 月粒度与日粒度互斥。
    self.assertRaises(AssertionError, lambda: TransitMoment(1990, gz_month=Dizhi.寅, solar_date=date(1990, 5, 20)))

  def test_granularity_rejection(self) -> None:
    '''Month/day granularities are explicitly rejected before #48 lands / #48 落地前，月/日粒度显式拒绝。'''
    chart: BaziChart = BaziChart.random()
    db: TransitDatabase = TransitDatabase(chart)
    gz_year: int = chart.bazi.ganzhi_date.year

    moments = [
      TransitMoment(gz_year, gz_month=Dizhi.寅),
      TransitMoment(gz_year, solar_date=date(gz_year, 5, 20)),
    ]
    for moment in moments:
      self.assertRaises(NotImplementedError, lambda: db.support(moment, TransitOptions.LIUNIAN))
      self.assertRaises(NotImplementedError, lambda: db.ganzhis(moment, TransitOptions.LIUNIAN))


class TestAllOptions(unittest.TestCase):
  def test_enumeration(self) -> None:
    '''`_ALL_OPTIONS` enumerates all non-empty combos of the single-bit members / 枚举单 bit 成员的全部非空组合（扩位自动跟随）。'''
    singles = [opt for opt in TransitOptions if opt.value > 0 and opt.value & (opt.value - 1) == 0]

    self.assertEqual(len(_ALL_OPTIONS), 2 ** len(singles) - 1)
    # The unnamed combo that the old hand-listed `random()` never returned.
    self.assertIn(TransitOptions.XIAOYUN | TransitOptions.DAYUN, _ALL_OPTIONS)
    # Every enumerated option is non-zero and composed of known bits only.
    # (Do NOT assert `opt in TransitOptions` here -- on Python 3.11 the enum `in`
    # rejects unnamed composites, which is exactly what this test enumerates.)
    full_mask = sum(opt.value for opt in singles)
    for opt in _ALL_OPTIONS:
      self.assertGreater(opt.value, 0)
      self.assertEqual(full_mask, opt.value | full_mask)


class TestTransitDatabaseHourMinutePrecisions(unittest.TestCase):
  '''
  HOUR / MINUTE charts (issue #6): the database's birth-side year must be the chart's own
  precision-attributed `Bazi.ganzhi_year`, not the day-level `ganzhi_date.year`.
  '''

  def test_birth_year_is_precision_attributed(self) -> None:
    '''
    Cross-midnight tie chart (2009-02-03 23:30 female, HOUR): the chart's year pillar is
    己丑 2009, its liunian generator starts at 2009, and its dayun starts in 2018 (虚岁 10).
    Before the fix the day-level 2008 leaked in: `ganzhis(2008, LIUNIAN)` returned 戊子 --
    a ganzhi this chart's liunian never produces -- and 虚岁 10 mapped to 2017, so the true
    dayun-start year 2018 answered `support == False` for xiaoyun.
    '''
    chart: BaziChart = BaziChart(Bazi.create('2009-02-03 23:30', 'female', 'hour'))
    self.assertEqual(chart.bazi.ganzhi_year, 2009)
    db: TransitDatabase = TransitDatabase(chart)

    for options in (TransitOptions.LIUNIAN, TransitOptions.XIAOYUN):
      with self.subTest(options=options):
        self.assertFalse(db.support(TransitMoment(2008), options))
        self.assertTrue(db.support(TransitMoment(2009), options))

    self.assertTrue(db.support(TransitMoment(2018), TransitOptions.XIAOYUN)) # 虚岁 10, the dayun-start year.
    self.assertFalse(db.support(TransitMoment(2019), TransitOptions.XIAOYUN)) # Past the xiaoyun range.
    self.assertEqual(
      db.ganzhis(TransitMoment(2009), TransitOptions.LIUNIAN),
      (chart.bazi.year_pillar,), # The first liunian IS the year pillar.
    )

  def test_day_precision_unchanged(self) -> None:
    '''At DAY the two year channels agree, so the database is unaffected by the migration.'''
    chart: BaziChart = BaziChart(Bazi.create('2009-02-03 23:30', 'female', 'day'))
    self.assertEqual(chart.bazi.ganzhi_year, chart.bazi.ganzhi_date.year)
    db: TransitDatabase = TransitDatabase(chart)
    self.assertTrue(db.support(TransitMoment(2008), TransitOptions.LIUNIAN))  # 戊子 2008 IS this chart's first liunian.
    self.assertFalse(db.support(TransitMoment(2007), TransitOptions.LIUNIAN))
