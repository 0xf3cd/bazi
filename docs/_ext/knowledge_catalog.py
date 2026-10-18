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
from bazi.context_matching import criteria
from bazi.knowledge import KnowledgeBase, KnowledgeEntry


'''目录 kind 到相关条目查询维度的关系；criteria 与 entries 是显式特例。'''
KIND_DIMENSIONS: Final[dict[str, str]] = {
  'objects': 'object_id', 'contexts': 'context_id', 'sources': 'source_id',
  'topics': 'topic', 'viewpoints': 'viewpoint',
}


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
      section += nodes.title(text=identifier)
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
      description = nodes.field_list()
      for name, content in fields:
        field = nodes.field()
        field += nodes.field_name(text=name)
        body = nodes.field_body()
        if name == 'url' and isinstance(content, str) and content.startswith(('https://', 'http://')):
          paragraph = nodes.paragraph()
          paragraph += nodes.reference('', content, refuri=content)
          body += paragraph
        else:
          body += nodes.paragraph(text=text_value(content))
        field += body
        description += field
      section += description
      if kind == 'entries':
        section += nodes.literal_block(text=kb.render(value, show_sources=False))
      elif selected:
        section += nodes.paragraph(text='相关条目（包含仅供参考条目）：')
        listing = nodes.bullet_list()
        for entry in selected:
          item = nodes.list_item()
          paragraph = nodes.paragraph()
          path = self.env.app.builder.get_relative_uri(self.env.docname, 'catalog/entries')
          paragraph += nodes.reference('', entry.claim_id, refuri=path + '#catalog-entries-' + entry.claim_id, internal=True)
          item += paragraph
          listing += item
        section += listing
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
