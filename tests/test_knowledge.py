# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import FrozenInstanceError, asdict, fields, replace
from pathlib import Path
from typing import Any, get_args, get_origin

import pytest

from bazi.defines import Shishen, Tiangan
from bazi.knowledge import (
  KnowledgeBase, KnowledgeObject, KnowledgeRole, KnowledgeRelation, KnowledgeEntry,
  LegacyDescription, KnowledgeContext, object_id,
)

from knowledge_additions import AUXILIARY_SOURCE_IDS, AUXILIARY_ENTRY_IDS, AUXILIARY_WITNESSED_IDS


KNOWLEDGE_BASE = KnowledgeBase.load()
LEDGER: dict[str, Any] = json.loads(
  (Path(__file__).with_name('data') / 'corpus_allowed_changes.json').read_text(encoding='utf-8')
)
ALLOWED_CHANGES: dict[str, dict[str, object]] = LEDGER['allowed_changes']
TRANSLATED_ATTRIBUTION: dict[str, str] = LEDGER['translated']['attribution']
TRANSLATED_SOURCES: dict[str, dict[str, list[str]]] = LEDGER['translated']['sources']


def _ids(entries: tuple[KnowledgeEntry, ...]) -> tuple[str, ...]:
  return tuple(entry.claim_id for entry in entries)


def _discovery_knowledge() -> KnowledgeBase:
  original = KNOWLEDGE_BASE.entry('tiangan.ding.definition')
  default = replace(
    original,
    claim_id='custom.default',
    text='default body',
    roles=(KnowledgeRole('subject', 'concept.one'),),
    relations=(),
    topics=('shared',),
    attribution='known attribution',
    viewpoint='default_view',
    exceptions=(),
    limits=(),
    legacy=None,
  )
  reference = replace(
    default,
    claim_id='custom.reference',
    text='reference body',
    roles=(KnowledgeRole('subject', 'concept.two'),),
    topics=('shared', 'reference_topic'),
    applicability='described',
    premise='explicit premise',
    contexts=('context.used',),
    viewpoint='reference_view',
    output='reference_only',
  )
  sources = tuple(KNOWLEDGE_BASE.sources[key] for key in original.sources)
  return KnowledgeBase(
    (
      KnowledgeObject('concept.one', 'concept', '同名'),
      KnowledgeObject('concept.two', 'concept', '同名'),
      KnowledgeObject('concept.unused', 'concept', 'Unused'),
    ),
    (
      KnowledgeContext('context.used', '情境标签专用串', 'used.scope', ()),
      KnowledgeContext('context.unused', '未引用情境', 'unused.scope', ()),
    ),
    tuple(replace(source, work='来源全文专用串', excerpt='来源全文专用串') for source in sources) +
    (replace(sources[0], source_id='source.unused'),),
    (default, reference),
  )


def test_find_objects_keeps_duplicates_in_order() -> None:
  knowledge = _discovery_knowledge()
  assert knowledge.find_objects('同名') == (knowledge.objects['concept.one'], knowledge.objects['concept.two'])
  assert knowledge.find_objects('Unused') == (knowledge.objects['concept.unused'],)
  assert knowledge.find_objects('unused') == ()
  assert knowledge.find_objects(' 同名 ') == ()
  assert knowledge.find_objects('无此名称') == ()
  assert KnowledgeBase((), (), (), ()).find_objects('同名') == ()
  with pytest.raises(FrozenInstanceError):
    knowledge.find_objects('同名')[0].name = 'changed' # type: ignore[misc]


@pytest.mark.parametrize('value', [None, 1, True, '', '   '])
def test_discovery_text_inputs_fail_immediately(value: object) -> None:
  knowledge = _discovery_knowledge()
  error = ValueError if isinstance(value, str) else TypeError
  with pytest.raises(error):
    knowledge.find_objects(value) # type: ignore[arg-type]
  with pytest.raises(error):
    knowledge.search(value) # type: ignore[arg-type]
  with pytest.raises(error):
    knowledge.filter_values(value) # type: ignore[arg-type]


def test_filter_values_cover_every_domain() -> None:
  for knowledge in (KNOWLEDGE_BASE, _discovery_knowledge(), KnowledgeBase((), (), (), ())):
    expected = {
      'object_id': tuple(sorted(knowledge.objects)),
      'context_id': tuple(sorted(knowledge.contexts)),
      'source_id': tuple(sorted(knowledge.sources)),
      'topic': tuple(sorted({topic for entry in knowledge.entries.values() for topic in entry.topics})),
      'viewpoint': tuple(sorted({entry.viewpoint for entry in knowledge.entries.values()})),
      'applicability': ('described', 'unconditional', 'unresolved'),
      'time_scope': tuple(sorted({context.time_scope for context in knowledge.contexts.values()})),
    }
    for dimension, values in expected.items():
      assert knowledge.filter_values(dimension) == values
      for value in values:
        assert isinstance(knowledge.query(**{dimension: value}, include_reference_only=True), tuple) # type: ignore[arg-type]
  custom = _discovery_knowledge()
  assert 'reference_topic' in custom.filter_values('topic')
  assert custom.query(topic='reference_topic') == ()
  assert _ids(custom.query(topic='reference_topic', include_reference_only=True)) == ('custom.reference',)
  assert custom.query(object_id='concept.unused', time_scope='unused.scope', source_id='source.unused', include_reference_only=True) == ()
  for dimension in ('unknown', 'include_reference_only'):
    with pytest.raises(ValueError, match='Unknown dimension'):
      custom.filter_values(dimension)


