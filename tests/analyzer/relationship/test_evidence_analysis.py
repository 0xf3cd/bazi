# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_evidence_analysis.py

import pytest

from datetime import datetime
from collections.abc import Sequence
from dataclasses import replace
from typing import Any

from bazi.defines import Tiangan, Dizhi, Ganzhi, DizhiRelation, TianganRelation
from bazi.utils import tiangan_utils, dizhi_utils
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.rules import DizhiRules
from bazi.school import BaziConfig, BaziSchool, PeiouXingDef
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind, TransitSet
from bazi.analyzer.relationship import (
  RelationshipEvidence, StarAppearance, StemRelationDiscovery, _discover_stem_occurrences, spouse_evidence,
)


def _at(combo: frozenset) -> set[int]:
  return {occurrence.index for occurrence in combo}


def test_stem_occurrences_expand_per_position() -> None:
  left = [Ganzhi.from_str(value) for value in ('甲子', '己丑', '丙寅', '己卯')]
  right = [Ganzhi.from_str(value) for value in ('甲子', '丙寅', '己丑', '己卯')]
  left_discovery = _discover_stem_occurrences(left)
  right_discovery = _discover_stem_occurrences(right)
  assert [_at(combo) for combo in left_discovery[TianganRelation.合]] == [{0, 1}, {0, 3}]
  assert [_at(combo) for combo in right_discovery[TianganRelation.合]] == [{0, 2}, {0, 3}]
  assert tiangan_utils.discover([gz.tiangan for gz in left]) == tiangan_utils.discover([gz.tiangan for gz in right])
  assert left_discovery != right_discovery
  # The day master's visible stem (position 0 here) may appear as a real participant; combos carry no direction.
  for discovery in (left_discovery, right_discovery):
    assert all(0 in _at(combo) for combo in discovery[TianganRelation.合])

  # Hidden stems never enter Tiangan combos: 子 hides 癸, 辰 hides 戊, else 癸 at 子 and visible 戊 at 辰 would 合.
  hidden_carrier = [Ganzhi.from_str('甲子'), Ganzhi.from_str('戊辰')]
  assert TianganRelation.合 not in _discover_stem_occurrences(hidden_carrier)


def test_evidence_transit_relations_shift_indexes() -> None:
  # A 丙 day-master male chart (2000-01-09T12:00, 己卯丁丑丙寅甲午): target stem 辛, target branch 酉.
  chart = BaziChart(Bazi.create(datetime(2000, 1, 9, 12), 'male'))
  transits = TransitSet(
    xiaoyun=Ganzhi.from_str('丙戌'),
    dayun=Ganzhi.from_str('甲申'),
    liunian=Ganzhi.from_str('丁酉'),
  )
  evidence = spouse_evidence(chart, transits)
  assert isinstance(evidence, RelationshipEvidence)
  assert evidence.star_target.tiangan is Tiangan.辛
  assert evidence.star_target.dizhi == (Dizhi.酉,)
  assert evidence.transits is transits

  # Transit-internal 三会 申酉戌: indexes 4, 5, 6.
  assert [_at(combo) for combo in evidence.star_relations[DizhiRelation.三会]] == [{4, 5, 6}]
  # It has no day pillar, so no house evidence; it has 酉 (the spouse-star branch), so it enters star evidence.
  assert DizhiRelation.三会 not in evidence.house_relations
  # Every house-evidence combo contains the day pillar as a specific occurrence (index 2).
  for combos in evidence.house_relations.values():
    assert all(2 in _at(combo) for combo in combos)
  # Every stem-evidence combo contains the target stem; this chart has no visible 辛, so the key is empty.
  assert evidence.stem_relations == StemRelationDiscovery({})

  # One liunian forms no internal relation and cannot verify numbering; internal relations need two or more transits (above).
  single = spouse_evidence(chart, TransitSet(liunian=Ganzhi.from_str('甲辰')))
  assert single.transits is not None and single.transits.json == {'liunian': '甲辰'}
  for discovery in (single.house_relations, single.star_relations):
    for combos in discovery.values():
      for combo in combos:
        # A single-liunian combo cannot have all indexes >= 4; cross-group combos (like 1, 4) may exist.
        assert not all(index >= 4 for index in _at(combo))


