# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path
from typing import Any

import pytest

import bazi.context_matching as matching_module
from bazi.context_matching import (
  ContextProfile, _CRITERIA, evaluate_context, CriterionInfo, criterion as lookup_criterion, criteria,
)
from bazi.context_matching import RelationshipProfile, TransitCoordinate
from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.common import frozendict
from bazi.knowledge import KnowledgeBase
from bazi.transits import TransitKind

from matching_samples import GUANSHA, FEMALE, LEGAL


DIRECTORY_BASELINE: dict[str, Any] = json.loads(
  (Path(__file__).parents[1] / 'data' / 'criterion_behavior_v200.json').read_text(encoding='utf-8')
)


def _check_directory_coverage(directory: frozendict[str, CriterionInfo], cases: list[dict[str, Any]]) -> None:
  assert set(directory) == {case['criterion_id'] for case in cases}
  for identifier in directory:
    assert {case['scenario'] for case in cases if case['criterion_id'] == identifier} == {
      'natal', 'transit', 'missing', 'unavailable', 'binding_changed', 'entry_missing', 'default_output',
    }


def _check_directory_info(info: CriterionInfo, case: dict[str, Any]) -> None:
  assert info.criterion_id == case['criterion_id']
  assert info.definition == case['expected']['criterion']['definition']
  assert info.profile_kind == case['profile_kind']
  assert info.profile_type is (ContextProfile if case['profile_kind'] == 'context' else RelationshipProfile)
  assert info.entry_role == case['entry_role']
  assert info.observation_keys == tuple(case['observation_keys'])
  assert info.claim_ids == tuple(case['claim_ids'])
  assert info.required_gender is (BaziGender.FEMALE if case['criterion_id'] == FEMALE else None)
  assert info.claim_genders == ({key: BaziGender.MALE for key in case['claim_ids']} if case['profile_kind'] == 'relationship' else {})
  assert info.binding_effect == ('entry_unknown' if case['entry_role'] == 'premise' else 'related_unrecognized')


def test_directory_is_complete_immutable_no_load(monkeypatch: pytest.MonkeyPatch) -> None:
  def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError('Directory lookup must not create a chart or load a corpus')
  monkeypatch.setattr(KnowledgeBase, 'load', forbidden)
  monkeypatch.setattr(Bazi, 'create', forbidden)
  monkeypatch.setattr(BaziChart, '__init__', forbidden)
  directory = criteria()
  _check_directory_coverage(directory, DIRECTORY_BASELINE['cases'])
  assert set(directory) == set(_CRITERIA)
  assert DIRECTORY_BASELINE['source_sha'] == 'ddfe16e7c51d695167b09cc4c2f64ba46e7565c3'
  assert tuple(directory) == tuple(dict.fromkeys(case['criterion_id'] for case in DIRECTORY_BASELINE['cases']))
  for identifier, info in directory.items():
    assert lookup_criterion(identifier) == info and hash(lookup_criterion(identifier)) == hash(info)
    assert info.required_inputs == ('chart', 'criterion_id', 'profile')
    assert info.optional_inputs == ('knowledge', 'include_reference_only')
    parameters = inspect.signature(evaluate_context).parameters
    assert info.required_inputs == tuple(name for name, parameter in parameters.items() if parameter.default is inspect.Parameter.empty)
    assert info.optional_inputs == tuple(name for name, parameter in parameters.items() if parameter.default is not inspect.Parameter.empty)
    assert set(info.unknown_conditions) == {'missing_transit_coordinate', 'transit_unavailable'}
    assert set(info.unknown_conditions) == {
      reason for reason, status in matching_module._STATUS_BY_REASON.items()
      if status == 'UNKNOWN' and reason != 'binding_unrecognized'
    }
    assert all(text.strip() for text in info.unknown_conditions.values())
    if info.profile_type is ContextProfile:
      assert info.scopes == ('natal', 'natal_and_liunian')
      assert info.scope_inputs == {'natal': (), 'natal_and_liunian': ('ganzhi_year',)}
      assert info.transit_entries == {} and info.transit_kinds == {}
    else:
      assert info.scopes == ('natal', 'natal_and_transits')
      assert info.scope_inputs == {'natal': (), 'natal_and_transits': ('coordinate', 'kinds')}
      assert info.transit_entries == {
        'at_year': ('gz_year',), 'at_month': ('gz_year', 'gz_month'),
        'at_date': ('solar_date',), 'at_moment': ('solar_moment',),
      }
      assert info.transit_kinds == {
        'at_year': frozenset((TransitKind.XIAOYUN, TransitKind.DAYUN, TransitKind.LIUNIAN)),
        'at_month': frozenset((TransitKind.XIAOYUN, TransitKind.DAYUN, TransitKind.LIUNIAN, TransitKind.LIUYUE)),
        'at_date': frozenset(TransitKind), 'at_moment': frozenset(TransitKind),
      }
    with pytest.raises(FrozenInstanceError):
      info.definition = 'changed' # type: ignore[misc]
    with pytest.raises(TypeError):
      info.scope_inputs['natal'] = ('changed',) # type: ignore[index]
    with pytest.raises(TypeError):
      directory[identifier] = info # type: ignore[index]


