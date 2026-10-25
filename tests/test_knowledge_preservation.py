# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from bazi.defines import Shishen, Tiangan
from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase, KnowledgeEntry, object_id

from knowledge_additions import AUXILIARY_OBJECT_IDS, AUXILIARY_SOURCE_IDS, AUXILIARY_ENTRY_IDS


KNOWLEDGE_BASE = KnowledgeBase.load()
BASELINE = json.loads((Path(__file__).with_name('data') / 'description_legacy_baseline.json').read_text(encoding='utf-8'))
LEDGER = json.loads((Path(__file__).with_name('data') / 'corpus_allowed_changes.json').read_text(encoding='utf-8'))
# The 45 claim IDs allowed to rewrite attribution; limits rewrites stay out of this file's
# row fingerprints and are pinned by test_knowledge's allow table.
ATTRIBUTION_ALLOWED: frozenset[str] = frozenset(
  claim_id for claim_id, fields in LEDGER['allowed_changes'].items() if 'attribution' in fields
)
# Translated attributions and source fields map back to the originals, so the pinned
# fingerprints below still cover every other field.
ORIGINAL_ATTRIBUTION: dict[str, str] = {new: old for old, new in LEDGER['translated']['attribution'].items()}
TRANSLATED_SOURCES: dict[str, dict[str, list[str]]] = LEDGER['translated']['sources']
OLD_ATTRIBUTION: str = 'Legacy corpus; source unverified'
LEGACY_ATTRIBUTION: str = LEDGER['translated']['attribution'][OLD_ATTRIBUTION]
NEW_ATTRIBUTION: str = '作者据网络材料归纳，原始出处未核'


def _positioned_entries(subject: Tiangan | Shishen, field: str) -> tuple[KnowledgeEntry, ...]:
  return tuple(sorted(
    (
      entry for entry in KNOWLEDGE_BASE.entries.values()
      if entry.legacy is not None and entry.legacy.object_id == object_id(subject) and entry.legacy.field == field
    ),
    key=lambda entry: entry.legacy.ordinal if entry.legacy is not None else -1,
  ))


