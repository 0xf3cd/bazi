# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize('defect,optimized,expected', [
  ('none', True, '1 passed, 1 deselected'),
  ('missing', True, 'Input contracts without rejection tests'),
  ('unknown', True, 'unknown input contracts'),
  ('none', False, 'requires python -O'),
])
def test_selection_checks_its_input_roster(
  tmp_path: Path, defect: str, optimized: bool, expected: str,
) -> None:
  root = Path(__file__).parent
  (tmp_path / 'conftest.py').write_bytes((root / 'conftest.py').read_bytes())
  (tmp_path / 'api_contract.py').write_text("INPUT_CONTRACTS = {'fixture': 'entry'}\n", encoding='utf-8')
  name = 'other' if defect == 'unknown' else 'entry'
  marker = '' if defect == 'missing' else f"@pytest.mark.input_contract('fixture', '{name}')\n"
  (tmp_path / 'test_sample.py').write_text(
    'import pytest\n' + marker + 'def test_rejection():\n  assert True\n'
    'def test_not_selected():\n  raise RuntimeError("unselected")\n',
    encoding='utf-8',
  )
  result = subprocess.run(
    [sys.executable, *(['-O'] if optimized else []), '-m', 'pytest', '--input-contracts', '-q'],
    cwd=tmp_path, capture_output=True, text=True, encoding='utf-8', timeout=30, check=False,
  )
  assert result.returncode == (0 if defect == 'none' and optimized else 4), result.stdout + result.stderr
  assert expected in result.stdout + result.stderr


@pytest.mark.optimized
def test_context_helpers_reject_wrong_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.syspath_prepend(str(Path(__file__).parent / 'context_matching'))
  from matching_samples import match, rel_match, occurrences, relationship_evidence, obtained_transits

  with pytest.raises(AssertionError):
    occurrences(rel_match())
  with pytest.raises(AssertionError):
    relationship_evidence(match())
  with pytest.raises(AssertionError):
    obtained_transits(rel_match())


@pytest.mark.optimized
def test_transit_helper_rejects_unavailable_year(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.syspath_prepend(str(Path(__file__).parent / 'analyzer/relationship'))
  from relationship_samples import at_year
  from bazi.bazi import Bazi
  from bazi.bazi_chart import BaziChart
  from bazi.transit_chart import TransitChart

  transits = TransitChart(BaziChart(Bazi.create('2000-01-01 12:00', 'male')))
  with pytest.raises(AssertionError):
    at_year(transits, 1900)