@pytest.mark.parametrize('field', ['text', 'premise', 'attribution', 'topics', 'viewpoint', 'exceptions', 'limits', 'object_name'])
def test_search_matches_fields_casefolded(field: str) -> None:
  original = _discovery_knowledge()
  reference = original.entry('custom.reference')
  objects = tuple(original.objects.values())
  if field == 'object_name':
    objects = tuple(replace(obj, name='Straße丁火') if obj.object_id == 'concept.two' else obj for obj in objects)
  else:
    value: Any = ('Straße丁火',) if field in ('topics', 'exceptions', 'limits') else 'Straße丁火'
    reference = replace(reference, **{field: value})
  knowledge = KnowledgeBase(objects, tuple(original.contexts.values()), tuple(original.sources.values()), (original.entry('custom.default'), reference))
  assert _ids(knowledge.search('STRASSE', include_reference_only=True)) == ('custom.reference',)
  assert knowledge.search('STRASSE') == ()
  assert _ids(knowledge.search('丁火', include_reference_only=True)) == ('custom.reference',)
  assert knowledge.search(' Straße丁火 ', include_reference_only=True) == ()
  assert isinstance(knowledge.search('丁火', include_reference_only=True), tuple)


def test_search_filters_without_searching_sources() -> None:
  knowledge = _discovery_knowledge()
  assert _ids(knowledge.search('body')) == ('custom.default',)
  assert _ids(knowledge.search('BODY', include_reference_only=True)) == ('custom.default', 'custom.reference')
  assert _ids(knowledge.search(
    'body',
    object_id='concept.two',
    context_id='context.used',
    topic='reference_topic',
    source_id=knowledge.entry('custom.reference').sources[0],
    viewpoint='reference_view',
    applicability='described',
    time_scope='used.scope',
    include_reference_only=True,
  )) == ('custom.reference',)
  assert knowledge.search('reference', object_id='concept.one', include_reference_only=True) == ()
  for keyword in ('来源全文专用串', '情境标签专用串', 'concept.two', 'custom.reference'):
    assert knowledge.search(keyword, include_reference_only=True) == ()
  reference = replace(knowledge.entry('custom.reference'), text='literal [ bracket')
  literal = KnowledgeBase(tuple(knowledge.objects.values()), tuple(knowledge.contexts.values()), tuple(knowledge.sources.values()), (reference,))
  assert literal.search('[', include_reference_only=True) == (reference,)
  assert literal.search('.', include_reference_only=True) == ()
  assert KnowledgeBase((), (), (), ()).search('body') == ()
  with pytest.raises(TypeError):
    knowledge.search('body', include_reference_only=1) # type: ignore[arg-type]


def test_search_excludes_structural_metadata() -> None:
  original = _discovery_knowledge()
  source = next(iter(original.sources.values()))
  source_fields = ('source_id', 'work', 'attribution', 'edition', 'locator', 'url', 'lineage', 'excerpt', 'supports', 'limitations')
  changes: dict[str, Any] = {field: 'source-only-' + field for field in source_fields}
  source = replace(source, **changes)
  context = KnowledgeContext('context-only-id', 'context-only-label', 'context-only-scope', ('context-only-limit',))
  entry = replace(
    original.entry('custom.reference'),
    claim_id='entry-only-id',
    roles=(KnowledgeRole('role-only-name', 'concept.two'), KnowledgeRole('other-role-only-name', 'concept.one')),
    relations=(KnowledgeRelation('role-only-name', 'other-role-only-name', 'relation-only-text'),),
    sources=(source.source_id,),
    contexts=(context.context_id,),
    legacy=LegacyDescription('concept.two', 'general', 987654, ('chart_context_required',), 'legacy-only-premise'),
  )
  objects = tuple(replace(obj, kind='tiangan') if obj.object_id == 'concept.two' else obj for obj in original.objects.values())
  knowledge = KnowledgeBase(objects, (context,), (source,), (entry,))
  excluded = (
    *changes.values(), source.text_layer, source.state,
    context.context_id, context.label, context.time_scope, *context.limits,
    entry.claim_id, 'role-only-name', 'other-role-only-name', 'relation-only-text',
    'concept.two', 'tiangan', entry.applicability, entry.output, entry.source_state,
    'general', '987654', 'chart_context_required', 'legacy-only-premise',
  )
  assert knowledge.search('reference body', include_reference_only=True) == (entry,)
  for keyword in excluded:
    assert knowledge.search(keyword, include_reference_only=True) == (), keyword


def test_filter_values_sort_by_code_point() -> None:
  original = _discovery_knowledge()
  labels = ('😀', 'Ａ', 'a', 'B', 'A')
  source = next(iter(original.sources.values()))
  knowledge = KnowledgeBase(
    tuple(KnowledgeObject(label, 'concept', label) for label in labels),
    tuple(KnowledgeContext(label, label, label, ()) for label in labels),
    tuple(replace(source, source_id=label) for label in labels),
    tuple(replace(original.entry('custom.default'), claim_id=label, output='reference_only',
                  roles=(KnowledgeRole('subject', label),), sources=(label,),
                  topics=(label,), viewpoint=label) for label in labels),
  )
  for dimension in ('object_id', 'context_id', 'source_id', 'topic', 'viewpoint', 'time_scope'):
    assert knowledge.filter_values(dimension) == ('A', 'B', 'a', 'Ａ', '😀')


@pytest.mark.parametrize('dimension', ['object_id', 'context_id', 'source_id', 'topic', 'viewpoint', 'applicability', 'time_scope'])
def test_search_validates_filters_without_match(dimension: str) -> None:
  knowledge = _discovery_knowledge()
  for value, error in (('unknown', ValueError), (1, TypeError)):
    with pytest.raises(error):
      knowledge.search('no match', **{dimension: value}) # type: ignore[arg-type]