def test_evidence_gong_scopes_not_suppressed() -> None:
  # Natal 甲申、甲戌 拱 酉 with the transit bringing 酉: the natal-internal 拱会 (2,3) stays, not suppressed by the fill-in.
  natal_gong = BaziChart(Bazi.create(datetime(1998, 8, 5, 20), 'male'))
  assert tuple(map(str, natal_gong.bazi.pillars)) == ('戊寅', '己未', '甲申', '甲戌')
  filled = spouse_evidence(natal_gong, TransitSet(liunian=Ganzhi.from_str('己酉')))
  assert [_at(combo) for combo in filled.house_relations[DizhiRelation.拱会]] == [{2, 3}]

  # Mirror: transit-internal 甲申、甲戌 拱 酉 while the natal has 酉, so transit-internal 拱会 (4,5) stays.
  # 癸 day-master female: target stem 戊, target branches 辰戌; 戌 is a real branch participant, so the 拱会 enters star evidence.
  transit_gong = BaziChart(Bazi.create(datetime(1969, 9, 25, 6), 'female'))
  assert tuple(map(str, transit_gong.bazi.pillars)) == ('己酉', '癸酉', '癸卯', '乙卯')
  mirrored = spouse_evidence(transit_gong, TransitSet(
    dayun=Ganzhi.from_str('甲申'),
    liunian=Ganzhi.from_str('甲戌'),
  ))
  assert mirrored.star_target.tiangan is Tiangan.戊
  assert [_at(combo) for combo in mirrored.star_relations[DizhiRelation.拱会]] == [{4, 5}]


def test_evidence_reads_school_in_all_calls() -> None:
  # 刑 follows xing_def: on the same real chart (庚辰辛巳丙寅甲午), LOOSE forms a 刑 between day pillar (寅) and 巳,
  # STRICT does not. 拱 follows gong_def: 戊寅己未甲申甲戌 has natal-internal 拱会 under both SAME_STEM levels,
  # none under TRANSFORMING_NARROW (no metal stem) or LU_NARROW (禄 level has no 拱会).
  for xing_def, expected in (
    (DizhiRules.XingDef.LOOSE, [{1, 2}]),
    (DizhiRules.XingDef.STRICT, []),
  ):
    chart = BaziChart(Bazi.create(
      datetime(2000, 5, 8, 12), 'male',
      BaziConfig(school=BaziSchool(xing_def=xing_def)),
    ))
    assert tuple(map(str, chart.bazi.pillars)) == ('庚辰', '辛巳', '丙寅', '甲午')
    evidence = spouse_evidence(chart, None)
    assert [{o.index for o in combo} for combo in evidence.house_relations.get(DizhiRelation.刑, ())] == expected

  # 冲 and 自刑 ignore xing_def: on 己卯丙子戊午戊午 the 子午 冲 and 午午 自刑 give the same result under both levels.
  for xing_def in DizhiRules.XingDef:
    chart = BaziChart(Bazi.create(
      datetime(2000, 1, 1, 12), 'male',
      BaziConfig(school=BaziSchool(xing_def=xing_def)),
    ))
    evidence = spouse_evidence(chart, None)
    assert [_at(combo) for combo in evidence.house_relations[DizhiRelation.冲]] == [{1, 2}]
    assert [_at(combo) for combo in evidence.house_relations[DizhiRelation.刑]] == [{2, 3}]

  for gong_def, expected in (
    (DizhiRules.GongDef.SAME_STEM_NARROW, [{2, 3}]),
    (DizhiRules.GongDef.SAME_STEM_WIDE, [{2, 3}]),
    (DizhiRules.GongDef.TRANSFORMING_NARROW, []),
    (DizhiRules.GongDef.LU_NARROW, []),
  ):
    chart = BaziChart(Bazi.create(
      datetime(1998, 8, 5, 20), 'male',
      BaziConfig(school=BaziSchool(gong_def=gong_def)),
    ))
    evidence = spouse_evidence(chart, None)
    assert [_at(combo) for combo in evidence.house_relations.get(DizhiRelation.拱会, ())] == expected


