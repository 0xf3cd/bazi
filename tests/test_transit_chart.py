# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transit_chart.py

import unittest

from datetime import datetime

from src.bazi import Bazi, BaziGender, BaziPrecision
from src.bazi_chart import BaziChart
from src.defines import Dizhi
from src.transits import TransitMoment, TransitOptions, TransitDatabase
from src.transit_chart import TransitChart, 流年大运


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
        self.assertEqual(transits.support(TransitMoment(gz_year), option), db.support(TransitMoment(gz_year), option))
        if transits.support(TransitMoment(gz_year), option):
          self.assertEqual(transits.ganzhis(TransitMoment(gz_year), option), db.ganzhis(TransitMoment(gz_year), option))

  def test_delegation_negative(self) -> None:
    bazi: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
    transits: TransitChart = TransitChart(BaziChart(bazi))

    self.assertRaises(AssertionError, lambda: transits.support('1999', TransitOptions.XIAOYUN)) # type: ignore
    self.assertRaises(AssertionError, lambda: transits.support(1999, TransitOptions.XIAOYUN)) # type: ignore # int no longer accepted; `TransitMoment` required.
    self.assertRaises(AssertionError, lambda: transits.ganzhis(TransitMoment(1999), 'XIAOYUN')) # type: ignore
    # Month/day-granularity moments are rejected until #48 / #48 落地前，月/日粒度的 moment 显式拒绝。
    self.assertRaises(NotImplementedError, lambda: transits.support(TransitMoment(2000, gz_month=Dizhi.寅), TransitOptions.LIUNIAN))

    first_dayun_gz_year: int = next(transits.bazi_chart.dayun).ganzhi_year
    self.assertFalse(transits.support(TransitMoment(first_dayun_gz_year - 1), TransitOptions.DAYUN))
    self.assertRaises(ValueError, lambda: transits.ganzhis(TransitMoment(first_dayun_gz_year - 1), TransitOptions.DAYUN))