def test_frozen_oracle_conserves_claims_sources() -> None:
  fixture = Path(__file__).with_name('data') / 'description_legacy_baseline.json'
  baseline = json.loads(fixture.read_text(encoding='utf-8'))
  actual: list[dict[str, Any]] = []
  for subjects in (Shishen, Tiangan):
    for subject in subjects:
      selected = [
        entry for entry in KNOWLEDGE_BASE.entries.values()
        if entry.legacy is not None and entry.legacy.object_id == object_id(subject)
      ]
      field_order = ('general', 'in_good_status', 'in_bad_status', 'relationship') if isinstance(subject, Shishen) else ('general', 'personality')
      for field in field_order:
        claims = sorted(
          (entry for entry in selected if entry.legacy is not None and entry.legacy.field == field),
          key=lambda entry: entry.legacy.ordinal if entry.legacy is not None else -1,
        )
        for ordinal, claim in enumerate(claims):
          assert claim.legacy is not None
          assert claim.legacy.ordinal == ordinal
          actual.append({
            'subject_kind': subjects.__name__, 'subject': str(subject), 'field': field,
            'claim': {
              'claim_id': claim.claim_id, 'text': claim.text, 'sources': list(claim.sources),
              'attribution': claim.attribution, 'conditions': list(claim.legacy.conditions),
              'output': claim.output,
            },
          })
  # Projection logic untouched: expected rows are re-normalized only by the exact 45-ID attribution
  # allowance table and the attribution translation table.
  expected_rows = [
    {**row, 'claim': {**row['claim'], 'attribution': ALLOWED_CHANGES[row['claim']['claim_id']]['attribution']}}
    if row['claim']['claim_id'] in ALLOWED_CHANGES and 'attribution' in ALLOWED_CHANGES[row['claim']['claim_id']]
    else {**row, 'claim': {**row['claim'], 'attribution': TRANSLATED_ATTRIBUTION.get(row['claim']['attribution'], row['claim']['attribution'])}}
    for row in baseline['rows']
  ]
  assert actual == expected_rows
  for source_id, expected in baseline['sources'].items():
    record = asdict(KNOWLEDGE_BASE.sources[source_id])
    translated = {field: new for field, (_, new) in TRANSLATED_SOURCES.get(source_id, {}).items()}
    assert {key: record[key] for key in expected} == {**expected, **translated}
  old_ids = {row['claim']['claim_id'] for row in baseline['rows']}
  assert len(old_ids) == 291
  assert {entry.claim_id for entry in KNOWLEDGE_BASE.entries.values() if entry.legacy is not None} == old_ids
  assert set(_ids(KNOWLEDGE_BASE.query())) == {
    row['claim']['claim_id'] for row in baseline['rows'] if row['claim']['output'] == 'default'
  }
  assert len(KNOWLEDGE_BASE.entries) == 312


def test_attribution_allowance_matches_entries() -> None:
  # Two-way assertion: the allowance table's attribution set is exactly the 45 IDs with legacy.field=='relationship'.
  attribution_allowed = {
    claim_id for claim_id, changes in ALLOWED_CHANGES.items() if 'attribution' in changes
  }
  relationship_field = {
    entry.claim_id for entry in KNOWLEDGE_BASE.entries.values()
    if entry.legacy is not None and entry.legacy.field == 'relationship'
  }
  assert attribution_allowed == relationship_field and len(attribution_allowed) == 45
  limits_allowed = {
    claim_id for claim_id, changes in ALLOWED_CHANGES.items() if 'limits' in changes
  }
  old_stars = {'legacy.shishen.SH-' + number for number in ('094', '114', '135', '155')}
  assert limits_allowed == attribution_allowed | old_stars and len(limits_allowed) == 49
  for claim_id, changes in ALLOWED_CHANGES.items():
    entry = KNOWLEDGE_BASE.entry(claim_id)
    for field, expected in changes.items():
      actual = getattr(entry, field)
      # limits are a list in JSON and a tuple on the entry; compared verbatim.
      assert (list(actual) if isinstance(actual, tuple) else actual) == expected, (claim_id, field)


def test_translation_table_matches_the_corpus() -> None:
  # Two-way: every translated value is in the corpus and no original value is left behind.
  for source_id, changes in TRANSLATED_SOURCES.items():
    record = asdict(KNOWLEDGE_BASE.sources[source_id])
    for field, (old, new) in changes.items():
      assert record[field] == new and old != new, (source_id, field)
  attributions = {entry.attribution for entry in KNOWLEDGE_BASE.entries.values()}
  # Unique translations keep the reverse map used by the fingerprints well defined.
  assert len(set(TRANSLATED_ATTRIBUTION.values())) == len(TRANSLATED_ATTRIBUTION)
  assert set(TRANSLATED_ATTRIBUTION.values()) <= attributions
  assert not set(TRANSLATED_ATTRIBUTION) & attributions


def test_descriptive_fields_are_chinese() -> None:
  # Quoted excerpts and URLs are exempt; editorial-layer excerpts are repository records, not quotes.
  def has_han(value: str) -> bool:
    return any('\u4e00' <= char <= '\u9fff' for char in value)
  for entry in KNOWLEDGE_BASE.entries.values():
    assert has_han(entry.attribution), entry.claim_id
  for source in KNOWLEDGE_BASE.sources.values():
    fields = ['work', 'attribution', 'edition', 'locator', 'supports', 'limitations']
    if source.text_layer == 'editorial':
      fields.append('excerpt')
    for field in fields:
      assert has_han(getattr(source, field)), (source.source_id, field)


def test_real_queries_intersect_dimensions() -> None:
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
  bijian = _ids(k.query(object_id='shishen.bijian', applicability='unresolved', include_reference_only=True))
  assert 'legacy.shishen.SH-011' in bijian
  assert 'shishen.bijian.definition' not in bijian
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


def test_premises_organized_without_new_rules() -> None:
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
  assert k.entry('editorial.shishen.zhengguan.legal_trouble').applicability == 'described'
  new_relationship_ids = set(json.loads(
    (Path(__file__).with_name('data') / 'corpus_allowed_changes.json').read_text(encoding='utf-8')
  )['added']['entries'])
  for entry in k.entries.values():
    assert not {'in_good_status', 'in_bad_status'} & set(entry.topics)
    if entry.legacy is None:
      assert entry.output == 'reference_only'
      if entry.claim_id in new_relationship_ids | {'shensha.kongwang.xunkong', 'shensha.kongwang.lookup', *AUXILIARY_WITNESSED_IDS}:
        # Entries in new_relationship_ids have source_state 'witnessed' (古籍见证).
        assert entry.source_state == 'witnessed'
      else:
        assert entry.source_state == 'repository_attributed'
        assert all(k.sources[source].text_layer == 'editorial' for source in entry.sources)


