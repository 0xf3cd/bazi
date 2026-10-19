# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_package_init.py

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

import bazi


ROOT = Path(__file__).resolve().parents[1]

LAZY = ('bazi', 'bazi_chart', 'analyzer', 'knowledge', 'context_matching', 'transits', 'transit_chart', 'chart_text')


def test_dir_lists_lazy_submodules_unimported() -> None:
  code = (
    'import sys, bazi\n'
    f'lazy = {LAZY!r}\n'
    'assert all(f"bazi.{name}" not in sys.modules for name in lazy), "imported too early"\n'
    'assert all(name in dir(bazi) for name in lazy), sorted(set(lazy) - set(dir(bazi)))\n'
    'assert all(f"bazi.{name}" not in sys.modules for name in lazy), "dir() imported a submodule"\n'
  )
  result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True, check=False)
  assert result.returncode == 0, result.stderr


def test_dir_covers_every_declared_name() -> None:
  assert set(bazi.__all__) <= set(dir(bazi))
  assert dir(bazi) == sorted(dir(bazi))


@pytest.mark.parametrize('name, module', sorted(bazi._ENTRY_MODULES.items()))
def test_entry_attribute_names_its_module(name: str, module: str) -> None:
  assert getattr(importlib.import_module(module), name).__module__ == module
  with pytest.raises(AttributeError, match=f'use: from {module} import {name}'):
    getattr(bazi, name)


def test_unknown_attribute_has_no_hint() -> None:
  with pytest.raises(AttributeError) as error:
    bazi.not_a_name # noqa: B018
  assert str(error.value) == "module 'bazi' has no attribute 'not_a_name'"


def test_chart_text_loads_on_demand_outside_all() -> None:
  code = (
    'import sys, bazi\n'
    'assert "chart_text" not in bazi.__all__ and "chart_text" in dir(bazi)\n'
    'assert "bazi.chart_text" not in sys.modules\n'
    'from bazi import chart_text as imported\n'
    'assert bazi.chart_text is imported and callable(bazi.chart_text.chart_text)\n'
    'namespace = {}\n'
    'exec("from bazi import *", namespace)\n'
    'assert "chart_text" not in namespace\n'
  )
  result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True, check=False)
  assert result.returncode == 0, result.stderr


def test_entry_table_names_the_documented_entries() -> None:
  assert set(bazi._ENTRY_MODULES) == {
    'Bazi', 'BaziChart', 'TransitChart', 'RelationshipAnalyzer', 'AtBirthAnalysis', 'TransitAnalysis',
    'BaziConfig', 'KnowledgeBase',
  }
