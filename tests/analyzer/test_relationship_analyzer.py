# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_analyzer.py

import pytest
import unittest

import random
import itertools

from src.Defines import Tiangan, Dizhi, Shishen, DizhiRelation
from src.Utils import ShenshaUtils, TianganUtils, DizhiUtils, BaziUtils
from src.BaziChart import BaziChart
from src.Transits import TransitOptions, TransitDatabase
from src.Analyzer.Relationship import RelationshipAnalyzer, TransitAnalysis


class TestAtBirthAnalysis(unittest.TestCase):
  @pytest.mark.slow
  def test_shensha(self) -> None:
    for _ in range(100):
      chart = BaziChart.random()
      analyzer = RelationshipAnalyzer(chart)

      dm: Tiangan = chart.bazi.day_master
      y, m, d, h = chart.bazi.four_dizhis

      at_birth = analyzer.at_birth

      with self.subTest('Taohua / 桃花'):
        expected_taohua: list[Dizhi] = []
        for dz1, dz2 in itertools.product([y], [m, d, h]):
          if ShenshaUtils.taohua(dz1, dz2):
            expected_taohua.append(dz2)
        for dz1, dz2 in itertools.product([d], [y, m, h]):
          if ShenshaUtils.taohua(dz1, dz2):
            expected_taohua.append(dz2)
        self.assertSetEqual(at_birth.shensha['taohua'], set(expected_taohua))
        self.assertSetEqual(at_birth.shensha['taohua'], at_birth.shensha['taohua'], 'Constancy')

      with self.subTest('Hongyan / 红艳'):
        expected_hongyan: list[Dizhi] = []
        for tg, dz in itertools.product([dm], [y, m, d, h]):
          if ShenshaUtils.hongyan(tg, dz):
            expected_hongyan.append(dz)
        self.assertSetEqual(at_birth.shensha['hongyan'], set(expected_hongyan))
        self.assertSetEqual(at_birth.shensha['hongyan'], at_birth.shensha['hongyan'], 'Constancy')

      with self.subTest('Hongluan / 红鸾'):
        expected_hongluan: list[Dizhi] = []
        for dz1, dz2 in itertools.product([y], [m, d, h]):
          if ShenshaUtils.hongluan(dz1, dz2):
            expected_hongluan.append(dz2)
        self.assertSetEqual(at_birth.shensha['hongluan'], set(expected_hongluan))
        self.assertSetEqual(at_birth.shensha['hongluan'], at_birth.shensha['hongluan'], 'Constancy')

      with self.subTest('Tianxi / 天喜'):
        expected_tianxi: list[Dizhi] = []
        for dz1, dz2 in itertools.product([y], [m, d, h]):
          if ShenshaUtils.tianxi(dz1, dz2):
            expected_tianxi.append(dz2)
        self.assertSetEqual(at_birth.shensha['tianxi'], set(expected_tianxi))
        self.assertSetEqual(at_birth.shensha['tianxi'], at_birth.shensha['tianxi'], 'Constancy')

  @pytest.mark.slow
  def test_day_master_relations(self) -> None:
    for _ in range(100):
      chart = BaziChart.random()
      analyzer = RelationshipAnalyzer(chart)

      dm = chart.bazi.day_master
      at_birth = analyzer.at_birth

      self.assertEqual(at_birth.day_master_relations, TianganUtils.discover_mutual([
        chart.bazi.year_pillar.tiangan, 
        chart.bazi.month_pillar.tiangan,
        chart.bazi.hour_pillar.tiangan
      ], [dm]))
      self.assertEqual(at_birth.day_master_relations, at_birth.day_master_relations, 'Constancy')

  @pytest.mark.slow
  def test_house_relations(self) -> None:
    for _ in range(100):
      chart = BaziChart.random()
      analyzer = RelationshipAnalyzer(chart)

      y, m, d, h = chart.bazi.four_dizhis
      at_birth = analyzer.at_birth

      # For AtBirth analysis, the following two algorithms are equivalent.
      self.assertEqual(at_birth.house_relations, DizhiUtils.discover([y, m, d, h]).filter(
        lambda _, combo : d in combo
      )) 
      self.assertEqual(at_birth.house_relations, DizhiUtils.discover_mutual([y, m, h], [d]))

      self.assertEqual(at_birth.house_relations, at_birth.house_relations, 'Constancy')

  @pytest.mark.slow
  def test_star_relations(self) -> None:
    for _ in range(100):
      chart = BaziChart.random()
      analyzer = RelationshipAnalyzer(chart)

      at_birth = analyzer.at_birth
      stars = chart.relationship_stars
      
      for tg_combos in at_birth.star_relations.tiangan.values():
        for tg_combo in tg_combos:
          self.assertIn(stars.tiangan, tg_combo)
      for dz_combos in at_birth.star_relations.dizhi.values():
        for dz_combo in dz_combos:
          self.assertTrue(any(dz in dz_combo for dz in stars.dizhi))

      self.assertEqual(at_birth.star_relations.tiangan, at_birth.star_relations.tiangan, 'Constancy')
      self.assertEqual(at_birth.star_relations.dizhi, at_birth.star_relations.dizhi, 'Constancy')

  @pytest.mark.slow
  def test_filtered(self) -> None:
    '''Test "star_relations" only contain filtered combos.'''
    for _ in range(16):
      chart: BaziChart = BaziChart.random()
      analyzer: RelationshipAnalyzer = RelationshipAnalyzer(chart)

      stars = chart.relationship_stars
      at_birth = analyzer.at_birth

      for tg_rel, tg_combos in TianganUtils.discover(chart.bazi.four_tiangans).items():
        if tg_rel not in at_birth.star_relations.tiangan:
          self.assertTrue(all(stars.tiangan not in tg_combo for tg_combo in tg_combos))
        else:
          for tg_combo in tg_combos:
            self.assertEqual(stars.tiangan in tg_combo,
                             tg_combo in at_birth.star_relations.tiangan[tg_rel])
            
      for dz_rel, dz_combos in DizhiUtils.discover(chart.bazi.four_dizhis).items():
        if dz_rel not in at_birth.star_relations.dizhi:
          self.assertTrue(all(dz not in dz_combo for dz_combo in dz_combos for dz in stars.dizhi))
        else:
          for dz_combo in dz_combos:
            self.assertEqual(any(dz in dz_combo for dz in stars.dizhi),
                             dz_combo in at_birth.star_relations.dizhi[dz_rel])


