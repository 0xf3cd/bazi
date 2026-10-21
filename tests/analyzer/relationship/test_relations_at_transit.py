# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relations_at_transit.py

import pytest

import random
from datetime import datetime

from bazi.defines import Dizhi, Ganzhi, Shishen, DizhiRelation
from bazi.utils import tiangan_utils, dizhi_utils, bazi_utils
from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.rules import DizhiRules
from bazi.school import BaziConfig, BaziSchool
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind, TransitSet
from bazi.analyzer.relationship import RelationshipAnalyzer, TransitAnalysis

from relationship_samples import project_gong, discoveries_equal, at_year, random_year_transits


@pytest.mark.slow
def test_transit_day_master_relations(rng: random.Random) -> None:
  for _ in range(32):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = random_year_transits(transit_chart, random_year, rng)

      transit_tg = tuple(gz.tiangan for gz in transits.ganzhis)
      expected = tiangan_utils.discover_mutual([chart.bazi.day_master], transit_tg)
      actual = transits_analysis.day_master_relations(transits)

      assert discoveries_equal(expected, actual)


@pytest.mark.slow
def test_transit_house_relations(rng: random.Random) -> None:
  for _ in range(32):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    house = chart.house_of_relationship
    bazi = chart.bazi
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = random_year_transits(transit_chart, random_year, rng)

      transit_dz = [gz.dizhi for gz in transits.ganzhis]

      actual = transits_analysis.house_relations(transits)
      for combos in actual.values():
        for combo in combos:
          assert house in combo
          assert not set(transit_dz).isdisjoint(combo)

      def __expected_filter(dz_rel: DizhiRelation, combo: dizhi_utils.DizhiCombo):
        # `house` must appear in the combo.
        if house not in combo:
          return False

        # Special handling for 自刑 cases.
        if len(combo) == 1:
          assert dz_rel is DizhiRelation.刑
          return house in transit_dz

        return not (combo - {house}).isdisjoint(transit_dz)

      expected = dizhi_utils.discover_mutual(
        bazi.four_dizhis, transit_dz,
        definitions=bazi.config.school.relation_definitions, # The oracle mirrors the chart's school (issue #69).
      ).filter(__expected_filter)

      gong = project_gong(
        dizhi_utils.discover_mutual_ganzhis(
          bazi.pillars,
          transits.ganzhis,
          definitions=bazi.config.school.relation_definitions,
        ),
        lambda combo : any(occurrence.index == 2 for occurrence in combo),
      )
      expected = expected.merge(gong)

      assert discoveries_equal(expected, actual)


@pytest.fixture
def gong_chart() -> BaziChart:
  chart = BaziChart(Bazi.create(datetime(1980, 1, 12, 20), BaziGender.MALE))
  return chart


def test_transit_gong_rejects_filled_gap(gong_chart: BaziChart) -> None:
  chart = gong_chart
  analysis = RelationshipAnalyzer(chart).transits
  combo = dizhi_utils.DizhiCombo((Dizhi.申, Dizhi.辰))

  transits = TransitSet(liunian=Ganzhi.from_str('甲辰'))
  assert combo in analysis.house_relations(transits)[DizhiRelation.拱合]

  filled = TransitSet(
    dayun=Ganzhi.from_str('甲辰'),
    liunian=Ganzhi.from_str('甲子'),
  )
  assert combo not in analysis.house_relations(filled).get(DizhiRelation.拱合, ())


def test_transit_gong_obeys_school_scope(gong_chart: BaziChart) -> None:
  chart = gong_chart
  analysis = RelationshipAnalyzer(chart).transits
  wide_only = TransitSet(liunian=Ganzhi.from_str('甲子'))
  assert DizhiRelation.拱合 not in analysis.house_relations(wide_only)
  wide_chart = BaziChart(Bazi.create(
    datetime(1980, 1, 12, 20),
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)),
  ))
  assert dizhi_utils.DizhiCombo((Dizhi.申, Dizhi.子)) in (
    RelationshipAnalyzer(wide_chart).transits.house_relations(wide_only)[DizhiRelation.拱合]
  )


