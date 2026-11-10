# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''从完整注册表生成知识目录；语料仅作为文本，不解析为标记。'''

import dataclasses
import inspect
import json
from collections.abc import Callable, Mapping
from enum import Enum
from typing import Any, Final

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

from api_contract import DECLARED_MEMBERS
from bazi.context_matching import CriterionInfo, criteria
from bazi.knowledge import KnowledgeBase, KnowledgeContext, KnowledgeEntry, KnowledgeObject, KnowledgeSource


'''目录 kind 到相关条目查询维度的关系；criteria 与 entries 是显式特例。'''
KIND_DIMENSIONS: Final[dict[str, str]] = {
  'objects': 'object_id', 'contexts': 'context_id', 'sources': 'source_id',
  'topics': 'topic', 'viewpoints': 'viewpoint',
}


'''正文先呈现的字段；其余契约字段仍完整列在登记信息中。'''
READING_FIELDS: Final[dict[str, tuple[tuple[str, str], ...]]] = {
  'objects': (('name', '名称'), ('kind', '类别')),
  'contexts': (('label', '情境'), ('time_scope', '时间范围'), ('limits', '限度')),
  'sources': (
    ('work', '作品'), ('attribution', '署名'), ('edition', '版本'), ('locator', '位置'),
    ('url', '原文'), ('text_layer', '文本层'), ('state', '来源状态'),
    ('excerpt', '摘录'), ('supports', '支持内容'), ('limitations', '支持限度'),
  ),
  'entries': (
    ('text', '条文'), ('applicability', '前提整理状态'), ('premise', '前提'),
    ('exceptions', '例外'), ('limits', '限度'), ('source_state', '来源状态'),
    ('show_by_default', '默认展示'),
  ),
  'criteria': (
    ('definition', '定义与未实现部分'), ('entry_role', '关联条目的前提关系'),
    ('required_gender', '判据性别门槛'),
    ('claim_genders', '关联条目的性别限制'),
  ),
}


def entry_label(entry: KnowledgeEntry) -> str:
  '''链接保留稳定 ID，以原文片段提示内容，不另编摘要。'''
  excerpt = ' '.join(entry.text.split())
  return (excerpt[:28] + '…' if len(excerpt) > 28 else excerpt) + ' [' + entry.claim_id + ']'


def catalog_label(
  kb: KnowledgeBase, identifier: str,
  value: KnowledgeEntry | KnowledgeObject | KnowledgeContext | KnowledgeSource | CriterionInfo | str,
) -> str:
  if isinstance(value, KnowledgeEntry):
    names = '、'.join(dict.fromkeys(kb.objects[role.object_id].name for role in value.roles))
    return names + ' · ' + '、'.join(value.topics) + ' [' + identifier + ']'
  if isinstance(value, KnowledgeObject):
    return value.name + ' [' + identifier + ']'
  if isinstance(value, KnowledgeContext):
    return value.label + ' [' + identifier + ']'
  if isinstance(value, KnowledgeSource):
    return value.work + ' · ' + value.locator + ' [' + identifier + ']'
  if isinstance(value, CriterionInfo):
    return value.definition.split('；', 1)[0] + ' [' + identifier + ']'
  return value