def test_reference_samples_keep_text_limits() -> None:
  k = KNOWLEDGE_BASE
  samples: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ('wuxing.mu_sheng_huo', '木生火。', ('仅说明基础关系方向，不证明命盘中的有效生克或流转。',)),
    ('wuxing.jin_ke_mu', '金克木。', ('仅说明基础关系方向，不证明命盘中的有效生克或流转。',)),
    ('shensha.guoyin.modern', '国印的 MODERN 表按禄前第九位（含禄，偏移 +8）取值。', (
      '表值与四柱查法的支持来源分开；古籍的守照身命表述不等于查四柱地支。',
      '本条转述仓内来源边界，未新增已核古籍见证。',
    )),
    ('shensha.guoyin.wuxing_jingji', '国印的 WUXING_JINGJI 表按禄前第八位（含禄，偏移 +7）取值。', (
      '年干锚与含禄起算的明文出自《五行精纪注释》的今人【注释】，不混作【原文】的断言。',
      '白文、清抄本与注释本的传抄关系未定（#194）。',
    )),
  )
  for claim_id, text, limits in samples:
    entry = k.entry(claim_id)
    assert entry.text == text
    assert entry.limits == limits
    rendered = k.render(entry, show_sources=False)
    for limit in limits:
      assert limit in rendered

  contexts: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ('legacy.shishen.SH-066', 'shishen.xiaoyin_duoshi', (
      '枭印夺食的判据及适用范围尚未定义，不等同于偏印与食神共现。',
    )),
    ('legacy.shishen.SH-199', 'shishen.pianyin_favorable_or_balanced', (
      '喜用、不过旺及不受刑克冲害的具体判据尚未确认。',
    )),
    ('legacy.tiangan.ding.weak_state', 'tiangan.ding_weak_and_overcontrolled', (
      '身弱与克太多的判据尚未定义。',
    )),
  )
  for claim_id, context_id, limits in contexts:
    entry = k.entry(claim_id)
    assert entry.contexts == (context_id,)
    assert k.contexts[context_id].limits == limits
    rendered = k.render(entry, show_sources=False)
    for limit in limits:
      assert limit in rendered

  relation = k.entry('legacy.shishen.SH-052')
  assert relation.limits == (
    '财未具体分为正财或偏财。',
    '克制与避祸等解释的适用前提尚未还原，不表示有效制杀已成立。',
  )
  rendered = k.render(relation, show_sources=False)
  for limit in relation.limits:
    assert limit in rendered


def test_ding_nested_premises_stay_unresolved() -> None:
  k = KNOWLEDGE_BASE
  entry = k.entry('legacy.tiangan.ding.weak_state')
  context_id = 'tiangan.ding_weak_and_overcontrolled'
  assert entry.text == '丁火日主若是身弱，就发挥不出丁火的优点，如果又见克太多，则会变成胆小，多愁多虑。'
  assert entry.premise == '丁火日主若是身弱，就发挥不出丁火的优点，如果又见克太多'
  assert entry.applicability == 'unresolved'
  assert entry.contexts == (context_id,)
  assert k.contexts[context_id].time_scope == '未限定'
  limit = '嵌套前提与中间结果尚未拆分。'
  assert entry.limits == (limit,)
  selected = k.query(
    object_id='tiangan.ding',
    context_id=context_id,
    topic='性格',
    applicability='unresolved',
    time_scope='未限定',
    include_reference_only=True,
  )
  assert selected == (entry,)
  assert k.query(context_id=context_id, applicability='described', include_reference_only=True) == ()
  assert k.query(context_id=context_id) == ()
  for show_sources in (False, True):
    rendered = k.render(entry, manual_context=True, show_sources=show_sources)
    for text in (
      entry.text, '前提：' + entry.premise, '前提待梳理', '来源尚未核实',
      '人工给定情境；命盘适用性未判断',
      '情境：tiangan.ding_weak_and_overcontrolled；未限定；丁火日主身弱条目情境',
      '限度：' + limit,
    ):
      assert text in rendered
  restored = KnowledgeBase.from_json(k.export_json(selected))
  assert restored.query(context_id=context_id, applicability='unresolved', time_scope='未限定', include_reference_only=True) == selected
  assert restored.render(entry, manual_context=True) == k.render(entry, manual_context=True)


def test_migrated_field_premises_conserved() -> None:
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


def test_render_definition_metadata() -> None:
  k = KNOWLEDGE_BASE
  definition = k.render(k.entry('shishen.shishen.definition'))
  assert '仅供参考' not in definition and '未判断' not in definition
  assert '支持范围：' in definition and '局限：' in definition
  assert '文本层：baiwen' in definition
  assert '生我者為正印偏印' in definition
  assert '文字关系：讨论对象→七杀' in k.render(k.entry('legacy.shishen.SH-052'))


def test_render_historical_reference_warning() -> None:
  k = KNOWLEDGE_BASE
  historical = k.entry('tiangan.ding.lamp_symbol')
  assert '仅供参考' in k.render(historical)
  assert '来源尚未核实' not in k.render(historical)


def test_render_preserves_legacy_premises() -> None:
  k = KNOWLEDGE_BASE
  text = k.render(k.entry('legacy.shishen.SH-011'), show_sources=False)
  assert '前提待梳理' in text and '命盘适用性未判断' in text
  assert '旧栏目前提（待梳理；未作为判据）：当十神处于力量不过强' in text
  assert '条目：' not in text and '来源：' not in text
  legacy_detail = k.render(k.entry('legacy.shishen.SH-011'))
  assert '旧栏目前提（待梳理；未作为判据）：当十神处于力量不过强' in legacy_detail
  assert '如不被冲、克，也不过旺/为命主喜用时' in legacy_detail
  for entry in k.entries.values():
    if entry.legacy is not None and entry.legacy.field_premise:
      assert entry.legacy.field_premise in k.render(entry, show_sources=False)


