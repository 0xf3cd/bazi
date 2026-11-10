import dataclasses
import importlib
import inspect
import json
import re
import sys
import typing
import zlib
from collections import Counter
from collections.abc import Callable, Mapping
from enum import Enum
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'docs' / '_ext'))

from api_contract import DECLARED_MEMBERS, PRIVATE_BASE_MEMBERS, PUBLIC_NAMES
from api_examples import check_example_blocks, collect_examples, run_example
from house_docstrings import HEADER_WORDS, source_attribute_docs
from knowledge_catalog import json_value
from bazi.context_matching import CriterionInfo, criteria
from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase, KnowledgeEntry
from bazi.rules import BaziRules, TianganRules, DizhiRules, ShenshaRules, DizhiRelationDefinitions
from bazi.school import BaziConfig, BaziSchool


BARE_HEADER = re.compile(r'(?:' + '|'.join(HEADER_WORDS) + ')[:：]')
DOCTEST_PHASES = ('setup', 'cleanup')


EXAMPLE_GROUPS = {
  'readme-example': {'readme-first'},
  'guides/quickstart': {'quickstart-chart', 'quickstart-text', 'quickstart-save'},
  'guides/configuration': {'config-create', 'config-precision', 'config-overseas', 'config-backend', 'config-rollover', 'config-school-preset', 'config-dayun-rule', 'config-location', 'config-replace', 'kongwang-configuration', 'config-tuwang'},
  'guides/relations-transits': {'transits-query', 'relations-day-master', 'relations-house', 'transits-generators', 'transits-text', 'kongwang-details', 'relations-shensha-labels', 'relations-all-positions', 'relations-tonggen-tougan'},
  'guides/integration': {'integration-fields', 'integration-pillars', 'integration-context', 'integration-transits', 'integration-text-style', 'integration-auxiliary'},
  'guides/knowledge': {'load', 'search', 'sources', 'render', 'edit', 'criteria', 'auxiliary-knowledge', 'shensha-knowledge'},
  'guides/rule-coverage': {'guoyin-lookup'},
}

SOURCELESS_ALIAS_DESCRIPTIONS = {
  'bazi.bazi_chart.BaziChart.PillarShishens': 'GanzhiData[Shishen | None, Shishen] 的别名',
  'bazi.bazi_chart.BaziChart.PillarTraits': 'GanzhiData[TraitTuple, TraitTuple] 的别名',
}


