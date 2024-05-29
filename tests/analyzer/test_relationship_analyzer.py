# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_analyzer.py

import pytest
import unittest

import itertools

from src.Defines import Tiangan, Dizhi
from src.Utils import ShenshaUtils, TianganUtils, DizhiUtils
from src.BaziChart import BaziChart
from src.Analyzer.Relationship import RelationshipAnalyzer


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


# TODO: Integration tests on `RelationshipAnalyzer`.
