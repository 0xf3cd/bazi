# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_analyzer.py

import pytest
import unittest

import itertools

from src.Defines import Tiangan, Dizhi
from src.Utils import ShenshaUtils, TianganUtils, DizhiUtils
from src.BaziChart import BaziChart
from src.Analyzer.Relationship import RelationshipAnalyzer


class TestRelationshipAnalyzer(unittest.TestCase):
  def test_at_birth_misc(self) -> None:
    chart = BaziChart.random()
    analyzer = RelationshipAnalyzer(chart)

    self.assertEqual(analyzer.at_birth, analyzer.at_birth, 'Equality')
    self.assertEqual(analyzer.at_birth, analyzer.at_birth, 'Constancy')

  @pytest.mark.slow
  def test_at_birth(self) -> None:
    for _ in range(100):
      chart = BaziChart.random()
      analyzer = RelationshipAnalyzer(chart)

      dm: Tiangan = chart.bazi.day_master
      y, m, d, h = chart.bazi.four_dizhis

      with self.subTest('Taohua / 桃花'):
        expected_taohua: list[Dizhi] = []
        for dz1, dz2 in itertools.product([y], [m, d, h]):
          if ShenshaUtils.taohua(dz1, dz2):
            expected_taohua.append(dz2)
        for dz1, dz2 in itertools.product([d], [y, m, h]):
          if ShenshaUtils.taohua(dz1, dz2):
            expected_taohua.append(dz2)
        self.assertSetEqual(analyzer.at_birth['taohua'], set(expected_taohua))
        self.assertSetEqual(analyzer.at_birth['taohua'], analyzer.at_birth['taohua'], 'Constancy')

      with self.subTest('Hongyan / 红艳'):
        expected_hongyan: list[Dizhi] = []
        for tg, dz in itertools.product([dm], [y, m, d, h]):
          if ShenshaUtils.hongyan(tg, dz):
            expected_hongyan.append(dz)
        self.assertSetEqual(analyzer.at_birth['hongyan'], set(expected_hongyan))
        self.assertSetEqual(analyzer.at_birth['hongyan'], analyzer.at_birth['hongyan'], 'Constancy')

      with self.subTest('Hongluan / 红鸾'):
        expected_hongluan: list[Dizhi] = []
        for dz1, dz2 in itertools.product([y], [m, d, h]):
          if ShenshaUtils.hongluan(dz1, dz2):
            expected_hongluan.append(dz2)
        self.assertSetEqual(analyzer.at_birth['hongluan'], set(expected_hongluan))
        self.assertSetEqual(analyzer.at_birth['hongluan'], analyzer.at_birth['hongluan'], 'Constancy')

      with self.subTest('Tianxi / 天喜'):
        expected_tianxi: list[Dizhi] = []
        for dz1, dz2 in itertools.product([y], [m, d, h]):
          if ShenshaUtils.tianxi(dz1, dz2):
            expected_tianxi.append(dz2)
        self.assertSetEqual(analyzer.at_birth['tianxi'], set(expected_tianxi))
        self.assertSetEqual(analyzer.at_birth['tianxi'], analyzer.at_birth['tianxi'], 'Constancy')

      with self.subTest('House of Relationship / 婚姻宫'):
        self.assertEqual(analyzer.at_birth['house_relations'], DizhiUtils.discover_mutual([y, m, h], [d]))
        self.assertEqual(analyzer.at_birth['house_relations'], analyzer.at_birth['house_relations'], 'Constancy')

      with self.subTest('Day Master Relations / 日主关系'):
        self.assertEqual(analyzer.at_birth['day_master_relations'], TianganUtils.discover_mutual([
          chart.bazi.year_pillar.tiangan, 
          chart.bazi.month_pillar.tiangan,
          chart.bazi.hour_pillar.tiangan
        ], [dm]))
        self.assertEqual(analyzer.at_birth['day_master_relations'], analyzer.at_birth['day_master_relations'], 'Constancy')

      with self.subTest('Relationship Star Relations / 夫妻星关系'):
        stars = chart.relationship_stars
        for tg_combos in analyzer.at_birth['tg_star_relations'].values():
          for tg_combo in tg_combos:
            self.assertIn(stars.tiangan, tg_combo)
        for dz_combos in analyzer.at_birth['dz_star_relations'].values():
          for dz_combo in dz_combos:
            self.assertTrue(any(dz in dz_combo for dz in stars.dizhi))

        self.assertEqual(analyzer.at_birth['tg_star_relations'], analyzer.at_birth['tg_star_relations'], 'Constancy')
        self.assertEqual(analyzer.at_birth['dz_star_relations'], analyzer.at_birth['dz_star_relations'], 'Constancy')


  @pytest.mark.slow
  def test_filtered(self) -> None:
    '''Test "tg_star_relations" and "dz_star_relations" only contain filtered combos.'''
    for _ in range(16):
      chart: BaziChart = BaziChart.random()
      analyzer: RelationshipAnalyzer = RelationshipAnalyzer(chart)
      stars = chart.relationship_stars
      
      with self.subTest('at_birth'):
        at_birth_analysis = analyzer.at_birth

        for tg_rel, tg_combos in TianganUtils.discover(chart.bazi.four_tiangans).items():
          if tg_rel not in at_birth_analysis['tg_star_relations']:
            self.assertTrue(all(stars.tiangan not in tg_combo for tg_combo in tg_combos))
          else:
            for tg_combo in tg_combos:
              self.assertEqual(stars.tiangan in tg_combo,
                               tg_combo in at_birth_analysis['tg_star_relations'][tg_rel])
              
        for dz_rel, dz_combos in DizhiUtils.discover(chart.bazi.four_dizhis).items():
          if dz_rel not in at_birth_analysis['dz_star_relations']:
            self.assertTrue(all(dz not in dz_combo for dz_combo in dz_combos for dz in stars.dizhi))
          else:
            for dz_combo in dz_combos:
              self.assertEqual(any(dz in dz_combo for dz in stars.dizhi),
                               dz_combo in at_birth_analysis['dz_star_relations'][dz_rel])
