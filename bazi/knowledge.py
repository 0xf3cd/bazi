# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''按讨论对象查阅知识条目及其出处；不判断命盘适用性。'''

from dataclasses import MISSING, dataclass, fields
from functools import cached_property
from pathlib import Path
from typing import Any, Final, Literal, TypeVar, get_args, get_origin

from .common import frozendict
from .defines import Shishen, Tiangan, Wuxing
from ._validation import _text, _choice, _tuple, _mapping, _json_loads


'''来源记录的核验状态；未填写不表示已核实，也不认证命盘前提或现实事件。'''
SourceState = Literal['witnessed', 'editorial', 'unverified', 'repository_attributed']

_T = TypeVar('_T')
_SCHEMA_VERSION: Final = 4
DEFAULT_SOURCE_PATH: Final[Path] = Path(__file__).with_name('knowledge_data.json')


@dataclass(frozen=True)
class KnowledgeObject:
  '''具名讨论对象；kind 区分同名的天干、十神、五行、神煞与概念。'''

  object_id: str
  kind:      str
  name:      str

  def __post_init__(self) -> None:
    _text(self.object_id)
    _choice(self.kind, ('tiangan', 'shishen', 'wuxing', 'shensha', 'concept'))
    _text(self.name)


@dataclass(frozen=True)
class KnowledgeSource:
  '''出处与支持范围；只有 source_id 和作品名 work 必填，摘录按原文保存。'''

  source_id:   str
  work:        str
  attribution: str = ''
  edition:     str = ''
  locator:     str = ''
  url:         str = ''
  excerpt:     str = ''
  supports:    str = ''
  limitations: str = ''
  state:       SourceState | None = None

  def __post_init__(self) -> None:
    _text(self.source_id)
    _text(self.work)
    for value in (
      self.attribution, self.edition, self.locator, self.url,
      self.excerpt, self.supports, self.limitations,
    ):
      _text(value, empty=True)
    if self.state is not None:
      _choice(self.state, get_args(SourceState))


@dataclass(frozen=True)
class KnowledgeEntry:
  '''讨论对象与正文，附有材料支持的前提、读法、署名和出处。

  只有 claim_id、objects、text 必填。前提为空只表示没有填写；
  多对象条目在每个对象下都能查到，对象顺序不表示主次，关系方向由正文表达。
  '''

  claim_id:    str
  objects:     tuple[str, ...]
  text:        str
  topics:      tuple[str, ...] = ()
  premise:     str = ''
  viewpoint:   str = ''
  attribution: str = ''
  sources:     tuple[str, ...] = ()
  limits:      tuple[str, ...] = ()

  def __post_init__(self) -> None:
    _text(self.claim_id)
    _text(self.text)
    for value in (self.premise, self.viewpoint, self.attribution):
      _text(value, empty=True)
    for values in (self.objects, self.topics, self.sources, self.limits):
      _tuple(values, str)
    if not self.objects:
      raise ValueError('Entries require discussion objects')
    for values in (self.objects, self.topics, self.sources):
      if len(set(values)) != len(values):
        raise ValueError(f'Duplicate reference: {self.claim_id}')


def _array(value: object) -> list[Any]:
  if not isinstance(value, list):
    raise TypeError(f'Expected JSON array, got {type(value)}')
  return value


