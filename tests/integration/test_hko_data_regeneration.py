# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_hko_data_regeneration.py

import pytest

import os
import shutil
import subprocess
import sys

from pathlib import Path


pytestmark = pytest.mark.integration


# The repo root is the level holding `bazi/`; this file lives at tests/integration/.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

# Paths of the two encoded tables relative to the checkout root (see hko_data/common.py).
JIEQI_BIN: Path = Path('tests/calendar/hko_data/data/jieqi_encoded.bin')
LUNARDATE_BIN: Path = Path('tests/calendar/hko_data/data/lunardate_encoded.bin')


def test_hko_data_regeneration_via_module_entry(tmp_path: Path) -> None:
  '''Issue #79: the module entry rebuilds missing encoded tables offline.

  A fresh process imports hko_data before its encoder. That import must work when
  both binary files are absent, using only the committed raw HKO text.
  '''

  sandbox: Path = tmp_path / 'sandbox'
  shutil.copytree(REPO_ROOT / 'bazi', sandbox / 'bazi', ignore=shutil.ignore_patterns('__pycache__'))
  shutil.copytree(REPO_ROOT / 'tests/calendar/hko_data', sandbox / 'tests/calendar/hko_data', ignore=shutil.ignore_patterns('__pycache__'))

  # Knock out both encoded tables inside the copy; the repo's own data/ stays untouched.
  (sandbox / JIEQI_BIN).unlink()
  (sandbox / LUNARDATE_BIN).unlink()

  env: dict[str, str] = dict(os.environ)
  env['PYTHONPATH'] = os.pathsep.join((str(sandbox / 'tests/calendar'), str(sandbox)))
  result: subprocess.CompletedProcess[str] = subprocess.run(
    [sys.executable, '-m', 'hko_data.encoder'],
    cwd=sandbox,
    env=env,
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
