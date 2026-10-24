# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from bazi.bazi_chart import BaziChart
from bazi._validation import _json_loads, _json_dumps
from bazi.common import frozendict
from bazi.context_matching import ContextResult
from bazi.knowledge import KnowledgeBase
from bazi.record_migration import migrate_chart_json, migrate_knowledge_json, migrate_context_json


def _records() -> dict[str, Any]:
  records: dict[str, Any] = json.loads((Path(__file__).parent / 'data/v230_records.json').read_text(encoding='utf-8'))
  return records


@pytest.mark.parametrize('text', ['中文', '😀', json.loads('"\\ud83d\\ude00"'), '\\ud800'])
def test_supported_text_roundtrips(text: str) -> None:
  for key, migrate in [
    ('knowledge', migrate_knowledge_json),
    ('context', migrate_context_json),
  ]:
    record = _records()[key]
    knowledge = record if key == 'knowledge' else record['knowledge']
    knowledge['entries'][0]['text'] = text
    migrated = migrate(json.dumps(record))
    restored = KnowledgeBase.from_json(migrated.json_text) if key == 'knowledge' else ContextResult.from_json(migrated.json_text)
    assert text in restored.export_json()
    restored.export_json().encode('utf-8')
  assert _json_loads(_json_dumps({'文字': [text]})) == {'文字': [text]}


@pytest.mark.parametrize('bad', [chr(0xd800), chr(0xdfff)])
@pytest.mark.parametrize('surface', ['text', 'nested_value', 'nested_key', 'observation_key'])
def test_surrogates_rejected_at_record_boundaries(bad: str, surface: str) -> None:
  for kind, migrate, restore in [
    ('knowledge', migrate_knowledge_json, KnowledgeBase.from_json),
    ('context', migrate_context_json, ContextResult.from_json),
  ]:
    if kind == 'knowledge' and surface != 'text':
      continue
    record = _records()[kind]
    if surface == 'text':
      knowledge = record if kind == 'knowledge' else record['knowledge']
      knowledge['entries'][0]['text'] = bad
    elif surface == 'observation_key':
      record['criterion']['observations'] = {bad: True}
    else:
      record['input']['config']['school']['extension'] = {bad: 'ok'} if surface == 'nested_key' else {'nested': [bad]}
    text = json.dumps(record)
    with pytest.raises(ValueError, match='surrogate'):
      migrate(text)
    if kind == 'knowledge':
      record['schema_version'] = 2
    else:
      record['record_version'] = 5
      record['knowledge']['schema_version'] = 2
    with pytest.raises(ValueError, match='surrogate'):
      restore(json.dumps(record))


def test_programmatic_render_export_utf8_guards() -> None:
  knowledge = KnowledgeBase.from_json(migrate_knowledge_json(json.dumps(_records()['knowledge'])).json_text)
  entry = next(iter(knowledge.entries.values()))
  bad = replace(entry, text=entry.text + '\ud800')
  bad_knowledge = KnowledgeBase(
    tuple(knowledge.objects.values()), tuple(knowledge.contexts.values()), tuple(knowledge.sources.values()),
    tuple(bad if value.claim_id == entry.claim_id else value for value in knowledge.entries.values()),
  )
  assert bad.legacy is not None
  object_id = bad.legacy.object_id
  for operation in [bad_knowledge.export_json, lambda: bad_knowledge.render(bad),
                    lambda: bad_knowledge.render_subject(object_id, include_reference_only=True),
                    lambda: knowledge.render(entry, premise_verdict='\ud800')]:
    with pytest.raises(ValueError, match='surrogate'):
      operation()
  # Queries are not text output boundaries and keep their earlier acceptance rules.
  assert knowledge.find_objects('\ud800') == ()
  assert knowledge.search('\ud800') == ()
  for kind in ('context', 'relationship'):
    result = ContextResult.from_json(migrate_context_json(json.dumps(_records()[kind])).json_text)
    result = replace(result, criterion=replace(result.criterion, observations=frozendict({'\ud800': True})))
    for operation in (result.export_json, result.render):
      with pytest.raises(ValueError, match='surrogate'):
        operation()


def test_nesting_follows_runtime_json_capacity() -> None:
  depth = 2000
  text = '[' * depth + '0' + ']' * depth
  for load in (KnowledgeBase.from_json, ContextResult.from_json, migrate_knowledge_json, migrate_context_json):
    try:
      load(text)
    except ValueError as error:
      assert 'depth' in str(error)
    except TypeError as error:
      assert 'Expected JSON object' in str(error)
    else:
      pytest.fail('A non-object record was accepted')
  record = _records()['context']
  record['record_version'] = 5
  record['knowledge']['schema_version'] = 2
  record['input']['config']['school']['extension'] = '__depth_marker__'
  text = json.dumps(record).replace('"__depth_marker__"', '[' * depth + '0' + ']' * depth)
  try:
    restored = ContextResult.from_json(text)
  except ValueError as error:
    assert 'depth' in str(error)
  else:
    extension = json.loads(restored.input_json)['config']['school']['extension']
    for _ in range(depth):
      assert isinstance(extension, list) and len(extension) == 1
      extension = extension[0]
    assert extension == 0
  nested: object = 0
  for _ in range(depth):
    nested = [nested]
  try:
    encoded = _json_dumps(nested)
  except ValueError as error:
    assert 'serialization depth' in str(error)
  else:
    assert encoded == json.dumps(nested, ensure_ascii=False, indent=2) + '\n'


