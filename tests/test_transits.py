# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transits.py

import pytest
import unittest

import random
import itertools
from datetime import datetime

from src.Common import DayunTuple
from src.Defines import Ganzhi
from src.Utils import BaziUtils

from src.Calendar.HkoDataCalendarUtils import to_ganzhi
from src.Bazi import Bazi, BaziGender, BaziPrecision
from src.BaziChart import BaziChart
from src.Transits import DayunDatabase, TransitOptions, TransitDatabase


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
      self.assertRaises(AssertionError, lambda: db.support(1999, 'XIAOYUN')) # type: ignore
      self.assertRaises(AssertionError, lambda: db.support(1999, 0x1 | 0x4)) # type: ignore

      with self.subTest('Test ganzhi years before the birth year. Expect not to support.'):
        for gz_year in range(chart.bazi.ganzhi_date.year - 10, chart.bazi.ganzhi_date.year):
          for option in TransitOptions:
            self.assertFalse(db.support(gz_year, option))

      with self.subTest('Test Xiaoyun / 小运.'):
        first_dayun_gz_year: int = next(chart.dayun).ganzhi_year
        for gz_year in range(chart.bazi.ganzhi_date.year, chart.bazi.ganzhi_date.year + len(chart.xiaoyun)):
          self.assertTrue(db.support(gz_year, TransitOptions.XIAOYUN))
          self.assertTrue(db.support(gz_year, TransitOptions.LIUNIAN))
          self.assertTrue(db.support(gz_year, TransitOptions.XIAOYUN_LIUNIAN))

          # The last Xiaoyun year may also be the first Dayun year - this is the only expected overlap.
          if db.support(gz_year, TransitOptions.DAYUN):
            self.assertEqual(gz_year, first_dayun_gz_year)
          else:
            self.assertLess(gz_year, first_dayun_gz_year)

      with self.subTest('Test Dayun / 大运.'):
        for start_gz_year, _ in itertools.islice(chart.dayun, 10): # Expect the first 10 dayuns to be supported anyways...
          for gz_year in range(start_gz_year, start_gz_year + 10):
            self.assertTrue(db.support(gz_year, TransitOptions.DAYUN))
            self.assertTrue(db.support(gz_year, TransitOptions.LIUNIAN))
            self.assertTrue(db.support(gz_year, TransitOptions.DAYUN_LIUNIAN))

  def test_ganzhis(self) -> None:
    for _ in range(4):
      chart = BaziChart.random()
      db: TransitDatabase = TransitDatabase(chart)

      xiaoyun_ganzhis: dict[int, Ganzhi] = {
        chart.bazi.ganzhi_date.year + age - 1 : xy
        for age, xy in chart.xiaoyun
      }

      dayun_start_gz_year: int = to_ganzhi(chart.dayun_start_moment).year
      dayun_ganzhis: list[Ganzhi] = list(dy.ganzhi for dy in itertools.islice(chart.dayun, 50))

      # Randomly select 20 ganzhi years to test...
      random_liunians = random.sample(list(itertools.islice(chart.liunian, 200)), 20)
      random.shuffle(random_liunians)

      self.assertRaises(ValueError, lambda: db.ganzhis(dayun_start_gz_year - 1, TransitOptions.DAYUN))

      for gz_year, _ in random_liunians:
        for option in TransitOptions:
          if not db.support(gz_year, option):
            self.assertRaises(ValueError, lambda: db.ganzhis(gz_year, option))
            continue

          transit_ganzhis: list[Ganzhi] = []
          if option.value & TransitOptions.XIAOYUN.value:
            transit_ganzhis.append(xiaoyun_ganzhis[gz_year])
          if option.value & TransitOptions.DAYUN.value:
            dayun_index: int = (gz_year - dayun_start_gz_year) // 10
            transit_ganzhis.append(dayun_ganzhis[dayun_index])
          if option.value & TransitOptions.LIUNIAN.value:
            transit_ganzhis.append(BaziUtils.ganzhi_of_year(gz_year))

          actual = db.ganzhis(gz_year, option)
          self.assertEqual(len(actual), len(transit_ganzhis))
          for gz in actual:
            self.assertIn(gz, transit_ganzhis)