def test_render_reports_repository_attribution() -> None:
  k = KNOWLEDGE_BASE
  assert '来源状态：repository_attributed' in k.render(k.entry('shensha.guoyin.modern'))


def test_registries_results_deeply_immutable() -> None:
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
def test_boolean_options_reject_non_bools(value: object) -> None:
  k = KNOWLEDGE_BASE
  with pytest.raises(TypeError):
    k.query(include_reference_only=value) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    k.render(k.entry('tiangan.ding.definition'), show_sources=value) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    k.render(k.entry('tiangan.ding.definition'), manual_context=value) # type: ignore[arg-type]


@pytest.mark.parametrize('value', [1, None, 'yes'])
def test_render_rejects_non_entries(value: object) -> None:
  k = KNOWLEDGE_BASE
  with pytest.raises(TypeError):
    k.render(value) # type: ignore[arg-type]


@pytest.mark.parametrize('value', [1, None, 'yes'])
def test_lookup_rejects_invalid_ids(value: object) -> None:
  k = KNOWLEDGE_BASE
  with pytest.raises(ValueError if isinstance(value, str) else TypeError):
    k.entry(value) # type: ignore[arg-type]


@pytest.mark.parametrize('value', [1, 'yes'])
def test_file_load_rejects_invalid_input(value: object) -> None:
  with pytest.raises(TypeError):
    KnowledgeBase.load(value) # type: ignore[arg-type]


@pytest.mark.parametrize('value', [1, None, 'yes'])
def test_json_load_rejects_invalid_input(value: object) -> None:
  with pytest.raises(ValueError if isinstance(value, str) else TypeError):
    KnowledgeBase.from_json(value) # type: ignore[arg-type]


def test_lookup_rejects_unknown_claim() -> None:
  k = KNOWLEDGE_BASE
  with pytest.raises(ValueError, match='Unknown claim'):
    k.entry('missing')


def test_selections_reject_foreign_entries() -> None:
  k = KNOWLEDGE_BASE
  entry = k.entry('tiangan.ding.definition')
  foreign = replace(entry, text='Another text.')
  with pytest.raises(ValueError, match='Foreign entry'):
    k.render(foreign)
  with pytest.raises(ValueError, match='Foreign entry'):
    k.export_json((foreign,))


def test_export_rejects_invalid_selection() -> None:
  k = KNOWLEDGE_BASE
  entry = k.entry('tiangan.ding.definition')
  with pytest.raises(ValueError, match='Duplicate selection'):
    k.export_json((entry, entry))
  with pytest.raises(TypeError):
    k.export_json([entry]) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    k.export_json((object(),)) # type: ignore[arg-type]


def test_value_constructors_validate_fields() -> None:
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
def test_corpus_rejects_integrity_violations(mutation: str, message: str) -> None:
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


def test_json_rejects_malformed_corpus() -> None:
  for text in ('{"schema_version":1,"schema_version":1}', '[1]', '{}', '{bad json'):
    with pytest.raises((TypeError, ValueError)):
      KnowledgeBase.from_json(text)
  for key in ('objects', 'contexts', 'sources', 'entries'):
    data = json.loads(KNOWLEDGE_BASE.export_json())
    data[key] = {}
    with pytest.raises(TypeError, match='JSON array'):
      KnowledgeBase.from_json(json.dumps(data))
  for version in (True, '2', 1, 3, 2.0):
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
  with pytest.raises(ValueError):
    KnowledgeBase.from_json('')


def test_constructor_requires_typed_tuples() -> None:
  with pytest.raises(TypeError):
    KnowledgeBase([], (), (), ()) # type: ignore[arg-type]
  with pytest.raises(TypeError):
    KnowledgeBase((object(),), (), (), ()) # type: ignore[arg-type]


def test_witnessed_zhushi_is_distinct_layer() -> None:
  source = replace(KNOWLEDGE_BASE.sources['yuanhai_ziping_relations'], source_id='annotation', text_layer='zhushi')
  k = KnowledgeBase((), (), (source,), ())
  assert k.sources['annotation'].text_layer == 'zhushi'
  assert KnowledgeBase.from_json(k.export_json()).sources == k.sources


# Entries in _NEW_RELATIONSHIP_IDS and their registry; corpus facts are pinned here, with protection asserts in the two tests below.
_NEW_RELATIONSHIP_IDS: tuple[str, ...] = (
  'editorial.liuqin.spouse_star_yinyanggan.v1',
  'editorial.liuqin.spouse_star_zhengpian.v1',
  'editorial.liuqin.qiqie_gong.v1',
  'editorial.tanyuan.wife_palace_xingchong.v1',
  'editorial.tanyuan.wife_star_gantou.v1',
  'editorial.tanyuan.wife_star_liangtou.v1',
  'editorial.liuqin.sanming_qiqie_zuodi.v1',
)
_GATED_CLAIM_IDS: tuple[str, ...] = (
  'editorial.tanyuan.wife_palace_xingchong.v1',
  'editorial.tanyuan.wife_star_gantou.v1',
)


