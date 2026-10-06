# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import FrozenInstanceError, asdict, fields, replace
from pathlib import Path
from typing import Any, get_args, get_origin

import pytest

from bazi.defines import Shishen, Tiangan
from bazi.descriptions import DescriptionSource
from bazi.interpreter import Interpreter
from bazi.knowledge import (
  KnowledgeBase, KnowledgeObject, KnowledgeRole, KnowledgeRelation, KnowledgeEntry,
  LegacyDescription,
)


KNOWLEDGE_BASE = KnowledgeBase.load()


def _ids(entries: tuple[KnowledgeEntry, ...]) -> tuple[str, ...]:
  return tuple(entry.claim_id for entry in entries)


def test_frozen_legacy_oracle_conserves_every_claim_and_source() -> None:
  fixture = Path(__file__).with_name('data') / 'description_legacy_baseline.json'
  baseline = json.loads(fixture.read_text(encoding='utf-8'))
  actual: list[dict[str, Any]] = []
  for subjects in (Shishen, Tiangan):
    for subject in subjects:
      selected = (
        Interpreter.query_shishen(subject, include_reference_only=True) if isinstance(subject, Shishen)
        else Interpreter.query_tiangan(subject, include_reference_only=True)
      )
      for field, claims in selected.items():
        actual.extend({'subject_kind': subjects.__name__, 'subject': str(subject), 'field': field, 'claim': asdict(claim)} for claim in claims)
  normalized = json.loads(json.dumps(actual, default=lambda value: value.value))
  assert normalized == baseline['rows']
  for source_id, expected in baseline['sources'].items():
    record = asdict(Interpreter.query_source(DescriptionSource(source_id)))
    assert json.loads(json.dumps(record, default=lambda value: value.value)) == expected
  old_ids = {row['claim']['claim_id'] for row in baseline['rows']}
  assert len(old_ids) == 291
  assert {entry.claim_id for entry in KNOWLEDGE_BASE.entries.values() if entry.legacy is not None} == old_ids
  assert set(_ids(KNOWLEDGE_BASE.query())) == {
    row['claim']['claim_id'] for row in baseline['rows'] if row['claim']['output'] == 'default'
  }
  assert len(KNOWLEDGE_BASE.entries) == 295


def test_real_queries_intersect_roles_topics_contexts_and_sources() -> None:
  k = KNOWLEDGE_BASE
  assert _ids(k.query(object_id='tiangan.ding', topic='历史象', include_reference_only=True)) == ('tiangan.ding.lamp_symbol',)
  assert _ids(k.query(object_id='tiangan.ding', topic='定义', include_reference_only=True)) == ('tiangan.ding.definition',)
  assert _ids(k.query(object_id='tiangan.ding', topic='性格', include_reference_only=True)) == (
    'legacy.tiangan.ding.personality', 'legacy.tiangan.ding.weak_state', 'legacy.tiangan.ding.emotional_expression',
  )
  assert _ids(k.query(topic='历史象', source_id='yuanhai_ziping_stem_symbols_p70', include_reference_only=True)) == (
    'tiangan.ding.lamp_symbol', 'tiangan.wu.wall_symbol', 'tiangan.xin.jewel_symbol', 'tiangan.ren.river_symbol',
  )
  assert _ids(k.query(object_id='shishen.qisha', topic='组合关系', include_reference_only=True)) == ('legacy.shishen.SH-052',)
  assert _ids(k.query(object_id='concept.cai', include_reference_only=True)) == ('legacy.shishen.SH-052',)
  assert _ids(k.query(object_id='shishen.shishen', topic='组合关系', include_reference_only=True)) == (
    'legacy.shishen.SH-052', 'legacy.shishen.SH-066',
  )
  assert _ids(k.query(object_id='shishen.pianyin', context_id='shishen.pianyin_favorable_or_balanced', topic='性格', include_reference_only=True)) == ('legacy.shishen.SH-199',)
  assert 'legacy.shishen.SH-011' in _ids(k.query(object_id='shishen.bijian', applicability='unresolved', include_reference_only=True))
  assert _ids(k.query(object_id='tiangan.geng', topic='性格', time_scope='行运', applicability='described', include_reference_only=True)) == ('legacy.tiangan.geng.regulated_transit',)
  assert _ids(k.query(object_id='shensha.guoyin', viewpoint='MODERN', include_reference_only=True)) == ('shensha.guoyin.modern',)
  assert _ids(k.query(object_id='shensha.guoyin', viewpoint='WUXING_JINGJI', include_reference_only=True)) == ('shensha.guoyin.wuxing_jingji',)
  assert _ids(k.query(object_id='wuxing.mu', topic='基础关系', include_reference_only=True)) == ('wuxing.mu_sheng_huo', 'wuxing.jin_ke_mu')
  assert k.query(object_id='shishen.jiecai') == ()
  assert k.query(object_id='tiangan.ding', source_id='yuanhai_ziping_stem_table', include_reference_only=True) == ()
  assert k.query(object_id='wuxing.mu') == ()
  assert k.query(applicability='described') == ()
  assert _ids(k.query(source_id='yuanhai_ziping_stem_symbols_p70')) == (
    'tiangan.ding.definition', 'tiangan.wu.definition', 'tiangan.ji.definition',
    'tiangan.geng.definition', 'tiangan.xin.definition', 'tiangan.ren.definition', 'tiangan.gui.definition',
  )