@pytest.mark.parametrize('kind', ['knowledge', 'context'])
@pytest.mark.parametrize('error_type,expected_error', [(RecursionError, ValueError), (RuntimeError, RuntimeError)])
def test_import_checks_record_encoding(
  kind: str, error_type: type[Exception], expected_error: type[Exception], monkeypatch: pytest.MonkeyPatch,
) -> None:
  record = _records()[kind]
  if kind == 'knowledge':
    record['schema_version'] = 2
  else:
    record['record_version'] = 5
    record['knowledge']['schema_version'] = 2
  text = json.dumps(record)
  restore = KnowledgeBase.from_json if kind == 'knowledge' else ContextResult.from_json
  restore(text)
  original_dumps = json.dumps

  def encoding(value: object, *args: Any, **kwargs: Any) -> str:
    if kwargs.get('indent') == 2:
      raise error_type('injected output boundary')
    return original_dumps(value, *args, **kwargs)

  monkeypatch.setattr(json, 'dumps', encoding)
  message = 'serialization depth' if error_type is RecursionError else 'injected output boundary'
  with pytest.raises(expected_error, match=message):
    restore(text)


def test_recursion_conversion_does_not_hide_bugs(monkeypatch: pytest.MonkeyPatch) -> None:
  def recursion(*args: object, **kwargs: object) -> Any:
    raise RecursionError('injected parser limit')
  monkeypatch.setattr(json, 'loads', recursion)
  with pytest.raises(ValueError, match='parsing depth'):
    _json_loads('{}')

  def bug(*args: object, **kwargs: object) -> Any:
    raise RuntimeError('programming error')
  monkeypatch.setattr(json, 'loads', bug)
  with pytest.raises(RuntimeError, match='programming error'):
    _json_loads('{}')


@pytest.mark.parametrize('load,next_step', [
  (KnowledgeBase.from_json, 'Use migrate_knowledge_json'),
  (ContextResult.from_json, 'Use migrate_context_json'),
  (migrate_knowledge_json, 'Preserve the original knowledge source'),
  (migrate_context_json, 'Preserve the original context record'),
])
def test_parse_error_keeps_source_and_position(load: Any, next_step: str) -> None:
  text = '\n{"field":'
  with pytest.raises(json.JSONDecodeError) as original:
    json.loads(text)
  with pytest.raises(json.JSONDecodeError) as raised:
    load(text)
  assert raised.value.doc == original.value.doc == text
  assert raised.value.pos == original.value.pos
  assert raised.value.msg.startswith(original.value.msg)
  assert next_step in raised.value.msg


@pytest.mark.parametrize('kind', ['chart', 'location_chart'])
@pytest.mark.parametrize('surface', ['gender', 'derived', 'key'])
def test_chart_bad_text_has_displayable_error(kind: str, surface: str) -> None:
  record = _records()[kind]
  record['schema_version'] = 1
  BaziChart.from_json(record)
  if surface == 'gender':
    record['gender'] = '\ud800'
  elif surface == 'derived':
    record['pillars']['day'] = '\ud800'
  else:
    record['\ud800'] = 'extra'
  for load in (BaziChart.from_json, migrate_chart_json):
    with pytest.raises(ValueError) as raised:
      load(record)
    str(raised.value).encode('utf-8')


@pytest.mark.parametrize('version', [None, 4, 5.0, '5'])
def test_record_version_error_reports_value(version: object) -> None:
  record = _records()['context']
  record['record_version'] = 5
  record['knowledge']['schema_version'] = 2
  ContextResult.from_json(json.dumps(record))
  record['record_version'] = version
  with pytest.raises(ValueError) as raised:
    ContextResult.from_json(json.dumps(record))
  assert str(raised.value).startswith(f'Unsupported record version: {version!r}')


@pytest.mark.parametrize('kind', ['chart', 'knowledge'])
def test_string_version_error_keeps_quotes(kind: str) -> None:
  record = _records()[kind]
  record['schema_version'] = 1 if kind == 'chart' else 2
  if kind == 'chart':
    BaziChart.from_json(record)
  else:
    KnowledgeBase.from_json(json.dumps(record))
  record['schema_version'] = str(record['schema_version'])
  with pytest.raises(ValueError) as raised:
    if kind == 'chart':
      BaziChart.from_json(record)
    else:
      KnowledgeBase.from_json(json.dumps(record))
  assert f'version: {record["schema_version"]!r}.' in str(raised.value)