def test_relationship_additions_counts_surface() -> None:
  k = KNOWLEDGE_BASE
  assert len(k.entries) == 312 and len(k.sources) == 23 and len(k.contexts) == 10 and len(k.objects) == 34
  assert len(k.query()) == 19 # all added entries are reference_only, so the default query surface is untouched.
  for claim_id in _NEW_RELATIONSHIP_IDS:
    entry = k.entry(claim_id)
    assert entry.legacy is None and entry.output == 'reference_only'
    assert entry.source_state == 'witnessed'
  # The 星坐地 and 两透 entries with unverified conditions bind no criterion and no context (unresolved, empty premise).
  for claim_id in ('editorial.tanyuan.wife_star_liangtou.v1', 'editorial.liuqin.sanming_qiqie_zuodi.v1'):
    entry = k.entry(claim_id)
    assert entry.applicability == 'unresolved' and entry.premise == '' and entry.contexts == ()
  for claim_id in _NEW_RELATIONSHIP_IDS[:5]:
    assert k.entry(claim_id).applicability == 'described' and k.entry(claim_id).premise
  # New query surface: two objects and one context; the unchanged static query surface of old objects, contexts, and sources is covered by the remaining asserts and fingerprints.
  assert _ids(k.query(object_id='concept.peiou_xing', include_reference_only=True)) == (
    'editorial.liuqin.spouse_star_yinyanggan.v1', 'editorial.liuqin.spouse_star_zhengpian.v1',
    'editorial.tanyuan.wife_star_gantou.v1', 'editorial.tanyuan.wife_star_liangtou.v1',
    'editorial.liuqin.sanming_qiqie_zuodi.v1',
  )
  assert _ids(k.query(object_id='concept.peiou_gong', include_reference_only=True)) == (
    'editorial.liuqin.qiqie_gong.v1', 'editorial.tanyuan.wife_palace_xingchong.v1',
  )
  assert _ids(k.query(context_id='liuqin.spouse_star_readings', include_reference_only=True)) == (
    'editorial.liuqin.spouse_star_yinyanggan.v1', 'editorial.liuqin.spouse_star_zhengpian.v1',
  )
  assert len(k.query(topic='取象', include_reference_only=True)) == 193
  # New-source excerpts are verbatim short quotes, appearing word for word in the entry texts that cite them.
  for source_id in ('sanming_liuqin', 'yuanhai_liuqin_charts', 'yuanhai_qiqie_note', 'tanyuan_qizi'):
    source = k.sources[source_id]
    citing = [entry for entry in k.entries.values() if source_id in entry.sources]
    assert citing and any(source.excerpt in entry.text for entry in citing), source_id


def test_gender_gate_marker_matches_table() -> None:
  # Corpus markers and the gate table mirror each other: marked entries are exactly the keys of _RELATED_GENDERS, and markers stay out of text/premise.
  from bazi.context_matching import _RELATED_GENDERS
  marker = '女命查询不关联本条，静态查阅不受限。'
  marked = {
    entry.claim_id for entry in KNOWLEDGE_BASE.entries.values()
    if any(marker in limit for limit in entry.limits)
  }
  assert marked == set(_RELATED_GENDERS) == set(_GATED_CLAIM_IDS)
  assert len(marked) == 2
  for entry in KNOWLEDGE_BASE.entries.values():
    assert marker not in entry.text and marker not in entry.premise
    if entry.claim_id not in _GATED_CLAIM_IDS:
      assert all(marker not in limit for limit in entry.limits)


def test_normalized_legacy_projection_fingerprint() -> None:
  # Normalized projection of all 291 old entries: attribution of the 45 allowed IDs and limits of the
  # 49 allowed IDs stripped, translated attributions mapped back, all other fields included.
  # Fingerprints are identical on the pre- and post-change corpora; this is not new-hash removal of protection.
  import hashlib
  from dataclasses import asdict as _asdict
  attribution_allowed = {
    claim_id for claim_id, changes in ALLOWED_CHANGES.items() if 'attribution' in changes
  }
  limits_allowed = {claim_id for claim_id, changes in ALLOWED_CHANGES.items() if 'limits' in changes}
  original_attribution = {new: old for old, new in TRANSLATED_ATTRIBUTION.items()}
  rows = []
  for entry in KNOWLEDGE_BASE.entries.values():
    if entry.legacy is None:
      continue
    row = _asdict(entry)
    if entry.claim_id in attribution_allowed:
      del row['attribution']
    else:
      row['attribution'] = original_attribution.get(entry.attribution, entry.attribution)
    if entry.claim_id in limits_allowed:
      del row['limits']
    rows.append(row)
  digest = hashlib.sha256(
    json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
  ).hexdigest()
  assert digest == 'b84a66ca805566abeab5bbd23c67cd665e84caa85bcadd365bd2b1ee887417c5'
  # Entries with pre-existing non-empty limits (2 of the 6 legacy entries in the old corpus; the other
  # 4 in-repo entries are pinned verbatim by test_reference_samples_keep_text_limits)
  # are not loosened by the allowance table.
  unchanged_nonempty = {
    entry.claim_id: entry.limits for entry in KNOWLEDGE_BASE.entries.values()
    if entry.legacy is not None and entry.limits and entry.claim_id not in limits_allowed
  }
  assert set(unchanged_nonempty) == {'legacy.shishen.SH-052', 'legacy.tiangan.ding.weak_state'}
  assert unchanged_nonempty['legacy.shishen.SH-052'] == (
    '财未具体分为正财或偏财。',
    '克制与避祸等解释的适用前提尚未还原，不表示有效制杀已成立。',
  )
  assert unchanged_nonempty['legacy.tiangan.ding.weak_state'] == ('嵌套前提与中间结果尚未拆分。',)


def test_non_legacy_entries_fingerprint() -> None:
  # The 11 entries without legacy metadata have no oracle row; pin every field, with translated
  # attributions mapped back as in the legacy projection. The digest equals the pre-translation corpus.
  import hashlib
  original_attribution = {new: old for old, new in TRANSLATED_ATTRIBUTION.items()}
  rows = []
  for entry in KNOWLEDGE_BASE.entries.values():
    if entry.legacy is not None or entry.claim_id in {
      'shensha.kongwang.xunkong', 'shensha.kongwang.lookup', 'shensha.kongwang.repository',
      *AUXILIARY_ENTRY_IDS,
    }:
      continue
    row = asdict(entry)
    row['attribution'] = original_attribution.get(entry.attribution, entry.attribution)
    rows.append(row)
  assert len(rows) == 11
  digest = hashlib.sha256(
    json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
  ).hexdigest()
  assert digest == '8d988184034a46465c1763610cdaa16dd928cbec3e372570a468fae3cefb19c2'