@pytest.mark.parametrize('case', DIRECTORY_BASELINE['cases'], ids=lambda case: case['criterion_id'] + ':' + case['scenario'])
def test_directory_matches_v200_behavior(case: dict[str, Any]) -> None:
  info = lookup_criterion(case['criterion_id'])
  _check_directory_info(info, case)
  profile_data = case['profile']
  profile: ContextProfile | RelationshipProfile
  if case['profile_kind'] == 'context':
    profile = ContextProfile(**profile_data)
  else:
    coordinate = None if profile_data['coordinate'] is None else TransitCoordinate(**profile_data['coordinate'])
    profile = RelationshipProfile(profile_data['scope'], coordinate, tuple(TransitKind(kind) for kind in profile_data['kinds']))
  knowledge = KnowledgeBase.load()
  entries = tuple(knowledge.entries.values())
  if case['scenario'] == 'binding_changed':
    entries = tuple(replace(entry, text=entry.text + '（测试改写）') if entry.claim_id == case['claim_ids'][0] else entry for entry in entries)
  elif case['scenario'] == 'entry_missing':
    entries = tuple(entry for entry in entries if entry.claim_id not in case['claim_ids'])
  if case['scenario'] in ('binding_changed', 'entry_missing'):
    knowledge = KnowledgeBase(tuple(knowledge.objects.values()), tuple(knowledge.contexts.values()), tuple(knowledge.sources.values()), entries)
  result = evaluate_context(
    BaziChart(Bazi.create(case['birth'], case['gender'])),
    criterion_id=case['criterion_id'],
    profile=profile,
    knowledge=knowledge,
    include_reference_only=case['scenario'] != 'default_output',
  )
  text = result.export_json()
  record_data = json.loads(text)
  for key in ('criterion', 'entries', 'related'):
    assert record_data[key] == case['expected'][key]
  assert hashlib.sha256(text.encode()).hexdigest() == case['expected']['record_sha256']
  assert tuple(result.criterion.observations) == info.observation_keys
  if result.criterion.status == 'UNKNOWN':
    assert result.criterion.reason in info.unknown_conditions
  if case['scenario'] == 'binding_changed':
    assert result.criterion.reason != 'binding_unrecognized'
    if info.binding_effect == 'entry_unknown':
      assert result.entries[0].reason == 'binding_unrecognized'
    else:
      assert result.related[0].recognized is False


@pytest.mark.parametrize('value', [None, 1, True, '', ' ', 'unknown'])
def test_directory_lookup_rejects_invalid_ids(value: object) -> None:
  with pytest.raises(ValueError if isinstance(value, str) else TypeError):
    lookup_criterion(value) # type: ignore[arg-type]


def test_constructor_checks_each_declared_field() -> None:
  info = lookup_criterion(GUANSHA)
  for field in fields(info):
    change: dict[str, Any] = {field.name: object()}
    with pytest.raises(TypeError):
      replace(info, **change)


@pytest.mark.parametrize('field', ['criterion_id', 'definition'])
@pytest.mark.parametrize('value, error, message', [
  (object(), TypeError, "Expected str, got <class 'object'>"),
  ('', ValueError, 'Expected non-empty text'),
  (' \t\u3000', ValueError, 'Expected non-empty text'),
])
def test_text_fields_keep_validation_messages(field: str, value: object, error: type[Exception], message: str) -> None:
  change: dict[str, Any] = {field: value}
  with pytest.raises(error) as failure:
    replace(lookup_criterion(GUANSHA), **change)
  assert str(failure.value) == message


@pytest.mark.parametrize('change, error', [
  ({'criterion_id': ''}, ValueError), ({'definition': ' '}, ValueError),
  ({'profile_type': int}, ValueError), ({'entry_role': 'full'}, ValueError),
  ({'observation_keys': ()}, ValueError), ({'observation_keys': ('x', 'x')}, ValueError),
  ({'claim_ids': ()}, ValueError), ({'claim_ids': ('x', 'x')}, ValueError),
  ({'observation_keys': ('',)}, ValueError),
  ({'claim_genders': frozendict({'unknown': BaziGender.MALE})}, ValueError),
  ({'claim_genders': frozendict({1: BaziGender.MALE})}, TypeError),
  ({'claim_genders': frozendict({LEGAL[0]: 'male'})}, TypeError),
])
def test_constructor_rejects_invalid_metadata(change: dict[str, Any], error: type[Exception]) -> None:
  with pytest.raises(error):
    replace(lookup_criterion(GUANSHA), **change)


def test_guards_missing_metadata_behavior_cases(monkeypatch: pytest.MonkeyPatch) -> None:
  directory = criteria()
  with monkeypatch.context() as patcher:
    patcher.setattr(matching_module, '_CRITERIA', frozendict({**_CRITERIA, 'test.ninth': _CRITERIA[GUANSHA]}))
    with pytest.raises(ValueError, match='Unsupported criterion metadata'):
      criteria()
  with monkeypatch.context() as patcher:
    patcher.setattr(matching_module, '_CRITERIA', frozendict({**_CRITERIA, GUANSHA: _CRITERIA[GUANSHA]._replace(claims=())}))
    with pytest.raises(ValueError, match='non-empty distinct metadata'):
      lookup_criterion(GUANSHA)
  with pytest.raises(AssertionError):
    _check_directory_coverage(frozendict({**directory, 'test.ninth': replace(directory[GUANSHA], criterion_id='test.ninth')}), DIRECTORY_BASELINE['cases'])
  with pytest.raises(AssertionError):
    _check_directory_coverage(directory, [case for case in DIRECTORY_BASELINE['cases'] if case['criterion_id'] != GUANSHA])
  case = next(case for case in DIRECTORY_BASELINE['cases'] if case['criterion_id'] == GUANSHA)
  for changed in (
    replace(directory[GUANSHA], observation_keys=('wrong',)),
    replace(directory[GUANSHA], profile_type=RelationshipProfile),
  ):
    with pytest.raises(AssertionError):
      _check_directory_info(changed, case)
  with monkeypatch.context() as patcher:
    patcher.setattr(CriterionInfo, 'binding_effect', property(lambda self: 'related_unrecognized'))
    with pytest.raises(AssertionError):
      _check_directory_info(directory[GUANSHA], case)