class TestTransitAnalysis(unittest.TestCase):
  @staticmethod
  def __equal(discovery1, discovery2) -> bool:
    if type(discovery1) is not type(discovery2):
      return False
    if set(discovery1.keys()) != set(discovery2.keys()):
      return False
    for key in discovery1.keys():
      if set(discovery1[key]) != set(discovery2[key]):
        return False
    return True
  
  @staticmethod
  def __random_transit_options() -> TransitOptions:
    return random.choice([
      TransitOptions.DAYUN,
      TransitOptions.DAYUN_LIUNIAN,
      TransitOptions.LIUNIAN,
      TransitOptions.XIAOYUN,
      TransitOptions.XIAOYUN_LIUNIAN
    ])

  @pytest.mark.slow
  def test_shensha(self) -> None:
    for _ in range(32):
      chart = BaziChart.random()      
      db = TransitDatabase(chart)

      dm = chart.bazi.day_master
      y_dz = chart.bazi.year_pillar.dizhi
      d_dz = chart.bazi.day_pillar.dizhi

      analyzer = RelationshipAnalyzer(chart)
      transits_analysis = analyzer.transits

      for __ in range(128):
        randon_year = chart.bazi.ganzhi_date.year + random.randint(0, 100)
        random_options = self.__random_transit_options()
        if not transits_analysis.support(randon_year, random_options):
          continue

        transit_dz = tuple(gz.dizhi for gz in db.ganzhis(randon_year, random_options))
        actual = transits_analysis.shensha(randon_year, random_options)

        with self.subTest('Taohua / 桃花'):
          expected = []
          for dz in transit_dz:
            if ShenshaUtils.taohua(y_dz, dz):
              expected.append(dz)
            if ShenshaUtils.taohua(d_dz, dz):
              expected.append(dz)
          self.assertSetEqual(actual['taohua'], set(expected))

        with self.subTest('Hongyan / 红艳'):
          expected = []
          for dz in transit_dz:
            if ShenshaUtils.hongyan(dm, dz):
              expected.append(dz)
          self.assertSetEqual(actual['hongyan'], set(expected))

        with self.subTest('Hongluan / 红鸾'):
          expected = []
          for dz in transit_dz:
            if ShenshaUtils.hongluan(y_dz, dz):
              expected.append(dz)
          self.assertSetEqual(actual['hongluan'], set(expected))

        with self.subTest('Tianxi / 天喜'):
          expected = []
          for dz in transit_dz:
            if ShenshaUtils.tianxi(y_dz, dz):
              expected.append(dz)
          self.assertSetEqual(actual['tianxi'], set(expected))

  @pytest.mark.slow
  def test_day_master_relations(self) -> None:
    for _ in range(32):
      chart = BaziChart.random()
      db = TransitDatabase(chart)
      analyzer = RelationshipAnalyzer(chart)
      transits_analysis = analyzer.transits

      for __ in range(128):
        randon_year = chart.bazi.ganzhi_date.year + random.randint(0, 100)
        random_options = self.__random_transit_options()
        if not transits_analysis.support(randon_year, random_options):
          continue
        
        transit_tg = tuple(gz.tiangan for gz in db.ganzhis(randon_year, random_options))
        expected = TianganUtils.discover_mutual([chart.bazi.day_master], transit_tg)
        actual = transits_analysis.day_master_relations(randon_year, random_options)

        self.assertTrue(TestTransitAnalysis.__equal(expected, actual))

  @pytest.mark.slow
  def test_house_relations(self) -> None:
    for _ in range(32):
      chart = BaziChart.random()
      bazi = chart.bazi
      db = TransitDatabase(chart)
      analyzer = RelationshipAnalyzer(chart)
      transits_analysis = analyzer.transits

      for __ in range(128):
        randon_year = chart.bazi.ganzhi_date.year + random.randint(0, 100)
        random_options = self.__random_transit_options()
        if not transits_analysis.support(randon_year, random_options):
          continue

        transit_dz = list(gz.dizhi for gz in db.ganzhis(randon_year, random_options))

        actual = transits_analysis.house_relations(randon_year, random_options)
        for _, combos in actual.items():
          for combo in combos:
            self.assertTrue(chart.house_of_relationship in combo)
            self.assertFalse(set(transit_dz).isdisjoint(combo))

        print(list(actual.keys()))
        
        expected = DizhiUtils.discover_mutual([chart.house_of_relationship], transit_dz)

        def __discover(rel: DizhiRelation):
          def __filter(rel: DizhiRelation, combo: frozenset[Dizhi]):
            if len(combo) != 3:
              return False
            for dz1 in transit_dz:
              for dz2 in [bazi.year_pillar.dizhi, bazi.month_pillar.dizhi,  bazi.hour_pillar.dizhi]:
                if combo == frozenset([dz1, dz2, chart.house_of_relationship]):
                  return True
            return False

          return DizhiUtils.DizhiRelationDiscovery({
            rel : DizhiUtils.search(list(bazi.four_dizhis) + transit_dz, rel)
          }).filter(__filter)

        expected = expected.merge(__discover(DizhiRelation.三合))
        expected = expected.merge(__discover(DizhiRelation.三会))
        expected = expected.merge(__discover(DizhiRelation.刑))

        self.assertTrue(TestTransitAnalysis.__equal(expected, actual))

  @pytest.mark.slow
  def test_star_relations(self) -> None:
    for _ in range(32):
      chart = BaziChart.random()
      stars = chart.relationship_stars

      db = TransitDatabase(chart)
      analyzer = RelationshipAnalyzer(chart)
      transits_analysis = analyzer.transits

      for __ in range(64):
        randon_year = chart.bazi.ganzhi_date.year + random.randint(0, 100)
        random_options = self.__random_transit_options()
        random_level = random.choice([
          TransitAnalysis.Level.TRANSITS_ONLY, 
          TransitAnalysis.Level.MUTUAL, 
          TransitAnalysis.Level.ALL
        ]) # mypy with Python 3.12 is problematic here on type checking... Explicitly list all enum values.
        if not transits_analysis.support(randon_year, random_options):
          continue
        
        transit_tg = tuple(gz.tiangan for gz in db.ganzhis(randon_year, random_options))
        transit_dz = tuple(gz.dizhi for gz in db.ganzhis(randon_year, random_options))

        tg_discovery = TianganUtils.TianganRelationDiscovery({})
        dz_discovery = DizhiUtils.DizhiRelationDiscovery({})
        if random_level in [TransitAnalysis.Level.TRANSITS_ONLY, TransitAnalysis.Level.ALL]:
          tg_discovery = tg_discovery.merge(TianganUtils.discover(transit_tg))
          dz_discovery = dz_discovery.merge(DizhiUtils.discover(transit_dz))
        if random_level in [TransitAnalysis.Level.MUTUAL, TransitAnalysis.Level.ALL]:
          tg_discovery = tg_discovery.merge(TianganUtils.discover_mutual(chart.bazi.four_tiangans, transit_tg))
          dz_discovery = dz_discovery.merge(DizhiUtils.discover_mutual(chart.bazi.four_dizhis, transit_dz))

        actual = transits_analysis.star_relations(randon_year, random_options, level=random_level)

        with self.subTest('Tiangan'):
          for tg_rel, tg_combos in actual.tiangan.items():
            self.assertIn(tg_rel, tg_discovery)
            for tg_combo in tg_combos:
              self.assertIn(tg_combo, tg_discovery[tg_rel])
          
          for tg_rel, tg_combos in tg_discovery.items():
            for tg_combo in tg_combos:
              if stars.tiangan in tg_combo:
                self.assertIn(tg_combo, actual.tiangan[tg_rel])

          self.assertTrue(TestTransitAnalysis.__equal(actual.tiangan, tg_discovery.filter(
            lambda _, combo : stars.tiangan in combo
          )))

        with self.subTest('Dizhi'):
          for dz_rel, dz_combos in actual.dizhi.items():
            self.assertIn(dz_rel, dz_discovery)
            for dz_combo in dz_combos:
              self.assertIn(dz_combo, dz_discovery[dz_rel])
          
          for dz_rel, dz_combos in dz_discovery.items():
            for dz_combo in dz_combos:
              if len(dz_combo & set(stars.dizhi)) > 0:
                self.assertIn(dz_combo, actual.dizhi[dz_rel])

          self.assertTrue(TestTransitAnalysis.__equal(actual.dizhi, dz_discovery.filter(
            lambda _, combo : len(combo & set(stars.dizhi)) > 0
          )))

  @pytest.mark.slow
  def test_zhengyin(self) -> None:
    for _ in range(32):
      chart = BaziChart.random()
      db = TransitDatabase(chart)
      analyzer = RelationshipAnalyzer(chart)
      transits_analysis = analyzer.transits

      for __ in range(128):
        randon_year = chart.bazi.ganzhi_date.year + random.randint(0, 100)
        random_options = self.__random_transit_options()
        if not transits_analysis.support(randon_year, random_options):
          continue

        expected_tg: bool = False
        expected_dz: bool = False
        for gz in db.ganzhis(randon_year, random_options):
          if BaziUtils.shishen(chart.bazi.day_master, gz.tiangan) == Shishen.正印:
            expected_tg = True
          if BaziUtils.shishen(chart.bazi.day_master, gz.dizhi) == Shishen.正印:
            expected_dz = True

        actual = transits_analysis.zhengyin(randon_year, random_options)
        self.assertEqual(expected_tg, actual.tiangan)
        self.assertEqual(expected_dz, actual.dizhi)

  @pytest.mark.slow
  def test_star(self) -> None:
    for _ in range(16):
      chart = BaziChart.random()
      db = TransitDatabase(chart)
      analyzer = RelationshipAnalyzer(chart)
      transits_analysis = analyzer.transits

      for __ in range(64):
        randon_year = chart.bazi.ganzhi_date.year + random.randint(0, 100)
        random_options = self.__random_transit_options()
        if not transits_analysis.support(randon_year, random_options):
          continue

        expected_tg: bool = False
        expected_dz: bool = False
        for gz in db.ganzhis(randon_year, random_options):
          if gz.tiangan == chart.relationship_stars.tiangan:
            expected_tg = True
          if gz.dizhi in chart.relationship_stars.dizhi:
            expected_dz = True

        actual = transits_analysis.star(randon_year, random_options)
        self.assertEqual(expected_tg, actual.tiangan)
        self.assertEqual(expected_dz, actual.dizhi)


# TODO: Integration tests on `RelationshipAnalyzer`.
# Also test `TransitDatabase`?
