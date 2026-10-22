# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import fields
from pathlib import Path
from typing import Any

import pytest

from bazi.context_matching import ContextResult, EntryMatch
from bazi.knowledge import (
  KnowledgeBase, KnowledgeObject, KnowledgeContext, KnowledgeSource, KnowledgeEntry, KnowledgeRole, KnowledgeRelation, LegacyDescription,
)

from matching_samples import GUANSHA, FEMALE, LEGAL, RELATIONSHIP, match


def test_legacy_oracle_matches_frozen_hash() -> None:
  import hashlib
  fixture = Path(__file__).parents[1] / 'data' / 'description_legacy_baseline.json'
  assert hashlib.sha256(fixture.read_bytes().replace(b'\r\n', b'\n')).hexdigest() == '6e50cf38d5b9a74a6f2a7ba2b3502b8dad818955a67ac6530e97f8d768f6b774'


def test_corpus_organizes_reference_entries() -> None:
  knowledge = KnowledgeBase.load()
  assert len(knowledge.entries) == 312 and len(knowledge.sources) == 23 and len(knowledge.query()) == 19
  for criterion, keys, context_id in ((GUANSHA, LEGAL, 'editorial.guansha_coexistence'), (FEMALE, RELATIONSHIP, 'editorial.guansha_coexistence_female')):
    assert tuple(e.claim_id for e in knowledge.query(context_id=context_id, include_reference_only=True)) == keys
    assert knowledge.query(context_id=context_id) == ()
    for key in keys:
      entry = knowledge.entry(key)
      assert entry.applicability == 'described' and entry.sources == ('editorial',)
      assert entry.output == 'reference_only' and entry.viewpoint == '仓内原作'
      assert all(limit in knowledge.render(entry) for limit in knowledge.contexts[context_id].limits)
    assert all(m.status == 'SATISFIED' for m in match(criterion_id=criterion).entries)


