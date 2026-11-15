# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import FrozenInstanceError, asdict, fields, replace
from pathlib import Path
from typing import Any

import pytest

from bazi.defines import Dizhi, Shishen, Tiangan, Wuxing
from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase, KnowledgeEntry, KnowledgeObject, KnowledgeSource


def _data() -> dict[str, Any]:
  return {
    'schema_version': 4,
    'objects': [
      {'object_id': 'stem.ding', 'name': '丁', 'kind': 'tiangan'},
      {'object_id': 'other.ding', 'name': '丁', 'kind': 'concept'},
      {'object_id': 'wuxing.mu', 'name': '木', 'kind': 'wuxing'},
    ],
    'sources': [{'source_id': 'source', 'work': '出处'}],
    'entries': [{'claim_id': 'entry', 'objects': ['stem.ding', 'wuxing.mu'], 'text': '甲生丁。'}],
  }


def _load(data: Any, tmp_path: Path) -> KnowledgeBase:
  path = tmp_path / 'knowledge.json'
  path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  return KnowledgeBase.load(path)


def test_minimal_edit_query_reload(tmp_path: Path) -> None:
  data = _data()
  knowledge = _load(data, tmp_path)
  entry = KnowledgeEntry('entry', ('stem.ding', 'wuxing.mu'), '甲生丁。')
  assert knowledge.query() == (entry,)
  assert knowledge.query(Tiangan.丁) == knowledge.query('stem.ding') == knowledge.query(Wuxing.木)
  assert knowledge.render(entry) == '条目：entry\n甲生丁。'
  assert knowledge.sources['source'] == KnowledgeSource('source', '出处')
  data['entries'][0]['text'] = '修改后的正文。'
  edited = _load(data, tmp_path)
  assert edited.entry('entry').text == '修改后的正文。'
  assert knowledge.entry('entry') == entry and edited != knowledge
  assert hash(knowledge) == hash(_load(_data(), tmp_path))


def test_names_enums_and_ambiguity(tmp_path: Path) -> None:
  knowledge = _load(_data(), tmp_path)
  assert tuple(obj.object_id for obj in knowledge.find_objects('丁')) == ('stem.ding', 'other.ding')
  assert knowledge.find_objects('丁 ') == () and knowledge.find_objects('不存在') == ()
  with pytest.raises(ValueError, match='stem.ding, other.ding'):
    knowledge.query('丁')
  data = _data()
  data['objects'].append({'object_id': 'second.stem', 'name': '丁', 'kind': 'tiangan'})
  with pytest.raises(ValueError, match='stem.ding, second.stem'):
    _load(data, tmp_path).query(Tiangan.丁)
  bundled = KnowledgeBase.load()
  for subject in (*Tiangan, *Shishen, Wuxing.木, Wuxing.火):
    assert bundled.query(subject) == bundled.query(str(subject))
  assert bundled.query(Tiangan.JIA) == bundled.query(Tiangan.甲)
  assert bundled.query(Wuxing.WOOD) == bundled.query('wuxing.mu')
  assert bundled.query('文昌', viewpoint='XIN_XU') == (bundled.entry('shensha.wenchang.xin_xu'),)


def test_intersection_and_literal_search(tmp_path: Path) -> None:
  data = _data()
  data['entries'][0].update(
    premise='前提文字', viewpoint='CaseFold', topics=['主题', 'A'], attribution='署名',
    limits=['必要限度'], sources=['source'],
  )
  data['sources'][0]['excerpt'] = '不参与搜索的引文'
  knowledge = _load(data, tmp_path)
  for keyword in ('甲生丁', '前提', 'casefold', '主题', '署名', '必要', '木'):
    assert knowledge.search(keyword) == knowledge.query()
  for keyword in ('entry', 'stem.ding', '不参与搜索的引文', '枭印', '甲.*丁', ' 甲'):
    assert knowledge.search(keyword) == ()
  assert knowledge.search('丁', subject=Wuxing.木, topic='主题', viewpoint='CaseFold', source_id='source') == knowledge.query()
  assert knowledge.query('other.ding', topic='主题') == ()
  assert knowledge.filter_values('object_id') == ('other.ding', 'stem.ding', 'wuxing.mu')
  assert knowledge.filter_values('topic') == ('A', '主题')
  assert knowledge.filter_values('viewpoint') == ('CaseFold',)
  assert knowledge.filter_values('source_id') == ('source',)
  assert KnowledgeBase((), (), ()).filter_values('topic') == ()
  with pytest.raises(ValueError, match='Unknown topic'):
    knowledge.search('missing', topic='不存在')


