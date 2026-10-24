# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import base64
import copy
import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import FrozenInstanceError
from importlib import metadata
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Any, cast

import pytest

from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextResult
from bazi.knowledge import KnowledgeBase
from bazi.record_migration import migrate_chart_json, migrate_knowledge_json, migrate_context_json
import bazi.record_migration as migration


def _records() -> dict[str, Any]:
  return cast(dict[str, Any], json.loads((Path(__file__).parent / 'data/v230_records.json').read_text(encoding='utf-8')))


def _readonly(value: Any) -> Any:
  return MappingProxyType({key: _readonly(item) for key, item in value.items()}) if isinstance(value, dict) else value


@pytest.mark.parametrize('kind', ['chart', 'location_chart', 'knowledge', 'context', 'relationship'])
def test_record_output_keeps_public_format(kind: str) -> None:
  record = _records()[kind]
  result = (
    migrate_chart_json(record) if kind in ('chart', 'location_chart') else
    migrate_knowledge_json(json.dumps(record)) if kind == 'knowledge' else
    migrate_context_json(json.dumps(record))
  )
  data = json.loads(result.json_text)
  expected = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
  assert result.json_text == expected
  if kind == 'knowledge':
    assert KnowledgeBase.from_json(result.json_text).export_json() == expected
  elif kind in ('context', 'relationship'):
    assert ContextResult.from_json(result.json_text).export_json() == expected


