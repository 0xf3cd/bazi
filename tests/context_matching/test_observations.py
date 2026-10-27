# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import asdict, fields, replace
from datetime import datetime
from datetime import date as _date_module  # The construction-time matrix needs the native date type.
from datetime import UTC as _UTC
from typing import Any, get_args

import pytest

from bazi.context_matching import (
  Observation, NatalObservation, LiunianObservation, TransitObservation, ScopeName,
  YearCoordinate, MonthCoordinate, DateCoordinate, MomentCoordinate,
  _BINDINGS, _CRITERIA, _binding_digest, evaluate_context,
  _CLASS_CRITERIA, _DAY_MASTER_CRITERIA, _RELATED_GENDERS,
)
from bazi.knowledge import KnowledgeBase
from bazi.transits import TransitKind
from bazi.bazi import BaziGender as _BaziGender
from bazi.defines import Dizhi as _Dizhi

from matching_samples import (
  GUANSHA,
  FEMALE,
  DING,
  GENG,
  PIANYIN,
  XIAOYIN,
  CONDITION_CLAIMS,
  chart,
  Year,
  PALACE,
  TOUGAN,
  RELATED_PALACE,
  RELATED_TOUGAN,
)


def test_relationship_claims_have_male_gates() -> None:
  # Claims of all relationship criteria sit in _BINDINGS; the gate table holds exactly the two restricted IDs and is a subset of those claims.
  relationship_claims = {
    claim_id for criterion in _CRITERIA.values()
    if criterion.analysis_kind == 'relationship' for claim_id in criterion.claims
  }
  assert relationship_claims == {RELATED_PALACE, RELATED_TOUGAN}
  assert relationship_claims <= set(_BINDINGS)
  assert set(_RELATED_GENDERS) == {RELATED_PALACE, RELATED_TOUGAN}
  assert set(_RELATED_GENDERS) <= relationship_claims
  assert all(gender is _BaziGender.MALE for gender in _RELATED_GENDERS.values())


def test_criteria_partition_scope_and_entry_roles() -> None:
  # Analysis kind picks accepted observations and evidence; entry role picks how claims attach.
  assert {key for key, value in _CRITERIA.items() if value.analysis_kind == 'context'} == {GUANSHA, FEMALE, *CONDITION_CLAIMS}
  assert {key for key, value in _CRITERIA.items() if value.entry_role == 'premise'} == {GUANSHA, FEMALE}
  assert all(claim_id in _BINDINGS for criterion in _CRITERIA.values() for claim_id in criterion.claims)
  # evaluate_context treats any context criterion outside both fact tables as 官杀: each must be in exactly one place.
  context_conditions = {key for key, value in _CRITERIA.items() if value.analysis_kind == 'context' and value.entry_role == 'condition'}
  assert not set(_DAY_MASTER_CRITERIA) & set(_CLASS_CRITERIA)
  assert set(_DAY_MASTER_CRITERIA) | set(_CLASS_CRITERIA) == context_conditions


def test_literal_criterion_definitions() -> None:
  assert {key: value.definition for key, value in _CRITERIA.items()} == {
    GUANSHA: '选定范围内正官与七杀各至少出现一次。',
    FEMALE: '选定范围内正官与七杀各至少出现一次，且输入为女命。',
    DING: '日主为丁火；身弱、克太多留在条目文字中，程序不判别。',
    GENG: '日主为庚金；行运有制有化、后天有教养留在条目文字中，程序不判别；即使选了流年，也不视为条文中的行运。',
    PIANYIN: '选定范围内偏印至少出现一次；喜用、不过旺、不受刑克冲害留在条目文字中，程序不判别。',
    XIAOYIN: '选定范围内偏印与食神各至少出现一次；共现不等于枭印夺食，夺食是否成立留在条目文字中。',
    PALACE: '选定范围内，日柱地支作为具体参与者卷入刑或冲；刑按命盘流派的刑定义解释。',
    TOUGAN: '选定范围内，按命盘流派配置的配偶星目标干至少有一处明干实际出现。',
  }


@pytest.mark.parametrize('claim_id', [RELATED_PALACE, RELATED_TOUGAN])
def test_relationship_binding_fingerprints(claim_id: str) -> None:
  knowledge = KnowledgeBase.load()
  assert _binding_digest(knowledge, knowledge.entry(claim_id)) == _BINDINGS[claim_id]


@pytest.mark.parametrize('criterion_id, observation', [
  (PALACE, LiunianObservation(2024)),
  (GUANSHA, TransitObservation((TransitKind.LIUNIAN,))),
  *((criterion_id, TransitObservation((TransitKind.LIUNIAN,))) for criterion_id in CONDITION_CLAIMS),
])
def test_criterion_rejects_foreign_observation(criterion_id: str, observation: Observation) -> None:
  with pytest.raises(ValueError, match='does not support'):
    evaluate_context(chart(), criterion_id=criterion_id, observation=observation)


def test_natal_observation_is_shared() -> None:
  observation = NatalObservation()
  for criterion_id in _CRITERIA:
    assert evaluate_context(chart(), criterion_id=criterion_id, observation=observation).observation is observation
  assert get_args(ScopeName) == ('natal', 'natal_and_liunian', 'natal_and_transits')


