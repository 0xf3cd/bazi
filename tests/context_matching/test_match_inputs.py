# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import FrozenInstanceError, asdict, fields, replace
from datetime import datetime
from typing import Any

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.common import frozendict
from bazi.context_matching import (
  Observation, NatalObservation, LiunianObservation, TransitObservation, LiunianPosition,
  ContextResult, CriterionResult, MatchStatus, CriterionReason,
  TransitCoordinate, YearCoordinate, _CRITERIA, evaluate_context,
)
from bazi.defines import Zhu, Tiangan, Ganzhi, DizhiRelation
from bazi.school import Anchor, BaziConfig, BaziSchool, DayRollover, DEFAULT_CONFIG
from bazi.transits import TransitKind, TransitSet
from bazi.utils.dizhi_utils import GanzhiOccurrence, GanzhiRelationDiscovery

from matching_samples import GUANSHA, LEGAL, PALACE, TOUGAN, chart, match, rel_match, Year, record
from matching_samples import occurrences, relationship_evidence


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
    LiunianObservation(value)
  with pytest.raises(TypeError):
    LiunianPosition(value)


def test_bad_requests_fail_instead_of_unknown() -> None:
  c = chart()
  options: dict[str, Any]
  for options in ({'criterion_id': 42}, {'observation': 'natal'}, {'knowledge': {}}, {'include_reference_only': 1}):
    with pytest.raises(TypeError):
      evaluate_context(c, **{'criterion_id': GUANSHA, 'observation': NatalObservation(), **options}) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    evaluate_context(None, criterion_id=GUANSHA, observation=NatalObservation()) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    NatalObservation(2024) # type: ignore[call-arg] # 原局观察不接坐标。
  with pytest.raises(ValueError):
    match(criterion_id='editorial.guansha_coexistance.v1')


def test_public_record_value_boundaries() -> None:
  result = match()
  o = occurrences(result)[0]
  change: dict[str, Any]
  for change in ({'position': Zhu.日}, {'stem': Tiangan.甲}):
    with pytest.raises(ValueError):
      replace(o, **change)
  for change in ({'index': True}, {'index': -1}, {'ganzhi': '己卯'}, {'stem': '己'}, {'shishen': '正印'}, {'position': '年'}, {'position': TransitKind.LIUNIAN}, {'layer': '明干'}):
    with pytest.raises(TypeError):
      replace(o, **change)
  with pytest.raises(ValueError):
    replace(occurrences(result)[1], stem=Tiangan.丁)
  for change in ({'reason': 'bad'}, {'reason': 'binding_unrecognized'}, {'criterion_id': 'unknown'}):
    with pytest.raises(ValueError):
      replace(result.criterion, **change) # type: ignore[arg-type] # 故意传入非法原因与未注册 ID。
  for change in ({'observations': {}}, {'observations': frozendict({1: True})}, {'observations': frozendict({'a': 1})}, {'reason': 1}):
    with pytest.raises(TypeError):
      replace(result.criterion, **change)
  for change in ({'observation': 'natal'}, {'criterion': {}}, {'evidence': []}, {'reference_ids': []}, {'reference_ids': (1,)}, {'_bazi': None}, {'knowledge': None}, {'evidence': (None,)}):
    with pytest.raises(TypeError):
      replace(result, **change)
  with pytest.raises(ValueError):
    replace(result, reference_ids=('unknown',))
  with pytest.raises(ValueError):
    replace(result, reference_ids=('',))


@pytest.mark.parametrize('reason,status,complete', [
  ('premise_satisfied', 'SATISFIED', True),
  ('required_classification_absent', 'NOT_SATISFIED', True),
  ('day_master_differs', 'NOT_SATISFIED', True),
  ('female_gate_false', 'NOT_SATISFIED', True),
  ('missing_transit_coordinate', 'UNKNOWN', False),
  ('transit_unavailable', 'UNKNOWN', False),
])
def test_criterion_reasons_derive_scope(
  reason: CriterionReason, status: MatchStatus, complete: bool,
) -> None:
  result = CriterionResult(GUANSHA, reason, frozendict({}))
  assert result.status == status and result.scope_complete is complete


@pytest.mark.parametrize('value', [None, True, 1, 1.0, [], {}])
def test_verdict_reason_types_raise_type_error(value: Any) -> None:
  result = match()
  with pytest.raises((TypeError, ValueError)) as error:
    replace(result.criterion, reason=value)
  assert type(error.value) is TypeError
  assert str(error.value).startswith('Expected str, got ')


@pytest.mark.parametrize('bad, hint', [
  (Bazi.create('2000-01-01 12:00', 'male'), r'wrap it with BaziChart\(bazi\)'),
  (None, r'build one with BaziChart\(Bazi.create\(birth_time, gender\)\)'),
])
def test_evaluate_context_hints_chart_input(bad: object, hint: str) -> None:
  with pytest.raises(TypeError, match=f'^Expected BaziChart, got <class .*>; {hint}$'):
    evaluate_context(bad, criterion_id=GUANSHA, observation=NatalObservation()) # type: ignore