def test_mixed_sources_and_render_limits(tmp_path: Path) -> None:
  data = _data()
  data['sources'][0].update(
    state='witnessed', limitations='夹注，不能当正文。', excerpt='原文：甲,丁.',
    edition='甲本', locator='第六页', url='https://example.org', supports='只支持一格', attribution='某人',
  )
  data['sources'].append({'source_id': 'unverified', 'work': '待核作品', 'state': 'unverified'})
  data['entries'][0].update(
    premise='须结合命盘', limits=['不推断事件'], viewpoint='读法一', attribution='作者',
    topics=['定义'], sources=['source', 'unverified'],
  )
  knowledge = _load(data, tmp_path)
  entry = knowledge.entry('entry')
  short = knowledge.render(entry)
  detailed = knowledge.render(entry, show_sources=True)
  for text in ('须结合命盘', '不推断事件', '读法一', '作者', '夹注，不能当正文。', 'unverified', '出处'):
    assert text in short and text in detailed
  assert '原文：甲,丁.' not in short and '原文：甲,丁.' in detailed
  for key in ('edition', 'locator', 'url', 'supports', 'attribution'):
    assert data['sources'][0][key] in detailed
  assert '原文：甲,丁.' == knowledge.sources['source'].excerpt


def test_result_order_and_immutability() -> None:
  knowledge = KnowledgeBase.load()
  reverse = KnowledgeBase(tuple(knowledge.objects.values()), tuple(knowledge.sources.values()), tuple(reversed(tuple(knowledge.entries.values()))))
  assert reverse != knowledge and knowledge != object()
  assert reverse.query('丁') == tuple(reversed(knowledge.query('丁')))
  rendered = reverse.render_subject('丁')
  positions = [rendered.index('条目：' + entry.claim_id) for entry in reverse.query('丁')]
  assert positions == sorted(positions)
  entry = knowledge.entry('legacy.shishen.SH-052')
  for identifier in entry.objects:
    assert entry in knowledge.query(identifier)
    assert entry.text in knowledge.render_subject(identifier)
  assert KnowledgeBase(tuple(knowledge.objects.values()), (), ()).render_subject('丁') == ''
  with pytest.raises(FrozenInstanceError):
    entry.text = 'changed' # type: ignore[misc]
  with pytest.raises(TypeError):
    knowledge.entries[entry.claim_id] = entry # type: ignore[index]


@pytest.mark.parametrize('bad', [None, 0, True, (), [], {}, Dizhi.子])
def test_text_inputs_reject_wrong_types(bad: Any) -> None:
  knowledge = KnowledgeBase.load()
  for call in (knowledge.entry, knowledge.find_objects, knowledge.filter_values, knowledge.search):
    with pytest.raises(TypeError):
      call(bad)
  if bad is not None:
    with pytest.raises(TypeError):
      knowledge.query(bad)
    with pytest.raises(TypeError):
      knowledge.query(topic=bad)
    with pytest.raises(TypeError):
      KnowledgeBase.load(bad)


@pytest.mark.parametrize('bad', ['', ' ', '\t\n'])
def test_blank_names_fail(bad: str) -> None:
  knowledge = KnowledgeBase.load()
  for call in (knowledge.entry, knowledge.find_objects, knowledge.filter_values, knowledge.search, knowledge.query):
    with pytest.raises(ValueError, match='non-empty'):
      call(bad)


def test_unknown_values_and_foreign_entries() -> None:
  knowledge = KnowledgeBase.load()
  for call in (knowledge.entry, knowledge.query, knowledge.filter_values):
    with pytest.raises(ValueError, match='Unknown'):
      call('missing')
  entry = knowledge.query()[0]
  with pytest.raises(ValueError, match='Foreign entry'):
    knowledge.render(replace(entry, text='changed'))
  with pytest.raises(TypeError):
    knowledge.render(None) # type: ignore[arg-type]
  for bad in (0, None, 'true'):
    with pytest.raises(TypeError):
      knowledge.render(entry, show_sources=bad) # type: ignore[arg-type]
    with pytest.raises(TypeError):
      knowledge.render_subject('丁', show_sources=bad) # type: ignore[arg-type]


