# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from pathlib import Path

import pytest

from cli_runner import SCRIPT, run_cli, run_guarded_script


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('args', [
  ('--seed', '42'), ('--seed=42',), ('--count', '2'),
  ('--birth-time', '2000-01-01 12:00', '--gender', 'female'),
  ('--query-knowledge',), ('--validate-knowledge',), ('--object', 'tiangan.ding'),
  ('--match-context', 'editorial.guansha_coexistence.v1'),
  ('--export-knowledge-base',), ('--export-knowledge-json', 'out/k.json'),
  ('--seed', '1', '--help'), ('--seed', '1', '-h'), ('-h', 'chart'), ('--help', '--seed', '1'),
])
def test_flat_options_fail_with_migration_help(tmp_path: Path, optimized: bool, args: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, *args, optimized=optimized)
  assert result.returncode == 2 and result.stdout == ''
  assert 'usage: python run_interpreter.py [-h] <任务>' in result.stderr
  assert 'v2.3.0' in result.stderr and '移除' in result.stderr
  for command in ('chart', 'knowledge', 'match', '--help'):
    assert f'python run_interpreter.py {command}' in result.stderr
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('optimized', [False, True])
def test_bare_call_is_identical_to_help(tmp_path: Path, optimized: bool) -> None:
  bare = run_cli(tmp_path, optimized=optimized)
  help_result = run_cli(tmp_path, '--help', optimized=optimized)
  assert bare.returncode == help_result.returncode == 0
  assert bare.stdout == help_result.stdout and bare.stderr == help_result.stderr == ''
  assert 'random seed:' not in bare.stdout and '出生时间：' not in bare.stdout
  assert list(tmp_path.iterdir()) == []
  guarded = run_guarded_script(SCRIPT, tmp_path, ())
  assert guarded.returncode == 0 and guarded.stdout == bare.stdout and guarded.stderr == ''


def test_unknown_task_is_not_a_removed_call(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'chrat')
  assert result.returncode == 2 and 'invalid choice' in result.stderr
  assert 'v2.3.0' not in result.stderr and result.stdout == ''
  assert list(tmp_path.iterdir()) == []


def test_migration_help_survives_ascii_output(tmp_path: Path) -> None:
  result = run_cli(tmp_path, '--seed', '1', env={'PYTHONIOENCODING': 'ascii:backslashreplace'})
  assert result.returncode == 2 and 'v2.3.0' in result.stderr
  assert 'python run_interpreter.py chart' in result.stderr and 'Traceback' not in result.stderr
  assert result.stdout == '' and list(tmp_path.iterdir()) == []
