# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_hko_data_regeneration.py

import pytest

import shutil
import subprocess
import sys

from pathlib import Path


pytestmark = pytest.mark.integration


# The repo root is the level holding `src/`; this file lives at tests/integration/.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

# Paths of the two encoded tables relative to an `src/` tree (see hko_data/common.py).
JIEQI_BIN: Path = Path('src/calendar/hko_data/data/jieqi_encoded.bin')
LUNARDATE_BIN: Path = Path('src/calendar/hko_data/data/lunardate_encoded.bin')


def test_hko_data_regeneration_via_module_entry(tmp_path: Path) -> None:
  '''Issue #79: the regeneration entry must survive missing encoded data.

  When the two .bin tables (节气 jieqi / 农历 lunardate) are absent,
  `python -m src.calendar.hko_data.encoder` must rebuild them. That entry imports the
  parent packages first, and only the PEP 562 lazy imports in `src/__init__.py` /
  `src/calendar/__init__.py` keep it from tripping over the decoder's fail-fast
  (数据缺失即 RuntimeError) before it can regenerate anything. The in-process
  `test_do_encode` (tests/calendar/test_hko_data.py) never exercises this subprocess
  path — its import chain is already complete in the test process — so a regression
  back to eager imports would pass the whole suite unnoticed.
  '''

  # Sandbox: a full copy of src/ (the raw HKO txt travels with it, so encoding stays
  # offline). `__pycache__` is left out — stale bytecode must not shadow copied sources.
  sandbox: Path = tmp_path / 'sandbox'
  shutil.copytree(REPO_ROOT / 'src', sandbox / 'src', ignore=shutil.ignore_patterns('__pycache__'))

  # Knock out both encoded tables inside the copy; the repo's own data/ stays untouched.
  (sandbox / JIEQI_BIN).unlink()
  (sandbox / LUNARDATE_BIN).unlink()

  # The entry under test, exactly as users invoke it. cwd must be the sandbox root
  # (the level containing src/), not the repo root.
  result: subprocess.CompletedProcess[str] = subprocess.run(
    [sys.executable, '-m', 'src.calendar.hko_data.encoder'],
    cwd=sandbox,
    capture_output=True,
    text=True,
    timeout=60,
    check=False,
  )
  assert result.returncode == 0, f'encoder entry failed:\n{result.stdout}\n{result.stderr}'

  # Both tables rebuilt...
  assert (sandbox / JIEQI_BIN).is_file()
  assert (sandbox / LUNARDATE_BIN).is_file()

  # ...and the encoding is deterministic: byte-identical to the committed tables.
  assert (sandbox / JIEQI_BIN).read_bytes() == (REPO_ROOT / JIEQI_BIN).read_bytes()
  assert (sandbox / LUNARDATE_BIN).read_bytes() == (REPO_ROOT / LUNARDATE_BIN).read_bytes()