def test_premises_are_organized_without_inventing_rules() -> None:
  k = KNOWLEDGE_BASE
  old = k.entry('legacy.shishen.SH-011')
  assert old.applicability == 'unresolved' and old.premise == ''
  assert old.legacy is not None and old.legacy.field == 'in_good_status'
  assert '力量不过强' in old.legacy.field_premise
  compound = k.entry('legacy.shishen.SH-199')
  assert compound.applicability == 'described'
  assert compound.premise == '偏印为喜用或状态良好（不过旺、不受刑克冲害）'
  assert compound.source_state == 'unverified' and compound.output == 'reference_only'
  transit = k.entry('legacy.tiangan.geng.regulated_transit')
  assert transit.contexts == ('tiangan.geng_regulated_transit',)
  context = k.contexts[transit.contexts[0]]
  assert context.time_scope == '行运'
  assert context.limits == (
    '有制有化尚未定义，不据基础生克关系认定成立。',
    '后天有教养是盘外前提，不能从命盘查表还原。',
  )
  assert '后天有教养' in transit.premise
  relation = k.entry('legacy.shishen.SH-052')
  assert next(role.object_id for role in relation.roles if role.name == '财') == 'concept.cai'
  assert relation.applicability == 'unresolved'
  assert relation.relations[1].text == '食神又能克制七杀'
  assert k.entry('editorial.shishen.shishen.anxiety_insomnia').applicability == 'unresolved'
  assert k.entry('editorial.shishen.zhengguan.legal_trouble').applicability == 'unresolved'
  for entry in k.entries.values():
    assert not {'in_good_status', 'in_bad_status'} & set(entry.topics)
    if entry.legacy is None:
      assert entry.output == 'reference_only' and entry.source_state == 'repository_attributed'
      assert all(k.sources[source].text_layer == 'editorial' for source in entry.sources)
  assert '#194' in ' '.join(k.entry('shensha.guoyin.wuxing_jingji').limits)


