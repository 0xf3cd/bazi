# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_analysis.py

import pytest

import random

from datetime import datetime
from typing import cast

from src.defines import Tiangan, Dizhi, Ganzhi, TianganRelation, DizhiRelation, Shishen
from src.utils import tiangan_utils, dizhi_utils, bazi_utils, shensha_utils
from src.bazi import Bazi, BaziGender, BaziPrecision
from src.bazi_chart import BaziChart
from src.transits import TransitMoment, TransitOptions, TransitDatabase
from src.analyzer.relationship import RelationshipAnalyzer, ShenshaAnalysis, TransitAnalysis, AtBirthAnalysis
from src.rules import DizhiRules


DiscoveryType = tiangan_utils.TianganRelationDiscovery | dizhi_utils.DizhiRelationDiscovery
def _equal(d1: DiscoveryType, d2: DiscoveryType) -> bool:
  assert type(d1) is type(d2)
  if set(d1.keys()) != set(d2.keys()):
    return False
  for rel, combos in d1.items():
    if set(combos) != set(d2[rel]):  # type: ignore
      return False
  return True

def _check_tiangan(expected: dict[TianganRelation, list[tiangan_utils.TianganCombo]], actual: tiangan_utils.TianganRelationDiscovery) -> bool:
  for rel, expected_combos in expected.items():
    if rel not in actual:
      return False
    for combo in expected_combos:
      if combo not in actual[rel]:
        return False
  return True

def _check_dizhi(expected: dict[DizhiRelation, list[dizhi_utils.DizhiCombo]], actual: dizhi_utils.DizhiRelationDiscovery) -> bool:
  for rel, expected_combos in expected.items():
    if rel not in actual:
      return False
    for combo in expected_combos:
      if combo not in actual[rel]:
        return False
  return True

