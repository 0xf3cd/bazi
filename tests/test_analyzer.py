# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_analyzer.py

import pytest
import unittest

import random
import itertools

from src.Defines import Tiangan, TianganRelation, Dizhi, DizhiRelation
from src.Utils import BaziUtils, TianganUtils, DizhiUtils
from src.Calendar.HkoDataCalendarUtils import to_ganzhi

from src.BaziChart import BaziChart
from src.Analyzer import RelationAnalyzer, Result


class TestRelationAnalysis(unittest.TestCase):
  def test_supports(self) -> None:
    for _ in range(5):
      chart: BaziChart = BaziChart.random()
      analyzer: RelationAnalyzer = RelationAnalyzer(chart)

      self.assertRaises(AssertionError, analyzer.supports, '1999', RelationAnalyzer.TransitOption.XIAOYUN)
      self.assertRaises(AssertionError, analyzer.supports, 1999, 'XIAOYUN')
      self.assertRaises(AssertionError, analyzer.supports, 1999, 0x1 | 0x4)

      with self.subTest('Test ganzhi years before the birth year. Expect not to support.'):
        for gz_year in range(chart.bazi.ganzhi_date.year - 10, chart.bazi.ganzhi_date.year):
          for option in RelationAnalyzer.TransitOption:
            self.assertFalse(analyzer.supports(gz_year, option))

      with self.subTest('Test Xiaoyun / 小运.'):
        first_dayun_gz_year: int = next(chart.dayun).ganzhi_year
        for gz_year in range(chart.bazi.ganzhi_date.year, chart.bazi.ganzhi_date.year + len(chart.xiaoyun)):
          self.assertTrue(analyzer.supports(gz_year, RelationAnalyzer.TransitOption.XIAOYUN))
          self.assertTrue(analyzer.supports(gz_year, RelationAnalyzer.TransitOption.LIUNIAN))
          self.assertTrue(analyzer.supports(gz_year, RelationAnalyzer.TransitOption.XIAOYUN_LIUNIAN))

          # The last Xiaoyun year may also be the first Dayun year - this is the only expected overlap.
          if analyzer.supports(gz_year, RelationAnalyzer.TransitOption.DAYUN):
            self.assertEqual(gz_year, first_dayun_gz_year)
          else:
            self.assertLess(gz_year, first_dayun_gz_year)

      with self.subTest('Test Dayun / 大运.'):
        for start_gz_year, _ in itertools.islice(chart.dayun, 10): # Expect the first 10 dayuns to be supported anyways...
          for gz_year in range(start_gz_year, start_gz_year + 10):
            self.assertTrue(analyzer.supports(gz_year, RelationAnalyzer.TransitOption.DAYUN))
            self.assertTrue(analyzer.supports(gz_year, RelationAnalyzer.TransitOption.LIUNIAN))
            self.assertTrue(analyzer.supports(gz_year, RelationAnalyzer.TransitOption.DAYUN_LIUNIAN))

  @pytest.mark.slow
  def test_tiangan_negative(self) -> None:
    for _ in range(16):
      chart: BaziChart = BaziChart.random()
      analyzer: RelationAnalyzer = RelationAnalyzer(chart)

      self.assertRaises(AssertionError, analyzer.tiangan, '1999', RelationAnalyzer.TransitOption.XIAOYUN)
      self.assertRaises(AssertionError, analyzer.tiangan, 1999, 'XIAOYUN')
      self.assertRaises(AssertionError, analyzer.tiangan, 1999, 0x1 | 0x4)

      for gz_year in range(chart.bazi.ganzhi_date.year - 10, chart.bazi.ganzhi_date.year):
        for option in RelationAnalyzer.TransitOption:
          self.assertRaises(ValueError, analyzer.tiangan, gz_year, option)

      # Iteration starting from the first liunian (which is the birth ganzhi year).
      random_selected = random.sample(list(itertools.islice(chart.liunian, 300)), 100)
      for gz_year, _ in random_selected:
        for option in RelationAnalyzer.TransitOption:
          if analyzer.supports(gz_year, option):
            self.assertIsNotNone(analyzer.tiangan(gz_year, option))
          else:
            self.assertRaises(ValueError, analyzer.tiangan, gz_year, option)

  @pytest.mark.slow
  def test_tiangan_misc(self) -> None:
    for _ in range(128):
      chart: BaziChart = BaziChart.random()
      analyzer: RelationAnalyzer = RelationAnalyzer(chart)

      for dayun_start_gz_year, _ in itertools.islice(chart.dayun, 10):
        for option in RelationAnalyzer.TransitOption:
          if not analyzer.supports(dayun_start_gz_year, option):
            continue

          r1 = analyzer.tiangan(dayun_start_gz_year, option)
          r2 = analyzer.tiangan(dayun_start_gz_year, option)
          with self.subTest('new object'):
            self.assertIsNot(r1, r2)
          with self.subTest('equality'):
            self.assertEqual(r1.at_birth, r2.at_birth)
            self.assertEqual(r1.transits, r2.transits)
            self.assertEqual(r1.mutual, r2.mutual)

  @pytest.mark.slow
  def test_tiangan_correctness(self) -> None:
    for _ in range(64):
      chart: BaziChart = BaziChart.random()
      analyzer: RelationAnalyzer = RelationAnalyzer(chart)

      xiaoyun_tiangans: dict[int, Tiangan] = {
        chart.bazi.ganzhi_date.year + age - 1 : xy.tiangan
        for age, xy in chart.xiaoyun
      }

      dayun_start_gz_year: int = to_ganzhi(chart.dayun_start_moment).year
      dayun_tiangans: list[Tiangan] = list(dy.ganzhi.tiangan for dy in itertools.islice(chart.dayun, 50))

      # Randomly select 20 ganzhi years to test...
      random_liunians = random.sample(list(itertools.islice(chart.liunian, 200)), 20)
      random.shuffle(random_liunians)

      for gz_year, _ in random_liunians:
        for option in RelationAnalyzer.TransitOption:
          if not analyzer.supports(gz_year, option):
            continue
          
          result: Result[TianganUtils.TianganRelationDiscovery] = analyzer.tiangan(gz_year, option)
          self.assertIsNotNone(result)

          transit_tiangans: list[Tiangan] = []
          if option.value & RelationAnalyzer.TransitOption.XIAOYUN.value:
            transit_tiangans.append(xiaoyun_tiangans[gz_year])
          if option.value & RelationAnalyzer.TransitOption.DAYUN.value:
            dayun_index: int = (gz_year - dayun_start_gz_year) // 10
            transit_tiangans.append(dayun_tiangans[dayun_index])
          if option.value & RelationAnalyzer.TransitOption.LIUNIAN.value:
            transit_tiangans.append(BaziUtils.ganzhi_of_year(gz_year).tiangan)

          self.assertEqual(result.at_birth, TianganUtils.discover(chart.bazi.four_tiangans), 'At-birth / 原局')
          self.assertEqual(result.transits, TianganUtils.discover(transit_tiangans), 'Transits / 运（即大运、流年、小运）')
          self.assertEqual(result.mutual, TianganUtils.discover_mutually(chart.bazi.four_tiangans, transit_tiangans), 'Mutual / 原局和运之间的互相作用力/关系')

          expected_combined: TianganUtils.TianganRelationDiscovery = TianganUtils.discover(list(chart.bazi.four_tiangans) + transit_tiangans)
          for rel in TianganRelation:
            self.assertSetEqual(set(expected_combined[rel]), 
                                set(list(result.at_birth[rel]) + list(result.transits[rel]) + list(result.mutual[rel])))

  def test_tiangan_malicious(self) -> None:
    '''This test assumes that the `tiangan` method is not cached and always returns a new object. May be an overkill though...'''
    chart: BaziChart = BaziChart.random()
    analyzer: RelationAnalyzer = RelationAnalyzer(chart)

    gz_year: int = next(chart.dayun).ganzhi_year + random.randint(0, 100)
    options: RelationAnalyzer.TransitOption = random.choice([RelationAnalyzer.TransitOption.DAYUN, 
                                                             RelationAnalyzer.TransitOption.LIUNIAN, 
                                                             RelationAnalyzer.TransitOption.DAYUN_LIUNIAN])

    r1 = analyzer.tiangan(gz_year, options)
    r2 = analyzer.tiangan(gz_year, options)

    self.assertEqual(r1.at_birth, r2.at_birth)
    self.assertEqual(r1.transits, r2.transits)
    self.assertEqual(r1.mutual, r2.mutual)

    def __random_discovery() -> TianganUtils.TianganRelationDiscovery:
      return TianganUtils.discover(random.sample(Tiangan.as_list(), random.randint(0, len(Tiangan))))
    
    while True:
      new_at_birth = __random_discovery()
      if new_at_birth != r1.at_birth:
        r1._at_birth = new_at_birth # type: ignore
        break

    while True:
      new_transits = __random_discovery()
      if new_transits != r1.transits:
        r1._transits = new_transits # type: ignore
        break

    while True:
      new_mutual = __random_discovery()
      if new_mutual != r1.mutual:
        r1._mutual = new_mutual # type: ignore
        break

    self.assertNotEqual(r1.at_birth, r2.at_birth)
    self.assertNotEqual(r1.transits, r2.transits)
    self.assertNotEqual(r1.mutual, r2.mutual)

    r3 = analyzer.tiangan(gz_year, options)
    self.assertEqual(r2.at_birth, r3.at_birth)
    self.assertEqual(r2.transits, r3.transits)
    self.assertEqual(r2.mutual, r3.mutual)

  @pytest.mark.slow
  def test_dizhi_negative(self) -> None:
    for _ in range(16):
      chart: BaziChart = BaziChart.random()
      analyzer: RelationAnalyzer = RelationAnalyzer(chart)

      self.assertRaises(AssertionError, analyzer.dizhi, '1999', RelationAnalyzer.TransitOption.XIAOYUN)
      self.assertRaises(AssertionError, analyzer.dizhi, 1999, 'XIAOYUN')
      self.assertRaises(AssertionError, analyzer.dizhi, 1999, 0x1 | 0x4)

      for gz_year in range(chart.bazi.ganzhi_date.year - 10, chart.bazi.ganzhi_date.year):
        for option in RelationAnalyzer.TransitOption:
          self.assertRaises(ValueError, analyzer.dizhi, gz_year, option)

      # Iteration starting from the first liunian (which is the birth ganzhi year).
      random_selected = random.sample(list(itertools.islice(chart.liunian, 300)), 100)
      for gz_year, _ in random_selected:
        for option in RelationAnalyzer.TransitOption:
          if analyzer.supports(gz_year, option):
            self.assertIsNotNone(analyzer.dizhi(gz_year, option))
          else:
            self.assertRaises(ValueError, analyzer.dizhi, gz_year, option)

  @pytest.mark.slow
  def test_dizhi_misc(self) -> None:
    for _ in range(64):
      chart: BaziChart = BaziChart.random()
      analyzer: RelationAnalyzer = RelationAnalyzer(chart)

      for dayun_start_gz_year, _ in itertools.islice(chart.dayun, 10):
        for option in RelationAnalyzer.TransitOption:
          if not analyzer.supports(dayun_start_gz_year, option):
            continue

          r1 = analyzer.dizhi(dayun_start_gz_year, option)
          r2 = analyzer.dizhi(dayun_start_gz_year, option)
          with self.subTest('new object'):
            self.assertIsNot(r1, r2)
          with self.subTest('equality'):
            self.assertEqual(r1.at_birth, r2.at_birth)
            self.assertEqual(r1.transits, r2.transits)
            self.assertEqual(r1.mutual, r2.mutual)

  @pytest.mark.slow
  def test_dizhi_correctness(self) -> None:
    for _ in range(32):
      chart: BaziChart = BaziChart.random()
      analyzer: RelationAnalyzer = RelationAnalyzer(chart)

      xiaoyun_dizhis: dict[int, Dizhi] = {
        chart.bazi.ganzhi_date.year + age - 1 : xy.dizhi
        for age, xy in chart.xiaoyun
      }

      dayun_start_gz_year: int = to_ganzhi(chart.dayun_start_moment).year
      dayun_dizhis: list[Dizhi] = list(dy.ganzhi.dizhi for dy in itertools.islice(chart.dayun, 50))

      # Randomly select 20 liunians to test...
      random_liunians = random.sample(list(itertools.islice(chart.liunian, 200)), 20)
      random.shuffle(random_liunians)

      for gz_year, _ in random_liunians:
        for option in RelationAnalyzer.TransitOption:
          if not analyzer.supports(gz_year, option):
            continue

          result: Result[DizhiUtils.DizhiRelationDiscovery] = analyzer.dizhi(gz_year, option)
          self.assertIsNotNone(result)

          transit_dizhis: list[Dizhi] = []
          if option.value & RelationAnalyzer.TransitOption.XIAOYUN.value:
            transit_dizhis.append(xiaoyun_dizhis[gz_year])
          if option.value & RelationAnalyzer.TransitOption.DAYUN.value:
            dayun_index: int = (gz_year - dayun_start_gz_year) // 10
            transit_dizhis.append(dayun_dizhis[dayun_index])
          if option.value & RelationAnalyzer.TransitOption.LIUNIAN.value:
            transit_dizhis.append(BaziUtils.ganzhi_of_year(gz_year).dizhi)

          self.assertEqual(result.at_birth, DizhiUtils.discover(chart.bazi.four_dizhis), 'At-birth / 原局')
          self.assertEqual(result.transits, DizhiUtils.discover(transit_dizhis), 'Transits / 运（即大运、流年、小运）')
          self.assertEqual(result.mutual, DizhiUtils.discover_mutually(chart.bazi.four_dizhis, transit_dizhis), 'Mutual / 原局和运之间的互相作用力/关系')

          expected_combined = DizhiUtils.discover(list(chart.bazi.four_dizhis) + transit_dizhis)
          for rel in DizhiRelation:
            self.assertSetEqual(set(expected_combined[rel]), 
                                set(list(result.at_birth[rel]) + list(result.transits[rel]) + list(result.mutual[rel])))

  def test_dizhi_malicious(self) -> None:
    '''This test assumes that the 'dizhi' method is not cached and always returns a new object. May be an overkill though...'''
    chart: BaziChart = BaziChart.random()
    analyzer: RelationAnalyzer = RelationAnalyzer(chart)

    gz_year: int = next(chart.dayun).ganzhi_year + random.randint(0, 100)
    options: RelationAnalyzer.TransitOption = random.choice([RelationAnalyzer.TransitOption.DAYUN, 
                                                             RelationAnalyzer.TransitOption.LIUNIAN, 
                                                             RelationAnalyzer.TransitOption.DAYUN_LIUNIAN])

    r1 = analyzer.dizhi(gz_year, options)
    r2 = analyzer.dizhi(gz_year, options)

    self.assertEqual(r1.at_birth, r2.at_birth)
    self.assertEqual(r1.transits, r2.transits)
    self.assertEqual(r1.mutual, r2.mutual)

    def __random_discovery() -> DizhiUtils.DizhiRelationDiscovery:
      return DizhiUtils.discover(random.sample(Dizhi.as_list(), random.randint(0, len(Dizhi))))
    
    while True:
      new_at_birth = __random_discovery()
      if new_at_birth != r1.at_birth:
        r1._at_birth = new_at_birth # type: ignore
        break

    while True:
      new_transits = __random_discovery()
      if new_transits != r1.transits:
        r1._transits = new_transits # type: ignore
        break

    while True:
      new_mutual = __random_discovery()
      if new_mutual != r1.mutual:
        r1._mutual = new_mutual # type: ignore
        break

    self.assertNotEqual(r1.at_birth, r2.at_birth)
    self.assertNotEqual(r1.transits, r2.transits)
    self.assertNotEqual(r1.mutual, r2.mutual)

    r3 = analyzer.dizhi(gz_year, options)
    self.assertEqual(r2.at_birth, r3.at_birth)
    self.assertEqual(r2.transits, r3.transits)
    self.assertEqual(r2.mutual, r3.mutual)
