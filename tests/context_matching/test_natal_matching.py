# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json

import pytest

from bazi.context_matching import ContextProfile, ContextResult, _BINDINGS, _binding_digest, evaluate_context
from bazi.defines import Shishen
from bazi.knowledge import KnowledgeBase
from bazi.transits import TransitKind

from matching_samples import GUANSHA, FEMALE, LEGAL, RELATIONSHIP, CONDITION_CLAIMS, chart, match


@pytest.mark.parametrize('claim_id', LEGAL + RELATIONSHIP + tuple(CONDITION_CLAIMS.values()))
def test_builtin_editorial_binding_fingerprint(claim_id: str) -> None:
  knowledge = KnowledgeBase.load()
  computed = _binding_digest(knowledge, knowledge.entry(claim_id))
  assert computed == _BINDINGS.get(claim_id), (
    f'Binding fingerprint mismatch for {claim_id}: computed {computed}. '
    'Re-pin _BINDINGS in bazi/context_matching.py.'
  )


def test_literal_witnesses_and_negative_control() -> None:
  result = match()
  assert json.loads(result.input_json)['pillars'] == ['己卯', '丙子', '庚申', '壬午']
  # This oracle is a literal ordered inventory, not a call to the production classifier.
  expected = (
    ('year', 0, '己卯', 'visible', '己', '正印'),
    ('year', 0, '己卯', 'hidden', '乙', '正财'),
    ('month', 1, '丙子', 'visible', '丙', '七杀'),
    ('month', 1, '丙子', 'hidden', '癸', '伤官'),
    ('day', 2, '庚申', 'hidden', '庚', '比肩'),
    ('day', 2, '庚申', 'hidden', '壬', '食神'),
    ('day', 2, '庚申', 'hidden', '戊', '偏印'),
    ('hour', 3, '壬午', 'visible', '壬', '食神'),
    ('hour', 3, '壬午', 'hidden', '丁', '正官'),
    ('hour', 3, '壬午', 'hidden', '己', '正印'),
  )
  assert tuple((o.pillar, o.index, str(o.ganzhi), o.layer, str(o.stem), str(o.shishen)) for o in result.occurrences) == expected
  assert all(o.origin == 'natal' and o.kind is None and o.ganzhi_year is None for o in result.occurrences)
  assert result.criterion.status == 'SATISFIED' and result.criterion.scope_complete
  assert result.criterion.reason == 'premise_satisfied'
  assert tuple(m.claim_id for m in result.entries) == LEGAL
  assert all(m.status == 'SATISFIED' for m in result.entries)
  visible = {o.shishen for o in result.occurrences if o.layer == 'visible'}
  assert not {Shishen.正官, Shishen.七杀} <= visible
  assert chart().shishen.day.tiangan is None


def test_non_main_hidden_stem_is_in_scope() -> None:
  # 辰藏乙 is secondary qi: a LIUNIAN must retain it, independently of its percentage.
  result = match(1, profile=ContextProfile('natal_and_liunian', 2024))
  assert tuple((str(o.stem), str(o.shishen)) for o in result.occurrences if o.origin == 'transit' and o.layer == 'hidden') == (
    ('戊', '比肩'), ('乙', '正官'), ('癸', '正财'),
  )
  assert result.criterion.status == 'SATISFIED'


def test_duplicate_pillars_keep_all_occurrences() -> None:
  result = match(1)
  assert json.loads(result.input_json)['pillars'] == ['己卯', '丙子', '戊午', '戊午']
  repeated = [(o.pillar, o.index, str(o.ganzhi), str(o.stem)) for o in result.occurrences if o.layer == 'hidden' and o.ganzhi.dizhi.name == 'WU']
  assert repeated == [('day', 2, '戊午', '丁'), ('day', 2, '戊午', '己'), ('hour', 3, '戊午', '丁'), ('hour', 3, '戊午', '己')]
  assert result.criterion.status == 'NOT_SATISFIED'
  assert result.criterion.reason == 'required_classification_absent'
  assert len(result.occurrences) == 9