def json_value(value: Any) -> Any:
  if isinstance(value, type):
    return value.__module__ + '.' + value.__qualname__
  if isinstance(value, Enum):
    return json_value(value.value)
  if dataclasses.is_dataclass(value):
    return {field.name: json_value(getattr(value, field.name)) for field in dataclasses.fields(value)}
  if isinstance(value, Mapping):
    return {key: json_value(item) for key, item in value.items()}
  if isinstance(value, (set, frozenset)):
    return sorted((json_value(item) for item in value), key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
  if isinstance(value, (tuple, list)):
    return [json_value(item) for item in value]
  if isinstance(value, (str, int, float, bool)) or value is None:
    return value
  raise TypeError(type(value))


def text_value(value: Any) -> str:
  return value if isinstance(value, str) else json.dumps(json_value(value), ensure_ascii=False)


class KnowledgeCatalog(SphinxDirective):
  required_arguments = 1

  def reference(self, kind: str, identifier: str, label: str) -> nodes.reference:
    path = self.env.app.builder.get_relative_uri(self.env.docname, 'catalog/' + kind)
    return nodes.reference('', label, refuri=path + '#catalog-' + kind + '-' + identifier, internal=True)

  def references(self, kb: KnowledgeBase, value: KnowledgeEntry) -> list[nodes.Node]:
    '''人读链接与原始引用字段分开呈现；无引用时明确说明。'''
    result: list[nodes.Node] = []
    for title, kind, identifiers, registry in (
      ('讨论对象', 'objects', tuple(role.object_id for role in value.roles), kb.objects),
      ('情境', 'contexts', value.contexts, kb.contexts),
      ('来源', 'sources', value.sources, kb.sources),
    ):
      paragraph = nodes.paragraph(text=title + '：')
      for index, identifier in enumerate(dict.fromkeys(identifiers)):
        if index:
          paragraph += nodes.Text('；')
        paragraph += self.reference(kind, identifier, catalog_label(kb, identifier, registry[identifier]))
      if not identifiers:
        paragraph += nodes.Text('未登记' if kind == 'sources' else '无')
      result.append(paragraph)
    return result

  def fields(self, fields: list[tuple[str, Any]], labels: Mapping[str, str]) -> nodes.field_list:
    description = nodes.field_list()
    for name, content in fields:
      field = nodes.field()
      field += nodes.field_name(text=labels.get(name, name), classes=['catalog-field-' + name])
      body = nodes.field_body()
      if name == 'url' and isinstance(content, str) and content.startswith(('https://', 'http://')):
        paragraph = nodes.paragraph()
        paragraph += nodes.reference('', content, refuri=content)
        body += paragraph
      else:
        body += nodes.paragraph(text=text_value(content))
      field += body
      description += field
    return description

  def run(self) -> list[nodes.Node]:
    kb = KnowledgeBase.load()
    kind = self.arguments[0]
    if kind == 'filters':
      return filter_tables(kb)
    registries: dict[str, Mapping[str, Any]] = {
      'objects': kb.objects, 'contexts': kb.contexts, 'sources': kb.sources, 'entries': kb.entries,
    }
    items: Any
    if kind in registries:
      items = registries[kind].items()
    elif kind == 'criteria':
      items = criteria().items()
    elif kind in KIND_DIMENSIONS:
      items = ((value, value) for value in kb.filter_values(KIND_DIMENSIONS[kind]))
    else:
      raise self.error('Unsupported catalog: ' + kind)
    query: Callable[..., tuple[KnowledgeEntry, ...]] = kb.query
    sections: list[nodes.Node] = []
    for identifier, value in items:
      section = nodes.section(ids=['catalog-' + kind + '-' + identifier])
      label = catalog_label(kb, identifier, value)
      title = nodes.title()
      if label.endswith(' [' + identifier + ']'):
        title += nodes.Text(label[:-(len(identifier) + 3)] + ' ')
        title += nodes.literal('', '[' + identifier + ']', classes=['catalog-id'])
      else:
        title += nodes.Text(label)
      section += title
      fields: list[tuple[str, Any]] = []
      if kind not in ('topics', 'viewpoints'):
        members = DECLARED_MEMBERS.get(f'{type(value).__module__}.{type(value).__qualname__}')
        if members is None:
          raise self.error('Catalog value is not declared in the public contract: ' + type(value).__qualname__)
        fields = [(name, getattr(value, name)) for name in members.split()]
      selected: tuple[KnowledgeEntry, ...]
      if kind == 'entries':
        selected = ()
      elif kind == 'criteria':
        selected = tuple(kb.entries[claim_id] for claim_id in value.claim_ids if claim_id in kb.entries)
      else:
        selected = query(**{KIND_DIMENSIONS[kind]: identifier}, include_reference_only=True)
      primary = dict(READING_FIELDS.get(kind, ()))
      field_values = dict(fields)
      primary = {
        name: label for name, label in primary.items()
        if field_values[name] not in ('', (), None)
        and not (isinstance(field_values[name], Mapping) and not field_values[name])
      }
      section += self.fields([(name, field_values[name]) for name in primary], primary)
      if kind == 'entries':
        section.extend(self.references(kb, value))
      if kind == 'criteria':
        section += nodes.paragraph(text='观察请求、范围与额外输入：')
        observations = nodes.bullet_list()
        for observation_type, scope in zip(value.observation_types, value.scopes):
          item = nodes.list_item()
          paragraph = nodes.paragraph(text=scope + '：')
          qualified = observation_type.__module__ + '.' + observation_type.__qualname__
          path = self.env.app.builder.get_relative_uri(self.env.docname, 'api/' + observation_type.__module__.replace('.', '-'))
          paragraph += nodes.reference('', observation_type.__name__, refuri=path + '#' + qualified, internal=True)
          inputs = value.scope_inputs[scope]
          paragraph += nodes.Text('；额外输入：' + '、'.join(inputs) if inputs else '；无额外输入')
          item += paragraph
          observations += item
        section += observations
        paragraph = nodes.paragraph(text='求值步骤与结果读取：')
        path = self.env.app.builder.get_relative_uri(self.env.docname, 'guides/integration')
        paragraph += nodes.reference('', '前提匹配指南', refuri=path + '#context-matching', internal=True)
        section += paragraph
      if selected:
        section += nodes.paragraph(text='相关条目（包含仅供参考条目）：')
        listing = nodes.bullet_list()
        for entry in selected:
          item = nodes.list_item()
          paragraph = nodes.paragraph()
          paragraph += self.reference('entries', entry.claim_id, entry_label(entry))
          item += paragraph
          listing += item
        section += listing
      metadata = [(name, content) for name, content in fields if name not in primary]
      if metadata:
        section += nodes.raw('', '<details class="catalog-metadata"><summary>登记信息（字段原值）</summary>', format='html')
        section += self.fields(metadata, {})
        section += nodes.raw('', '</details>', format='html')
      sections.append(section)
    return sections


def filter_tables(kb: KnowledgeBase) -> list[nodes.Node]:
  '''合法值来自查询接口；默认与含参考命中数分别实际查询。'''
  sections: list[nodes.Node] = []
  query: Callable[..., tuple[KnowledgeEntry, ...]] = kb.query
  for dimension in inspect.signature(kb.query).parameters:
    if dimension == 'include_reference_only':
      continue
    section = nodes.section(ids=['catalog-filters-' + dimension])
    section += nodes.title(text=dimension)
    table = nodes.table()
    group = nodes.tgroup(cols=3)
    for width in (3, 1, 1):
      group += nodes.colspec(colwidth=width)
    header = nodes.thead()
    row = nodes.row()
    for title in ('合法值', '默认命中', '含参考命中'):
      entry = nodes.entry()
      entry += nodes.paragraph(text=title)
      row += entry
    header += row
    group += header
    body = nodes.tbody()
    for value in kb.filter_values(dimension):
      row = nodes.row()
      counts = (value, str(len(query(**{dimension: value}))), str(len(query(**{dimension: value}, include_reference_only=True))))
      for text in counts:
        entry = nodes.entry()
        entry += nodes.paragraph(text=text)
        row += entry
      body += row
    group += body
    table += group
    section += table
    sections.append(section)
  return sections


def setup(app: Sphinx) -> dict[str, bool]:
  app.add_directive('knowledge-catalog', KnowledgeCatalog)
  return {'parallel_read_safe': True, 'parallel_write_safe': True}
