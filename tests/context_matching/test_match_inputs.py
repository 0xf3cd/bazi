# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime
from typing import Any, get_args

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.common import frozendict
from bazi.context_matching import (
  ContextProfile, ContextResult, EntryMatch, RelatedEntry, MatchReason, MatchStatus,
  RelationshipProfile, TransitCoordinate, _CRITERIA, evaluate_context,
)
from bazi.defines import Tiangan, Ganzhi, DizhiRelation
from bazi.school import Anchor, BaziConfig, BaziSchool, DayRollover, DEFAULT_CONFIG
from bazi.transits import TransitKind, TransitSet
from bazi.utils.dizhi_utils import GanzhiOccurrence, GanzhiRelationDiscovery

from matching_samples import GUANSHA, LEGAL, PALACE, TOUGAN, chart, match, rel_match, Year, record


def test_input_identity_includes_configuration() -> None:
  result = match()
  assert result.bazi.solar_datetime == datetime(2000, 1, 3, 12) and str(result.bazi.gender) == 'female'
  assert result.bazi.config == DEFAULT_CONFIG
  assert len(fields(result.bazi.config.school)) == 24
  assert result.bazi.config.school.kongwang_anchor is Anchor.DAY
  for config in (
    BaziConfig(school=BaziSchool(day_rollover=DayRollover.ZIZHENG)),
    BaziConfig.from_values(precision='hour'), BaziConfig.from_values(backend='hko'),
    BaziConfig.from_values(dayun_year_rule='fixed_decade'),
  ):
    changed = BaziChart(Bazi.create(datetime(2000, 1, 3, 12), 'female', config))
    changed_result = evaluate_context(changed, criterion_id=GUANSHA, profile=ContextProfile('natal'))
    assert changed_result.bazi != result.bazi and changed_result != result
    assert changed_result.bazi.config == config


def test_result_components_are_immutable() -> None:
  result = match()
  assert isinstance(result.profile, ContextProfile)
  with pytest.raises(FrozenInstanceError):
    result.profile.ganzhi_year = 2024 # type: ignore[misc]
  with pytest.raises(FrozenInstanceError):
    result.occurrences[0].index = 1 # type: ignore[misc]
  with pytest.raises(TypeError):
    result.criterion.observations['female'] = False # type: ignore[index]
  assert result == match() and hash(result) == hash(match())


def test_result_input_is_copied_in_and_out() -> None:
  baseline = match()
  incoming = baseline.bazi
  result = replace(baseline, _bazi=incoming)
  expected_hash, rendered, pillars = hash(result), result.render(), result.bazi.pillars
  outgoing = result.bazi
  assert outgoing is not result.bazi and outgoing is not incoming
  for value in (incoming, outgoing):
    # Private mutation is a probe of the copy boundary, not a supported Bazi operation.
    object.__setattr__(value, '_config', BaziConfig.from_values(dayun_year_rule='fixed_decade'))
    object.__setattr__(value, '_solar_datetime', datetime(2001, 1, 1))
  assert result == baseline and hash(result) == expected_hash
  assert result.render() == rendered and result.bazi.pillars == pillars


def test_result_render_rejects_surrogates() -> None:
  for result in (match(), rel_match()):
    bad = replace(result, criterion=replace(result.criterion, observations=frozendict({'\ud800': True})))
    with pytest.raises(ValueError, match='surrogate'):
      bad.render()


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
  for change in ({'profile': 'natal'}, {'criterion': {}}, {'occurrences': []}, {'entries': []}, {'_bazi': None}, {'knowledge': None}, {'occurrences': (None,)}, {'entries': (None,)}):
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


@pytest.mark.parametrize('profile', [ContextProfile('natal'), ContextProfile('natal_and_liunian', 2024), ContextProfile('natal_and_liunian'), ContextProfile('natal_and_liunian', 1998)])
@pytest.mark.parametrize('day,gender', [(3, 'female'), (5, 'male')])
@pytest.mark.parametrize('criterion_id', [key for key, value in _CRITERIA.items() if value.profile_kind == 'context'])
@pytest.mark.parametrize('field,message', [
  ('reason', 'predicate_undefined'), ('definition', 'Unsupported criterion definition'),
  ('status', 'Status and reason disagree'), ('criterion_id', 'editorial.unregistered.v1'),
])
def test_criterion_matrix_rejects_corruption(criterion_id: str, profile: ContextProfile, day: int, gender: str, field: str, message: str) -> None:
  criterion = record(criterion_id, profile, day, gender).criterion
  change = {
    'reason': 'predicate_undefined', 'definition': '完整前提已由程序确认。',
    'status': 'NOT_SATISFIED' if criterion.status == 'SATISFIED' else 'SATISFIED',
    'criterion_id': 'editorial.unregistered.v1',
  }
  with pytest.raises(ValueError, match=message):
    replace(criterion, **{field: change[field]}) # type: ignore[arg-type]


def test_result_cross_field_constraints() -> None:
  result = rel_match(TOUGAN, birth='2000-01-29 06:00', include_reference_only=True)
  assert result.relationship is not None
  with pytest.raises(TypeError):
    replace(result, relationship=object()) # type: ignore[arg-type]
  with pytest.raises(ValueError, match='profile'):
    replace(result, profile=ContextProfile('natal'))
  with pytest.raises(ValueError):
    replace(result, occurrences=match().occurrences[:1])
  with pytest.raises(ValueError, match='Context profile cannot carry relationship evidence'):
    replace(match(), relationship=result.relationship)
  with pytest.raises(ValueError, match='Premise criterion cannot carry condition references'):
    replace(match(), related=result.related)
  with pytest.raises(ValueError, match='Natal scope'):
    replace(result, relationship=replace(result.relationship, transits=TransitSet(liunian=Ganzhi.from_str('甲辰'))))
  with pytest.raises(ValueError, match='sequence'):
    replace(result, relationship=replace(result.relationship, house_relations=GanzhiRelationDiscovery({
      DizhiRelation.冲: (frozenset({GanzhiOccurrence(9, Ganzhi.from_str('甲子'))}),),
    })))
  with pytest.raises(ValueError, match='Unknown claim'):
    replace(result, related=(RelatedEntry('unknown.claim', True),))


def test_complete_scope_requires_obtained_kinds() -> None:
  def evaluate(coordinate: TransitCoordinate | None, kinds: tuple[TransitKind, ...]) -> ContextResult:
    return evaluate_context(chart(1, 'male'), criterion_id=PALACE, profile=RelationshipProfile('natal_and_transits', coordinate, kinds))

  no_coordinate = evaluate(None, (TransitKind.LIUNIAN,))
  partial = evaluate(TransitCoordinate('at_year', gz_year=2024), (TransitKind.XIAOYUN, TransitKind.DAYUN))
  for result in (no_coordinate, partial):
    assert result.criterion.scope_complete is False
    with pytest.raises(ValueError, match='Complete scope'):
      replace(result, criterion=replace(result.criterion, status='SATISFIED', reason='premise_satisfied', scope_complete=True))
  complete = evaluate(TransitCoordinate('at_year', gz_year=2024), (TransitKind.DAYUN, TransitKind.LIUNIAN))
  assert isinstance(complete.profile, RelationshipProfile) and complete.criterion.scope_complete
  with pytest.raises(ValueError, match='Complete scope'):
    replace(complete, profile=replace(complete.profile, coordinate=None))
  with pytest.raises(ValueError, match='requested kinds'):
    replace(complete, profile=replace(complete.profile, kinds=(TransitKind.DAYUN,)))
