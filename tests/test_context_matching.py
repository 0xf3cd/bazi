# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import FrozenInstanceError, asdict, fields, replace
from datetime import datetime
from pathlib import Path
from typing import Any, get_args

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.common import frozendict
from bazi.context_matching import (
  ContextProfile, ContextResult, EntryMatch, MatchReason, MatchStatus, _BINDINGS, _binding_digest, evaluate_context,
)
from bazi.defines import Ganzhi, Tiangan, Shishen, DizhiRelation
from bazi.knowledge import (
  KnowledgeBase, KnowledgeObject, KnowledgeContext, KnowledgeSource, KnowledgeEntry, KnowledgeRole, KnowledgeRelation, LegacyDescription,
)
from bazi.school import BaziConfig, BaziSchool, DayRollover, PeiouXingDef, _config_json
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind, TransitSet


GUANSHA = 'editorial.guansha_coexistence.v1'
FEMALE = 'editorial.guansha_coexistence_female.v1'
LEGAL = ('editorial.shishen.zhengguan.legal_trouble', 'editorial.shishen.qisha.legal_trouble')
RELATIONSHIP = ('editorial.shishen.zhengguan.infidelity', 'editorial.shishen.qisha.infidelity')


def chart(day: int = 3, gender: str = 'female', hour: int = 12) -> BaziChart:
  return BaziChart(Bazi.create(datetime(2000, 1, day, hour), gender, BaziConfig.from_values(backend='celestial', precision='day')))


def match(day: int = 3, gender: str = 'female', **kwargs: Any) -> ContextResult:
  options = {'criterion_id': GUANSHA, 'profile': ContextProfile('natal'), 'include_reference_only': True, **kwargs}
  return evaluate_context(chart(day, gender), **options)


@pytest.mark.parametrize('claim_id', LEGAL + RELATIONSHIP)
def test_builtin_editorial_binding_fingerprint(claim_id: str) -> None:
  knowledge = KnowledgeBase.load()
  computed = _binding_digest(knowledge, knowledge.entry(claim_id))
  assert computed == _BINDINGS.get(claim_id), (
    f'Binding fingerprint mismatch for {claim_id}: computed {computed}. '
    'Re-pin _BINDINGS in bazi/context_matching.py.'
  )


def test_literal_natal_witnesses_and_visible_negative_control() -> None:
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


def test_visible_positive_and_female_gate() -> None:
  result = evaluate_context(chart(5, hour=16), criterion_id=GUANSHA, profile=ContextProfile('natal'), include_reference_only=True)
  assert json.loads(result.input_json)['pillars'] == ['己卯', '丙子', '壬戌', '戊申']
  assert {(o.pillar, str(o.stem), str(o.shishen)) for o in result.occurrences if o.layer == 'visible' and o.shishen in (Shishen.正官, Shishen.七杀)} == {
    ('year', '己', '正官'), ('hour', '戊', '七杀'),
  }
  female, male = match(criterion_id=FEMALE), match(gender='male', criterion_id=FEMALE)
  assert female.criterion.status == 'SATISFIED'
  assert male.criterion.status == 'NOT_SATISFIED' and male.criterion.reason == 'female_gate_false'
  assert male.criterion.observations['observed_coexistence'] is True
  assert male.criterion.observations['female'] is False
  assert tuple(m.claim_id for m in female.entries) == RELATIONSHIP
  assert all(m.status == 'NOT_SATISFIED' for m in male.entries)
  assert match(gender='male').criterion.status == 'SATISFIED'


def test_liunian_coordinate_kind_and_repeated_cycle_identity() -> None:
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
  # at_year has no calendar-data upper cutoff: preserve that existing label contract.
  assert match(1, profile=ContextProfile('natal_and_liunian', 10000)).criterion.scope_complete


def test_export_preserves_literal_evidence_year_kind_and_input() -> None:
  result = match(1, profile=ContextProfile('natal_and_liunian', 2024))
  data = json.loads(result.export_json())
  assert data['record_version'] == 3
  assert data['profile'] == {'observation_scope': 'natal_and_liunian', 'ganzhi_year': 2024}
  assert data['input'] == json.loads(result.input_json)
  assert len(data['occurrences']) == 13
  assert data['occurrences'][-3:] == [
    {'origin': 'transit', 'pillar': 'liunian', 'ganzhi': '甲辰', 'layer': 'hidden', 'stem': stem, 'shishen': classification, 'kind': 'liunian', 'ganzhi_year': 2024}
    for stem, classification in [('戊', '比肩'), ('乙', '正官'), ('癸', '正财')]
  ]


@pytest.mark.parametrize('day,year,reason', [
  (1, None, 'missing_transit_coordinate'), (3, None, 'missing_transit_coordinate'),
  (1, 1998, 'transit_unavailable'), (1, 0, 'transit_unavailable'), (1, -1, 'transit_unavailable'),
])
def test_incomplete_scope_is_unknown_even_when_partial_natal_is_true(day: int, year: int | None, reason: str) -> None:
  result = match(day, profile=ContextProfile('natal_and_liunian', year))
  assert result.criterion.status == 'UNKNOWN' and result.criterion.reason == reason
  assert result.criterion.scope_complete is False
  assert all(o.origin == 'natal' for o in result.occurrences)
  assert result.criterion.observations['observed_coexistence'] is (day == 3)
  assert all(m.status == 'UNKNOWN' for m in result.entries)
  assert ContextResult.from_json(result.export_json()) == result


def test_required_kind_unavailable_is_unknown_and_errors_are_not_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(TransitChart, 'at_year', lambda self, year: TransitSet(dayun=Ganzhi.from_str('甲辰')))
  result = match(profile=ContextProfile('natal_and_liunian', 2024))
  assert result.criterion.status == 'UNKNOWN' and result.criterion.reason == 'transit_unavailable'
  def broken(self: TransitChart, year: int) -> TransitSet:
    raise ValueError('A programming error, not unavailability')
  monkeypatch.setattr(TransitChart, 'at_year', broken)
  with pytest.raises(ValueError, match='programming error'):
    match(profile=ContextProfile('natal_and_liunian', 2024))


@pytest.mark.parametrize('criterion_id,gender,year,reason', [
  (FEMALE, 'female', None, 'missing_transit_coordinate'),
  (FEMALE, 'male', None, 'missing_transit_coordinate'),
  (FEMALE, 'female', 1998, 'transit_unavailable'),
  (FEMALE, 'male', 1998, 'transit_unavailable'),
  ('tiangan.geng_regulated_transit', 'female', None, 'predicate_undefined'),
  ('tiangan.geng_regulated_transit', 'male', 1998, 'predicate_undefined'),
])
def test_incomplete_scope_reason_precedence(criterion_id: str, gender: str, year: int | None, reason: str) -> None:
  result = match(gender=gender, criterion_id=criterion_id, profile=ContextProfile('natal_and_liunian', year))
  assert result.criterion.status == 'UNKNOWN'
  assert result.criterion.reason == reason and result.criterion.scope_complete is False
  assert all(entry.status == 'UNKNOWN' and entry.reason == reason for entry in result.entries)
  assert all(o.origin == 'natal' for o in result.occurrences)
  assert ContextResult.from_json(result.export_json()) == result


@pytest.mark.parametrize('criterion_id,claim_id', [
  ('tiangan.ding_weak_and_overcontrolled', 'legacy.tiangan.ding.weak_state'),
  ('tiangan.geng_regulated_transit', 'legacy.tiangan.geng.regulated_transit'),
  ('shishen.pianyin_favorable_or_balanced', 'legacy.shishen.SH-199'),
  ('shishen.xiaoyin_duoshi', 'legacy.shishen.SH-066'),
])
def test_registered_undefined_controls_preserve_every_premise_and_limit(criterion_id: str, claim_id: str) -> None:
  knowledge = KnowledgeBase.load()
  result = match(criterion_id=criterion_id)
  assert result.criterion.status == 'UNKNOWN' and result.criterion.reason == 'predicate_undefined'
  assert result.criterion.observations == {'observed_coexistence': True, 'female': True}
  assert result.entries == (EntryMatch(claim_id, 'UNKNOWN', 'predicate_undefined'),)
  restored = result.knowledge
  assert restored.entries == knowledge.entries and restored.contexts == knowledge.contexts
  entry = restored.entry(claim_id)
  rendered = result.render()
  assert entry.text in rendered and entry.premise in rendered
  for text in entry.limits + tuple(limit for key in entry.contexts for limit in restored.contexts[key].limits):
    assert text in rendered
  if entry.legacy is not None:
    assert entry.legacy.field_premise in rendered
  assert 'UNKNOWN' in rendered


