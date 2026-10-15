# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import FrozenInstanceError, asdict, fields, replace
from pathlib import Path
from typing import Any, get_args, get_origin

import pytest

from bazi.defines import Shishen, Tiangan
from bazi.knowledge import (
  KnowledgeBase, KnowledgeObject, KnowledgeRole, KnowledgeRelation, KnowledgeEntry,
  LegacyDescription, object_id,
)


KNOWLEDGE_BASE = KnowledgeBase.load()
ALLOWED_CHANGES: dict[str, dict[str, object]] = json.loads(
  (Path(__file__).with_name('data') / 'corpus_allowed_changes.json').read_text(encoding='utf-8')
)['allowed_changes']


def _ids(entries: tuple[KnowledgeEntry, ...]) -> tuple[str, ...]:
  return tuple(entry.claim_id for entry in entries)


def test_frozen_legacy_oracle_conserves_every_claim_and_source() -> None:
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
  # 投影逻辑不动：期望值仅按 45 个允许 ID 的 attribution 精确允许表反向规范化。
  expected_rows = [
    {**row, 'claim': {**row['claim'], 'attribution': ALLOWED_CHANGES[row['claim']['claim_id']]['attribution']}}
    if row['claim']['claim_id'] in ALLOWED_CHANGES and 'attribution' in ALLOWED_CHANGES[row['claim']['claim_id']]
    else row
    for row in baseline['rows']
  ]
  assert actual == expected_rows
  for source_id, expected in baseline['sources'].items():
    record = asdict(KNOWLEDGE_BASE.sources[source_id])
    assert {key: record[key] for key in expected} == expected
  old_ids = {row['claim']['claim_id'] for row in baseline['rows']}
  assert len(old_ids) == 291
  assert {entry.claim_id for entry in KNOWLEDGE_BASE.entries.values() if entry.legacy is not None} == old_ids
  assert set(_ids(KNOWLEDGE_BASE.query())) == {
    row['claim']['claim_id'] for row in baseline['rows'] if row['claim']['output'] == 'default'
  }
  assert len(KNOWLEDGE_BASE.entries) == 302


def test_attribution_allowance_is_exactly_the_relationship_field_entries() -> None:
  # 双向断言：允许表的 attribution 集合恰为 legacy.field=='relationship' 的 45 个 ID。
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
      # limits 在 JSON 中是列表、条目上是元组；逐字相等。
      assert (list(actual) if isinstance(actual, tuple) else actual) == expected, (claim_id, field)


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
  assert k.entry('editorial.shishen.zhengguan.legal_trouble').applicability == 'described'
  new_relationship_ids = set(json.loads(
    (Path(__file__).with_name('data') / 'corpus_allowed_changes.json').read_text(encoding='utf-8')
  )['added']['entries'])
  for entry in k.entries.values():
    assert not {'in_good_status', 'in_bad_status'} & set(entry.topics)
    if entry.legacy is None:
      assert entry.output == 'reference_only'
      if entry.claim_id in new_relationship_ids:
        # 本批新增的婚恋条目挂古籍见证，不再是仓内整理署名。
        assert entry.source_state == 'witnessed'
      else:
        assert entry.source_state == 'repository_attributed'
        assert all(k.sources[source].text_layer == 'editorial' for source in entry.sources)


def test_reference_samples_preserve_text_and_complete_limits() -> None:
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


def test_ding_nested_premises_remain_unresolved_and_time_unspecified() -> None:
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


# 本批新增的婚恋条目与注册表；语料事实钉在这里，保护断言见下两条。
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


def test_relationship_additions_registry_counts_and_default_surface() -> None:
  k = KNOWLEDGE_BASE
  assert len(k.entries) == 302 and len(k.sources) == 13 and len(k.contexts) == 10 and len(k.objects) == 31
  assert len(k.query()) == 19 # 新条目全部 reference_only，默认输出面不变。
  for claim_id in _NEW_RELATIONSHIP_IDS:
    entry = k.entry(claim_id)
    assert entry.legacy is None and entry.output == 'reference_only'
    assert entry.source_state == 'witnessed'
  # 星坐地与两透两条件未核条目不挂判据、不挂情境（unresolved，premise 为空）。
  for claim_id in ('editorial.tanyuan.wife_star_liangtou.v1', 'editorial.liuqin.sanming_qiqie_zuodi.v1'):
    entry = k.entry(claim_id)
    assert entry.applicability == 'unresolved' and entry.premise == '' and entry.contexts == ()
  for claim_id in _NEW_RELATIONSHIP_IDS[:5]:
    assert k.entry(claim_id).applicability == 'described' and k.entry(claim_id).premise
  # 新查询面：两个对象与一个情境；旧对象／情境／来源的静态查询面不变由其余断言与指纹承担。
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
  # 新来源的 excerpt 是原样短摘，逐字出现在以其为引文依据的条目 text 里。
  for source_id in ('sanming_liuqin', 'yuanhai_liuqin_charts', 'yuanhai_qiqie_note', 'tanyuan_qizi'):
    source = k.sources[source_id]
    citing = [entry for entry in k.entries.values() if source_id in entry.sources]
    assert citing and any(source.excerpt in entry.text for entry in citing), source_id


def test_gender_gate_marker_matches_the_gate_table_exactly() -> None:
  # 语料标记与门槛表互为对照：含标记的条目恰是 _RELATED_GENDERS 的键，标记不进 text／premise。
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
  # 全 291 旧条目的规范化投影：去 45 个允许 ID 的 attribution、49 个允许 ID 的 limits，
  # 其余字段全入。指纹在改前改后语料上相同，不是新 hash 消除保护。
  import hashlib
  from dataclasses import asdict as _asdict
  attribution_allowed = {
    claim_id for claim_id, changes in ALLOWED_CHANGES.items() if 'attribution' in changes
  }
  limits_allowed = {claim_id for claim_id, changes in ALLOWED_CHANGES.items() if 'limits' in changes}
  rows = []
  for entry in KNOWLEDGE_BASE.entries.values():
    if entry.legacy is None:
      continue
    row = _asdict(entry)
    if entry.claim_id in attribution_allowed:
      del row['attribution']
    if entry.claim_id in limits_allowed:
      del row['limits']
    rows.append(row)
  digest = hashlib.sha256(
    json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
  ).hexdigest()
  assert digest == 'b84a66ca805566abeab5bbd23c67cd665e84caa85bcadd365bd2b1ee887417c5'
  # 既有非空 limits 的条目（旧语料 6 条中的 2 条 legacy；另 4 条仓内条目由
  # test_reference_samples_preserve_text_and_complete_limits 逐字钉住）不由允许表放宽。
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
