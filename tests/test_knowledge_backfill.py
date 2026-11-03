# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase

from knowledge_additions import BACKFILL_SOURCE_IDS, BACKFILL_ENTRY_IDS, FOLLOWUP_SOURCE_IDS, FOLLOWUP_ENTRY_IDS
from knowledge_errata import SOURCE_BACKFILL, SOURCE_FOLLOWUP, before_errata


KNOWLEDGE = KnowledgeBase.load()
BACKFILLS = (
  (SOURCE_BACKFILL, BACKFILL_ENTRY_IDS, 'ced09f24e6690d485386b91918db2a57f217de31'),
  (SOURCE_FOLLOWUP, FOLLOWUP_ENTRY_IDS, 'e5d8956b32f872178f802948b108dfb046ab245b'),
)


def _assert_backfill(
  data: dict[str, Any],
  changes: dict[str, Any],
  entry_ids: tuple[str, ...] = BACKFILL_ENTRY_IDS,
  base_sha: str = 'ced09f24e6690d485386b91918db2a57f217de31',
) -> None:
  assert set(changes) == {'base_sha', 'entries', 'reason'}
  assert changes['base_sha'] == base_sha
  assert set(changes['entries']) == set(entry_ids)
  assert isinstance(changes['reason'], str) and changes['reason'].strip()
  originals = {
    'sources': [], 'source_state': 'unverified', 'attribution': '旧语料，出处未核',
    'viewpoint': '旧语料（未核）', 'limits': [],
  }
  current = {row['claim_id']: row for row in data['entries']}
  for claim_id, fields in changes['entries'].items():
    assert set(fields) == set(originals)
    for field, pair in fields.items():
      assert isinstance(pair, list) and len(pair) == 2
      old, new = pair
      assert old == originals[field] and new == current[claim_id][field] and old != new, (claim_id, field)
    original = before_errata(current[claim_id], fields)
    assert all(original[field] == value for field, value in originals.items())


