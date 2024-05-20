# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_ganzhi_discoverer.py

import pytest
import unittest

import random
import itertools
from datetime import datetime

from src.Common import PillarData
from src.Defines import Tiangan, Dizhi, Ganzhi, TianganRelation, DizhiRelation
from src.Utils import TianganUtils, DizhiUtils, BaziUtils
from src.Calendar.HkoDataCalendarUtils import to_ganzhi

from src.Bazi import Bazi, BaziGender, BaziPrecision
from src.BaziChart import BaziChart
from src.Discoverer.GanzhiDiscoverer import GanzhiDiscoverer, TransitOptions


class TestGanzhiDiscoverer(unittest.TestCase):
  def test_support(self) -> None:
    for _ in range(5):
      chart: BaziChart = BaziChart.random()
      discoverer: GanzhiDiscoverer = GanzhiDiscoverer(chart)

      self.assertRaises(AssertionError, discoverer.support, '1999', TransitOptions.XIAOYUN)
      self.assertRaises(AssertionError, discoverer.support, 1999, 'XIAOYUN')
      self.assertRaises(AssertionError, discoverer.support, 1999, 0x1 | 0x4)

      with self.subTest('Test ganzhi years before the birth year. Expect not to support.'):
        for gz_year in range(chart.bazi.ganzhi_date.year - 10, chart.bazi.ganzhi_date.year):
          for option in TransitOptions:
            self.assertFalse(discoverer.support(gz_year, option))

      with self.subTest('Test Xiaoyun / 小运.'):
        first_dayun_gz_year: int = next(chart.dayun).ganzhi_year
        for gz_year in range(chart.bazi.ganzhi_date.year, chart.bazi.ganzhi_date.year + len(chart.xiaoyun)):
          self.assertTrue(discoverer.support(gz_year, TransitOptions.XIAOYUN))
          self.assertTrue(discoverer.support(gz_year, TransitOptions.LIUNIAN))
          self.assertTrue(discoverer.support(gz_year, TransitOptions.XIAOYUN_LIUNIAN))

          # The last Xiaoyun year may also be the first Dayun year - this is the only expected overlap.
          if discoverer.support(gz_year, TransitOptions.DAYUN):
            self.assertEqual(gz_year, first_dayun_gz_year)
          else:
            self.assertLess(gz_year, first_dayun_gz_year)

      with self.subTest('Test Dayun / 大运.'):
        for start_gz_year, _ in itertools.islice(chart.dayun, 10): # Expect the first 10 dayuns to be supported anyways...
          for gz_year in range(start_gz_year, start_gz_year + 10):
            self.assertTrue(discoverer.support(gz_year, TransitOptions.DAYUN))
            self.assertTrue(discoverer.support(gz_year, TransitOptions.LIUNIAN))
            self.assertTrue(discoverer.support(gz_year, TransitOptions.DAYUN_LIUNIAN))

  def test_at_birth(self) -> None:
    for _ in range(5):
      chart: BaziChart = BaziChart.random()
      discoverer: GanzhiDiscoverer = GanzhiDiscoverer(chart)

      at_birth = discoverer.at_birth
      self.assertEqual(discoverer.at_birth.tiangan, TianganUtils.discover(chart.bazi.four_tiangans), 'Correctness')
      self.assertEqual(discoverer.at_birth.dizhi, DizhiUtils.discover(chart.bazi.four_dizhis), 'Correctness')
      self.assertEqual(discoverer.at_birth.tiangan, at_birth.tiangan, 'Returning identical objects.')
      self.assertEqual(discoverer.at_birth.dizhi, at_birth.dizhi, 'Returning identical objects.')

  @pytest.mark.slow
  def test_negative(self) -> None:
    for _ in range(16):
      chart: BaziChart = BaziChart.random()
      discoverer: GanzhiDiscoverer = GanzhiDiscoverer(chart)

      self.assertRaises(AssertionError, discoverer.transits, '1999', TransitOptions.XIAOYUN)
      self.assertRaises(AssertionError, discoverer.transits, 1999, 'XIAOYUN')
      self.assertRaises(AssertionError, discoverer.transits, 1999, 0x1 | 0x4)

      self.assertRaises(AssertionError, discoverer.mutual, '1999', TransitOptions.XIAOYUN)
      self.assertRaises(AssertionError, discoverer.mutual, 1999, 'XIAOYUN')
      self.assertRaises(AssertionError, discoverer.mutual, 1999, 0x1 | 0x4)

      for gz_year in range(chart.bazi.ganzhi_date.year - 10, chart.bazi.ganzhi_date.year):
        for option in TransitOptions:
          self.assertRaises(ValueError, discoverer.transits, gz_year, option)
          self.assertRaises(ValueError, discoverer.mutual, gz_year, option)

      # Iteration starting from the first liunian (which is the birth ganzhi year).
      random_selected = random.sample(list(itertools.islice(chart.liunian, 300)), 100)
      for gz_year, _ in random_selected:
        for option in TransitOptions:
          if discoverer.support(gz_year, option):
            self.assertIsNotNone(discoverer.transits(gz_year, option))
            self.assertIsNotNone(discoverer.mutual(gz_year, option))
          else:
            self.assertRaises(ValueError, discoverer.transits, gz_year, option)
            self.assertRaises(ValueError, discoverer.mutual, gz_year, option)

  @pytest.mark.slow
  def test_misc(self) -> None:
    for _ in range(8):
      chart: BaziChart = BaziChart.random()
      discoverer: GanzhiDiscoverer = GanzhiDiscoverer(chart)

      for dayun_start_gz_year, _ in itertools.islice(chart.dayun, 10):
        for option in TransitOptions:
          if not discoverer.support(dayun_start_gz_year, option):
            continue

          with self.subTest('identical returns'):
            self.assertIsNot(discoverer.transits(dayun_start_gz_year, option),
                             discoverer.transits(dayun_start_gz_year, option))
            self.assertIsNot(discoverer.mutual(dayun_start_gz_year, option),
                             discoverer.mutual(dayun_start_gz_year, option))
            
          with self.subTest('equality'):
            self.assertEqual(discoverer.transits(dayun_start_gz_year, option),
                             discoverer.transits(dayun_start_gz_year, option))
            self.assertEqual(discoverer.mutual(dayun_start_gz_year, option),
                             discoverer.mutual(dayun_start_gz_year, option))

          with self.subTest('another discoverer'):
            discoverer2: GanzhiDiscoverer = GanzhiDiscoverer(chart)
            self.assertEqual(discoverer.transits(dayun_start_gz_year, option),
                             discoverer2.transits(dayun_start_gz_year, option))
            self.assertEqual(discoverer.mutual(dayun_start_gz_year, option),
                             discoverer2.mutual(dayun_start_gz_year, option))

  @pytest.mark.slow
  def test_correctness(self) -> None:
    for _ in range(16):
      chart: BaziChart = BaziChart.random()
      discoverer: GanzhiDiscoverer = GanzhiDiscoverer(chart)

      xiaoyun_ganzhis: dict[int, Ganzhi] = {
        chart.bazi.ganzhi_date.year + age - 1 : xy
        for age, xy in chart.xiaoyun
      }

      dayun_start_gz_year: int = to_ganzhi(chart.dayun_start_moment).year
      dayun_ganzhis: list[Ganzhi] = list(dy.ganzhi for dy in itertools.islice(chart.dayun, 50))

      # Randomly select 20 ganzhi years to test...
      random_liunians = random.sample(list(itertools.islice(chart.liunian, 200)), 20)
      random.shuffle(random_liunians)

      for gz_year, _ in random_liunians:
        for option in TransitOptions:
          if not discoverer.support(gz_year, option):
            continue

          transit_ganzhis: list[Ganzhi] = []
          if option.value & TransitOptions.XIAOYUN.value:
            transit_ganzhis.append(xiaoyun_ganzhis[gz_year])
          if option.value & TransitOptions.DAYUN.value:
            dayun_index: int = (gz_year - dayun_start_gz_year) // 10
            transit_ganzhis.append(dayun_ganzhis[dayun_index])
          if option.value & TransitOptions.LIUNIAN.value:
            transit_ganzhis.append(BaziUtils.ganzhi_of_year(gz_year))

          transit_tiangans: list[Tiangan] = [gz.tiangan for gz in transit_ganzhis]
          transit_dizhis: list[Dizhi] = [gz.dizhi for gz in transit_ganzhis]

          at_birth = discoverer.at_birth
          self.assertEqual(at_birth, 
                           PillarData(TianganUtils.discover(chart.bazi.four_tiangans), DizhiUtils.discover(chart.bazi.four_dizhis)), 
                           'At-birth / 原局')
          
          transits = discoverer.transits(gz_year, option)
          self.assertEqual(transits, 
                           PillarData(TianganUtils.discover(transit_tiangans), DizhiUtils.discover(transit_dizhis)),
                           'Transits / 运（即大运、流年、小运）')
          
          mutual = discoverer.mutual(gz_year, option)
          self.assertEqual(mutual, 
                           PillarData(TianganUtils.discover_mutual(chart.bazi.four_tiangans, transit_tiangans), DizhiUtils.discover_mutual(chart.bazi.four_dizhis, transit_dizhis)), 
                           'Mutual / 原局和运之间的互相作用力/关系')

          expected_tiangan_combined: TianganUtils.TianganRelationDiscovery = TianganUtils.discover(list(chart.bazi.four_tiangans) + transit_tiangans)
          for tg_rel in TianganRelation:
            self.assertSetEqual(set(expected_tiangan_combined[tg_rel]),
                                set(at_birth.tiangan[tg_rel]) | set(transits.tiangan[tg_rel]) | set(mutual.tiangan[tg_rel]))
                  
          expected_dizhi_combined: DizhiUtils.DizhiRelationDiscovery = DizhiUtils.discover(list(chart.bazi.four_dizhis) + transit_dizhis)
          for dz_rel in DizhiRelation:
            self.assertSetEqual(set(expected_dizhi_combined[dz_rel]), 
                                set(at_birth.dizhi[dz_rel]) | set(transits.dizhi[dz_rel]) | set(mutual.dizhi[dz_rel]))


