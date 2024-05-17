# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_analyzer.py

import pytest
import unittest
import itertools

from src.Defines import Tiangan
from src.Common import TianganRelationDiscovery
from src.Utils import BaziUtils, TianganUtils
from src.Calendar.HkoDataCalendarUtils import to_ganzhi

from src.BaziChart import BaziChart
from src.Analyzer import AtBirthAnalyzer, TransitAnalyzer


class TestAtBirthAnalyzer(unittest.TestCase):
  @pytest.mark.slow
  def test_tiangan(self) -> None:
    for _ in range(128):
      chart: BaziChart = BaziChart.random()
      analyzer: AtBirthAnalyzer = AtBirthAnalyzer(chart)

      with self.subTest('new discovery dict'):
        self.assertIsNot(analyzer.tiangan, analyzer.tiangan)
      with self.subTest('equality'):
        self.assertEqual(analyzer.tiangan, analyzer.tiangan)

      expected: TianganRelationDiscovery = TianganUtils.discover(chart.bazi.four_tiangans)
      self.assertEqual(expected, analyzer.tiangan)


class TestTransitAnalyzer(unittest.TestCase):
  def test_supports(self) -> None:
    for _ in range(5):
      chart: BaziChart = BaziChart.random()
      analyzer: TransitAnalyzer = TransitAnalyzer(chart)

      self.assertRaises(AssertionError, analyzer.supports, '1999', TransitAnalyzer.Level.XIAOYUN) # type: ignore
      self.assertRaises(AssertionError, analyzer.supports, 1999, 'XIAOYUN') # type: ignore
      self.assertRaises(AssertionError, analyzer.supports, 1999, 0x1 | 0x4) # type: ignore

      for gz_year in range(chart.bazi.ganzhi_date.year - 10, chart.bazi.ganzhi_date.year):
        for level in TransitAnalyzer.Level:
          self.assertFalse(analyzer.supports(gz_year, level))

      first_dayun_gz_year: int = next(chart.dayun).ganzhi_year
      for gz_year in range(chart.bazi.ganzhi_date.year, chart.bazi.ganzhi_date.year + len(chart.xiaoyun)):
        self.assertTrue(analyzer.supports(gz_year, TransitAnalyzer.Level.XIAOYUN))
        self.assertTrue(analyzer.supports(gz_year, TransitAnalyzer.Level.LIUNIAN))
        self.assertTrue(analyzer.supports(gz_year, TransitAnalyzer.Level.XIAOYUN_LIUNIAN))

        # The last Xiaoyun year may also be the first Dayun year - this is the only expected overlap.
        if analyzer.supports(gz_year, TransitAnalyzer.Level.DAYUN):
          self.assertEqual(gz_year, first_dayun_gz_year)
        else:
          self.assertLess(gz_year, first_dayun_gz_year)

      for start_gz_year, _ in itertools.islice(chart.dayun, 10): # Expect the first 10 dayuns to be supported anyways...
        for gz_year in range(start_gz_year, start_gz_year + 10):
          self.assertTrue(analyzer.supports(gz_year, TransitAnalyzer.Level.DAYUN))
          self.assertTrue(analyzer.supports(gz_year, TransitAnalyzer.Level.LIUNIAN))
          self.assertTrue(analyzer.supports(gz_year, TransitAnalyzer.Level.DAYUN_LIUNIAN))

  @pytest.mark.slow
  def test_tiangan_negative(self) -> None:
    for _ in range(16):
      chart: BaziChart = BaziChart.random()
      analyzer: TransitAnalyzer = TransitAnalyzer(chart)

      self.assertRaises(AssertionError, analyzer.tiangan, '1999', TransitAnalyzer.Level.XIAOYUN)
      self.assertRaises(AssertionError, analyzer.tiangan, 1999, 'XIAOYUN')
      self.assertRaises(AssertionError, analyzer.tiangan, 1999, 0x1 | 0x4)

      for gz_year in range(chart.bazi.ganzhi_date.year - 10, chart.bazi.ganzhi_date.year):
        for level in TransitAnalyzer.Level:
          self.assertRaises(ValueError, analyzer.tiangan, gz_year, level)

      # Iteration starting from the first liuniqn (which is the birth ganzhi year).
      for gz_year, _ in itertools.islice(chart.liunian, 300):
        for level in TransitAnalyzer.Level:
          if analyzer.supports(gz_year, level):
            self.assertIsNotNone(analyzer.tiangan(gz_year, level))
          else:
            self.assertRaises(ValueError, analyzer.tiangan, gz_year, level)

  @pytest.mark.slow
  def test_tiangan_correctness(self) -> None:
    for _ in range(32):
      chart: BaziChart = BaziChart.random()
      analyzer: TransitAnalyzer = TransitAnalyzer(chart)

      xiaoyun_tiangans: dict[int, Tiangan] = {
        chart.bazi.ganzhi_date.year + age - 1 : xy.tiangan
        for age, xy in chart.xiaoyun
      }

      dayun_start_gz_year: int = to_ganzhi(chart.dayun_start_moment).year
      dayun_tiangans: list[Tiangan] = list(dy.ganzhi.tiangan for dy in itertools.islice(chart.dayun, 50))

      for gz_year, _ in itertools.islice(chart.liunian, 200):
        for level in TransitAnalyzer.Level:
          if not analyzer.supports(gz_year, level):
            continue
          
          result: TianganRelationDiscovery = analyzer.tiangan(gz_year, level)
          self.assertIsNotNone(result)

          transit_tiangans: list[Tiangan] = []
          if level.value & TransitAnalyzer.Level.XIAOYUN.value:
            transit_tiangans.append(xiaoyun_tiangans[gz_year])
          if level.value & TransitAnalyzer.Level.DAYUN.value:
            dayun_index: int = (gz_year - dayun_start_gz_year) // 10
            transit_tiangans.append(dayun_tiangans[dayun_index])
          if level.value & TransitAnalyzer.Level.LIUNIAN.value:
            transit_tiangans.append(BaziUtils.ganzhi_of_year(gz_year).tiangan)

          expected: TianganRelationDiscovery = TianganUtils.discover_mutually(chart.bazi.four_tiangans, transit_tiangans)
          self.assertEqual(expected, result)