def test_non_oracle_sources_fingerprint() -> None:
  # The 6 sources absent from the legacy oracle have no oracle record; pin every field, with translated
  # fields mapped back to the ledger's originals. The digest equals the pre-translation corpus.
  import hashlib
  oracle = json.loads(
    (Path(__file__).with_name('data') / 'description_legacy_baseline.json').read_text(encoding='utf-8')
  )['sources']
  rows = []
  for source_id, source in KNOWLEDGE_BASE.sources.items():
    if source_id in oracle or source_id in {
      'yuanhai_ziping.kongwang', 'sanming_tonghui.kongwang', 'luoluzi_xiaoxifu.kongwang',
      'wuxing_jingji.kongwang', 'repository.kongwang',
      *AUXILIARY_SOURCE_IDS,
    }:
      continue
    row = asdict(source)
    for field, (old, _) in TRANSLATED_SOURCES.get(source_id, {}).items():
      row[field] = old
    rows.append(row)
  assert len(rows) == 6
  digest = hashlib.sha256(
    json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
  ).hexdigest()
  assert digest == '41c021df77ea786cd5e5e0524fb56d5f568d4713b915860451c8c752f7373ab2'


def test_auxiliary_queries_stay_reference_only() -> None:
  k = KNOWLEDGE_BASE
  for identifier in ('concept.taiyuan', 'concept.minggong'):
    assert k.objects[identifier].kind == 'concept'
    assert k.query(object_id=identifier) == ()
    selected = k.query(object_id=identifier, include_reference_only=True)
    assert selected and all(entry.claim_id in AUXILIARY_ENTRY_IDS for entry in selected)
    assert all({role.object_id for role in entry.roles} == {identifier} for entry in selected)
  for identifier in AUXILIARY_ENTRY_IDS:
    entry = k.entry(identifier)
    assert entry.output == 'reference_only' and entry.legacy is None
    assert entry.contexts == () and entry.relations == () and entry.limits
    assert entry.source_state == ('witnessed' if identifier in AUXILIARY_WITNESSED_IDS else 'repository_attributed')
    assert all(k.sources[source].state == entry.source_state for source in entry.sources)
    if identifier in ('concept.taiyuan.three_hundred_days', 'concept.minggong.month_boundary_candidates'):
      assert entry.applicability == 'unresolved' and entry.premise == ''
      assert '未编码' in ''.join(entry.limits)
    else:
      assert entry.applicability == 'unconditional' and entry.premise == ''
  assert len(k.query()) == 19
  assert KnowledgeBase.from_json(k.export_json()) == k


@pytest.mark.parametrize('claim_id,sources', [
  ('concept.minggong.palm', ('sanming_tonghui.minggong', 'youyilu.taiyuan_minggong')),
  ('concept.taiyuan.month_shift', ('youyilu.taiyuan_minggong', 'sanming_tonghui.taiyuan')),
])
def test_auxiliary_default_needs_independence(claim_id: str, sources: tuple[str, ...]) -> None:
  k = KNOWLEDGE_BASE
  entry = k.entry(claim_id)
  assert entry.sources == sources
  assert entry.applicability == 'unconditional' and entry.source_state == 'witnessed'
  promoted = replace(entry, output='default')
  with pytest.raises(ValueError, match=f'^Default entry needs independent lineages: {claim_id}$'):
    KnowledgeBase(
      tuple(k.objects.values()), tuple(k.contexts.values()), tuple(k.sources.values()),
      tuple(promoted if value.claim_id == claim_id else value for value in k.entries.values()),
    )
  assert entry.output == 'reference_only' and len(k.query()) == 19


def test_auxiliary_source_support_is_separated() -> None:
  k = KNOWLEDGE_BASE
  expected = {
    'youyilu.taiyuan_minggong': ('baiwen', 'sanming_tonghui', '生月干前一位，枝前三位即是。如己巳月生，则胎元在庚申；壬午月生，则胎元在癸酉。'),
    'sanming_tonghui.taiyuan': ('baiwen', 'sanming_tonghui', '惟有一法以當生前三百日為十月之氣乃是受胎之正'),
    'sanming_tonghui.minggong': ('baiwen', 'sanming_tonghui', '次将所生之時加於所生之月順行十二位逢卯即安命宫'),
    'mingli_tanyuan.minggong': ('zhushi', 'mingli_tanyuan', '古人谓交过中气，即作次月推'),
  }
  for identifier, (layer, lineage, excerpt) in expected.items():
    source = k.sources[identifier]
    assert (source.text_layer, source.lineage, source.excerpt, source.state) == (layer, lineage, excerpt, 'witnessed')
    assert any(excerpt in entry.text for entry in k.query(source_id=identifier, include_reference_only=True))
    assert '转录' in source.edition + source.attribution and source.limitations
  assert '然則貴人受胎定在三百日又豈可據乎' in k.sources['sanming_tonghui.taiyuan'].limitations
  critique = '今人多以法取胎元未審精當'
  source = k.sources['sanming_tonghui.taiyuan']
  assert critique in source.supports
  assert '一巳' in source.limitations and '前十日' in source.limitations
  shifted = k.entry('concept.taiyuan.month_shift')
  assert critique in ''.join(shifted.limits)
  assert '不等于该书赞同' in ''.join(shifted.limits)
  grouped = k.sources['youyilu.taiyuan_minggong']
  assert '独立性未核' in grouped.limitations and '保守' in grouped.limitations
  assert '不是已证直接承袭' in grouped.limitations
  assert '未明确' in k.sources['sanming_tonghui.minggong'].limitations
  assert '按语' in k.sources['mingli_tanyuan.minggong'].limitations
  locator = k.sources['mingli_tanyuan.minggong'].locator
  assert '下载页题名作《命理探源》' in locator and '本库沿称《命理探原》' in locator
  assert '立春' not in k.entry('concept.minggong.zhongqi').text
  candidate = ''.join(k.entry('concept.taiyuan.three_hundred_days').limits)
  assert all(text in candidate for text in ('四库固定转录', '网页选录', '批评', '段末另有质疑', '先核对选录截取与转录范围，再查底本'))
  policy = k.sources['repository.taiyuan_minggong']
  assert policy.state == 'repository_attributed' and policy.text_layer == 'editorial'


