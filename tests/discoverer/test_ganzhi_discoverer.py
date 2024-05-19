# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_ganzhi_discoverer.py

import pytest
import unittest

import random
import itertools

from src.Common import PillarData
from src.Defines import Tiangan, Dizhi, Ganzhi, TianganRelation, DizhiRelation
from src.BaziChart import BaziChart
from src.Utils import TianganUtils, DizhiUtils, BaziUtils
from src.Calendar.HkoDataCalendarUtils import to_ganzhi
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
                                set(list(at_birth.tiangan[tg_rel]) + list(transits.tiangan[tg_rel]) + list(mutual.tiangan[tg_rel])))
            
          expected_dizhi_combined: DizhiUtils.DizhiRelationDiscovery = DizhiUtils.discover(list(chart.bazi.four_dizhis) + transit_dizhis)
          for dz_rel in DizhiRelation:
            self.assertSetEqual(set(expected_dizhi_combined[dz_rel]), 
                                set(list(at_birth.dizhi[dz_rel]) + list(transits.dizhi[dz_rel]) + list(mutual.dizhi[dz_rel])))
