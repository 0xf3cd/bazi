# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Editable interpretation knowledge.
可编辑的解释知识。'''

import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Final, Literal, TypeVar, get_args, get_origin

from .common import frozendict


'''Knowledge organization state, not a chart verdict. / 知识整理状态，不是命盘判别结果。'''
Applicability = Literal['unconditional', 'described', 'unresolved']

'''A claim's source state. / 条目的来源状态。'''
SourceState = Literal['witnessed', 'editorial', 'unverified', 'repository_attributed']

'''Presentation eligibility. / 输出资格。'''
OutputPolicy = Literal['default', 'reference_only']

_T = TypeVar('_T')
_APPLICABILITY: Final = get_args(Applicability)
_SOURCE_STATES: Final = get_args(SourceState)
_OUTPUTS: Final = get_args(OutputPolicy)


def _text(value: object, *, empty: bool = False) -> None:
  if not isinstance(value, str):
    raise TypeError(f'Expected str, got {type(value)}')
  if not empty and not value.strip():
    raise ValueError('Expected non-empty text')


def _choice(value: object, choices: tuple[str, ...]) -> None:
  _text(value)
  if value not in choices:
    raise ValueError(f'Unsupported value: {value}')


def _tuple(value: object, member_type: type[_T]) -> None:
  if not isinstance(value, tuple):
    raise TypeError(f'Expected tuple, got {type(value)}')
  for member in value:
    if not isinstance(member, member_type):
      raise TypeError(f'Expected {member_type.__name__}, got {type(member)}')
    if isinstance(member, str):
      _text(member)


@dataclass(frozen=True)
class KnowledgeObject:
  '''A named discussion object.
  具名讨论对象。'''

  object_id: str
  kind:      str
  name:      str

  def __post_init__(self) -> None:
    _text(self.object_id)
    _choice(self.kind, ('tiangan', 'shishen', 'wuxing', 'shensha', 'concept'))
    _text(self.name)


@dataclass(frozen=True)
class KnowledgeRole:
  '''A named role bound to a discussion object. / 绑定讨论对象的具名角色。'''

  name:      str
  object_id: str

  def __post_init__(self) -> None:
    _text(self.name)
    _text(self.object_id)


@dataclass(frozen=True)
class KnowledgeRelation:
  '''A directed textual claim between roles, not a computed relation.
  角色之间有方向的文字陈述，不表示已计算的命盘关系。'''

  from_role: str
  to_role:   str
  text:      str

  def __post_init__(self) -> None:
    for value in (self.from_role, self.to_role, self.text):
      _text(value)


@dataclass(frozen=True)
class KnowledgeContext:
  '''A named lookup context with time scope and limits.
  带时间语境与限度的具名查阅情境。'''

  context_id: str
  label:      str
  time_scope: str
  limits:     tuple[str, ...]

  def __post_init__(self) -> None:
    for value in (self.context_id, self.label, self.time_scope):
      _text(value)
    _tuple(self.limits, str)


@dataclass(frozen=True)
class KnowledgeSource:
  '''A source witness with attribution and evidentiary boundaries.
  带署名与证据边界的来源见证。'''

  source_id:   str
  work:        str
  attribution: str
  edition:     str
  locator:     str
  url:         str
  text_layer:  str
  lineage:     str
  excerpt:     str
  supports:    str
  limitations: str
  state:       SourceState

  def __post_init__(self) -> None:
    for value in (
      self.source_id, self.work, self.attribution, self.edition, self.locator,
      self.url, self.lineage, self.excerpt, self.supports, self.limitations,
    ):
      _text(value)
    _choice(self.text_layer, ('editorial', 'baiwen', 'zhushi'))
    _choice(self.state, _SOURCE_STATES)


@dataclass(frozen=True)
class LegacyDescription:
  '''The exact placement and condition metadata of an old description.
  旧描述的字段、顺序及条件元数据。'''

  object_id:     str
  field:         str
  ordinal:       int
  conditions:    tuple[str, ...]
  field_premise: str

  def __post_init__(self) -> None:
    _text(self.object_id)
    _text(self.field)
    if type(self.ordinal) is not int:
      raise TypeError(f'Expected int, got {type(self.ordinal)}')
    if self.ordinal < 0:
      raise ValueError(f'Unsupported ordinal: {self.ordinal}')
    _tuple(self.conditions, str)
    for condition in self.conditions:
      _choice(condition, ('chart_context_required',))
    _text(self.field_premise, empty=True)