def test_reference_eligibility_source_modal_and_full_knowledge_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
  knowledge = KnowledgeBase.load()
  default = evaluate_context(chart(), criterion_id=GUANSHA, profile=ContextProfile('natal'))
  assert default.criterion.status == 'SATISFIED' and default.entries == ()
  assert '前提满足只表示本范围内的原作使用条件满足，不表示现实事件成立。' in default.render()
  assert len(knowledge.query()) == 19
  result = match()
  data = json.loads(result.export_json())
  assert 'stem_scope' not in data['profile']
  assert all('index' not in value for value in data['occurrences'])
  assert 'revision' not in data['criterion']
  assert data['knowledge'] == json.loads(knowledge.export_json())
  assert len(data['knowledge']['entries']) == 302
  assert data['criterion']['observations']['observed_coexistence'] is True
  rendered = result.render()
  assert '来源状态：editorial' in rendered and '见证状态：editorial' in rendered
  source = knowledge.sources['editorial']
  for text in asdict(source).values():
    assert text in rendered
  for key in LEGAL:
    entry = knowledge.entry(key)
    assert entry.text in rendered and '也许' in entry.text
    assert entry.premise in rendered and entry.viewpoint in rendered
    assert entry.source_state == 'editorial' and entry.output == 'reference_only'
    assert '命盘适用性未判断' in knowledge.render(entry)
    assert '命盘适用性未判断' not in rendered
    for context_id in entry.contexts:
      assert all(limit in rendered for limit in knowledge.contexts[context_id].limits)
  assert '可能会' in match(criterion_id=FEMALE).render()
  # Record restoration must not call a chart/transit constructor or evaluator.
  def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise RuntimeError('Unexpected recalculation')
  monkeypatch.setattr(Bazi, 'create', forbidden)
  monkeypatch.setattr(TransitChart, 'at_year', forbidden)
  restored = ContextResult.from_json(result.export_json())
  assert restored == result and restored.render() == rendered and restored.export_json() == result.export_json()


@pytest.mark.parametrize('day,criterion_id,status', [
  (3, GUANSHA, 'SATISFIED'), (1, GUANSHA, 'NOT_SATISFIED'),
  (3, 'tiangan.geng_regulated_transit', 'UNKNOWN'),
])
def test_render_premise_annotations_are_evaluation_only(day: int, criterion_id: str, status: str) -> None:
  result = match(day, criterion_id=criterion_id)
  knowledge = result.knowledge
  text = result.render()
  for entry_match in result.entries:
    block = text.split(f'原作参考前提：{entry_match.claim_id}；', 1)[1].split('\n原作参考前提：', 1)[0]
    entry = knowledge.entry(entry_match.claim_id)
    assert f'输出资格：{entry.output}' in block and f'前提判别：{status}' in block
    assert '前提判别：' not in knowledge.render(entry)
    assert '输出资格：' not in knowledge.render(entry)


@pytest.mark.parametrize('claim_id,criterion_id', [
  (LEGAL[0], GUANSHA),
  ('legacy.tiangan.ding.weak_state', 'tiangan.ding_weak_and_overcontrolled'),
])
@pytest.mark.parametrize('separator', ['\n', '\r\n', '\r', '\u2028'])
def test_multiline_custom_text_keeps_one_copy_and_source_cautions(claim_id: str, criterion_id: str, separator: str) -> None:
  data = json.loads(KnowledgeBase.load().export_json())
  entry = next(e for e in data['entries'] if e['claim_id'] == claim_id)
  text = 'FIRST-TEXT-LINE' + separator + 'SECOND-TEXT-LINE'
  entry['text'] = text
  knowledge = KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))
  result = match(criterion_id=criterion_id, knowledge=knowledge)
  rendered = result.render()
  assert rendered.count(text) == 1 and rendered.count('SECOND-TEXT-LINE') == 1
  assert '命盘适用性未判断' not in rendered
  assert knowledge.render(knowledge.entry(claim_id)).count(text) == 1
  assert '命盘适用性未判断' in knowledge.render(knowledge.entry(claim_id))
  if criterion_id == GUANSHA:
    assert result.entries[0].reason == 'binding_unrecognized'
    assert all(value in rendered for value in asdict(knowledge.sources['editorial']).values())
  else:
    assert result.entries[0].reason == 'predicate_undefined'
    assert '来源尚未核实' in rendered and '前提待梳理' in rendered
    assert '来源状态：unverified' in rendered
  restored = ContextResult.from_json(result.export_json())
  assert restored == result and restored.render() == rendered


@pytest.mark.parametrize('dimension', ['text', 'premise', 'contexts', 'roles', 'viewpoint', 'source', 'context', 'object', 'qualification'])
def test_same_id_custom_binding_is_not_semantic_authentication(dimension: str) -> None:
  data = json.loads(KnowledgeBase.load().export_json())
  entry = next(e for e in data['entries'] if e['claim_id'] == LEGAL[0])
  if dimension in ('text', 'premise', 'viewpoint'):
    entry[dimension] += '（编辑口径）'
  elif dimension == 'contexts':
    entry['contexts'] = ['legacy.chart_context']
  elif dimension == 'roles':
    entry['roles'][0]['name'] = '其他角色'
  elif dimension == 'source':
    data['sources'][0]['limitations'] = '不同支持边界。'
  elif dimension == 'context':
    next(c for c in data['contexts'] if c['context_id'] == entry['contexts'][0])['limits'] = ['另一个条件。']
  elif dimension == 'object':
    next(o for o in data['objects'] if o['object_id'] == 'shishen.zhengguan')['name'] = '同名异物'
  else:
    entry.update(output='default', applicability='unconditional', premise='', contexts=[], source_state='witnessed', sources=['yuanhai_ziping_relations', 'mingli_tanyuan_shishen_definitions'])
  custom = KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))
  result = match(knowledge=custom)
  assert result.criterion.status == 'SATISFIED'
  assert result.entries[0] == EntryMatch(LEGAL[0], 'UNKNOWN', 'binding_unrecognized')
  assert json.loads(result.knowledge.export_json()) == data
  assert ContextResult.from_json(result.export_json()) == result
  if dimension == 'qualification':
    default = evaluate_context(chart(), criterion_id=GUANSHA, profile=ContextProfile('natal'), knowledge=custom)
    assert default.entries == (EntryMatch(LEGAL[0], 'UNKNOWN', 'binding_unrecognized'),)
    assert '输出资格：default' in default.render() and '前提判别：UNKNOWN' in default.render()


def test_equal_custom_export_bindings_and_missing_entries() -> None:
  knowledge = KnowledgeBase.load()
  selection = knowledge.query(context_id='editorial.guansha_coexistence', include_reference_only=True)
  custom = KnowledgeBase.from_json(knowledge.export_json(selection))
  assert match(knowledge=custom).entries == match().entries
  assert match(knowledge=KnowledgeBase.from_json(knowledge.export_json(()))).entries == ()


def test_full_input_identity_and_immutability() -> None:
  result = match()
  identity = json.loads(result.input_json)
  assert identity['birth_time'] == '2000-01-03T12:00:00' and identity['gender'] == 'female'
  assert identity['config']['backend'] == 'celestial' and identity['config']['precision'] == 'day'
  assert len(identity['config']['school']) == 23
  for config in (
    BaziConfig(school=BaziSchool(day_rollover=DayRollover.ZIZHENG)),
    BaziConfig.from_values(precision='hour'), BaziConfig.from_values(backend='hko'),
    BaziConfig.from_values(dayun_year_rule='fixed_decade'),
  ):
    changed = BaziChart(Bazi.create(datetime(2000, 1, 3, 12), 'female', config))
    changed_result = evaluate_context(changed, criterion_id=GUANSHA, profile=ContextProfile('natal'))
    assert changed_result.input_json != result.input_json
    assert ContextResult.from_json(changed_result.export_json()) == changed_result
  assert isinstance(result.profile, ContextProfile)
  with pytest.raises(FrozenInstanceError):
    result.profile.ganzhi_year = 2024 # type: ignore[misc]
  with pytest.raises(FrozenInstanceError):
    result.occurrences[0].index = 1 # type: ignore[misc]
  with pytest.raises(TypeError):
    result.criterion.observations['female'] = False # type: ignore[index]
  assert hash(result) == hash(ContextResult.from_json(result.export_json()))


def test_configuration_wire_roster_and_chart_input_agree() -> None:
  c = chart()
  wire = _config_json(c.bazi.config)
  assert set(wire) == {field.name for field in fields(BaziConfig)}
  assert set(wire['school']) == {field.name for field in fields(BaziSchool)}
  chart_json: dict[str, Any] = dict(c.json)
  assert {key: chart_json[key] for key in wire} == wire
  assert json.loads(match().input_json)['config'] == wire


def test_undefined_criterion_observations_use_the_editorial_roster() -> None:
  result = match(10, criterion_id='tiangan.ding_weak_and_overcontrolled')
  assert chart(10).bazi.day_master is Tiangan.丁
  assert set(result.criterion.observations) == {'observed_coexistence', 'female'}
  assert result.criterion.observations['female'] is True
  assert result.criterion.status == 'UNKNOWN' and result.criterion.reason == 'predicate_undefined'


class Year(int):
  pass