def test_evidence_cross_group_gong_participants() -> None:
  # Male chart 戊寅己未甲申甲戌: the chosen liunian 甲戌 (explicit TransitSet, the function's declared input) 拱 酉
  # with the day pillar; the cross-group 拱会 is exactly {2,4}: index 2 is day pillar 甲申, index 4 is the chosen
  # liunian (transits start at 4); natal-internal 拱会 {2,3} stays, not suppressed by the liunian filling the 拱.
  chart = BaziChart(Bazi.create(datetime(1998, 8, 5, 20), 'male'))
  evidence = spouse_evidence(chart, TransitSet(liunian=Ganzhi.from_str('甲戌')))
  assert [_at(combo) for combo in evidence.house_relations[DizhiRelation.拱会]] == [{2, 3}, {2, 4}]
  participants = {
    occurrence.index: str(occurrence.ganzhi)
    for combo in evidence.house_relations[DizhiRelation.拱会]
    for occurrence in combo
  }
  assert participants == {2: '甲申', 3: '甲戌', 4: '甲戌'}


def test_evidence_school_flows_through_segments(monkeypatch: pytest.MonkeyPatch) -> None:
  # Male chart 戊寅己未甲申甲戌 (gong_def=SAME_STEM_WIDE): transits are queried for real by coordinate (at_year
  # 2054, 甲戌 liunian), never hand-picked ganzhi. Spies wrap the real discovery tools, recording the definitions
  # (non-拱 full sequence, natal 拱, cross-group 拱, transit-internal 拱); each must be this chart's definitions.
  chart = BaziChart(Bazi.create(
    datetime(1998, 8, 5, 20), 'male',
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)),
  ))
  queried = TransitChart(chart).at_year(2054)
  assert queried is not None and queried.liunian is not None
  transits = queried.select(TransitKind.LIUNIAN)
  definitions = chart.bazi.config.school.relation_definitions

  seen: list[tuple[str, int, bool]] = []
  original_discover = dizhi_utils.discover_ganzhis
  original_mutual = dizhi_utils.discover_mutual_ganzhis

  def __spied_discover(ganzhis: Sequence[Ganzhi], **kwargs: Any) -> dizhi_utils.GanzhiRelationDiscovery:
    # relation_definitions builds a new object each time, so the spy compares by value.
    seen.append(('discover_ganzhis', len(ganzhis), kwargs['definitions'] == definitions))
    return original_discover(ganzhis, **kwargs)

  def __spied_mutual(
    left: Sequence[Ganzhi], right: Sequence[Ganzhi], **kwargs: Any,
  ) -> dizhi_utils.GanzhiRelationDiscovery:
    seen.append(('discover_mutual_ganzhis', len(left) + len(right), kwargs['definitions'] == definitions))
    return original_mutual(left, right, **kwargs)

  monkeypatch.setattr(dizhi_utils, 'discover_ganzhis', __spied_discover)
  monkeypatch.setattr(dizhi_utils, 'discover_mutual_ganzhis', __spied_mutual)
  evidence = spouse_evidence(chart, transits)
  assert seen == [
    ('discover_ganzhis', 5, True),
    ('discover_ganzhis', 4, True),
    ('discover_mutual_ganzhis', 5, True),
    ('discover_ganzhis', 1, True),
  ]
  # Non-default gong_def changes transit-inclusive evaluation: cross-group 拱 {2,4} exists here; TRANSFORMING_NARROW on the same chart and liunian has none.
  assert [_at(combo) for combo in evidence.house_relations[DizhiRelation.拱会]] == [{2, 3}, {2, 4}]
  narrow = BaziChart(Bazi.create(
    datetime(1998, 8, 5, 20), 'male',
    BaziConfig(school=BaziSchool(gong_def=DizhiRules.GongDef.TRANSFORMING_NARROW)),
  ))
  narrow_queried = TransitChart(narrow).at_year(2054)
  assert narrow_queried is not None and narrow_queried.liunian is not None
  narrow_evidence = spouse_evidence(narrow, narrow_queried.select(TransitKind.LIUNIAN))
  assert DizhiRelation.拱会 not in narrow_evidence.house_relations