@pytest.mark.parametrize('registry', ['objects', 'sources', 'entries'])
def test_duplicate_ids_and_value_order(registry: str, tmp_path: Path) -> None:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  knowledge = _load(data, tmp_path)
  data[registry].reverse()
  assert _load(data, tmp_path) != knowledge
  data[registry].append(data[registry][0])
  with pytest.raises(ValueError, match='Duplicate identifier'):
    _load(data, tmp_path)


@pytest.mark.parametrize('field,value,error', [
  ('objects', [], ValueError), ('objects', ['missing'], ValueError), ('sources', ['missing'], ValueError),
  ('objects', ['stem.ding', 'stem.ding'], ValueError), ('topics', ['同', '同'], ValueError),
  ('sources', ['source', 'source'], ValueError), ('text', '', ValueError), ('text', 42, TypeError),
  ('objects', 'stem.ding', TypeError), ('objects', [None], TypeError),
  ('premise', None, TypeError), ('topics', [1], TypeError), ('limits', [''], ValueError),
  ('unknown', 'value', ValueError),
])
def test_entry_input_validation(field: str, value: Any, error: type[Exception], tmp_path: Path) -> None:
  data = _data()
  data['entries'][0][field] = value
  with pytest.raises(error):
    _load(data, tmp_path)


def test_record_fields_and_typed_registries() -> None:
  records = (KnowledgeObject('object', 'concept', '对象'), KnowledgeSource('source', '作品'), KnowledgeEntry('entry', ('object',), '正文'))
  for record in records:
    for field in fields(record):
      with pytest.raises(TypeError):
        replace(record, **{field.name: object()}) # type: ignore[arg-type]
  with pytest.raises(ValueError):
    KnowledgeObject('object', 'invalid', '对象')
  with pytest.raises(ValueError):
    KnowledgeSource('source', '作品', state='invalid') # type: ignore[arg-type]
  for registry in range(3):
    args: list[Any] = [(), (), ()]
    args[registry] = [records[registry]]
    with pytest.raises(TypeError):
      KnowledgeBase(*args)
    args[registry] = ('wrong type',)
    with pytest.raises(TypeError):
      KnowledgeBase(*args)
  with pytest.raises(TypeError):
    KnowledgeEntry('entry', ['object'], '正文') # type: ignore[arg-type]


@pytest.mark.parametrize('data,error', [
  ([], TypeError), ({}, ValueError),
  ({**_data(), 'schema_version': True}, ValueError), ({**_data(), 'schema_version': 3}, ValueError),
  ({**_data(), 'objects': {}}, TypeError), ({**_data(), 'objects': [None]}, TypeError),
  ({**_data(), 'entries': [{'objects': ['stem.ding'], 'text': '正文'}]}, ValueError),
])
def test_json_structure(data: Any, error: type[Exception], tmp_path: Path) -> None:
  with pytest.raises(error):
    _load(data, tmp_path)


def test_duplicate_keys_and_parse_position(tmp_path: Path) -> None:
  path = tmp_path / 'bad.json'
  path.write_text('{"objects": [], "objects": []}', encoding='utf-8')
  with pytest.raises(ValueError, match='Duplicate JSON key'):
    KnowledgeBase.load(path)
  path.write_text('{\n "broken": }', encoding='utf-8')
  with pytest.raises(json.JSONDecodeError) as caught:
    KnowledgeBase.load(path)
  assert caught.value.lineno == 2
  with pytest.raises(FileNotFoundError):
    KnowledgeBase.load(tmp_path / 'missing.json')


def test_optional_fields_round_trip(tmp_path: Path) -> None:
  original = KnowledgeBase.load()
  data = {'schema_version': 4, **{
    name: [asdict(value) for value in getattr(original, name).values()]
    for name in ('objects', 'sources', 'entries')
  }}
  assert _load(data, tmp_path) == original
