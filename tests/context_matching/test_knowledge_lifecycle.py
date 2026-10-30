# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import fields
from pathlib import Path
from typing import Any

import pytest

from bazi.knowledge import (
  DEFAULT_SOURCE_PATH, KnowledgeBase, KnowledgeObject, KnowledgeContext, KnowledgeSource, KnowledgeEntry, KnowledgeRole, KnowledgeRelation, LegacyDescription,
)

from matching_samples import GUANSHA, FEMALE, LEGAL, RELATIONSHIP, match, load_knowledge


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
      assert entry.show_by_default is False and entry.viewpoint == '仓内原作'
      assert all(limit in knowledge.render(entry) for limit in knowledge.contexts[context_id].limits)
    assert match(criterion_id=criterion).reference_ids == keys
    assert match(criterion_id=criterion).criterion.status == 'SATISFIED'


def test_shared_lifecycle_keeps_loaded_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  source = tmp_path / 'knowledge.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  knowledge = KnowledgeBase.load(source)
  count = 0
  original_init = KnowledgeBase.__init__

  def counted(self: KnowledgeBase, *args: Any, **kwargs: Any) -> None:
    nonlocal count
    count += 1
    original_init(self, *args, **kwargs)

  monkeypatch.setattr(KnowledgeBase, '__init__', counted)
  results = tuple(match(day, knowledge=knowledge) for day in (1, 3, 5))
  for result in results:
    assert result.knowledge is knowledge
    rendered = result.render()
    assert result.render() == rendered
  assert count == 0

  result = results[1]
  rendered, fingerprint = result.render(), hash(result)
  changed = json.loads(json.dumps(data))
  next(entry for entry in changed['entries'] if entry['claim_id'] == LEGAL[0])['text'] = 'External source changed.'
  source.write_text(json.dumps(changed, ensure_ascii=False), encoding='utf-8')
  assert result.render() == rendered and hash(result) == fingerprint
  source.unlink()
  assert result.render() == rendered and hash(result) == fingerprint and count == 0
  equal = match(3, knowledge=knowledge)
  assert equal == result and hash(equal) == hash(result)
  assert len({result, equal}) == 1 and {result: 'value'}[equal] == 'value'
  assert equal.render() == rendered and count == 0


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
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  source = tmp_path / 'knowledge.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  monkeypatch.setattr('bazi.knowledge.DEFAULT_SOURCE_PATH', source)
  shared = KnowledgeBase.load()
  original_text = shared.entry(LEGAL[0]).text
  original_results = (match(), match(knowledge=shared))
  snapshots = tuple((result, result.render(), hash(result)) for result in original_results)

  next(entry for entry in data['entries'] if entry['claim_id'] == LEGAL[0])['text'] = 'Updated reference text.'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  default = match()
  assert default.knowledge.entry(LEGAL[0]).text == 'Updated reference text.'
  assert default.criterion.status == 'SATISFIED'
  assert default.reference_ids == LEGAL
  assert default.knowledge.entry(LEGAL[0]).show_by_default is False

  still_shared = match(knowledge=shared)
  assert still_shared.knowledge is shared and still_shared.knowledge.entry(LEGAL[0]).text == original_text
  assert still_shared == original_results[1]
  reloaded = KnowledgeBase.load()
  assert match(knowledge=reloaded) == default
  assert reloaded is not shared
  for result, rendered, fingerprint in snapshots:
    assert result.knowledge.entry(LEGAL[0]).text == original_text
    assert result.render() == rendered and hash(result) == fingerprint


@pytest.mark.parametrize('missing', [False, True])
def test_source_errors_keep_shared_results(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: bool) -> None:
  source = tmp_path / 'knowledge.json'
  source.write_text(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'), encoding='utf-8')
  monkeypatch.setattr('bazi.knowledge.DEFAULT_SOURCE_PATH', source)
  shared = KnowledgeBase.load()
  result = match()
  rendered, fingerprint = result.render(), hash(result)
  if missing:
    source.unlink()
  else:
    source.write_text('{', encoding='utf-8')
  with pytest.raises(FileNotFoundError if missing else json.JSONDecodeError):
    match()
  assert match(knowledge=shared) == result
  assert result.render() == rendered and hash(result) == fingerprint


def test_value_fields_participate_in_comparison() -> None:
  for record_type in (KnowledgeObject, KnowledgeContext, KnowledgeSource, KnowledgeEntry, KnowledgeRole, KnowledgeRelation, LegacyDescription):
    assert all(field.compare for field in fields(record_type)), record_type.__name__


@pytest.mark.parametrize('registry', ['objects', 'contexts', 'sources', 'entries'])
def test_value_equality_keeps_content_order(registry: str, tmp_path: Path) -> None:
  knowledge = KnowledgeBase.load()
  result = match(knowledge=knowledge)
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  data[registry].reverse()
  reordered = load_knowledge(data, tmp_path)
  other = match(knowledge=reordered)
  assert knowledge != reordered and reordered != knowledge and knowledge != object()
  assert result != other and len({result, other}) == 2
  assert tuple(getattr(other.knowledge, registry)) == tuple(reversed(tuple(getattr(knowledge, registry))))

  changed = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  changed['entries'][0]['text'] += ' Extra recorded text.'
  changed_result = match(knowledge=load_knowledge(changed, tmp_path))
  assert changed_result != result and len({result, changed_result}) == 2


@pytest.mark.parametrize('registry, field', [
  ('objects', 'name'), ('contexts', 'label'), ('sources', 'excerpt'), ('entries', 'viewpoint'),
])
def test_value_equality_keeps_nontext_fields(registry: str, field: str, tmp_path: Path) -> None:
  knowledge = KnowledgeBase.load()
  result = match(knowledge=knowledge)
  changed = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  changed[registry][0][field] += ' changed'
  other_knowledge = load_knowledge(changed, tmp_path)
  other = match(knowledge=other_knowledge)
  assert knowledge != other_knowledge and result != other
  assert len({result, other}) == 2
