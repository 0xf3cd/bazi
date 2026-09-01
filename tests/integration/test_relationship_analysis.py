# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relationship_analysis.py

import pytest

import random

from datetime import date, datetime
from typing import cast

from src.defines import Tiangan, Dizhi, Ganzhi, TianganRelation, DizhiRelation, Shishen
from src.utils import tiangan_utils, dizhi_utils, bazi_utils, shensha_utils
from src.bazi import Bazi, BaziGender
from src.bazi_chart import BaziChart
from src.school import KeyStem, ZaishaAnchor, ShenshaAnchorProfile, BaziSchool, BaziConfig
from src.transit_chart import TransitChart
from src.transits import TransitKind, TransitSet
from src.analyzer.relationship import RelationshipAnalyzer, ShenshaAnalysis, TransitAnalysis, AtBirthAnalysis
from src.rules import DizhiRules, ShenshaRules


pytestmark = pytest.mark.integration


'''Operand type of `_equal`: either relation-discovery flavor.'''
DiscoveryType = tiangan_utils.TianganRelationDiscovery | dizhi_utils.DizhiRelationDiscovery
def _equal(d1: DiscoveryType, d2: DiscoveryType) -> bool:
  assert type(d1) is type(d2)
  if set(d1.keys()) != set(d2.keys()):
    return False
  for rel, combos in d1.items():
    if set(combos) != set(d2[rel]):  # type: ignore
      return False
  return True


def _at_year(transit_chart: TransitChart, gz_year: int) -> TransitSet:
  transits = transit_chart.at_year(gz_year)
  assert transits is not None
  return transits


def _random_year_transits(transit_chart: TransitChart, gz_year: int) -> TransitSet:
  full_transits = _at_year(transit_chart, gz_year)
  available = tuple(full_transits)
  selected = random.sample(available, random.randint(1, len(available)))
  return full_transits.select(*selected)


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


def test_month_date_and_moment_transits_reach_relationship_analysis() -> None:
  chart = BaziChart(Bazi.create(
    '1984-04-01 11:08',
    'male',
    BaziConfig.from_values(precision='minute'),
  ))
  transit_chart = TransitChart(chart)
  month_transits = transit_chart.at_month(2024, Dizhi.寅)
  date_transits = transit_chart.at_date(date(2024, 2, 4))
  moment_transits = transit_chart.at_moment(datetime(2024, 2, 4, 18, 0))
  assert month_transits is not None
  assert date_transits is not None
  assert moment_transits is not None

  analysis = RelationshipAnalyzer(chart).transits
  for transits in (
    month_transits.select(TransitKind.LIUYUE),
    date_transits.select(TransitKind.LIURI),
    moment_transits.select(TransitKind.LIURI),
  ):
    expected = tiangan_utils.discover_mutual(
      [chart.bazi.day_master],
      tuple(gz.tiangan for gz in transits.ganzhis),
    )
    assert _equal(expected, analysis.day_master_relations(transits))


@pytest.mark.parametrize('birth_time, pillars, luming, diwang', [
  ('1980-10-15 12:00', ('庚申', '丙戌', '辛酉', '甲午'), Dizhi.戌, Dizhi.申),
  ('1984-01-10 12:00', ('癸亥', '乙丑', '癸卯', '戊午'), Dizhi.丑, Dizhi.亥),
  ('1986-04-11 12:00', ('丙寅', '壬辰', '乙酉', '壬午'), Dizhi.辰, Dizhi.寅),
  ('1989-07-16 12:00', ('己巳', '辛未', '丁丑', '丙午'), Dizhi.未, Dizhi.巳),
  ('1989-07-18 12:00', ('己巳', '辛未', '己卯', '庚午'), Dizhi.未, Dizhi.巳),
])
def test_wenzhen_yangren_definitions(
  birth_time: str,
  pillars: tuple[str, str, str, str],
  luming: Dizhi,
  diwang: Dizhi,
) -> None:
  '''Five charts with a Yin Day Master, read from 问真 on 2026-08-27:
  https://pcbz.iwzwh.com/#/paipan/index. 问真 reports the DIWANG branch; each chart
  also contains its distinct LUMING branch, so it distinguishes all three definitions.'''
  expected_by_definition = {
    ShenshaRules.YangrenDef.ZIPING : frozenset(),
    ShenshaRules.YangrenDef.LUMING : frozenset({luming}),
    ShenshaRules.YangrenDef.DIWANG : frozenset({diwang}),
  }
  for yangren_def, expected in expected_by_definition.items():
    school: BaziSchool = BaziSchool(yangren_def=yangren_def)
    chart: BaziChart = BaziChart(Bazi.create(
      birth_time,
      BaziGender.MALE,
      BaziConfig(school=school),
    ))
    assert tuple(map(str, chart.bazi.pillars)) == pillars
    assert RelationshipAnalyzer(chart).at_birth.shensha['yangren'] == expected

  default_chart: BaziChart = BaziChart(Bazi.create(birth_time, BaziGender.MALE))
  assert RelationshipAnalyzer(default_chart).at_birth.shensha['yangren'] == frozenset()