@pytest.mark.parametrize('value', [True, False, Year(2024), '2024', 2024.0, []])
def test_year_rejects_non_exact_int(value: Any) -> None:
  with pytest.raises(TypeError):
    ContextProfile('natal_and_liunian', value)


def test_bad_requests_fail_instead_of_unknown() -> None:
  c = chart()
  options: dict[str, Any]
  for options in ({'criterion_id': 42}, {'profile': 'natal'}, {'knowledge': {}}, {'include_reference_only': 1}):
    with pytest.raises(TypeError):
      evaluate_context(c, **{'criterion_id': GUANSHA, 'profile': ContextProfile('natal'), **options}) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    evaluate_context(None, criterion_id=GUANSHA, profile=ContextProfile('natal')) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    ContextProfile(42) # type: ignore[arg-type]
  with pytest.raises(ValueError):
    ContextProfile('natal', 2024)
  with pytest.raises(ValueError):
    ContextProfile('dayun') # type: ignore[arg-type]
  with pytest.raises(ValueError):
    match(criterion_id='editorial.guansha_coexistance.v1')


def test_public_record_value_boundaries() -> None:
  result = match()
  o = result.occurrences[0]
  change: dict[str, Any]
  for change in ({'origin': 'other'}, {'pillar': 'other'}, {'layer': 'other'}, {'kind': TransitKind.DAYUN}, {'ganzhi_year': 2024}, {'pillar': 'day'}, {'stem': Tiangan.甲}):
    with pytest.raises(ValueError):
      replace(o, **change)
  for change in ({'index': True}, {'index': -1}, {'ganzhi': '己卯'}, {'stem': '己'}, {'shishen': '正印'}, {'kind': 'liunian'}, {'ganzhi_year': True}):
    with pytest.raises(TypeError):
      replace(o, **change)
  with pytest.raises(ValueError):
    replace(result.occurrences[1], stem=Tiangan.丁)
  with pytest.raises(ValueError):
    replace(o, origin='transit')
  for change in ({'definition': 'other'}, {'status': 'UNKNOWN'}, {'reason': 'bad'}, {'scope_complete': False}):
    with pytest.raises(ValueError):
      replace(result.criterion, **change)
  for change in ({'observations': {}}, {'observations': frozendict({1: True})}, {'observations': frozendict({'a': 1})}, {'scope_complete': 1}):
    with pytest.raises(TypeError):
      replace(result.criterion, **change)
  with pytest.raises(TypeError):
    EntryMatch(1, 'UNKNOWN', 'predicate_undefined') # type: ignore[arg-type]
  with pytest.raises(ValueError):
    EntryMatch('', 'UNKNOWN', 'predicate_undefined')
  for change in ({'profile': 'natal'}, {'criterion': {}}, {'occurrences': []}, {'entries': []}, {'input_json': None}, {'knowledge': None}, {'occurrences': (None,)}, {'entries': (None,)}):
    with pytest.raises(TypeError):
      replace(result, **change)
  with pytest.raises(ValueError):
    replace(result, entries=(EntryMatch('unknown', 'UNKNOWN', 'predicate_undefined'),))


def test_each_reason_has_one_admissible_status() -> None:
  expected: dict[MatchReason, MatchStatus] = {
    'premise_satisfied': 'SATISFIED',
    'required_classification_absent': 'NOT_SATISFIED',
    'female_gate_false': 'NOT_SATISFIED',
    'missing_transit_coordinate': 'UNKNOWN',
    'transit_unavailable': 'UNKNOWN',
    'predicate_undefined': 'UNKNOWN',
    'binding_unrecognized': 'UNKNOWN',
  }
  assert set(expected) == set(get_args(MatchReason))
  for reason, status in expected.items():
    assert EntryMatch(LEGAL[0], status, reason).status == status
    for other in get_args(MatchStatus):
      if other != status:
        with pytest.raises(ValueError, match='Status and reason disagree'):
          EntryMatch(LEGAL[0], other, reason)


@pytest.mark.parametrize('value', [None, True, 1, 1.0, [], {}])
def test_public_verdict_status_types_raise_type_error(value: Any) -> None:
  result = match()
  for factory in (
    lambda: EntryMatch(LEGAL[0], value, 'premise_satisfied'),
    lambda: replace(result.criterion, status=value),
  ):
    with pytest.raises((TypeError, ValueError)) as error:
      factory()
    assert type(error.value) is TypeError
    assert str(error.value).startswith('Expected str, got ')


@pytest.mark.parametrize('dimension,value,error', [
  ('record_version', True, ValueError), ('record_version', False, ValueError),
  ('record_version', -1, ValueError), ('record_version', 0, ValueError),
  ('record_version', 1, ValueError), ('record_version', 2, ValueError),
  ('record_version', 4, ValueError),
  ('record_version', 3.0, ValueError), ('record_version', '3', ValueError),
  ('record_version', None, ValueError),
  ('profile', [], TypeError), ('criterion', {}, ValueError), ('occurrences', {}, TypeError),
  ('entries', {}, TypeError), ('input', {}, ValueError), ('knowledge', {}, ValueError),
])
def test_restore_rejects_wrong_record_shape(dimension: str, value: Any, error: type[Exception]) -> None:
  data = json.loads(match().export_json())
  data[dimension] = value
  with pytest.raises(error):
    ContextResult.from_json(json.dumps(data))


def test_restore_rejects_corrupt_nested_records() -> None:
  original = json.loads(match(profile=ContextProfile('natal_and_liunian', 2024)).export_json())
  mutations = [
    ('profile', 'stem_scope', 'visible'), ('profile', 'ganzhi_year', True),
    ('criterion', 'observations', []), ('input', 'birth_time', '2000-01-03T12:00:00+00:00'),
    ('input', 'birth_time', '2000-01-03 12:00'), ('input', 'birth_time', '2000-01-03T12:00:01'),
    ('input', 'birth_time', 42), ('input', 'gender', '女'), ('input', 'pillars', ['甲子']),
    ('input', 'pillars', ['甲子', '甲子', '甲子', 42]),
  ]
  for section, key, value in mutations:
    data = json.loads(json.dumps(original))
    data[section][key] = value
    with pytest.raises((TypeError, ValueError)):
      ContextResult.from_json(json.dumps(data))
  for key, value in (('kind', 'dayun'), ('kind', None), ('ganzhi_year', None), ('stem', 42)):
    data = json.loads(json.dumps(original))
    data['occurrences'][-1][key] = value
    with pytest.raises((TypeError, ValueError)):
      ContextResult.from_json(json.dumps(data))
  data = json.loads(json.dumps(original))
  data['occurrences'][0]['index'] = 0
  with pytest.raises(ValueError, match='JSON fields differ'):
    ContextResult.from_json(json.dumps(data))
  for key, value in (('backend', 'nope'), ('precision', 'bogus'), ('dayun_year_rule', 'bogus'), ('school', {})):
    data = json.loads(json.dumps(original))
    data['input']['config'][key] = value
    with pytest.raises(ValueError):
      ContextResult.from_json(json.dumps(data))
  with pytest.raises(TypeError):
    ContextResult.from_json(42) # type: ignore[arg-type]
  with pytest.raises(ValueError):
    ContextResult.from_json('{"record_version":2,"record_version":2}')
  with pytest.raises(TypeError):
    ContextResult.from_json('[]')


def test_restore_rejects_duplicate_keys_in_an_otherwise_complete_record() -> None:
  text = match().export_json()
  for needle, duplicate in (
    ('"record_version": 3', '"record_version": 3'),
    ('"gender": "female"', '"gender": "male"'),
    ('"scope_complete": true', '"scope_complete": false'),
  ):
    assert text.count(needle) == 1
    corrupted = text.replace(needle, needle + ', ' + duplicate)
    with pytest.raises(ValueError, match='Duplicate JSON key'):
      ContextResult.from_json(corrupted)


def test_corpus_organization_and_frozen_oracle_hash() -> None:
  import hashlib
  fixture = Path(__file__).with_name('data') / 'description_legacy_baseline.json'
  assert hashlib.sha256(fixture.read_bytes().replace(b'\r\n', b'\n')).hexdigest() == '6e50cf38d5b9a74a6f2a7ba2b3502b8dad818955a67ac6530e97f8d768f6b774'
  knowledge = KnowledgeBase.load()
  assert len(knowledge.entries) == 302 and len(knowledge.sources) == 13 and len(knowledge.query()) == 19
  for criterion, keys, context_id in ((GUANSHA, LEGAL, 'editorial.guansha_coexistence'), (FEMALE, RELATIONSHIP, 'editorial.guansha_coexistence_female')):
    assert tuple(e.claim_id for e in knowledge.query(context_id=context_id, include_reference_only=True)) == keys
    assert knowledge.query(context_id=context_id) == ()
    for key in keys:
      entry = knowledge.entry(key)
      assert entry.applicability == 'described' and entry.sources == ('editorial',)
      assert entry.output == 'reference_only' and entry.viewpoint == '仓内原作'
      assert all(limit in knowledge.render(entry) for limit in knowledge.contexts[context_id].limits)
    assert all(m.status == 'SATISFIED' for m in match(criterion_id=criterion).entries)