@pytest.mark.parametrize('changes,entry_ids,base_sha', BACKFILLS)
def test_backfill_allowance_is_exact(changes: dict[str, Any], entry_ids: tuple[str, ...], base_sha: str) -> None:
  assert len(BACKFILL_ENTRY_IDS) == 11 and len(FOLLOWUP_ENTRY_IDS) == 2
  assert set(BACKFILL_ENTRY_IDS).isdisjoint(FOLLOWUP_ENTRY_IDS)
  _assert_backfill(json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8')), changes, entry_ids, base_sha)


@pytest.mark.parametrize('mutation', [
  'extra_id', 'unlisted_field', 'wrong_old', 'wrong_new', 'missing_pair', 'empty_reason',
])
@pytest.mark.parametrize('changes,entry_ids,base_sha', BACKFILLS)
def test_backfill_rejects_wider_allowance(
  mutation: str,
  changes: dict[str, Any],
  entry_ids: tuple[str, ...],
  base_sha: str,
) -> None:
  changes = deepcopy(changes)
  first = changes['entries'][entry_ids[0]]
  if mutation == 'extra_id':
    changes['entries']['legacy.shishen.SH-001'] = deepcopy(first)
  elif mutation == 'unlisted_field':
    first['text'] = ['旧句', '改句']
  elif mutation == 'wrong_old':
    first['attribution'][0] = '不同旧值'
  elif mutation == 'wrong_new':
    first['attribution'][1] = '未准的新值'
  elif mutation == 'missing_pair':
    first['sources'].pop()
  else:
    assert mutation == 'empty_reason'
    changes['reason'] = ''
  with pytest.raises(AssertionError):
    _assert_backfill(json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8')), changes, entry_ids, base_sha)


def test_backfill_metadata_is_pinned() -> None:
  rows = [asdict(KNOWLEDGE.sources[key]) for key in BACKFILL_SOURCE_IDS]
  payload = json.dumps({'sources': rows, 'changes': SOURCE_BACKFILL}, ensure_ascii=False, sort_keys=True)
  # Captured from the two new source records and this batch's exact allowance.
  assert sha256(payload.encode('utf-8')).hexdigest() == '31c10c6c7d14a65c3292c163dc7e73b6459a4d9a523be19e2eef72fa5a2514d9'
  selected = tuple(key for key in KNOWLEDGE.sources if key in BACKFILL_SOURCE_IDS)
  assert selected == BACKFILL_SOURCE_IDS
  positions = tuple(tuple(KNOWLEDGE.sources).index(key) for key in selected)
  assert positions == tuple(range(positions[0], positions[0] + len(selected)))


def test_backfill_keeps_one_witness_per_entry() -> None:
  modern, historical = BACKFILL_SOURCE_IDS
  for index, source_id in enumerate(BACKFILL_SOURCE_IDS):
    selected = KNOWLEDGE.query(source_id=source_id, include_reference_only=True)
    expected = BACKFILL_ENTRY_IDS[:10] if index == 0 else BACKFILL_ENTRY_IDS[10:]
    assert {entry.claim_id for entry in selected} == set(expected)
    assert KNOWLEDGE.query(source_id=source_id) == ()
    for entry in selected:
      assert entry.sources == (source_id,) and entry.source_state == 'witnessed'
      assert entry.applicability == 'unresolved' and entry.premise == '' and entry.contexts == ()
      assert entry.show_by_default is False and entry.legacy is not None
  assert (KNOWLEDGE.sources[modern].lineage, KNOWLEDGE.sources[historical].lineage) == ('guoguan_wenhua', 'ditiansui')
  assert (KNOWLEDGE.sources[modern].text_layer, KNOWLEDGE.sources[historical].text_layer) == ('editorial', 'baiwen')
  assert Counter(entry.source_state for entry in KNOWLEDGE.entries.values()) == {
    'unverified': 232, 'witnessed': 64, 'editorial': 22, 'repository_attributed': 8,
  }
  assert len(KNOWLEDGE.query()) == 19
  assert KNOWLEDGE.entry('legacy.shishen.SH-021').sources == ()


@pytest.mark.parametrize('claim_id', BACKFILL_ENTRY_IDS + FOLLOWUP_ENTRY_IDS)
def test_single_witness_cannot_promote(claim_id: str) -> None:
  promoted = replace(
    KNOWLEDGE.entry(claim_id),
    show_by_default=True, applicability='unconditional', premise='', contexts=(), legacy=None,
  )
  with pytest.raises(ValueError, match='Default entry needs independent lineages'):
    KnowledgeBase(tuple(KNOWLEDGE.objects.values()), (), tuple(KNOWLEDGE.sources.values()), (promoted,))


def test_backfill_reload_renders_text_limits(tmp_path: Path) -> None:
  path = tmp_path / 'knowledge.json'
  path.write_text(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'), encoding='utf-8')
  loaded = KnowledgeBase.load(path)
  for claim_id in BACKFILL_ENTRY_IDS + FOLLOWUP_ENTRY_IDS:
    entry = loaded.entry(claim_id)
    assert entry == KNOWLEDGE.entry(claim_id)
    rendered = loaded.render(entry)
    assert entry.text in rendered and '仅供参考' in rendered
    if entry.applicability == 'unresolved':
      assert '前提待梳理' in rendered
    else:
      assert entry.applicability == 'described' and entry.premise in rendered
    marked = loaded.render(entry, premise_verdict='UNKNOWN')
    assert '默认展示：否' in marked and '前提判别：UNKNOWN' in marked
    assert loaded.sources[entry.sources[0]].limitations in rendered
    assert all(limit in rendered for limit in entry.limits)
    hidden = loaded.render(entry, show_sources=False)
    assert entry.text in hidden and all(limit in hidden for limit in entry.limits)
  ji = loaded.entry('legacy.tiangan.ji.personality')
  assert ji.text.endswith('外随和内坚忍。')
  assert loaded.sources[ji.sources[0]].excerpt.startswith('己日：' + ji.text[:-1] + '，')
  historic = loaded.sources[BACKFILL_SOURCE_IDS[1]]
  assert historic.excerpt == '丙火猛烈，欺霜侮雪。'
  assert historic.url.endswith('oldid=2600158')


def test_followup_restores_previous_corpus() -> None:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  data['entries'] = [before_errata(row, SOURCE_FOLLOWUP['entries'].get(row['claim_id'], {})) for row in data['entries']]
  data['sources'] = [row for row in data['sources'] if row['source_id'] not in FOLLOWUP_SOURCE_IDS]
  payload = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
  assert sha256(payload.encode('utf-8')).hexdigest() == 'a6b66f2255f456d11eec2a3bd201a7824f63fb78818d5e477eeec9c3e17b62fc'


def test_followup_metadata_is_pinned() -> None:
  rows = [asdict(KNOWLEDGE.sources[key]) for key in FOLLOWUP_SOURCE_IDS]
  payload = json.dumps({'sources': rows, 'changes': SOURCE_FOLLOWUP}, ensure_ascii=False, sort_keys=True)
  assert sha256(payload.encode('utf-8')).hexdigest() == '9f1a29b74957f653cb28a805b46fd1a19b4713e1cbcd8ba19ed8a0a657c035f4'
  assert tuple(KNOWLEDGE.sources)[-2:] == FOLLOWUP_SOURCE_IDS
  for claim_id, source_id in zip(FOLLOWUP_ENTRY_IDS, FOLLOWUP_SOURCE_IDS):
    entry = KNOWLEDGE.entry(claim_id)
    assert entry.sources == (source_id,) and entry.source_state == 'witnessed'
    assert not entry.show_by_default and KNOWLEDGE.query(source_id=source_id) == ()
    assert KNOWLEDGE.query(source_id=source_id, include_reference_only=True) == (entry,)
  bing, geng = map(KNOWLEDGE.entry, FOLLOWUP_ENTRY_IDS)
  assert bing.applicability == 'unresolved' and bing.premise == '' and bing.contexts == ()
  assert geng.applicability == 'described' and geng.contexts == ('tiangan.geng_regulated_transit',)
  assert geng.premise == '如果庚金日主盘中的庚金行运有制有化，后天有教养'
  with pytest.raises(ValueError, match='Ineligible default entry'):
    replace(geng, show_by_default=True)
  assert '急躁' in bing.text and '急燥' in rows[0]['excerpt']
  assert all(term in rows[1]['excerpt'] for term in ('庚金如为忌神', '有制有化', '后天有教养', '还可能有成'))
  for claim_id in ('legacy.tiangan.yi.opportunity', 'legacy.shishen.SH-066', 'legacy.shishen.SH-180'):
    assert KNOWLEDGE.entry(claim_id).sources == () and KNOWLEDGE.entry(claim_id).source_state == 'unverified'
