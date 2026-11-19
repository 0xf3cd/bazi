# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import importlib
import runpy
import sys

from datetime import date, datetime
from pathlib import Path
from types import ModuleType

import pytest

from bazi.calendar.celestial_data.loader import DATA_DIR


@pytest.fixture
def generator() -> ModuleType:
  pytest.importorskip('celestial_calendar')
  return importlib.import_module('run_calendar_generation')


def test_lunar_generation_matches_frozen_data(generator: ModuleType) -> None:
  rows = generator._gen_lunar_rows()
  text = generator._render_lunar_table(rows, date(2026, 1, 1))
  actual = [line for line in text.splitlines() if not line.startswith('#')]
  expected = [
    line for line in (DATA_DIR / 'lunar_years.txt').read_text(encoding='utf-8').splitlines()
    if not line.startswith('#')
  ]
  assert actual == expected
  assert len(actual) == 199


def test_jieqi_generation_matches_frozen_year(generator: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(generator, 'JIEQI_START_YEAR', 2024)
  monkeypatch.setattr(generator, 'JIEQI_END_YEAR', 2024)
  monkeypatch.setattr(generator, 'EXPECTED_JIEQI_ROWS', 24)
  rows = generator._gen_jieqi_rows()
  text = generator._render_jieqi_table(rows, date(2026, 1, 1))
  actual = [line for line in text.splitlines() if not line.startswith('#')]
  expected = [
    line for line in (DATA_DIR / 'jieqi_moments.txt').read_text(encoding='utf-8').splitlines()
    if line.startswith('2024 ')
  ]
  assert actual == expected
  assert len(actual) == 24


def test_ut1_conversion_carries_and_truncates(generator: ModuleType) -> None:
  source = generator.celestial.CivilDateTime(2024, 12, 31, (23 * 3600 + 59 * 60 + 59.6) / 86400)
  assert generator._ut1_moment_to_utc8(source) == datetime(2025, 1, 1, 7, 59, 59)


def test_version_gate_rejects_changed_package(generator: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(generator.celestial, '__version__', '0.0.0')
  assert generator.__file__ is not None
  with pytest.raises(RuntimeError, match='Version gate failed'):
    runpy.run_path(generator.__file__)


def test_eot_only_writes_requested_directory(
  generator: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
  monkeypatch.setattr(generator, 'EOT_START_DATE', date(2000, 1, 1))
  monkeypatch.setattr(generator, 'EOT_SENTINEL_DATE', date(2000, 1, 3))
  monkeypatch.setattr(sys, 'argv', ['run_calendar_generation.py', '--eot-only', '--output-dir', str(tmp_path)])
  generator.main()
  encoded = (tmp_path / 'equation_of_time.bin').read_bytes()
  assert {p.name for p in tmp_path.iterdir()} == {'equation_of_time.bin'}
  header = generator.EOT_HEADER.unpack_from(encoded)
  assert header[:5] == (b'BAZIEOT1', date(2000, 1, 1).toordinal(), 3, 86400, 10)
  assert len(encoded) == 56 + 3 * 2


def test_generation_rejects_invalid_month_length(generator: ModuleType) -> None:
  with pytest.raises(RuntimeError, match='29 or 30 days'):
    generator._encode_days_counts((30, 28))