def test_shared_knowledge_lifecycle_and_independent_record_recovery(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
  data = json.loads(KnowledgeBase.load().export_json())
  source = tmp_path / 'knowledge.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  knowledge = KnowledgeBase.load(source)
  count = 0
  original_init = KnowledgeBase.__init__

  def counted(self: KnowledgeBase, *args: Any, **kwargs: Any) -> None:
    nonlocal count
    count += 1
    original_init(self, *args, **kwargs)

  def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError('Unexpected whole-corpus JSON round trip')

  monkeypatch.setattr(KnowledgeBase, '__init__', counted)
  monkeypatch.setattr(KnowledgeBase, 'from_json', forbidden)
  monkeypatch.setattr(KnowledgeBase, 'export_json', forbidden)
  results = tuple(match(day, knowledge=knowledge) for day in (1, 3, 5))
  for result in results:
    assert result.knowledge is knowledge
    rendered = result.render()
    assert result.render() == rendered
    assert json.loads(result.export_json())['knowledge'] == data
  assert count == 0

  result = results[1]
  rendered, exported = result.render(), result.export_json()
  changed = json.loads(json.dumps(data))
  next(entry for entry in changed['entries'] if entry['claim_id'] == LEGAL[0])['text'] = 'External source changed.'
  source.write_text(json.dumps(changed, ensure_ascii=False), encoding='utf-8')
  assert result.render() == rendered and result.export_json() == exported
  source.unlink()
  assert result.render() == rendered and result.export_json() == exported
  restored = ContextResult.from_json(exported)
  assert count == 1
  assert restored.knowledge is not knowledge and restored.knowledge == knowledge
  assert restored == result and hash(restored) == hash(result)
  assert len({result, restored}) == 1 and {result: 'record'}[restored] == 'record'
  assert restored.render() == rendered and restored.export_json() == exported and count == 1


def test_default_knowledge_is_loaded_independently(monkeypatch: pytest.MonkeyPatch) -> None:
  original_load = KnowledgeBase.load
  calls = 0

  def counted(*args: Any, **kwargs: Any) -> KnowledgeBase:
    nonlocal calls
    calls += 1
    return original_load(*args, **kwargs)

  monkeypatch.setattr(KnowledgeBase, 'load', counted)
  left, right = match(), match()
  assert calls == 2
  assert left.knowledge is not right.knowledge
  assert left.knowledge == right.knowledge and left == right


def test_default_reload_and_shared_snapshot_after_source_update(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
  data = json.loads(KnowledgeBase.load().export_json())
  source = tmp_path / 'knowledge.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  monkeypatch.setattr('bazi.knowledge.DEFAULT_SOURCE_PATH', source)
  shared = KnowledgeBase.load()
  original_text = shared.entry(LEGAL[0]).text
  original_results = (match(), match(knowledge=shared))
  snapshots = tuple((result, result.render(), result.export_json()) for result in original_results)

  next(entry for entry in data['entries'] if entry['claim_id'] == LEGAL[0])['text'] = 'Updated reference text.'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  default = match()
  assert default.knowledge.entry(LEGAL[0]).text == 'Updated reference text.'
  assert default.criterion.status == 'SATISFIED'
  assert default.entries[0] == EntryMatch(LEGAL[0], 'UNKNOWN', 'binding_unrecognized')
  assert default.knowledge.entry(LEGAL[0]).output == 'reference_only'

  still_shared = match(knowledge=shared)
  assert still_shared.knowledge is shared and still_shared.knowledge.entry(LEGAL[0]).text == original_text
  assert still_shared == original_results[1]
  reloaded = KnowledgeBase.load()
  assert match(knowledge=reloaded) == default
  assert reloaded is not shared
  for result, rendered, exported in snapshots:
    assert result.knowledge.entry(LEGAL[0]).text == original_text
    assert result.render() == rendered and result.export_json() == exported
    assert ContextResult.from_json(exported) == result


@pytest.mark.parametrize('missing', [False, True])
def test_default_source_errors_leave_shared_results_intact(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: bool) -> None:
  source = tmp_path / 'knowledge.json'
  source.write_text(KnowledgeBase.load().export_json(), encoding='utf-8')
  monkeypatch.setattr('bazi.knowledge.DEFAULT_SOURCE_PATH', source)
  shared = KnowledgeBase.load()
  result = match()
  rendered, exported = result.render(), result.export_json()
  if missing:
    source.unlink()
  else:
    source.write_text('{', encoding='utf-8')
  with pytest.raises(FileNotFoundError if missing else json.JSONDecodeError):
    match()
  assert match(knowledge=shared) == result
  assert result.render() == rendered and result.export_json() == exported
  assert ContextResult.from_json(exported) == result


def test_all_knowledge_value_fields_participate_in_comparison() -> None:
  for record_type in (KnowledgeObject, KnowledgeContext, KnowledgeSource, KnowledgeEntry, KnowledgeRole, KnowledgeRelation, LegacyDescription):
    assert all(field.compare for field in fields(record_type)), record_type.__name__


@pytest.mark.parametrize('registry', ['objects', 'contexts', 'sources', 'entries'])
def test_record_equality_preserves_full_knowledge_content_and_order(registry: str) -> None:
  knowledge = KnowledgeBase.load()
  result = match(knowledge=knowledge)
  data = json.loads(knowledge.export_json())
  data[registry].reverse()
  reordered = KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))
  other = match(knowledge=reordered)
  assert knowledge != reordered and reordered != knowledge and knowledge != object()
  assert result != other and len({result, other}) == 2
  assert json.loads(other.export_json())['knowledge'][registry] == data[registry]

  changed = json.loads(knowledge.export_json())
  changed['entries'][0]['text'] += ' Extra recorded text.'
  changed_result = match(knowledge=KnowledgeBase.from_json(json.dumps(changed, ensure_ascii=False)))
  assert changed_result != result and len({result, changed_result}) == 2


@pytest.mark.parametrize('registry, field', [
  ('objects', 'name'), ('contexts', 'label'), ('sources', 'excerpt'), ('entries', 'viewpoint'),
])
def test_record_equality_preserves_nontext_knowledge_fields(registry: str, field: str) -> None:
  knowledge = KnowledgeBase.load()
  result = match(knowledge=knowledge)
  changed = json.loads(knowledge.export_json())
  changed[registry][0][field] += ' changed'
  other_knowledge = KnowledgeBase.from_json(json.dumps(changed, ensure_ascii=False))
  other = match(knowledge=other_knowledge)
  assert knowledge != other_knowledge and result != other
  assert len({result, other}) == 2


# ----------------------------------------------------------------------------------
# #233 婚恋判据：explicit transit profiles, missing data, three-state reference matrix, and record v3.
# All cases use reproducible real birth inputs and configs; 岁运 come from real TransitChart queries by coordinate.

from datetime import date as _date_module  # The construction-time matrix needs the native date type.
from datetime import UTC as _UTC

from bazi.bazi import BaziGender as _BaziGender
from bazi.context_matching import (
  RelatedEntry, RelationshipProfile, TransitCoordinate, _CRITERIA, _RELATED_GENDERS,
)
from bazi.defines import Dizhi as _Dizhi


PALACE = 'editorial.spouse_palace_xingchong.v1'
TOUGAN = 'editorial.spouse_star_tougan.v1'
RELATED_PALACE = 'editorial.tanyuan.wife_palace_xingchong.v1'
RELATED_TOUGAN = 'editorial.tanyuan.wife_star_gantou.v1'


def rel_match(
  criterion_id: str = PALACE,
  birth: str = '2000-01-01 12:00',
  gender: str = 'male',
  **kwargs: Any,
) -> ContextResult:
  options: dict[str, Any] = {'profile': RelationshipProfile('natal'), **kwargs}
  return evaluate_context(chart_from(birth, gender), criterion_id=criterion_id, **options)


def chart_from(birth: str, gender: str) -> BaziChart:
  return BaziChart(Bazi.create(birth, gender))


def test_relationship_criterion_registry_and_gates() -> None:
  # Claims of all relationship criteria sit in _BINDINGS; the gate table holds exactly the two restricted IDs and is a subset of those claims.
  relationship_claims = {
    claim_id for criterion in _CRITERIA.values()
    if criterion.profile_kind == 'relationship' for claim_id in criterion.claims
  }
  assert relationship_claims == {RELATED_PALACE, RELATED_TOUGAN}
  assert relationship_claims <= set(_BINDINGS)
  assert set(_RELATED_GENDERS) == {RELATED_PALACE, RELATED_TOUGAN}
  assert set(_RELATED_GENDERS) <= relationship_claims
  assert all(gender is _BaziGender.MALE for gender in _RELATED_GENDERS.values())
  # The 官杀 criteria and the four undefined criteria are labeled 'context'; behavior and fingerprints stay unchanged.
  assert {key for key, value in _CRITERIA.items() if value.profile_kind == 'context'} == {
    GUANSHA, FEMALE, 'tiangan.ding_weak_and_overcontrolled', 'tiangan.geng_regulated_transit',
    'shishen.pianyin_favorable_or_balanced', 'shishen.xiaoyin_duoshi',
  }


