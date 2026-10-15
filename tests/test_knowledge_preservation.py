# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from hashlib import sha256
from pathlib import Path

from bazi.defines import Shishen, Tiangan
from bazi.knowledge import KnowledgeBase, KnowledgeEntry, object_id


KNOWLEDGE_BASE = KnowledgeBase.load()
BASELINE = json.loads((Path(__file__).with_name('data') / 'description_legacy_baseline.json').read_text(encoding='utf-8'))
# 45 个允许改写 attribution 的 ID；limits 改写不进本文件的行指纹，由 test_knowledge 的允许表钉。
ATTRIBUTION_ALLOWED: frozenset[str] = frozenset(
  claim_id for claim_id, fields in json.loads(
    (Path(__file__).with_name('data') / 'corpus_allowed_changes.json').read_text(encoding='utf-8')
  )['allowed_changes'].items() if 'attribution' in fields
)
OLD_ATTRIBUTION: str = 'Legacy corpus; source unverified'
NEW_ATTRIBUTION: str = '作者据网络材料归纳，原始出处未核'


def _positioned_entries(subject: Tiangan | Shishen, field: str) -> tuple[KnowledgeEntry, ...]:
  return tuple(sorted(
    (
      entry for entry in KNOWLEDGE_BASE.entries.values()
      if entry.legacy is not None and entry.legacy.object_id == object_id(subject) and entry.legacy.field == field
    ),
    key=lambda entry: entry.legacy.ordinal if entry.legacy is not None else -1,
  ))


def test_complete_text_order_and_metadata_fingerprints_are_conserved() -> None:
  text_rows: list[list[str]] = [[], []]
  claim_rows: list[str] = []
  for subjects, field_order, prefix, rows in (
    (Shishen, ('general', 'in_good_status', 'in_bad_status', 'relationship'), 'S', text_rows[0]),
    (Tiangan, ('general', 'personality'), 'T', text_rows[1]),
  ):
    for subject in subjects:
      for field in field_order:
        for entry in _positioned_entries(subject, field):
          assert entry.legacy is not None
          rows.append(f'{prefix}:{subject}:{field}:{entry.text}')
          # claim_rows 对 45 个允许 ID 做反向规范化后保持原指纹，不需要重钉新 hash。
          attribution = OLD_ATTRIBUTION if entry.claim_id in ATTRIBUTION_ALLOWED else entry.attribution
          claim_rows.append('\0'.join((
            'C', str(subject), field, entry.claim_id, entry.text,
            ','.join(entry.sources), attribution,
            ','.join(entry.legacy.conditions), entry.output,
          )))
          assert entry.text == entry.text.strip() and entry.text.endswith('。')
  shishen_rows, tiangan_rows = text_rows
  assert sha256('\n'.join(shishen_rows).encode()).hexdigest() == '5d46532e1f6800a368225bd5d1457c05d8906d14c06af156a623730f23e0ae5e'
  assert sha256('\n'.join(tiangan_rows).encode()).hexdigest() == 'cbd11b02806a73ff5f062823d913b4d2343504e38a94ddb344a1d6caccf6133c'
  assert sha256('\n'.join(shishen_rows + tiangan_rows).encode()).hexdigest() == 'a83bd9e440aff6a83a8c8fb9ad687525291cb80c9926be55664c7e90f6ba7b48'
  assert sha256('\n'.join(shishen_rows + tiangan_rows + claim_rows).encode()).hexdigest() == '42daeca42c35c59f30bbc5fa4a259f94edfec8e5e0b46f2ad113c7f4a5d6272d'


