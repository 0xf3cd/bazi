# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_analyzer.py

import pytest
import unittest
import itertools

from src.Common import TianganRelationDiscovery
from src.Utils import TianganUtils

from src.Bazi import Bazi
from src.BaziChart import BaziChart
from src.Analyzer import AtBirthAnalyzer, TransitAnalyzer


class TestAtBirthAnalyzer(unittest.TestCase):
  @pytest.mark.slow
  def test_tiangan(self) -> None:
    for _ in range(128):
      bazi: Bazi = Bazi.random()
      chart: BaziChart = BaziChart(bazi)
      analyzer: AtBirthAnalyzer = AtBirthAnalyzer(chart)

      with self.subTest('new discovery dict'):
        self.assertIsNot(analyzer.tiangan, analyzer.tiangan)
      with self.subTest('equality'):
        self.assertEqual(analyzer.tiangan, analyzer.tiangan)

      expected: TianganRelationDiscovery = TianganUtils.discover(bazi.four_tiangans)
      self.assertEqual(expected, analyzer.tiangan)


class TestTransitAnalyzer(unittest.TestCase):
  @pytest.mark.slow
  def test_supports(self) -> None:
    for _ in range(128):
      bazi: Bazi = Bazi.random()
      chart: BaziChart = BaziChart(bazi)
      analyzer: TransitAnalyzer = TransitAnalyzer(chart)

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

  # TODO: more tests...