@pytest.mark.parametrize('claim_id', [RELATED_PALACE, RELATED_TOUGAN])
def test_relationship_binding_fingerprints(claim_id: str) -> None:
  knowledge = KnowledgeBase.load()
  assert _binding_digest(knowledge, knowledge.entry(claim_id)) == _BINDINGS[claim_id]


@pytest.mark.parametrize('criterion_id, profile, error', [
  (PALACE, ContextProfile('natal'), ValueError),
  (PALACE, ContextProfile('natal_and_liunian', 2024), ValueError),
  (GUANSHA, RelationshipProfile('natal'), ValueError),
  ('tiangan.ding_weak_and_overcontrolled', RelationshipProfile('natal'), ValueError),
])
def test_criterion_profile_kind_must_match(criterion_id: str, profile: ContextProfile | RelationshipProfile, error: type[Exception]) -> None:
  with pytest.raises(error, match='profile'):
    evaluate_context(chart(), criterion_id=criterion_id, profile=profile)


@pytest.mark.parametrize('kwargs, error', [
  ({'scope': 'natal_and_liunian'}, ValueError),
  ({'scope': 'dayun'}, ValueError),
  ({'scope': 'natal', 'kinds': (TransitKind.LIUNIAN,)}, ValueError),
  ({'scope': 'natal_and_transits', 'coordinate': 'at_year', 'kinds': (TransitKind.LIUNIAN,)}, TypeError),
  ({'scope': 'natal_and_transits'}, ValueError),
  ({'scope': 'natal_and_transits', 'kinds': [TransitKind.LIUNIAN]}, TypeError),
  ({'scope': 'natal_and_transits', 'kinds': ('liunian',)}, TypeError),
  ({'scope': 'natal_and_transits', 'kinds': (TransitKind.LIUNIAN, TransitKind.LIUNIAN)}, ValueError),
  ({
    'scope': 'natal_and_transits',
    'coordinate': TransitCoordinate('at_year', gz_year=2024),
    'kinds': (TransitKind.LIUYUE,),
  }, ValueError),
  ({
    'scope': 'natal_and_transits',
    'coordinate': TransitCoordinate('at_month', gz_year=2024, gz_month=_Dizhi.辰),
    'kinds': (TransitKind.LIURI,),
  }, ValueError),
])
def test_relationship_profile_request_errors(kwargs: dict[str, Any], error: type[Exception]) -> None:
  with pytest.raises(error):
    RelationshipProfile(**kwargs)


def test_relationship_profile_normalizes_legal_but_unordered_kinds() -> None:
  profile = RelationshipProfile(
    'natal_and_transits',
    TransitCoordinate('at_date', solar_date=_date_module(2024, 4, 10)),
    (TransitKind.LIUNIAN, TransitKind.XIAOYUN, TransitKind.DAYUN),
  )
  assert profile.kinds == (TransitKind.XIAOYUN, TransitKind.DAYUN, TransitKind.LIUNIAN)
  assert profile == RelationshipProfile(
    'natal_and_transits',
    TransitCoordinate('at_date', solar_date=_date_module(2024, 4, 10)),
    (TransitKind.DAYUN, TransitKind.LIUNIAN, TransitKind.XIAOYUN),
  )
  # coordinate=None is a legal profile (a missing coordinate yields UNKNOWN at evaluation time), distinct from a malformed coordinate object.
  assert RelationshipProfile('natal_and_transits', None, (TransitKind.LIUNIAN,)).coordinate is None


@pytest.mark.parametrize('entry, kwargs, error', [
  ('at_five', {}, ValueError),
  ('at_year', {'gz_month': _Dizhi.酉}, ValueError),
  ('at_year', {'gz_year': 2024, 'solar_date': _date_module(2024, 4, 10)}, ValueError),
  ('at_month', {'gz_year': 2024}, ValueError),
  ('at_month', {'gz_month': _Dizhi.酉}, ValueError),
  ('at_date', {}, ValueError),
  ('at_date', {'solar_date': _date_module(2024, 4, 10), 'gz_year': 2024}, ValueError),
  ('at_moment', {'solar_moment': datetime(2024, 4, 10, 12), 'gz_month': _Dizhi.酉}, ValueError),
  ('at_year', {'gz_year': True}, TypeError),
  ('at_year', {'gz_year': Year(2024)}, TypeError),
  ('at_month', {'gz_year': 2024, 'gz_month': '酉'}, TypeError),
  ('at_date', {'solar_date': datetime(2024, 4, 10, 12)}, TypeError),
  ('at_moment', {'solar_moment': _date_module(2024, 4, 10)}, TypeError),
  ('at_moment', {'solar_moment': datetime(2024, 4, 10, 12, tzinfo=_UTC)}, ValueError),
])
def test_transit_coordinate_request_errors(entry: str, kwargs: dict[str, Any], error: type[Exception]) -> None:
  with pytest.raises(error):
    TransitCoordinate(entry, **kwargs) # type: ignore[arg-type]


def test_relationship_verdicts_and_observations() -> None:
  # 宫刑冲: the male chart with 子午冲＋午午自刑 is SATISFIED; the 丙寅 day chart without 刑 or 冲 is NOT_SATISFIED.
  satisfied = rel_match()
  assert satisfied.criterion.status == 'SATISFIED' and satisfied.criterion.reason == 'premise_satisfied'
  assert satisfied.criterion.scope_complete is True
  assert dict(satisfied.criterion.observations) == {'day_pillar_in_chong': True, 'day_pillar_in_xing': True}
  unsatisfied = rel_match(birth='2000-01-09 12:00')
  assert unsatisfied.criterion.status == 'NOT_SATISFIED' and unsatisfied.criterion.reason == 'required_classification_absent'
  assert dict(unsatisfied.criterion.observations) == {'day_pillar_in_chong': False, 'day_pillar_in_xing': False}
  # 透干: a visible 辛明干 is SATISFIED; 藏干 only record facts and never satisfy 「透」.
  visible = rel_match(TOUGAN, birth='2000-01-29 06:00')
  assert visible.criterion.status == 'SATISFIED'
  assert dict(visible.criterion.observations) == {'target_stem_visible': True, 'target_stem_hidden': True}
  hidden_only = rel_match(TOUGAN, birth='2000-01-01 12:00') # 丑 hides 辛; no 辛 in 明干.
  assert hidden_only.criterion.status == 'NOT_SATISFIED'
  assert dict(hidden_only.criterion.observations) == {'target_stem_visible': False, 'target_stem_hidden': True}
  for result in (satisfied, unsatisfied, visible, hidden_only):
    assert result.occurrences == () and result.entries == () and result.relationship is not None
    assert ContextResult.from_json(result.export_json()) == result


def test_relationship_scope_missing_data_paths() -> None:
  c = chart_from('2000-01-01 12:00', 'male') # born 2000-01-01, 干支年 1999.
  # Missing query coordinate: kinds stay explicitly non-empty; UNKNOWN／missing_transit_coordinate with transits None.
  no_coordinate = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', None, (TransitKind.LIUNIAN, TransitKind.DAYUN),
  ))
  assert no_coordinate.criterion.status == 'UNKNOWN' and no_coordinate.criterion.reason == 'missing_transit_coordinate'
  assert no_coordinate.criterion.scope_complete is False
  assert no_coordinate.relationship is not None and no_coordinate.relationship.transits is None
  # Before birth: the entry returns None → transit_unavailable.
  before_birth = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=1998), (TransitKind.LIUNIAN,),
  ))
  assert before_birth.criterion.reason == 'transit_unavailable'
  assert before_birth.relationship is not None and before_birth.relationship.transits is None
  # A DAY-precision at_moment entry is unavailable → transit_unavailable.
  day_precision = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_moment', solar_moment=datetime(2024, 4, 10, 12)), (TransitKind.LIUNIAN,),
  ))
  assert day_precision.criterion.reason == 'transit_unavailable'
  for result in (no_coordinate, before_birth, day_precision):
    assert ContextResult.from_json(result.export_json()) == result
    rendered = result.render()
    assert '请求种类=' in rendered and '未取得种类=' in rendered


