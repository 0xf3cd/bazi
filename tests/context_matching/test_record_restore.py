# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from typing import Any, get_args

import pytest

from bazi.context_matching import ContextProfile, ContextResult, MatchReason, ObservationScope, _CRITERIA

from matching_samples import match, record


# One profile per scope state a context record can carry: complete natal, complete 流年, missing year, unavailable year.
RECORD_PROFILES = (
  ContextProfile('natal'), ContextProfile('natal_and_liunian', 2024),
  ContextProfile('natal_and_liunian'), ContextProfile('natal_and_liunian', 1998),
)
RECORD_CHARTS = ((3, 'female'), (5, 'male'))
RECORD_CRITERIA = tuple(key for key, value in _CRITERIA.items() if value.profile_kind == 'context')


def test_record_matrix_is_a_legal_baseline() -> None:
  results = [
    (profile, record(criterion_id, profile, day, gender))
    for criterion_id in RECORD_CRITERIA for profile in RECORD_PROFILES for day, gender in RECORD_CHARTS
  ]
  for _, result in results:
    assert ContextResult.from_json(result.export_json()) == result
    assert json.loads(result.export_json())['relationship'] is None
  assert {p.observation_scope for p, r in results if r.criterion.scope_complete} == set(get_args(ObservationScope))
  # binding_unrecognized qualifies entries only, never a criterion.
  assert {r.criterion.reason for _, r in results} == set(get_args(MatchReason)) - {'binding_unrecognized'}


@pytest.mark.parametrize('field,message', [
  ('reason', 'predicate_undefined'), ('definition', 'Unsupported criterion definition'),
  ('status', 'Status and reason disagree'), ('criterion_id', 'editorial.unregistered.v1'),
])
@pytest.mark.parametrize('day,gender', RECORD_CHARTS)
@pytest.mark.parametrize('profile', RECORD_PROFILES)
@pytest.mark.parametrize('criterion_id', RECORD_CRITERIA)
def test_restore_rejects_a_corrupted_criterion(
  criterion_id: str, profile: ContextProfile, day: int, gender: str, field: str, message: str,
) -> None:
  data = json.loads(record(criterion_id, profile, day, gender).export_json())
  criterion = data['criterion']
  criterion[field] = {
    'reason': 'predicate_undefined',
    'definition': '完整前提已由程序确认。',
    'status': 'NOT_SATISFIED' if criterion['status'] == 'SATISFIED' else 'SATISFIED',
    'criterion_id': 'editorial.unregistered.v1',
  }[field]
  with pytest.raises(ValueError, match=message):
    ContextResult.from_json(json.dumps(data, ensure_ascii=False))


@pytest.mark.parametrize('dimension,value,error', [
  ('record_version', True, ValueError), ('record_version', False, ValueError),
  ('record_version', -1, ValueError), ('record_version', 0, ValueError),
  ('record_version', 1, ValueError), ('record_version', 2, ValueError),
  ('record_version', 3, ValueError), ('record_version', 4, ValueError), ('record_version', 6, ValueError),
  ('record_version', 4.0, ValueError), ('record_version', 5.0, ValueError),
  ('record_version', '4', ValueError),
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


def test_restore_rejects_duplicate_keys() -> None:
  text = match().export_json()
  for needle, duplicate in (
    ('"record_version": 5', '"record_version": 5'),
    ('"gender": "female"', '"gender": "male"'),
    ('"scope_complete": true', '"scope_complete": false'),
  ):
    assert text.count(needle) == 1
    corrupted = text.replace(needle, needle + ', ' + duplicate)
    with pytest.raises(ValueError, match='Duplicate JSON key'):
      ContextResult.from_json(corrupted)
