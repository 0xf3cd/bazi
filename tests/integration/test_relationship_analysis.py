# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_analysis.py

import pytest
import unittest

import random
import logging

from datetime import datetime
from typing import cast, Union, Iterable

from src.Defines import Tiangan, Dizhi, Ganzhi, TianganRelation, DizhiRelation, Shishen
from src.Utils import TianganUtils, DizhiUtils, BaziUtils, ShenshaUtils
from src.Bazi import Bazi, BaziGender, BaziPrecision
from src.BaziChart import BaziChart
from src.Transits import TransitOptions, TransitDatabase
from src.Analyzer.Relationship import RelationshipAnalyzer, ShenshaAnalysis, TransitAnalysis, AtBirthAnalysis
from src.Rules import DizhiRules


logger = logging.getLogger(__name__)


DiscoveryType = Union[TianganUtils.TianganRelationDiscovery, DizhiUtils.DizhiRelationDiscovery]
def _equal(d1: DiscoveryType, d2: DiscoveryType) -> bool:
  assert type(d1) == type(d2)
  if set(d1.keys()) != set(d2.keys()):
    return False
  for rel, combos in d1.items():
    if not set(combos) == set(d2[rel]):  # type: ignore
      return False
  return True

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

  def test_case2(self) -> None:
    '''From 问真八字 https://pcbz.iwzwh.com/#/paipan/index'''
    bazi: Bazi = Bazi(
      birth_time=datetime(2020, 7, 2, 19, 8),
      gender=BaziGender.FEMALE,
      precision=BaziPrecision.DAY,
    )
    chart: BaziChart = BaziChart(bazi)
    birth_gz_year: int = bazi.ganzhi_date.year
    analyzer: RelationshipAnalyzer = RelationshipAnalyzer(chart)
    transits: TransitAnalysis = analyzer.transits

    with self.subTest('basic info correctness'):
      self.assertEqual(bazi.year_pillar, Ganzhi.from_str('庚子'))
      self.assertEqual(bazi.month_pillar, Ganzhi.from_str('壬午'))
      self.assertEqual(bazi.day_pillar, Ganzhi.from_str('丙午'))
      self.assertEqual(bazi.hour_pillar, Ganzhi.from_str('戊戌'))

      self.assertEqual(chart.xiaoyun[0].ganzhi, Ganzhi.from_str('丁酉'))
      self.assertEqual(next(chart.dayun).ganzhi, Ganzhi.from_str('辛巳'), 'first dayun Ganzhi')
      self.assertEqual(next(chart.dayun).ganzhi_year, 2029, 'first dayun year')

    with self.subTest('at birth'):
      at_birth: AtBirthAnalysis = analyzer.at_birth

      self.assertSetEqual(at_birth.shensha['taohua'],   set())
      self.assertSetEqual(at_birth.shensha['hongluan'], set())
      self.assertSetEqual(at_birth.shensha['hongyan'],  set()) 
      self.assertSetEqual(at_birth.shensha['tianxi'],   set())

      # 感情分析主要关心日主被合的情况，但原局日主没有被合。
      # 虽然我们不关心其他关系，但在这里还是检查一下。
      self.assertTrue(self.__check_tiangan({
        TianganRelation.生 : [frozenset({Tiangan.丙, Tiangan.戊})],
        TianganRelation.克 : [frozenset({Tiangan.丙, Tiangan.壬}),
                             frozenset({Tiangan.丙, Tiangan.庚})],
      }, at_birth.day_master_relations))

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.生 : [frozenset({Dizhi.午, Dizhi.戌})],
        DizhiRelation.克 : [frozenset({Dizhi.午, Dizhi.子})],
        DizhiRelation.半合 : [frozenset({Dizhi.午, Dizhi.戌})],
        DizhiRelation.刑 : [frozenset({Dizhi.午})],
        DizhiRelation.冲 : [frozenset({Dizhi.子, Dizhi.午})],
      }, at_birth.house_relations))

      self.assertEqual(len(at_birth.star_relations.tiangan), 0)

      self.assertTrue(self.__check_dizhi({
        DizhiRelation.克 : [frozenset({Dizhi.午, Dizhi.子}),
                           frozenset({Dizhi.戌, Dizhi.子})],
        DizhiRelation.冲 : [frozenset({Dizhi.子, Dizhi.午})],
      }, at_birth.star_relations.dizhi))

    with self.subTest('transits - shensha'):
      shensha_expected_dz: ShenshaAnalysis = {
        'taohua'   : frozenset([Dizhi.酉, Dizhi.卯]),
        'hongyan'  : frozenset([Dizhi.寅]),
        'hongluan' : frozenset([Dizhi.卯]),
        'tianxi'   : frozenset([Dizhi.酉]),
      }

      db = TransitDatabase(chart)
      for _ in range(50):
        random_year = random.randint(birth_gz_year, birth_gz_year + 200)
        random_option = TransitOptions.random()
        if not transits.support(random_year, random_option):
          continue

        transits_gz = db.ganzhis(random_year, random_option)
        transits_dz = set(gz.dizhi for gz in transits_gz)

        self.assertDictEqual(transits.shensha(random_year, random_option), {
          name : cast(frozenset[Dizhi], fs) & transits_dz
          for name, fs in shensha_expected_dz.items()
        })

    with self.subTest('transits - day master relations'):
      dm_relation_expected: dict[TianganRelation, set[Tiangan]] = {
        TianganRelation.生 : {Tiangan.戊, Tiangan.己, Tiangan.甲, Tiangan.乙},
        TianganRelation.克 : {Tiangan.壬, Tiangan.癸, Tiangan.庚, Tiangan.辛},
        TianganRelation.合 : {Tiangan.辛},
        TianganRelation.冲 : {Tiangan.壬},
      }

      db = TransitDatabase(chart)
      for year in random.sample(range(birth_gz_year, birth_gz_year + 600), 100):
        for option in TransitOptions:
          if not transits.support(year, option):
            continue

          transits_gz = db.ganzhis(year, option)
          transits_tg = set(gz.tiangan for gz in transits_gz)

          for tg_rel, tg_combos in transits.day_master_relations(year, option).items():
            expected_tg_combos = {
              frozenset([tg, bazi.day_master])
              for tg in (dm_relation_expected[tg_rel] & transits_tg)
            }
            self.assertSetEqual(set(tg_combos), expected_tg_combos)

    with self.subTest('transits - house relations'):
      house_relation_expected: dict[DizhiRelation, list[set[Dizhi]]] = {
        DizhiRelation.三会 : [{Dizhi.巳, Dizhi.未}],
        DizhiRelation.六合 : [{Dizhi.未}],
        DizhiRelation.暗合 : [{Dizhi.亥}, {Dizhi.寅}],
        DizhiRelation.通合 : [{Dizhi.亥}],
        DizhiRelation.通禄合 : [{Dizhi.亥}, {Dizhi.寅}],
        DizhiRelation.三合 : [{Dizhi.寅, Dizhi.戌}],
        DizhiRelation.半合 : [{Dizhi.寅}, {Dizhi.戌}],
        DizhiRelation.刑 : [{Dizhi.午}],
        DizhiRelation.冲 : [{Dizhi.子}],
        DizhiRelation.破 : [{Dizhi.卯}],
        DizhiRelation.害 : [{Dizhi.丑}],
        DizhiRelation.生 : [{Dizhi.戌}, {Dizhi.未}, {Dizhi.丑}, {Dizhi.辰}, {Dizhi.寅}, {Dizhi.卯}],
        DizhiRelation.克 : [{Dizhi.子}, {Dizhi.亥}, {Dizhi.申}, {Dizhi.酉}],
      }

      db = TransitDatabase(chart)
      for year in random.sample(range(birth_gz_year, birth_gz_year + 600), 100):
        for option in TransitOptions:
          if not transits.support(year, option):
            continue

          transits_gz = db.ganzhis(year, option)
          transits_dz = set(gz.dizhi for gz in transits_gz)

          house_dz = chart.house_of_relationship
          other_dz = set([bazi.year_pillar.dizhi, bazi.month_pillar.dizhi, bazi.hour_pillar.dizhi])
          house_relations = transits.house_relations(year, option)

          for dz_rel, dz_expected_list in house_relation_expected.items():
            expected_dz_combos: set[frozenset[Dizhi]] = set()
            for dz_expected in dz_expected_list:
              from_transits = dz_expected & transits_dz

              if len(dz_expected) == 1: # Non 三合、三会、三刑 cases
                if from_transits == dz_expected:
                  expected_dz_combos.add(frozenset({house_dz} | dz_expected))

              else: # 三合、三会、三刑 cases
                assert len(dz_expected) == 2
                if from_transits == dz_expected:
                  expected_dz_combos.add(frozenset({house_dz} | dz_expected))
                elif len(from_transits) == 1:
                  from_other_dz = dz_expected & other_dz
                  if from_other_dz | from_transits == dz_expected:
                    expected_dz_combos.add(frozenset({house_dz} | dz_expected))

            if len(expected_dz_combos) == 0:
              self.assertNotIn(dz_rel, house_relations)
            else:
              self.assertSetEqual(set(house_relations[dz_rel]), expected_dz_combos)

    with self.subTest('transits - star relations'):
      self.assertEqual(chart.relationship_stars.tiangan, Tiangan.癸)
      self.assertSetEqual(set(chart.relationship_stars.dizhi), {Dizhi.子})

      db = TransitDatabase(chart)
      for year in random.sample(range(birth_gz_year, birth_gz_year + 600), 100):
        for option in TransitOptions:
          if not transits.support(year, option):
            continue

          transits_gz = db.ganzhis(year, option)
          transits_tg = set(gz.tiangan for gz in transits_gz)
          transits_dz = set(gz.dizhi for gz in transits_gz)

          # Test TRANSITS_ONLY
          transits_only_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.TRANSITS_ONLY)
          expected_transits_only_tg_star_relations = TianganUtils.discover(list(transits_tg)).filter(
            lambda _, combo : Tiangan.癸 in combo
          )
          expected_transits_only_dz_star_relations = DizhiUtils.discover(list(transits_dz)).filter(
            lambda _, combo : Dizhi.子 in combo
          )

          self.assertTrue(_equal(transits_only_star_relations.tiangan, expected_transits_only_tg_star_relations))
          self.assertTrue(_equal(transits_only_star_relations.dizhi, expected_transits_only_dz_star_relations))

          # Test MUTUAL
          mutual_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.MUTUAL)
          expected_mutual_tg_star_relations = TianganUtils.discover_mutual(
            bazi.four_tiangans, list(transits_tg)
          ).filter(
            lambda _, combo : Tiangan.癸 in combo
          )
          expected_mutual_dz_star_relations = DizhiUtils.discover_mutual(
            bazi.four_dizhis, list(transits_dz)
          ).filter(
            lambda _, combo : Dizhi.子 in combo
          )

          self.assertTrue(_equal(mutual_star_relations.tiangan, expected_mutual_tg_star_relations))
          self.assertTrue(_equal(mutual_star_relations.dizhi, expected_mutual_dz_star_relations))

          # Test ALL
          all_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.ALL)
          expected_all_tg_star_relations = expected_transits_only_tg_star_relations.merge(expected_mutual_tg_star_relations)
          expected_all_dz_star_relations = expected_transits_only_dz_star_relations.merge(expected_mutual_dz_star_relations)

          self.assertTrue(_equal(all_star_relations.tiangan, expected_all_tg_star_relations))
          self.assertTrue(_equal(all_star_relations.dizhi, expected_all_dz_star_relations))

          self.assertTrue(_equal(all_star_relations.tiangan, TianganUtils.discover(
            list(transits_tg) + list(bazi.four_tiangans)
          ).filter(
            lambda _, combo : Tiangan.癸 in combo and len(combo.intersection(transits_tg)) > 0
          )))
          self.assertTrue(_equal(all_star_relations.dizhi, DizhiUtils.discover(
            list(transits_dz) + list(bazi.four_dizhis)
          ).filter(
            lambda _, combo : Dizhi.子 in combo and len(combo.intersection(transits_dz)) > 0
          )))

    with self.subTest('transits - zhengyin and star'):
      def is_zhengyin(tg_or_dz: Union[Tiangan, Dizhi]) -> bool:
        return Shishen.正印 is BaziUtils.shishen(bazi.day_master, tg_or_dz)
      
      def is_star(tg_or_dz: Union[Tiangan, Dizhi]) -> bool:
        return Shishen.正官 is BaziUtils.shishen(bazi.day_master, tg_or_dz)

      self.assertTrue(is_star(Tiangan.癸))
      self.assertTrue(is_star(Dizhi.子))
      self.assertTrue(is_zhengyin(Tiangan.乙))
      self.assertTrue(is_zhengyin(Dizhi.卯))      

      db = TransitDatabase(chart)
      for year in random.sample(range(birth_gz_year, birth_gz_year + 600), 100):
        for option in TransitOptions:
          if not transits.support(year, option):
            continue

          transits_gz = db.ganzhis(year, option)
          transits_tg = set(gz.tiangan for gz in transits_gz)
          transits_dz = set(gz.dizhi for gz in transits_gz)

          zhengyin_result = transits.zhengyin(year, option)
          self.assertEqual(zhengyin_result.tiangan, any(is_zhengyin(tg) for tg in transits_tg))
          self.assertEqual(zhengyin_result.dizhi, any(is_zhengyin(dz) for dz in transits_dz))

          star_result = transits.star(year, option)
          self.assertEqual(star_result.tiangan, any(is_star(tg) for tg in transits_tg))
          self.assertEqual(star_result.dizhi, any(is_star(dz) for dz in transits_dz))


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.parametrize('bazi', [Bazi.random() for _ in range(5)])
def test_random_cases(bazi: Bazi) -> None:
  logger.debug(f'birth time: {bazi.solar_datetime}, gender: {bazi.gender}, precision: {bazi.precision}')
  logger.debug(f'year: {bazi.year_pillar}, month: {bazi.month_pillar}, day: {bazi.day_pillar}, hour: {bazi.hour_pillar}')

  chart = BaziChart(bazi)
  y_dz, m_dz, d_dz, h_dz = bazi.four_dizhis
  house = chart.house_of_relationship

  db = TransitDatabase(chart)
  analyzer: RelationshipAnalyzer = RelationshipAnalyzer(chart)
  transits: TransitAnalysis = analyzer.transits

  # basic info
  dm: Tiangan = bazi.day_master
  star: Shishen = Shishen.正财 if bazi.gender is BaziGender.MALE else Shishen.正官

  assert star is BaziUtils.shishen(dm, chart.relationship_stars.tiangan)
  for star_dz in chart.relationship_stars.dizhi:
    assert star is BaziUtils.shishen(dm, star_dz)

  # shensha
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    for option in TransitOptions:
      if not transits.support(year, option):
        continue

      transits_gz = db.ganzhis(year, option)
      transits_dz_set = set(gz.dizhi for gz in transits_gz)

      def __taohua(dz: Dizhi) -> bool:
        return ShenshaUtils.taohua(y_dz, dz) or ShenshaUtils.taohua(d_dz, dz)
      
      expected_taohua:   set[Dizhi] = set(filter(__taohua, transits_dz_set))
      expected_hongyan:  set[Dizhi] = set(filter(lambda dz : ShenshaUtils.hongyan(dm, dz), transits_dz_set))
      expected_hongluan: set[Dizhi] = set(filter(lambda dz : ShenshaUtils.hongluan(y_dz, dz), transits_dz_set))
      expected_tianxi:   set[Dizhi] = set(filter(lambda dz : ShenshaUtils.tianxi(y_dz, dz), transits_dz_set))

      shensha = transits.shensha(year, option)
      assert expected_taohua == shensha['taohua']
      assert expected_hongyan == shensha['hongyan']
      assert expected_hongluan == shensha['hongluan']
      assert expected_tianxi == shensha['tianxi']

  # day master and house relations
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    for option in TransitOptions:
      if not transits.support(year, option):
        continue

      transits_gz = db.ganzhis(year, option)
      transits_tg_set = set(gz.tiangan for gz in transits_gz)
      transits_dz_set = set(gz.dizhi for gz in transits_gz)

      expected_tg_relations = TianganUtils.discover_mutual([bazi.day_master], list(transits_tg_set))
      expected_dz_relations = DizhiUtils.discover_mutual(
        [house], list(transits_dz_set)
      ).merge(
        DizhiUtils.discover_mutual(
          [house], list(transits_dz_set) + [y_dz, m_dz, h_dz]
        ).filter(
          lambda _, combo : len(combo) == 3
        ).filter(
          lambda _, combo : not combo.isdisjoint(filter(lambda dz : dz is not house, transits_dz_set))
        )
      )

      tg_relations = transits.day_master_relations(year, option)
      dz_relations = transits.house_relations(year, option)

      assert _equal(expected_tg_relations, tg_relations)
      assert _equal(expected_dz_relations, dz_relations)

      def __trirelation(expected_combo: Iterable[Dizhi]) -> bool:
        __dz_set = set(expected_combo)
        assert len(__dz_set) == 3
        if house not in __dz_set:
          return False

        other_dz = __dz_set - {house}
        assert len(other_dz) == 2

        if other_dz.isdisjoint(transits_dz_set):
          return False
        
        __dz_set = transits_dz_set.union([y_dz, m_dz, h_dz])
        count = sum(map(lambda dz : dz in __dz_set, other_dz))
        return count == 2
      
      # 三刑 cases
      expected_sanxing_combos: set[frozenset[Dizhi]] = set(
        frozenset(dz_tuple) 
        for dz_tuple in DizhiRules.DIZHI_XING.loose 
        if len(dz_tuple) == 3 and __trirelation(dz_tuple)
      )
      filtered_dz_relations = dz_relations.filter(
        lambda rel, combo : rel is DizhiRelation.刑 and len(combo) == 3
      )

      if len(expected_sanxing_combos) == 0:
        assert DizhiRelation.刑 not in filtered_dz_relations
      else:
        assert len(expected_sanxing_combos) == len(filtered_dz_relations[DizhiRelation.刑])
        for c in expected_sanxing_combos:
          assert c in filtered_dz_relations[DizhiRelation.刑]

      # 三合 cases
      expected_sanhe_combos: set[frozenset[Dizhi]] = set(dz_fs for dz_fs in DizhiRules.DIZHI_SANHE if __trirelation(dz_fs))
      if len(expected_sanhe_combos) == 0:
        assert DizhiRelation.三合 not in dz_relations
      else:
        assert len(expected_sanhe_combos) == len(dz_relations[DizhiRelation.三合])
        for c in expected_sanhe_combos:
          assert c in dz_relations[DizhiRelation.三合]

      # 三会 cases
      expected_sanhui_combos: set[frozenset[Dizhi]] = set(dz_fs for dz_fs in DizhiRules.DIZHI_SANHUI if __trirelation(dz_fs))
      if len(expected_sanhui_combos) == 0:
        assert DizhiRelation.三会 not in dz_relations
      else:
        assert len(expected_sanhui_combos) == len(dz_relations[DizhiRelation.三会])
        for c in expected_sanhui_combos:
          assert c in dz_relations[DizhiRelation.三会]

      # 自刑 cases
      if house in [Dizhi.午, Dizhi.亥, Dizhi.辰]:
        if house in transits_dz_set:
          assert frozenset({house}) in dz_relations[DizhiRelation.刑]

  # star relations
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    for option in TransitOptions:
      if not transits.support(year, option):
        continue

      transits_gz = db.ganzhis(year, option)
      transits_tg_list = list(gz.tiangan for gz in transits_gz)
      transits_dz_list = list(gz.dizhi for gz in transits_gz)

      stars = chart.relationship_stars

      # TRANSITS_ONLY
      transits_only_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.TRANSITS_ONLY)

      expected_transits_only_tg = TianganUtils.TianganRelationDiscovery({})
      if stars.tiangan in transits_tg_list:
        tg_list = transits_tg_list.copy()
        tg_list.remove(stars.tiangan)
        expected_transits_only_tg = TianganUtils.discover_mutual([stars.tiangan], tg_list)

      expected_transits_only_dz = DizhiUtils.discover(transits_dz_list).filter(
        lambda _, combo : len(combo.intersection(stars.dizhi)) > 0
      )

      assert _equal(transits_only_star_relations.tiangan, expected_transits_only_tg)
      assert _equal(transits_only_star_relations.dizhi, expected_transits_only_dz)

      # MUTUAL
      mutual_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.MUTUAL)

      expected_mutual_tg = TianganUtils.discover_mutual(
        bazi.four_tiangans, transits_tg_list
      ).filter(
        lambda _, combo : stars.tiangan in combo
      )

      expected_mutual_dz = DizhiUtils.discover_mutual(
        bazi.four_dizhis, transits_dz_list
      ).filter(
        lambda _, combo : len(combo.intersection(stars.dizhi)) > 0
      )

      assert _equal(mutual_star_relations.tiangan, expected_mutual_tg)
      assert _equal(mutual_star_relations.dizhi, expected_mutual_dz)

      # ALL
      all_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.ALL)

      assert _equal(all_star_relations.tiangan, expected_transits_only_tg.merge(expected_mutual_tg))
      assert _equal(all_star_relations.dizhi, expected_transits_only_dz.merge(expected_mutual_dz))

      assert _equal(
        all_star_relations.tiangan, 
        TianganUtils.discover(
          transits_tg_list + list(bazi.four_tiangans)
        ).filter(
          lambda _, combo : stars.tiangan in combo
        ).filter(
          lambda _, combo : len(combo.intersection(transits_tg_list)) > 0
        )
      )

      assert _equal(
        all_star_relations.dizhi, 
        DizhiUtils.discover(
          transits_dz_list + list(bazi.four_dizhis)
        ).filter(
          lambda _, combo : len(combo.intersection(stars.dizhi)) > 0
        ).filter(
          lambda _, combo : len(combo.intersection(transits_dz_list)) > 0
        )
      )

  # zhengyin and star methods
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    for option in TransitOptions:
      if not transits.support(year, option):
        continue

      transits_gz = db.ganzhis(year, option)
      transits_tg_set = set(gz.tiangan for gz in transits_gz)
      transits_dz_set = set(gz.dizhi for gz in transits_gz)

      zhengyin_results = transits.zhengyin(year, option)
      assert zhengyin_results.tiangan == any(BaziUtils.shishen(dm, tg) is Shishen.正印 for tg in transits_tg_set)
      assert zhengyin_results.dizhi == any(BaziUtils.shishen(dm, dz) is Shishen.正印 for dz in transits_dz_set)

      stars = chart.relationship_stars
      star_results = transits.star(year, option)
      assert star_results.tiangan == (stars.tiangan in transits_tg_set)
      assert star_results.dizhi == (not transits_dz_set.isdisjoint(stars.dizhi))