def test_evidence_star_target_follows_peiou_xing() -> None:
  # 乙 day-master male (2000-01-08T12:00, 己卯丁丑乙丑壬午): the default reading takes 戊 (辰戌), 阴阳干 takes 己 (丑未).
  default = BaziChart(Bazi.create(datetime(2000, 1, 8, 12), 'male'))
  yinyang = BaziChart(Bazi.create(
    datetime(2000, 1, 8, 12), 'male',
    BaziConfig(school=BaziSchool(peiou_xing_def=PeiouXingDef.YINYANGGAN)),
  ))
  assert tuple(map(str, default.bazi.pillars)) == ('己卯', '丁丑', '乙丑', '壬午')
  assert default.relationship_stars.tiangan is Tiangan.戊
  assert yinyang.relationship_stars.tiangan is Tiangan.己
  default_evidence = spouse_evidence(default, None)
  yinyang_evidence = spouse_evidence(yinyang, None)
  # Default reading: the natal has no 辰戌, so star evidence is empty; 阴阳干 reading: 丑 (both occurrences) joins as a target branch.
  assert default_evidence.star_relations == dizhi_utils.GanzhiRelationDiscovery({})
  assert {o.index for combo in yinyang_evidence.star_relations[DizhiRelation.害] for o in combo} == {1, 2, 3}


def test_evidence_keeps_layers_and_positions() -> None:
  # 丙 day-master male (2000-01-29T06:00, 己卯丁丑丙戌辛卯): target 辛 is 藏干 in month branch 丑 and day branch
  # 戌, 明干 in the hour stem; both layers coexist per position; the day pillar's visible slot never shows the target (never the day master).
  chart = BaziChart(Bazi.create(datetime(2000, 1, 29, 6), 'male'))
  assert tuple(map(str, chart.bazi.pillars)) == ('己卯', '丁丑', '丙戌', '辛卯')
  evidence = spouse_evidence(chart, None)
  assert [(a.origin, a.pillar, a.kind, str(a.ganzhi), a.layer, a.stem) for a in evidence.appearances] == [
    ('natal', 'month', None, '丁丑', 'hidden', Tiangan.辛),
    ('natal', 'day', None, '丙戌', 'hidden', Tiangan.辛),
    ('natal', 'hour', None, '辛卯', 'visible', Tiangan.辛),
  ]
  with_transits = spouse_evidence(chart, TransitSet(liunian=Ganzhi.from_str('辛亥')))
  assert [(a.origin, a.kind, str(a.ganzhi), a.layer) for a in with_transits.appearances if a.origin == 'transit'] == [
    ('transit', TransitKind.LIUNIAN, '辛亥', 'visible'),
  ]
  # Chosen liunian 辛酉: 酉 hides 辛, so visible and hidden layers coexist at one position, one appearance each, kind preserved.
  xinyou = spouse_evidence(chart, TransitSet(liunian=Ganzhi.from_str('辛酉')))
  assert [(a.origin, a.kind, str(a.ganzhi), a.layer) for a in xinyou.appearances if a.origin == 'transit'] == [
    ('transit', TransitKind.LIUNIAN, '辛酉', 'visible'),
    ('transit', TransitKind.LIUNIAN, '辛酉', 'hidden'),
  ]
  # Construction checks follow the ChartOccurrence style: visible stem must equal the pillar stem, hidden stem must live in its branch, exclusive coordinates rejected.
  appearance = evidence.appearances[2]
  assert appearance is not None
  value_changes: tuple[dict[str, Any], ...] = (
    {'origin': 'other'}, {'layer': 'other'}, {'layer': 'hidden'}, {'pillar': 'liunian'},
    {'kind': TransitKind.LIUNIAN}, {'stem': Tiangan.庚},
  )
  for change in value_changes:
    with pytest.raises(ValueError):
      replace(appearance, **change)
  type_changes: tuple[dict[str, Any], ...] = (
    {'ganzhi': '辛卯'}, {'stem': '辛'}, {'kind': 'liunian'},
    {'origin': 1}, {'layer': 1}, {'pillar': 1},
  )
  for change in type_changes:
    with pytest.raises(TypeError):
      replace(appearance, **change)
  # RelationshipEvidence's construction-time type gate; scope-style cross-field constraints belong to ContextResult.
  for change in (
    {'star_target': '辛'}, {'appearances': (object(),)}, {'house_relations': {}},
    {'stem_relations': {}}, {'transits': TransitChart},
  ):
    with pytest.raises(TypeError):
      replace(evidence, **change)
  assert spouse_evidence(chart, None).transits is None
  with pytest.raises(TypeError):
    spouse_evidence(chart.bazi, None) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    spouse_evidence(chart, '甲辰') # type: ignore[arg-type]
  assert StarAppearance('transit', None, TransitKind.LIUNIAN, Ganzhi.from_str('辛亥'), 'visible', Tiangan.辛)
  with pytest.raises(ValueError):
    StarAppearance('transit', 'hour', TransitKind.LIUNIAN, Ganzhi.from_str('辛亥'), 'visible', Tiangan.辛)


