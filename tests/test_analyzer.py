# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_analyzer.py

import unittest

from src.BaziChart import BaziChart
from src.Analyzer import RelationAnalyzer


class TestRelationAnalyzer(unittest.TestCase):
  def test_chart(self) -> None:
    chart: BaziChart = BaziChart.random()
    analyzer: RelationAnalyzer = RelationAnalyzer(chart)

    with self.subTest('deepcopy'):
      self.assertIsNot(analyzer.chart, analyzer.chart)
      self.assertIsNot(analyzer.chart.bazi, analyzer.chart.bazi)
    
    with self.subTest('equality'):
      self.assertEqual(analyzer.chart.bazi, chart.bazi)
      self.assertEqual(analyzer.chart.json, chart.json)
      self.assertEqual(analyzer.chart.bazi, analyzer.chart.bazi)
      self.assertEqual(analyzer.chart.json, analyzer.chart.json)
