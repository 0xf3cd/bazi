# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'docs/_ext'))

from run_doc_checks import Page, check_related
from knowledge_catalog import json_value
from bazi.common import frozendict
from bazi.context_matching import criteria
from bazi.knowledge import KnowledgeBase


class Option(Enum):
  ONE = 'one'


@dataclass(frozen=True)
class Record:
  value: str


# 字面期望钉住生产编码器；目录展示与 checker 的 criteria 值都走这一份。
@pytest.mark.parametrize('value, expected', [
  (('定义', '限制'), ['定义', '限制']),
  (frozenset({'b', 'a'}), ['a', 'b']),
  (frozendict({'key': (Option.ONE, None)}), {'key': ['one', None]}),
  (Record('text'), {'value': 'text'}),
  (str, 'builtins.str'),
  (False, False),
  (None, None),
])
def test_catalog_values_have_explicit_json_shapes(value, expected):
  assert json_value(value) == expected


def test_unsupported_values_not_stringified():
  with pytest.raises(TypeError):
    json_value(object())


def test_observation_metadata_serializes_as_names():
  for info in criteria().values():
    expected = (
      ['bazi.context_matching.NatalObservation', 'bazi.context_matching.LiunianObservation']
      if info.analysis_kind == 'context' else
      ['bazi.context_matching.NatalObservation', 'bazi.context_matching.TransitObservation']
    )
    assert json_value(info.observation_types) == expected
    assert json_value(info)['analysis_kind'] == info.analysis_kind
    assert 'observation_types' not in json_value(info)
    for name, member in vars(type(info)).items():
      if isinstance(member, property):
        json_value(getattr(info, name))


@pytest.mark.parametrize('count, label, valid', [
  (1, 'tiangan.ding.definition', True),
  (0, 'tiangan.ding.definition', False),
  (2, 'tiangan.ding.definition', False),
  (1, 'wrong-visible-label', False),
])
def test_related_entries_must_match_exactly(count, label, valid):
  identifier = 'catalog-sources-example'
  entry = KnowledgeBase.load().entry('tiangan.ding.definition')
  link = f'<a class="reference internal" href="entries.html#catalog-entries-{entry.claim_id}">{label}</a>'
  page = Page()
  page.feed(f'<section id="{identifier}">{link * count}</section>')
  if valid:
    check_related(page, identifier, (entry,))
  else:
    with pytest.raises(AssertionError, match='Related entries'):
      check_related(page, identifier, (entry,))


def test_heading_permalink_not_related_entry():
  page = Page()
  page.feed('<section id="catalog-entries-example"><a class="headerlink" href="#catalog-entries-example">¶</a></section>')
  check_related(page, 'catalog-entries-example', ())