class Page(HTMLParser):
  def __init__(self) -> None:
    super().__init__()
    self.ids: set[str] = set()
    self.links: list[str] = []
    self.labels: dict[str, str] = {}
    self.current_id: str | None = None
    self.label_depth = 0
    self.label_text: list[str] = []
    self.sections: dict[str, dict[str, str]] = {}
    self.blocks: dict[str, list[str]] = {}
    self.code_blocks: list[str] = []
    self.rows: dict[str, list[list[str]]] = {}
    self.related: dict[str, list[tuple[str, str]]] = {}
    self.related_id: str | None = None
    self.related_text: list[str] = []
    self.row: list[str] | None = None
    self.cell: list[str] | None = None
    self.cells: list[str] = []
    self.section: str | None = None
    self.section_stack: list[str | None] = []
    self.dt: list[str] | None = None
    self.dd: list[str] | None = None
    self.pre: list[str] | None = None
    self.paragraph: list[str] | None = None
    self.paragraphs: list[str] = []
    self.field_name: str | None = None
    self.field_key: str | None = None
    self.heading: list[str] | None = None
    self.headings: list[str] = []
    self.section_headings: dict[str, str] = {}
    self.references: dict[str, list[tuple[str, str]]] = {}
    self.reference_href: str | None = None
    self.reference_text: list[str] = []

  def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
    attributes = dict(attrs)
    if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
      self.heading = []
    identifier = attributes.get('id')
    if identifier:
      if identifier in self.ids:
        raise ValueError(f'Duplicate HTML id: {identifier}')
      self.ids.add(identifier)
    href = attributes.get('href')
    if tag in ('a', 'link') and href is not None:
      self.links.append(href)
      fragment = unquote(urlsplit(href).fragment)
      if tag == 'a' and self.section and 'reference' in (attributes.get('class') or '').split() and fragment.startswith('catalog-entries-'):
        self.related_id = fragment.removeprefix('catalog-entries-')
        self.related_text = []
      if tag == 'a' and self.section and 'reference' in (attributes.get('class') or '').split():
        self.reference_href = href
        self.reference_text = []
    source = attributes.get('src')
    if tag in ('img', 'script') and source is not None:
      self.links.append(source)
    if tag == 'dt':
      self.current_id = identifier
      self.field_key = next((value.removeprefix('catalog-field-')
        for value in (attributes.get('class') or '').split() if value.startswith('catalog-field-')), None)
    if tag == 'span':
      if self.label_depth:
        self.label_depth += 1
      elif self.current_id and 'descname' in (attributes.get('class') or '').split():
        self.label_depth = 1
        self.label_text = []
    if tag == 'section':
      self.section_stack.append(self.section)
      if identifier and identifier.startswith('catalog-'):
        self.section = identifier
        self.sections[identifier] = {}
        self.blocks[identifier] = []
        self.rows[identifier] = []
        self.related[identifier] = []
        self.references[identifier] = []
    if self.section:
      if tag == 'dt':
        self.dt = []
      elif tag == 'dd':
        self.dd = []
      elif tag == 'tr':
        self.row = []
    if tag == 'pre':
      self.pre = []
    if tag in ('th', 'td'):
      self.cell = []
    if tag == 'p':
      self.paragraph = []

  def handle_data(self, text: str) -> None:
    if self.heading is not None:
      self.heading.append(text)
    if self.label_depth:
      self.label_text.append(text)
    if self.related_id is not None:
      self.related_text.append(text)
    if self.reference_href is not None:
      self.reference_text.append(text)
    if self.paragraph is not None:
      self.paragraph.append(text)
    for target in (self.dt, self.dd, self.pre, self.cell):
      if target is not None:
        target.append(text)

  def handle_endtag(self, tag: str) -> None:
    if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6') and self.heading is not None:
      heading = ''.join(self.heading).removesuffix('¶').strip()
      self.headings.append(heading)
      if self.section is not None:
        self.section_headings[self.section] = heading
      self.heading = None
    if tag == 'a' and self.reference_href is not None:
      assert self.section is not None
      self.references[self.section].append((self.reference_href, ''.join(self.reference_text)))
      self.reference_href = None
    if tag == 'a' and self.related_id is not None:
      assert self.section is not None
      self.related[self.section].append((self.related_id, ''.join(self.related_text)))
      self.related_id = None
    if tag == 'p' and self.paragraph is not None:
      self.paragraphs.append(''.join(self.paragraph))
      self.paragraph = None
    if tag == 'span' and self.label_depth:
      self.label_depth -= 1
      if not self.label_depth and self.current_id:
        self.labels[self.current_id] = ''.join(self.label_text)
    if tag == 'dt':
      self.current_id = None
      if self.dt is not None:
        self.field_name = self.field_key or ''.join(self.dt).strip().removesuffix(':')
        self.dt = None
    elif tag == 'dd' and self.dd is not None:
      assert self.section is not None and self.field_name is not None
      assert self.field_name not in self.sections[self.section]
      self.sections[self.section][self.field_name] = ''.join(self.dd)
      self.dd = None
    elif tag == 'pre' and self.pre is not None:
      text = ''.join(self.pre)
      self.code_blocks.append(text)
      if self.section is not None:
        self.blocks[self.section].append(text)
      self.pre = None
    elif tag == 'section':
      self.section = self.section_stack.pop()
    elif tag in ('th', 'td') and self.cell is not None:
      text = ''.join(self.cell).strip()
      self.cells.append(text)
      if self.row is not None:
        self.row.append(text)
      self.cell = None
    elif tag == 'tr' and self.row is not None:
      assert self.section is not None
      self.rows[self.section].append(self.row)
      self.row = None