def test_visible_guansha_satisfies_premise() -> None:
  result = evaluate_context(chart(5, hour=16), criterion_id=GUANSHA, profile=ContextProfile('natal'), include_reference_only=True)
  assert json.loads(result.input_json)['pillars'] == ['己卯', '丙子', '壬戌', '戊申']
  assert {(o.pillar, str(o.stem), str(o.shishen)) for o in result.occurrences if o.layer == 'visible' and o.shishen in (Shishen.正官, Shishen.七杀)} == {
    ('year', '己', '正官'), ('hour', '戊', '七杀'),
  }


def test_female_premise_rejects_male_chart() -> None:
  female, male = match(criterion_id=FEMALE), match(gender='male', criterion_id=FEMALE)
  assert female.criterion.status == 'SATISFIED'
  assert male.criterion.status == 'NOT_SATISFIED' and male.criterion.reason == 'female_gate_false'
  assert male.criterion.observations['observed_coexistence'] is True
  assert male.criterion.observations['female'] is False
  assert tuple(m.claim_id for m in female.entries) == RELATIONSHIP
  assert all(m.status == 'NOT_SATISFIED' for m in male.entries)
  assert match(gender='male').criterion.status == 'SATISFIED'


def test_liunian_kind_and_cycle_identity() -> None:
  natal = match(1)
  first = match(1, profile=ContextProfile('natal_and_liunian', 2024))
  next_cycle = match(1, profile=ContextProfile('natal_and_liunian', 2084))
  assert natal.criterion.status == 'NOT_SATISFIED'
  assert first.criterion.status == next_cycle.criterion.status == 'SATISFIED'
  assert first != next_cycle
  assert isinstance(first.profile, ContextProfile) and isinstance(next_cycle.profile, ContextProfile)
  assert first.profile.ganzhi_year == 2024 and next_cycle.profile.ganzhi_year == 2084
  for result, year in ((first, 2024), (next_cycle, 2084)):
    transit = [o for o in result.occurrences if o.origin == 'transit']
    assert len(transit) == 4
    assert all(o.kind is TransitKind.LIUNIAN and o.index == 4 and o.pillar == 'liunian' and o.ganzhi_year == year and str(o.ganzhi) == '甲辰' for o in transit)
    assert [(o.layer, str(o.stem), str(o.shishen)) for o in transit] == [
      ('visible', '甲', '七杀'), ('hidden', '戊', '比肩'), ('hidden', '乙', '正官'), ('hidden', '癸', '正财'),
    ]
    assert ContextResult.from_json(result.export_json()) == result
  assert [(o.pillar, str(o.stem), str(o.shishen)) for o in first.occurrences] == [(o.pillar, str(o.stem), str(o.shishen)) for o in next_cycle.occurrences]


def test_liunian_label_has_no_calendar_cutoff() -> None:
  # at_year has no calendar-data upper cutoff: preserve that existing label contract.
  assert match(1, profile=ContextProfile('natal_and_liunian', 10000)).criterion.scope_complete


def test_export_keeps_evidence_year_kind_input() -> None:
  result = match(1, profile=ContextProfile('natal_and_liunian', 2024))
  data = json.loads(result.export_json())
  assert data['record_version'] == 4
  assert data['profile'] == {'observation_scope': 'natal_and_liunian', 'ganzhi_year': 2024}
  assert data['input'] == json.loads(result.input_json)
  assert len(data['occurrences']) == 13
  assert data['occurrences'][-3:] == [
    {'origin': 'transit', 'pillar': 'liunian', 'ganzhi': '甲辰', 'layer': 'hidden', 'stem': stem, 'shishen': classification, 'kind': 'liunian', 'ganzhi_year': 2024}
    for stem, classification in [('戊', '比肩'), ('乙', '正官'), ('癸', '正财')]
  ]
