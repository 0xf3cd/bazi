# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from datetime import datetime
from datetime import date as _date_module  # The construction-time matrix needs the native date type.
from datetime import UTC as _UTC
from typing import Any

import pytest

from bazi.context_matching import (
  ContextProfile, _BINDINGS, _CRITERIA, _binding_digest, evaluate_context, RelationshipProfile, TransitCoordinate,
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
    if criterion.profile_kind == 'relationship' for claim_id in criterion.claims
  }
  assert relationship_claims == {RELATED_PALACE, RELATED_TOUGAN}
  assert relationship_claims <= set(_BINDINGS)
  assert set(_RELATED_GENDERS) == {RELATED_PALACE, RELATED_TOUGAN}
  assert set(_RELATED_GENDERS) <= relationship_claims
  assert all(gender is _BaziGender.MALE for gender in _RELATED_GENDERS.values())


def test_criteria_partition_scope_and_entry_roles() -> None:
  # Two independent axes: profile kind picks the scope and evidence shape, entry role picks how claims attach.
  assert {key for key, value in _CRITERIA.items() if value.profile_kind == 'context'} == {GUANSHA, FEMALE, *CONDITION_CLAIMS}
  assert {key for key, value in _CRITERIA.items() if value.entry_role == 'premise'} == {GUANSHA, FEMALE}
  assert all(claim_id in _BINDINGS for criterion in _CRITERIA.values() for claim_id in criterion.claims)
  # evaluate_context treats any context criterion outside both fact tables as 官杀: each must be in exactly one place.
  context_conditions = {key for key, value in _CRITERIA.items() if value.profile_kind == 'context' and value.entry_role == 'condition'}
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


@pytest.mark.parametrize('criterion_id, profile, error', [
  (PALACE, ContextProfile('natal'), ValueError),
  (PALACE, ContextProfile('natal_and_liunian', 2024), ValueError),
  (GUANSHA, RelationshipProfile('natal'), ValueError),
  *((criterion_id, RelationshipProfile('natal'), ValueError) for criterion_id in CONDITION_CLAIMS),
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


def test_profile_normalizes_unordered_kinds() -> None:
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