def test_transit_gonghui_hits_mutual_scope(gong_chart: BaziChart) -> None:
  chart = gong_chart
  analysis = RelationshipAnalyzer(chart).transits
  gonghui = TransitSet(liunian=Ganzhi.from_str('甲戌'))
  assert dizhi_utils.DizhiCombo((Dizhi.申, Dizhi.戌)) in (
    analysis.house_relations(gonghui)[DizhiRelation.拱会]
  )


def test_transit_gong_relations_reach_stars() -> None:
  chart = BaziChart(Bazi.create(datetime(1980, 1, 21, 2), BaziGender.MALE))
  analysis = RelationshipAnalyzer(chart).transits
  transits = TransitSet(liunian=Ganzhi.from_str('癸丑'))
  combo = dizhi_utils.DizhiCombo((Dizhi.巳, Dizhi.丑))

  mutual = analysis.star_relations(transits, level=TransitAnalysis.Level.MUTUAL)
  assert combo in mutual.dizhi[DizhiRelation.拱合]
  assert DizhiRelation.拱合 not in analysis.star_relations(
    transits,
    level=TransitAnalysis.Level.TRANSITS_ONLY,
  ).dizhi

  star_birth_time = datetime(1984, 2, 17)
  star_chart = BaziChart(Bazi.create(star_birth_time, BaziGender.MALE))
  star_analysis = RelationshipAnalyzer(star_chart).transits
  wide_transits = TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('甲午'),
  )
  assert DizhiRelation.拱合 not in star_analysis.star_relations(
    wide_transits,
    level=TransitAnalysis.Level.TRANSITS_ONLY,
  ).dizhi

  wide_star_chart = BaziChart(Bazi.create(
    star_birth_time,
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)),
  ))
  wide_star_relations = RelationshipAnalyzer(wide_star_chart).transits.star_relations(
    wide_transits,
    level=TransitAnalysis.Level.TRANSITS_ONLY,
  )
  assert dizhi_utils.DizhiCombo((Dizhi.寅, Dizhi.午)) in (
    wide_star_relations.dizhi[DizhiRelation.拱合]
  )

  full = TransitSet(
    dayun=Ganzhi.from_str('甲寅'),
    liunian=Ganzhi.from_str('甲午'),
    liuyue=Ganzhi.from_str('甲辰'),
  )
  narrow = full.select(TransitKind.DAYUN, TransitKind.LIUYUE)
  assert DizhiRelation.拱会 not in star_analysis.star_relations(
    full,
    level=TransitAnalysis.Level.TRANSITS_ONLY,
  ).dizhi
  assert dizhi_utils.DizhiCombo((Dizhi.寅, Dizhi.辰)) in star_analysis.star_relations(
    narrow,
    level=TransitAnalysis.Level.TRANSITS_ONLY,
  ).dizhi[DizhiRelation.拱会]