@dataclass(frozen=True)
class KnowledgeEntry:
  '''An interpretation with independently recorded source, premise and output states.
  分别记录来源、前提及输出状态的解释条目。'''

  claim_id:      str
  text:          str
  roles:         tuple[KnowledgeRole, ...]
  relations:     tuple[KnowledgeRelation, ...]
  topics:        tuple[str, ...]
  applicability: Applicability
  premise:       str
  contexts:      tuple[str, ...]
  sources:       tuple[str, ...]
  source_state:  SourceState
  attribution:   str
  viewpoint:     str
  exceptions:    tuple[str, ...]
  limits:        tuple[str, ...]
  output:        OutputPolicy
  legacy:        LegacyDescription | None

  def __post_init__(self) -> None:
    for value in (self.claim_id, self.text, self.attribution, self.viewpoint):
      _text(value)
    _text(self.premise, empty=True)
    _tuple(self.roles, KnowledgeRole)
    _tuple(self.relations, KnowledgeRelation)
    for values in (self.topics, self.contexts, self.sources, self.exceptions, self.limits):
      _tuple(values, str)
    _choice(self.applicability, _APPLICABILITY)
    _choice(self.source_state, _SOURCE_STATES)
    _choice(self.output, _OUTPUTS)
    if self.legacy is not None and not isinstance(self.legacy, LegacyDescription):
      raise TypeError(f'Expected LegacyDescription | None, got {type(self.legacy)}')
    if not self.roles or not self.topics:
      raise ValueError('Entries require roles and topics')
    names = tuple(role.name for role in self.roles)
    if len(set(names)) != len(names):
      raise ValueError(f'Duplicate role: {self.claim_id}')
    for relation in self.relations:
      if relation.from_role not in names or relation.to_role not in names:
        raise ValueError(f'Unknown relation role: {self.claim_id}')
    for values in (self.topics, self.contexts, self.sources):
      if len(set(values)) != len(values):
        raise ValueError(f'Duplicate reference: {self.claim_id}')
    if self.applicability == 'unconditional' and (self.premise or self.contexts):
      raise ValueError(f'Unconditional entry has a premise: {self.claim_id}')
    if self.applicability == 'described' and not self.premise.strip():
      raise ValueError(f'Described entry needs premise text: {self.claim_id}')
    if self.legacy is not None and self.legacy.conditions and self.applicability == 'unconditional':
      raise ValueError(f'Unconditional entry has legacy conditions: {self.claim_id}')
    if self.legacy is not None and self.legacy.field_premise and self.applicability == 'unconditional':
      raise ValueError(f'Unconditional entry has a legacy field premise: {self.claim_id}')
    if (self.source_state == 'unverified') != (not self.sources):
      raise ValueError(f'Source state and witnesses disagree: {self.claim_id}')
    if self.output == 'default' and (
      self.applicability != 'unconditional' or self.source_state != 'witnessed'
    ):
      raise ValueError(f'Ineligible default entry: {self.claim_id}')


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
  result: dict[str, object] = {}
  for key, value in pairs:
    if key in result:
      raise ValueError(f'Duplicate JSON key: {key}')
    result[key] = value
  return result


def _array(value: object) -> list[Any]:
  if not isinstance(value, list):
    raise TypeError(f'Expected JSON array, got {type(value)}')
  return value


def _mapping(value: object, keys: tuple[str, ...]) -> dict[str, Any]:
  if not isinstance(value, dict):
    raise TypeError(f'Expected JSON object, got {type(value)}')
  if set(value) != set(keys):
    raise ValueError(f'JSON fields differ: {set(value) ^ set(keys)}')
  return value


