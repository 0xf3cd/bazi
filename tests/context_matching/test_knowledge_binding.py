# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import asdict
from typing import Any

import pytest

from bazi.bazi import Bazi
from bazi.context_matching import ContextProfile, ContextResult, EntryMatch, evaluate_context
from bazi.knowledge import KnowledgeBase
from bazi.transit_chart import TransitChart

from matching_samples import GUANSHA, FEMALE, LEGAL, chart, match


def test_reference_eligibility_and_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
  knowledge = KnowledgeBase.load()
  default = evaluate_context(chart(), criterion_id=GUANSHA, profile=ContextProfile('natal'))
  assert default.criterion.status == 'SATISFIED' and default.entries == ()
  assert '前提满足只表示本范围内的原作使用条件满足，不表示现实事件成立。' in default.render()
  assert len(knowledge.query()) == 19
  result = match()
  data = json.loads(result.export_json())
  assert 'stem_scope' not in data['profile']
  assert all('index' not in value for value in data['occurrences'])
  assert 'revision' not in data['criterion']
  assert data['knowledge'] == json.loads(knowledge.export_json())
  assert len(data['knowledge']['entries']) == 302
  assert data['criterion']['observations']['observed_coexistence'] is True
  rendered = result.render()
  assert '来源状态：editorial' in rendered and '见证状态：editorial' in rendered
  source = knowledge.sources['editorial']
  for text in asdict(source).values():
    assert text in rendered
  for key in LEGAL:
    entry = knowledge.entry(key)
    assert entry.text in rendered and '也许' in entry.text
    assert entry.premise in rendered and entry.viewpoint in rendered
    assert entry.source_state == 'editorial' and entry.output == 'reference_only'
    assert '命盘适用性未判断' in knowledge.render(entry)
    assert '命盘适用性未判断' not in rendered
    for context_id in entry.contexts:
      assert all(limit in rendered for limit in knowledge.contexts[context_id].limits)
  assert '可能会' in match(criterion_id=FEMALE).render()
  # Record restoration must not call a chart/transit constructor or evaluator.
  def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise RuntimeError('Unexpected recalculation')
  monkeypatch.setattr(Bazi, 'create', forbidden)
  monkeypatch.setattr(TransitChart, 'at_year', forbidden)
  restored = ContextResult.from_json(result.export_json())
  assert restored == result and restored.render() == rendered and restored.export_json() == result.export_json()


@pytest.mark.parametrize('day,status', [(3, 'SATISFIED'), (1, 'NOT_SATISFIED')])
def test_premise_annotations_are_evaluation_only(day: int, status: str) -> None:
  result = match(day)
  knowledge = result.knowledge
  text = result.render()
  assert len(result.entries) == 2
  for entry_match in result.entries:
    block = text.split(f'原作参考前提：{entry_match.claim_id}；', 1)[1].split('\n原作参考前提：', 1)[0]
    entry = knowledge.entry(entry_match.claim_id)
    assert f'输出资格：{entry.output}' in block and f'前提判别：{status}' in block
    assert '前提判别：' not in knowledge.render(entry)
    assert '输出资格：' not in knowledge.render(entry)


@pytest.mark.parametrize('separator', ['\n', '\r\n', '\r', '\u2028'])
def test_multiline_custom_text_keeps_one_copy(separator: str) -> None:
  claim_id = LEGAL[0]
  data = json.loads(KnowledgeBase.load().export_json())
  entry = next(e for e in data['entries'] if e['claim_id'] == claim_id)
  text = 'FIRST-TEXT-LINE' + separator + 'SECOND-TEXT-LINE'
  entry['text'] = text
  knowledge = KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))
  result = match(knowledge=knowledge)
  rendered = result.render()
  assert rendered.count(text) == 1 and rendered.count('SECOND-TEXT-LINE') == 1
  assert '命盘适用性未判断' not in rendered
  assert knowledge.render(knowledge.entry(claim_id)).count(text) == 1
  assert '命盘适用性未判断' in knowledge.render(knowledge.entry(claim_id))
  assert result.entries[0].reason == 'binding_unrecognized'
  assert all(value in rendered for value in asdict(knowledge.sources['editorial']).values())
  restored = ContextResult.from_json(result.export_json())
  assert restored == result and restored.render() == rendered


@pytest.mark.parametrize('dimension', ['text', 'premise', 'contexts', 'roles', 'viewpoint', 'source', 'context', 'object', 'qualification'])
def test_same_id_binding_is_not_authentication(dimension: str) -> None:
  data = json.loads(KnowledgeBase.load().export_json())
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
    entry.update(output='default', applicability='unconditional', premise='', contexts=[], source_state='witnessed', sources=['yuanhai_ziping_relations', 'mingli_tanyuan_shishen_definitions'])
  custom = KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))
  result = match(knowledge=custom)
  assert result.criterion.status == 'SATISFIED'
  assert result.entries[0] == EntryMatch(LEGAL[0], 'UNKNOWN', 'binding_unrecognized')
  assert json.loads(result.knowledge.export_json()) == data
  assert ContextResult.from_json(result.export_json()) == result
  if dimension == 'qualification':
    default = evaluate_context(chart(), criterion_id=GUANSHA, profile=ContextProfile('natal'), knowledge=custom)
    assert default.entries == (EntryMatch(LEGAL[0], 'UNKNOWN', 'binding_unrecognized'),)
    assert '输出资格：default' in default.render() and '前提判别：UNKNOWN' in default.render()


def test_custom_export_bindings_missing_entries() -> None:
  knowledge = KnowledgeBase.load()
  selection = knowledge.query(context_id='editorial.guansha_coexistence', include_reference_only=True)
  custom = KnowledgeBase.from_json(knowledge.export_json(selection))
  assert match(knowledge=custom).entries == match().entries
  assert match(knowledge=KnowledgeBase.from_json(knowledge.export_json(()))).entries == ()
