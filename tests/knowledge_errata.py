# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from pathlib import Path
from typing import Any


SOURCE_ERRATA: dict[str, Any] = json.loads(
  (Path(__file__).with_name('data') / 'corpus_allowed_changes.json').read_text(encoding='utf-8')
)['source_errata']


def before_errata(record: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
  original: dict[str, Any] = json.loads(json.dumps(record))
  for field, (old, new) in changes.items():
    assert original[field] == new, field
    original[field] = old
  return original