@pytest.mark.integration
def test_case1() -> None:
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

  # basic info correctness
  assert bazi.year_pillar == Ganzhi.from_str('甲子')
  assert bazi.month_pillar == Ganzhi.from_str('丁卯')
  assert bazi.day_pillar == Ganzhi.from_str('乙丑')
  assert bazi.hour_pillar == Ganzhi.from_str('壬午')

  assert chart.xiaoyun[0].ganzhi == Ganzhi.from_str('癸未')
  assert next(chart.dayun).ganzhi == Ganzhi.from_str('戊辰'), 'first dayun Ganzhi'
  assert next(chart.dayun).ganzhi_year == 1985, 'first dayun year'

  assert chart.relationship_stars.tiangan == Tiangan.戊
  assert set(chart.relationship_stars.dizhi) == {Dizhi.辰, Dizhi.戌}

  # at birth
  at_birth: AtBirthAnalysis = analyzer.at_birth

  assert at_birth.shensha['taohua']   == {Dizhi.午}
  assert at_birth.shensha['hongluan'] == {Dizhi.卯}
  # 问真八字以乙日主见午为红艳，但 `ShenshaRules.HONGYAN` 中以乙日主见申为红艳，所以这里为空。
  assert at_birth.shensha['hongyan']  == set()
  assert at_birth.shensha['tianxi']   == set()
  assert at_birth.shensha['yima']     == set()

  # 感情分析主要关心日主被合的情况，但原局日主没有被合。
  # 虽然我们不关心相生关系，但在这里还是检查一下。
  assert _check_tiangan({
    TianganRelation.生 : [frozenset({Tiangan.乙, Tiangan.丁}),
                         frozenset({Tiangan.乙, Tiangan.壬})],
  }, at_birth.day_master_relations)

  assert _check_dizhi({
    DizhiRelation.六合 : [frozenset({Dizhi.子, Dizhi.丑})],
    DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
    DizhiRelation.生 : [frozenset({Dizhi.午, Dizhi.丑})],
    DizhiRelation.克 : [frozenset({Dizhi.丑, Dizhi.子}),
                       frozenset({Dizhi.卯, Dizhi.丑})],
  }, at_birth.house_relations)

  # 原局无正财星，所以配偶星的关系分析为空。
  assert len(at_birth.star_relations.tiangan) == 0
  assert len(at_birth.star_relations.dizhi) == 0

  # 1990
  assert set(db.ganzhis(TransitMoment(1990), TransitOptions.DAYUN_LIUNIAN)) == {Ganzhi.from_str('戊辰'), Ganzhi.from_str('庚午')}

  shensha = transits.shensha(1990, TransitOptions.DAYUN_LIUNIAN)
  assert shensha['taohua']   == {Dizhi.午}
  assert shensha['hongluan'] == set()
  assert shensha['hongyan']  == set()
  assert shensha['tianxi']   == set()
  assert shensha['yima']     == set()

  assert _check_tiangan({
    TianganRelation.合 : [frozenset({Tiangan.乙, Tiangan.庚})],
    TianganRelation.克 : [frozenset({Tiangan.庚, Tiangan.乙}),
                         frozenset({Tiangan.乙, Tiangan.戊})],
  }, transits.day_master_relations(1990, TransitOptions.DAYUN_LIUNIAN))

  assert _check_dizhi({
    DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
    DizhiRelation.破 : [frozenset({Dizhi.辰, Dizhi.丑})],
    DizhiRelation.生 : [frozenset({Dizhi.午, Dizhi.丑})],
  }, transits.house_relations(1990, TransitOptions.DAYUN_LIUNIAN))

  star_relations_all = transits.star_relations(1990, TransitOptions.DAYUN_LIUNIAN) # level is `ALL` by default.

  assert _check_tiangan({
    TianganRelation.生 : [frozenset({Tiangan.戊, Tiangan.庚}),
                         frozenset({Tiangan.戊, Tiangan.丁})],
    TianganRelation.克 : [frozenset({Tiangan.甲, Tiangan.戊}),
                         frozenset({Tiangan.乙, Tiangan.戊}),
                         frozenset({Tiangan.壬, Tiangan.戊})],
  }, star_relations_all.tiangan)

  assert _check_dizhi({
    DizhiRelation.生 : [frozenset({Dizhi.午, Dizhi.辰})],
    DizhiRelation.克 : [frozenset({Dizhi.辰, Dizhi.子}),
                       frozenset({Dizhi.卯, Dizhi.辰})],
    DizhiRelation.破 : [frozenset({Dizhi.辰, Dizhi.丑})],
    DizhiRelation.害 : [frozenset({Dizhi.辰, Dizhi.卯})],
    DizhiRelation.半合 : [frozenset({Dizhi.子, Dizhi.辰})],
  }, star_relations_all.dizhi)

  assert not transits.zhengyin(1990, TransitOptions.DAYUN_LIUNIAN).tiangan
  assert not transits.zhengyin(1990, TransitOptions.DAYUN_LIUNIAN).dizhi

  assert transits.star(1990, TransitOptions.DAYUN_LIUNIAN).tiangan
  assert transits.star(1990, TransitOptions.DAYUN_LIUNIAN).dizhi
  assert transits.star(1990, TransitOptions.DAYUN).tiangan
  assert transits.star(1990, TransitOptions.DAYUN).dizhi
  assert not transits.star(1990, TransitOptions.LIUNIAN).tiangan
  assert not transits.star(1990, TransitOptions.LIUNIAN).dizhi

  # 2018
  assert set(db.ganzhis(TransitMoment(2018), TransitOptions.DAYUN_LIUNIAN)) == {Ganzhi.from_str('辛未'), Ganzhi.from_str('戊戌')}

  shensha = transits.shensha(2018, TransitOptions.DAYUN_LIUNIAN)
  assert shensha['taohua']   == set()
  assert shensha['hongluan'] == set()
  assert shensha['hongyan']  == set()
  assert shensha['tianxi']   == set()
  assert shensha['yima']     == set()

  assert _check_tiangan({
    TianganRelation.克 : [frozenset({Tiangan.乙, Tiangan.辛}),
                         frozenset({Tiangan.乙, Tiangan.戊})],
  }, transits.day_master_relations(2018, TransitOptions.DAYUN_LIUNIAN))

  assert _check_dizhi({
    DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未, Dizhi.戌}),
                       frozenset({Dizhi.丑, Dizhi.未})],
    DizhiRelation.冲 : [frozenset({Dizhi.丑, Dizhi.未})],
  }, transits.house_relations(2018, TransitOptions.DAYUN_LIUNIAN))

  star_relations_all = transits.star_relations(2018, TransitOptions.DAYUN_LIUNIAN) # level is `ALL` by default.

  assert _check_tiangan({
    TianganRelation.克 : [frozenset({Tiangan.甲, Tiangan.戊}),
                         frozenset({Tiangan.壬, Tiangan.戊})],
  }, star_relations_all.tiangan)

  assert _check_dizhi({
    DizhiRelation.六合 : [frozenset({Dizhi.戌, Dizhi.卯})],
    DizhiRelation.半合 : [frozenset({Dizhi.戌, Dizhi.午})],
    DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未, Dizhi.戌})],
    DizhiRelation.破 : [frozenset({Dizhi.戌, Dizhi.未})],
    DizhiRelation.生 : [frozenset({Dizhi.戌, Dizhi.午})],
    DizhiRelation.克 : [frozenset({Dizhi.戌, Dizhi.卯}),
                       frozenset({Dizhi.戌, Dizhi.子})],
  }, star_relations_all.dizhi)

  assert not transits.zhengyin(2018, TransitOptions.DAYUN_LIUNIAN).tiangan
  assert not transits.zhengyin(2018, TransitOptions.DAYUN_LIUNIAN).dizhi

  assert transits.star(2018, TransitOptions.DAYUN_LIUNIAN).tiangan
  assert transits.star(2018, TransitOptions.DAYUN_LIUNIAN).dizhi
  assert transits.star(2018, TransitOptions.LIUNIAN).tiangan
  assert transits.star(2018, TransitOptions.LIUNIAN).dizhi
  assert not transits.star(2018, TransitOptions.DAYUN).tiangan
  assert not transits.star(2018, TransitOptions.DAYUN).dizhi

  # 2031
  assert set(db.ganzhis(TransitMoment(2031), TransitOptions.DAYUN_LIUNIAN)) == {Ganzhi.from_str('辛亥'), Ganzhi.from_str('壬申')}

  shensha = transits.shensha(2031, TransitOptions.DAYUN_LIUNIAN)
  assert shensha['taohua']   == set()
  assert shensha['hongluan'] == set()
  assert shensha['hongyan']  == {Dizhi.申}
  assert shensha['tianxi']   == set()
  assert shensha['yima']     == {Dizhi.亥}

  assert _check_tiangan({
    TianganRelation.克 : [frozenset({Tiangan.乙, Tiangan.辛})],
    TianganRelation.生 : [frozenset({Tiangan.乙, Tiangan.壬})],
  }, transits.day_master_relations(2031, TransitOptions.DAYUN_LIUNIAN))

  assert _check_dizhi({
    DizhiRelation.生 : [frozenset({Dizhi.申, Dizhi.丑})],
    DizhiRelation.克 : [frozenset({Dizhi.丑, Dizhi.亥})],
    DizhiRelation.三会 : [frozenset({Dizhi.亥, Dizhi.子, Dizhi.丑})],
  }, transits.house_relations(2031, TransitOptions.DAYUN_LIUNIAN))

  star_relations_all = transits.star_relations(2031, TransitOptions.DAYUN_LIUNIAN) # level is `ALL` by default.
  assert 0 == len(star_relations_all.tiangan)
  assert 0 == len(star_relations_all.dizhi)

  assert transits.zhengyin(2031, TransitOptions.DAYUN_LIUNIAN).tiangan
  assert transits.zhengyin(2031, TransitOptions.DAYUN_LIUNIAN).dizhi

  assert not transits.star(2031, TransitOptions.DAYUN_LIUNIAN).tiangan
  assert not transits.star(2031, TransitOptions.DAYUN_LIUNIAN).dizhi

