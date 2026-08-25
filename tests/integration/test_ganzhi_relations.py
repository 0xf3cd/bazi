# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_ganzhi_relations.py

import pytest

from datetime import datetime

from src.bazi import Bazi, BaziGender
from src.bazi_chart import BaziChart
from src.transit_chart import TransitChart
from src.transits import TransitKind, TransitSet
from src.defines import Tiangan, Dizhi, Ganzhi, TianganRelation, DizhiRelation
from src.utils import tiangan_utils, dizhi_utils


pytestmark = pytest.mark.integration


def _at_year(transit_chart: TransitChart, gz_year: int) -> TransitSet:
  transits = transit_chart.at_year(gz_year)
  assert transits is not None
  return transits


# Integration tests are mainly aiming to test the correctness of `tiangan_utils` and `dizhi_utils` in transit context.
# The Bazi cases are collected from "测测" app / "问真八字" web site.
#
# In this project, `search`, `discover`, and `discover_mutual` methods in `tiangan_utils` and `dizhi_utils` will
# return all possible combos.
# However, for 测测 and 问真八字, they only consider part of the combos. For example,
# they don't consider SHENG / 生 relation.
#
# So in the following tests, we only test that the relation combos that 测测/问真八字 find
# are in `tiangan_utils`'s and `dizhi_utils`'s returns.
# There can be some combos in the returns but not in 测测/问真八字's results.


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


def test_case1() -> None:
  '''From 问真八字 https://pcbz.iwzwh.com/#/paipan/index'''
  bazi: Bazi = Bazi(
    birth_time=datetime(1984, 4, 1, 11, 8),
    gender=BaziGender.MALE,
  )
  chart: BaziChart = BaziChart(bazi)
  transit_chart = TransitChart(chart)

  # pillar correctness
  assert bazi.year_pillar == Ganzhi.from_str('甲子')
  assert bazi.month_pillar == Ganzhi.from_str('丁卯')
  assert bazi.day_pillar == Ganzhi.from_str('乙丑')
  assert bazi.hour_pillar == Ganzhi.from_str('壬午')
  assert chart.xiaoyun[0].ganzhi == Ganzhi.from_str('癸未')
  assert next(chart.dayun).ganzhi == Ganzhi.from_str('戊辰'), 'first dayun Ganzhi'
  assert next(chart.dayun).ganzhi_year == 1985, 'first dayun year'

  # at birth
  assert _check_tiangan({
    TianganRelation.合 : [frozenset({Tiangan.丁, Tiangan.壬})],
  }, tiangan_utils.discover(chart.bazi.four_tiangans))

  assert _check_dizhi({
    DizhiRelation.六合 : [frozenset({Dizhi.子, Dizhi.丑})],
    DizhiRelation.刑 : [frozenset({Dizhi.子, Dizhi.卯})],
    DizhiRelation.冲 : [frozenset({Dizhi.子, Dizhi.午})],
    DizhiRelation.破 : [frozenset({Dizhi.午, Dizhi.卯})],
    DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
  }, dizhi_utils.discover(chart.bazi.four_dizhis))

  # 1993 dayun and liunian - transits only
  ganzhis = _at_year(transit_chart, 1993).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  ).ganzhis

  assert _check_tiangan({
    TianganRelation.合 : [frozenset({Tiangan.戊, Tiangan.癸})],
  }, tiangan_utils.discover(tuple(gz.tiangan for gz in ganzhis)))

  assert _check_dizhi({
    DizhiRelation.六合 : [frozenset({Dizhi.辰, Dizhi.酉})],
  }, dizhi_utils.discover(tuple(gz.dizhi for gz in ganzhis)))

  # 2024 dayun and liunian - between transits and at-birth
  ganzhis = _at_year(transit_chart, 2024).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  ).ganzhis

  assert _check_tiangan({
    TianganRelation.克 : [frozenset({Tiangan.丁, Tiangan.辛}), frozenset({Tiangan.辛, Tiangan.乙})],
  }, tiangan_utils.discover_mutual(bazi.four_tiangans, tuple(gz.tiangan for gz in ganzhis)))

  assert _check_dizhi({
    DizhiRelation.六合 : [frozenset({Dizhi.午, Dizhi.未})],
    DizhiRelation.半合 : [frozenset({Dizhi.子, Dizhi.辰}), frozenset({Dizhi.卯, Dizhi.未})],
    DizhiRelation.刑 : [frozenset({Dizhi.未, Dizhi.丑})], # LOOSE mode is used for XING relation.
    DizhiRelation.冲 : [frozenset({Dizhi.未, Dizhi.丑})],
    DizhiRelation.破 : [frozenset({Dizhi.丑, Dizhi.辰})],
    DizhiRelation.害 : [frozenset({Dizhi.未, Dizhi.子}), frozenset({Dizhi.辰, Dizhi.卯})],
  }, dizhi_utils.discover_mutual(bazi.four_dizhis, tuple(gz.dizhi for gz in ganzhis)))

  # 2051 dayun and liunian - transits only
  ganzhis = _at_year(transit_chart, 2051).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  ).ganzhis

  assert _check_dizhi({
    DizhiRelation.破 : [frozenset({Dizhi.戌, Dizhi.未})],
    DizhiRelation.刑 : [frozenset({Dizhi.未, Dizhi.戌})],
  }, dizhi_utils.discover(tuple(gz.dizhi for gz in ganzhis)))

  # 2051 dayun and liunian - between transits and at-birth
  ganzhis = _at_year(transit_chart, 2051).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  ).ganzhis

  assert _check_tiangan({
    TianganRelation.克 : [frozenset({Tiangan.丁, Tiangan.辛}), frozenset({Tiangan.辛, Tiangan.乙})],
  }, tiangan_utils.discover_mutual(bazi.four_tiangans, tuple(gz.tiangan for gz in ganzhis)))

  assert _check_dizhi({
    DizhiRelation.六合 : [frozenset({Dizhi.卯, Dizhi.戌}), frozenset({Dizhi.午, Dizhi.未})],
    DizhiRelation.半合 : [frozenset({Dizhi.卯, Dizhi.未}), frozenset({Dizhi.午, Dizhi.戌})],
    DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未, Dizhi.戌}),
                        frozenset({Dizhi.未, Dizhi.丑}),
                        frozenset({Dizhi.戌, Dizhi.丑}),], # LOOSE mode is used for XING relation.
    DizhiRelation.冲 : [frozenset({Dizhi.丑, Dizhi.未})],
    DizhiRelation.害 : [frozenset({Dizhi.未, Dizhi.子})],
  }, dizhi_utils.discover_mutual(bazi.four_dizhis, tuple(gz.dizhi for gz in ganzhis)))