class AttributeDescriptions(HTMLParser):
  def __init__(self) -> None:
    super().__init__()
    self.definitions: list[tuple[bool, str | None]] = []
    self.dd_depth = 0
    self.capture_depth = 0
    self.current: str | None = None
    self.text: list[str] = []
    self.descriptions: dict[str, str] = {}

  def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
    attributes = dict(attrs)
    if tag == 'dl':
      classes = (attributes.get('class') or '').split()
      self.definitions.append(('py' in classes and bool({'data', 'attribute'} & set(classes)), None))
    elif tag == 'dt' and self.definitions:
      self.definitions[-1] = self.definitions[-1][0], attributes.get('id')
    elif tag == 'dd':
      self.dd_depth += 1
      if not self.current and self.definitions and self.definitions[-1][0]:
        self.current = self.definitions[-1][1]
        self.capture_depth = self.dd_depth
        self.text = []

  def handle_data(self, text: str) -> None:
    if self.current:
      self.text.append(text)

  def handle_endtag(self, tag: str) -> None:
    if tag == 'dd':
      if self.current and self.dd_depth == self.capture_depth:
        self.descriptions[self.current] = ''.join(self.text).strip()
        self.current = None
      self.dd_depth -= 1
    elif tag == 'dl':
      self.definitions.pop()


class Signatures(HTMLParser):
  def __init__(self) -> None:
    super().__init__()
    self.current: str | None = None
    self.parameter: list[str] | None = None
    self.parameters: list[str] = []
    self.result: dict[str, list[str]] = {}
    self.texts: dict[str, str] = {}
    self.text: list[str] = []

  def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
    attributes = dict(attrs)
    if tag == 'dt' and 'sig-object' in (attributes.get('class') or '').split():
      self.current = attributes.get('id')
      self.parameters = []
      self.text = []
    if self.current and tag == 'em' and 'sig-param' in (attributes.get('class') or '').split():
      self.parameter = []

  def handle_data(self, data: str) -> None:
    if self.current:
      self.text.append(data)
    if self.parameter is not None:
      self.parameter.append(data)

  def handle_endtag(self, tag: str) -> None:
    if tag == 'em' and self.parameter is not None:
      self.parameters.append(''.join(self.parameter))
      self.parameter = None
    if tag == 'dt' and self.current:
      self.result[self.current] = self.parameters
      self.texts[self.current] = ''.join(self.text)
      self.current = None


def signature_defaults(parameters: list[str]) -> dict[str, str]:
  '''签名中的类型和排版空格不参与默认值比较；名字、顺序和值仍逐项核对。'''
  return {
    parameter.split('=', 1)[0].split(':', 1)[0].strip(): parameter.split('=', 1)[1].strip()
    for parameter in parameters
  }


def check_configuration_signatures(site: Path) -> None:
  signatures = Signatures()
  for name in ('bazi-school', 'bazi-rules'):
    signatures.feed((site / 'api' / (name + '.html')).read_text(encoding='utf-8'))
  for cls in (BaziConfig, BaziSchool, DizhiRelationDefinitions):
    qualified = cls.__module__ + '.' + cls.__name__
    parameters = signatures.result[qualified]
    expected = inspect.signature(cls).parameters
    rendered = signature_defaults(parameters)
    assert list(rendered) == list(expected), (qualified, parameters, list(expected))
    for name, parameter in expected.items():
      value = parameter.default
      default = f'{type(value).__name__}.{value.name}' if isinstance(value, Enum) else repr(value)
      assert rendered[name] == default, (qualified, name, rendered[name], default)
      if isinstance(value, Enum):
        member = qualified + '.' + name
        assert '= ' + type(value).__qualname__ + '.' + value.name in signatures.texts[member], ('Field default', member)
  assert signature_defaults(signatures.result['bazi.school.BaziConfig.from_values']) == {
    'precision': 'BaziPrecision.DAY', 'backend': 'CalendarBackend.CELESTIAL',
    'school': 'DEFAULT_SCHOOL', 'dayun_year_rule': 'DayunYearRule.JIE_PROJECTED',
  }
  for rule_class in (BaziRules, TianganRules, DizhiRules, ShenshaRules):
    qualified = rule_class.__module__ + '.' + rule_class.__name__
    for name in DECLARED_MEMBERS[qualified].split():
      if name.isupper():
        member = qualified + '.' + name
        assert '=' not in signatures.texts[member], ('Rule table value', member)