def test_relationship_partial_and_empty_kind_availability() -> None:
  c = chart_from('2000-01-01 12:00', 'male')
  # No 小运 after adulthood: requesting {小运, 大运} obtains only 大运 → UNKNOWN／transit_unavailable, evidence of obtained kinds kept.
  partial = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.XIAOYUN, TransitKind.DAYUN),
  ))
  assert partial.criterion.reason == 'transit_unavailable' and partial.criterion.scope_complete is False
  assert partial.relationship is not None
  assert partial.relationship.transits is not None
  assert tuple(partial.relationship.transits) == (TransitKind.DAYUN,)
  # Fully missing: only 小运 requested and none that year → empty intersection, transits None; the underlying select exception is not raised.
  all_missing = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.XIAOYUN,),
  ))
  assert all_missing.criterion.reason == 'transit_unavailable'
  assert all_missing.relationship is not None and all_missing.relationship.transits is None
  # All requested kinds obtained: verdict per the criterion, obtained set in fixed order.
  complete = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.LIUNIAN, TransitKind.DAYUN),
  ))
  assert complete.criterion.status == 'SATISFIED' and complete.criterion.scope_complete is True
  assert complete.relationship is not None
  assert complete.relationship.transits is not None
  assert tuple(kind for kind, _ in complete.relationship.transits.items) == (TransitKind.DAYUN, TransitKind.LIUNIAN)
  for result in (partial, all_missing, complete):
    restored = ContextResult.from_json(result.export_json())
    assert restored == result
    # After round-trip the requested/obtained difference still resolves.
    assert isinstance(result.profile, RelationshipProfile) and isinstance(restored.profile, RelationshipProfile)
    assert result.profile.kinds == restored.profile.kinds


def test_relationship_at_moment_microseconds_are_evaluation_equal_but_recorded() -> None:
  c = BaziChart(Bazi.create('2000-01-01 12:00', 'male', BaziConfig.from_values(precision='hour')))
  profile_a = RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_moment', solar_moment=datetime(2024, 4, 10, 12, 30, 0, 500000)),
    (TransitKind.LIUNIAN, TransitKind.LIUYUE),
  )
  profile_b = RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_moment', solar_moment=datetime(2024, 4, 10, 12, 29, 59, 750000)),
    (TransitKind.LIUNIAN, TransitKind.LIUYUE),
  )
  left = evaluate_context(c, criterion_id=PALACE, profile=profile_a)
  right = evaluate_context(c, criterion_id=PALACE, profile=profile_b)
  assert left.criterion == right.criterion and left.relationship == right.relationship
  assert left != right # records keep the request as given, with no fake sub-second precision.
  assert isinstance(left.profile, RelationshipProfile) and isinstance(right.profile, RelationshipProfile)
  assert left.profile.coordinate is not None
  assert left.profile.coordinate.solar_moment is not None
  assert left.profile.coordinate.solar_moment.microsecond == 500000
  assert json.loads(left.export_json())['profile']['coordinate']['solar_moment'] == '2024-04-10T12:30:00.500000'
  assert ContextResult.from_json(left.export_json()) == left


def test_relationship_reference_matrix() -> None:
  # Related-entry matrix over include_reference_only × gender × structural status (three states).
  male = chart_from('2000-01-01 12:00', 'male')
  female = chart_from('2000-01-01 12:00', 'female')
  hidden: dict[str, Any] = {'include_reference_only': True}

  # False × anything: no reference section.
  off = evaluate_context(male, criterion_id=PALACE, profile=RelationshipProfile('natal'))
  assert off.related == () and '关联参考' not in off.render()

  # True × male × SATISFIED／NOT_SATISFIED／UNKNOWN (two reasons): entry returned, recognized=True.
  for result in (
    evaluate_context(male, criterion_id=PALACE, profile=RelationshipProfile('natal'), **hidden),
    evaluate_context(chart_from('2000-01-09 12:00', 'male'), criterion_id=PALACE, profile=RelationshipProfile('natal'), **hidden),
    evaluate_context(male, criterion_id=PALACE, profile=RelationshipProfile('natal_and_transits', None, (TransitKind.LIUNIAN,)), **hidden),
    evaluate_context(male, criterion_id=PALACE, profile=RelationshipProfile(
      'natal_and_transits', TransitCoordinate('at_year', gz_year=1998), (TransitKind.LIUNIAN,)), **hidden),
  ):
    assert [entry.claim_id for entry in result.related] == [RELATED_PALACE]
    assert all(entry.recognized for entry in result.related)
    rendered = result.render()
    assert '关联参考（该判据的条件参考，不表示结构已命中或完整前提已满足）：' + RELATED_PALACE in rendered
    assert knowledge_text(RELATED_PALACE) in rendered
    # NOT_SATISFIED／UNKNOWN use the same reference wording as SATISFIED; no 「已核结构命中」 appears.
    assert '已核结构命中' not in rendered
    assert '结构前提：' + result.criterion.status in rendered
    assert '结构判别不表示原文完整条件已满足，也不表示现实事件成立。' in rendered
    assert '前提满足只表示本范围内的原作使用条件满足' not in rendered

  # True × female: the two gated entries are never related (same-ID replacement included); structure is still evaluated; static queries stay unrestricted.
  female_result = evaluate_context(female, criterion_id=PALACE, profile=RelationshipProfile('natal'), **hidden)
  assert female_result.related == () and '关联参考' not in female_result.render()
  assert female_result.criterion.status == 'SATISFIED' # female charts are still evaluated by the structural criteria.
  knowledge = KnowledgeBase.load()
  assert knowledge.entry(RELATED_PALACE).text and knowledge.entry(RELATED_TOUGAN).text

  # True × male × entry missing from the knowledge base: no RelatedEntry is produced.
  trimmed = KnowledgeBase.from_json(knowledge.export_json(()))
  missing = evaluate_context(male, criterion_id=PALACE, profile=RelationshipProfile('natal'), knowledge=trimmed, **hidden)
  assert missing.related == () and '关联参考' not in missing.render()


def knowledge_text(claim_id: str) -> str:
  return KnowledgeBase.load().entry(claim_id).text


@pytest.mark.parametrize('dimension', ['text', 'premise', 'limits', 'viewpoint', 'object', 'source'])
def test_relationship_female_gate_precedes_binding_and_replacement(dimension: str) -> None:
  # Female charts never relate the two restricted IDs, and a same-ID custom replacement cannot bypass;
  # male replacement yields recognized=False, listing only the ID with 「绑定未识别」, without rendering the replacement text.
  knowledge = KnowledgeBase.load()
  data = json.loads(knowledge.export_json())
  entry = next(value for value in data['entries'] if value['claim_id'] == RELATED_PALACE)
  if dimension in ('text', 'premise', 'viewpoint'):
    entry[dimension] += '（编辑口径）'
  elif dimension == 'limits':
    entry['limits'] = [*entry['limits'], '编辑者另记的限度。']
  elif dimension == 'object':
    next(value for value in data['objects'] if value['object_id'] == 'concept.peiou_gong')['name'] = '同名异物'
  else:
    next(value for value in data['sources'] if value['source_id'] == 'tanyuan_qizi')['limitations'] += '不同边界。'
  custom = KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))

  female = evaluate_context(chart_from('2000-01-01 12:00', 'female'), criterion_id=PALACE,
                            profile=RelationshipProfile('natal'), knowledge=custom, include_reference_only=True)
  assert female.related == () and '关联参考' not in female.render()
  assert '（编辑口径）' not in female.render()

  male = evaluate_context(chart_from('2000-01-01 12:00', 'male'), criterion_id=PALACE,
                          profile=RelationshipProfile('natal'), knowledge=custom, include_reference_only=True)
  assert [entry.claim_id for entry in male.related] == [RELATED_PALACE]
  assert male.related[0] == RelatedEntry(RELATED_PALACE, False)
  rendered = male.render()
  assert ('关联参考（该判据的条件参考，不表示结构已命中或完整前提已满足）：' + RELATED_PALACE + '；绑定未识别') in rendered
  assert '绑定未识别' in rendered
  if dimension == 'text':
    assert '（编辑口径）' not in rendered
  assert ContextResult.from_json(male.export_json()) == male
  with pytest.raises(ValueError):
    RelatedEntry('', True)
  with pytest.raises(TypeError):
    RelatedEntry(RELATED_PALACE, 1) # type: ignore[arg-type]