def test_case1() -> None:
  '''From 问真八字 https://pcbz.iwzwh.com/#/paipan/index'''
  bazi: Bazi = Bazi(
    birth_time=datetime(1984, 4, 1, 11, 8),
    gender=BaziGender.MALE,
  )
  chart: BaziChart = BaziChart(bazi)
  transit_chart = TransitChart(chart)
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

  assert at_birth.shensha['taohua']    == {Dizhi.午}
  assert at_birth.shensha['hongluan']  == {Dizhi.卯}
  # 问真八字以乙日主见午为红艳，但 `ShenshaRules.HONGYAN` 中以乙日主见申为红艳，所以这里为空。
  assert at_birth.shensha['hongyan']   == set()
  assert at_birth.shensha['tianxi']    == set()
  assert at_birth.shensha['yima']      == set()
  assert at_birth.shensha['huagai']    == set()
  assert at_birth.shensha['yangren']   == set()
  assert at_birth.shensha['feiren']    == set()
  assert at_birth.shensha['tianyi']    == {Dizhi.子, Dizhi.丑}
  assert at_birth.shensha['jiangxing'] == set()
  assert at_birth.shensha['jiesha']    == set()
  assert at_birth.shensha['wangshen']  == set()
  assert at_birth.shensha['guchen']    == set()
  assert at_birth.shensha['guasu']     == set()
  assert at_birth.shensha['lushen']    == {Dizhi.卯}
  assert at_birth.shensha['jinyu']     == set()
  assert at_birth.shensha['kuigang']   is None
  assert at_birth.shensha['tianshe']   is None

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
  transits_1990 = _at_year(transit_chart, 1990).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  )
  assert set(transits_1990.ganzhis) == {Ganzhi.from_str('戊辰'), Ganzhi.from_str('庚午')}

  shensha = transits.shensha(transits_1990)
  assert shensha['taohua']    == {Dizhi.午}
  assert shensha['hongluan']  == set()
  assert shensha['hongyan']   == set()
  assert shensha['tianxi']    == set()
  assert shensha['yima']      == set()
  assert shensha['huagai']    == {Dizhi.辰}
  assert shensha['yangren']   == set()
  assert shensha['feiren']    == set()
  assert shensha['tianyi']    == set()
  assert shensha['jiangxing'] == set()
  assert shensha['jiesha']    == set()
  assert shensha['wangshen']  == set()
  assert shensha['guchen']    == set()
  assert shensha['guasu']     == set()
  assert shensha['lushen']    == set()
  assert shensha['jinyu']     == set()

  assert _check_tiangan({
    TianganRelation.合 : [frozenset({Tiangan.乙, Tiangan.庚})],
    TianganRelation.克 : [frozenset({Tiangan.庚, Tiangan.乙}),
                         frozenset({Tiangan.乙, Tiangan.戊})],
  }, transits.day_master_relations(transits_1990))

  assert _check_dizhi({
    DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
    DizhiRelation.破 : [frozenset({Dizhi.辰, Dizhi.丑})],
    DizhiRelation.生 : [frozenset({Dizhi.午, Dizhi.丑})],
  }, transits.house_relations(transits_1990))

  star_relations_all = transits.star_relations(transits_1990) # level is `ALL` by default.

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

  assert not transits.zhengyin(transits_1990).tiangan
  assert not transits.zhengyin(transits_1990).dizhi

  assert transits.star(transits_1990).tiangan
  assert transits.star(transits_1990).dizhi
  assert transits.star(transits_1990.select(TransitKind.DAYUN)).tiangan
  assert transits.star(transits_1990.select(TransitKind.DAYUN)).dizhi
  assert not transits.star(transits_1990.select(TransitKind.LIUNIAN)).tiangan
  assert not transits.star(transits_1990.select(TransitKind.LIUNIAN)).dizhi

  # 2018
  transits_2018 = _at_year(transit_chart, 2018).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  )
  assert set(transits_2018.ganzhis) == {Ganzhi.from_str('辛未'), Ganzhi.from_str('戊戌')}

  shensha = transits.shensha(transits_2018)
  assert shensha['taohua']    == set()
  assert shensha['hongluan']  == set()
  assert shensha['hongyan']   == set()
  assert shensha['tianxi']    == set()
  assert shensha['yima']      == set()
  assert shensha['huagai']    == set()
  assert shensha['yangren']   == set()
  assert shensha['feiren']    == set()
  assert shensha['tianyi']    == {Dizhi.未}
  assert shensha['jiangxing'] == set()
  assert shensha['jiesha']    == set()
  assert shensha['wangshen']  == set()
  assert shensha['guchen']    == set()
  assert shensha['guasu']     == {Dizhi.戌}
  assert shensha['lushen']    == set()
  assert shensha['jinyu']     == set()

  assert _check_tiangan({
    TianganRelation.克 : [frozenset({Tiangan.乙, Tiangan.辛}),
                         frozenset({Tiangan.乙, Tiangan.戊})],
  }, transits.day_master_relations(transits_2018))

  assert _check_dizhi({
    DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未, Dizhi.戌}),
                       frozenset({Dizhi.丑, Dizhi.未})],
    DizhiRelation.冲 : [frozenset({Dizhi.丑, Dizhi.未})],
  }, transits.house_relations(transits_2018))

  star_relations_all = transits.star_relations(transits_2018) # level is `ALL` by default.

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

  assert not transits.zhengyin(transits_2018).tiangan
  assert not transits.zhengyin(transits_2018).dizhi

  assert transits.star(transits_2018).tiangan
  assert transits.star(transits_2018).dizhi
  assert transits.star(transits_2018.select(TransitKind.LIUNIAN)).tiangan
  assert transits.star(transits_2018.select(TransitKind.LIUNIAN)).dizhi
  assert not transits.star(transits_2018.select(TransitKind.DAYUN)).tiangan
  assert not transits.star(transits_2018.select(TransitKind.DAYUN)).dizhi

  transits_2025 = _at_year(transit_chart, 2025).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  )
  assert set(transits_2025.ganzhis) == {Ganzhi.from_str('壬申'), Ganzhi.from_str('乙巳')}
  assert set(transits.house_relations(transits_2025)[DizhiRelation.拱合]) == {
    dizhi_utils.DizhiCombo((Dizhi.丑, Dizhi.巳)),
  }

  # 2031
  transits_2031 = _at_year(transit_chart, 2031).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  )
  assert set(transits_2031.ganzhis) == {Ganzhi.from_str('辛亥'), Ganzhi.from_str('壬申')}

  shensha = transits.shensha(transits_2031)
  assert shensha['taohua']    == set()
  assert shensha['hongluan']  == set()
  assert shensha['hongyan']   == {Dizhi.申}
  assert shensha['tianxi']    == set()
  assert shensha['yima']      == {Dizhi.亥}
  assert shensha['huagai']    == set()
  assert shensha['yangren']   == set()
  assert shensha['feiren']    == set()
  assert shensha['tianyi']    == {Dizhi.申}
  assert shensha['jiangxing'] == set()
  assert shensha['jiesha']    == set()
  assert shensha['wangshen']  == {Dizhi.亥, Dizhi.申}
  assert shensha['guchen']    == set()
  assert shensha['guasu']     == set()
  assert shensha['lushen']    == set()
  assert shensha['jinyu']     == set()

  assert _check_tiangan({
    TianganRelation.克 : [frozenset({Tiangan.乙, Tiangan.辛})],
    TianganRelation.生 : [frozenset({Tiangan.乙, Tiangan.壬})],
  }, transits.day_master_relations(transits_2031))

  assert _check_dizhi({
    DizhiRelation.生 : [frozenset({Dizhi.申, Dizhi.丑})],
    DizhiRelation.克 : [frozenset({Dizhi.丑, Dizhi.亥})],
    DizhiRelation.三会 : [frozenset({Dizhi.亥, Dizhi.子, Dizhi.丑})],
  }, transits.house_relations(transits_2031))

  star_relations_all = transits.star_relations(transits_2031) # level is `ALL` by default.
  assert 0 == len(star_relations_all.tiangan)
  assert 0 == len(star_relations_all.dizhi)

  assert transits.zhengyin(transits_2031).tiangan
  assert transits.zhengyin(transits_2031).dizhi

  assert not transits.star(transits_2031).tiangan
  assert not transits.star(transits_2031).dizhi


