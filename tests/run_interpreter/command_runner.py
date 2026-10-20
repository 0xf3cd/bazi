# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# command_runner.py

import os
import shutil
import subprocess
import sys
from pathlib import Path

from bazi.knowledge import DEFAULT_SOURCE_PATH


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'run_interpreter.py'
GUANSHA = 'editorial.guansha_coexistence.v1'
XINGCHONG = 'editorial.spouse_palace_xingchong.v1'
BIRTH = ('--birth-time', '2000-01-03 12:00')


def run(cwd: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, str(SCRIPT), *args],
    cwd=cwd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
    env=None if env is None else {**os.environ, **env},
  )


def prepare(cwd: Path) -> Path:
  cwd.mkdir(parents=True, exist_ok=True)
  shutil.copyfile(DEFAULT_SOURCE_PATH, cwd / 'src.json')
  return cwd