def test_relationship_record_roundtrip_and_rejections() -> None:
  c = chart_from('2000-01-01 12:00', 'male')
  result = evaluate_context(c, criterion_id=TOUGAN, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_month', gz_year=2024, gz_month=_Dizhi.辰), (TransitKind.DAYUN, TransitKind.LIUNIAN),
  ), include_reference_only=True)
  data = json.loads(result.export_json())
  assert data['record_version'] == 3
  assert data['profile'] == {
    'scope': 'natal_and_transits',
    'coordinate': {'entry': 'at_month', 'gz_year': 2024, 'gz_month': '辰', 'solar_date': None, 'solar_moment': None},
    'kinds': ['dayun', 'liunian'],
  }
  assert data['occurrences'] == [] and data['entries'] == []
  assert data['related'] == [{'claim_id': RELATED_TOUGAN, 'recognized': True}]
  assert data['relationship']['star_target'] == {'tiangan': '癸', 'dizhi': ['子']}
  assert data['relationship']['transits'] == {'dayun': '甲戌', 'liunian': '甲辰'}
  assert ContextResult.from_json(result.export_json()) == result
  assert ContextResult.from_json(result.export_json()).render() == result.render()
  rendered = result.render()
  assert '范围：natal_and_transits；坐标=at_month；干支年=2024；干支月=辰；' in rendered
  assert '请求种类=[dayun,liunian]；取得种类=[dayun,liunian]；未取得种类=[]' in rendered

  # Direct evaluation of at_date and at_moment coordinates: date queries really work; the DAY-precision moment entry is unavailable.
  at_date = evaluate_context(c, criterion_id=TOUGAN, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_date', solar_date=_date_module(2024, 4, 10)),
    (TransitKind.LIUNIAN, TransitKind.LIUYUE, TransitKind.LIURI),
  ))
  assert at_date.criterion.scope_complete is True
  assert at_date.relationship is not None and at_date.relationship.transits is not None
  assert json.loads(at_date.export_json())['profile']['coordinate']['solar_date'] == '2024-04-10'
  assert ContextResult.from_json(at_date.export_json()) == at_date
  assert '坐标=at_date；公历日=2024-04-10' in at_date.render()

  # Non-canonical spellings rejected case by case: compact dates, space-separated moments, microsecond
  # abbreviations, offsets, branch-name readback, unordered kinds, non-negative indexes, bool indexes and bool years.
  def __mutate(section: str, key: Any, value: Any) -> str:
    mutated = json.loads(json.dumps(data))
    if section == 'profile.coordinate':
      mutated['profile']['coordinate'][key] = value
    elif section == 'profile':
      mutated['profile'][key] = value
    elif section == 'relationship':
      mutated['relationship'][key] = value
    return json.dumps(mutated)

  for section, key, value in (
    ('profile.coordinate', 'solar_date', '20240410'),
    ('profile.coordinate', 'solar_moment', '2024-04-10 12:00:00'),
    ('profile.coordinate', 'gz_year', True),
    ('profile', 'kinds', ['liunian', 'dayun']),
    ('profile', 'kinds', ['dayun', 'dayun', 'liunian']),
    ('profile', 'kinds', ['dayun', 'bogus']),
  ):
    with pytest.raises((TypeError, ValueError)):
      ContextResult.from_json(__mutate(section, key, value))

  # at_year records have mutually exclusive entry fields: injecting an at_month month into an at_year record must be rejected by the coordinate construction.
  year_result = evaluate_context(c, criterion_id=TOUGAN, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.LIUNIAN,),
  ), include_reference_only=True)
  year_data = json.loads(year_result.export_json())
  year_data['profile']['coordinate']['gz_month'] = '辰'
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(year_data))

  # Evidence combo indexes: bool and negative values rejected (combo members are {index, ganzhi} records).
  evidence = json.loads(json.dumps(data))
  star_relations = evidence['relationship']['star_relations']
  first_key = next(iter(star_relations))
  star_relations[first_key][0][0]['index'] = True
  with pytest.raises(TypeError):
    ContextResult.from_json(json.dumps(evidence))
  star_relations[first_key][0][0]['index'] = -1
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(evidence))


def test_relationship_record_version_before_keys_and_old_school() -> None:
  # Real v2 shape: a 官杀 record with the old key set (no relationship／related); the version check runs
  # before the key-set check, so the rejection is about the version, not key differences. Not a v3 with a hand-edited version number.
  context_record = json.loads(match().export_json())
  v2_text = json.dumps({
    key: value for key, value in context_record.items() if key not in ('relationship', 'related')
  } | {'record_version': 2}, ensure_ascii=False)
  with pytest.raises(ValueError, match='Unsupported record version'):
    ContextResult.from_json(v2_text)

  # v3 record version plus an old school (missing peiou_xing_def): a different trigger path from the case above.
  legacy_school = json.loads(match().export_json())
  config_block: dict[str, Any] = legacy_school['input']['config']
  config_block['school'] = {
    key: value for key, value in config_block['school'].items() if key != 'peiou_xing_def'
  }
  with pytest.raises(ValueError, match='Missing school field: peiou_xing_def'):
    ContextResult.from_json(json.dumps(legacy_school))

  # Third entry point: an old chart JSON missing that field hits the same message via BaziChart.from_json.
  chart_json: dict[str, Any] = dict(chart().json)
  chart_json['school'] = {
    key: value for key, value in chart_json['school'].items() if key != 'peiou_xing_def'
  }
  with pytest.raises(ValueError, match='Missing school field: peiou_xing_def'):
    BaziChart.from_json(chart_json)


def test_relationship_record_structural_constraints() -> None:
  result = rel_match(TOUGAN, birth='2000-01-29 06:00', include_reference_only=True)
  # RelationshipEvidence type gates and mutually exclusive combos are rejected, as is a criterion/profile kind mismatch.
  with pytest.raises(TypeError):
    replace(result, relationship=object()) # type: ignore[arg-type]
  with pytest.raises(ValueError, match='profile'):
    replace(result, profile=ContextProfile('natal'))
  with pytest.raises(ValueError):
    replace(result, occurrences=result_with_occurrences())
  guansha = match()
  with pytest.raises(ValueError):
    replace(guansha, relationship=result.relationship, related=result.related)
  # A natal-scope record carrying obtained 岁运 must be rejected.
  carrying = json.loads(result.export_json())
  carrying['relationship']['transits'] = {'liunian': '甲辰'}
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(carrying))
  # Obtained kinds beyond the requested set / indexes beyond the query sequence / scope_complete without all requested kinds.
  transiting = evaluate_context(chart_from('2000-01-01 12:00', 'male'), criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.DAYUN, TransitKind.LIUNIAN),
  ))
  exceeded = json.loads(transiting.export_json())
  exceeded['profile']['kinds'] = ['dayun']
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(exceeded))
  indexed = json.loads(result.export_json())
  indexed['relationship']['house_relations'] = {'冲': [[{'index': 9, 'ganzhi': '甲子'}]]}
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(indexed))
  # natal scope with scope_complete=True is legal; flipping it to True when kinds are missing under natal_and_transits must be rejected.
  partial_record = evaluate_context(chart_from('2000-01-01 12:00', 'male'), criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.XIAOYUN, TransitKind.DAYUN),
  ))
  incomplete = json.loads(partial_record.export_json())
  assert incomplete['criterion']['scope_complete'] is False
  incomplete['criterion']['scope_complete'] = True
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(incomplete))
  # related referencing a missing knowledge entry is rejected.
  missing_related = json.loads(result.export_json())
  missing_related['related'] = [{'claim_id': 'unknown.claim', 'recognized': True}]
  with pytest.raises(ValueError):
    ContextResult.from_json(json.dumps(missing_related))


def test_relationship_transits_flip_palace_and_tougan_verdicts() -> None:
  # Male chart born 2000-01-09 12:00 (己卯丁丑丙寅甲午): the chosen 岁运 really flip the verdict.
  c = chart_from('2000-01-09 12:00', 'male')

  def verdict(criterion_id: str, year: int | None) -> ContextResult:
    profile = RelationshipProfile('natal') if year is None else RelationshipProfile(
      'natal_and_transits', TransitCoordinate('at_year', gz_year=year), (TransitKind.DAYUN, TransitKind.LIUNIAN),
    )
    return evaluate_context(c, criterion_id=criterion_id, profile=profile)

  # 宫刑冲: NOT at birth; SAT in 2016 (乙亥大运、丙申流年, 申寅刑冲); NOT again in 2021／2024.
  assert verdict(PALACE, None).criterion.status == 'NOT_SATISFIED'
  flipped = verdict(PALACE, 2016)
  assert flipped.criterion.status == 'SATISFIED' and flipped.criterion.reason == 'premise_satisfied'
  assert flipped.criterion.scope_complete is True
  assert dict(flipped.criterion.observations) == {'day_pillar_in_chong': True, 'day_pillar_in_xing': True}
  assert flipped.relationship is not None and flipped.relationship.transits is not None
  assert flipped.relationship.transits.json == {'dayun': '乙亥', 'liunian': '丙申'}
  for year in (2021, 2024):
    stayed = verdict(PALACE, year)
    assert stayed.criterion.status == 'NOT_SATISFIED' and stayed.criterion.scope_complete is True
  # 透干: NOT at birth (辛 only hidden in 丑); SAT in 2021 (甲戌大运、辛丑流年, 辛明透); NOT again in 2024.
  assert verdict(TOUGAN, None).criterion.status == 'NOT_SATISFIED'
  assert verdict(TOUGAN, 2021).criterion.status == 'SATISFIED'
  assert verdict(TOUGAN, 2024).criterion.status == 'NOT_SATISFIED'
  for result in (flipped, verdict(PALACE, 2024), verdict(TOUGAN, 2021)):
    assert ContextResult.from_json(result.export_json()) == result


