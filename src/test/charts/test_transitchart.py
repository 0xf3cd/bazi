# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transitchart.py

import unittest
from datetime import date

from src.Bazi import Bazi
from src.Charts import BaziChart, TransitChart
from src.Charts.TransitChart import 流年大运


class TestTransitChart(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertIs(TransitChart, 流年大运)

    for _ in range(10):
      random_bazi: Bazi = Bazi.random()
      transits: TransitChart = TransitChart(random_bazi)

      self.assertEqual(transits.bazi.gender, random_bazi.gender)
      self.assertEqual(transits.bazi.precision, random_bazi.precision)
      self.assertEqual(transits.bazi.solar_datetime, random_bazi.solar_datetime)
      self.assertTupleEqual(transits.bazi.pillars, random_bazi.pillars)

  def test_basic_negative(self) -> None:
    self.assertRaises(AssertionError, lambda: TransitChart(BaziChart(Bazi.random())))  # type: ignore
    self.assertRaises(AssertionError, lambda: TransitChart(date(2024, 1, 1)))  # type: ignore

    with self.assertRaises(AttributeError):
      TransitChart(Bazi.random()).bazi = Bazi.random()  # type: ignore