def test_reference_samples_preserve_relation_and_lookup_boundaries() -> None:
  k = KNOWLEDGE_BASE
  for claim_id, text in (('wuxing.mu_sheng_huo', '木生火。'), ('wuxing.jin_ke_mu', '金克木。')):
    entry = k.entry(claim_id)
    assert entry.text == text
    assert '不证明命盘中的有效生克或流转' in k.render(entry, show_sources=False)
  modern = k.entry('shensha.guoyin.modern')
  assert '含禄，偏移 +8' in modern.text
  assert '表值与四柱查法的支持来源分开' in k.render(modern, show_sources=False)
  assert '守照身命表述不等于查四柱地支' in k.render(modern, show_sources=False)
  alternative = k.entry('shensha.guoyin.wuxing_jingji')
  assert '含禄，偏移 +7' in alternative.text
  assert '今人【注释】，不混作【原文】的断言' in k.render(alternative, show_sources=False)
  assert '#194' in k.render(alternative, show_sources=False)
  assert '不等同于偏印与食神共现' in k.render(k.entry('legacy.shishen.SH-066'), show_sources=False)
  assert '身弱与克太多的判据尚未定义' in k.render(k.entry('legacy.tiangan.ding.weak_state'), show_sources=False)
  relation = k.render(k.entry('legacy.shishen.SH-052'), show_sources=False)
  assert '财未具体分为正财或偏财' in relation
  assert '不表示有效制杀已成立' in relation


def test_migrated_legacy_field_premises_are_conserved() -> None:
  # Column wording from the pre-migration descriptions module.
  premises = {
    'in_good_status': '当十神处于力量不过强，状态良好的时候（如不被冲、克，也不过旺/为命主喜用时），这个十神代表的特征。',
    'in_bad_status': '当十神过旺（如在天干和地支藏干中出现3次）或被其他元素冲克（如处于“绝”一柱/受刑、穿、克...）的时候，这个十神代表的特征。',
  }
  for entry in KNOWLEDGE_BASE.entries.values():
    if entry.legacy is not None:
      assert entry.legacy.field_premise == premises.get(entry.legacy.field, ''), entry.claim_id


def test_edit_validate_query_render_export_reload(tmp_path: Path) -> None:
  data = json.loads(KNOWLEDGE_BASE.export_json())
  entry = next(value for value in data['entries'] if value['claim_id'] == 'legacy.tiangan.geng.regulated_transit')
  entry['limits'] = ['编辑者另记的适用限度。']
  entry['exceptions'] = ['编辑者另记的例外。']
  source = tmp_path / 'edited.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  edited = KnowledgeBase.load(source)
  selected = edited.query(object_id='tiangan.geng', time_scope='行运', topic='性格', include_reference_only=True)
  assert _ids(selected) == ('legacy.tiangan.geng.regulated_transit',)
  rendered = edited.render(selected[0], manual_context=True)
  for text in ('后天有教养', '有制有化尚未定义', '来源尚未核实', '命盘适用性未判断', '人工给定情境', '编辑者另记的例外。', '编辑者另记的适用限度。'):
    assert text in rendered
  exported = edited.export_json(selected)
  restored = KnowledgeBase.from_json(exported)
  assert restored.query(object_id='tiangan.geng', time_scope='行运', include_reference_only=True) == selected
  assert restored.render(selected[0], manual_context=True) == rendered
  assert restored.export_json() == exported
  assert KNOWLEDGE_BASE.entry(selected[0].claim_id).limits == ()
  default = KnowledgeBase.load()
  assert default.export_json() == KNOWLEDGE_BASE.export_json()
  assert KnowledgeBase.from_json(default.export_json()).entries == default.entries
  symbolic = default.query(topic='历史象', include_reference_only=True)
  selection = KnowledgeBase.from_json(default.export_json(symbolic))
  assert selection.query(topic='历史象', include_reference_only=True) == symbolic
  assert selection.sources == default.sources
  empty = KnowledgeBase.from_json(default.export_json(()))
  assert empty.query(object_id='tiangan.ding') == ()