def test_historical_corpus_is_append_only() -> None:
  # Historical fingerprints from ddfe16e7c51d695167b09cc4c2f64ba46e7565c3 and test_record_contract.
  # Compare the loaded values to the editing source before checking its historical subsets.
  current = KnowledgeBase.load()
  source = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  for registry in ('objects', 'contexts', 'sources', 'entries'):
    assert json.loads(json.dumps([asdict(value) for value in getattr(current, registry).values()])) == source[registry]
  for objects, sources, entries, fingerprint in (
    (
      AUXILIARY_OBJECT_IDS, AUXILIARY_SOURCE_IDS, AUXILIARY_ENTRY_IDS,
      '64a1c29572de1d45e6e3a19361823af0da0b961eb25b9c3bcb19b6d5e29fa7f4',
    ),
    (
      {'shensha.kongwang', *AUXILIARY_OBJECT_IDS},
      {
        'yuanhai_ziping.kongwang', 'sanming_tonghui.kongwang', 'luoluzi_xiaoxifu.kongwang',
        'wuxing_jingji.kongwang', 'repository.kongwang', *AUXILIARY_SOURCE_IDS,
      },
      {'shensha.kongwang.xunkong', 'shensha.kongwang.lookup', 'shensha.kongwang.repository', *AUXILIARY_ENTRY_IDS},
      '15eb6b066357e68b58996fcd603972cf4a94f4b6ded70d591ddfd8595a574fa7',
    ),
  ):
    data = {**source, 'schema_version': 1}
    for registry, identifier, additions in (
      ('objects', 'object_id', objects), ('sources', 'source_id', sources), ('entries', 'claim_id', entries),
    ):
      prefix = [row for row in source[registry] if row[identifier] not in additions]
      assert [row[identifier] for row in source[registry]] == [
        *(row[identifier] for row in prefix), *(row[identifier] for row in source[registry] if row[identifier] in additions),
      ]
      data[registry] = prefix
    assert sha256((json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()).hexdigest() == fingerprint
  without_auxiliary = KnowledgeBase(
    tuple(value for key, value in current.objects.items() if key not in AUXILIARY_OBJECT_IDS),
    tuple(current.contexts.values()),
    tuple(value for key, value in current.sources.items() if key not in AUXILIARY_SOURCE_IDS),
    tuple(value for key, value in current.entries.items() if key not in AUXILIARY_ENTRY_IDS),
  )
  assert (len(without_auxiliary.objects), len(without_auxiliary.contexts), len(without_auxiliary.sources), len(without_auxiliary.entries), len(without_auxiliary.query())) == (32, 10, 18, 305, 19)
  assert current.contexts == without_auxiliary.contexts
  assert current.query() == without_auxiliary.query()


def test_text_order_fingerprints_conserved() -> None:
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
          # claim_rows reverse-normalize the 45 allowed IDs and the translated attributions
          # back to the original fingerprints, so no new hash needs pinning.
          attribution = (
            OLD_ATTRIBUTION if entry.claim_id in ATTRIBUTION_ALLOWED
            else ORIGINAL_ATTRIBUTION.get(entry.attribution, entry.attribution)
          )
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


def test_source_registry_fingerprint_conserved() -> None:
  rows: list[str] = []
  for source_id in BASELINE['sources']:
    record = asdict(KNOWLEDGE_BASE.sources[source_id])
    for field, (old, new) in TRANSLATED_SOURCES.get(source_id, {}).items():
      assert record[field] == new and BASELINE['sources'][source_id][field] == old, (source_id, field)
      record[field] = old
    values = tuple(record[field] for field in (
      'source_id', 'work', 'attribution', 'edition', 'locator', 'url', 'text_layer', 'lineage',
      'excerpt', 'supports', 'limitations',
    ))
    assert all(values)
    assert record['text_layer'] == ('editorial' if source_id == 'editorial' else 'baiwen')
    rows.append('\0'.join(values))
  assert sha256('\n'.join(rows).encode()).hexdigest() == '7ccb163266026302dfe340108e28c9018cccfec48001f696c2f5056893c06a3e'
  for source_id in ('mingli_tanyuan_stem_basics', 'mingli_tanyuan_shishen_definitions'):
    assert KNOWLEDGE_BASE.sources[source_id].work == '《命理探源》'
    assert KNOWLEDGE_BASE.sources[source_id].edition == '版心题《命理探原》'


def test_selections_preserve_old_positions() -> None:
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


def test_projection_keeps_legacy_classification() -> None:
  k = KNOWLEDGE_BASE
  conditional_shishen: set[str] = set()
  for entry in k.entries.values():
    if entry.legacy is None:
      continue
    if not entry.sources:
      assert entry.source_state == 'unverified'
      # The 45 allowed IDs equal exactly the new attribution; the rest equal the translated
      # legacy one. Projection does not upgrade output eligibility.
      assert entry.attribution == (NEW_ATTRIBUTION if entry.claim_id in ATTRIBUTION_ALLOWED else LEGACY_ATTRIBUTION)
      assert entry.output == 'reference_only'
      if entry.legacy.object_id.startswith('shishen.') and entry.legacy.conditions:
        conditional_shishen.add(entry.claim_id)
    if entry.legacy.field in ('in_good_status', 'in_bad_status'):
      if not entry.sources:
        assert entry.legacy.conditions == ('chart_context_required',)
      assert entry.applicability != 'unconditional' and entry.output == 'reference_only'
    if entry.sources == ('editorial',):
      assert entry.source_state == 'editorial' and entry.output == 'reference_only'
      assert entry.attribution == LEDGER['translated']['attribution']['Repository editorial']
  assert len(conditional_shishen) == 79
