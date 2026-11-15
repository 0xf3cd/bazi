# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import importlib.util
from pathlib import Path

import pytest

import bazi
from bazi.knowledge import DEFAULT_SOURCE_PATH


def test_removed_modules_are_absent() -> None:
  for name in ('descriptions', 'interpreter'):
    assert name not in bazi.__all__
    assert importlib.util.find_spec('bazi.' + name) is None
    with pytest.raises(AttributeError):
      getattr(bazi, name)
  assert DEFAULT_SOURCE_PATH == Path(bazi.knowledge.__file__).with_name('knowledge_data.json')


def test_root_lazily_resolves_a_runtime_module(monkeypatch: pytest.MonkeyPatch) -> None:
  module = bazi.knowledge
  monkeypatch.delattr(bazi, 'knowledge')
  assert bazi.knowledge is module