@pytest.mark.integration
class TestGanzhiDiscovererIntegration(unittest.TestCase):
  '''
  Integration tests are mainly aiming to test the correctness of `GanzhiDiscoverer`.
  The Bazi cases are collected from "测测" app / "问真八字" web site.

  In this project, `search`, `discover`, and `discover_mutual` methods in `TianganUtils` and `DizhiUtils` will
  return all possible combos.
  However, for 测测 and 问真八字, they only consider part of the combos. For example, 
  they don't consider SHENG / 生 relation.

  So in the following tests, we only test that the relation combos that 测测/问真八字 find 
  are in `GanzhiDiscoverer`'s returns. 
  There can be some combos in `GanzhiDiscoverer`'s returns but not in 测测/问真八字's results.
  '''

  @staticmethod
  def __check_tiangan(expected: dict[TianganRelation, list[TianganUtils.TianganCombo]], actual: TianganUtils.TianganRelationDiscovery) -> bool:
    for rel, expected_combos in expected.items():
      if rel not in actual:
        return False
      for combo in expected_combos:
        if combo not in actual[rel]:
          return False
    return True

  @staticmethod
  def __check_dizhi(expected: dict[DizhiRelation, list[DizhiUtils.DizhiCombo]], actual: DizhiUtils.DizhiRelationDiscovery) -> bool:
    for rel, expected_combos in expected.items():
      if rel not in actual:
        return False
      for combo in expected_combos:
        if combo not in actual[rel]:
          return False
    return True

  def test_case1(self) -> None:
    '''From 问真八字 https://pcbz.iwzwh.com/#/paipan/index'''
    bazi: Bazi = Bazi(
      birth_time=datetime(1984, 4, 1, 11, 8),
      gender=BaziGender.MALE,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)
    discoverer: GanzhiDiscoverer = GanzhiDiscoverer(chart)

    with self.subTest('pillar correctness'):
      self.assertEqual(bazi.year_pillar, Ganzhi.from_str('甲子'))
      self.assertEqual(bazi.month_pillar, Ganzhi.from_str('丁卯'))
      self.assertEqual(bazi.day_pillar, Ganzhi.from_str('乙丑'))
      self.assertEqual(bazi.hour_pillar, Ganzhi.from_str('壬午'))
      self.assertEqual(chart.xiaoyun[0].ganzhi, Ganzhi.from_str('癸未'))
      self.assertEqual(next(chart.dayun).ganzhi, Ganzhi.from_str('戊辰'))
      self.assertEqual(next(chart.dayun).ganzhi_year, 1985)

    with self.subTest('at birth'):
      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.丁, Tiangan.壬})],
      }, discoverer.at_birth.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.子, Dizhi.丑})],
        DizhiRelation.刑 : [frozenset({Dizhi.子, Dizhi.卯})],
        DizhiRelation.冲 : [frozenset({Dizhi.子, Dizhi.午})],
        DizhiRelation.破 : [frozenset({Dizhi.午, Dizhi.卯})],
        DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
      }, discoverer.at_birth.dizhi))

    with self.subTest('1993 dayun and liunian'):
      dayun_liunian = discoverer.transits(1993, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.戊, Tiangan.癸})],
      }, dayun_liunian.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.辰, Dizhi.酉})],
      }, dayun_liunian.dizhi))

    with self.subTest('2024 dayun and liunian - mutual'):
      mutual = discoverer.mutual(2024, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.克 : [frozenset({Tiangan.丁, Tiangan.辛}), frozenset({Tiangan.辛, Tiangan.乙})],
      }, mutual.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.午, Dizhi.未})],
        DizhiRelation.半合 : [frozenset({Dizhi.子, Dizhi.辰}), frozenset({Dizhi.卯, Dizhi.未})],
        DizhiRelation.刑 : [frozenset({Dizhi.未, Dizhi.丑})], # LOOSE mode is used for XING relation.
        DizhiRelation.冲 : [frozenset({Dizhi.未, Dizhi.丑})],
        DizhiRelation.破 : [frozenset({Dizhi.丑, Dizhi.辰})],
        DizhiRelation.害 : [frozenset({Dizhi.未, Dizhi.子}), frozenset({Dizhi.辰, Dizhi.卯})],
      }, mutual.dizhi))

    with self.subTest('2051 dayun and liunian'):
      dayun_liunian = discoverer.transits(2051, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.破 : [frozenset({Dizhi.戌, Dizhi.未})],
        DizhiRelation.刑 : [frozenset({Dizhi.未, Dizhi.戌})],
      }, dayun_liunian.dizhi))

    with self.subTest('2051 dayun and liunian - mutual'):
      mutual = discoverer.mutual(2051, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.克 : [frozenset({Tiangan.丁, Tiangan.辛}), frozenset({Tiangan.辛, Tiangan.乙})],
      }, mutual.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.卯, Dizhi.戌}), frozenset({Dizhi.午, Dizhi.未})],
        DizhiRelation.半合 : [frozenset({Dizhi.卯, Dizhi.未}), frozenset({Dizhi.午, Dizhi.戌})],
        DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未, Dizhi.戌}),
                            frozenset({Dizhi.未, Dizhi.丑}),
                            frozenset({Dizhi.戌, Dizhi.丑}),], # LOOSE mode is used for XING relation.
        DizhiRelation.冲 : [frozenset({Dizhi.丑, Dizhi.未})],
        DizhiRelation.害 : [frozenset({Dizhi.未, Dizhi.子})],
      }, mutual.dizhi))

  def test_case2(self) -> None:
    '''From 测测 and 问真八字'''
    bazi: Bazi = Bazi(
      birth_time=datetime(2024, 5, 19, 18, 59),
      gender=BaziGender.FEMALE,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)
    discoverer: GanzhiDiscoverer = GanzhiDiscoverer(chart)

    with self.subTest('pillar correctness'):
      self.assertEqual(bazi.year_pillar, Ganzhi.from_str('甲辰'))
      self.assertEqual(bazi.month_pillar, Ganzhi.from_str('己巳'))
      self.assertEqual(bazi.day_pillar, Ganzhi.from_str('癸未'))
      self.assertEqual(bazi.hour_pillar, Ganzhi.from_str('辛酉'))
      self.assertEqual(chart.xiaoyun[0].ganzhi, Ganzhi.from_str('庚申'))
      self.assertEqual(next(chart.dayun).ganzhi, Ganzhi.from_str('戊辰'))
      self.assertEqual(next(chart.dayun).ganzhi_year, 2029)

    with self.subTest('at birth'):
      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.甲, Tiangan.己})],
        TianganRelation.克 : [frozenset({Tiangan.己, Tiangan.癸})],
      }, discoverer.at_birth.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.辰, Dizhi.酉})],
        DizhiRelation.半合 : [frozenset({Dizhi.巳, Dizhi.酉})],
      }, discoverer.at_birth.dizhi))

    with self.subTest('2024 xiaoyun and liunian - mutual'): 
      # 测测's Xiaoyun result is kinda buggy. So use 问真八字's Xiaoyun result here.
      mutual = discoverer.mutual(2024, TransitOptions.XIAOYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.甲, Tiangan.己})],
        TianganRelation.克 : [frozenset({Tiangan.庚, Tiangan.甲})],
      }, mutual.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.辰, Dizhi.酉}), frozenset({Dizhi.巳, Dizhi.申})],
        DizhiRelation.刑 : [frozenset({Dizhi.辰}), frozenset({Dizhi.巳, Dizhi.申})], # LOOSE mode is used.
        DizhiRelation.破 : [frozenset({Dizhi.巳, Dizhi.申})],
      }, mutual.dizhi))

    with self.subTest('2052 dayun and liunian - transits'):
      transits = discoverer.transits(2052, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.冲 : [frozenset({Tiangan.丙, Tiangan.壬})],
      }, transits.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.冲 : [frozenset({Dizhi.寅, Dizhi.申})],
        DizhiRelation.刑 : [frozenset({Dizhi.寅, Dizhi.申})],
      }, transits.dizhi))

    with self.subTest('2052 dayun and liunian - mutual'):
      mutual = discoverer.mutual(2052, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.丙, Tiangan.辛})],
      }, mutual.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.巳, Dizhi.申})],
        DizhiRelation.破 : [frozenset({Dizhi.巳, Dizhi.申})],
        DizhiRelation.刑 : [frozenset({Dizhi.寅, Dizhi.巳, Dizhi.申}),
                           frozenset({Dizhi.寅, Dizhi.巳}),
                           frozenset({Dizhi.巳, Dizhi.申}),],
      }, mutual.dizhi))

    with self.subTest('2062 dayun and liunian - transits'):
      transits = discoverer.transits(2062, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
      }, transits.dizhi))

    with self.subTest('2062 dayun and liunian - mutual'):
      mutual = discoverer.mutual(2062, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.冲 : [frozenset({Tiangan.乙, Tiangan.辛})],
        TianganRelation.克 : [frozenset({Tiangan.乙, Tiangan.己})],
      }, mutual.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.午, Dizhi.未})],
        DizhiRelation.三合 : [frozenset({Dizhi.巳, Dizhi.酉, Dizhi.丑})],
        DizhiRelation.三会 : [frozenset({Dizhi.巳, Dizhi.午, Dizhi.未})],
        DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未})], # LOOSE mode is used here...
        DizhiRelation.冲 : [frozenset({Dizhi.丑, Dizhi.未})],
        DizhiRelation.破 : [frozenset({Dizhi.丑, Dizhi.辰})],
      }, mutual.dizhi))