def _decode(record_type: type[_T], value: object) -> _T:
  attributes = fields(record_type) # type: ignore[arg-type] # Only the dataclasses above reach this helper.
  data = _mapping(value, tuple(field.name for field in attributes))
  kwargs: dict[str, Any] = dict(data)
  for field in attributes:
    if get_origin(field.type) is tuple:
      member_type = get_args(field.type)[0]
      kwargs[field.name] = tuple(
        _decode(member_type, member) if isinstance(member_type, type) and is_dataclass(member_type) else member
        for member in _array(data[field.name])
      )
  if record_type is KnowledgeEntry and data['legacy'] is not None:
    kwargs['legacy'] = _decode(LegacyDescription, data['legacy'])
  return record_type(**kwargs)


def _registry(values: tuple[_T, ...], key: str) -> frozendict[str, _T]:
  result: dict[str, _T] = {}
  for value in values:
    identifier: str = getattr(value, key)
    if identifier in result:
      raise ValueError(f'Duplicate identifier: {identifier}')
    result[identifier] = value
  return frozendict(result)


class KnowledgeBase:
  '''Validate, index, query and export immutable interpretation records.
  校验、索引、查询并导出不可变解释条目。

  Note:
  - JSON is the editing source; indexes and exports are derived.
  - JSON 为编辑来源；索引与导出由它生成。
  '''

  def __init__(
    self,
    objects: tuple[KnowledgeObject, ...],
    contexts: tuple[KnowledgeContext, ...],
    sources: tuple[KnowledgeSource, ...],
    entries: tuple[KnowledgeEntry, ...],
  ) -> None:
    for values, member_type in (
      (objects, KnowledgeObject), (contexts, KnowledgeContext),
      (sources, KnowledgeSource), (entries, KnowledgeEntry),
    ):
      _tuple(values, member_type)
    self._objects: Final = _registry(objects, 'object_id')
    self._contexts: Final = _registry(contexts, 'context_id')
    self._sources: Final = _registry(sources, 'source_id')
    self._entries: Final = _registry(entries, 'claim_id')

    placements: set[tuple[str, str, int]] = set()
    index: dict[tuple[str, str], set[str]] = {}
    for entry in entries:
      for object_id in (role.object_id for role in entry.roles):
        if object_id not in self.objects:
          raise ValueError(f'Unknown object: {object_id} ({entry.claim_id})')
      for dimension, registry, references in (
        ('context', self.contexts, entry.contexts), ('source', self.sources, entry.sources),
      ):
        for reference in references:
          if reference not in registry:
            raise ValueError(f'Unknown {dimension}: {reference} ({entry.claim_id})')
      if any(self.sources[source].state != entry.source_state for source in entry.sources):
        raise ValueError(f'Witness state differs: {entry.claim_id}')
      if entry.output == 'default' and len({self.sources[source].lineage for source in entry.sources}) < 2:
        raise ValueError(f'Default entry needs independent lineages: {entry.claim_id}')
      if entry.legacy is not None:
        legacy = entry.legacy
        if legacy.object_id not in {role.object_id for role in entry.roles}:
          raise ValueError(f'Legacy object is missing: {entry.claim_id}')
        kind = self.objects[legacy.object_id].kind
        allowed = (
          ('general', 'in_good_status', 'in_bad_status', 'relationship') if kind == 'shishen'
          else ('general', 'personality') if kind == 'tiangan' else ()
        )
        if legacy.field not in allowed:
          raise ValueError(f'Unsupported legacy field: {legacy.field}')
        placement = (legacy.object_id, legacy.field, legacy.ordinal)
        if placement in placements:
          raise ValueError(f'Duplicate legacy placement: {placement}')
        placements.add(placement)

      for dimension, indexed_values in (
        ('object_id', tuple(role.object_id for role in entry.roles)),
        ('context_id', entry.contexts), ('source_id', entry.sources), ('topic', entry.topics),
        ('viewpoint', (entry.viewpoint,)), ('applicability', (entry.applicability,)),
        ('time_scope', tuple(self.contexts[context].time_scope for context in entry.contexts)),
      ):
        for value in indexed_values:
          index.setdefault((dimension, value), set()).add(entry.claim_id)
    self._index: Final = frozendict({key: frozenset(ids) for key, ids in index.items()})

  @property
  def objects(self) -> frozendict[str, KnowledgeObject]:
    return self._objects

  @property
  def contexts(self) -> frozendict[str, KnowledgeContext]:
    return self._contexts

  @property
  def sources(self) -> frozendict[str, KnowledgeSource]:
    return self._sources

  @property
  def entries(self) -> frozendict[str, KnowledgeEntry]:
    return self._entries

  @classmethod
  def from_json(cls, text: str) -> 'KnowledgeBase':
    '''Load strict JSON, rejecting duplicate keys and dangling references.
    加载严格 JSON，拒绝重复键、错误字段与断引用。

    Args:
    - text: (str) UTF-8 JSON text. / UTF-8 JSON 文字。
    Returns:
    - (KnowledgeBase) The validated knowledge base. / 校验后的知识库。
    '''
    _text(text)
    data = _mapping(
      json.loads(text, object_pairs_hook=_pairs),
      ('schema_version', 'objects', 'contexts', 'sources', 'entries'),
    )
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
      raise ValueError(f'Unsupported schema version: {data["schema_version"]}')
    return cls(
      tuple(_decode(KnowledgeObject, item) for item in _array(data['objects'])),
      tuple(_decode(KnowledgeContext, item) for item in _array(data['contexts'])),
      tuple(_decode(KnowledgeSource, item) for item in _array(data['sources'])),
      tuple(_decode(KnowledgeEntry, item) for item in _array(data['entries'])),
    )

  @classmethod
  def load(cls, path: Path | None = None) -> 'KnowledgeBase':
    '''Read an editing source, or the bundled corpus when no path is given.
    读取指定编辑来源；未给路径时读取随库分发的语料。
    '''
    if path is not None and not isinstance(path, Path):
      raise TypeError(f'Expected Path | None, got {type(path)}')
    source = Path(__file__).with_name('knowledge_data.json') if path is None else path
    return cls.from_json(source.read_text(encoding='utf-8'))

  def entry(self, claim_id: str) -> KnowledgeEntry:
    '''Resolve a stable entry ID. / 按稳定标识查阅条目。'''
    _text(claim_id)
    if claim_id not in self.entries:
      raise ValueError(f'Unknown claim ID: {claim_id}')
    return self.entries[claim_id]

  def query(
    self,
    *,
    object_id: str | None = None,
    context_id: str | None = None,
    topic: str | None = None,
    source_id: str | None = None,
    viewpoint: str | None = None,
    applicability: Applicability | None = None,
    time_scope: str | None = None,
    include_reference_only: bool = False,
  ) -> tuple[KnowledgeEntry, ...]:
    '''Intersect lookup filters, preserving corpus order and output eligibility.
    按查阅条件取交集，保留语料顺序及输出资格。

    Note:
    - Object lookup includes every bound role. Unknown filters fail explicitly.
    - 对象查询包含所有绑定角色；未知标识明确报错。
    Returns:
    - (tuple[KnowledgeEntry, ...]) Immutable matching entries. / 命中的不可变条目。
    '''
    if not isinstance(include_reference_only, bool):
      raise TypeError(f'Expected bool, got {type(include_reference_only)}')
    filters = {
      'object_id': object_id, 'context_id': context_id, 'topic': topic, 'source_id': source_id,
      'viewpoint': viewpoint, 'applicability': applicability, 'time_scope': time_scope,
    }
    known = {
      'object_id': set(self.objects), 'context_id': set(self.contexts), 'source_id': set(self.sources),
      'applicability': set(_APPLICABILITY),
      'time_scope': {context.time_scope for context in self.contexts.values()},
    }
    candidates = frozenset(self.entries)
    for dimension, value in filters.items():
      if value is None:
        continue
      _text(value)
      accepted = known.get(dimension, {key[1] for key in self._index if key[0] == dimension})
      if value not in accepted:
        raise ValueError(f'Unknown {dimension}: {value}')
      candidates &= self._index.get((dimension, value), frozenset())
    return tuple(
      entry for entry in self.entries.values()
      if entry.claim_id in candidates and (include_reference_only or entry.output == 'default')
    )

  def export_json(self, entries: tuple[KnowledgeEntry, ...] | None = None) -> str:
    '''Export a reloadable corpus or selection with all registries preserved.
    导出可重载的完整语料或所选条目，保留全部对象、情境及来源注册表。
    '''
    selected = tuple(self.entries.values()) if entries is None else entries
    _tuple(selected, KnowledgeEntry)
    ids: set[str] = set()
    for entry in selected:
      if self.entries.get(entry.claim_id) != entry:
        raise ValueError(f'Foreign entry: {entry.claim_id}')
      if entry.claim_id in ids:
        raise ValueError(f'Duplicate selection: {entry.claim_id}')
      ids.add(entry.claim_id)
    data = {
      'schema_version': 1,
      'objects': [asdict(value) for value in self.objects.values()],
      'contexts': [asdict(value) for value in self.contexts.values()],
      'sources': [asdict(value) for value in self.sources.values()],
      'entries': [asdict(value) for value in selected],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'

  def render(
    self,
    entry: KnowledgeEntry,
    *,
    show_sources: bool = True,
    manual_context: bool = False,
  ) -> str:
    '''Display text, premises and limits; source details are optional.
    展示原文、前提与限度；可选择显示来源详情。
    '''
    return self._render(entry, show_sources=show_sources, manual_context=manual_context)

  def _render(
    self,
    entry: KnowledgeEntry,
    *,
    show_sources: bool = True,
    manual_context: bool = False,
    premise_verdict: str | None = None,
  ) -> str:
    '''Render an entry, optionally annotating a verdict supplied by the caller.
    展示条目，可附调用方提供的前提判别；本方法不求值前提。'''
    assert premise_verdict is None or isinstance(premise_verdict, str)
    if not isinstance(entry, KnowledgeEntry):
      raise TypeError(f'Expected KnowledgeEntry, got {type(entry)}')
    for flag in (show_sources, manual_context):
      if not isinstance(flag, bool):
        raise TypeError(f'Expected bool, got {type(flag)}')
    if self.entries.get(entry.claim_id) != entry:
      raise ValueError(f'Foreign entry: {entry.claim_id}')

    notes: list[str] = []
    if entry.output == 'reference_only':
      notes.append('仅供参考')
    if entry.source_state == 'unverified':
      notes.append('来源尚未核实')
    if entry.applicability == 'unresolved':
      notes.append('前提待梳理')
    if premise_verdict is not None:
      notes.extend((f'输出资格：{entry.output}', f'前提判别：{premise_verdict}'))
    elif manual_context:
      notes.append('人工给定情境；命盘适用性未判断')
    elif entry.applicability != 'unconditional':
      notes.append('命盘适用性未判断')
    lines = [entry.text + ('【' + '；'.join(notes) + '】' if notes else '')]
    if entry.premise:
      lines.append(f'前提：{entry.premise}')
    for context_id in entry.contexts:
      context = self.contexts[context_id]
      lines.append(f'情境：{context.context_id}；{context.time_scope}；{context.label}')
      lines.extend('情境限度：' + limit for limit in context.limits)
    lines.extend('例外：' + exception for exception in entry.exceptions)
    lines.extend('限度：' + limit for limit in entry.limits)
    if entry.legacy is not None and entry.legacy.field_premise:
      lines.append(f'旧栏目前提（待梳理；未作为判据）：{entry.legacy.field_premise}')

    if show_sources:
      lines.extend((
        f'条目：{entry.claim_id}；署名：{entry.attribution}',
        '角色：' + '；'.join(f'{role.name}={self.objects[role.object_id].name}' for role in entry.roles),
        f'主题：{"／".join(entry.topics)}；口径：{entry.viewpoint}；来源状态：{entry.source_state}',
      ))
      lines.extend(f'文字关系：{relation.from_role}→{relation.to_role}；{relation.text}' for relation in entry.relations)
      for source_id in entry.sources:
        source = self.sources[source_id]
        lines.extend((
          f'来源：{source.source_id}；{source.work}；{source.attribution}；{source.edition}；{source.locator}',
          source.url,
          f'文本层：{source.text_layer}；谱系：{source.lineage}；见证状态：{source.state}',
          f'引文／记录：{source.excerpt}',
          f'支持范围：{source.supports}',
          f'局限：{source.limitations}',
        ))
    return '\n'.join(lines)