def normalized(text: str) -> str:
  return ' '.join(text.split())


def check_header_paragraphs(pages: dict[str, Page]) -> int:
  '''API 页的裸节标题须是所在段落唯一的非空行。'''
  checked = 0
  for filename, page in sorted(pages.items()):
    if not filename.startswith('api/'):
      continue
    for paragraph in page.paragraphs:
      lines = paragraph.splitlines()
      for line in lines:
        if BARE_HEADER.fullmatch(line.strip()) is None:
          continue
        checked += 1
        assert sum(bool(part.strip()) for part in lines) == 1, (filename, paragraph)
  assert checked > 0, 'No section header paragraphs checked'
  return checked


def contract_class(qualified: str) -> type[typing.Any]:
  '''按契约名解析运行时类；模块名取自公开契约，嵌套类沿 qualname 取得。'''
  parts = qualified.split('.')
  for index in range(len(parts) - 1, 0, -1):
    module = '.'.join(parts[:index])
    if module not in PUBLIC_NAMES:
      continue
    value: typing.Any = importlib.import_module(module)
    for part in parts[index:]:
      value = getattr(value, part)
    assert isinstance(value, type)
    return value
  raise ValueError(f'Unsupported contract class: {qualified}')


def runtime_members(cls: str) -> set[str]:
  '''沿实际 __mro__／TypedDict 合并注解求继承期望，不复用生成器的名字解析。'''
  declared = DECLARED_MEMBERS | PRIVATE_BASE_MEMBERS
  names = set(declared.get(cls, '').split())
  value = contract_class(cls)
  if typing.is_typeddict(value):
    return names | set(value.__annotations__)
  for base in value.__mro__[1:]:
    names |= set(declared.get(base.__module__ + '.' + base.__qualname__, '').split())
  return names


def check_api(site: Path, pages: dict[str, Page]) -> int:
  expected = set(PUBLIC_NAMES)
  expected.update(module + '.' + name for module, names in PUBLIC_NAMES.items() for name in names.split())
  for cls in DECLARED_MEMBERS:
    expected.update(cls + '.' + name for name in runtime_members(cls))
  with (site / 'objects.inv').open('rb') as stream:
    for _ in range(4):
      stream.readline()
    inventory = {
      row[0]: row[3] for line in zlib.decompress(stream.read()).decode().splitlines()
      if ' py:' in line and (row := line.split(maxsplit=4))
    }
  assert inventory.keys() == expected, ('inventory', sorted(expected - inventory.keys()), sorted(inventory.keys() - expected))
  for name in expected:
    uri = unquote(inventory[name].replace('$', name))
    filename, _, fragment = uri.partition('#')
    assert filename in pages and fragment in pages[filename].ids, (name, uri)
    if name not in PUBLIC_NAMES:
      assert pages[filename].labels.get(fragment) == name.rsplit('.', 1)[-1], (name, uri)
  return len(expected)


def check_related(page: Page, identifier: str, entries: tuple[KnowledgeEntry, ...]) -> None:
  expected = []
  for entry in entries:
    text = ' '.join(entry.text.split())
    label = (text[:28] + '…' if len(text) > 28 else text) + ' [' + entry.claim_id + ']'
    expected.append((entry.claim_id, label))
  expected.sort()
  assert sorted(page.related[identifier]) == expected, ('Related entries', identifier)


def check_entry_references(page: Page, identifier: str, entry: KnowledgeEntry, kb: KnowledgeBase) -> None:
  '''检查必需链接，而不是仅检查页面上已经存在的链接是否可达。'''
  expected = []
  for object_id in dict.fromkeys(role.object_id for role in entry.roles):
    expected.append(('objects.html#catalog-objects-' + object_id, kb.objects[object_id].name + ' [' + object_id + ']'))
  for context_id in entry.contexts:
    expected.append(('contexts.html#catalog-contexts-' + context_id, kb.contexts[context_id].label + ' [' + context_id + ']'))
  for source_id in entry.sources:
    source = kb.sources[source_id]
    expected.append(('sources.html#catalog-sources-' + source_id, source.work + ' · ' + source.locator + ' [' + source_id + ']'))
  assert page.references[identifier] == expected, ('Entry references', identifier)


