# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import FrozenInstanceError, asdict, fields, replace
from datetime import datetime
from typing import Any, get_args

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.common import frozendict
from bazi.context_matching import (
  NatalObservation, LiunianObservation, TransitObservation,
  ContextResult, CriterionResult, MatchStatus, CriterionReason,
  TransitCoordinate, YearCoordinate, evaluate_context,
)
from bazi.defines import Zhu
from bazi.school import Anchor, BaziConfig, BaziSchool, DayRollover, TuwangDef, DEFAULT_CONFIG
from bazi.transits import TransitKind

from matching_samples import GUANSHA, LEGAL, PALACE, chart, match, rel_match
from matching_samples import occurrences


def test_input_identity_includes_configuration() -> None:
  result = match()
  assert result.bazi.solar_datetime == datetime(2000, 1, 3, 12) and str(result.bazi.gender) == 'female'
  assert result.bazi.config == DEFAULT_CONFIG
  assert len(fields(result.bazi.config.school)) == 25
  assert result.bazi.config.school.kongwang_anchor is Anchor.DAY
  assert result.bazi.config.school.tuwang_def is TuwangDef.WHOLE_MONTH
  for config in (
    BaziConfig(school=BaziSchool(day_rollover=DayRollover.ZIZHENG)),
    BaziConfig(school=BaziSchool(tuwang_def=TuwangDef.AFTER_TWELVE_DAYS)),
    BaziConfig.from_values(precision='hour'), BaziConfig.from_values(backend='hko'),
    BaziConfig.from_values(dayun_year_rule='fixed_decade'),
  ):
    changed = BaziChart(Bazi.create(datetime(2000, 1, 3, 12), 'female', config))
    changed_result = evaluate_context(changed, criterion_id=GUANSHA, observation=NatalObservation())
    assert changed_result.bazi != result.bazi and changed_result != result
    assert changed_result.bazi.config == config


def test_result_components_are_immutable() -> None:
  result = match()
  assert isinstance(result.observation, NatalObservation)
  with pytest.raises(FrozenInstanceError):
    result.observation.scope = 'natal' # type: ignore[misc]
  with pytest.raises(FrozenInstanceError):
    occurrences(result)[0].index = 1 # type: ignore[misc]
  with pytest.raises(TypeError):
    result.criterion.observations['female'] = False # type: ignore[index]
  assert result == match() and hash(result) == hash(match())


def test_result_directly_holds_input() -> None:
  baseline = match()
  incoming = baseline.bazi
  result = replace(baseline, bazi=incoming)
  assert result.bazi is incoming and result == baseline


@pytest.mark.input_contract('bazi.context_matching', 'ContextResult.render')
def test_result_render_rejects_surrogates() -> None:
  for result in (match(), rel_match()):
    bad = replace(result, criterion=replace(result.criterion, observations=frozendict({'\ud800': True})))
    with pytest.raises(ValueError, match='surrogate'):
      bad.render()


@pytest.mark.input_contract('bazi.context_matching', 'LiunianObservation')
@pytest.mark.parametrize('value', ['2024', 2024.0, []])
def test_year_rejects_non_int(value: Any) -> None:
  with pytest.raises(TypeError):
    LiunianObservation(value)


@pytest.mark.input_contract('bazi.context_matching', 'evaluate_context')
def test_bad_requests_fail_instead_of_unknown() -> None:
  c = chart()
  options: dict[str, Any]
  for options in ({'criterion_id': 42}, {'observation': 'natal'}):
    with pytest.raises(TypeError):
      evaluate_context(c, **{'criterion_id': GUANSHA, 'observation': NatalObservation(), **options}) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    evaluate_context(None, criterion_id=GUANSHA, observation=NatalObservation()) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    NatalObservation(2024) # type: ignore[call-arg] # 原局观察不接坐标。
  with pytest.raises(ValueError):
    match(criterion_id='editorial.guansha_coexistance.v1')


REASON_CASES = (
  ('premise_satisfied', 'SATISFIED', True),
  ('required_classification_absent', 'NOT_SATISFIED', True),
  ('day_master_differs', 'NOT_SATISFIED', True),
  ('female_gate_false', 'NOT_SATISFIED', True),
  ('missing_transit_coordinate', 'UNKNOWN', False),
  ('transit_unavailable', 'UNKNOWN', False),
)


