# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import inspect
from dataclasses import FrozenInstanceError, fields, replace
from typing import Any

import pytest

import bazi.context_matching as matching_module
from bazi.context_matching import (
  NatalObservation, LiunianObservation, TransitObservation,
  _CRITERIA, evaluate_context, CriterionInfo, criterion as lookup_criterion, criteria,
)
from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.common import frozendict
from bazi.knowledge import KnowledgeBase
from bazi.transits import TransitKind

from matching_samples import (
  GUANSHA, FEMALE, LEGAL, RELATIONSHIP, DING, GENG, PIANYIN, XIAOYIN, CONDITION_CLAIMS,
  PALACE, TOUGAN, RELATED_PALACE, RELATED_TOUGAN,
)


# Literal public metadata, independent of the production registry and evaluator.
EXPECTED = frozendict({
  GUANSHA: CriterionInfo(
    GUANSHA, '选定范围内正官与七杀各至少出现一次。', 'context', 'premise',
    ('observed_coexistence', 'female'), None, LEGAL, frozendict({}),
  ),
  FEMALE: CriterionInfo(
    FEMALE, '选定范围内正官与七杀各至少出现一次，且输入为女命。', 'context', 'premise',
    ('observed_coexistence', 'female'), BaziGender.FEMALE, RELATIONSHIP, frozendict({}),
  ),
  DING: CriterionInfo(
    DING, '日主为丁火；身弱、克太多留在条目文字中，程序不判别。', 'context', 'condition',
    ('day_master_ding',), None, (CONDITION_CLAIMS[DING],), frozendict({}),
  ),
  GENG: CriterionInfo(
    GENG, '日主为庚金；行运有制有化、后天有教养留在条目文字中，程序不判别；即使选了流年，也不视为条文中的行运。',
    'context', 'condition', ('day_master_geng',), None, (CONDITION_CLAIMS[GENG],), frozendict({}),
  ),
  PIANYIN: CriterionInfo(
    PIANYIN, '选定范围内偏印至少出现一次；喜用、不过旺、不受刑克冲害留在条目文字中，程序不判别。',
    'context', 'condition', ('pianyin_observed',), None, (CONDITION_CLAIMS[PIANYIN],), frozendict({}),
  ),
  XIAOYIN: CriterionInfo(
    XIAOYIN, '选定范围内偏印与食神各至少出现一次；共现不等于枭印夺食，夺食是否成立留在条目文字中。',
    'context', 'condition', ('pianyin_observed', 'shishen_observed'), None, (CONDITION_CLAIMS[XIAOYIN],), frozendict({}),
  ),
  PALACE: CriterionInfo(
    PALACE, '选定范围内，日柱地支作为具体参与者卷入刑或冲；刑按命盘流派的刑定义解释。',
    'relationship', 'condition', ('day_pillar_in_chong', 'day_pillar_in_xing'), None,
    (RELATED_PALACE,), frozendict({RELATED_PALACE: BaziGender.MALE}),
  ),
  TOUGAN: CriterionInfo(
    TOUGAN, '选定范围内，按命盘流派配置的配偶星目标干至少有一处明干实际出现。',
    'relationship', 'condition', ('target_stem_visible', 'target_stem_hidden'), None,
    (RELATED_TOUGAN,), frozendict({RELATED_TOUGAN: BaziGender.MALE}),
  ),
})


def _check_directory(directory: frozendict[str, CriterionInfo]) -> None:
  assert tuple(directory) == tuple(EXPECTED)
  assert directory == EXPECTED


def test_directory_is_complete_immutable_no_load(monkeypatch: pytest.MonkeyPatch) -> None:
  def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError('Directory lookup must not create a chart or load a corpus')
  monkeypatch.setattr(KnowledgeBase, 'load', forbidden)
  monkeypatch.setattr(Bazi, 'create', forbidden)
  monkeypatch.setattr(BaziChart, '__init__', forbidden)
  directory = criteria()
  _check_directory(directory)
  for identifier, info in directory.items():
    assert lookup_criterion(identifier) == info and hash(lookup_criterion(identifier)) == hash(info)
    assert info.observation_types == ((NatalObservation, LiunianObservation) if info.analysis_kind == 'context' else (NatalObservation, TransitObservation))
    assert info.required_inputs == ('chart', 'criterion_id', 'observation')
    assert info.optional_inputs == ('knowledge', 'include_reference_only')
    parameters = inspect.signature(evaluate_context).parameters
    assert info.required_inputs == tuple(name for name, parameter in parameters.items() if parameter.default is inspect.Parameter.empty)
    assert info.optional_inputs == tuple(name for name, parameter in parameters.items() if parameter.default is not inspect.Parameter.empty)
    assert set(info.unknown_conditions) == {'missing_transit_coordinate', 'transit_unavailable'}
    assert all(text.strip() for text in info.unknown_conditions.values())
    if info.analysis_kind == 'context':
      assert info.scopes == ('natal', 'natal_and_liunian')
      assert info.scope_inputs == {'natal': (), 'natal_and_liunian': ('ganzhi_year',)}
      assert info.transit_entries == {} and info.transit_kinds == {}
    else:
      assert info.scopes == ('natal', 'natal_and_transits')
      assert info.scope_inputs == {'natal': (), 'natal_and_transits': ('coordinate', 'kinds')}
      assert info.transit_entries == {
        'at_year': ('ganzhi_year',), 'at_month': ('ganzhi_year', 'ganzhi_month'),
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
  ({'analysis_kind': 'unknown'}, ValueError), ({'entry_role': 'full'}, ValueError),
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


def test_guards_missing_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
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
    _check_directory(frozendict({**directory, 'test.ninth': replace(directory[GUANSHA], criterion_id='test.ninth')}))
  with pytest.raises(AssertionError):
    _check_directory(frozendict({key: value for key, value in directory.items() if key != GUANSHA}))
  with pytest.raises(AssertionError):
    _check_directory(frozendict(dict(reversed(tuple(directory.items())))))


@pytest.mark.parametrize('change', [
  {'definition': 'wrong'}, {'analysis_kind': 'relationship'}, {'entry_role': 'condition'},
  {'observation_keys': ('wrong',)}, {'claim_ids': tuple(reversed(LEGAL))},
  {'required_gender': BaziGender.MALE}, {'claim_genders': frozendict({LEGAL[0]: BaziGender.MALE})},
])
def test_metadata_oracle_rejects_changes(change: dict[str, Any]) -> None:
  directory = criteria()
  changed = replace(directory[GUANSHA], **change)
  with pytest.raises(AssertionError):
    _check_directory(frozendict({**directory, GUANSHA: changed}))