@pytest.mark.integration
def test_case2() -> None:
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

  # basic info correctness
  assert bazi.year_pillar == Ganzhi.from_str('庚子')
  assert bazi.month_pillar == Ganzhi.from_str('壬午')
  assert bazi.day_pillar == Ganzhi.from_str('丙午')
  assert bazi.hour_pillar == Ganzhi.from_str('戊戌')

  assert chart.xiaoyun[0].ganzhi == Ganzhi.from_str('丁酉')
  assert next(chart.dayun).ganzhi == Ganzhi.from_str('辛巳'), 'first dayun Ganzhi'
  assert next(chart.dayun).ganzhi_year == 2029, 'first dayun year'

  # at birth
  at_birth: AtBirthAnalysis = analyzer.at_birth

  assert at_birth.shensha['taohua']   == set()
  assert at_birth.shensha['hongluan'] == set()
  assert at_birth.shensha['hongyan']  == set()
  assert at_birth.shensha['tianxi']   == set()
  assert at_birth.shensha['yima']     == set()

  # 感情分析主要关心日主被合的情况，但原局日主没有被合。
  # 虽然我们不关心其他关系，但在这里还是检查一下。
  assert _check_tiangan({
    TianganRelation.生 : [frozenset({Tiangan.丙, Tiangan.戊})],
    TianganRelation.克 : [frozenset({Tiangan.丙, Tiangan.壬}),
                         frozenset({Tiangan.丙, Tiangan.庚})],
  }, at_birth.day_master_relations)

  assert _check_dizhi({
    DizhiRelation.生 : [frozenset({Dizhi.午, Dizhi.戌})],
    DizhiRelation.克 : [frozenset({Dizhi.午, Dizhi.子})],
    DizhiRelation.半合 : [frozenset({Dizhi.午, Dizhi.戌})],
    DizhiRelation.刑 : [frozenset({Dizhi.午})],
    DizhiRelation.冲 : [frozenset({Dizhi.子, Dizhi.午})],
  }, at_birth.house_relations)

  assert len(at_birth.star_relations.tiangan) == 0

  assert _check_dizhi({
    DizhiRelation.克 : [frozenset({Dizhi.午, Dizhi.子}),
                       frozenset({Dizhi.戌, Dizhi.子})],
    DizhiRelation.冲 : [frozenset({Dizhi.子, Dizhi.午})],
  }, at_birth.star_relations.dizhi)

  # transits - shensha
  shensha_expected_dz: ShenshaAnalysis = {
    'taohua'   : frozenset([Dizhi.酉, Dizhi.卯]),
    'hongyan'  : frozenset([Dizhi.寅]),
    'hongluan' : frozenset([Dizhi.卯]),
    'tianxi'   : frozenset([Dizhi.酉]),
    'yima'     : frozenset([Dizhi.寅, Dizhi.申]),
  }

  db = TransitDatabase(chart)
  for _ in range(50):
    random_year = random.randint(birth_gz_year, birth_gz_year + 200)
    random_option = TransitOptions.random()
    if not transits.support(random_year, random_option):
      continue

    transits_gz = db.ganzhis(TransitMoment(random_year), random_option)
    transits_dz = {gz.dizhi for gz in transits_gz}

    assert transits.shensha(random_year, random_option) == {
      name : cast(frozenset[Dizhi], fs) & transits_dz
      for name, fs in shensha_expected_dz.items()
    }

  # transits - day master relations
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

      transits_gz = db.ganzhis(TransitMoment(year), option)
      transits_tg = {gz.tiangan for gz in transits_gz}

      for tg_rel, tg_combos in transits.day_master_relations(year, option).items():
        expected_tg_combos = {
          frozenset([tg, bazi.day_master])
          for tg in (dm_relation_expected[tg_rel] & transits_tg)
        }
        assert set(tg_combos) == expected_tg_combos

  # transits - house relations
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

      transits_gz = db.ganzhis(TransitMoment(year), option)
      transits_dz = {gz.dizhi for gz in transits_gz}

      house_dz = chart.house_of_relationship
      other_dz = {bazi.year_pillar.dizhi, bazi.month_pillar.dizhi, bazi.hour_pillar.dizhi}
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
          assert dz_rel not in house_relations
        else:
          assert set(house_relations[dz_rel]) == expected_dz_combos

  # transits - star relations
  assert chart.relationship_stars.tiangan == Tiangan.癸
  assert set(chart.relationship_stars.dizhi) == {Dizhi.子}

  db = TransitDatabase(chart)
  for year in random.sample(range(birth_gz_year, birth_gz_year + 600), 100):
    for option in TransitOptions:
      if not transits.support(year, option):
        continue

      transits_gz = db.ganzhis(TransitMoment(year), option)
      transits_tg = {gz.tiangan for gz in transits_gz}
      transits_dz = {gz.dizhi for gz in transits_gz}

      # Test TRANSITS_ONLY
      transits_only_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.TRANSITS_ONLY)
      expected_transits_only_tg_star_relations = tiangan_utils.discover(list(transits_tg)).filter(
        lambda _, combo : Tiangan.癸 in combo
      )
      expected_transits_only_dz_star_relations = dizhi_utils.discover(list(transits_dz)).filter(
        lambda _, combo : Dizhi.子 in combo
      )

      assert _equal(transits_only_star_relations.tiangan, expected_transits_only_tg_star_relations)
      assert _equal(transits_only_star_relations.dizhi, expected_transits_only_dz_star_relations)

      # Test MUTUAL
      mutual_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.MUTUAL)
      expected_mutual_tg_star_relations = tiangan_utils.discover_mutual(chart.bazi.four_tiangans, list(transits_tg)).filter(
        lambda _, combo : Tiangan.癸 in combo
      )
      expected_mutual_dz_star_relations = dizhi_utils.discover_mutual(chart.bazi.four_dizhis, list(transits_dz)).filter(
        lambda _, combo : Dizhi.子 in combo
      )

      assert _equal(mutual_star_relations.tiangan, expected_mutual_tg_star_relations)
      assert _equal(mutual_star_relations.dizhi, expected_mutual_dz_star_relations)

      # Test ALL
      all_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.ALL)
      expected_all_tg_star_relations = expected_transits_only_tg_star_relations.merge(expected_mutual_tg_star_relations)
      expected_all_dz_star_relations = expected_transits_only_dz_star_relations.merge(expected_mutual_dz_star_relations)

      assert _equal(all_star_relations.tiangan, expected_all_tg_star_relations)
      assert _equal(all_star_relations.dizhi, expected_all_dz_star_relations)

      assert _equal(all_star_relations.tiangan, tiangan_utils.discover(list(transits_tg) + list(bazi.four_tiangans)).filter(
        lambda _, combo : Tiangan.癸 in combo and not combo.isdisjoint(transits_tg)
      ))
      assert _equal(all_star_relations.dizhi, dizhi_utils.discover(list(transits_dz) + list(bazi.four_dizhis)).filter(
        lambda _, combo : Dizhi.子 in combo and not combo.isdisjoint(transits_dz)
      ))

  # transits - zhengyin and star
  def is_zhengyin(tg_or_dz: Tiangan | Dizhi) -> bool:
    return Shishen.正印 is bazi_utils.shishen(bazi.day_master, tg_or_dz)

  def is_star(tg_or_dz: Tiangan | Dizhi) -> bool:
    return Shishen.正官 is bazi_utils.shishen(bazi.day_master, tg_or_dz)

  assert is_star(Tiangan.癸)
  assert is_star(Dizhi.子)
  assert is_zhengyin(Tiangan.乙)
  assert is_zhengyin(Dizhi.卯)

  db = TransitDatabase(chart)
  for year in random.sample(range(birth_gz_year, birth_gz_year + 600), 100):
    for option in TransitOptions:
      if not transits.support(year, option):
        continue

      transits_gz = db.ganzhis(TransitMoment(year), option)
      transits_tg = {gz.tiangan for gz in transits_gz}
      transits_dz = {gz.dizhi for gz in transits_gz}

      zhengyin_result = transits.zhengyin(year, option)
      assert zhengyin_result.tiangan == any(is_zhengyin(tg) for tg in transits_tg)
      assert zhengyin_result.dizhi == any(is_zhengyin(dz) for dz in transits_dz)

      star_result = transits.star(year, option)
      assert star_result.tiangan == any(is_star(tg) for tg in transits_tg)
      assert star_result.dizhi == any(is_star(dz) for dz in transits_dz)