@pytest.mark.optimized
@pytest.mark.parametrize('reason,status,complete', REASON_CASES)
def test_criterion_reasons_derive_scope(
  reason: CriterionReason, status: MatchStatus, complete: bool,
) -> None:
  assert {case[0] for case in REASON_CASES} == set(get_args(CriterionReason))
  result = CriterionResult(GUANSHA, reason, frozendict({}))
  assert result.status == status and result.scope_complete is complete


@pytest.mark.input_contract('bazi.context_matching', 'evaluate_context')
@pytest.mark.parametrize('bad, hint', [
  (Bazi.create('2000-01-01 12:00', 'male'), r'wrap it with BaziChart\(bazi\)'),
  (None, r'build one with BaziChart\(Bazi.create\(birth_time, gender\)\)'),
])
def test_evaluate_context_hints_chart_input(bad: object, hint: str) -> None:
  with pytest.raises(TypeError, match=f'^Expected BaziChart, got <class .*>; {hint}$'):
    evaluate_context(bad, criterion_id=GUANSHA, observation=NatalObservation()) # type: ignore


def test_complete_scope_requires_obtained_kinds() -> None:
  def evaluate(coordinate: TransitCoordinate | None, kinds: tuple[TransitKind, ...]) -> ContextResult:
    return evaluate_context(chart(1, 'male'), criterion_id=PALACE, observation=TransitObservation(kinds, coordinate))

  no_coordinate = evaluate(None, (TransitKind.LIUNIAN,))
  partial = evaluate(YearCoordinate(ganzhi_year=2024), (TransitKind.XIAOYUN, TransitKind.DAYUN))
  for result in (no_coordinate, partial):
    assert result.criterion.scope_complete is False
  complete = evaluate(YearCoordinate(ganzhi_year=2024), (TransitKind.DAYUN, TransitKind.LIUNIAN))
  assert isinstance(complete.observation, TransitObservation) and complete.criterion.scope_complete


def test_result_fields_and_noncertification() -> None:
  result = match()
  assert tuple(asdict(result.criterion)) == ('criterion_id', 'reason', 'observations')
  assert CriterionResult.__match_args__ == ('criterion_id', 'reason', 'observations')
  assert ContextResult.__match_args__ == ('observation', 'criterion', 'evidence', 'reference_ids', 'bazi')
  assert tuple(asdict(result)) == ('observation', 'criterion', 'evidence', 'reference_ids', 'bazi')
  assert asdict(result)['reference_ids'] == LEGAL
  constructed = ContextResult(result.observation, result.criterion, result.evidence, LEGAL, result.bazi)
  assert constructed == result and hash(constructed) == hash(result)
  match constructed:
    case ContextResult(_, _, _, ids, _):
      assert ids == LEGAL
    case _:
      pytest.fail('ContextResult positional pattern did not match')
  with pytest.raises(TypeError):
    replace(result, references=()) # type: ignore[call-arg] # Removed field.
  for name in ('status', 'definition', 'scope_complete'):
    with pytest.raises(TypeError):
      replace(result.criterion, **{name: 'obsolete'}) # type: ignore[arg-type] # 派生属性不再是构造字段。
  unknown = replace(result.criterion, reason='missing_transit_coordinate')
  assert replace(result, criterion=unknown).criterion.scope_complete is False
  manual = replace(result, observation=LiunianObservation(2024), criterion=unknown)
  assert manual.criterion.reason == 'missing_transit_coordinate'
  assert all(isinstance(value.position, Zhu) for value in occurrences(manual))


@pytest.mark.optimized
def test_manual_reference_ids_keep_order_repeats() -> None:
  result = match()
  ids = (LEGAL[1], LEGAL[0], LEGAL[1])
  manual = replace(result, reference_ids=ids)
  assert manual.reference_ids == ids
  assert asdict(manual)['reference_ids'] == ids
  rendered = manual.render()
  assert rendered.index('参考条目：' + LEGAL[1]) < rendered.index('参考条目：' + LEGAL[0])
  assert rendered.count('参考条目：' + LEGAL[1]) == 2
  foreign = ('tiangan.ding.definition',)
  assert replace(result, reference_ids=foreign).reference_ids == foreign
  assert result.reference_ids == LEGAL