def test_shared_lifecycle_and_record_recovery(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
  data = json.loads(KnowledgeBase.load().export_json())
  source = tmp_path / 'knowledge.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  knowledge = KnowledgeBase.load(source)
  count = 0
  original_init = KnowledgeBase.__init__

  def counted(self: KnowledgeBase, *args: Any, **kwargs: Any) -> None:
    nonlocal count
    count += 1
    original_init(self, *args, **kwargs)

  def forbidden(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError('Unexpected whole-corpus JSON round trip')

  monkeypatch.setattr(KnowledgeBase, '__init__', counted)
  monkeypatch.setattr(KnowledgeBase, 'from_json', forbidden)
  monkeypatch.setattr(KnowledgeBase, 'export_json', forbidden)
  results = tuple(match(day, knowledge=knowledge) for day in (1, 3, 5))
  for result in results:
    assert result.knowledge is knowledge
    rendered = result.render()
    assert result.render() == rendered
    assert json.loads(result.export_json())['knowledge'] == data
  assert count == 0

  result = results[1]
  rendered, exported = result.render(), result.export_json()
  changed = json.loads(json.dumps(data))
  next(entry for entry in changed['entries'] if entry['claim_id'] == LEGAL[0])['text'] = 'External source changed.'
  source.write_text(json.dumps(changed, ensure_ascii=False), encoding='utf-8')
  assert result.render() == rendered and result.export_json() == exported
  source.unlink()
  assert result.render() == rendered and result.export_json() == exported
  restored = ContextResult.from_json(exported)
  assert count == 1
  assert restored.knowledge is not knowledge and restored.knowledge == knowledge
  assert restored == result and hash(restored) == hash(result)
  assert len({result, restored}) == 1 and {result: 'record'}[restored] == 'record'
  assert restored.render() == rendered and restored.export_json() == exported and count == 1


def test_default_knowledge_loads_independently(monkeypatch: pytest.MonkeyPatch) -> None:
  original_load = KnowledgeBase.load
  calls = 0

  def counted(*args: Any, **kwargs: Any) -> KnowledgeBase:
    nonlocal calls
    calls += 1
    return original_load(*args, **kwargs)

  monkeypatch.setattr(KnowledgeBase, 'load', counted)
  left, right = match(), match()
  assert calls == 2
  assert left.knowledge is not right.knowledge
  assert left.knowledge == right.knowledge and left == right


def test_reload_snapshot_after_source_update(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
  data = json.loads(KnowledgeBase.load().export_json())
  source = tmp_path / 'knowledge.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  monkeypatch.setattr('bazi.knowledge.DEFAULT_SOURCE_PATH', source)
  shared = KnowledgeBase.load()
  original_text = shared.entry(LEGAL[0]).text
  original_results = (match(), match(knowledge=shared))
  snapshots = tuple((result, result.render(), result.export_json()) for result in original_results)

  next(entry for entry in data['entries'] if entry['claim_id'] == LEGAL[0])['text'] = 'Updated reference text.'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  default = match()
  assert default.knowledge.entry(LEGAL[0]).text == 'Updated reference text.'
  assert default.criterion.status == 'SATISFIED'
  assert default.entries[0] == EntryMatch(LEGAL[0], 'UNKNOWN', 'binding_unrecognized')
  assert default.knowledge.entry(LEGAL[0]).output == 'reference_only'

  still_shared = match(knowledge=shared)
  assert still_shared.knowledge is shared and still_shared.knowledge.entry(LEGAL[0]).text == original_text
  assert still_shared == original_results[1]
  reloaded = KnowledgeBase.load()
  assert match(knowledge=reloaded) == default
  assert reloaded is not shared
  for result, rendered, exported in snapshots:
    assert result.knowledge.entry(LEGAL[0]).text == original_text
    assert result.render() == rendered and result.export_json() == exported
    assert ContextResult.from_json(exported) == result


@pytest.mark.parametrize('missing', [False, True])
def test_source_errors_keep_shared_results(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: bool) -> None:
  source = tmp_path / 'knowledge.json'
  source.write_text(KnowledgeBase.load().export_json(), encoding='utf-8')
  monkeypatch.setattr('bazi.knowledge.DEFAULT_SOURCE_PATH', source)
  shared = KnowledgeBase.load()
  result = match()
  rendered, exported = result.render(), result.export_json()
  if missing:
    source.unlink()
  else:
    source.write_text('{', encoding='utf-8')
  with pytest.raises(FileNotFoundError if missing else json.JSONDecodeError):
    match()
  assert match(knowledge=shared) == result
  assert result.render() == rendered and result.export_json() == exported
  assert ContextResult.from_json(exported) == result


def test_value_fields_participate_in_comparison() -> None:
  for record_type in (KnowledgeObject, KnowledgeContext, KnowledgeSource, KnowledgeEntry, KnowledgeRole, KnowledgeRelation, LegacyDescription):
    assert all(field.compare for field in fields(record_type)), record_type.__name__


@pytest.mark.parametrize('registry', ['objects', 'contexts', 'sources', 'entries'])
def test_record_equality_keeps_content_order(registry: str) -> None:
  knowledge = KnowledgeBase.load()
  result = match(knowledge=knowledge)
  data = json.loads(knowledge.export_json())
  data[registry].reverse()
  reordered = KnowledgeBase.from_json(json.dumps(data, ensure_ascii=False))
  other = match(knowledge=reordered)
  assert knowledge != reordered and reordered != knowledge and knowledge != object()
  assert result != other and len({result, other}) == 2
  assert json.loads(other.export_json())['knowledge'][registry] == data[registry]

  changed = json.loads(knowledge.export_json())
  changed['entries'][0]['text'] += ' Extra recorded text.'
  changed_result = match(knowledge=KnowledgeBase.from_json(json.dumps(changed, ensure_ascii=False)))
  assert changed_result != result and len({result, changed_result}) == 2


@pytest.mark.parametrize('registry, field', [
  ('objects', 'name'), ('contexts', 'label'), ('sources', 'excerpt'), ('entries', 'viewpoint'),
])
def test_record_equality_keeps_nontext_fields(registry: str, field: str) -> None:
  knowledge = KnowledgeBase.load()
  result = match(knowledge=knowledge)
  changed = json.loads(knowledge.export_json())
  changed[registry][0][field] += ' changed'
  other_knowledge = KnowledgeBase.from_json(json.dumps(changed, ensure_ascii=False))
  other = match(knowledge=other_knowledge)
  assert knowledge != other_knowledge and result != other
  assert len({result, other}) == 2
