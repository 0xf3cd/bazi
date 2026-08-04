# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_import_from_any_cwd.py

import pytest

import subprocess
import sys

from pathlib import Path


pytestmark = pytest.mark.integration


# The repo root is the level holding `src/`; this file lives at tests/integration/.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]


def test_pytest_runs_from_any_cwd(tmp_path: Path) -> None:
  '''Issue #90 item 2: the suite must not depend on being launched from the repo root.

  Tests import `from src...`, which used to resolve only via `sys.path[0]` — i.e. only
  when pytest was launched with the repo root as cwd/script dir; from any other cwd
  collection died with `ModuleNotFoundError: No module named 'src'`. The fix is
  `pythonpath = ..` in tests/pytest.ini (rootdir is tests/, so `..` is the repo root).
  This test is what keeps that one-liner falsifiable: delete it and this goes red.

  Runs a small stable test file in a subprocess with a tmp cwd — pytest startup plus
  collection takes seconds, so the timeout is generous.
  '''
  result: subprocess.CompletedProcess[str] = subprocess.run(
    [sys.executable, '-m', 'pytest', str(REPO_ROOT / 'tests' / 'test_common.py'), '-x', '-q'],
    cwd=tmp_path,
    capture_output=True,
    text=True,
    timeout=120,
    check=False,
  )
  output: str = result.stdout + result.stderr
  assert 'ModuleNotFoundError' not in output
  assert result.returncode == 0, f'pytest from a foreign cwd failed:\n{output}'
