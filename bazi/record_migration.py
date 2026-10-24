# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''调用方主动执行的记录格式迁移；不写文件、不猜配置、不重新判别前提。'''

import base64
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

from .bazi_chart import BaziChart, _SCHEMA_VERSION as _CHART_VERSION
from .context_matching import ContextResult, _RECORD_VERSION
from .knowledge import KnowledgeBase, _SCHEMA_VERSION as _KNOWLEDGE_VERSION
from ._validation import _json_loads, _json_dumps, _record_errors


@dataclass(frozen=True)
class MigrationChange:
  '''一个已转换的版本字段；before 为 None 表示原命盘没有该字段。'''

  path:   str
  before: int | None
  after:  int
  reason: str


@dataclass(frozen=True)
class MigrationResult:
  '''迁移入口返回的新文本及不可变说明，不持有原输入。

  tool_version 只报告路径及文件哈希可核的分发元数据；无法核定时为 None。
  它不认证元数据真伪或历史执行。json_text 可用 UTF-8 保存，文件与原件由调用方管理。
  '''

  json_text:      str
  source_version: int | None
  target_version: int
  tool_version:   str | None
  changes:        tuple[MigrationChange, ...]


def _tool_version() -> str | None:
  try:
    distribution = metadata.distribution('bazi')
  except metadata.PackageNotFoundError:
    return None
  actual = Path(__file__).resolve()
  for item in distribution.files or ():
    if str(item) != 'bazi/record_migration.py':
      continue
    if Path(str(distribution.locate_file(item))).resolve() != actual:
      return None
    digest = item.hash
    if digest is None or digest.mode != 'sha256':
      return None
    try:
      content_hash = base64.urlsafe_b64encode(hashlib.sha256(actual.read_bytes()).digest()).rstrip(b'=').decode('ascii')
    except OSError:
      return None
    return distribution.version if digest.value == content_hash else None
  return None


def _version(value: object, allowed: tuple[int, ...], label: str) -> int:
  if type(value) is not int or value not in allowed:
    raise ValueError(f'Unsupported {label}: {value!r}; check its producing version')
  return value


@_record_errors('Preserve the original chart; missing configuration requires an explicit school choice and reconstruction.')
def migrate_chart_json(record: Mapping[str, object]) -> MigrationResult:
  '''将完整无版本命盘迁为 schema 1，或校验已有 schema 1；接收映射，不接收文本。

  仍用当前实现重建并核对派生值，不冻结旧算法。缺 kongwang_anchor 时拒绝，不补 DAY。
  TypeError 表示类型错误，ValueError 表示不支持的版本、结构、值或不一致；不修改原映射。
  '''
  if not isinstance(record, Mapping):
    raise TypeError(f'Expected Mapping, got {type(record)}')
  source = None if 'schema_version' not in record else _version(record['schema_version'], (_CHART_VERSION,), 'chart schema version')
  data = dict(record)
  data['schema_version'] = _CHART_VERSION
  chart = BaziChart._from_data(data)
  changes = () if source is not None else (
    MigrationChange('schema_version', None, _CHART_VERSION, '完整无版本命盘新增格式版本；输入、配置与派生值不变。'),
  )
  return MigrationResult(_json_dumps(chart.json), source, _CHART_VERSION, _tool_version(), changes)


@_record_errors('Preserve the original knowledge source; migration does not repair text, fields or references.')
def migrate_knowledge_json(text: str) -> MigrationResult:
  '''将合法 schema 1 知识文本迁为 schema 2，或校验 schema 2；不替换原语料。

  字段、引用、状态和文本须满足目标合同；拒绝孤立代理项与无法按记录格式保存的嵌套。
  TypeError 表示类型错误，ValueError 表示版本、结构或值不支持。函数不写文件。
  '''
  data = _json_loads(text)
  if not isinstance(data, dict):
    raise TypeError(f'Expected JSON object, got {type(data)}')
  source = _version(data.get('schema_version'), (1, _KNOWLEDGE_VERSION), 'knowledge schema version')
  data['schema_version'] = _KNOWLEDGE_VERSION
  output = _json_dumps(data)
  KnowledgeBase._from_data(data)
  changes = () if source == _KNOWLEDGE_VERSION else (
    MigrationChange('schema_version', source, _KNOWLEDGE_VERSION, '知识格式增加 UTF-8 保存边界；不改语料。'),
  )
  return MigrationResult(output, source, _KNOWLEDGE_VERSION, _tool_version(), changes)


@_record_errors('Preserve the original context record; missing configuration requires an explicit choice and reevaluation.')
def migrate_context_json(text: str) -> MigrationResult:
  '''将完整 record 4／内嵌知识 schema 1 迁为 record 5／schema 2，或校验已有目标格式。

  不改变输入拼写、观察、证据、绑定或原判别，不重新求值。混版、record 1–3、缺配置及失效定义拒绝；
  须重新求值时保留旧结果。TypeError 表示类型错误，ValueError 表示版本、结构或值不支持。
  '''
  data = _json_loads(text)
  if not isinstance(data, dict):
    raise TypeError(f'Expected JSON object, got {type(data)}')
  source = _version(data.get('record_version'), (4, _RECORD_VERSION), 'record version')
  if 'knowledge' not in data:
    raise ValueError('Missing context field: knowledge')
  knowledge: Any = data['knowledge']
  if not isinstance(knowledge, dict):
    raise TypeError(f'Expected JSON object at knowledge, got {type(knowledge)}')
  expected = 1 if source == 4 else _KNOWLEDGE_VERSION
  _version(knowledge.get('schema_version'), (expected,), 'nested knowledge schema version')
  data['record_version'] = _RECORD_VERSION
  knowledge['schema_version'] = _KNOWLEDGE_VERSION
  output = _json_dumps(data)
  ContextResult._from_data(data)
  changes = () if source == _RECORD_VERSION else (
    MigrationChange('record_version', source, _RECORD_VERSION, '前提记录新增文本保存边界；保留原判别，不重新求值。'),
    MigrationChange('knowledge.schema_version', 1, _KNOWLEDGE_VERSION, '只迁移内嵌知识格式，不替换知识快照或绑定。'),
  )
  return MigrationResult(output, source, _RECORD_VERSION, _tool_version(), changes)
