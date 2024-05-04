# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transit_chart.py

import unittest

from src.Bazi import BaziChart, BaziGender
from src.TransitChart import TransitChart, 流年大运


class TestTransitChart(unittest.TestCase):
  def test_basic(self) -> None:
    self.assertIs(TransitChart, 流年大运)

    for _ in range(10):
      bazi_chart: BaziChart = BaziChart.random()
      transits: TransitChart = TransitChart(bazi_chart)
      none_transits: TransitChart = TransitChart(bazi_chart, override_gender=None)
      self.assertEqual(bazi_chart.json, transits.bazi_chart.json)
      self.assertEqual(bazi_chart.json, none_transits.bazi_chart.json)
      self.assertEqual(bazi_chart.bazi.gender, transits.gender, 'Transit order defaults to the bazi chart gender.')
      self.assertEqual(bazi_chart.bazi.gender, none_transits.gender, 'Transit order defaults to the bazi chart gender.')

    for _ in range(10):
      bazi_chart: BaziChart = BaziChart.random()
      yang_transits: TransitChart = TransitChart(bazi_chart, override_gender=BaziGender.YANG)
      yin_transits: TransitChart = TransitChart(bazi_chart, override_gender=BaziGender.YIN)
      self.assertEqual(yang_transits.gender, BaziGender.YANG)
      self.assertEqual(yin_transits.gender, BaziGender.YIN)

  def test_basic_negative(self) -> None:
    self.assertRaises(AssertionError, lambda: TransitChart(BaziChart.random(), override_gender='BaziGender.YANG'))  # type: ignore
    self.assertRaises(AssertionError, lambda: TransitChart(BaziChart.random(), override_gender='YANG'))  # type: ignore
    self.assertRaises(AssertionError, lambda: TransitChart(BaziChart.random(), override_gender='Yin'))  # type: ignore
    self.assertRaises(AssertionError, lambda: TransitChart(BaziChart.random(), override_gender='女'))  # type: ignore
    self.assertRaises(AssertionError, lambda: TransitChart(BaziChart.random(), override_gender=0))  # type: ignore
    self.assertRaises(AssertionError, lambda: TransitChart(BaziChart.random(), override_gender=0.0))  # type: ignore

    with self.assertRaises(AttributeError):
      TransitChart(BaziChart.random()).bazi_chart = BaziChart.random()  # type: ignore
    with self.assertRaises(AttributeError):
      TransitChart(BaziChart.random()).gender = BaziGender.YANG  # type: ignore