@pytest.mark.parametrize('kwargs, error', [
  ({'coordinate': 'at_year', 'kinds': (TransitKind.LIUNIAN,)}, TypeError),
  ({}, TypeError),
  ({'kinds': ()}, ValueError),
  ({'kinds': [TransitKind.LIUNIAN]}, TypeError),
  ({'kinds': ('liunian',)}, TypeError),
  ({'kinds': (TransitKind.LIUNIAN, TransitKind.LIUNIAN)}, ValueError),
  ({
    'coordinate': YearCoordinate(ganzhi_year=2024),
    'kinds': (TransitKind.LIUYUE,),
  }, ValueError),
  ({
    'coordinate': MonthCoordinate(ganzhi_year=2024, ganzhi_month=_Dizhi.辰),
    'kinds': (TransitKind.LIURI,),
  }, ValueError),
])
def test_transit_observation_request_errors(kwargs: dict[str, Any], error: type[Exception]) -> None:
  with pytest.raises(error):
    TransitObservation(**kwargs)


def test_observation_normalizes_unordered_kinds() -> None:
  observation = TransitObservation(
    (TransitKind.LIUNIAN, TransitKind.XIAOYUN, TransitKind.DAYUN),
    DateCoordinate(solar_date=_date_module(2024, 4, 10)),
  )
  assert observation.kinds == (TransitKind.XIAOYUN, TransitKind.DAYUN, TransitKind.LIUNIAN)
  assert observation == TransitObservation(
    (TransitKind.DAYUN, TransitKind.LIUNIAN, TransitKind.XIAOYUN),
    DateCoordinate(solar_date=_date_module(2024, 4, 10)),
  )
  # Missing coordinates are legal requests, unlike malformed coordinates.
  assert TransitObservation((TransitKind.LIUNIAN,)).coordinate is None


@pytest.mark.parametrize('factory, kwargs, error', [
  (YearCoordinate, {}, TypeError),
  (YearCoordinate, {'ganzhi_month': _Dizhi.酉}, TypeError),
  (YearCoordinate, {'ganzhi_year': 2024, 'solar_date': _date_module(2024, 4, 10)}, TypeError),
  (MonthCoordinate, {'ganzhi_year': 2024}, TypeError),
  (MonthCoordinate, {'ganzhi_month': _Dizhi.酉}, TypeError),
  (DateCoordinate, {}, TypeError),
  (DateCoordinate, {'solar_date': _date_module(2024, 4, 10), 'ganzhi_year': 2024}, TypeError),
  (MomentCoordinate, {}, TypeError),
  (MomentCoordinate, {'solar_moment': datetime(2024, 4, 10, 12), 'ganzhi_month': _Dizhi.酉}, TypeError),
  (YearCoordinate, {'ganzhi_year': True}, TypeError),
  (YearCoordinate, {'ganzhi_year': Year(2024)}, TypeError),
  (MonthCoordinate, {'ganzhi_year': True, 'ganzhi_month': _Dizhi.酉}, TypeError),
  (MonthCoordinate, {'ganzhi_year': 2024, 'ganzhi_month': '酉'}, TypeError),
  (DateCoordinate, {'solar_date': datetime(2024, 4, 10, 12)}, TypeError),
  (MomentCoordinate, {'solar_moment': _date_module(2024, 4, 10)}, TypeError),
  (MomentCoordinate, {'solar_moment': datetime(2024, 4, 10, 12, tzinfo=_UTC)}, ValueError),
])
def test_transit_coordinate_request_errors(factory: Any, kwargs: dict[str, Any], error: type[Exception]) -> None:
  with pytest.raises(error):
    factory(**kwargs)


@pytest.mark.parametrize('value', [
  NatalObservation(), LiunianObservation(), TransitObservation((TransitKind.LIUNIAN,)),
  YearCoordinate(2024), MonthCoordinate(2024, _Dizhi.辰), DateCoordinate(_date_module(2024, 4, 10)),
  MomentCoordinate(datetime(2024, 4, 10, 12, 0, 0, 123456)),
])
def test_fixed_labels_are_not_dataclass_fields(value: Any) -> None:
  label = 'scope' if isinstance(value, Observation) else 'entry'
  assert label not in asdict(value) and label not in value.__match_args__
  assert label not in {field.name for field in fields(value)}
  assert label + '=' not in repr(value)
  with pytest.raises(TypeError):
    replace(value, **{label: 'other'})
  assert value == replace(value) and hash(value) == hash(replace(value))


@pytest.mark.parametrize('factory, kwargs', [
  (NatalObservation, {'ganzhi_year': 2024}),
  (LiunianObservation, {'coordinate': YearCoordinate(2024)}),
  (LiunianObservation, {'scope': 'natal'}),
  (TransitObservation, {'kinds': (TransitKind.LIUNIAN,), 'ganzhi_year': 2024}),
  (TransitObservation, {'kinds': (TransitKind.LIUNIAN,), 'scope': 'natal'}),
])
def test_observations_reject_foreign_fields(factory: Any, kwargs: dict[str, Any]) -> None:
  with pytest.raises(TypeError):
    factory(**kwargs)
