# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re

from pathlib import Path

import pytest

import bazi
from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase


def test_bundled_source_is_next_to_module() -> None:
  assert DEFAULT_SOURCE_PATH == Path(bazi.knowledge.__file__).with_name('knowledge_data.json')


def test_root_lazily_resolves_a_runtime_module(monkeypatch: pytest.MonkeyPatch) -> None:
  module = bazi.knowledge
  monkeypatch.delattr(bazi, 'knowledge')
  assert bazi.knowledge is module


def test_rule_source_pointers_resolve() -> None:
  root = Path(__file__).resolve().parents[1]
  knowledge = KnowledgeBase.load()
  identifiers = knowledge.objects.keys() | knowledge.sources.keys() | knowledge.entries.keys()
  paths = [*(root / 'bazi').rglob('*.py'), *(root / 'docs').rglob('*.md'),
    *(root / name for name in ('README.md', 'API_CONTRACT.md', 'AGENTS.md', 'CONTRIBUTING.md'))]
  for path in paths:
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
      for identifier in re.findall(r'\b(?:concept|shensha|repository)\.[a-z0-9_]+(?:\.[a-z0-9_]+)*', line):
        assert identifier in identifiers, f'{path.relative_to(root)}:{number}: Unknown knowledge ID: {identifier}'