def test_evidence_day_pillar_is_occurrence() -> None:
  # 己卯丙子戊午戊午: day branch 午 冲 month branch 子 (1,2); the hour branch equals the day branch in value, but
  # the 子午 combo (1,3) lacks the day pillar as a specific occurrence, so it does not enter house evidence.
  chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
  assert tuple(map(str, chart.bazi.pillars)) == ('己卯', '丙子', '戊午', '戊午')
  evidence = spouse_evidence(chart, None)
  assert [_at(combo) for combo in evidence.house_relations[DizhiRelation.冲]] == [{1, 2}]
  for combos in evidence.house_relations.values():
    assert all(2 in _at(combo) for combo in combos)
    assert all(_at(combo) != {1, 3} for combo in combos)


@pytest.mark.slow
def test_non_gong_full_equals_three_segments() -> None:
  # Non-拱 relations on the full sequence equal, combo by combo, 「原局内部 ∪ 跨组 ∪ 岁运内部(+4)」; this is a seeded
  # randomized property test (seed hardcoded here), not exhaustive; 拱 is deliberately not unioned segment-wise (fill-in semantics).
  from random import Random
  from bazi.rules import DizhiRelationDefinitions
  from bazi.utils.dizhi_utils import GanzhiOccurrence, GanzhiRelationDiscovery
  rng = Random(20261015)
  non_gong = tuple(rel for rel in DizhiRelation if rel not in DizhiRules.GONG_RELATIONS)
  cycle = tuple(Ganzhi.from_str(f'{tg}{dz}') for tg in Tiangan for dz in Dizhi)

  def __shifted(discovery: GanzhiRelationDiscovery, offset: int) -> dict[DizhiRelation, set[frozenset[GanzhiOccurrence]]]:
    return {
      relation: {
        frozenset(GanzhiOccurrence(occurrence.index + offset, occurrence.ganzhi) for occurrence in combo)
        for combo in combos
      }
      for relation, combos in discovery.items()
    }

  for _ in range(40):
    natal = tuple(rng.choice(cycle) for _ in range(4))
    transits = tuple(rng.choice(cycle) for _ in range(rng.randrange(0, 5)))
    definitions = DizhiRelationDefinitions(
      anhe_def=rng.choice(tuple(DizhiRules.AnheDef)),
      xing_def=rng.choice(tuple(DizhiRules.XingDef)),
      gong_def=rng.choice(tuple(DizhiRules.GongDef)),
    )
    combined = dizhi_utils.discover_ganzhis(natal + transits, definitions=definitions, relations=non_gong)
    segments = (
      dizhi_utils.discover_ganzhis(natal, definitions=definitions, relations=non_gong),
      dizhi_utils.discover_mutual_ganzhis(natal, transits, definitions=definitions, relations=non_gong),
      dizhi_utils.discover_ganzhis(transits, definitions=definitions, relations=non_gong),
    )
    union: dict[DizhiRelation, set[frozenset[GanzhiOccurrence]]] = {}
    for index, segment in enumerate(segments):
      for relation, combos in __shifted(segment, 0 if index < 2 else 4).items():
        union.setdefault(relation, set()).update(combos)
    for relation in non_gong:
      expected = {frozenset(combo) for combo in union.get(relation, ())}
      actual = {frozenset(combo) for combo in combined.get(relation, ())}
      assert expected == actual, (relation, natal, transits)