def check_catalog(pages: dict[str, Page]) -> dict[str, int]:
  kb = KnowledgeBase.load()
  source = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  records: dict[str, Mapping[str, typing.Any]] = {
    kind: {record[key_name]: record for record in source[kind]} for kind, key_name in (
      ('objects', 'object_id'), ('contexts', 'context_id'), ('sources', 'source_id'), ('entries', 'claim_id'),
    )
  }
  registries: dict[str, typing.Mapping[str, typing.Any]] = {
    'objects': kb.objects, 'contexts': kb.contexts, 'sources': kb.sources, 'entries': kb.entries, 'criteria': criteria(),
  }
  result = {}
  for kind, registry in registries.items():
    page = pages[f'catalog/{kind}.html']
    assert set(page.sections) == {'catalog-' + kind + '-' + key for key in registry}, kind
    for key, value in registry.items():
      identifier = 'catalog-' + kind + '-' + key
      section = page.sections[identifier]
      names = {field.name for field in dataclasses.fields(value)}
      if kind == 'criteria':
        names |= {name for name, member in vars(CriterionInfo).items() if isinstance(member, property)}
      assert set(section) == names, (kind, key, set(section), names)
      for name in names:
        rendered = getattr(value, name)
        expected = json_value(rendered) if kind == 'criteria' else records[kind][key][name]
        if isinstance(rendered, str):
          assert normalized(section[name]) == normalized(expected), (kind, key, name)
        else:
          actual_json = json.dumps(json.loads(section[name]), ensure_ascii=False, sort_keys=True)
          expected_json = json.dumps(expected, ensure_ascii=False, sort_keys=True)
          assert actual_json == expected_json, (kind, key, name, actual_json, expected_json)
      selected: tuple[KnowledgeEntry, ...]
      if kind == 'entries':
        assert not page.blocks[identifier], ('Repeated entry rendering', key)
        assert list(section)[:2] == ['text', 'applicability'], ('Entry reading order', key)
        if value.premise:
          assert list(section)[2] == 'premise', ('Entry premise order', key)
        check_entry_references(page, identifier, value, kb)
        selected = ()
      elif kind == 'criteria':
        assert list(section)[:2] == ['definition', 'entry_role'], ('Criterion reading order', key)
        assert any('guides/integration.html#' in href for href, _ in page.references[identifier]), ('Criterion guide', key)
        for observation_type in value.observation_types:
          qualified = observation_type.__module__ + '.' + observation_type.__qualname__
          href = '../api/' + observation_type.__module__.replace('.', '-') + '.html#' + qualified
          assert (href, observation_type.__name__) in page.references[identifier], ('Criterion observation', key, qualified)
        selected = tuple(kb.entries[claim_id] for claim_id in value.claim_ids if claim_id in kb.entries)
      elif kind == 'objects':
        selected = kb.query(object_id=key, include_reference_only=True)
      elif kind == 'contexts':
        selected = kb.query(context_id=key, include_reference_only=True)
      else:
        selected = kb.query(source_id=key, include_reference_only=True)
      check_related(page, identifier, selected)
      heading = page.section_headings[identifier]
      assert '[' + key + ']' in heading, ('Stable ID in title', kind, key)
      if kind == 'objects':
        assert heading.startswith(value.name + ' ['), ('Object name', key)
      elif kind == 'contexts':
        assert heading.startswith(value.label + ' ['), ('Context name', key)
      elif kind == 'sources':
        assert heading.startswith(value.work + ' · ' + value.locator + ' ['), ('Source title', key)
        assert (value.url, value.url) in page.references[identifier], ('Source original', key)
      elif kind == 'entries':
        object_names = '、'.join(dict.fromkeys(kb.objects[role.object_id].name for role in value.roles))
        assert heading == object_names + ' · ' + '、'.join(value.topics) + ' [' + key + ']', ('Entry title', key)
    result[kind] = len(registry)
  for kind, dimension in (('topics', 'topic'), ('viewpoints', 'viewpoint')):
    expected_ids = {'catalog-' + kind + '-' + value for value in kb.filter_values(dimension)}
    assert set(pages[f'catalog/{kind}.html'].sections) == expected_ids, kind
    result[kind] = len(expected_ids)
    for value in kb.filter_values(dimension):
      selected = (kb.query(topic=value, include_reference_only=True) if kind == 'topics'
                  else kb.query(viewpoint=value, include_reference_only=True))
      check_related(pages[f'catalog/{kind}.html'], 'catalog-' + kind + '-' + value, selected)
  dimensions = ('object_id', 'context_id', 'source_id', 'topic', 'viewpoint', 'applicability', 'time_scope')
  filters = pages['catalog/filters.html']
  assert set(filters.sections) == {'catalog-filters-' + dimension for dimension in dimensions}
  query: Callable[..., tuple[KnowledgeEntry, ...]] = kb.query
  for dimension in dimensions:
    expected_rows = [['合法值', '默认命中', '含参考命中']]
    for value in kb.filter_values(dimension):
      expected_rows.append([value, str(len(query(**{dimension: value}))), str(len(query(**{dimension: value}, include_reference_only=True)))])
    assert filters.rows['catalog-filters-' + dimension] == expected_rows, dimension
  result['filter_dimensions'] = len(dimensions)
  return result


