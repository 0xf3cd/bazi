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
from bazi.context_matching import ContextResult, ContextProfile, evaluate_context
from bazi.knowledge import KnowledgeBase
from bazi.record_migration import migrate_knowledge_json, migrate_chart_json, migrate_context_json
from bazi.school import Anchor, BaziConfig, BaziSchool

from knowledge_additions import AUXILIARY_OBJECT_IDS, AUXILIARY_SOURCE_IDS, AUXILIARY_ENTRY_IDS


def _records() -> dict[str, Any]:
  records: dict[str, Any] = json.loads((Path(__file__).with_name('data') / 'v200_records.json').read_text(encoding='utf-8'))
  return records


def _text(value: object) -> str:
  return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def _rebuilt_chart() -> BaziChart:
  record = _records()['chart']
  school = BaziSchool.from_json({**record['school'], 'kongwang_anchor': Anchor.DAY.name})
  return BaziChart(Bazi.create(
    record['birth_time'], record['gender'],
    BaziConfig.from_values(
      precision=record['precision'], backend=record['backend'],
      dayun_year_rule=record['dayun_year_rule'], school=school,
    ),
  ))


def test_default_inputs_preserve_v200_chart() -> None:
  current = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male')).json
  assert current['school']['kongwang_anchor'] == 'DAY'
  del current['school']['kongwang_anchor'] # type: ignore[misc] # Compare the old shape without deriving defaults from its record.
  assert {key: value for key, value in current.items() if key != 'schema_version'} == _records()['chart']


def test_v200_chart_requires_explicit_rebuild() -> None:
  records = _records()
  assert records['source_sha'] == 'ddfe16e7c51d695167b09cc4c2f64ba46e7565c3'
  with pytest.raises(ValueError, match='Unsupported chart schema version'):
    BaziChart.from_json(records['chart'])
  with pytest.raises(ValueError, match='Missing school field: kongwang_anchor'):
    migrate_chart_json(records['chart'])
  original = _rebuilt_chart()
  assert {key: value for key, value in original.json.items() if key not in ('school', 'schema_version')} == {
    key: value for key, value in records['chart'].items() if key != 'school'
  }
  assert {key: value for key, value in original.json['school'].items() if key != 'kongwang_anchor'} == records['chart']['school']
  assert original.json['school']['kongwang_anchor'] == 'DAY'
  restored = BaziChart.from_json(original.json)
  assert restored.json == original.json
  assert restored.bazi == original.bazi
  assert restored != original
  assert restored.json['schema_version'] == 1 and 'record_version' not in restored.json
  detached = restored.json
  detached['gender'] = 'female'
  assert restored.json == original.json
  inconsistent = original.json
  inconsistent['pillars']['day'] = '甲子'
  with pytest.raises(ValueError):
    BaziChart.from_json(inconsistent)


def test_v200_records_keep_distinct_contracts() -> None:
  records = _records()
  knowledge_text = _text(records['knowledge'])
  with pytest.raises(ValueError, match='migrate_knowledge_json'):
    KnowledgeBase.from_json(knowledge_text)
  migrated = migrate_knowledge_json(knowledge_text)
  knowledge = KnowledgeBase.from_json(migrated.json_text)
  assert json.loads(knowledge.export_json()) == {**records['knowledge'], 'schema_version': 2}
  assert hash(knowledge) == hash(KnowledgeBase.from_json(migrated.json_text))
  assert records['knowledge']['schema_version'] == 1
  current = KnowledgeBase.load()
  new_objects = {'shensha.kongwang', *AUXILIARY_OBJECT_IDS}
  new_sources = {
    'yuanhai_ziping.kongwang', 'sanming_tonghui.kongwang', 'luoluzi_xiaoxifu.kongwang',
    'wuxing_jingji.kongwang', 'repository.kongwang',
    *AUXILIARY_SOURCE_IDS,
  }
  new_entries = {'shensha.kongwang.xunkong', 'shensha.kongwang.lookup', 'shensha.kongwang.repository', *AUXILIARY_ENTRY_IDS}
  old = KnowledgeBase(
    tuple(value for key, value in current.objects.items() if key not in new_objects),
    tuple(current.contexts.values()),
    tuple(value for key, value in current.sources.items() if key not in new_sources),
    tuple(value for key, value in current.entries.items() if key not in new_entries),
  )
  old_data = {**json.loads(old.export_json()), 'schema_version': 1}
  assert hashlib.sha256(_text(old_data).encode()).hexdigest() == records['full_knowledge_sha256']
  context_text = _text(records['context'])
  with pytest.raises(ValueError, match='Unsupported record version'):
    ContextResult.from_json(context_text)
  with pytest.raises(ValueError, match='Missing school field: kongwang_anchor'):
    migrate_context_json(context_text)
  assert records['context']['record_version'] == 4


