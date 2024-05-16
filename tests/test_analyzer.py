# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_analyzer.py

import pytest
import unittest

from src.Common import TianganRelationDiscovery
from src.Utils import TianganUtils

from src.Bazi import Bazi
from src.BaziChart import BaziChart
from src.Analyzer import AtBirthRelation, TransitRelation


class TestAtBirthRelation(unittest.TestCase):
  @pytest.mark.slow
  def test_tiangan(self) -> None:
    for _ in range(128):
      bazi: Bazi = Bazi.random()
      chart: BaziChart = BaziChart(bazi)
      relation: AtBirthRelation = AtBirthRelation(chart)

      with self.subTest('new discovery dict'):
        self.assertIsNot(relation.tiangan, relation.tiangan)
      with self.subTest('equality'):
        self.assertEqual(relation.tiangan, relation.tiangan)

      expected: TianganRelationDiscovery = TianganUtils.discover(bazi.four_tiangans)
      self.assertEqual(expected, relation.tiangan)


class TestTransitRelation(unittest.TestCase):
  def test_supports(self) -> None:
    for _ in range(128):
      bazi: Bazi = Bazi.random()
      chart: BaziChart = BaziChart(bazi)
      relation: TransitRelation = TransitRelation(chart)

      relation.supports(1, TransitRelation.Level.DAYUN_LIUNIAN)

  # @pytest.mark.slow
  # def test_tiangan_supported_years(self) -> None:
  #   for _ in range(128):
  #     bazi: Bazi = Bazi.random()
  #     chart: BaziChart = BaziChart(bazi)
  #     relation: TransitRelation = TransitRelation(chart)
  #     supported_years: set[int] = relation.supported_ganzhi_years

  #     with self.subTest('test supported ganzhi years'):
  #       for gz_year in supported_years:
  #         for level in TransitRelation.Level:
  #           self.assertIsNotNone(relation.tiangan(gz_year, level))

  #     with self.subTest('test out of supported years'):
  #       for level in TransitRelation.Level:
  #         for year in range(max(supported_years) + 1, 10):
  #           self.assertRaises(ValueError, relation.tiangan, year, level)
  #         for year in range(min(supported_years) - 1, min(supported_years) - 10, -1):
  #           self.assertRaises(ValueError, relation.tiangan, year, level)

  # TODO: more tests...