def check_links(site: Path, pages: dict[str, Page]) -> None:
  for filename, page in pages.items():
    for href in page.links:
      target = urlsplit(href)
      if target.scheme or target.netloc:
        assert target.scheme in ('http', 'https'), (filename, href)
        continue
      destination = (site / filename).parent / unquote(target.path) if target.path else site / filename
      destination = destination.resolve()
      assert destination.is_relative_to(site.resolve()) and destination.is_file(), (filename, href)
      relative = destination.relative_to(site.resolve()).as_posix()
      if target.fragment:
        assert relative in pages and unquote(target.fragment) in pages[relative].ids, (filename, href)


def check_release_notes(pages: dict[str, Page]) -> int:
  '''检查发布页导航、必需迁移节及正本标题、段落和表格的渲染对应。'''
  page = pages['release-notes.html']
  assert any(urlsplit(link).path == 'release-notes.html' and not urlsplit(link).scheme
    for link in pages['index.html'].links), 'Release notes missing from navigation'
  reference = Page()
  source = (ROOT / 'RELEASE_NOTES.md').read_text(encoding='utf-8')
  reference.feed(MarkdownIt('commonmark').enable('table').render(source))
  assert {
    '知识结构迁移', '安装版命令与脚本迁移', '存取接口移除', '结构接口迁移', '源码脚本的平铺参数',
  } <= set(reference.headings), 'Missing release migration sections'
  assert page.headings[:len(reference.headings)] == reference.headings, 'Rendered release headings differ from source'
  expected = Counter(map(normalized, reference.paragraphs))
  assert expected <= Counter(map(normalized, page.paragraphs)), 'Rendered release paragraphs differ from source'
  assert Counter(map(normalized, reference.cells)) <= Counter(map(normalized, page.cells)), 'Rendered release tables differ from source'
  return len(reference.headings)


