# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_ganzhi_relations.py

import pytest
import unittest

from datetime import datetime

from src.Bazi import Bazi, BaziGender, BaziPrecision
from src.BaziChart import BaziChart, TransitOptions, TransitDatabase
from src.Defines import Tiangan, Dizhi, Ganzhi, TianganRelation, DizhiRelation
from src.Utils import TianganUtils, DizhiUtils


@pytest.mark.integration
class TestTianganDizhiRelations(unittest.TestCase):
  '''
  Integration tests are mainly aiming to test the correctness of `TianganUtils` and `DizhiUtils` in transit context.
  The Bazi cases are collected from "测测" app / "问真八字" web site.

  In this project, `search`, `discover`, and `discover_mutual` methods in `TianganUtils` and `DizhiUtils` will
  return all possible combos.
  However, for 测测 and 问真八字, they only consider part of the combos. For example, 
  they don't consider SHENG / 生 relation.

  So in the following tests, we only test that the relation combos that 测测/问真八字 find 
  are in `TianganUtils`'s and `DizhiUtils`'s returns. 
  There can be some combos in the returns but not in 测测/问真八字's results.
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
    db: TransitDatabase = chart.transit_db

    with self.subTest('pillar correctness'):
      self.assertEqual(bazi.year_pillar, Ganzhi.from_str('甲子'))
      self.assertEqual(bazi.month_pillar, Ganzhi.from_str('丁卯'))
      self.assertEqual(bazi.day_pillar, Ganzhi.from_str('乙丑'))
      self.assertEqual(bazi.hour_pillar, Ganzhi.from_str('壬午'))
      self.assertEqual(chart.xiaoyun[0].ganzhi, Ganzhi.from_str('癸未'))
      self.assertEqual(next(chart.dayun).ganzhi, Ganzhi.from_str('戊辰'), 'first dayun Ganzhi')
      self.assertEqual(next(chart.dayun).ganzhi_year, 1985, 'first dayun year')

    with self.subTest('at birth'):
      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.丁, Tiangan.壬})],
      }, TianganUtils.discover(chart.bazi.four_tiangans)))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.子, Dizhi.丑})],
        DizhiRelation.刑 : [frozenset({Dizhi.子, Dizhi.卯})],
        DizhiRelation.冲 : [frozenset({Dizhi.子, Dizhi.午})],
        DizhiRelation.破 : [frozenset({Dizhi.午, Dizhi.卯})],
        DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
      }, DizhiUtils.discover(chart.bazi.four_dizhis)))

    with self.subTest('1993 dayun and liunian - transits only'):
      ganzhis = db.ganzhis(1993, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.戊, Tiangan.癸})],
      }, TianganUtils.discover(tuple(gz.tiangan for gz in ganzhis))))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.辰, Dizhi.酉})],
      }, DizhiUtils.discover(tuple(gz.dizhi for gz in ganzhis))))

    with self.subTest('2024 dayun and liunian - between transits and at-birth'):
      ganzhis = db.ganzhis(2024, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.克 : [frozenset({Tiangan.丁, Tiangan.辛}), frozenset({Tiangan.辛, Tiangan.乙})],
      }, TianganUtils.discover_mutual(bazi.four_tiangans, tuple(gz.tiangan for gz in ganzhis))))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.午, Dizhi.未})],
        DizhiRelation.半合 : [frozenset({Dizhi.子, Dizhi.辰}), frozenset({Dizhi.卯, Dizhi.未})],
        DizhiRelation.刑 : [frozenset({Dizhi.未, Dizhi.丑})], # LOOSE mode is used for XING relation.
        DizhiRelation.冲 : [frozenset({Dizhi.未, Dizhi.丑})],
        DizhiRelation.破 : [frozenset({Dizhi.丑, Dizhi.辰})],
        DizhiRelation.害 : [frozenset({Dizhi.未, Dizhi.子}), frozenset({Dizhi.辰, Dizhi.卯})],
      }, DizhiUtils.discover_mutual(bazi.four_dizhis, tuple(gz.dizhi for gz in ganzhis))))

    with self.subTest('2051 dayun and liunian - transits only'):
      ganzhis = db.ganzhis(2051, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.破 : [frozenset({Dizhi.戌, Dizhi.未})],
        DizhiRelation.刑 : [frozenset({Dizhi.未, Dizhi.戌})],
      }, DizhiUtils.discover(tuple(gz.dizhi for gz in ganzhis))))

    with self.subTest('2051 dayun and liunian - between transits and at-birth'):
      ganzhis = db.ganzhis(2051, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.克 : [frozenset({Tiangan.丁, Tiangan.辛}), frozenset({Tiangan.辛, Tiangan.乙})],
      }, TianganUtils.discover_mutual(bazi.four_tiangans, tuple(gz.tiangan for gz in ganzhis))))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.卯, Dizhi.戌}), frozenset({Dizhi.午, Dizhi.未})],
        DizhiRelation.半合 : [frozenset({Dizhi.卯, Dizhi.未}), frozenset({Dizhi.午, Dizhi.戌})],
        DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未, Dizhi.戌}),
                            frozenset({Dizhi.未, Dizhi.丑}),
                            frozenset({Dizhi.戌, Dizhi.丑}),], # LOOSE mode is used for XING relation.
        DizhiRelation.冲 : [frozenset({Dizhi.丑, Dizhi.未})],
        DizhiRelation.害 : [frozenset({Dizhi.未, Dizhi.子})],
      }, DizhiUtils.discover_mutual(bazi.four_dizhis, tuple(gz.dizhi for gz in ganzhis))))

  def test_case2(self) -> None:
    '''From 测测 and 问真八字'''
    bazi: Bazi = Bazi(
      birth_time=datetime(2024, 5, 19, 18, 59),
      gender=BaziGender.FEMALE,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)
    db: TransitDatabase = chart.transit_db

    with self.subTest('pillar correctness'):
      self.assertEqual(bazi.year_pillar, Ganzhi.from_str('甲辰'))
      self.assertEqual(bazi.month_pillar, Ganzhi.from_str('己巳'))
      self.assertEqual(bazi.day_pillar, Ganzhi.from_str('癸未'))
      self.assertEqual(bazi.hour_pillar, Ganzhi.from_str('辛酉'))
      self.assertEqual(chart.xiaoyun[0].ganzhi, Ganzhi.from_str('庚申'))
      self.assertEqual(next(chart.dayun).ganzhi, Ganzhi.from_str('戊辰'), 'first dayun Ganzhi')
      self.assertEqual(next(chart.dayun).ganzhi_year, 2029, 'first dayun year')

    with self.subTest('at birth'):
      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.甲, Tiangan.己})],
        TianganRelation.克 : [frozenset({Tiangan.己, Tiangan.癸})],
      }, TianganUtils.discover(bazi.four_tiangans)))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.辰, Dizhi.酉})],
        DizhiRelation.半合 : [frozenset({Dizhi.巳, Dizhi.酉})],
      }, DizhiUtils.discover(bazi.four_dizhis)))

    with self.subTest('2024 xiaoyun and liunian - between transits and at-birth'): 
      # 测测's Xiaoyun result is kinda buggy. So use 问真八字's Xiaoyun result here.
      ganzhis = db.ganzhis(2024, TransitOptions.XIAOYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.甲, Tiangan.己})],
        TianganRelation.克 : [frozenset({Tiangan.庚, Tiangan.甲})],
      }, TianganUtils.discover_mutual(bazi.four_tiangans, tuple(gz.tiangan for gz in ganzhis))))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.辰, Dizhi.酉}), frozenset({Dizhi.巳, Dizhi.申})],
        DizhiRelation.刑 : [frozenset({Dizhi.辰}), frozenset({Dizhi.巳, Dizhi.申})], # LOOSE mode is used.
        DizhiRelation.破 : [frozenset({Dizhi.巳, Dizhi.申})],
      }, DizhiUtils.discover_mutual(bazi.four_dizhis, tuple(gz.dizhi for gz in ganzhis))))

    with self.subTest('2052 dayun and liunian - transits only'):
      ganzhis = db.ganzhis(2052, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.冲 : [frozenset({Tiangan.丙, Tiangan.壬})],
      }, TianganUtils.discover(tuple(gz.tiangan for gz in ganzhis))))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.冲 : [frozenset({Dizhi.寅, Dizhi.申})],
        DizhiRelation.刑 : [frozenset({Dizhi.寅, Dizhi.申})],
      }, DizhiUtils.discover(tuple(gz.dizhi for gz in ganzhis))))

    with self.subTest('2052 dayun and liunian - between transits and at-birth'):
      ganzhis = db.ganzhis(2052, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.合 : [frozenset({Tiangan.丙, Tiangan.辛})],
      }, TianganUtils.discover_mutual(bazi.four_tiangans, tuple(gz.tiangan for gz in ganzhis))))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.巳, Dizhi.申})],
        DizhiRelation.破 : [frozenset({Dizhi.巳, Dizhi.申})],
        DizhiRelation.刑 : [frozenset({Dizhi.寅, Dizhi.巳, Dizhi.申}),
                           frozenset({Dizhi.寅, Dizhi.巳}),
                           frozenset({Dizhi.巳, Dizhi.申}),],
      }, DizhiUtils.discover_mutual(bazi.four_dizhis, tuple(gz.dizhi for gz in ganzhis))))

    with self.subTest('2062 dayun and liunian - transits only'):
      ganzhis = db.ganzhis(2062, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
      }, DizhiUtils.discover(tuple(gz.dizhi for gz in ganzhis))))

    with self.subTest('2062 dayun and liunian - between transits and at-birth'):
      ganzhis = db.ganzhis(2062, TransitOptions.DAYUN_LIUNIAN)

      self.assertTrue(self.__check_tiangan({
        TianganRelation.冲 : [frozenset({Tiangan.乙, Tiangan.辛})],
        TianganRelation.克 : [frozenset({Tiangan.乙, Tiangan.己})],
      }, TianganUtils.discover_mutual(bazi.four_tiangans, tuple(gz.tiangan for gz in ganzhis))))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.六合 : [frozenset({Dizhi.午, Dizhi.未})],
        DizhiRelation.三合 : [frozenset({Dizhi.巳, Dizhi.酉, Dizhi.丑})],
        DizhiRelation.三会 : [frozenset({Dizhi.巳, Dizhi.午, Dizhi.未})],
        DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未})], # LOOSE mode is used here...
        DizhiRelation.冲 : [frozenset({Dizhi.丑, Dizhi.未})],
        DizhiRelation.破 : [frozenset({Dizhi.丑, Dizhi.辰})],
      }, DizhiUtils.discover_mutual(bazi.four_dizhis, tuple(gz.dizhi for gz in ganzhis))))