def test_case2() -> None:
  '''From 问真八字 https://pcbz.iwzwh.com/#/paipan/index'''
  bazi: Bazi = Bazi(
    birth_time=datetime(2020, 7, 2, 19, 8),
    gender=BaziGender.FEMALE,
  )
  chart: BaziChart = BaziChart(bazi)
  transit_chart = TransitChart(chart)
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

  assert at_birth.shensha['taohua']    == set()
  assert at_birth.shensha['hongluan']  == set()
  assert at_birth.shensha['hongyan']   == set()
  assert at_birth.shensha['tianxi']    == set()
  assert at_birth.shensha['yima']      == set()
  assert at_birth.shensha['huagai']    == {Dizhi.戌}
  assert at_birth.shensha['yangren']   == {Dizhi.午}
  assert at_birth.shensha['feiren']    == {Dizhi.子}
  assert at_birth.shensha['tianyi']    == set()
  assert at_birth.shensha['jiangxing'] == {Dizhi.午}
  assert at_birth.shensha['zaisha']    == {Dizhi.午}
  assert at_birth.shensha['jiesha']    == set()
  assert at_birth.shensha['wangshen']  == set()
  assert at_birth.shensha['guchen']    == set()
  assert at_birth.shensha['guasu']     == {Dizhi.戌}
  assert at_birth.shensha['lushen']    == set()
  assert at_birth.shensha['jinyu']     == set()
  assert at_birth.shensha['kuigang']   is None
  assert at_birth.shensha['tianshe']   is None

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
    'huagai'   : frozenset([Dizhi.辰, Dizhi.戌]),
    'yangren'  : frozenset([Dizhi.午]),
    'feiren'   : frozenset([Dizhi.子]),
    'tianyi'   : frozenset([Dizhi.丑, Dizhi.未, Dizhi.亥, Dizhi.酉]),
    'jiangxing': frozenset([Dizhi.子, Dizhi.午]),
    'zaisha'   : frozenset([Dizhi.午]),
    'jiesha'   : frozenset([Dizhi.巳, Dizhi.亥]),
    'wangshen' : frozenset([Dizhi.亥, Dizhi.巳]),
    'guchen'   : frozenset([Dizhi.寅]),
    'guasu'    : frozenset([Dizhi.戌]),
    'lushen'   : frozenset([Dizhi.巳]),
    'jinyu'    : frozenset([Dizhi.未]),
  }

  for _ in range(50):
    random_year = random.randint(birth_gz_year, birth_gz_year + 200)
    selected_transits = _random_year_transits(transit_chart, random_year)
    transits_gz = selected_transits.ganzhis
    transits_dz = {gz.dizhi for gz in transits_gz}

    assert transits.shensha(selected_transits) == {
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

  for year in random.sample(range(birth_gz_year, birth_gz_year + 600), 100):
    year_transits = _at_year(transit_chart, year)
    for kind in year_transits:
      selected_transits = year_transits.select(kind)
      transits_gz = selected_transits.ganzhis
      transits_tg = {gz.tiangan for gz in transits_gz}

      for tg_rel, tg_combos in transits.day_master_relations(selected_transits).items():
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

  for year in random.sample(range(birth_gz_year, birth_gz_year + 600), 100):
    year_transits = _at_year(transit_chart, year)
    for kind in year_transits:
      selected_transits = year_transits.select(kind)
      transits_gz = selected_transits.ganzhis
      transits_dz = {gz.dizhi for gz in transits_gz}

      house_dz = chart.house_of_relationship
      other_dz = {bazi.year_pillar.dizhi, bazi.month_pillar.dizhi, bazi.hour_pillar.dizhi}
      house_relations = transits.house_relations(selected_transits)
      assert set(house_relations).issubset(house_relation_expected)

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

  # The oracle mirrors the analyzer by reading the chart's school profile (issue #69).
  school: BaziSchool = chart.bazi.config.school

  for year in random.sample(range(birth_gz_year, birth_gz_year + 600), 100):
    year_transits = _at_year(transit_chart, year)
    for kind in year_transits:
      selected_transits = year_transits.select(kind)
      transits_gz = selected_transits.ganzhis
      transits_tg = {gz.tiangan for gz in transits_gz}
      transits_dz = {gz.dizhi for gz in transits_gz}

      # Test TRANSITS_ONLY
      transits_only_star_relations = transits.star_relations(
        selected_transits,
        level=TransitAnalysis.Level.TRANSITS_ONLY,
      )
      expected_transits_only_tg_star_relations = tiangan_utils.discover(list(transits_tg)).filter(
        lambda _, combo : Tiangan.癸 in combo
      )
      expected_transits_only_dz_star_relations = dizhi_utils.discover(
        list(transits_dz), anhe_def=school.anhe_def, xing_def=school.xing_def,
      ).filter(
        lambda _, combo : Dizhi.子 in combo
      )

      assert _equal(transits_only_star_relations.tiangan, expected_transits_only_tg_star_relations)
      assert _equal(transits_only_star_relations.dizhi, expected_transits_only_dz_star_relations)

      # Test MUTUAL
      mutual_star_relations = transits.star_relations(
        selected_transits,
        level=TransitAnalysis.Level.MUTUAL,
      )
      expected_mutual_tg_star_relations = tiangan_utils.discover_mutual(chart.bazi.four_tiangans, list(transits_tg)).filter(
        lambda _, combo : Tiangan.癸 in combo
      )
      expected_mutual_dz_star_relations = dizhi_utils.discover_mutual(
        chart.bazi.four_dizhis, list(transits_dz), anhe_def=school.anhe_def, xing_def=school.xing_def,
      ).filter(
        lambda _, combo : Dizhi.子 in combo
      )

      assert _equal(mutual_star_relations.tiangan, expected_mutual_tg_star_relations)
      assert _equal(mutual_star_relations.dizhi, expected_mutual_dz_star_relations)

      # Test ALL
      all_star_relations = transits.star_relations(
        selected_transits,
        level=TransitAnalysis.Level.ALL,
      )
      expected_all_tg_star_relations = expected_transits_only_tg_star_relations.merge(expected_mutual_tg_star_relations)
      expected_all_dz_star_relations = expected_transits_only_dz_star_relations.merge(expected_mutual_dz_star_relations)

      assert _equal(all_star_relations.tiangan, expected_all_tg_star_relations)
      assert _equal(all_star_relations.dizhi, expected_all_dz_star_relations)

      assert _equal(all_star_relations.tiangan, tiangan_utils.discover(list(transits_tg) + list(bazi.four_tiangans)).filter(
        lambda _, combo : Tiangan.癸 in combo and not combo.isdisjoint(transits_tg)
      ))
      assert _equal(all_star_relations.dizhi, dizhi_utils.discover(
        list(transits_dz) + list(bazi.four_dizhis), anhe_def=school.anhe_def, xing_def=school.xing_def,
      ).filter(
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

  for year in random.sample(range(birth_gz_year, birth_gz_year + 600), 100):
    year_transits = _at_year(transit_chart, year)
    for kind in year_transits:
      selected_transits = year_transits.select(kind)
      transits_gz = selected_transits.ganzhis
      transits_tg = {gz.tiangan for gz in transits_gz}
      transits_dz = {gz.dizhi for gz in transits_gz}

      zhengyin_result = transits.zhengyin(selected_transits)
      assert zhengyin_result.tiangan == any(is_zhengyin(tg) for tg in transits_tg)
      assert zhengyin_result.dizhi == any(is_zhengyin(dz) for dz in transits_dz)

      star_result = transits.star(selected_transits)
      assert star_result.tiangan == any(is_star(tg) for tg in transits_tg)
      assert star_result.dizhi == any(is_star(dz) for dz in transits_dz)


@pytest.mark.parametrize('bazi', [Bazi.random() for _ in range(5)])
def test_random_cases(bazi: Bazi) -> None:
  chart = BaziChart(bazi)
  y_dz, m_dz, d_dz, h_dz = bazi.four_dizhis
  house = chart.house_of_relationship

  transit_chart = TransitChart(chart)
  analyzer: RelationshipAnalyzer = RelationshipAnalyzer(chart)
  transits: TransitAnalysis = analyzer.transits

  # basic info
  dm: Tiangan = bazi.day_master
  star: Shishen = Shishen.正财 if bazi.gender is BaziGender.MALE else Shishen.正官

  # The 红艳 anchor stem follows the chart's school (查法锚干, issue #69) -- don't assume the day master.
  hongyan_anchor: Tiangan = dm if bazi.config.school.hongyan_key is KeyStem.DAY_MASTER else bazi.year_pillar.tiangan

  # The Dizhi-relation oracles below mirror the analyzer by reading the same school profile
  # (issue #69) -- they don't assume the default 暗合/刑 definitions either.
  # 地支关系 oracle 同样从流派档案读暗合/刑口径，不假设默认定义（issue #69）。
  school: BaziSchool = bazi.config.school

  assert star is bazi_utils.shishen(dm, chart.relationship_stars.tiangan)
  for star_dz in chart.relationship_stars.dizhi:
    assert star is bazi_utils.shishen(dm, star_dz)

  # shensha
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    year_transits = _at_year(transit_chart, year)
    for kind in year_transits:
      selected_transits = year_transits.select(kind)
      transits_gz = selected_transits.ganzhis
      transits_dz_set = {gz.dizhi for gz in transits_gz}

      def __taohua(dz: Dizhi) -> bool:
        return shensha_utils.taohua(y_dz, dz) or shensha_utils.taohua(d_dz, dz)

      def __yima(dz: Dizhi) -> bool:
        return ((school.shensha_anchor_profile is ShenshaAnchorProfile.WENZHEN
                 and shensha_utils.yima(y_dz, dz)) or shensha_utils.yima(d_dz, dz))

      def __huagai(dz: Dizhi) -> bool:
        return ((school.shensha_anchor_profile is ShenshaAnchorProfile.WENZHEN
                 and shensha_utils.huagai(y_dz, dz)) or shensha_utils.huagai(d_dz, dz))

      def __jiangxing(dz: Dizhi) -> bool:
        return ((school.shensha_anchor_profile is ShenshaAnchorProfile.WENZHEN
                 and shensha_utils.jiangxing(y_dz, dz)) or shensha_utils.jiangxing(d_dz, dz))

      def __zaisha(dz: Dizhi) -> bool:
        return (shensha_utils.zaisha(y_dz, dz) or
                (school.zaisha_anchor is ZaishaAnchor.YEAR_AND_DAY and shensha_utils.zaisha(d_dz, dz)))

      def __jiesha(dz: Dizhi) -> bool:
        return ((school.shensha_anchor_profile is ShenshaAnchorProfile.WENZHEN
                 and shensha_utils.jiesha(y_dz, dz)) or shensha_utils.jiesha(d_dz, dz))

      def __wangshen(dz: Dizhi) -> bool:
        return ((school.shensha_anchor_profile is ShenshaAnchorProfile.WENZHEN
                 and shensha_utils.wangshen(y_dz, dz)) or shensha_utils.wangshen(d_dz, dz))

      expected_taohua:    set[Dizhi] = set(filter(__taohua, transits_dz_set))
      expected_hongyan:   set[Dizhi] = set(filter(lambda dz : shensha_utils.hongyan(hongyan_anchor, dz), transits_dz_set))
      expected_hongluan:  set[Dizhi] = set(filter(lambda dz : shensha_utils.hongluan(y_dz, dz), transits_dz_set))
      expected_tianxi:    set[Dizhi] = set(filter(lambda dz : shensha_utils.tianxi(y_dz, dz), transits_dz_set))
      expected_yima:      set[Dizhi] = set(filter(__yima, transits_dz_set))
      expected_huagai:    set[Dizhi] = set(filter(__huagai, transits_dz_set))
      expected_yangren:   set[Dizhi] = set(filter(
        lambda dz: shensha_utils.yangren(dm, dz, definition=school.yangren_def),
        transits_dz_set,
      ))
      expected_feiren:    set[Dizhi] = set(filter(
        lambda dz: shensha_utils.feiren(dm, dz, definition=school.feiren_def),
        transits_dz_set,
      ))
      expected_tianyi:    set[Dizhi] = set(filter(
        lambda dz: any(shensha_utils.tianyi(tg, dz, definition=school.tianyi_def)
                       for tg in (bazi.year_pillar.tiangan, dm)),
        transits_dz_set,
      ))
      expected_jiangxing: set[Dizhi] = set(filter(__jiangxing, transits_dz_set))
      expected_zaisha:    set[Dizhi] = set(filter(__zaisha, transits_dz_set))
      expected_jiesha:    set[Dizhi] = set(filter(__jiesha, transits_dz_set))
      expected_wangshen:  set[Dizhi] = set(filter(__wangshen, transits_dz_set))
      expected_guchen:    set[Dizhi] = set(filter(lambda dz: shensha_utils.guchen(y_dz, dz), transits_dz_set))
      expected_guasu:     set[Dizhi] = set(filter(lambda dz: shensha_utils.guasu(y_dz, dz), transits_dz_set))
      expected_lushen:    set[Dizhi] = set(filter(lambda dz: shensha_utils.lushen(dm, dz), transits_dz_set))
      expected_jinyu:     set[Dizhi] = set(filter(lambda dz: shensha_utils.jinyu(dm, dz), transits_dz_set))

      shensha = transits.shensha(selected_transits)
      assert expected_taohua == shensha['taohua']
      assert expected_hongyan == shensha['hongyan']
      assert expected_hongluan == shensha['hongluan']
      assert expected_tianxi == shensha['tianxi']
      assert expected_yima == shensha['yima']
      assert expected_huagai == shensha['huagai']
      assert expected_yangren == shensha['yangren']
      assert expected_feiren == shensha['feiren']
      assert expected_tianyi == shensha['tianyi']
      assert expected_jiangxing == shensha['jiangxing']
      assert expected_zaisha == shensha['zaisha']
      assert expected_jiesha == shensha['jiesha']
      assert expected_wangshen == shensha['wangshen']
      assert expected_guchen == shensha['guchen']
      assert expected_guasu == shensha['guasu']
      assert expected_lushen == shensha['lushen']
      assert expected_jinyu == shensha['jinyu']

  # day master and house relations
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    year_transits = _at_year(transit_chart, year)
    for kind in year_transits:
      selected_transits = year_transits.select(kind)
      transits_gz = selected_transits.ganzhis
      transits_tg_set = {gz.tiangan for gz in transits_gz}
      transits_dz_set = {gz.dizhi for gz in transits_gz}

      expected_tg_relations = tiangan_utils.discover_mutual([chart.bazi.day_master], list(transits_tg_set))
      expected_dz_relations = dizhi_utils.discover_mutual(
        [house], list(transits_dz_set), anhe_def=school.anhe_def, xing_def=school.xing_def,
      ).merge(
        dizhi_utils.discover_mutual(
          [house], list(transits_dz_set) + [y_dz, m_dz, h_dz], anhe_def=school.anhe_def, xing_def=school.xing_def,
        ).filter(
          lambda _, combo : len(combo) == 3
        ).filter(
          lambda _, combo : not combo.isdisjoint(filter(lambda dz : dz is not house, transits_dz_set))
        )
      )
      positioned_gong = dizhi_utils.discover_mutual_ganzhis(
        bazi.pillars,
        transits_gz,
        anhe_def=school.anhe_def,
        xing_def=school.xing_def,
        gong_def=school.gong_def,
      )
      expected_gong = dizhi_utils.GanzhiRelationDiscovery({
        relation : tuple(
          combo for combo in positioned_gong.get(relation, ())
          if any(occurrence.index == 2 for occurrence in combo)
        )
        for relation in (DizhiRelation.拱合, DizhiRelation.拱会)
      }).to_dizhi_discovery()
      expected_dz_relations = expected_dz_relations.merge(expected_gong)

      tg_relations = transits.day_master_relations(selected_transits)
      dz_relations = transits.house_relations(selected_transits)

      assert _equal(expected_tg_relations, tg_relations)
      assert _equal(expected_dz_relations, dz_relations)

      if house in [Dizhi.午, Dizhi.亥, Dizhi.辰] and house in transits_dz_set: # 自刑 cases
        assert frozenset({house}) in dz_relations[DizhiRelation.刑]

      for dz_tuple in DizhiRules.DIZHI_XING[school.xing_def]: # 三刑 cases (len-3 combos coincide across defs / 三组合在各定义下相同)
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
    year_transits = _at_year(transit_chart, year)
    for kind in year_transits:
      selected_transits = year_transits.select(kind)
      transits_gz = selected_transits.ganzhis
      transits_tg_list = [gz.tiangan for gz in transits_gz]
      transits_dz_list = [gz.dizhi for gz in transits_gz]

      stars = chart.relationship_stars

      # TRANSITS_ONLY
      transits_only_star_relations = transits.star_relations(
        selected_transits,
        level=TransitAnalysis.Level.TRANSITS_ONLY,
      )

      expected_transits_only_tg = tiangan_utils.TianganRelationDiscovery({})
      if stars.tiangan in transits_tg_list:
        tg_list = transits_tg_list.copy()
        tg_list.remove(stars.tiangan)
        expected_transits_only_tg = tiangan_utils.discover_mutual([stars.tiangan], tg_list)

      expected_transits_only_dz = dizhi_utils.discover(
        transits_dz_list, anhe_def=school.anhe_def, xing_def=school.xing_def,
      ).filter(
        lambda _, combo : not combo.isdisjoint(stars.dizhi)
      )
      transits_only_gong = dizhi_utils.discover_ganzhis(
        transits_gz,
        anhe_def=school.anhe_def,
        xing_def=school.xing_def,
        gong_def=school.gong_def,
      )
      expected_transits_only_dz = expected_transits_only_dz.merge(
        dizhi_utils.GanzhiRelationDiscovery({
          relation : tuple(
            combo for combo in transits_only_gong.get(relation, ())
            if any(occurrence.ganzhi.dizhi in stars.dizhi for occurrence in combo)
          )
          for relation in (DizhiRelation.拱合, DizhiRelation.拱会)
        }).to_dizhi_discovery()
      )

      assert _equal(transits_only_star_relations.tiangan, expected_transits_only_tg)
      assert _equal(transits_only_star_relations.dizhi, expected_transits_only_dz)

      # MUTUAL
      mutual_star_relations = transits.star_relations(
        selected_transits,
        level=TransitAnalysis.Level.MUTUAL,
      )

      expected_mutual_tg = tiangan_utils.discover_mutual(bazi.four_tiangans, transits_tg_list).filter(
        lambda _, combo : stars.tiangan in combo
      )

      expected_mutual_dz = dizhi_utils.discover_mutual(
        bazi.four_dizhis, transits_dz_list, anhe_def=school.anhe_def, xing_def=school.xing_def,
      ).filter(
        lambda _, combo : len(combo & set(stars.dizhi)) > 0
      )
      mutual_gong = dizhi_utils.discover_mutual_ganzhis(
        bazi.pillars,
        transits_gz,
        anhe_def=school.anhe_def,
        xing_def=school.xing_def,
        gong_def=school.gong_def,
      )
      expected_mutual_dz = expected_mutual_dz.merge(
        dizhi_utils.GanzhiRelationDiscovery({
          relation : tuple(
            combo for combo in mutual_gong.get(relation, ())
            if any(occurrence.ganzhi.dizhi in stars.dizhi for occurrence in combo)
          )
          for relation in (DizhiRelation.拱合, DizhiRelation.拱会)
        }).to_dizhi_discovery()
      )

      assert _equal(mutual_star_relations.tiangan, expected_mutual_tg)
      assert _equal(mutual_star_relations.dizhi, expected_mutual_dz)

      # ALL
      all_star_relations = transits.star_relations(
        selected_transits,
        level=TransitAnalysis.Level.ALL,
      )

      assert _equal(all_star_relations.tiangan, expected_transits_only_tg.merge(expected_mutual_tg))
      assert _equal(all_star_relations.dizhi, expected_transits_only_dz.merge(expected_mutual_dz))

      assert _equal(all_star_relations.tiangan, tiangan_utils.discover(transits_tg_list + list(bazi.four_tiangans)).filter(
        lambda _, combo : stars.tiangan in combo
      ).filter(
        lambda _, combo : not combo.isdisjoint(transits_tg_list)
      ))

      all_dizhi_without_gong = dizhi_utils.DizhiRelationDiscovery({
        relation : combos
        for relation, combos in all_star_relations.dizhi.items()
        if relation not in (DizhiRelation.拱合, DizhiRelation.拱会)
      })
      assert _equal(all_dizhi_without_gong, dizhi_utils.discover(
        transits_dz_list + list(bazi.four_dizhis), anhe_def=school.anhe_def, xing_def=school.xing_def,
      ).filter(
        lambda _, combo : len(combo & set(stars.dizhi)) > 0
      ).filter(
        lambda _, combo : not combo.isdisjoint(transits_dz_list)
      ))

  # zhengyin and star methods
  for year in range(bazi.ganzhi_date.year, bazi.ganzhi_date.year + 100):
    year_transits = _at_year(transit_chart, year)
    for kind in year_transits:
      selected_transits = year_transits.select(kind)
      transits_gz = selected_transits.ganzhis
      transits_tg_set = {gz.tiangan for gz in transits_gz}
      transits_dz_set = {gz.dizhi for gz in transits_gz}

      zhengyin_results = transits.zhengyin(selected_transits)
      assert zhengyin_results.tiangan == any(bazi_utils.shishen(dm, tg) is Shishen.正印 for tg in transits_tg_set)
      assert zhengyin_results.dizhi == any(bazi_utils.shishen(dm, dz) is Shishen.正印 for dz in transits_dz_set)

      stars = chart.relationship_stars
      star_results = transits.star(selected_transits)
      assert star_results.tiangan == (stars.tiangan in transits_tg_set)
      assert star_results.dizhi != set(transits_dz_set).isdisjoint(stars.dizhi)


def test_school_variants_reach_relationship_analysis() -> None:
  # End-to-end pins that the chart's school steers relation discovery (issue #69). Assertions
  # pin exact combo sets, not "fewer results" -- MANGPAI ⊂ NORMAL_EXTENDED and STRICT ⊂ LOOSE,
  # so a "differs" assertion would also pass on a wrong or empty table.
  # 端到端钉住流派档案确实驱动关系查法（issue #69）。断言钉精确集合而非「有差异」——
  # MANGPAI/STRICT 都是默认定义的子集，「变少」在错传空表/错表时同样成立。

  # Chart A: 戊寅 day with 午 in the month pillar -- 寅午 forms ANHE under NORMAL /
  # NORMAL_EXTENDED but not MANGPAI. Covers the AtBirth `discover` path.
  # 盘 A：戊寅日、月支午——寅午暗合 NORMAL / NORMAL_EXTENDED 皆有、MANGPAI 无。覆盖 AtBirth `discover` 路径。
  dt_a: datetime = datetime(1984, 6, 13) # 甲子 / 庚午 / 戊寅 / 壬子
  anhe_default: AtBirthAnalysis = RelationshipAnalyzer(BaziChart(Bazi.create(dt_a, BaziGender.MALE))).at_birth
  anhe_mangpai: AtBirthAnalysis = RelationshipAnalyzer(BaziChart(Bazi.create(
    dt_a, BaziGender.MALE, BaziConfig(school=BaziSchool(anhe_def=DizhiRules.AnheDef.MANGPAI)),
  ))).at_birth

  default_rels_a = anhe_default.house_relations
  mangpai_rels_a = anhe_mangpai.house_relations
  assert set(map(frozenset, default_rels_a[DizhiRelation.暗合])) == {frozenset((Dizhi.寅, Dizhi.午))}
  assert DizhiRelation.暗合 not in mangpai_rels_a
  # Only the 暗合 key may differ between the two charts (其余关系两盘一致).
  assert {r: c for r, c in default_rels_a.items() if r is not DizhiRelation.暗合} == dict(mangpai_rels_a.items())

  # Chart B: 癸丑 day with 未 in the month pillar -- 丑未 forms XING only under LOOSE
  # (STRICT requires all three of 丑未戌). Same path, the other knob.
  # 盘 B：癸丑日、月支未——丑未刑仅 LOOSE 成立（STRICT 要求三支齐现）。同路径，另一个旋钮。
  dt_b: datetime = datetime(1984, 7, 18) # 甲子 / 辛未 / 癸丑 / 壬子
  xing_default: AtBirthAnalysis = RelationshipAnalyzer(BaziChart(Bazi.create(dt_b, BaziGender.MALE))).at_birth
  xing_strict: AtBirthAnalysis = RelationshipAnalyzer(BaziChart(Bazi.create(
    dt_b, BaziGender.MALE, BaziConfig(school=BaziSchool(xing_def=DizhiRules.XingDef.STRICT)),
  ))).at_birth

  default_rels_b = xing_default.house_relations
  strict_rels_b = xing_strict.house_relations
  assert set(map(frozenset, default_rels_b[DizhiRelation.刑])) == {frozenset((Dizhi.丑, Dizhi.未))}
  assert DizhiRelation.刑 not in strict_rels_b
  assert {r: c for r, c in default_rels_b.items() if r is not DizhiRelation.刑} == dict(strict_rels_b.items())

  # Chart C: 辛丑 day with no 未 at birth; the 1991 辛未 流年 brings 未 -- covers the
  # transit-side `discover_mutual` path in `TransitAnalysis.house_relations`.
  # 盘 C：辛丑日、原局无未；1991 辛未流年带来未——覆盖流运侧 `discover_mutual` 路径。
  dt_c: datetime = datetime(1984, 1, 8) # 癸亥 / 乙丑 / 辛丑 / 戊子
  chart_default_c = BaziChart(Bazi.create(dt_c, BaziGender.MALE))
  chart_strict_c = BaziChart(Bazi.create(
    dt_c, BaziGender.MALE, BaziConfig(school=BaziSchool(xing_def=DizhiRules.XingDef.STRICT)),
  ))
  transit_default: TransitAnalysis = RelationshipAnalyzer(chart_default_c).transits
  transit_strict: TransitAnalysis = RelationshipAnalyzer(chart_strict_c).transits

  default_1991 = _at_year(TransitChart(chart_default_c), 1991).select(TransitKind.LIUNIAN)
  strict_1991 = _at_year(TransitChart(chart_strict_c), 1991).select(TransitKind.LIUNIAN)
  default_rels_c = transit_default.house_relations(default_1991)
  strict_rels_c = transit_strict.house_relations(strict_1991)
  assert set(map(frozenset, default_rels_c[DizhiRelation.刑])) == {frozenset((Dizhi.丑, Dizhi.未))}
  assert DizhiRelation.刑 not in strict_rels_c
  assert {r: c for r, c in default_rels_c.items() if r is not DizhiRelation.刑} == dict(strict_rels_c.items())

  # Chart D: 辛巳 day with 寅 in the month pillar -- the relationship star is 寅 (辛's
  # 正财甲 lives in 寅), and 寅巳 forms XING only under LOOSE. Covers the AtBirth
  # `star_relations` path.
  # 盘 D：辛巳日、月支寅——配偶星为寅（辛之正财甲藏于寅），寅巳刑仅 LOOSE 成立。
  # 覆盖 AtBirth `star_relations` 路径。
  dt_d: datetime = datetime(1984, 2, 17) # 甲子 / 丙寅 / 辛巳 / 戊子
  star_default_d = RelationshipAnalyzer(BaziChart(Bazi.create(dt_d, BaziGender.MALE))).at_birth.star_relations.dizhi
  star_strict_d = RelationshipAnalyzer(BaziChart(Bazi.create(
    dt_d, BaziGender.MALE, BaziConfig(school=BaziSchool(xing_def=DizhiRules.XingDef.STRICT)),
  ))).at_birth.star_relations.dizhi

  assert set(map(frozenset, star_default_d[DizhiRelation.刑])) == {frozenset((Dizhi.寅, Dizhi.巳))}
  assert DizhiRelation.刑 not in star_strict_d
  assert {r: c for r, c in star_default_d.items() if r is not DizhiRelation.刑} == dict(star_strict_d.items())

  # Chart E: 辛未 day, the star 寅 present (month), no 巳/申 at birth; the 1992 壬申 流年
  # brings 申 -- 寅申 forms XING only under LOOSE. Covers the transit-side `star_relations`
  # MUTUAL path (the TRANSITS_ONLY path shares `_dz_discover` with the AtBirth cases above).
  # 盘 E：辛未日、月支寅（配偶星）、原局无巳申；1992 壬申流年带来申——寅申刑仅 LOOSE 成立。
  # 覆盖流运侧 `star_relations` MUTUAL 路径（TRANSITS_ONLY 路径与上面 AtBirth 案例共用 `_dz_discover`）。
  dt_e: datetime = datetime(1984, 2, 7) # 甲子 / 丙寅 / 辛未 / 戊子
  chart_default_e = BaziChart(Bazi.create(dt_e, BaziGender.MALE))
  chart_strict_e = BaziChart(Bazi.create(
    dt_e, BaziGender.MALE, BaziConfig(school=BaziSchool(xing_def=DizhiRules.XingDef.STRICT)),
  ))
  transit_default_e: TransitAnalysis = RelationshipAnalyzer(chart_default_e).transits
  transit_strict_e: TransitAnalysis = RelationshipAnalyzer(chart_strict_e).transits

  default_1992 = _at_year(TransitChart(chart_default_e), 1992).select(TransitKind.LIUNIAN)
  strict_1992 = _at_year(TransitChart(chart_strict_e), 1992).select(TransitKind.LIUNIAN)
  default_star_e = transit_default_e.star_relations(
    default_1992,
    level=TransitAnalysis.Level.MUTUAL,
  ).dizhi
  strict_star_e = transit_strict_e.star_relations(
    strict_1992,
    level=TransitAnalysis.Level.MUTUAL,
  ).dizhi
  assert set(map(frozenset, default_star_e[DizhiRelation.刑])) == {frozenset((Dizhi.寅, Dizhi.申))}
  assert DizhiRelation.刑 not in strict_star_e
  assert {r: c for r, c in default_star_e.items() if r is not DizhiRelation.刑} == dict(strict_star_e.items())

  dt_f = datetime(1980, 1, 6, 12)
  gong_default_f = RelationshipAnalyzer(BaziChart(Bazi.create(dt_f, BaziGender.MALE))).at_birth.house_relations
  gong_wide_f = RelationshipAnalyzer(BaziChart(Bazi.create(
    dt_f,
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)),
  ))).at_birth.house_relations

  assert DizhiRelation.拱合 not in gong_default_f
  assert set(gong_wide_f[DizhiRelation.拱合]) == {dizhi_utils.DizhiCombo((Dizhi.寅, Dizhi.午))}
  assert {
    relation : combos
    for relation, combos in gong_default_f.items()
    if relation not in DizhiRules.GONG_RELATIONS
  } == {
    relation : combos
    for relation, combos in gong_wide_f.items()
    if relation not in DizhiRules.GONG_RELATIONS
  }