@pytest.mark.parametrize('version', [None, '9.8.7'])
def test_migration_reports_tool_version(version: str | None, monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(migration, '_tool_version', lambda: version)
  records = _records()
  results = (
    migrate_chart_json(records['chart']),
    migrate_chart_json(records['location_chart']),
    migrate_knowledge_json(json.dumps(records['knowledge'])),
    migrate_context_json(json.dumps(records['context'])),
    migrate_context_json(json.dumps(records['relationship'])),
  )
  assert all(result.tool_version == version for result in results)


@pytest.mark.parametrize('name', ['chart', 'location_chart'])
def test_chart_migration_keeps_original(name: str) -> None:
  record = _records()[name]
  before = copy.deepcopy(record)
  with pytest.raises(ValueError, match='migrate_chart_json'):
    BaziChart.from_json(record)
  result = migrate_chart_json(_readonly(record))
  data = json.loads(result.json_text)
  assert data == {**before, 'schema_version': 1}
  assert record == before
  assert result.source_version is None and result.target_version == 1
  assert [(change.path, change.before, change.after) for change in result.changes] == [('schema_version', None, 1)]
  assert all(change.reason for change in result.changes)
  assert BaziChart.from_json(data).json == data
  again = migrate_chart_json(data)
  assert again.source_version == again.target_version == 1 and again.changes == ()
  assert again.json_text == result.json_text
  record['gender'] = 'changed'
  assert json.loads(result.json_text) == data
  with pytest.raises(FrozenInstanceError):
    result.target_version = 99 # type: ignore[misc]
  with pytest.raises(FrozenInstanceError):
    result.changes[0].path = 'changed' # type: ignore[misc]


def test_knowledge_migration_preserves_snapshot() -> None:
  records = _records()
  assert records['source_sha'] == 'b40e89f41b077f4429a6fcd8a8a2a707c8a2e18d'
  record = records['knowledge']
  text = json.dumps(record, ensure_ascii=False)
  with pytest.raises(ValueError, match='migrate_knowledge_json'):
    KnowledgeBase.from_json(text)
  result = migrate_knowledge_json(text)
  assert result.source_version == 1 and result.target_version == 2
  assert json.loads(result.json_text) == {**record, 'schema_version': 2}
  assert len(KnowledgeBase.from_json(result.json_text).entries) == len(record['entries'])
  assert len(record['entries']) < len(KnowledgeBase.load().entries)
  assert [(change.path, change.before, change.after) for change in result.changes] == [('schema_version', 1, 2)]
  again = migrate_knowledge_json(result.json_text)
  assert again.changes == () and again.json_text == result.json_text
  assert text == json.dumps(record, ensure_ascii=False)


@pytest.mark.parametrize('kind', ['context', 'relationship'])
def test_context_migration_does_not_reevaluate(kind: str) -> None:
  record = _records()[kind]
  record['input']['config']['precision'] = 'D'
  record['input']['config']['school']['extension'] = {'文字': ['中文', '😀']}
  record['criterion']['observations'] = {'unregistered_observation': True}
  before = copy.deepcopy(record)
  text = json.dumps(record, ensure_ascii=False)
  with pytest.raises(ValueError, match='migrate_context_json'):
    ContextResult.from_json(text)
  result = migrate_context_json(text)
  expected = {**before, 'record_version': 5, 'knowledge': {**before['knowledge'], 'schema_version': 2}}
  assert json.loads(result.json_text) == expected
  assert record == before
  restored = ContextResult.from_json(result.json_text)
  assert json.loads(restored.export_json()) == expected
  assert restored.criterion.observations == {'unregistered_observation': True}
  assert result.source_version == 4 and result.target_version == 5
  assert [(change.path, change.before, change.after) for change in result.changes] == [
    ('record_version', 4, 5), ('knowledge.schema_version', 1, 2),
  ]
  again = migrate_context_json(result.json_text)
  assert again.source_version == again.target_version == 5 and again.changes == ()
  assert again.json_text == result.json_text


@pytest.mark.parametrize('version', [True, False, 0, 2, '1', None, 1.0])
def test_chart_migration_rejects_unknown_version(version: object) -> None:
  record = _records()['chart']
  record['schema_version'] = version
  with pytest.raises(ValueError, match='Unsupported chart schema version'):
    migrate_chart_json(record)


@pytest.mark.parametrize('version', [True, False, 0, 3, '1', None, 1.0])
def test_text_migration_rejects_unknown_version(version: object) -> None:
  for kind, key, migrate in (
    ('knowledge', 'schema_version', migrate_knowledge_json),
    ('context', 'record_version', migrate_context_json),
  ):
    record = _records()[kind]
    record[key] = version
    with pytest.raises(ValueError, match='Unsupported'):
      migrate(json.dumps(record))


@pytest.mark.parametrize('outer,inner', [(4, 2), (5, 1), (4, True), (5, 99)])
def test_migration_rejects_mixed_nested_versions(outer: int, inner: object) -> None:
  record = _records()['context']
  record['record_version'] = outer
  record['knowledge']['schema_version'] = inner
  with pytest.raises(ValueError, match='nested knowledge schema version'):
    migrate_context_json(json.dumps(record))


@pytest.mark.parametrize('version', [1, 2, 3])
def test_context_migration_rejects_old_versions(version: int) -> None:
  record = _records()['context']
  migrate_context_json(json.dumps(record))
  record['record_version'] = version
  with pytest.raises(ValueError, match='Unsupported record version'):
    migrate_context_json(json.dumps(record))


@pytest.mark.parametrize('outer', [4, 5])
@pytest.mark.parametrize('missing', [True, False])
def test_migration_requires_nested_version(outer: int, missing: bool) -> None:
  record = _records()['context']
  record['record_version'] = outer
  record['knowledge']['schema_version'] = 1 if outer == 4 else 2
  migrate_context_json(json.dumps(record))
  if missing:
    del record['knowledge']['schema_version']
  else:
    record['knowledge']['schema_version'] = None
  with pytest.raises(ValueError, match='nested knowledge schema version'):
    migrate_context_json(json.dumps(record))


def test_knowledge_migration_rejects_float_target() -> None:
  record = _records()['knowledge']
  record['schema_version'] = 2
  migrate_knowledge_json(json.dumps(record))
  record['schema_version'] = 2.0
  with pytest.raises(ValueError, match='Unsupported knowledge schema version'):
    migrate_knowledge_json(json.dumps(record))


def test_migration_validates_full_source_shape() -> None:
  chart = _records()['chart']
  chart['pillars']['day'] = '甲子'
  with pytest.raises(ValueError, match='Inconsistent value'):
    migrate_chart_json(chart)
  chart = _records()['chart']
  del chart['school']['kongwang_anchor']
  with pytest.raises(ValueError, match='explicit school choice'):
    migrate_chart_json(chart)
  context = _records()['context']
  context['criterion']['definition'] = '失效定义'
  with pytest.raises(ValueError, match='Unsupported criterion definition'):
    migrate_context_json(json.dumps(context))
  for kind, migrate in [('context', migrate_context_json), ('knowledge', migrate_knowledge_json)]:
    record = _records()[kind]
    record['extra'] = 'not a record field'
    with pytest.raises(ValueError, match='JSON fields differ'):
      migrate(json.dumps(record))
    with pytest.raises(ValueError, match='Duplicate JSON key'):
      migrate('{"schema_version":1,"schema_version":1}')
  context = _records()['context']
  del context['knowledge']
  with pytest.raises(ValueError, match='Missing context field'):
    migrate_context_json(json.dumps(context))
  context['knowledge'] = []
  with pytest.raises(TypeError, match='at knowledge'):
    migrate_context_json(json.dumps(context))


def test_migration_keeps_input_type_contracts() -> None:
  bad_values: tuple[object, ...] = (None, [], 1, 'json text')
  for value in bad_values:
    with pytest.raises(TypeError, match='Expected Mapping'):
      migrate_chart_json(cast(Mapping[str, object], value))
  for migrate in (migrate_knowledge_json, migrate_context_json):
    with pytest.raises(TypeError, match='Expected str'):
      migrate(cast(str, 1))
    with pytest.raises(TypeError, match='Expected JSON object'):
      migrate('[]')
    with pytest.raises(json.JSONDecodeError):
      migrate('{')


@pytest.mark.parametrize('kind', ['chart', 'knowledge', 'context'])
def test_errors_have_one_applicable_next_step(kind: str) -> None:
  record = _records()[kind]
  ordinary: Callable[[], object]
  if kind == 'chart':
    record['schema_version'] = 1
    BaziChart.from_json(record)
    record['pillars']['day'] = '甲子'
    ordinary = lambda: BaziChart.from_json(record)
    migrate = lambda: migrate_chart_json(record)
  elif kind == 'knowledge':
    record['schema_version'] = 2
    KnowledgeBase.from_json(json.dumps(record))
    record['sources'] = []
    ordinary = lambda: KnowledgeBase.from_json(json.dumps(record))
    migrate = lambda: migrate_knowledge_json(json.dumps(record))
  else:
    record['record_version'] = 5
    record['knowledge']['schema_version'] = 2
    ContextResult.from_json(json.dumps(record))
    record['criterion']['definition'] = '失效定义'
    ordinary = lambda: ContextResult.from_json(json.dumps(record))
    migrate = lambda: migrate_context_json(json.dumps(record))
  with pytest.raises(ValueError) as ordinary_error:
    ordinary()
  with pytest.raises(ValueError) as migration_error:
    migrate()
  assert str(ordinary_error.value).count('Preserve the original') == 1
  assert 'Use migrate_' in str(ordinary_error.value)
  assert str(migration_error.value).casefold().count('preserve the original') == 1
  assert 'Use migrate_' not in str(migration_error.value)
  assert str(ordinary_error.value).split('. Preserve', 1)[0] == str(migration_error.value).split('. Preserve', 1)[0]


@pytest.mark.parametrize('kind', ['chart', 'knowledge', 'context'])
def test_version_error_preserves_original_once(kind: str) -> None:
  record = _records()[kind]
  key = 'record_version' if kind == 'context' else 'schema_version'
  record[key] = 99
  migrate = migrate_knowledge_json if kind == 'knowledge' else migrate_context_json
  with pytest.raises(ValueError) as raised:
    if kind == 'chart':
      migrate_chart_json(record)
    else:
      migrate(json.dumps(record))
  message = str(raised.value)
  assert '99' in message and 'check its producing version' in message
  assert message.casefold().count('preserve the original') == 1


@pytest.mark.parametrize('case', ['missing', 'no_files', 'unlisted', 'wrong_path', 'no_hash', 'wrong_mode', 'changed', 'match', 'unreadable'])
def test_tool_version_requires_matching_record(case: str, monkeypatch: pytest.MonkeyPatch) -> None:
  actual = Path(migration.__file__).resolve()
  digest = base64.urlsafe_b64encode(hashlib.sha256(actual.read_bytes()).digest()).rstrip(b'=').decode('ascii')
  item = metadata.PackagePath('other.py' if case == 'unlisted' else 'bazi/record_migration.py')
  item.hash = None if case == 'no_hash' else metadata.FileHash(
    f'{"md5" if case == "wrong_mode" else "sha256"}={"wrong" if case == "changed" else digest}'
  )
  distribution = SimpleNamespace(
    files=None if case == 'no_files' else [item], version='9.8.7',
    locate_file=lambda _: actual.with_name('other.py') if case == 'wrong_path' else actual,
  )

  def installed(name: str) -> Any:
    assert name == 'bazi'
    if case == 'missing':
      raise metadata.PackageNotFoundError(name)
    return distribution

  monkeypatch.setattr(migration.metadata, 'distribution', installed)
  if case == 'unreadable':
    def unreadable(path: Path) -> bytes:
      raise OSError('unavailable')
    monkeypatch.setattr(Path, 'read_bytes', unreadable)
  assert migration._tool_version() == ('9.8.7' if case == 'match' else None)
