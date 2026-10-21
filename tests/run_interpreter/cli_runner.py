# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

# Shared by the core run_interpreter tests in this directory: the subprocess runner,
# the write-guard script runner, the fixed arguments and the preloaded knowledge base.
# Imported as a bare sibling module: the suite has no `__init__.py`, so pytest puts this directory on
# `sys.path`, and `from tests.<package>...` would be shadowed by a stray installed `tests` package
# (see the NOTE in `tests/calendar/test_celestial_tables.py`).

import subprocess
import sys
from pathlib import Path

from bazi.knowledge import KnowledgeBase


KNOWLEDGE_BASE = KnowledgeBase.load()

MATCH_BIRTH = ('--birth-time', '2000-01-03 12:00', '--gender', 'female')
MATCH_ARGS = ('match', 'editorial.guansha_coexistence.v1', *MATCH_BIRTH, '--observation-scope', 'natal')


def assert_cli_error(result: subprocess.CompletedProcess[str], task: str, error: str) -> None:
  # argparse reports unknown subcommand options through the top-level parser.
  usage = '[-h] <任务>' if error == 'unrecognized arguments' else task
  assert result.returncode == 2 and f'usage: python run_interpreter.py {usage}' in result.stderr
  assert error in result.stderr.split(': error:', 1)[1]
  assert 'v2.3.0' not in result.stderr and 'Traceback' not in result.stderr


def run_cli(cwd: Path, *args: str, script: Path | None = None, optimized: bool = False) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, *(['-O'] if optimized else []), str(Path(__file__).parents[2] / 'run_interpreter.py' if script is None else script), *args],
    cwd=cwd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
  )


def run_guarded_script(
  script: Path,
  cwd: Path,
  args: tuple[str, ...],
) -> subprocess.CompletedProcess[str]:
  guard = '''
import os
import runpy
import sys
from pathlib import Path

script = sys.argv[1]
sys.path.insert(0, str(Path(script).parent))
sys.argv = sys.argv[1:]

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
runpy.run_path(script, run_name='__main__')
'''
  return subprocess.run(
    [sys.executable, '-B', '-c', guard, str(script), *args],
    cwd=cwd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
  )
