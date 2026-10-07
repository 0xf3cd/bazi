# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.common import frozendict
from bazi.context_matching import (
  ContextProfile, ContextResult, EntryMatch, evaluate_context,
)
from bazi.defines import Ganzhi, Tiangan, Shishen
from bazi.knowledge import KnowledgeBase
from bazi.school import BaziConfig, BaziSchool, DayRollover
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
  assert data['profile'] == {'stem_scope': 'visible_and_hidden', 'observation_scope': 'natal_and_liunian', 'ganzhi_year': 2024}
  assert data['input'] == json.loads(result.input_json)
  assert len(data['occurrences']) == 13
  assert data['occurrences'][-3:] == [
    {'origin': 'transit', 'pillar': 'liunian', 'index': 4, 'ganzhi': '甲辰', 'layer': 'hidden', 'stem': stem, 'shishen': classification, 'kind': 'liunian', 'ganzhi_year': 2024}
    for stem, classification in [('戊', '比肩'), ('乙', '正官'), ('癸', '正财')]
  ]


@pytest.mark.parametrize('day,year,reason', [(1, None, 'missing_transit_coordinate'), (3, None, 'missing_transit_coordinate'), (1, 1998, 'transit_unavailable')])
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
  assert result.criterion.observations['day_master_is_geng']
  assert result.criterion.observations['observed_pianyin'] and result.criterion.observations['observed_shishen']
  assert result.entries == (EntryMatch(claim_id, 'UNKNOWN', 'predicate_undefined'),)
  restored = KnowledgeBase.from_json(result.knowledge_json)
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
  assert len(knowledge.query()) == 19
  result = match()
  assert result.criterion.revision == 1 and result.profile.stem_scope == 'visible_and_hidden'
  data = json.loads(result.export_json())
  assert data['knowledge'] == json.loads(knowledge.export_json())
  assert len(data['knowledge']['entries']) == 295
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
  assert json.loads(result.knowledge_json) == data
  assert ContextResult.from_json(result.export_json()) == result
  if dimension == 'qualification':
    default = evaluate_context(chart(), criterion_id=GUANSHA, profile=ContextProfile('natal'), knowledge=custom)
    assert default.entries == (EntryMatch(LEGAL[0], 'UNKNOWN', 'binding_unrecognized'),)


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
  assert len(identity['config']['school']) == 22
  changed = BaziChart(Bazi.create(datetime(2000, 1, 3, 12), 'female', BaziConfig(school=BaziSchool(day_rollover=DayRollover.ZIZHENG))))
  assert evaluate_context(changed, criterion_id=GUANSHA, profile=ContextProfile('natal')).input_json != result.input_json
  with pytest.raises(FrozenInstanceError):
    result.profile.ganzhi_year = 2024 # type: ignore[misc]
  with pytest.raises(FrozenInstanceError):
    result.occurrences[0].index = 1 # type: ignore[misc]
  with pytest.raises(TypeError):
    result.criterion.observations['female'] = False # type: ignore[index]
  assert hash(result) == hash(ContextResult.from_json(result.export_json()))


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
  for change in ({'origin': 'other'}, {'pillar': 'other'}, {'layer': 'other'}, {'index': -1}, {'kind': TransitKind.DAYUN}, {'ganzhi_year': 2024}, {'pillar': 'day', 'index': 2}, {'stem': Tiangan.甲}):
    with pytest.raises(ValueError):
      replace(o, **change)
  for change in ({'index': True}, {'ganzhi': '己卯'}, {'stem': '己'}, {'shishen': '正印'}, {'kind': 'liunian'}, {'ganzhi_year': True}):
    with pytest.raises(TypeError):
      replace(o, **change)
  with pytest.raises(ValueError):
    replace(result.occurrences[1], stem=Tiangan.丁)
  with pytest.raises(ValueError):
    replace(o, origin='transit')
  for change in ({'revision': 2}, {'definition': 'other'}, {'status': 'UNKNOWN'}, {'reason': 'bad'}, {'scope_complete': False}):
    with pytest.raises(ValueError):
      replace(result.criterion, **change)
  for change in ({'revision': True}, {'observations': {}}, {'observations': frozendict({1: True})}, {'observations': frozendict({'a': 1})}, {'scope_complete': 1}):
    with pytest.raises(TypeError):
      replace(result.criterion, **change)
  with pytest.raises(TypeError):
    EntryMatch(1, 'UNKNOWN', 'predicate_undefined') # type: ignore[arg-type]
  with pytest.raises(ValueError):
    EntryMatch('', 'UNKNOWN', 'predicate_undefined')
  for change in ({'profile': 'natal'}, {'criterion': {}}, {'occurrences': []}, {'entries': []}, {'input_json': None}, {'knowledge_json': None}, {'occurrences': (None,)}, {'entries': (None,)}):
    with pytest.raises(TypeError):
      replace(result, **change)
  with pytest.raises(ValueError):
    replace(result, entries=(EntryMatch('unknown', 'UNKNOWN', 'predicate_undefined'),))


@pytest.mark.parametrize('dimension,value,error', [
  ('record_version', True, ValueError), ('record_version', 2, ValueError),
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
  with pytest.raises(TypeError):
    ContextResult.from_json(42) # type: ignore[arg-type]
  with pytest.raises(ValueError):
    ContextResult.from_json('{"record_version":1,"record_version":1}')
  with pytest.raises(TypeError):
    ContextResult.from_json('[]')


def test_corpus_organization_and_frozen_oracle_hash() -> None:
  import hashlib
  fixture = Path(__file__).with_name('data') / 'description_legacy_baseline.json'
  assert hashlib.sha256(fixture.read_bytes()).hexdigest() == '6e50cf38d5b9a74a6f2a7ba2b3502b8dad818955a67ac6530e97f8d768f6b774'
  knowledge = KnowledgeBase.load()
  assert len(knowledge.entries) == 295 and len(knowledge.sources) == 9 and len(knowledge.query()) == 19
  for criterion, keys, context_id in ((GUANSHA, LEGAL, 'editorial.guansha_coexistence'), (FEMALE, RELATIONSHIP, 'editorial.guansha_coexistence_female')):
    assert tuple(e.claim_id for e in knowledge.query(context_id=context_id, include_reference_only=True)) == keys
    assert knowledge.query(context_id=context_id) == ()
    for key in keys:
      entry = knowledge.entry(key)
      assert entry.applicability == 'described' and entry.sources == ('editorial',)
      assert entry.output == 'reference_only' and entry.viewpoint == '仓内原作'
      assert all(limit in knowledge.render(entry) for limit in knowledge.contexts[context_id].limits)
    assert all(m.status == 'SATISFIED' for m in match(criterion_id=criterion).entries)
