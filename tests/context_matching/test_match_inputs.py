# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime
from typing import Any, get_args

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.common import frozendict
from bazi.context_matching import ContextProfile, ContextResult, EntryMatch, MatchReason, MatchStatus, evaluate_context
from bazi.defines import Tiangan
from bazi.school import BaziConfig, BaziSchool, DayRollover, _config_json
from bazi.transits import TransitKind

from matching_samples import GUANSHA, LEGAL, chart, match, Year


def test_input_identity_includes_configuration() -> None:
  result = match()
  identity = json.loads(result.input_json)
  assert identity['birth_time'] == '2000-01-03T12:00:00' and identity['gender'] == 'female'
  assert identity['config']['backend'] == 'celestial' and identity['config']['precision'] == 'day'
  assert len(identity['config']['school']) == 24
  assert identity['config']['school']['kongwang_anchor'] == 'DAY'
  for config in (
    BaziConfig(school=BaziSchool(day_rollover=DayRollover.ZIZHENG)),
    BaziConfig.from_values(precision='hour'), BaziConfig.from_values(backend='hko'),
    BaziConfig.from_values(dayun_year_rule='fixed_decade'),
  ):
    changed = BaziChart(Bazi.create(datetime(2000, 1, 3, 12), 'female', config))
    changed_result = evaluate_context(changed, criterion_id=GUANSHA, profile=ContextProfile('natal'))
    assert changed_result.input_json != result.input_json
    assert ContextResult.from_json(changed_result.export_json()) == changed_result


def test_result_components_are_immutable() -> None:
  result = match()
  assert isinstance(result.profile, ContextProfile)
  with pytest.raises(FrozenInstanceError):
    result.profile.ganzhi_year = 2024 # type: ignore[misc]
  with pytest.raises(FrozenInstanceError):
    result.occurrences[0].index = 1 # type: ignore[misc]
  with pytest.raises(TypeError):
    result.criterion.observations['female'] = False # type: ignore[index]
  assert hash(result) == hash(ContextResult.from_json(result.export_json()))


def test_wire_roster_and_chart_input_agree() -> None:
  c = chart()
  wire = _config_json(c.bazi.config)
  assert set(wire) == {field.name for field in fields(BaziConfig)}
  assert set(wire['school']) == {field.name for field in fields(BaziSchool)}
  chart_json: dict[str, Any] = dict(c.json)
  assert {key: chart_json[key] for key in wire} == wire
  assert json.loads(match().input_json)['config'] == wire


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
    EntryMatch(1, 'UNKNOWN', 'binding_unrecognized') # type: ignore[arg-type]
  with pytest.raises(ValueError):
    EntryMatch('', 'UNKNOWN', 'binding_unrecognized')
  for change in ({'profile': 'natal'}, {'criterion': {}}, {'occurrences': []}, {'entries': []}, {'input_json': None}, {'knowledge': None}, {'occurrences': (None,)}, {'entries': (None,)}):
    with pytest.raises(TypeError):
      replace(result, **change)
  with pytest.raises(ValueError):
    replace(result, entries=(EntryMatch('unknown', 'UNKNOWN', 'binding_unrecognized'),))


def test_each_reason_has_one_admissible_status() -> None:
  expected: dict[MatchReason, MatchStatus] = {
    'premise_satisfied': 'SATISFIED',
    'required_classification_absent': 'NOT_SATISFIED',
    'day_master_differs': 'NOT_SATISFIED',
    'female_gate_false': 'NOT_SATISFIED',
    'missing_transit_coordinate': 'UNKNOWN',
    'transit_unavailable': 'UNKNOWN',
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
def test_verdict_status_types_raise_type_error(value: Any) -> None:
  result = match()
  for factory in (
    lambda: EntryMatch(LEGAL[0], value, 'premise_satisfied'),
    lambda: replace(result.criterion, status=value),
  ):
    with pytest.raises((TypeError, ValueError)) as error:
      factory()
    assert type(error.value) is TypeError
    assert str(error.value).startswith('Expected str, got ')


@pytest.mark.parametrize('bad, hint', [
  (Bazi.create('2000-01-01 12:00', 'male'), r'wrap it with BaziChart\(bazi\)'),
  (None, r'build one with BaziChart\(Bazi.create\(birth_time, gender\)\)'),
])
def test_evaluate_context_hints_chart_input(bad: object, hint: str) -> None:
  with pytest.raises(TypeError, match=f'^Expected BaziChart, got <class .*>; {hint}$'):
    evaluate_context(bad, criterion_id=GUANSHA, profile=ContextProfile('natal')) # type: ignore