def test_render_metadata_selection_and_limits() -> None:
  k = KNOWLEDGE_BASE
  definition = k.render(k.entry('shishen.shishen.definition'))
  assert '仅供参考' not in definition and '未判断' not in definition
  assert '支持范围：' in definition and '局限：' in definition
  assert '文本层：baiwen' in definition
  assert '生我者為正印偏印' in definition
  assert '文字关系：讨论对象→七杀' in k.render(k.entry('legacy.shishen.SH-052'))
  historical = k.entry('tiangan.ding.lamp_symbol')
  assert '仅供参考' in k.render(historical)
  assert '来源尚未核实' not in k.render(historical)
  text = k.render(k.entry('legacy.shishen.SH-011'), show_sources=False)
  assert '前提待梳理' in text and '命盘适用性未判断' in text
  assert '旧栏目前提（待梳理；未作为判据）：当十神处于力量不过强' in text
  assert '条目：' not in text and '来源：' not in text
  legacy_detail = k.render(k.entry('legacy.shishen.SH-011'))
  assert '旧栏目前提（待梳理；未作为判据）：当十神处于力量不过强' in legacy_detail
  assert '如不被冲、克，也不过旺/为命主喜用时' in legacy_detail
  assert '来源状态：repository_attributed' in k.render(k.entry('shensha.guoyin.modern'))
  for entry in k.entries.values():
    if entry.legacy is not None and entry.legacy.field_premise:
      assert entry.legacy.field_premise in k.render(entry, show_sources=False)


def test_registries_and_results_are_transitively_immutable() -> None:
  k = KNOWLEDGE_BASE
  for registry in (k.objects, k.contexts, k.sources, k.entries):
    with pytest.raises(TypeError):
      registry['invalid'] = object() # type: ignore[index] # Immutable public mappings.
    assert hash(registry) == hash(registry)
  for name in ('objects', 'contexts', 'sources', 'entries'):
    with pytest.raises(AttributeError):
      setattr(k, name, {})
  result = k.query(object_id='tiangan.ding', include_reference_only=True)
  assert isinstance(result, tuple)
  with pytest.raises(FrozenInstanceError):
    result[0].text = 'changed' # type: ignore[misc]
  with pytest.raises(FrozenInstanceError):
    result[0].roles[0].name = 'changed' # type: ignore[misc]
  assert hash(result) == hash(k.query(object_id='tiangan.ding', include_reference_only=True))


@pytest.mark.parametrize('dimension', ['object_id', 'context_id', 'topic', 'source_id', 'viewpoint', 'applicability', 'time_scope'])
def test_filters_fail_for_typos_and_invalid_types(dimension: str) -> None:
  for value, error in (('typo', ValueError), ('', ValueError), (1, TypeError)):
    with pytest.raises(error):
      KNOWLEDGE_BASE.query(**{dimension: value}) # type: ignore[arg-type]
  with pytest.raises(ValueError, match='Unknown topic'):
    KNOWLEDGE_BASE.query(object_id='shishen.jiecai', topic='typo')


@pytest.mark.parametrize('value', [1, None, 'yes'])
def test_boolean_and_lookup_boundaries(value: object) -> None:
  k = KNOWLEDGE_BASE
  with pytest.raises(TypeError):
    k.query(include_reference_only=value) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    k.render(k.entry('tiangan.ding.definition'), show_sources=value) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    k.render(k.entry('tiangan.ding.definition'), manual_context=value) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    k.render(value) # type: ignore[arg-type]
  with pytest.raises(ValueError if isinstance(value, str) else TypeError):
    k.entry(value) # type: ignore[arg-type]
  if value is not None:
    with pytest.raises(TypeError):
      KnowledgeBase.load(value) # type: ignore[arg-type]
  with pytest.raises(ValueError if isinstance(value, str) else TypeError):
    KnowledgeBase.from_json(value) # type: ignore[arg-type]