def test_relationship_record_zero_obtained_complete_scope_rejected() -> None:
  c = chart_from('2000-01-01 12:00', 'male')
  # Zero obtained: a no-coordinate record forged to scope_complete=True／SATISFIED must be rejected (via both direct construction and from_json).
  no_coordinate = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile('natal_and_transits', None, (TransitKind.LIUNIAN,)))
  assert no_coordinate.relationship is not None and no_coordinate.relationship.transits is None
  forged = replace(
    no_coordinate.criterion,
    status='SATISFIED', reason='premise_satisfied', scope_complete=True,
  )
  with pytest.raises(ValueError, match='Complete scope'):
    replace(no_coordinate, criterion=forged)
  record = json.loads(no_coordinate.export_json())
  record['criterion'].update(status='SATISFIED', reason='premise_satisfied', scope_complete=True)
  with pytest.raises(ValueError, match='Complete scope'):
    ContextResult.from_json(json.dumps(record))
  # Partially obtained: requesting {小运, 大运} obtains only 大运; scope_complete=True is likewise rejected.
  partial = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.XIAOYUN, TransitKind.DAYUN),
  ))
  incomplete = json.loads(partial.export_json())
  incomplete['criterion'].update(status='SATISFIED', reason='premise_satisfied', scope_complete=True)
  with pytest.raises(ValueError, match='Complete scope'):
    ContextResult.from_json(json.dumps(incomplete))
  # Obtained 岁运 but coordinate removed: complete scope must be rejected.
  complete = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.LIUNIAN,),
  ))
  assert complete.criterion.scope_complete is True
  no_coord_record = json.loads(complete.export_json())
  no_coord_record['profile']['coordinate'] = None
  with pytest.raises(ValueError, match='Complete scope'):
    ContextResult.from_json(json.dumps(no_coord_record))
  # Normal missing-data UNKNOWN records (scope_complete=False) still round-trip legally.
  for result in (no_coordinate, partial):
    assert result.criterion.scope_complete is False
    assert ContextResult.from_json(result.export_json()) == result


def test_relationship_record_combo_order_rejections_and_absorptions() -> None:
  result = rel_match(PALACE, birth='2000-01-01 12:00')
  data = json.loads(result.export_json())
  star_chong = data['relationship']['star_relations']['冲']
  assert len(star_chong) == 2
  # Combo outer order reversed: disagrees with the exported ascending index tuples; rejected.
  reversed_record = json.loads(json.dumps(data))
  reversed_record['relationship']['star_relations']['冲'] = list(reversed(star_chong))
  with pytest.raises(ValueError, match='canonical order'):
    ContextResult.from_json(json.dumps(reversed_record))
  # Shuffled combo members and relation keys are absorbed by the immutable sets/maps; round-trip stays equal.
  shuffled = json.loads(json.dumps(data))
  shuffled['relationship']['star_relations']['冲'] = [list(reversed(combo)) for combo in star_chong]
  shuffled['relationship']['star_relations'] = dict(
    reversed(list(shuffled['relationship']['star_relations'].items()))
  )
  assert ContextResult.from_json(json.dumps(shuffled)) == result
  assert ContextResult.from_json(json.dumps(data)) == result
  # appearances keep prior behavior: a record with swapped appearance items still round-trips equal by itself.
  swapping = rel_match(TOUGAN, birth='2000-01-29 06:00')
  swapped = json.loads(swapping.export_json())
  swapped['relationship']['appearances'] = list(reversed(swapped['relationship']['appearances']))
  restored = ContextResult.from_json(json.dumps(swapped))
  assert restored != swapping # different appearance order is a different record.
  assert ContextResult.from_json(restored.export_json()) == restored


def test_relationship_render_labels_categories_and_scopes() -> None:
  # Sections and categories asserted by value: a combo in both 宫 and 星 categories is listed with each label, not just the section headers.
  natal = rel_match(PALACE, birth='2000-01-01 12:00')
  rendered = natal.render()
  assert (
    '证据：原局内部；宫·刑：2:戊午、3:戊午；宫·冲：1:丙子、2:戊午；宫·破：0:己卯、2:戊午；'
    '宫·生：0:己卯、2:戊午；宫·克：1:丙子、2:戊午；星·刑：0:己卯、1:丙子；星·冲：1:丙子、2:戊午；'
    '星·冲：1:丙子、3:戊午；星·生：0:己卯、1:丙子；星·克：1:丙子、2:戊午；星·克：1:丙子、3:戊午'
  ) in rendered
  assert '证据：原局×岁运；无' in rendered and '证据：岁运内部；无' in rendered
  # Cross-group combos land in the 原局×岁运 section; the 2016 岁运 flips the 宫刑冲 criterion from NOT to SAT.
  transits = evaluate_context(chart_from('2000-01-09 12:00', 'male'), criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2016), (TransitKind.DAYUN, TransitKind.LIUNIAN),
  ))
  rendered = transits.render()
  assert (
    '证据：原局×岁运；宫·六合：2:丙寅、4:乙亥；宫·刑：2:丙寅、5:丙申；宫·冲：2:丙寅、5:丙申；'
    '宫·破：2:丙寅、4:乙亥；宫·生：2:丙寅、4:乙亥；宫·克：2:丙寅、5:丙申'
  ) in rendered
  # 明干 category: 辛 shows in the 2021 辛丑流年, so transit 明干 combos carry the 「明干」 label; pure-transit combos land in the 岁运内部 section.
  toug = evaluate_context(chart_from('2000-01-09 12:00', 'male'), criterion_id=TOUGAN, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2021), (TransitKind.DAYUN, TransitKind.LIUNIAN),
  ))
  rendered = toug.render()
  assert '明干·合：2:丙寅、5:辛丑' in rendered
  assert '明干·生：0:己卯、5:辛丑' in rendered
  assert rendered.count('明干·克：') == 4
  assert '证据：岁运内部；明干·克：4:甲戌、5:辛丑' in rendered


def test_relationship_cross_group_gong_precise_participants() -> None:
  # Male chart 戊寅己未甲申甲戌 (1998-08-05 20:00): at_year 2054 (干支年 label, 甲戌流年) queried for real.
  c = chart_from('1998-08-05 20:00', 'male')
  result = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2054), (TransitKind.LIUNIAN,),
  ), include_reference_only=True)
  assert result.criterion.status == 'SATISFIED' and result.criterion.scope_complete is True
  evidence = result.relationship
  assert evidence is not None and evidence.transits is not None
  assert evidence.transits.json == {'liunian': '甲戌'}
  # 拱会 is exactly 原局内部 {2,3} and 原局×岁运 {2,4}; index 2 is the day pillar 甲申,
  # index 4 is the 甲戌流年 chosen via the at_year entry (first item of the only requested kind; transit indexes start at 4).
  assert [sorted(o.index for o in combo) for combo in evidence.house_relations[DizhiRelation.拱会]] == [[2, 3], [2, 4]]
  participants = {
    occurrence.index: str(occurrence.ganzhi)
    for combo in evidence.house_relations[DizhiRelation.拱会]
    for occurrence in combo
  }
  assert participants == {2: '甲申', 3: '甲戌', 4: '甲戌'}
  assert ContextResult.from_json(result.export_json()) == result


def test_relationship_yinyanggan_evaluation_export_restore() -> None:
  # Male chart with 乙 day master (2000-01-08 12:00, 己卯丁丑乙丑壬午): the 阴阳干读法 targets 己 (丑、未),
  # and the non-default definition keeps its input identity across evaluation, export, and restoration.
  c = BaziChart(Bazi.create('2000-01-08 12:00', 'male', BaziConfig(school=BaziSchool(peiou_xing_def=PeiouXingDef.YINYANGGAN))))
  result = evaluate_context(c, criterion_id=TOUGAN, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.LIUNIAN,),
  ))
  assert result.criterion.status == 'SATISFIED' and result.criterion.reason == 'premise_satisfied'
  evidence = result.relationship
  assert evidence is not None
  assert evidence.star_target.tiangan is Tiangan.己 and evidence.star_target.dizhi == (_Dizhi.丑, _Dizhi.未)
  assert json.loads(result.input_json)['config']['school']['peiou_xing_def'] == 'YINYANGGAN'
  restored = ContextResult.from_json(result.export_json())
  assert restored == result
  assert json.loads(restored.input_json)['config']['school']['peiou_xing_def'] == 'YINYANGGAN'


def test_relationship_location_chart_evaluation_and_roundtrip() -> None:
  # Location chart (真太阳时) combined with a 婚恋 profile: at_year evaluation and record round-trip.
  c = BaziChart(Bazi.create(
    '2024-01-01T12:00:00+14:00', 'male',
    BaziConfig.from_values(precision='minute'), longitude=-157.4,
  ))
  result = evaluate_context(c, criterion_id=PALACE, profile=RelationshipProfile(
    'natal_and_transits', TransitCoordinate('at_year', gz_year=2024), (TransitKind.LIUNIAN,),
  ))
  assert result.criterion.status == 'SATISFIED' and result.criterion.scope_complete is True
  assert 'time_basis' in result.input_json
  restored = ContextResult.from_json(result.export_json())
  assert restored == result and restored.render() == result.render()


def result_with_occurrences() -> tuple[Any, ...]:
  occurrence = match().occurrences[0]
  return (occurrence,)
