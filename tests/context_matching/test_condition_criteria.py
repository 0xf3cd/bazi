# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import replace

import pytest

from bazi.context_matching import ContextProfile, ContextResult, RelatedEntry, evaluate_context
from bazi.knowledge import KnowledgeBase

from matching_samples import DING, GENG, PIANYIN, XIAOYIN, CONDITION_CLAIMS, chart, match


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
  profile = ContextProfile('natal') if year is None else ContextProfile('natal_and_liunian', year)
  result = match(day, gender, criterion_id=criterion_id, profile=profile)
  assert result.criterion.observations == observations
  assert result.criterion.reason == reason and result.criterion.scope_complete is True
  assert result.criterion.status == ('SATISFIED' if reason == 'premise_satisfied' else 'NOT_SATISFIED')
  assert any(o.origin == 'transit' for o in result.occurrences) is (year is not None)
  # The reference is attached whatever the fact verdict or gender, and never as a premise match.
  assert result.entries == () and result.related == (RelatedEntry(CONDITION_CLAIMS[criterion_id], True),)
  data = json.loads(result.export_json())
  assert data['entries'] == [] and data['related'] == [{'claim_id': CONDITION_CLAIMS[criterion_id], 'recognized': True}]
  assert ContextResult.from_json(result.export_json()) == result


@pytest.mark.parametrize('criterion_id', CONDITION_CLAIMS)
def test_conditions_without_entry_still_judge(criterion_id: str) -> None:
  knowledge = KnowledgeBase.load()
  claim_id = CONDITION_CLAIMS[criterion_id]
  custom = KnowledgeBase.from_json(knowledge.export_json(tuple(e for e in knowledge.entries.values() if e.claim_id != claim_id)))
  result = match(3, criterion_id=criterion_id, knowledge=custom)
  assert result.criterion == match(3, criterion_id=criterion_id).criterion
  assert result.related == () and result.entries == ()
  assert '关联参考' not in result.render() and '事实判别不表示原文完整条件已满足' in result.render()
  assert ContextResult.from_json(result.export_json()) == result


@pytest.mark.parametrize('criterion_id', CONDITION_CLAIMS)
@pytest.mark.parametrize('year,reason', [(None, 'missing_transit_coordinate'), (1998, 'transit_unavailable')])
def test_conditions_keep_scope_reasons_apart(criterion_id: str, year: int | None, reason: str) -> None:
  # Day 3 makes the 丁 fact false and the other three true; incomplete scope overrides both.
  result = match(3, criterion_id=criterion_id, profile=ContextProfile('natal_and_liunian', year))
  assert result.criterion.status == 'UNKNOWN' and result.criterion.reason == reason
  assert result.criterion.scope_complete is False
  assert result.criterion.observations == match(3, criterion_id=criterion_id).criterion.observations
  assert result.entries == () and result.related == (RelatedEntry(CONDITION_CLAIMS[criterion_id], True),)
  assert all(o.origin == 'natal' for o in result.occurrences)
  assert ContextResult.from_json(result.export_json()) == result


@pytest.mark.parametrize('criterion_id', CONDITION_CLAIMS)
def test_references_render_full_unevaluated_text(criterion_id: str) -> None:
  knowledge = KnowledgeBase.load()
  claim_id = CONDITION_CLAIMS[criterion_id]
  entry = knowledge.entry(claim_id)
  result = match(3, criterion_id=criterion_id, knowledge=knowledge)
  rendered = result.render()
  block = rendered.split(f'关联参考（该判据的条件参考，不表示事实已成立或完整前提已满足）：{claim_id}\n', 1)[1]
  assert block == knowledge.render(entry, premise_verdict='完整前提未由程序判别')
  for text in (entry.text, entry.premise, *entry.limits, *(limit for key in entry.contexts for limit in knowledge.contexts[key].limits)):
    assert text in block
  assert entry.legacy is not None and entry.legacy.field_premise in block
  assert '事实判别不表示原文完整条件已满足，也不表示现实事件成立。' in rendered
  assert '前提满足只表示' not in rendered and '原作参考前提：' not in rendered
  # Static lookup by the same context returns the same entry without a chart verdict.
  assert tuple(value.claim_id for value in knowledge.query(context_id=criterion_id, include_reference_only=True)) == (claim_id,)
  assert '前提判别：' not in knowledge.render(entry)
  # Reference output stays opt-in: the default call judges the same fact and attaches nothing.
  default = evaluate_context(chart(3), criterion_id=criterion_id, profile=ContextProfile('natal'), knowledge=knowledge)
  assert default.criterion == result.criterion and default.related == ()


@pytest.mark.parametrize('criterion_id', CONDITION_CLAIMS)
def test_reference_binding_leaves_the_fact(criterion_id: str) -> None:
  claim_id = CONDITION_CLAIMS[criterion_id]
  data = json.loads(KnowledgeBase.load().export_json())
  next(e for e in data['entries'] if e['claim_id'] == claim_id)['text'] = 'CUSTOM-REPLACEMENT-TEXT'
  knowledge = KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))
  result = match(3, criterion_id=criterion_id, knowledge=knowledge)
  assert result.related == (RelatedEntry(claim_id, False),)
  assert result.criterion == match(3, criterion_id=criterion_id).criterion
  rendered = result.render()
  assert f'：{claim_id}；绑定未识别' in rendered and 'CUSTOM-REPLACEMENT-TEXT' not in rendered
  restored = ContextResult.from_json(result.export_json())
  assert restored == result and restored.render() == rendered


def test_entry_role_separates_premise_condition() -> None:
  premise = match(3)
  condition = match(3, criterion_id=PIANYIN)
  with pytest.raises(ValueError, match='Premise criterion cannot carry condition references'):
    replace(premise, related=condition.related)
  with pytest.raises(ValueError, match='Condition criterion cannot carry premise matches'):
    replace(condition, entries=premise.entries[:1])
