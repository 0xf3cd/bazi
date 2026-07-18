# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transit_chart.py

import unittest

from datetime import datetime

from src.Bazi import Bazi, BaziGender, BaziPrecision
from src.BaziChart import BaziChart
from src.Transits import TransitOptions, TransitDatabase
from src.TransitChart import TransitChart, 流年大运


class TestTransitChart(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertIs(TransitChart, 流年大运)

    for _ in range(4):
      bazi_chart: BaziChart = BaziChart.random()
      transits: TransitChart = TransitChart(bazi_chart)
      self.assertEqual(bazi_chart.json, transits.bazi_chart.json)

  def test_basic_negative(self) -> None:
    self.assertRaises(AssertionError, lambda: TransitChart(BaziChart.random().bazi)) # type: ignore
    self.assertRaises(AssertionError, lambda: TransitChart(datetime(2024, 1, 1))) # type: ignore

    with self.assertRaises(AttributeError):
      TransitChart(BaziChart.random()).bazi_chart = BaziChart.random() # type: ignore

  def test_delegation(self) -> None:
    bazi: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
    transits: TransitChart = TransitChart(BaziChart(bazi))
    db: TransitDatabase = TransitDatabase(transits.bazi_chart)

    first_dayun_gz_year: int = next(transits.bazi_chart.dayun).ganzhi_year

    for gz_year in (first_dayun_gz_year, first_dayun_gz_year + 7, first_dayun_gz_year + 25):
      for option in TransitOptions:
        self.assertEqual(transits.support(gz_year, option), db.support(gz_year, option))
        if transits.support(gz_year, option):
          self.assertEqual(transits.ganzhis(gz_year, option), db.ganzhis(gz_year, option))

  def test_delegation_negative(self) -> None:
    bazi: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
    transits: TransitChart = TransitChart(BaziChart(bazi))

    self.assertRaises(AssertionError, lambda: transits.support('1999', TransitOptions.XIAOYUN)) # type: ignore
    self.assertRaises(AssertionError, lambda: transits.ganzhis(1999, 'XIAOYUN')) # type: ignore

    first_dayun_gz_year: int = next(transits.bazi_chart.dayun).ganzhi_year
    self.assertFalse(transits.support(first_dayun_gz_year - 1, TransitOptions.DAYUN))
    self.assertRaises(ValueError, lambda: transits.ganzhis(first_dayun_gz_year - 1, TransitOptions.DAYUN))