def test_kongwang_additions_are_reference_only() -> None:
  k = KNOWLEDGE_BASE
  assert asdict(k.objects['shensha.kongwang']) == {
    'object_id': 'shensha.kongwang', 'kind': 'shensha', 'name': '六甲旬空',
  }
  expected = {
    'shensha.kongwang.xunkong': (
      'witnessed', '六甲旬空二支定义',
      ('yuanhai_ziping.kongwang', 'sanming_tonghui.kongwang', 'luoluzi_xiaoxifu.kongwang'),
    ),
    'shensha.kongwang.lookup': (
      'witnessed', '年日锚与流运语境', ('wuxing_jingji.kongwang', 'sanming_tonghui.kongwang'),
    ),
    'shensha.kongwang.repository': ('repository_attributed', '本仓默认与查询范围', ('repository.kongwang',)),
  }
  entries = k.query(object_id='shensha.kongwang', include_reference_only=True)
  texts = {
    'shensha.kongwang.xunkong': '六甲旬空的基础二支，是一旬十干配十支后余下的二支。《渊海子平》转录列：「甲子旬中無戌亥，甲戌旬中無申酉，甲申旬中無午未，甲午旬中無辰巳，甲辰旬中無寅卯，甲寅旬中無子丑。」《三命通会》四库本转录说明：「如甲子旬遁至酉而十干足所以無戌亥餘五干例見是為空亡」。《消息赋注》注中另述：「假令甲子旬中，戌亥空亡也。」',
    'shensha.kongwang.lookup': '查法须与基础二支分开。《五行精纪》卷二十五转引《神白经》有「此空亡只用生日旬中空亡極緊」，同段论及运与太岁；另引《林开五命》有「論空亡止以年日所在」。《三命通会》四库本转录有「假令甲子年壬戌日」的年日互换例。这里只记录汇编转引与该版例解，不把引书名当作已见原书。',
    'shensha.kongwang.repository': '日柱默认，年柱或年日双锚可选；只记录六甲旬空二支与原始命中。原局逐锚查其余三柱地支，流运只以本命锚查所选流运支。无命中保留二支，同值锚、重复柱支与同干支不同流运种类分别保留来源和位置。',
  }
  assert _ids(entries) == tuple(expected)
  assert k.query(object_id='shensha.kongwang') == ()
  assert len(k.query()) == 19
  for entry in entries:
    assert entry.text == texts[entry.claim_id]
    assert (entry.source_state, entry.viewpoint, entry.sources) == expected[entry.claim_id]
    assert entry.output == 'reference_only' and entry.legacy is None
    assert entry.applicability == 'unconditional' and entry.premise == '' and entry.contexts == ()
    assert entry.relations == () and len(entry.roles) == 1
    assert entry.roles[0].object_id == 'shensha.kongwang'
    assert all(k.sources[source].state == entry.source_state for source in entry.sources)
    assert entry.limits and entry.exceptions == ()
  assert KnowledgeBase.from_json(k.export_json()).query(object_id='shensha.kongwang', include_reference_only=True) == entries


def test_kongwang_sources_keep_witness_boundaries() -> None:
  k = KNOWLEDGE_BASE
  expected = {
    'yuanhai_ziping.kongwang': ('witnessed', 'baiwen', 'https://www.donglishuzhai.net/chapter/12794.html',
      '甲子旬中無戌亥，甲戌旬中無申酉，甲申旬中無午未，甲午旬中無辰巳，甲辰旬中無寅卯，甲寅旬中無子丑。'),
    'sanming_tonghui.kongwang': ('witnessed', 'baiwen', 'https://zh.wikisource.org/w/index.php?oldid=657369',
      '如甲子旬遁至酉而十干足所以無戌亥餘五干例見是為空亡'),
    'luoluzi_xiaoxifu.kongwang': ('witnessed', 'zhushi', 'https://zh.wikisource.org/w/index.php?oldid=857114',
      '假令甲子旬中，戌亥空亡也。'),
    'wuxing_jingji.kongwang': ('witnessed', 'baiwen', 'https://zh.wikisource.org/w/index.php?oldid=10494296',
      '此空亡只用生日旬中空亡極緊'),
    'repository.kongwang': ('repository_attributed', 'editorial', 'https://github.com/0xf3cd/bazi/issues/277',
      '日柱默认，年柱或年日双锚可选；只记录六甲旬空二支与原始命中。'),
  }
  cited = {source for entry in k.query(object_id='shensha.kongwang', include_reference_only=True) for source in entry.sources}
  assert cited == set(expected)
  for source_id, values in expected.items():
    source = k.sources[source_id]
    assert (source.state, source.text_layer, source.url, source.excerpt) == values
    assert source_id.startswith(source.lineage + '.')
    assert source.supports and source.limitations
    assert any(source.excerpt in entry.text for entry in k.query(source_id=source_id, include_reference_only=True))
  assert '不指已见《神白经》或《林开五命》原书' in k.sources['wuxing_jingji.kongwang'].limitations
  assert '壬戌月' in k.sources['sanming_tonghui.kongwang'].limitations
  assert '不把三命通会转引的单支读法归入本书' in k.sources['luoluzi_xiaoxifu.kongwang'].limitations
  assert '仓内政策不是古籍见证' in k.sources['repository.kongwang'].limitations
