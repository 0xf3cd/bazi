# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import replace
from typing import Any

import pytest

from bazi.bazi import Bazi
from bazi.context_matching import criterion
from bazi.knowledge import KnowledgeBase
from bazi.transit_chart import TransitChart

from matching_samples import LEGAL, GUANSHA, DING, PALACE, TOUGAN, match, rel_match


def test_references_keep_declaration_order() -> None:
  result = match()
  assert result.reference_ids == LEGAL == criterion(GUANSHA).claim_ids
  text = result.render()
  knowledge = KnowledgeBase.load()
  for claim_id in LEGAL:
    assert f'参考条目：{claim_id}' in text
    assert knowledge.entry(claim_id).text not in text
  assert '完整前提' in text and '不表示现实事件成立' in text


@pytest.mark.parametrize('criterion_id', [PALACE, TOUGAN])
def test_gender_gate_only_filters_references(criterion_id: str) -> None:
  male = rel_match(criterion_id=criterion_id, gender='male')
  female = rel_match(criterion_id=criterion_id, gender='female')
  assert male.reference_ids == criterion(criterion_id).claim_ids
  assert female.reference_ids == ()
  for result in (male, female):
    assert '局部条件' in result.render()
    assert '不表示原文完整条件已满足' in result.render()


def test_reference_render_does_not_recalculate(monkeypatch: pytest.MonkeyPatch) -> None:
  result = match()
  rendered = result.render()
  def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise RuntimeError('Unexpected recalculation')
  monkeypatch.setattr(Bazi, 'create', forbidden)
  monkeypatch.setattr(TransitChart, 'at_year', forbidden)
  assert result.render() == rendered


@pytest.mark.parametrize('criterion_id,relation', [(GUANSHA, '完整前提'), (DING, '局部条件')])
@pytest.mark.optimized
def test_empty_ids_keep_premise_relation(criterion_id: str, relation: str) -> None:
  result = replace(match(criterion_id=criterion_id), reference_ids=())
  assert relation in result.render()
  assert '不表示现实事件成立' in result.render()