def test_auxiliary_knowledge_is_append_only() -> None:
  current = KnowledgeBase.load()
  objects = tuple(value for key, value in current.objects.items() if key not in AUXILIARY_OBJECT_IDS)
  sources = tuple(value for key, value in current.sources.items() if key not in AUXILIARY_SOURCE_IDS)
  entries = tuple(value for key, value in current.entries.items() if key not in AUXILIARY_ENTRY_IDS)
  old = KnowledgeBase(objects, tuple(current.contexts.values()), sources, entries)
  assert (len(objects), len(old.contexts), len(sources), len(entries), len(old.query())) == (32, 10, 18, 305, 19)
  old_data = {**json.loads(old.export_json()), 'schema_version': 1}
  assert hashlib.sha256(_text(old_data).encode()).hexdigest() == '64a1c29572de1d45e6e3a19361823af0da0b961eb25b9c3bcb19b6d5e29fa7f4'
  for registry, prefix, additions in (
    (current.objects, old.objects, AUXILIARY_OBJECT_IDS),
    (current.sources, old.sources, AUXILIARY_SOURCE_IDS),
    (current.entries, old.entries, AUXILIARY_ENTRY_IDS),
  ):
    assert tuple(registry) == (*prefix, *additions)
  assert current.contexts == old.contexts
  assert current.query() == old.query()


def test_current_context_restores_without_recheck() -> None:
  context = evaluate_context(
    _rebuilt_chart(), criterion_id='editorial.guansha_coexistence.v1',
    profile=ContextProfile(observation_scope='natal'),
  )
  context_text = context.export_json()
  restored = ContextResult.from_json(context_text)
  assert restored == context
  assert context.export_json() == context_text
  data = json.loads(context_text)
  assert data['criterion'] == _records()['context']['criterion']
  assert data['occurrences'] == _records()['context']['occurrences']
  # A structurally valid recorded observation is restored, not silently re-evaluated or certified.
  data['criterion']['observations']['observed_coexistence'] = True
  restored = ContextResult.from_json(_text(data))
  assert restored.criterion.observations['observed_coexistence']
  assert not context.criterion.observations['observed_coexistence']
  del data['input']['config']['school']['kongwang_anchor']
  with pytest.raises(ValueError, match='Missing school field: kongwang_anchor'):
    ContextResult.from_json(_text(data))
  chart = _rebuilt_chart().json
  del chart['school']['kongwang_anchor'] # type: ignore[misc] # Deliberately incomplete current record.
  with pytest.raises(ValueError, match='Missing school field: kongwang_anchor'):
    BaziChart.from_json(chart)


@pytest.mark.parametrize('version', [True, 0, 1, 3, '2', None])
def test_knowledge_record_rejects_bad_versions(version: object) -> None:
  record = _records()['knowledge']
  record['schema_version'] = version
  with pytest.raises(ValueError):
    KnowledgeBase.from_json(_text(record))


@pytest.mark.parametrize('version', [True, 0, 1, 2, 3, 4, 6, '5', None])
def test_context_record_requires_its_own_version(version: object) -> None:
  record = _records()['context']
  record['record_version'] = version
  with pytest.raises(ValueError, match='Unsupported record version'):
    ContextResult.from_json(_text(record))


def test_generator_cached_tuple_lifetimes() -> None:
  chart = _rebuilt_chart()
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
def test_gender_aliases_keep_string_domain(alias: str) -> None:
  assert alias in BaziGender.__members__
  with pytest.raises(ValueError):
    Bazi.create(datetime(2000, 1, 1, 12), alias)
