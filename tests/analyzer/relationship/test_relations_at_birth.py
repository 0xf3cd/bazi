# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relations_at_birth.py

import pytest

import random
from datetime import datetime

from bazi.defines import Dizhi, DizhiRelation
from bazi.utils import tiangan_utils, dizhi_utils
from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.rules import DizhiRules
from bazi.school import BaziConfig, BaziSchool
from bazi.analyzer.relationship import RelationshipAnalyzer

from relationship_samples import GONG_RELATIONS, project_gong, discoveries_equal


@pytest.mark.slow
def test_at_birth_day_master_relations(rng: random.Random) -> None:
  for _ in range(100):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    analyzer = RelationshipAnalyzer(chart)

    dm = chart.bazi.day_master
    at_birth = analyzer.at_birth

    assert at_birth.day_master_relations == tiangan_utils.discover_mutual([
      chart.bazi.year_pillar.tiangan,
      chart.bazi.month_pillar.tiangan,
      chart.bazi.hour_pillar.tiangan
    ], [dm])
    assert at_birth.day_master_relations == at_birth.day_master_relations # Repeated lookup must answer the same.


@pytest.mark.slow
def test_at_birth_house_relations(rng: random.Random) -> None:
  for _ in range(100):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    analyzer = RelationshipAnalyzer(chart)

    y, m, d, h = chart.bazi.four_dizhis
    at_birth = analyzer.at_birth

    # The oracle mirrors the analyzer by reading the chart's school profile (issue #69).
    school: BaziSchool = chart.bazi.config.school

    # For AtBirth analysis, the following two algorithms are equivalent.
    existing = dizhi_utils.discover(
      [y, m, d, h], definitions=school.relation_definitions,
    ).filter(
      lambda _, combo : d in combo
    )
    gong = project_gong(
      dizhi_utils.discover_ganzhis(chart.bazi.pillars, definitions=school.relation_definitions),
      lambda combo : any(occurrence.index == 2 for occurrence in combo),
    )
    assert discoveries_equal(at_birth.house_relations, existing.merge(gong))

    existing_mutual = dizhi_utils.discover_mutual(
      [y, m, h], [d], definitions=school.relation_definitions,
    )
    actual_without_gong = dizhi_utils.DizhiRelationDiscovery({
      relation : combos
      for relation, combos in at_birth.house_relations.items()
      if relation not in GONG_RELATIONS
    })
    assert actual_without_gong == existing_mutual

    assert at_birth.house_relations == at_birth.house_relations # Repeated lookup must answer the same.


@pytest.mark.slow
def test_at_birth_star_relations(rng: random.Random) -> None:
  for _ in range(100):
    chart = BaziChart.random(rng=rng)
    print(f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}')
    analyzer = RelationshipAnalyzer(chart)

    at_birth = analyzer.at_birth
    stars = chart.relationship_stars

    for tg_combos in at_birth.star_relations.tiangan.values():
      for tg_combo in tg_combos:
        assert stars.tiangan in tg_combo
    for dz_combos in at_birth.star_relations.dizhi.values():
      for dz_combo in dz_combos:
        assert any(dz in dz_combo for dz in stars.dizhi)

    assert at_birth.star_relations.tiangan == at_birth.star_relations.tiangan # Repeated lookup must answer the same.
    assert at_birth.star_relations.dizhi == at_birth.star_relations.dizhi # Repeated lookup must answer the same.


def test_gong_relations_use_concrete_participants() -> None:
  positive = BaziChart(Bazi.create(datetime(1980, 1, 12, 20), BaziGender.MALE))
  assert dizhi_utils.DizhiCombo((Dizhi.申, Dizhi.戌)) in (
    RelationshipAnalyzer(positive).at_birth.house_relations[DizhiRelation.拱会]
  )

  # The day branch repeats the year branch, but only the year/month occurrences form 拱会.
  # A value-only house filter would incorrectly retain it for the day pillar.
  repeated_house = BaziChart(Bazi.create(datetime(1912, 1, 12, 2), BaziGender.MALE))
  assert repeated_house.bazi.year_pillar.dizhi is repeated_house.bazi.day_pillar.dizhi
  assert DizhiRelation.拱会 not in RelationshipAnalyzer(repeated_house).at_birth.house_relations

  wide_birth_time = datetime(1980, 1, 6, 12)
  default_wide = BaziChart(Bazi.create(wide_birth_time, BaziGender.MALE))
  assert DizhiRelation.拱合 not in RelationshipAnalyzer(default_wide).at_birth.house_relations
  wide = BaziChart(Bazi.create(
    wide_birth_time,
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)),
  ))
  assert dizhi_utils.DizhiCombo((Dizhi.寅, Dizhi.午)) in (
    RelationshipAnalyzer(wide).at_birth.house_relations[DizhiRelation.拱合]
  )


def test_gong_relations_reach_stars_read_school() -> None:
  birth_time = datetime(1980, 1, 21, 2)
  default_chart = BaziChart(Bazi.create(birth_time, BaziGender.MALE))
  combo = dizhi_utils.DizhiCombo((Dizhi.巳, Dizhi.丑))
  assert combo in RelationshipAnalyzer(default_chart).at_birth.star_relations.dizhi[DizhiRelation.拱合]

  lu_chart = BaziChart(Bazi.create(
    birth_time,
    BaziGender.MALE,
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.LU_NARROW)),
  ))
  assert DizhiRelation.拱合 not in RelationshipAnalyzer(lu_chart).at_birth.star_relations.dizhi
