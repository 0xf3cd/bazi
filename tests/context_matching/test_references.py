# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pytest

from bazi.bazi import Bazi
from bazi.context_matching import NatalObservation, evaluate_context
from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase
from bazi.transit_chart import TransitChart

from matching_samples import GUANSHA, FEMALE, LEGAL, chart, match, load_knowledge


def test_references_keep_default_eligibility() -> None:
  knowledge = KnowledgeBase.load()
  default = evaluate_context(chart(), criterion_id=GUANSHA, observation=NatalObservation())
  assert default.criterion.status == 'SATISFIED' and default.reference_ids == ()
  assert '前提满足只表示本范围内的原作使用条件满足，不表示现实事件成立。' in default.render()
  assert len(knowledge.query()) == 19
  result = match()
  assert result.knowledge == knowledge and len(result.knowledge.entries) == 312
  assert result.criterion.observations['observed_coexistence'] is True
  rendered = result.render()
  assert '来源状态：editorial' in rendered and '见证状态：editorial' in rendered
  source = knowledge.sources['editorial']
  for text in asdict(source).values():
    assert text in rendered
  for key in LEGAL:
    entry = knowledge.entry(key)
    assert entry.text in rendered and '也许' in entry.text
    assert entry.premise in rendered and entry.viewpoint in rendered
    assert entry.source_state == 'editorial' and entry.show_by_default is False
    assert '命盘适用性未判断' in knowledge.render(entry)
    assert '命盘适用性未判断' not in rendered
    for context_id in entry.contexts:
      assert all(limit in rendered for limit in knowledge.contexts[context_id].limits)
  assert '可能会' in match(criterion_id=FEMALE).render()


def test_reference_render_does_not_recalculate(monkeypatch: pytest.MonkeyPatch) -> None:
  result = match()
  rendered = result.render()
  # Rendering must not call a chart/transit constructor or evaluator.
  def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise RuntimeError('Unexpected recalculation')
  monkeypatch.setattr(Bazi, 'create', forbidden)
  monkeypatch.setattr(TransitChart, 'at_year', forbidden)
  assert result.render() == rendered


@pytest.mark.parametrize('day,status', [(3, 'SATISFIED'), (1, 'NOT_SATISFIED')])
def test_premise_annotations_are_evaluation_only(day: int, status: str) -> None:
  result = match(day)
  knowledge = result.knowledge
  text = result.render()
  assert result.reference_ids == LEGAL
  for claim_id in result.reference_ids:
    block = text.split(f'原作参考前提：{claim_id}；', 1)[1].split('\n原作参考前提：', 1)[0]
    entry = knowledge.entry(claim_id)
    assert '默认展示：否' in block and f'前提判别：{status}' in block
    assert '前提判别：' not in knowledge.render(entry)
    assert '默认展示：' not in knowledge.render(entry)


@pytest.mark.parametrize('separator', ['\n', '\r\n', '\r', '\u2028'])
def test_multiline_custom_text_keeps_one_copy(separator: str) -> None:
  claim_id = LEGAL[0]
  text = 'FIRST-TEXT-LINE' + separator + 'SECOND-TEXT-LINE'
  original = KnowledgeBase.load()
  knowledge = KnowledgeBase(
    tuple(original.objects.values()), tuple(original.contexts.values()), tuple(original.sources.values()),
    tuple(replace(e, text=text) if e.claim_id == claim_id else e for e in original.entries.values()),
  )
  result = match(knowledge=knowledge)
  rendered = result.render()
  assert rendered.count(text) == 1 and rendered.count('SECOND-TEXT-LINE') == 1
  assert '命盘适用性未判断' not in rendered
  assert knowledge.render(knowledge.entry(claim_id)).count(text) == 1
  assert '命盘适用性未判断' in knowledge.render(knowledge.entry(claim_id))
  assert result.reference_ids == LEGAL and result.criterion.status == 'SATISFIED'
  assert all(value in rendered for value in asdict(knowledge.sources['editorial']).values())
  assert result.render() == rendered


@pytest.mark.parametrize('dimension', ['text', 'premise', 'contexts', 'roles', 'viewpoint', 'source', 'context', 'object', 'qualification'])
def test_same_id_edits_keep_criterion_and_ids(dimension: str, tmp_path: Path) -> None:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  entry = next(e for e in data['entries'] if e['claim_id'] == LEGAL[0])
  if dimension in ('text', 'premise', 'viewpoint'):
    entry[dimension] += '（编辑口径）'
  elif dimension == 'contexts':
    entry['contexts'] = ['legacy.chart_context']
  elif dimension == 'roles':
    entry['roles'][0]['name'] = '其他角色'
  elif dimension == 'source':
    data['sources'][0]['limitations'] = '不同支持边界。'
  elif dimension == 'context':
    next(c for c in data['contexts'] if c['context_id'] == entry['contexts'][0])['limits'] = ['另一个条件。']
  elif dimension == 'object':
    next(o for o in data['objects'] if o['object_id'] == 'shishen.zhengguan')['name'] = '同名异物'
  else:
    entry.update(show_by_default=True, applicability='unconditional', premise='', contexts=[], source_state='witnessed', sources=['yuanhai_ziping_relations', 'mingli_tanyuan_shishen_definitions'])
  custom = load_knowledge(data, tmp_path)
  result = match(knowledge=custom)
  assert result.criterion.status == 'SATISFIED'
  assert result.reference_ids == LEGAL
  assert result.criterion == match().criterion
  assert result.knowledge is custom
  if dimension == 'qualification':
    default = evaluate_context(chart(), criterion_id=GUANSHA, observation=NatalObservation(), knowledge=custom)
    assert default.reference_ids == (LEGAL[0],)
    assert '默认展示：是' in default.render() and '前提判别：SATISFIED' in default.render()


def test_custom_knowledge_missing_entries() -> None:
  knowledge = KnowledgeBase.load()
  selection = knowledge.query(context_id='editorial.guansha_coexistence', include_reference_only=True)
  custom = KnowledgeBase(tuple(knowledge.objects.values()), tuple(knowledge.contexts.values()), tuple(knowledge.sources.values()), selection)
  assert match(knowledge=custom).reference_ids == LEGAL
  empty = KnowledgeBase(tuple(knowledge.objects.values()), tuple(knowledge.contexts.values()), tuple(knowledge.sources.values()), ())
  assert match(knowledge=empty).reference_ids == ()


def test_claim_order_ignores_registry_order() -> None:
  knowledge = KnowledgeBase.load()
  reordered = KnowledgeBase(
    tuple(knowledge.objects.values()), tuple(knowledge.contexts.values()), tuple(knowledge.sources.values()),
    tuple(reversed(tuple(knowledge.entries.values()))),
  )
  assert match(knowledge=reordered).reference_ids == LEGAL
  single = KnowledgeBase(
    tuple(knowledge.objects.values()), tuple(knowledge.contexts.values()), tuple(knowledge.sources.values()),
    (knowledge.entry(LEGAL[1]),),
  )
  assert match(knowledge=single).reference_ids == (LEGAL[1],)