def test_unknown_and_foreign_selections_fail() -> None:
  k = KNOWLEDGE_BASE
  with pytest.raises(ValueError, match='Unknown claim'):
    k.entry('missing')
  entry = k.entry('tiangan.ding.definition')
  foreign = replace(entry, text='Another text.')
  with pytest.raises(ValueError, match='Foreign entry'):
    k.render(foreign)
  with pytest.raises(ValueError, match='Foreign entry'):
    k.export_json((foreign,))
  with pytest.raises(ValueError, match='Duplicate selection'):
    k.export_json((entry, entry))
  with pytest.raises(TypeError):
    k.export_json([entry]) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    k.export_json((object(),)) # type: ignore[arg-type]


def test_public_value_constructors_validate_all_declared_fields() -> None:
  entry = KNOWLEDGE_BASE.entry('legacy.shishen.SH-052')
  records = (
    KNOWLEDGE_BASE.objects['tiangan.ding'], entry.roles[0], entry.relations[0],
    KNOWLEDGE_BASE.contexts['tiangan.geng_regulated_transit'],
    KNOWLEDGE_BASE.sources['editorial'], entry.legacy, entry,
  )
  for record in records:
    assert record is not None
    for field in fields(record):
      with pytest.raises(TypeError):
        replace(record, **{field.name: object()}) # type: ignore[arg-type]
      if get_origin(field.type) is tuple:
        with pytest.raises(TypeError):
          replace(record, **{field.name: (object(),)}) # type: ignore[arg-type]
        if get_args(field.type)[0] is str:
          with pytest.raises(ValueError):
            replace(record, **{field.name: ('',)}) # type: ignore[arg-type]
      if field.type is str and field.name not in ('premise', 'field_premise'):
        with pytest.raises(ValueError):
          replace(record, **{field.name: ''}) # type: ignore[arg-type]


@pytest.mark.parametrize('changes', [
  {'roles': ()}, {'topics': ()},
  {'roles': (KnowledgeRole('same', 'tiangan.ding'), KnowledgeRole('same', 'tiangan.jia'))},
  {'relations': (KnowledgeRelation('missing', '讨论对象', 'relationship'),)},
  {'topics': ('定义', '定义')}, {'contexts': ('x', 'x')}, {'sources': ('x', 'x')},
  {'premise': 'Unexpected premise'}, {'contexts': ('legacy.chart_context',)},
  {'applicability': 'described', 'premise': ''},
  {'source_state': 'unverified'}, {'sources': ()},
  {'output': 'default', 'applicability': 'unresolved'},
  {'source_state': 'editorial'}, {'applicability': 'typo'}, {'source_state': 'typo'}, {'output': 'typo'},
  {'legacy': LegacyDescription('tiangan.ding', 'general', 0, ('chart_context_required',), '')},
  {'legacy': LegacyDescription('tiangan.ding', 'general', 0, (), 'Unexpected legacy field premise')},
])
def test_entry_cross_field_invariants(changes: dict[str, Any]) -> None:
  with pytest.raises(ValueError):
    replace(KNOWLEDGE_BASE.entry('tiangan.ding.definition'), **changes)


def test_constructor_value_boundaries() -> None:
  with pytest.raises(ValueError):
    KnowledgeObject('object', 'typo', 'Object')
  with pytest.raises(ValueError):
    replace(KNOWLEDGE_BASE.sources['editorial'], text_layer='typo')
  with pytest.raises(ValueError):
    replace(KNOWLEDGE_BASE.sources['editorial'], state='typo') # type: ignore[arg-type]
  legacy = KNOWLEDGE_BASE.entry('legacy.shishen.SH-011').legacy
  assert legacy is not None
  with pytest.raises(TypeError):
    replace(legacy, ordinal=True)
  with pytest.raises(ValueError):
    replace(legacy, ordinal=-1)
  with pytest.raises(ValueError):
    replace(legacy, conditions=('typo',))


@pytest.mark.parametrize('kind', ['objects', 'contexts', 'sources', 'entries'])
def test_duplicate_registry_ids_are_rejected(kind: str) -> None:
  data = json.loads(KNOWLEDGE_BASE.export_json())
  data[kind].append(data[kind][0])
  with pytest.raises(ValueError, match='Duplicate identifier'):
    KnowledgeBase.from_json(json.dumps(data))