@pytest.mark.integration
@pytest.mark.parametrize('bazi', [Bazi.random() for _ in range(5)])
def test_random_cases(bazi: Bazi) -> None:
  chart = BaziChart(bazi)
  y_dz, m_dz, d_dz, h_dz = bazi.four_dizhis
  house = chart.house_of_relationship

  db = TransitDatabase(chart)
  analyzer: RelationshipAnalyzer = RelationshipAnalyzer(chart)
  transits: TransitAnalysis = analyzer.transits

  # basic info
  dm: Tiangan = bazi.day_master
  star: Shishen = Shishen.正财 if bazi.gender is BaziGender.MALE else Shishen.正官

  assert star is bazi_utils.shishen(dm, chart.relationship_stars.tiangan)
  for star_dz in chart.relationship_stars.dizhi:
    assert star is bazi_utils.shishen(dm, star_dz)

  # shensha
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    for option in TransitOptions:
      if not transits.support(year, option):
        continue

      transits_gz = db.ganzhis(TransitMoment(year), option)
      transits_dz_set = {gz.dizhi for gz in transits_gz}

      def __taohua(dz: Dizhi) -> bool:
        return shensha_utils.taohua(y_dz, dz) or shensha_utils.taohua(d_dz, dz)
      
      def __yima(dz: Dizhi) -> bool:
        return shensha_utils.yima(y_dz, dz) or shensha_utils.yima(d_dz, dz)

      expected_taohua:   set[Dizhi] = set(filter(__taohua, transits_dz_set))
      expected_hongyan:  set[Dizhi] = set(filter(lambda dz : shensha_utils.hongyan(dm, dz), transits_dz_set))
      expected_hongluan: set[Dizhi] = set(filter(lambda dz : shensha_utils.hongluan(y_dz, dz), transits_dz_set))
      expected_tianxi:   set[Dizhi] = set(filter(lambda dz : shensha_utils.tianxi(y_dz, dz), transits_dz_set))
      expected_yima:     set[Dizhi] = set(filter(__yima, transits_dz_set))

      shensha = transits.shensha(year, option)
      assert expected_taohua == shensha['taohua']
      assert expected_hongyan == shensha['hongyan']
      assert expected_hongluan == shensha['hongluan']
      assert expected_tianxi == shensha['tianxi']
      assert expected_yima == shensha['yima']

  # day master and house relations
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    for option in TransitOptions:
      if not transits.support(year, option):
        continue

      transits_gz = db.ganzhis(TransitMoment(year), option)
      transits_tg_set = {gz.tiangan for gz in transits_gz}
      transits_dz_set = {gz.dizhi for gz in transits_gz}

      expected_tg_relations = tiangan_utils.discover_mutual([chart.bazi.day_master], list(transits_tg_set))
      expected_dz_relations = dizhi_utils.discover_mutual([house], list(transits_dz_set)).merge(
        dizhi_utils.discover_mutual([house], list(transits_dz_set) + [y_dz, m_dz, h_dz]).filter(
          lambda _, combo : len(combo) == 3
        ).filter(
          lambda _, combo : not combo.isdisjoint(filter(lambda dz : dz is not house, transits_dz_set))
        )
      )

      tg_relations = transits.day_master_relations(year, option)
      dz_relations = transits.house_relations(year, option)

      assert _equal(expected_tg_relations, tg_relations)
      assert _equal(expected_dz_relations, dz_relations)

      if house in [Dizhi.午, Dizhi.亥, Dizhi.辰] and house in transits_dz_set: # 自刑 cases
        assert frozenset({house}) in dz_relations[DizhiRelation.刑]

      for dz_tuple in DizhiRules.DIZHI_XING[DizhiRules.XingDef.LOOSE]: # 三刑 cases
        if len(dz_tuple) == 3 and house in dz_tuple:
          other_dz = frozenset(dz_tuple) - {house}
          assert len(other_dz) == 2
          if not transits_dz_set.isdisjoint(other_dz):
            count = sum(1 if dz in [y_dz, m_dz, h_dz] or dz in transits_dz_set else 0 for dz in other_dz)
            if count == 2:
              assert frozenset(dz_tuple) in dz_relations[DizhiRelation.刑]
        
      for dz_fs in DizhiRules.DIZHI_SANHE: # 三合 cases
        if house in dz_fs:
          other_dz = dz_fs - {house}
          if other_dz & transits_dz_set == other_dz:
            assert dz_fs in dz_relations[DizhiRelation.三合]

      for dz_fs in DizhiRules.DIZHI_SANHUI: # 三会 cases
        if house in dz_fs:
          other_dz = dz_fs - {house}
          if other_dz & transits_dz_set == other_dz:
            assert dz_fs in dz_relations[DizhiRelation.三会]

  # star relations
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    for option in TransitOptions:
      if not transits.support(year, option):
        continue

      transits_gz = db.ganzhis(TransitMoment(year), option)
      transits_tg_list = [gz.tiangan for gz in transits_gz]
      transits_dz_list = [gz.dizhi for gz in transits_gz]

      stars = chart.relationship_stars

      # TRANSITS_ONLY
      transits_only_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.TRANSITS_ONLY)

      expected_transits_only_tg = tiangan_utils.TianganRelationDiscovery({})
      if stars.tiangan in transits_tg_list:
        tg_list = transits_tg_list.copy()
        tg_list.remove(stars.tiangan)
        expected_transits_only_tg = tiangan_utils.discover_mutual([stars.tiangan], tg_list)

      expected_transits_only_dz = dizhi_utils.discover(transits_dz_list).filter(
        lambda _, combo : not combo.isdisjoint(stars.dizhi)
      )

      assert _equal(transits_only_star_relations.tiangan, expected_transits_only_tg)
      assert _equal(transits_only_star_relations.dizhi, expected_transits_only_dz)

      # MUTUAL
      mutual_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.MUTUAL)

      expected_mutual_tg = tiangan_utils.discover_mutual(bazi.four_tiangans, transits_tg_list).filter(
        lambda _, combo : stars.tiangan in combo
      )

      expected_mutual_dz = dizhi_utils.discover_mutual(bazi.four_dizhis, transits_dz_list).filter(
        lambda _, combo : len(combo & set(stars.dizhi)) > 0
      )

      assert _equal(mutual_star_relations.tiangan, expected_mutual_tg)
      assert _equal(mutual_star_relations.dizhi, expected_mutual_dz)

      # ALL
      all_star_relations = transits.star_relations(year, option, level=TransitAnalysis.Level.ALL)

      assert _equal(all_star_relations.tiangan, expected_transits_only_tg.merge(expected_mutual_tg))
      assert _equal(all_star_relations.dizhi, expected_transits_only_dz.merge(expected_mutual_dz))

      assert _equal(all_star_relations.tiangan, tiangan_utils.discover(transits_tg_list + list(bazi.four_tiangans)).filter(
        lambda _, combo : stars.tiangan in combo
      ).filter(
        lambda _, combo : not combo.isdisjoint(transits_tg_list)
      ))

      assert _equal(all_star_relations.dizhi, dizhi_utils.discover(transits_dz_list + list(bazi.four_dizhis)).filter(
        lambda _, combo : len(combo & set(stars.dizhi)) > 0
      ).filter(
        lambda _, combo : not combo.isdisjoint(transits_dz_list)
      ))

  # zhengyin and star methods
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    for option in TransitOptions:
      if not transits.support(year, option):
        continue

      transits_gz = db.ganzhis(TransitMoment(year), option)
      transits_tg_set = {gz.tiangan for gz in transits_gz}
      transits_dz_set = {gz.dizhi for gz in transits_gz}

      zhengyin_results = transits.zhengyin(year, option)
      assert zhengyin_results.tiangan == any(bazi_utils.shishen(dm, tg) is Shishen.正印 for tg in transits_tg_set)
      assert zhengyin_results.dizhi == any(bazi_utils.shishen(dm, dz) is Shishen.正印 for dz in transits_dz_set)

      stars = chart.relationship_stars
      star_results = transits.star(year, option)
      assert star_results.tiangan == (stars.tiangan in transits_tg_set)
      assert star_results.dizhi != set(transits_dz_set).isdisjoint(stars.dizhi)
