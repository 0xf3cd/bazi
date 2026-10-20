# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
from dataclasses import fields, is_dataclass
from pathlib import Path

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

from bazi.rules import BaziRules, TianganRules, DizhiRules, ShenshaRules
from bazi.school import BaziSchool, BaziConfig
from run_package_checks import source_files


DOCUMENT = Path(__file__).resolve().parents[2] / 'docs/guides/rule-coverage.md'


@pytest.mark.parametrize('record', [BaziRules, TianganRules, DizhiRules, ShenshaRules, BaziSchool, BaziConfig])
def test_coverage_lists_current_definitions(record: type) -> None:
  text = DOCUMENT.read_text(encoding='utf-8')
  references = set(re.findall(r'\{py:attr\}`~?(bazi\.(?:rules|school)\.[\w.]+)`', text))
  prefix = f'{record.__module__}.{record.__qualname__}.'
  names = (field.name for field in fields(record)) if is_dataclass(record) else iter(record.__annotations__)
  expected = {prefix + name for name in names if not name.startswith('_')}
  assert {name for name in references if name.startswith(prefix)} == expected


def test_coverage_guide_is_in_sdist_inputs() -> None:
  root = Path(__file__).resolve().parents[2]
  assert DOCUMENT.relative_to(root).as_posix() in source_files(root)
