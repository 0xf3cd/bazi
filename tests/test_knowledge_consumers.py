# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from pathlib import Path

import pytest

import bazi
from bazi.knowledge import DEFAULT_SOURCE_PATH


def test_bundled_source_is_next_to_module() -> None:
  assert DEFAULT_SOURCE_PATH == Path(bazi.knowledge.__file__).with_name('knowledge_data.json')


def test_root_lazily_resolves_a_runtime_module(monkeypatch: pytest.MonkeyPatch) -> None:
  module = bazi.knowledge
  monkeypatch.delattr(bazi, 'knowledge')
  assert bazi.knowledge is module
