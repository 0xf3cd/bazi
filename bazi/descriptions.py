# Copyright (C) 2024 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Legacy description interfaces projected from the editable knowledge corpus.
从可编辑知识语料投影的旧描述接口；good/bad 字段仅用于兼容。'''

from dataclasses import dataclass
from enum import Enum
from typing import Final, TypeAlias, TypedDict

from .common import check_declared_types, frozendict
from .defines import Shishen, Tiangan
from .knowledge import KnowledgeBase, KnowledgeEntry, LegacyDescription


_KNOWLEDGE_BASE: Final[KnowledgeBase] = KnowledgeBase.load()


class ShishenDescription(TypedDict):
  general:        list[str]
  in_good_status: list[str]
  in_bad_status:  list[str]
  relationship:   list[str]


class TianganDescription(TypedDict):
  general:     list[str]
  personality: list[str]


class DescriptionSource(Enum):
  '''A stable source-witness identifier. / 稳定的来源见证标识。'''

  EDITORIAL                                = 'editorial'
  YUANHAI_ZIPING_RELATIONS                 = 'yuanhai_ziping_relations'
  YUANHAI_ZIPING_STEM_TABLE                = 'yuanhai_ziping_stem_table'
  YUANHAI_ZIPING_STEM_SYMBOLS_P69          = 'yuanhai_ziping_stem_symbols_p69'
  YUANHAI_ZIPING_STEM_SYMBOLS_P70          = 'yuanhai_ziping_stem_symbols_p70'
  MINGLI_TANYUAN_STEM_BASICS               = 'mingli_tanyuan_stem_basics'
  MINGLI_TANYUAN_SHISHEN_DEFINITIONS       = 'mingli_tanyuan_shishen_definitions'


class DescriptionLineage(Enum):
  '''An independent textual lineage. / 独立的文本谱系。'''

  EDITORIAL        = 'editorial'
  YUANHAI_ZIPING   = 'yuanhai_ziping'
  MINGLI_TANYUAN   = 'mingli_tanyuan'


class DescriptionTextLayer(Enum):
  '''The textual layer represented by a source witness. / 来源见证对应的文本层。'''

  EDITORIAL  = 'editorial'
  BAIWEN     = 'baiwen'


class DescriptionOutput(Enum):
  '''The output policy of a description claim. / 语料断言的输出策略。'''

  DEFAULT        = 'default'
  REFERENCE_ONLY = 'reference_only'


class DescriptionCondition(Enum):
  '''A prerequisite that enum lookup cannot evaluate. / 枚举查表无法判断的适用条件。'''

  CHART_CONTEXT_REQUIRED = 'chart_context_required'


@dataclass(frozen=True)
class DescriptionSourceRecord:
  '''A fixed witness and its evidentiary boundary. / 固定底本见证及其证据边界。'''

  work:         str
  attribution:  str
  edition:      str
  locator:      str
  url:          str
  text_layer:   DescriptionTextLayer
  lineage:      DescriptionLineage
  excerpt:      str
  supports:     str
  limitations:  str

  def __post_init__(self) -> None:
    check_declared_types(self)


@dataclass(frozen=True)
class DescriptionClaim:
  '''A description claim with source state and output policy. / 带来源状态与输出策略的语料断言。'''

  claim_id:    str
  text:        str
  sources:     tuple[DescriptionSource, ...]
  attribution: str
  conditions:  tuple[DescriptionCondition, ...]
  output:      DescriptionOutput

  def __post_init__(self) -> None:
    for value in (self.claim_id, self.text, self.attribution):
      if not isinstance(value, str):
        raise TypeError(f'Expected str, got {type(value)}')
    if not isinstance(self.output, DescriptionOutput):
      raise TypeError(f'Expected DescriptionOutput, got {type(self.output)}')
    for values, member_type in (
      (self.sources, DescriptionSource),
      (self.conditions, DescriptionCondition),
    ):
      if not isinstance(values, tuple):
        raise TypeError(f'Expected tuple, got {type(values)}')
      for member in values:
        if not isinstance(member, member_type):
          raise TypeError(f'Expected {member_type.__name__}, got {type(member)}')


'''Description fields mapped to immutable selected claims.
描述字段与所选不可变语料条目的映射。'''
DescriptionClaims: TypeAlias = frozendict[str, tuple[DescriptionClaim, ...]]


class _ShishenCorpusDescription(TypedDict):
  general:        list[DescriptionClaim]
  in_good_status: list[DescriptionClaim]
  in_bad_status:  list[DescriptionClaim]
  relationship:   list[DescriptionClaim]


class _TianganCorpusDescription(TypedDict):
  general:     list[DescriptionClaim]
  personality: list[DescriptionClaim]


def _legacy_claim(entry: KnowledgeEntry, legacy: LegacyDescription) -> DescriptionClaim:
  return DescriptionClaim(
    claim_id=entry.claim_id,
    text=entry.text,
    sources=tuple(DescriptionSource(source) for source in entry.sources),
    attribution=entry.attribution,
    conditions=tuple(DescriptionCondition(condition) for condition in legacy.conditions),
    output=DescriptionOutput(entry.output),
  )


def _legacy_items(object_id: str, field: str) -> list[DescriptionClaim]:
  positioned = [
    (legacy.ordinal, _legacy_claim(entry, legacy))
    for entry in _KNOWLEDGE_BASE.entries.values()
    if (legacy := entry.legacy) is not None and legacy.object_id == object_id and legacy.field == field
  ]
  return [claim for _, claim in sorted(positioned, key=lambda item: item[0])]


_DESCRIPTION_SOURCES: Final[frozendict[DescriptionSource, DescriptionSourceRecord]] = frozendict({
  source: DescriptionSourceRecord(
    work=record.work,
    attribution=record.attribution,
    edition=record.edition,
    locator=record.locator,
    url=record.url,
    text_layer=DescriptionTextLayer(record.text_layer),
    lineage=DescriptionLineage(record.lineage),
    excerpt=record.excerpt,
    supports=record.supports,
    limitations=record.limitations,
  )
  for source in DescriptionSource
  for record in (_KNOWLEDGE_BASE.sources[source.value],)
})

_SHISHEN_DESCRIPTION_CORPUS: Final[frozendict[Shishen, _ShishenCorpusDescription]] = frozendict({
  shishen: {
    'general':        _legacy_items('shishen.' + shishen.name.lower(), 'general'),
    'in_good_status': _legacy_items('shishen.' + shishen.name.lower(), 'in_good_status'),
    'in_bad_status':  _legacy_items('shishen.' + shishen.name.lower(), 'in_bad_status'),
    'relationship':   _legacy_items('shishen.' + shishen.name.lower(), 'relationship'),
  }
  for shishen in Shishen
})

_TIANGAN_DESCRIPTION_CORPUS: Final[frozendict[Tiangan, _TianganCorpusDescription]] = frozendict({
  tg: {
    'general':     _legacy_items('tiangan.' + tg.name.lower(), 'general'),
    'personality': _legacy_items('tiangan.' + tg.name.lower(), 'personality'),
  }
  for tg in Tiangan
})


def _selected_items(
  items: list[DescriptionClaim],
  include_reference_only: bool,
) -> list[DescriptionClaim]:
  assert isinstance(include_reference_only, bool)
  return [
    item for item in items
    if (
      include_reference_only
      or (item.output is DescriptionOutput.DEFAULT and not item.conditions)
    )
  ]


def _project_texts(
  items: list[DescriptionClaim],
  include_reference_only: bool,
) -> list[str]:
  return [
    item.text
    for item in _selected_items(items, include_reference_only)
  ]


def _project_shishen_description(
  description: _ShishenCorpusDescription,
  include_reference_only: bool,
) -> ShishenDescription:
  return {
    'general':        _project_texts(description['general'], include_reference_only),
    'in_good_status': _project_texts(description['in_good_status'], include_reference_only),
    'in_bad_status':  _project_texts(description['in_bad_status'], include_reference_only),
    'relationship':   _project_texts(description['relationship'], include_reference_only),
  }


def _project_tiangan_description(
  description: _TianganCorpusDescription,
  include_reference_only: bool,
) -> TianganDescription:
  return {
    'general':     _project_texts(description['general'], include_reference_only),
    'personality': _project_texts(description['personality'], include_reference_only),
  }


def _complete_shishen_description(shishen: Shishen) -> ShishenDescription:
  assert isinstance(shishen, Shishen)
  return _project_shishen_description(_SHISHEN_DESCRIPTION_CORPUS[shishen], include_reference_only=True)


def _complete_tiangan_description(tg: Tiangan) -> TianganDescription:
  assert isinstance(tg, Tiangan)
  return _project_tiangan_description(_TIANGAN_DESCRIPTION_CORPUS[tg], include_reference_only=True)


def _selected_claims(
  items: list[DescriptionClaim],
  include_reference_only: bool,
) -> tuple[DescriptionClaim, ...]:
  return tuple(_selected_items(items, include_reference_only))


def _shishen_claims(shishen: Shishen, include_reference_only: bool) -> DescriptionClaims:
  assert isinstance(shishen, Shishen)
  description = _SHISHEN_DESCRIPTION_CORPUS[shishen]
  return frozendict({
    'general':        _selected_claims(description['general'], include_reference_only),
    'in_good_status': _selected_claims(description['in_good_status'], include_reference_only),
    'in_bad_status':  _selected_claims(description['in_bad_status'], include_reference_only),
    'relationship':   _selected_claims(description['relationship'], include_reference_only),
  })


def _tiangan_claims(tg: Tiangan, include_reference_only: bool) -> DescriptionClaims:
  assert isinstance(tg, Tiangan)
  description = _TIANGAN_DESCRIPTION_CORPUS[tg]
  return frozendict({
    'general':     _selected_claims(description['general'], include_reference_only),
    'personality': _selected_claims(description['personality'], include_reference_only),
  })


def _source_record(source: DescriptionSource) -> DescriptionSourceRecord:
  assert isinstance(source, DescriptionSource)
  return _DESCRIPTION_SOURCES[source]


# The legacy tables keep mutable inner lists; Interpreter returns defensive copies.
# 旧表保留可变的内层列表；Interpreter 返回防御性副本。
SHISHEN_DESCRIPTIONS: Final[frozendict[Shishen, ShishenDescription]] = frozendict({
  shishen: _project_shishen_description(description, include_reference_only=False)
  for shishen, description in _SHISHEN_DESCRIPTION_CORPUS.items()
})

TIANGAN_DESCRIPTIONS: Final[frozendict[Tiangan, TianganDescription]] = frozendict({
  tg: _project_tiangan_description(description, include_reference_only=False)
  for tg, description in _TIANGAN_DESCRIPTION_CORPUS.items()
})
