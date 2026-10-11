# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import importlib.util
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

import bazi
from bazi.defines import Dizhi, Shishen, Tiangan
from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase, KnowledgeSource, object_id


def test_all_sources_and_future_sources_are_accessible_without_mirrors(tmp_path: Path) -> None:
  k = KnowledgeBase.load()
  assert set(k.sources) == {
    'editorial', 'yuanhai_ziping_relations', 'yuanhai_ziping_stem_table',
    'yuanhai_ziping_stem_symbols_p69', 'yuanhai_ziping_stem_symbols_p70',
    'mingli_tanyuan_stem_basics', 'mingli_tanyuan_shishen_definitions',
    'repository_guoyin_variants', 'repository_wuxing_relations',
  }
  # Both an unused source and a newly referenced source must survive reload.
  unused = replace(k.sources['yuanhai_ziping_relations'], source_id='future.unused', lineage='future.lineage', text_layer='zhushi')
  used = replace(unused, source_id='future.used')
  lamp = replace(k.entry('tiangan.ding.lamp_symbol'), sources=('future.used',))
  edited = KnowledgeBase(
    tuple(k.objects.values()), tuple(k.contexts.values()),
    (*k.sources.values(), unused, used),
    tuple(lamp if entry.claim_id == lamp.claim_id else entry for entry in k.entries.values()),
  )
  path = tmp_path / 'edited.json'
  path.write_text(edited.export_json(), encoding='utf-8')
  loaded = KnowledgeBase.load(path)
  assert len(loaded.sources) == 11
  for source_id, record in edited.sources.items():
    assert isinstance(loaded.sources[source_id], KnowledgeSource)
    assert loaded.sources[source_id] == record
    assert loaded.query(source_id=source_id, include_reference_only=True) == tuple(entry for entry in edited.entries.values() if source_id in entry.sources)
    for field in fields(record):
      with pytest.raises(TypeError):
        replace(record, **{field.name: object()}) # type: ignore[arg-type]
  assert loaded.query(source_id='future.unused', include_reference_only=True) == ()
  assert loaded.query(source_id='future.used', include_reference_only=True) == (lamp,)
  assert '文本层：zhushi；谱系：future.lineage' in loaded.render(lamp)
  with pytest.raises(FrozenInstanceError):
    loaded.sources['future.used'].work = 'changed' # type: ignore[misc]
  with pytest.raises(TypeError):
    loaded.sources['future.used'] = unused # type: ignore[index]


def test_removed_modules_are_absent_from_source_and_registration() -> None:
  for name in ('descriptions', 'interpreter'):
    assert name not in bazi.__all__
    assert importlib.util.find_spec('bazi.' + name) is None
    with pytest.raises(AttributeError):
      getattr(bazi, name)
  assert not hasattr(KnowledgeBase, '_render')
  assert DEFAULT_SOURCE_PATH == Path(bazi.knowledge.__file__).with_name('knowledge_data.json')


def test_object_ids_preserve_aliases_and_reject_unrelated_values() -> None:
  for subject in (*Tiangan, *Shishen):
    identifier = object_id(subject)
    record = KnowledgeBase.load().objects[identifier]
    assert record.name == str(subject)
    assert record.kind == ('tiangan' if isinstance(subject, Tiangan) else 'shishen')
  assert object_id(Tiangan.甲) == object_id(Tiangan.JIA) == 'tiangan.jia'
  assert object_id(Shishen.食神) == object_id(Shishen.SHISHEN) == 'shishen.shishen'
  for bad in ('甲', 0, None, Dizhi.子):
    with pytest.raises(TypeError, match='Expected Tiangan | Shishen'):
      object_id(bad) # type: ignore[arg-type]


def test_subject_projection_keeps_subject_roles_order_and_metadata_distinct() -> None:
  k = KnowledgeBase.load()
  relation = k.entry('legacy.shishen.SH-052')
  assert relation in k.query(object_id='shishen.qisha', include_reference_only=True)
  assert relation.text not in k.render_subject('shishen.qisha', include_reference_only=True)
  assert relation.text in k.render_subject('shishen.shishen', include_reference_only=True)
  # Corpus order is deliberately different from legacy placement order.
  reversed_k = KnowledgeBase(
    tuple(k.objects.values()), tuple(k.contexts.values()), tuple(k.sources.values()),
    tuple(reversed(tuple(k.entries.values()))),
  )
  text = reversed_k.render_subject('tiangan.ding', include_reference_only=True, show_sources=True)
  selected = reversed_k.query(object_id='tiangan.ding', include_reference_only=True)
  assert tuple(text.index('条目：' + entry.claim_id + '；') for entry in selected) == tuple(sorted(text.index('条目：' + entry.claim_id + '；') for entry in selected))
  assert tuple(entry.legacy for entry in selected) == tuple(reversed(tuple(entry.legacy for entry in k.query(object_id='tiangan.ding', include_reference_only=True))))
  for identifier in ('wuxing.mu', 'wuxing.huo', 'shensha.guoyin'):
    for entry in k.query(object_id=identifier, include_reference_only=True):
      assert entry.text in k.render_subject(identifier, include_reference_only=True)
  assert k.render_subject('shishen.jiecai') == ''
  assert KnowledgeBase.from_json(k.export_json(())).render_subject('tiangan.ding') == ''
  assert hash(selected) == hash(reversed_k.query(object_id='tiangan.ding', include_reference_only=True))


@pytest.mark.parametrize('bad_flag', [None, 0, 1, 'true', ()])
def test_subject_display_public_boundaries(bad_flag: object) -> None:
  k = KnowledgeBase.load()
  for identifier in ('tiangan.ding', 'shishen.jiecai'):
    with pytest.raises(TypeError, match='Expected bool'):
      k.render_subject(identifier, show_sources=bad_flag) # type: ignore[arg-type]
    with pytest.raises(TypeError, match='Expected bool'):
      k.render_subject(identifier, include_reference_only=bad_flag) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    k.render_subject(Tiangan.丁) # type: ignore[arg-type]
  with pytest.raises(ValueError, match='Unknown object_id'):
    k.render_subject('missing')
  with pytest.raises(TypeError):
    k.render_subject('tiangan.ding', True) # type: ignore[call-arg]


def test_render_verdict_is_display_only_and_does_not_change_eligibility() -> None:
  k = KnowledgeBase.load()
  reference = k.entry('editorial.shishen.zhengguan.legal_trouble')
  before = k.export_json()
  rendered = k.render(reference, manual_context=True, premise_verdict='SATISFIED')
  assert '前提判别：SATISFIED' in rendered
  assert '输出资格：reference_only' in rendered and '仅供参考' in rendered
  assert '也许' in rendered and 'Does not establish a classical rule or real-world prediction.' in rendered
  assert '人工给定情境' not in rendered
  assert reference not in k.query()
  assert k.export_json() == before
  for value in (1, False, (), object()):
    with pytest.raises(TypeError, match='Expected str | None'):
      k.render(reference, premise_verdict=value) # type: ignore[arg-type]