def test_original_source_registry_fingerprint_and_boundaries_are_conserved() -> None:
  rows: list[str] = []
  for source_id in BASELINE['sources']:
    record = KNOWLEDGE_BASE.sources[source_id]
    values = (
      source_id, record.work, record.attribution, record.edition, record.locator,
      record.url, record.text_layer, record.lineage, record.excerpt, record.supports,
      record.limitations,
    )
    assert all(values)
    assert record.text_layer == ('editorial' if source_id == 'editorial' else 'baiwen')
    rows.append('\0'.join(values))
  assert sha256('\n'.join(rows).encode()).hexdigest() == '7ccb163266026302dfe340108e28c9018cccfec48001f696c2f5056893c06a3e'
  assert KNOWLEDGE_BASE.sources['yuanhai_ziping_relations'].locator == 'PDF p. 6, right leaf, paragraph beginning “生我者為正印偏印”'
  assert KNOWLEDGE_BASE.sources['yuanhai_ziping_stem_table'].locator == 'PDF p. 8, “天干五阳通变” and “天干五阴通变” tables'
  for source_id in ('mingli_tanyuan_stem_basics', 'mingli_tanyuan_shishen_definitions'):
    assert KNOWLEDGE_BASE.sources[source_id].work == '《命理探源》'
    assert KNOWLEDGE_BASE.sources[source_id].edition == '版心题《命理探原》'


def test_default_and_reference_selection_preserve_all_old_positions() -> None:
  k = KNOWLEDGE_BASE
  for subjects, complete_counts, expected_default_total in (
    (Shishen, (25, 23, 23, 23, 20, 20, 22, 22, 19, 22), 9),
    (Tiangan, None, 10),
  ):
    default_total = 0
    complete_total = 0
    for index, subject in enumerate(subjects):
      assert isinstance(subject, (Tiangan, Shishen))
      expected = [row['claim'] for row in BASELINE['rows'] if row['subject_kind'] == subjects.__name__ and row['subject'] == str(subject)]
      if complete_counts is not None:
        assert len(expected) == complete_counts[index]
      complete_total += len(expected)
      default = k.query(object_id=object_id(subject))
      assert tuple(entry.claim_id for entry in default) == tuple(claim['claim_id'] for claim in expected if claim['output'] == 'default')
      default_total += len(default)
      for include_reference_only in (False, True):
        rendered = k.render_subject(object_id(subject), include_reference_only=include_reference_only)
        for claim in expected:
          assert (claim['text'] in rendered) is (include_reference_only or claim['output'] == 'default')
        assert ('仅供参考' in rendered) is include_reference_only
      for entry in default:
        assert entry.source_state == 'witnessed' and entry.applicability == 'unconditional'
        assert entry.legacy is not None and not entry.legacy.conditions
        assert len({k.sources[source_id].lineage for source_id in entry.sources}) >= 2
    assert default_total == expected_default_total
    assert complete_total == (219 if subjects is Shishen else 72)
  assert 'shishen.jiecai.definition' not in k.entries


def test_legacy_reference_classification_is_not_upgraded_by_projection() -> None:
  k = KNOWLEDGE_BASE
  conditional_shishen: set[str] = set()
  for entry in k.entries.values():
    if entry.legacy is None:
      continue
    if not entry.sources:
      assert entry.source_state == 'unverified'
      # 45 个允许 ID 精确等于新署名，其余仍等于旧署名；不因投影升级输出资格。
      assert entry.attribution == (NEW_ATTRIBUTION if entry.claim_id in ATTRIBUTION_ALLOWED else OLD_ATTRIBUTION)
      assert entry.output == 'reference_only'
      if entry.legacy.object_id.startswith('shishen.') and entry.legacy.conditions:
        conditional_shishen.add(entry.claim_id)
    if entry.legacy.field in ('in_good_status', 'in_bad_status'):
      if not entry.sources:
        assert entry.legacy.conditions == ('chart_context_required',)
      assert entry.applicability != 'unconditional' and entry.output == 'reference_only'
    if entry.sources == ('editorial',):
      assert entry.source_state == 'editorial' and entry.output == 'reference_only'
      assert entry.attribution == 'Repository editorial'
  assert len(conditional_shishen) == 79
