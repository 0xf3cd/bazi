# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import hashlib
import json
from datetime import datetime
from itertools import islice
from pathlib import Path
from typing import Any

import pytest

from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextResult
from bazi.knowledge import KnowledgeBase


def _records() -> dict[str, Any]:
  records: dict[str, Any] = json.loads((Path(__file__).with_name('data') / 'v200_records.json').read_text(encoding='utf-8'))
  return records


def _text(value: object) -> str:
  return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def test_v200_chart_record_recomputes_without_changing_the_mapping_contract() -> None:
  records = _records()
  assert records['source_sha'] == 'ddfe16e7c51d695167b09cc4c2f64ba46e7565c3'
  original = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
  restored = BaziChart.from_json(records['chart'])
  assert restored.json == records['chart'] == original.json
  assert restored.bazi == original.bazi
  assert restored != original
  assert 'schema_version' not in restored.json and 'record_version' not in restored.json
  detached = restored.json
  detached['gender'] = 'female'
  assert restored.json == records['chart']
  inconsistent = records['chart']
  inconsistent['pillars']['day'] = '甲子'
  with pytest.raises(ValueError):
    BaziChart.from_json(inconsistent)


def test_v200_knowledge_and_context_records_keep_their_distinct_text_contracts() -> None:
  records = _records()
  knowledge_text = _text(records['knowledge'])
  knowledge = KnowledgeBase.from_json(knowledge_text)
  assert knowledge.export_json() == knowledge_text
  assert hash(knowledge) == hash(KnowledgeBase.from_json(knowledge_text))
  assert records['knowledge']['schema_version'] == 1
  assert hashlib.sha256(KnowledgeBase.load().export_json().encode()).hexdigest() == records['full_knowledge_sha256']
  context_text = _text(records['context'])
  context = ContextResult.from_json(context_text)
  assert context.export_json() == context_text
  assert context.knowledge == knowledge
  assert records['context']['record_version'] == 4
  # A structurally valid recorded observation is restored, not silently re-evaluated or certified.
  records['context']['criterion']['observations']['observed_coexistence'] = True
  restored = ContextResult.from_json(_text(records['context']))
  assert restored.criterion.observations['observed_coexistence']
  assert not context.criterion.observations['observed_coexistence']


@pytest.mark.parametrize('version', [True, 0, 2, '1', None])
def test_knowledge_record_rejects_unknown_or_wrongly_typed_versions(version: object) -> None:
  record = _records()['knowledge']
  record['schema_version'] = version
  with pytest.raises(ValueError):
    KnowledgeBase.from_json(_text(record))


@pytest.mark.parametrize('version', [True, 0, 1, 2, 3, 5, '4', None])
def test_context_record_requires_its_own_version(version: object) -> None:
  record = _records()['context']
  record['record_version'] = version
  with pytest.raises(ValueError, match='Unsupported record version'):
    ContextResult.from_json(_text(record))


def test_generator_access_and_cached_tuple_have_different_lifetimes() -> None:
  chart = BaziChart.from_json(_records()['chart'])
  first = chart.dayun
  expected = tuple(first)
  assert expected and tuple(first) == ()
  assert tuple(chart.dayun) == expected
  assert chart.dayun is not chart.dayun
  years = chart.liunian
  prefix = tuple(islice(years, 3))
  assert len(prefix) == 3
  assert next(years) != prefix[0]
  assert tuple(islice(chart.liunian, 3)) == prefix
  assert chart.xiaoyun is chart.xiaoyun


@pytest.mark.parametrize('alias', ['乾', '坤', '阳', '阴', 'YANG', 'YIN'])
def test_gender_enum_aliases_do_not_expand_the_string_input_domain(alias: str) -> None:
  assert alias in BaziGender.__members__
  with pytest.raises(ValueError):
    Bazi.create(datetime(2000, 1, 1, 12), alias)