def _decode(record_type: type[_T], value: object) -> _T:
  attributes = fields(record_type) # type: ignore[arg-type] # 仅接收上方 dataclass 类型。
  if not isinstance(value, dict):
    raise TypeError(f'Expected JSON object, got {type(value)}')
  allowed = {field.name for field in attributes}
  required = {field.name for field in attributes if field.default is MISSING}
  if not required <= value.keys() or not value.keys() <= allowed:
    raise ValueError(f'JSON fields differ: {(required - value.keys()) | (value.keys() - allowed)}')
  kwargs = dict(value)
  for field in attributes:
    if field.name in kwargs and get_origin(field.type) is tuple:
      kwargs[field.name] = tuple(_array(kwargs[field.name]))
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
  '''加载、查询并渲染不可变知识条目。

  Note:
  - JSON 是编辑源；加载只校验结构与引用，不要求独立来源数量，不认定条目适用于某盘。
  - 对象、来源、条目的内容与顺序参与相等和哈希。来源注册表可以包含尚未引用的记录。
  - 原创署名与文献引用分别填写；没有引用不表示断言为假，署名也不等于已核定的古籍见证。
  '''

  def __init__(
    self,
    objects: tuple[KnowledgeObject, ...],
    sources: tuple[KnowledgeSource, ...],
    entries: tuple[KnowledgeEntry, ...],
  ) -> None:
    for values, member_type in (
      (objects, KnowledgeObject), (sources, KnowledgeSource), (entries, KnowledgeEntry),
    ):
      _tuple(values, member_type)
    self._objects: Final = _registry(objects, 'object_id')
    self._sources: Final = _registry(sources, 'source_id')
    self._entries: Final = _registry(entries, 'claim_id')

    index: dict[tuple[str, str], set[str]] = {}
    for entry in entries:
      for dimension, registry, references in (
        ('object', self.objects, entry.objects), ('source', self.sources, entry.sources),
      ):
        for reference in references:
          if reference not in registry:
            raise ValueError(f'Unknown {dimension}: {reference} ({entry.claim_id})')
      for dimension, indexed_values in (
        ('object_id', entry.objects), ('source_id', entry.sources),
        ('topic', entry.topics), ('viewpoint', (entry.viewpoint,) if entry.viewpoint else ()),
      ):
        for value in indexed_values:
          index.setdefault((dimension, value), set()).add(entry.claim_id)
    self._index: Final = frozendict({key: frozenset(ids) for key, ids in index.items()})

  @cached_property
  def _value(self) -> tuple[
    tuple[KnowledgeObject, ...], tuple[KnowledgeSource, ...], tuple[KnowledgeEntry, ...],
  ]:
    return tuple(self.objects.values()), tuple(self.sources.values()), tuple(self.entries.values())

  def __eq__(self, other: object) -> bool:
    return isinstance(other, KnowledgeBase) and self._value == other._value

  def __hash__(self) -> int:
    return hash(self._value)

  @property
  def objects(self) -> frozendict[str, KnowledgeObject]:
    return self._objects

  @property
  def sources(self) -> frozendict[str, KnowledgeSource]:
    return self._sources

  @property
  def entries(self) -> frozendict[str, KnowledgeEntry]:
    return self._entries

  @classmethod
  def _from_data(cls, value: Any) -> 'KnowledgeBase':
    data = _mapping(value, ('schema_version', 'objects', 'sources', 'entries'))
    version = data['schema_version']
    if type(version) is not int:
      raise ValueError(f'Unsupported schema version type: {type(version)}')
    if version != _SCHEMA_VERSION:
      raise ValueError(f'Unsupported schema version: {version}')
    return cls(
      tuple(_decode(KnowledgeObject, item) for item in _array(data['objects'])),
      tuple(_decode(KnowledgeSource, item) for item in _array(data['sources'])),
      tuple(_decode(KnowledgeEntry, item) for item in _array(data['entries'])),
    )

  @classmethod
  def load(cls, path: Path | None = None) -> 'KnowledgeBase':
    '''读取并校验知识 JSON；省略路径时读取随库语料。

    每次重新读取文件，不缓存共享实例；修改文件不影响已加载的知识库。

    Args:
    - path: (Path | None) 编辑源路径；None 使用 DEFAULT_SOURCE_PATH。

    Return: (KnowledgeBase) 已校验的知识库。
    '''
    if path is not None and not isinstance(path, Path):
      raise TypeError(f'Expected Path | None, got {type(path)}')
    source = DEFAULT_SOURCE_PATH if path is None else path
    return cls._from_data(_json_loads(source.read_text(encoding='utf-8')))

  def entry(self, claim_id: str) -> KnowledgeEntry:
    '''按稳定 ID 读取条目；未知 ID 抛 ValueError。'''
    _text(claim_id)
    if claim_id not in self.entries:
      raise ValueError(f'Unknown claim ID: {claim_id}')
    return self.entries[claim_id]

  def find_objects(self, name: str) -> tuple[KnowledgeObject, ...]:
    '''按名称精确查找对象，重名全部返回，保持注册顺序；无匹配返回空元组。'''
    _text(name)
    return tuple(value for value in self.objects.values() if value.name == name)

  def _resolve_object(self, subject: str | Tiangan | Shishen | Wuxing) -> str:
    if isinstance(subject, str):
      _text(subject)
      if subject in self.objects:
        return subject
      matches = self.find_objects(subject)
    elif isinstance(subject, (Tiangan, Shishen, Wuxing)):
      matches = tuple(
        value for value in self.find_objects(str(subject))
        if value.kind == type(subject).__name__.lower()
      )
    else:
      raise TypeError(f'Expected str | Tiangan | Shishen | Wuxing, got {type(subject)}')
    if not matches:
      raise ValueError(f'Unknown object: {subject}')
    if len(matches) != 1:
      raise ValueError(f'Ambiguous object: {subject}; candidates: {", ".join(value.object_id for value in matches)}')
    return matches[0].object_id

  def filter_values(self, dimension: str) -> tuple[str, ...]:
    '''列出 object_id、source_id、topic 或 viewpoint 的合法值，按 Unicode 序排列。

    包括尚未引用的对象和来源；合法过滤值不保证查询有匹配。
    '''
    _text(dimension)
    registries = {'object_id': tuple(self.objects), 'source_id': tuple(self.sources)}
    if dimension in registries:
      return tuple(sorted(registries[dimension]))
    if dimension in ('topic', 'viewpoint'):
      return tuple(sorted({key[1] for key in self._index if key[0] == dimension}))
    raise ValueError(f'Unknown dimension: {dimension}')

  def query(
    self,
    subject: str | Tiangan | Shishen | Wuxing | None = None,
    *,
    topic: str | None = None,
    source_id: str | None = None,
    viewpoint: str | None = None,
  ) -> tuple[KnowledgeEntry, ...]:
    '''按对象及可选过滤条件取交集，返回语料顺序的条目；无参数返回全部。

    Args:
    - subject: (str | Tiangan | Shishen | Wuxing | None) 对象 ID、精确名称或领域枚举；
      枚举按类别与中文名对应。重名抛 ValueError 并列出候选 ID。
    - topic: (str | None) 主题。
    - source_id: (str | None) 来源 ID。
    - viewpoint: (str | None) 读法。

    Return: (tuple[KnowledgeEntry, ...]) 命中条目；未知过滤值抛 ValueError。
    '''
    filters = {
      'object_id': None if subject is None else self._resolve_object(subject),
      'topic': topic, 'source_id': source_id, 'viewpoint': viewpoint,
    }
    candidates = frozenset(self.entries)
    for dimension, value in filters.items():
      if value is None:
        continue
      _text(value)
      if value not in self.filter_values(dimension):
        raise ValueError(f'Unknown {dimension}: {value}')
      candidates &= self._index.get((dimension, value), frozenset())
    return tuple(entry for entry in self.entries.values() if entry.claim_id in candidates)

  def search(
    self,
    keyword: str,
    *,
    subject: str | Tiangan | Shishen | Wuxing | None = None,
    topic: str | None = None,
    source_id: str | None = None,
    viewpoint: str | None = None,
  ) -> tuple[KnowledgeEntry, ...]:
    '''过滤后作 casefold 字面子串检索，无匹配返回空元组。

    搜索正文、前提、署名、主题、读法、限度及对象名称，不搜索 ID 或来源全文，
    不推断同义词。关键词须非空，不剥除两侧空白；其余条件与 query 相同。
    '''
    _text(keyword)
    needle = keyword.casefold()
    return tuple(
      entry for entry in self.query(subject, topic=topic, source_id=source_id, viewpoint=viewpoint)
      if any(needle in text.casefold() for text in (
        (entry.text, entry.premise, entry.attribution, entry.viewpoint) + entry.topics + entry.limits +
        tuple(self.objects[identifier].name for identifier in entry.objects)
      ))
    )

  def render(self, entry: KnowledgeEntry, *, show_sources: bool = False) -> str:
    '''显示条目、必要前提／限度、读法、署名及简短出处；空栏目省略。

    show_sources=True 另展开定位、原引文及支持范围。来源的必要说明始终显示，
    不因关闭详情而隐藏正文／夹注的区别或证据限度。本方法不求值命盘前提。
    '''
    if not isinstance(entry, KnowledgeEntry):
      raise TypeError(f'Expected KnowledgeEntry, got {type(entry)}')
    if not isinstance(show_sources, bool):
      raise TypeError(f'Expected bool, got {type(show_sources)}')
    if self.entries.get(entry.claim_id) != entry:
      raise ValueError(f'Foreign entry: {entry.claim_id}')
    lines = [f'条目：{entry.claim_id}', entry.text]
    for label, value in (
      ('主题', '／'.join(entry.topics)), ('前提', entry.premise),
      ('读法', entry.viewpoint), ('署名', entry.attribution),
    ):
      if value:
        lines.append(f'{label}：{value}')
    lines.extend('限度：' + limit for limit in entry.limits)
    for source_id in entry.sources:
      source = self.sources[source_id]
      lines.append(f'来源：{source.work}（{source.source_id}）')
      if source.state is not None:
        lines.append(f'来源状态：{source.state}')
      if source.limitations:
        lines.append(f'来源说明：{source.limitations}')
      if show_sources:
        for label, value in (
          ('来源署名', source.attribution), ('版本', source.edition), ('定位', source.locator),
          ('链接', source.url), ('引文／记录', source.excerpt), ('支持范围', source.supports),
        ):
          if value:
            lines.append(f'{label}：{value}')
    return '\n'.join(lines)

  def render_subject(
    self,
    subject: str | Tiangan | Shishen | Wuxing,
    *,
    show_sources: bool = False,
  ) -> str:
    '''按对象查询并展示全部相关条目；顺序与 query 相同，空查询返回空串。'''
    if not isinstance(show_sources, bool):
      raise TypeError(f'Expected bool, got {type(show_sources)}')
    return '\n\n'.join(self.render(entry, show_sources=show_sources) for entry in self.query(subject))
