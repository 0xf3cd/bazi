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

from knowledge_additions import BACKFILL_SOURCE_IDS, BACKFILL_ENTRY_IDS
from knowledge_errata import SOURCE_BACKFILL, before_errata


KNOWLEDGE = KnowledgeBase.load()


def _assert_backfill(data: dict[str, Any], changes: dict[str, Any]) -> None:
  assert set(changes) == {'base_sha', 'entries', 'reason'}
  # ced09f2 is the corpus immediately before this eleven-entry backfill.
  assert changes['base_sha'] == 'ced09f24e6690d485386b91918db2a57f217de31'
  assert set(changes['entries']) == set(BACKFILL_ENTRY_IDS) and len(BACKFILL_ENTRY_IDS) == 11
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


def test_backfill_allowance_is_exact() -> None:
  _assert_backfill(json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8')), SOURCE_BACKFILL)


@pytest.mark.parametrize('mutation', [
  'extra_id', 'unlisted_field', 'wrong_old', 'wrong_new', 'missing_pair', 'empty_reason',
])
def test_backfill_rejects_wider_allowance(mutation: str) -> None:
  changes = deepcopy(SOURCE_BACKFILL)
  first = changes['entries'][BACKFILL_ENTRY_IDS[0]]
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
    _assert_backfill(json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8')), changes)


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
    'unverified': 234, 'witnessed': 62, 'editorial': 22, 'repository_attributed': 8,
  }
  assert len(KNOWLEDGE.query()) == 19
  assert KNOWLEDGE.entry('legacy.shishen.SH-021').sources == ()


@pytest.mark.parametrize('claim_id', BACKFILL_ENTRY_IDS)
def test_single_witness_cannot_promote(claim_id: str) -> None:
  promoted = replace(KNOWLEDGE.entry(claim_id), show_by_default=True, applicability='unconditional')
  with pytest.raises(ValueError, match='Default entry needs independent lineages'):
    KnowledgeBase(tuple(KNOWLEDGE.objects.values()), (), tuple(KNOWLEDGE.sources.values()), (promoted,))


def test_backfill_reload_renders_text_limits(tmp_path: Path) -> None:
  path = tmp_path / 'knowledge.json'
  path.write_text(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'), encoding='utf-8')
  loaded = KnowledgeBase.load(path)
  for claim_id in BACKFILL_ENTRY_IDS:
    entry = loaded.entry(claim_id)
    assert entry == KNOWLEDGE.entry(claim_id)
    rendered = loaded.render(entry)
    assert entry.text in rendered and '仅供参考' in rendered and '前提待梳理' in rendered
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