@pytest.mark.parametrize('observation', [NatalObservation(), LiunianObservation(2024), LiunianObservation(), LiunianObservation(1998)])
@pytest.mark.parametrize('day,gender', [(3, 'female'), (5, 'male')])
@pytest.mark.parametrize('criterion_id', [key for key, value in _CRITERIA.items() if value.analysis_kind == 'context'])
@pytest.mark.parametrize('field,message', [
  ('reason', 'predicate_undefined'), ('criterion_id', 'editorial.unregistered.v1'),
])
def test_criterion_matrix_rejects_corruption(criterion_id: str, observation: Observation, day: int, gender: str, field: str, message: str) -> None:
  criterion = record(criterion_id, observation, day, gender).criterion
  change = {
    'reason': 'predicate_undefined',
    'criterion_id': 'editorial.unregistered.v1',
  }
  with pytest.raises(ValueError, match=message):
    replace(criterion, **{field: change[field]}) # type: ignore[arg-type]


def test_result_cross_field_constraints() -> None:
  result = rel_match(TOUGAN, birth='2000-01-29 06:00', include_reference_only=True)
  evidence = relationship_evidence(result)
  with pytest.raises(TypeError):
    replace(result, evidence=object()) # type: ignore[arg-type]
  with pytest.raises(ValueError, match='observation type'):
    replace(result, observation=LiunianObservation())
  with pytest.raises(ValueError):
    replace(result, evidence=occurrences(match())[:1])
  with pytest.raises(ValueError, match='Context criterion requires occurrences'):
    replace(match(), evidence=evidence)
  with pytest.raises(ValueError, match='Natal scope'):
    replace(result, evidence=replace(evidence, transits=TransitSet(liunian=Ganzhi.from_str('甲辰'))))
  with pytest.raises(ValueError, match='sequence'):
    replace(result, evidence=replace(evidence, house_relations=GanzhiRelationDiscovery({
      DizhiRelation.冲: (frozenset({GanzhiOccurrence(9, Ganzhi.from_str('甲子'))}),),
    })))
  with pytest.raises(ValueError, match='Unknown claim'):
    replace(result, reference_ids=('unknown.claim',))


def test_complete_scope_requires_obtained_kinds() -> None:
  def evaluate(coordinate: TransitCoordinate | None, kinds: tuple[TransitKind, ...]) -> ContextResult:
    return evaluate_context(chart(1, 'male'), criterion_id=PALACE, observation=TransitObservation(kinds, coordinate))

  no_coordinate = evaluate(None, (TransitKind.LIUNIAN,))
  partial = evaluate(YearCoordinate(ganzhi_year=2024), (TransitKind.XIAOYUN, TransitKind.DAYUN))
  for result in (no_coordinate, partial):
    assert result.criterion.scope_complete is False
    with pytest.raises(ValueError, match='Complete scope'):
      replace(result, criterion=replace(result.criterion, reason='premise_satisfied'))
  complete = evaluate(YearCoordinate(ganzhi_year=2024), (TransitKind.DAYUN, TransitKind.LIUNIAN))
  assert isinstance(complete.observation, TransitObservation) and complete.criterion.scope_complete
  with pytest.raises(ValueError, match='Complete scope'):
    replace(complete, observation=replace(complete.observation, coordinate=None))
  with pytest.raises(ValueError, match='requested kinds'):
    replace(complete, observation=replace(complete.observation, kinds=(TransitKind.DAYUN,)))


def test_result_fields_and_noncertification() -> None:
  result = match()
  assert tuple(asdict(result.criterion)) == ('criterion_id', 'reason', 'observations')
  assert CriterionResult.__match_args__ == ('criterion_id', 'reason', 'observations')
  assert ContextResult.__match_args__ == ('observation', 'criterion', 'evidence', 'reference_ids', '_bazi', 'knowledge')
  assert tuple(asdict(result)) == ('observation', 'criterion', 'evidence', 'reference_ids', '_bazi', 'knowledge')
  assert asdict(result)['reference_ids'] == LEGAL
  constructed = ContextResult(result.observation, result.criterion, result.evidence, LEGAL, result.bazi, result.knowledge)
  assert constructed == result and hash(constructed) == hash(result)
  match constructed:
    case ContextResult(_, _, _, ids, _, _):
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


def test_manual_reference_ids_keep_order_repeats() -> None:
  result = match()
  ids = (LEGAL[1], LEGAL[0], LEGAL[1])
  manual = replace(result, reference_ids=ids)
  assert manual.reference_ids == ids
  assert asdict(manual)['reference_ids'] == ids
  rendered = manual.render()
  assert rendered.index('原作参考前提：' + LEGAL[1]) < rendered.index('原作参考前提：' + LEGAL[0])
  assert rendered.count('原作参考前提：' + LEGAL[1]) == 2
  foreign = ('tiangan.ding.definition',)
  assert replace(result, reference_ids=foreign).reference_ids == foreign
  assert result.reference_ids == LEGAL
