# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_analysis.py

import pytest
import unittest

from datetime import datetime

from src.Defines import Tiangan, Dizhi, Ganzhi, TianganRelation, DizhiRelation
from src.Utils import TianganUtils, DizhiUtils
from src.Bazi import Bazi, BaziGender, BaziPrecision
from src.BaziChart import BaziChart
from src.Transits import TransitOptions, TransitDatabase
from src.Analyzer.Relationship import RelationshipAnalyzer, TransitAnalysis, AtBirthAnalysis


@pytest.mark.integration
class TestRelationshipAnalysis(unittest.TestCase):
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
    db: TransitDatabase = TransitDatabase(chart)
    analyzer: RelationshipAnalyzer = RelationshipAnalyzer(chart)
    transits: TransitAnalysis = analyzer.transits

    with self.subTest('basic info correctness'):
      self.assertEqual(bazi.year_pillar, Ganzhi.from_str('甲子'))
      self.assertEqual(bazi.month_pillar, Ganzhi.from_str('丁卯'))
      self.assertEqual(bazi.day_pillar, Ganzhi.from_str('乙丑'))
      self.assertEqual(bazi.hour_pillar, Ganzhi.from_str('壬午'))

      self.assertEqual(chart.xiaoyun[0].ganzhi, Ganzhi.from_str('癸未'))
      self.assertEqual(next(chart.dayun).ganzhi, Ganzhi.from_str('戊辰'), 'first dayun Ganzhi')
      self.assertEqual(next(chart.dayun).ganzhi_year, 1985, 'first dayun year')

      self.assertEqual(chart.relationship_stars.tiangan, Tiangan.戊)
      self.assertSetEqual(set(chart.relationship_stars.dizhi), {Dizhi.辰, Dizhi.戌})

    with self.subTest('at birth'):
      at_birth: AtBirthAnalysis = analyzer.at_birth

      self.assertSetEqual(at_birth.shensha['taohua'],   {Dizhi.午})
      self.assertSetEqual(at_birth.shensha['hongluan'], {Dizhi.卯})
      # 问真八字以乙日主见午为红艳，但 `Rules.HONGYAN` 中以乙日主见申为红艳，所以这里为空。
      self.assertSetEqual(at_birth.shensha['hongyan'],  set()) 
      self.assertSetEqual(at_birth.shensha['tianxi'],   set())

      # 感情分析主要关心日主被合的情况，但原局日主没有被合。
      # 虽然我们不关心相生关系，但在这里还是检查一下。
      self.assertTrue(self.__check_tiangan({
        TianganRelation.生 : [frozenset({Tiangan.乙, Tiangan.丁}),
                             frozenset({Tiangan.乙, Tiangan.壬})],
      }, at_birth.day_master_relations))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.子, Dizhi.丑})],
        DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
        DizhiRelation.生 : [frozenset({Dizhi.午, Dizhi.丑})],
        DizhiRelation.克 : [frozenset({Dizhi.丑, Dizhi.子}),
                           frozenset({Dizhi.卯, Dizhi.丑})],
      }, at_birth.house_relations))

      # 原局无正财星，所以配偶星的关系分析为空。
      self.assertEqual(len(at_birth.star_relations.tiangan), 0)
      self.assertEqual(len(at_birth.star_relations.dizhi), 0)

    with self.subTest('1990'):
      self.assertSetEqual(set(db.ganzhis(1990, TransitOptions.DAYUN_LIUNIAN)),
                          {Ganzhi.from_str('戊辰'), Ganzhi.from_str('庚午')})

      shensha = transits.shensha(1990, TransitOptions.DAYUN_LIUNIAN)
      self.assertSetEqual(shensha['taohua'],   {Dizhi.午})
      self.assertSetEqual(shensha['hongluan'], set())
      self.assertSetEqual(shensha['hongyan'],  set())
      self.assertSetEqual(shensha['tianxi'],   set())

      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.乙, Tiangan.庚})],
        TianganRelation.克 : [frozenset({Tiangan.庚, Tiangan.乙}),
                             frozenset({Tiangan.乙, Tiangan.戊})],
      }, transits.day_master_relations(1990, TransitOptions.DAYUN_LIUNIAN)))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
        DizhiRelation.破 : [frozenset({Dizhi.辰, Dizhi.丑})],
        DizhiRelation.生 : [frozenset({Dizhi.午, Dizhi.丑})],
      }, transits.house_relations(1990, TransitOptions.DAYUN_LIUNIAN)))

      star_relations_all = transits.star_relations(1990, TransitOptions.DAYUN_LIUNIAN) # level is `ALL` by default.
      
      self.assertTrue(self.__check_tiangan({
        TianganRelation.生 : [frozenset({Tiangan.戊, Tiangan.庚}),
                             frozenset({Tiangan.戊, Tiangan.丁})],
        TianganRelation.克 : [frozenset({Tiangan.甲, Tiangan.戊}),
                             frozenset({Tiangan.乙, Tiangan.戊}),
                             frozenset({Tiangan.壬, Tiangan.戊})],
      }, star_relations_all.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.生 : [frozenset({Dizhi.午, Dizhi.辰})],
        DizhiRelation.克 : [frozenset({Dizhi.辰, Dizhi.子}),
                           frozenset({Dizhi.卯, Dizhi.辰})],
        DizhiRelation.破 : [frozenset({Dizhi.辰, Dizhi.丑})],
        DizhiRelation.害 : [frozenset({Dizhi.辰, Dizhi.卯})],
        DizhiRelation.半合 : [frozenset({Dizhi.子, Dizhi.辰})],
      }, star_relations_all.dizhi))

      self.assertFalse(transits.zhengyin(1990, TransitOptions.DAYUN_LIUNIAN).tiangan)
      self.assertFalse(transits.zhengyin(1990, TransitOptions.DAYUN_LIUNIAN).dizhi)

      self.assertTrue(transits.star(1990, TransitOptions.DAYUN_LIUNIAN).tiangan)
      self.assertTrue(transits.star(1990, TransitOptions.DAYUN_LIUNIAN).dizhi)
      self.assertTrue(transits.star(1990, TransitOptions.DAYUN).tiangan)
      self.assertTrue(transits.star(1990, TransitOptions.DAYUN).dizhi)
      self.assertFalse(transits.star(1990, TransitOptions.LIUNIAN).tiangan)
      self.assertFalse(transits.star(1990, TransitOptions.LIUNIAN).dizhi)

    with self.subTest('2018'):
      self.assertSetEqual(set(db.ganzhis(2018, TransitOptions.DAYUN_LIUNIAN)),
                          {Ganzhi.from_str('辛未'), Ganzhi.from_str('戊戌')})
      
      shensha = transits.shensha(2018, TransitOptions.DAYUN_LIUNIAN)
      self.assertSetEqual(shensha['taohua'],   set())
      self.assertSetEqual(shensha['hongluan'], set())
      self.assertSetEqual(shensha['hongyan'],  set())
      self.assertSetEqual(shensha['tianxi'],   set())

      self.assertTrue(self.__check_tiangan({
        TianganRelation.克 : [frozenset({Tiangan.乙, Tiangan.辛}),
                             frozenset({Tiangan.乙, Tiangan.戊})],
      }, transits.day_master_relations(2018, TransitOptions.DAYUN_LIUNIAN)))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未, Dizhi.戌}),
                           frozenset({Dizhi.丑, Dizhi.未})],
        DizhiRelation.冲 : [frozenset({Dizhi.丑, Dizhi.未})],
      }, transits.house_relations(2018, TransitOptions.DAYUN_LIUNIAN)))

      star_relations_all = transits.star_relations(2018, TransitOptions.DAYUN_LIUNIAN) # level is `ALL` by default.
      
      self.assertTrue(self.__check_tiangan({
        TianganRelation.克 : [frozenset({Tiangan.甲, Tiangan.戊}),
                             frozenset({Tiangan.壬, Tiangan.戊})],
      }, star_relations_all.tiangan))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.戌, Dizhi.卯})],
        DizhiRelation.半合 : [frozenset({Dizhi.戌, Dizhi.午})],
        DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未, Dizhi.戌})],
        DizhiRelation.破 : [frozenset({Dizhi.戌, Dizhi.未})],
        DizhiRelation.生 : [frozenset({Dizhi.戌, Dizhi.午})],
        DizhiRelation.克 : [frozenset({Dizhi.戌, Dizhi.卯}),
                           frozenset({Dizhi.戌, Dizhi.子})],
      }, star_relations_all.dizhi))

      self.assertFalse(transits.zhengyin(2018, TransitOptions.DAYUN_LIUNIAN).tiangan)
      self.assertFalse(transits.zhengyin(2018, TransitOptions.DAYUN_LIUNIAN).dizhi)

      self.assertTrue(transits.star(2018, TransitOptions.DAYUN_LIUNIAN).tiangan)
      self.assertTrue(transits.star(2018, TransitOptions.DAYUN_LIUNIAN).dizhi)
      self.assertTrue(transits.star(2018, TransitOptions.LIUNIAN).tiangan)
      self.assertTrue(transits.star(2018, TransitOptions.LIUNIAN).dizhi)
      self.assertFalse(transits.star(2018, TransitOptions.DAYUN).tiangan)
      self.assertFalse(transits.star(2018, TransitOptions.DAYUN).dizhi)

    with self.subTest('2031'):
      self.assertSetEqual(set(db.ganzhis(2031, TransitOptions.DAYUN_LIUNIAN)),
                          {Ganzhi.from_str('辛亥'), Ganzhi.from_str('壬申')})

      shensha = transits.shensha(2031, TransitOptions.DAYUN_LIUNIAN)
      self.assertSetEqual(shensha['taohua'],   set())
      self.assertSetEqual(shensha['hongluan'], set())
      self.assertSetEqual(shensha['hongyan'],  {Dizhi.申})
      self.assertSetEqual(shensha['tianxi'],   set())

      self.assertTrue(self.__check_tiangan({
        TianganRelation.克 : [frozenset({Tiangan.乙, Tiangan.辛})],
        TianganRelation.生 : [frozenset({Tiangan.乙, Tiangan.壬})],
      }, transits.day_master_relations(2031, TransitOptions.DAYUN_LIUNIAN)))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.生 : [frozenset({Dizhi.申, Dizhi.丑})],
        DizhiRelation.克 : [frozenset({Dizhi.丑, Dizhi.亥})],
        DizhiRelation.三会 : [frozenset({Dizhi.亥, Dizhi.子, Dizhi.丑})],
      }, transits.house_relations(2031, TransitOptions.DAYUN_LIUNIAN)))

      star_relations_all = transits.star_relations(2031, TransitOptions.DAYUN_LIUNIAN) # level is `ALL` by default.
      self.assertEqual(0, len(star_relations_all.tiangan))
      self.assertEqual(0, len(star_relations_all.dizhi))

      self.assertTrue(transits.zhengyin(2031, TransitOptions.DAYUN_LIUNIAN).tiangan)
      self.assertTrue(transits.zhengyin(2031, TransitOptions.DAYUN_LIUNIAN).dizhi)

      self.assertFalse(transits.star(2031, TransitOptions.DAYUN_LIUNIAN).tiangan)
      self.assertFalse(transits.star(2031, TransitOptions.DAYUN_LIUNIAN).dizhi)
