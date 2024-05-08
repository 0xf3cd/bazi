# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_transitchart.py

import unittest
from datetime import date, datetime

from src.Defines import Ganzhi, Yinyang
from src.Bazi import Bazi, BaziGender, BaziPrecision
from src.Utils import BaziUtils
from src.Charts import BaziChart, TransitChart
from src.Charts.TransitChart import 流年大运
from src.Charts.ChartProtocol import ChartProtocol


class TestTransitChart(unittest.TestCase):
  def test_protocol_conformance(self) -> None:
    self.assertIsInstance(TransitChart(Bazi.random()), ChartProtocol)
    self.assertIsInstance(TransitChart, ChartProtocol)

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

  def test_dayun_sexagenary_cycle(self) -> None:
    for _ in range(10):
      random_bazi: Bazi = Bazi.random()
      transits: TransitChart = TransitChart(random_bazi)

      dayun_gen = transits.dayun
      first_60_dayuns: list[Ganzhi] = [next(dayun_gen) for _ in range(60)]
      next_60_dayuns: list[Ganzhi] = [next(dayun_gen) for _ in range(60)]

      self.assertListEqual(first_60_dayuns, next_60_dayuns)
      self.assertSetEqual(set(first_60_dayuns), set(Ganzhi.list_sexagenary_cycle()))

  def test_dayun_order(self) -> None:
    for _ in range(10):
      random_bazi: Bazi = Bazi.random()
      
      month_gz: Ganzhi = random_bazi.month_pillar
      year_dz_yinyaang: Yinyang = BaziUtils.dizhi_traits(random_bazi.year_pillar.dizhi).yinyang

      cycle: list[Ganzhi] = Ganzhi.list_sexagenary_cycle()
      expected_first_dayun: Ganzhi = cycle[(cycle.index(month_gz) + 1) % 60]
      if (random_bazi.gender is BaziGender.男) and (year_dz_yinyaang is Yinyang.阴):
        expected_first_dayun = cycle[(cycle.index(month_gz) - 1) % 60]
      elif (random_bazi.gender is BaziGender.女) and (year_dz_yinyaang is Yinyang.阳):
        expected_first_dayun = cycle[(cycle.index(month_gz) - 1) % 60]
      
      transits: TransitChart = TransitChart(random_bazi)
      first_dayun = next(transits.dayun)

      self.assertEqual(first_dayun, expected_first_dayun)

  def test_dayun_correctness(self) -> None:
    bazi1: Bazi = Bazi.create(datetime(2000, 2, 4, 22, 1), BaziGender.MALE, BaziPrecision.DAY)
    transit_chart1: TransitChart = TransitChart(bazi1)
    bazi1_dayun_gen = transit_chart1.dayun
    self.assertEqual(next(bazi1_dayun_gen), Ganzhi.from_str('己卯'))
    self.assertEqual(next(bazi1_dayun_gen), Ganzhi.from_str('庚辰'))
    self.assertEqual(next(bazi1_dayun_gen), Ganzhi.from_str('辛巳'))

    bazi2: Bazi = Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.MALE, BaziPrecision.DAY)
    transit_chart2: TransitChart = TransitChart(bazi2)
    bazi2_dayun_gen = transit_chart2.dayun
    self.assertEqual(next(bazi2_dayun_gen), Ganzhi.from_str('戊辰'))
    self.assertEqual(next(bazi2_dayun_gen), Ganzhi.from_str('己巳'))
    self.assertEqual(next(bazi2_dayun_gen), Ganzhi.from_str('庚午'))

    bazi3: Bazi = Bazi.create(datetime(1984, 4, 2, 4, 2), BaziGender.FEMALE, BaziPrecision.DAY)
    transit_chart3: TransitChart = TransitChart(bazi3)
    bazi3_dayun_gen = transit_chart3.dayun
    self.assertEqual(next(bazi3_dayun_gen), Ganzhi.from_str('丙寅'))
    self.assertEqual(next(bazi3_dayun_gen), Ganzhi.from_str('乙丑'))
    self.assertEqual(next(bazi3_dayun_gen), Ganzhi.from_str('甲子'))
