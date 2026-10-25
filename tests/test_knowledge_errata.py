# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase

from knowledge_errata import SOURCE_ERRATA, before_errata


BASELINE_PATH = Path(__file__).with_name('data') / 'source_errata_baseline.json'
BASELINE = json.loads(BASELINE_PATH.read_text(encoding='utf-8'))


def _assert_source_errata(data: dict[str, Any], changes: dict[str, Any]) -> None:
  assert set(changes) == {'base_sha', 'sources', 'entries', 'reasons'}
  assert changes['base_sha'] == BASELINE['base_sha'] == 'be907fc56afa77dc0195437232a172b6b72fe43a'
  allowed = {
    'sources': {
      'yuanhai_ziping_stem_symbols_p69': {'excerpt', 'limitations'},
      'yuanhai_ziping_stem_symbols_p70': {'excerpt', 'limitations'},
      'mingli_tanyuan_stem_basics': {'locator', 'excerpt', 'limitations'},
      'mingli_tanyuan_shishen_definitions': {'locator', 'excerpt', 'limitations'},
      'mingli_tanyuan.minggong': {'work', 'attribution', 'edition', 'locator', 'url', 'excerpt', 'limitations'},
    },
    'entries': {'concept.minggong.zhongqi': {'text', 'attribution', 'limits'}},
  }
  assert set(changes['reasons']) == set(allowed)
  for registry, identifier in (('sources', 'source_id'), ('entries', 'claim_id')):
    assert set(changes[registry]) == set(changes['reasons'][registry]) == set(allowed[registry])
    old_rows = {row[identifier]: row for row in BASELINE[registry]}
    rows = data[registry] if registry == 'sources' else [
      row for row in data[registry] if row[identifier] in old_rows
    ]
    assert len(rows) == len(old_rows) and {row[identifier] for row in rows} == set(old_rows)
    current = {row[identifier]: row for row in rows}
    for key, fields in changes[registry].items():
      assert set(fields) == set(changes['reasons'][registry][key]) == allowed[registry][key]
      for field, pair in fields.items():
        assert isinstance(pair, list) and len(pair) == 2
        old, new = pair
        assert old == old_rows[key][field] and new == current[key][field] and old != new, (key, field)
        reason = changes['reasons'][registry][key][field]
        assert isinstance(reason, str) and reason.strip(), (key, field)
    assert [before_errata(row, changes[registry].get(row[identifier], {})) for row in rows] == BASELINE[registry]


def test_errata_baseline_is_fixed() -> None:
  assert sha256(BASELINE_PATH.read_bytes()).hexdigest() == 'd582dc1a0a6e784eadac353ecb443ee6cbca28685b62b8e10fee95868372515c'
  assert len(BASELINE['sources']) == 23
  assert [row['claim_id'] for row in BASELINE['entries']] == ['concept.minggong.zhongqi']


def test_errata_matches_old_and_current_values() -> None:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  _assert_source_errata(data, SOURCE_ERRATA)
  assert len(KnowledgeBase.load().query()) == 19


@pytest.mark.parametrize('mutation', [
  'wrong_old', 'unlisted_source_field', 'unlisted_entry_field', 'missing_new',
  'source_order', 'extra_source', 'missing_reason',
])
def test_errata_rejects_unlisted_changes(mutation: str) -> None:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  changes = deepcopy(SOURCE_ERRATA)
  source = next(row for row in data['sources'] if row['source_id'] == 'mingli_tanyuan.minggong')
  entry = next(row for row in data['entries'] if row['claim_id'] == 'concept.minggong.zhongqi')
  if mutation == 'wrong_old':
    changes['sources']['mingli_tanyuan.minggong']['edition'][0] = '错误旧值'
  elif mutation == 'unlisted_source_field':
    source['supports'] += '未列变动'
  elif mutation == 'unlisted_entry_field':
    entry['topics'].append('负控')
  elif mutation == 'missing_new':
    source['edition'] = changes['sources']['mingli_tanyuan.minggong']['edition'][0]
  elif mutation == 'source_order':
    data['sources'].reverse()
  elif mutation == 'extra_source':
    data['sources'].append({**source, 'source_id': 'negative_control'})
  else:
    assert mutation == 'missing_reason'
    changes['reasons']['sources']['mingli_tanyuan.minggong']['edition'] = ''
  KnowledgeBase._from_data(data)
  with pytest.raises(AssertionError):
    _assert_source_errata(data, changes)
