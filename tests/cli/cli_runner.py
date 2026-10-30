# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

# Shared subprocess runners, sample inputs and working-directory preparation.
# Imported as a bare sibling module: the suite has no `__init__.py`, so pytest puts this directory on
# `sys.path`, and `from tests.<package>...` would be shadowed by a stray installed `tests` package
# (see the NOTE in `tests/calendar/test_celestial_tables.py`).

import os
import shutil
import subprocess
import sys
from pathlib import Path

from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase


KNOWLEDGE_BASE = KnowledgeBase.load()

ROOT = Path(__file__).resolve().parents[2]
# Source-checkout tests only; package checks exercise the installed launcher.
SOURCE_MAIN = 'import sys; sys.path.insert(0, sys.argv.pop(1)); from bazi.cli import main; raise SystemExit(main())'
GUANSHA = 'editorial.guansha_coexistence.v1'
XINGCHONG = 'editorial.spouse_palace_xingchong.v1'
BIRTH = ('--birth-time', '2000-01-03 12:00')
MATCH_BIRTH = ('--birth-time', '2000-01-03 12:00', '--gender', 'female')
MATCH_ARGS = ('match', GUANSHA, *MATCH_BIRTH, '--observation-scope', 'natal')


def assert_cli_error(result: subprocess.CompletedProcess[str], task: str, error: str) -> None:
  # argparse reports unknown subcommand options through the top-level parser.
  usage = '[-h] <任务>' if error == 'unrecognized arguments' else task
  assert result.returncode == 2 and f'usage: bazi {usage}' in result.stderr
  assert error in result.stderr.split(': error:', 1)[1]
  assert 'v2.3.0' not in result.stderr and 'Traceback' not in result.stderr


def run_cli(
  cwd: Path,
  *args: str,
  checkout_root: Path | None = None,
  optimized: bool = False,
  env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, *(['-O'] if optimized else []), '-c', SOURCE_MAIN,
     str(ROOT if checkout_root is None else checkout_root), *args],
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


def run_guarded_script(
  cwd: Path,
  args: tuple[str, ...],
  *,
  checkout_root: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
  guard = '''
import os
import sys

sys.path.insert(0, sys.argv.pop(1))

def deny_writes(event, args):
  if event == 'open':
    _, mode, flags = args
    # PyPy FileIO reports closefd rather than OS flags when a mode is present.
    writable = (
      any(char in mode for char in 'wax+')
      if mode is not None
      else bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
    )
    if writable:
      raise PermissionError('Unexpected default file export')
  if event in ('os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.truncate'):
    raise PermissionError('Unexpected default filesystem change')

sys.addaudithook(deny_writes)
from bazi.cli import main
raise SystemExit(main())
'''
  return subprocess.run(
    [sys.executable, '-B', '-c', guard, str(checkout_root), *args],
    cwd=cwd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
  )
