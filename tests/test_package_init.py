# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_package_init.py

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

import bazi


ROOT = Path(__file__).resolve().parents[1]

LAZY = ('bazi', 'bazi_chart', 'analyzer', 'knowledge', 'context_matching', 'transits', 'transit_chart')


def test_dir_lists_lazy_submodules_without_importing() -> None:
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
def test_entry_class_attribute_points_to_its_module(name: str, module: str) -> None:
  assert getattr(importlib.import_module(module), name).__module__ == module
  with pytest.raises(AttributeError, match=f'use: from {module} import {name}'):
    getattr(bazi, name)


def test_unknown_attribute_has_no_hint() -> None:
  with pytest.raises(AttributeError) as error:
    bazi.not_a_name # noqa: B018
  assert str(error.value) == "module 'bazi' has no attribute 'not_a_name'"