@pytest.mark.parametrize('mutation, message', [
  ('object', 'Unknown object'), ('context', 'Unknown context'), ('source', 'Unknown source'),
  ('state', 'Witness state differs'), ('lineage', 'independent lineages'),
  ('legacy-object', 'Legacy object is missing'), ('legacy-field', 'Unsupported legacy field'),
  ('legacy-placement', 'Duplicate legacy placement'), ('concept-legacy', 'Unsupported legacy field'),
])
def test_corpus_reference_and_policy_integrity(mutation: str, message: str) -> None:
  data = json.loads(KNOWLEDGE_BASE.export_json())
  entry = data['entries'][0]
  if mutation == 'object':
    entry['roles'][0]['object_id'] = 'missing'
  elif mutation == 'context':
    entry.update(applicability='described', premise='A premise', contexts=['missing'], output='reference_only')
  elif mutation == 'source':
    entry['sources'][0] = 'missing'
  elif mutation == 'state':
    data['sources'][1]['state'] = 'editorial'
  elif mutation == 'lineage':
    for source in data['sources']:
      source['lineage'] = 'same'
  elif mutation == 'legacy-object':
    entry['legacy']['object_id'] = 'tiangan.ding'
  elif mutation == 'legacy-field':
    entry['legacy']['field'] = 'personality'
  elif mutation == 'concept-legacy':
    entry['roles'][0]['object_id'] = 'concept.cai'
    entry['legacy']['object_id'] = 'concept.cai'
  else:
    extra = json.loads(json.dumps(entry))
    extra['claim_id'] = 'extra'
    data['entries'].append(extra)
  with pytest.raises(ValueError, match=message):
    KnowledgeBase.from_json(json.dumps(data))


def test_json_shape_and_optimized_public_boundary_contract() -> None:
  for text in ('{"schema_version":1,"schema_version":1}', '[1]', '{}', '{bad json'):
    with pytest.raises((TypeError, ValueError)):
      KnowledgeBase.from_json(text)
  for key in ('objects', 'contexts', 'sources', 'entries'):
    data = json.loads(KNOWLEDGE_BASE.export_json())
    data[key] = {}
    with pytest.raises(TypeError, match='JSON array'):
      KnowledgeBase.from_json(json.dumps(data))
  for version in (True, '1', 2):
    data = json.loads(KNOWLEDGE_BASE.export_json())
    data['schema_version'] = version
    with pytest.raises(ValueError, match='schema version'):
      KnowledgeBase.from_json(json.dumps(data))
  for bad in (1, {}, {'object_id': 'x', 'kind': 'concept', 'name': 'X', 'extra': 'x'}):
    data = json.loads(KNOWLEDGE_BASE.export_json())
    data['objects'][0] = bad
    with pytest.raises((TypeError, ValueError)):
      KnowledgeBase.from_json(json.dumps(data))
  data = json.loads(KNOWLEDGE_BASE.export_json())
  data['entries'][0]['roles'] = {}
  with pytest.raises(TypeError, match='JSON array'):
    KnowledgeBase.from_json(json.dumps(data))
  with pytest.raises(TypeError):
    KnowledgeBase([], (), (), ()) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    KnowledgeBase((object(),), (), (), ()) # type: ignore[arg-type]
  with pytest.raises(ValueError):
    KnowledgeBase.from_json('')


def test_witnessed_zhushi_is_a_distinct_text_layer() -> None:
  source = replace(KNOWLEDGE_BASE.sources['yuanhai_ziping_relations'], source_id='annotation', text_layer='zhushi')
  k = KnowledgeBase((), (), (source,), ())
  assert k.sources['annotation'].text_layer == 'zhushi'
  assert KnowledgeBase.from_json(k.export_json()).sources == k.sources