@pytest.mark.slow
def test_transit_star_relations(rng: random.Random) -> None:
  for _ in range(32):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    stars = chart.relationship_stars

    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(64):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = random_year_transits(transit_chart, random_year, rng)
      random_level = rng.choice([
        TransitAnalysis.Level.TRANSITS_ONLY,
        TransitAnalysis.Level.MUTUAL,
        TransitAnalysis.Level.ALL
      ]) # mypy with Python 3.12 is problematic here on type checking... Explicitly list all enum values.

      transit_tg = tuple(gz.tiangan for gz in transits.ganzhis)
      transit_dz = tuple(gz.dizhi for gz in transits.ganzhis)

      tg_discovery = tiangan_utils.TianganRelationDiscovery({})
      dz_discovery = dizhi_utils.DizhiRelationDiscovery({})
      # The oracle mirrors the analyzer by reading the chart's school profile (issue #69).
      school: BaziSchool = chart.bazi.config.school
      if random_level in [TransitAnalysis.Level.TRANSITS_ONLY, TransitAnalysis.Level.ALL]:
        tg_discovery = tg_discovery.merge(tiangan_utils.discover(transit_tg))
        dz_discovery = dz_discovery.merge(dizhi_utils.discover(transit_dz, definitions=school.relation_definitions))
        dz_discovery = dz_discovery.merge(project_gong(
          dizhi_utils.discover_ganzhis(transits.ganzhis, definitions=school.relation_definitions),
          lambda _: True,
        ))
      if random_level in [TransitAnalysis.Level.MUTUAL, TransitAnalysis.Level.ALL]:
        tg_discovery = tg_discovery.merge(tiangan_utils.discover_mutual(chart.bazi.four_tiangans, transit_tg))
        dz_discovery = dz_discovery.merge(dizhi_utils.discover_mutual(chart.bazi.four_dizhis, transit_dz, definitions=school.relation_definitions))
        dz_discovery = dz_discovery.merge(project_gong(
          dizhi_utils.discover_mutual_ganzhis(
            chart.bazi.pillars,
            transits.ganzhis,
            definitions=school.relation_definitions,
          ),
          lambda _: True,
        ))

      actual = transits_analysis.star_relations(transits, level=random_level)

      # Tiangan
      for tg_rel, tg_combos in actual.tiangan.items():
        assert tg_rel in tg_discovery
        for tg_combo in tg_combos:
          assert tg_combo in tg_discovery[tg_rel]

      for tg_rel, tg_combos in tg_discovery.items():
        for tg_combo in tg_combos:
          if stars.tiangan in tg_combo:
            assert tg_combo in actual.tiangan[tg_rel]

      assert discoveries_equal(actual.tiangan, tg_discovery.filter(
        lambda _, combo : stars.tiangan in combo
      ))

      # Dizhi
      for dz_rel, dz_combos in actual.dizhi.items():
        assert dz_rel in dz_discovery
        for dz_combo in dz_combos:
          assert dz_combo in dz_discovery[dz_rel]

      for dz_rel, dz_combos in dz_discovery.items():
        for dz_combo in dz_combos:
          if len(dz_combo & set(stars.dizhi)) > 0:
            assert dz_combo in actual.dizhi[dz_rel]

      assert discoveries_equal(actual.dizhi, dz_discovery.filter(
        lambda _, combo : len(combo & set(stars.dizhi)) > 0
      ))


@pytest.mark.slow
def test_zhengyin(rng: random.Random) -> None:
  for _ in range(32):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(128):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = random_year_transits(transit_chart, random_year, rng)

      expected_tg: bool = False
      expected_dz: bool = False
      for gz in transits.ganzhis:
        if bazi_utils.shishen(chart.bazi.day_master, gz.tiangan) == Shishen.正印:
          expected_tg = True
        if bazi_utils.shishen(chart.bazi.day_master, gz.dizhi) == Shishen.正印:
          expected_dz = True

      actual = transits_analysis.zhengyin(transits)
      assert expected_tg == actual.tiangan
      assert expected_dz == actual.dizhi


@pytest.mark.slow
def test_star(rng: random.Random) -> None:
  for _ in range(16):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    transit_chart = TransitChart(chart)
    analyzer = RelationshipAnalyzer(chart)
    transits_analysis = analyzer.transits

    for __ in range(64):
      random_year = chart.bazi.ganzhi_year + rng.randint(0, 100)
      transits = random_year_transits(transit_chart, random_year, rng)

      expected_tg: bool = False
      expected_dz: bool = False
      for gz in transits.ganzhis:
        if gz.tiangan == chart.relationship_stars.tiangan:
          expected_tg = True
        if gz.dizhi in chart.relationship_stars.dizhi:
          expected_dz = True

      actual = transits_analysis.star(transits)
      assert expected_tg == actual.tiangan
      assert expected_dz == actual.dizhi


def test_transit_analysis_negative(rng: random.Random) -> None:
  chart = BaziChart.random(rng=rng)
  transits_analysis = RelationshipAnalyzer(chart).transits

  for analysis in (transits_analysis.shensha, transits_analysis.day_master_relations,
                   transits_analysis.house_relations, transits_analysis.star_relations,
                   transits_analysis.zhengyin, transits_analysis.star):
    with pytest.raises(TypeError):
      analysis(object()) # type: ignore

  transits = at_year(TransitChart(chart), chart.bazi.ganzhi_year).select(TransitKind.LIUNIAN)
  with pytest.raises(TypeError):
    transits_analysis.star_relations(transits, level=0x8) # type: ignore
  # IntFlag happily constructs pseudo-members (undefined bit / empty flag); the gate rejects them by value.
  with pytest.raises(ValueError):
    transits_analysis.star_relations(transits, level=TransitAnalysis.Level(0x8))
  with pytest.raises(ValueError):
    transits_analysis.star_relations(transits, level=TransitAnalysis.Level(0))