def check_task_navigation(pages: dict[str, Page], version: str, sha: str) -> None:
  '''使用路径留在当前构建；当前贡献政策是明确允许的跨版本链接。'''
  for filename, page in pages.items():
    for link in page.links:
      url = urlsplit(link)
      if url.netloc == 'github.com' and url.path.startswith('/0xf3cd/bazi/blob/main/'):
        assert filename == 'contributing.html' and url.path == '/0xf3cd/bazi/blob/main/AGENTS.md', (filename, link)
      if url.netloc == '0xf3cd.github.io':
        assert url.path in ('/bazi/', '/bazi/versions/'), (filename, link)
  expected = {
    'guides/quickstart.html', 'guides/cli.html', 'guides/configuration.html',
    'guides/relations-transits.html', 'guides/knowledge.html', 'guides/integration.html', 'api-contract.html',
  }
  assert expected <= set(pages), ('Missing task pages', expected - set(pages))
  index_links = {urlsplit(link).path for link in pages['index.html'].links if not urlsplit(link).scheme}
  assert expected <= index_links, ('Missing task navigation', expected - index_links)
  requirement = f'git+https://github.com/0xf3cd/bazi.git@{sha}' if version == 'dev' else 'bazi==' + version.removeprefix('v')
  command = f'python -m pip install "{requirement}"'
  for name in ('quickstart', 'knowledge', 'cli'):
    assert any(block.strip() == command for block in pages[f'guides/{name}.html'].code_blocks), ('Installation identity', name)


def check_attribute_descriptions(site: Path) -> int:
  docs = source_attribute_docs(ROOT / 'bazi')
  checked = 0
  for path in site.rglob('*.html'):
    descriptions = AttributeDescriptions()
    descriptions.feed(path.read_text(encoding='utf-8'))
    for name, text in descriptions.descriptions.items():
      if name not in docs or docs[name]:
        continue
      checked += 1
      expected = SOURCELESS_ALIAS_DESCRIPTIONS.get(name, '')
      assert normalized(text) == expected, (name, text, expected)
  assert checked > 0, 'No source-less attributes checked'
  return checked


def check_doctests(doctest: Path) -> int:
  output = (doctest / 'output.txt').read_text(encoding='utf-8')
  summary = re.search(r'Doctest summary\s*=+\s*(\d+) tests?\s*\n\s*(\d+) failures?', output)
  assert summary is not None and int(summary[1]) == sum(map(len, EXAMPLE_GROUPS.values())) and int(summary[2]) == 0, 'Missing or failing doctests'
  blocks = re.split(r'^Document: (.+)\n-+\n', output, flags=re.MULTILINE)
  actual = {}
  phases = tuple(f' ({phase} code)' for phase in DOCTEST_PHASES)
  for index in range(1, len(blocks), 2):
    name, body = blocks[index:index + 2]
    assert name not in actual, ('Duplicate doctest document', name)
    reported = re.findall(r'^\s+1 tests? in (.+)$', body, flags=re.MULTILINE)
    assert len(reported) == len(set(reported)), ('Duplicate doctest group', name)
    groups = {group for group in reported if not group.endswith(phases)}
    lifecycle = {group.rsplit(' (', 1)[0] for group in reported if group.endswith(phases)}
    assert lifecycle <= groups, ('Orphan doctest setup or cleanup', name, lifecycle - groups)
    actual[name] = groups
  assert actual == EXAMPLE_GROUPS, ('Example coverage', actual, EXAMPLE_GROUPS)
  assert not re.search(r'\b[1-9][0-9]* failures? in (?:' + '|'.join(DOCTEST_PHASES) + ') code', output), 'Doctest setup or cleanup failed'
  return int(summary[1])


def main() -> None:
  if not __debug__:
    raise RuntimeError('Documentation checks require assertions; do not run with -O')
  site, doctest = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
  pages = {}
  for path in site.rglob('*.html'):
    page = Page()
    page.feed(path.read_text(encoding='utf-8'))
    pages[path.relative_to(site).as_posix()] = page
  result: dict[str, typing.Any] = {'api': check_api(site, pages), 'catalog': check_catalog(pages)}
  result['header_paragraphs'] = check_header_paragraphs(pages)
  check_configuration_signatures(site)
  check_links(site, pages)
  check_task_navigation(pages, sys.argv[3], sys.argv[4])
  result['release_sections'] = check_release_notes(pages)
  result['source_less_attributes'] = check_attribute_descriptions(site)
  result['doctests'] = check_doctests(doctest)
  examples = collect_examples(ROOT / 'bazi')
  check_example_blocks(examples, {name: page.code_blocks for name, page in pages.items()})
  for example in examples:
    run_example(example, ROOT)
  result['api_examples'] = [example.owner for example in examples]
  (site.parent / 'checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
  print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
  main()
