# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_analyzer.py

import pytest
import unittest

import itertools

from src.Defines import Tiangan, Dizhi, TianganRelation, DizhiRelation
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
        expected_house_relations: set[DizhiRelation] = set(DizhiUtils.discover_mutual([y, m, h], [d]).keys())
        self.assertSetEqual(analyzer.at_birth['house_relations'], expected_house_relations)
        self.assertSetEqual(analyzer.at_birth['house_relations'], analyzer.at_birth['house_relations'], 'Constancy')

      with self.subTest('Day Master Relations / 日主关系'):
        expected_day_master_relations: set[TianganRelation] = \
          set(TianganUtils.discover_mutual([
            chart.bazi.year_pillar.tiangan, 
            chart.bazi.month_pillar.tiangan,
            chart.bazi.hour_pillar.tiangan
          ], [dm]).keys())
        self.assertSetEqual(analyzer.at_birth['day_master_relations'], expected_day_master_relations)
        self.assertSetEqual(analyzer.at_birth['day_master_relations'], analyzer.at_birth['day_master_relations'], 'Constancy')
