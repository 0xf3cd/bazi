# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import replace

import pytest

from bazi.context_matching import NatalObservation, LiunianObservation, LiunianPosition, criterion
from bazi.defines import Zhu
from bazi.knowledge import KnowledgeBase

from matching_samples import DING, GENG, PIANYIN, XIAOYIN, CONDITION_CLAIMS, match
from matching_samples import occurrences


@pytest.mark.parametrize('criterion_id,day,year,observations,reason', [
  (DING, 10, None, {'day_master_ding': True}, 'premise_satisfied'),
  (DING, 3, None, {'day_master_ding': False}, 'day_master_differs'),
  (DING, 10, 2024, {'day_master_ding': True}, 'premise_satisfied'),
  (DING, 3, 2024, {'day_master_ding': False}, 'day_master_differs'),
  (GENG, 3, None, {'day_master_geng': True}, 'premise_satisfied'),
  (GENG, 10, None, {'day_master_geng': False}, 'day_master_differs'),
  # The 2024 流年 is recorded as evidence but adds no observation key: it is not read as the text's 行运.
  (GENG, 3, 2024, {'day_master_geng': True}, 'premise_satisfied'),
  (GENG, 10, 2024, {'day_master_geng': False}, 'day_master_differs'),
  # Day 3 holds 偏印 only as the 戊 hidden in 申 (literal inventory above); counting visible stems alone flips these.
  (PIANYIN, 3, None, {'pianyin_observed': True}, 'premise_satisfied'),
  (PIANYIN, 5, None, {'pianyin_observed': False}, 'required_classification_absent'),
  (PIANYIN, 5, 2020, {'pianyin_observed': True}, 'premise_satisfied'),
  (XIAOYIN, 3, None, {'pianyin_observed': True, 'shishen_observed': True}, 'premise_satisfied'),
  (XIAOYIN, 1, None, {'pianyin_observed': True, 'shishen_observed': False}, 'required_classification_absent'),
  (XIAOYIN, 13, None, {'pianyin_observed': False, 'shishen_observed': True}, 'required_classification_absent'),
  # Day 2 (己) has 伤官 庚 at the hour but no 食神 辛, so the 食神 key cannot be satisfied by its neighbor.
  (XIAOYIN, 2, None, {'pianyin_observed': True, 'shishen_observed': False}, 'required_classification_absent'),
  # The 2024 流年 supplies the missing 偏印, so both keys hold only with the transit included.
  (XIAOYIN, 13, 2024, {'pianyin_observed': True, 'shishen_observed': True}, 'premise_satisfied'),
])
@pytest.mark.parametrize('gender', ['female', 'male'])
def test_conditions_judge_only_computable_facts(
  criterion_id: str, day: int, year: int | None, observations: dict[str, bool], reason: str, gender: str,
) -> None:
  observation = NatalObservation() if year is None else LiunianObservation(year)
  result = match(day, gender, criterion_id=criterion_id, observation=observation)
  assert result.criterion.observations == observations
  assert result.criterion.reason == reason and result.criterion.scope_complete is True
  assert result.criterion.status == ('SATISFIED' if reason == 'premise_satisfied' else 'NOT_SATISFIED')
  assert any(isinstance(o.position, LiunianPosition) for o in occurrences(result)) is (year is not None)
  # The reference is attached whatever the fact verdict or gender, and never as a premise match.
  assert result.reference_ids == (CONDITION_CLAIMS[criterion_id],)


@pytest.mark.parametrize('criterion_id', CONDITION_CLAIMS)
@pytest.mark.parametrize('year,reason', [(None, 'missing_transit_coordinate'), (1998, 'transit_unavailable')])
def test_conditions_keep_scope_reasons_apart(criterion_id: str, year: int | None, reason: str) -> None:
  # Day 3 makes the 丁 fact false and the other three true; incomplete scope overrides both.
  result = match(3, criterion_id=criterion_id, observation=LiunianObservation(year))
  assert result.criterion.status == 'UNKNOWN' and result.criterion.reason == reason
  assert result.criterion.scope_complete is False
  assert result.criterion.observations == match(3, criterion_id=criterion_id).criterion.observations
  assert result.reference_ids == (CONDITION_CLAIMS[criterion_id],)
  assert all(isinstance(o.position, Zhu) for o in occurrences(result))


@pytest.mark.parametrize('criterion_id', CONDITION_CLAIMS)
def test_references_identify_unevaluated_text(criterion_id: str) -> None:
  knowledge = KnowledgeBase.load()
  claim_id = CONDITION_CLAIMS[criterion_id]
  entry = knowledge.entry(claim_id)
  result = match(3, criterion_id=criterion_id)
  rendered = result.render()
  assert f'参考条目：{claim_id}' in rendered and entry.text not in rendered
  assert '事实判别不表示原文完整条件已满足，也不表示现实事件成立。' in rendered
  for text in (entry.text, entry.premise, *entry.limits):
    assert text in knowledge.render(entry)


def test_entry_role_separates_premise_condition() -> None:
  premise = match(3)
  condition = match(3, criterion_id=PIANYIN)
  assert criterion(premise.criterion.criterion_id).entry_role == 'premise'
  assert criterion(condition.criterion.criterion_id).entry_role == 'condition'
  for result in (premise, condition):
    empty = replace(result, reference_ids=())
    rendered = empty.render()
    assert ('结构前提：' in rendered) is (result is premise)
    assert ('事实判别不表示原文完整条件已满足' in rendered) is (result is condition)
