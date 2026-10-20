# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from dataclasses import fields
from pathlib import Path
from typing import Final

import pytest
import yaml

from bazi.knowledge import KnowledgeEntry, KnowledgeSource


SOURCE_FIELDS: Final = {
  'work': True, 'attribution': True, 'edition': True, 'locator': True,
  'url': False, 'text_layer': False, 'excerpt': True, 'supports': True, 'limitations': True,
}


@pytest.mark.parametrize('name, discussion_fields', [
  ('knowledge-correction', {'problem': True}),
  ('school-reading', {'difference': True, 'config_option': False, 'variant': False, 'viewpoint': False}),
])
def test_issue_forms_record_and_discussion_fields(
  name: str, discussion_fields: dict[str, bool],
) -> None:
  path = Path(__file__).parents[1] / '.github/ISSUE_TEMPLATE' / (name + '.yml')
  body = yaml.safe_load(path.read_text(encoding='utf-8'))['body']
  inputs = [item for item in body if 'id' in item]
  assert len({item['id'] for item in inputs}) == len(inputs)
  assert {item['id']: item['validations']['required'] for item in inputs} == {
    'claim_id': False, 'text': True, **SOURCE_FIELDS, **discussion_fields,
  }
  assert set(SOURCE_FIELDS) <= {field.name for field in fields(KnowledgeSource)}
  assert {'claim_id', 'text', 'viewpoint'} <= {field.name for field in fields(KnowledgeEntry)}