def test_case2() -> None:
  '''From 测测 and 问真八字'''
  bazi: Bazi = Bazi(
    birth_time=datetime(2024, 5, 19, 18, 59),
    gender=BaziGender.FEMALE,
  )
  chart: BaziChart = BaziChart(bazi)
  transit_chart = TransitChart(chart)

  # pillar correctness
  assert bazi.year_pillar == Ganzhi.from_str('甲辰')
  assert bazi.month_pillar == Ganzhi.from_str('己巳')
  assert bazi.day_pillar == Ganzhi.from_str('癸未')
  assert bazi.hour_pillar == Ganzhi.from_str('辛酉')
  assert chart.xiaoyun[0].ganzhi == Ganzhi.from_str('庚申')
  assert next(chart.dayun).ganzhi == Ganzhi.from_str('戊辰'), 'first dayun Ganzhi'
  assert next(chart.dayun).ganzhi_year == 2029, 'first dayun year'

  # at birth
  assert _check_tiangan({
    TianganRelation.合 : [frozenset({Tiangan.甲, Tiangan.己})],
    TianganRelation.克 : [frozenset({Tiangan.己, Tiangan.癸})],
  }, tiangan_utils.discover(bazi.four_tiangans))

  assert _check_dizhi({
    DizhiRelation.六合 : [frozenset({Dizhi.辰, Dizhi.酉})],
    DizhiRelation.半合 : [frozenset({Dizhi.巳, Dizhi.酉})],
  }, dizhi_utils.discover(bazi.four_dizhis))

  # 2024 xiaoyun and liunian - between transits and at-birth
  # 测测's Xiaoyun result is kinda buggy. So use 问真八字's Xiaoyun result here.
  ganzhis = _at_year(transit_chart, 2024).select(
    TransitKind.XIAOYUN,
    TransitKind.LIUNIAN,
  ).ganzhis

  assert _check_tiangan({
    TianganRelation.合 : [frozenset({Tiangan.甲, Tiangan.己})],
    TianganRelation.克 : [frozenset({Tiangan.庚, Tiangan.甲})],
  }, tiangan_utils.discover_mutual(bazi.four_tiangans, tuple(gz.tiangan for gz in ganzhis)))

  assert _check_dizhi({
    DizhiRelation.六合 : [frozenset({Dizhi.辰, Dizhi.酉}), frozenset({Dizhi.巳, Dizhi.申})],
    DizhiRelation.刑 : [frozenset({Dizhi.辰}), frozenset({Dizhi.巳, Dizhi.申})], # LOOSE mode is used.
    DizhiRelation.破 : [frozenset({Dizhi.巳, Dizhi.申})],
  }, dizhi_utils.discover_mutual(bazi.four_dizhis, tuple(gz.dizhi for gz in ganzhis)))

  # 2052 dayun and liunian - transits only
  ganzhis = _at_year(transit_chart, 2052).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  ).ganzhis

  assert _check_tiangan({
    TianganRelation.冲 : [frozenset({Tiangan.丙, Tiangan.壬})],
  }, tiangan_utils.discover(tuple(gz.tiangan for gz in ganzhis)))

  assert _check_dizhi({
    DizhiRelation.冲 : [frozenset({Dizhi.寅, Dizhi.申})],
    DizhiRelation.刑 : [frozenset({Dizhi.寅, Dizhi.申})],
  }, dizhi_utils.discover(tuple(gz.dizhi for gz in ganzhis)))

  # 2052 dayun and liunian - between transits and at-birth
  ganzhis = _at_year(transit_chart, 2052).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  ).ganzhis

  assert _check_tiangan({
    TianganRelation.合 : [frozenset({Tiangan.丙, Tiangan.辛})],
  }, tiangan_utils.discover_mutual(bazi.four_tiangans, tuple(gz.tiangan for gz in ganzhis)))

  assert _check_dizhi({
    DizhiRelation.六合 : [frozenset({Dizhi.巳, Dizhi.申})],
    DizhiRelation.破 : [frozenset({Dizhi.巳, Dizhi.申})],
    DizhiRelation.刑 : [frozenset({Dizhi.寅, Dizhi.巳, Dizhi.申}),
                       frozenset({Dizhi.寅, Dizhi.巳}),
                       frozenset({Dizhi.巳, Dizhi.申}),],
  }, dizhi_utils.discover_mutual(bazi.four_dizhis, tuple(gz.dizhi for gz in ganzhis)))

  # 2062 dayun and liunian - transits only
  ganzhis = _at_year(transit_chart, 2062).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  ).ganzhis

  assert _check_dizhi({
    DizhiRelation.害 : [frozenset({Dizhi.丑, Dizhi.午})],
  }, dizhi_utils.discover(tuple(gz.dizhi for gz in ganzhis)))

  # 2062 dayun and liunian - between transits and at-birth
  ganzhis = _at_year(transit_chart, 2062).select(
    TransitKind.DAYUN,
    TransitKind.LIUNIAN,
  ).ganzhis

  assert _check_tiangan({
    TianganRelation.冲 : [frozenset({Tiangan.乙, Tiangan.辛})],
    TianganRelation.克 : [frozenset({Tiangan.乙, Tiangan.己})],
  }, tiangan_utils.discover_mutual(bazi.four_tiangans, tuple(gz.tiangan for gz in ganzhis)))

  assert _check_dizhi({
    DizhiRelation.六合 : [frozenset({Dizhi.午, Dizhi.未})],
    DizhiRelation.三合 : [frozenset({Dizhi.巳, Dizhi.酉, Dizhi.丑})],
    DizhiRelation.三会 : [frozenset({Dizhi.巳, Dizhi.午, Dizhi.未})],
    DizhiRelation.刑 : [frozenset({Dizhi.丑, Dizhi.未})], # LOOSE mode is used here...
    DizhiRelation.冲 : [frozenset({Dizhi.丑, Dizhi.未})],
    DizhiRelation.破 : [frozenset({Dizhi.丑, Dizhi.辰})],
  }, dizhi_utils.discover_mutual(bazi.four_dizhis, tuple(gz.dizhi for gz in ganzhis)))
