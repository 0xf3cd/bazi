# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import runpy
import sys
import os
import random
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.mark.parametrize('args, all_tasks, skip_test, expression, rate, verbose', [
  ([], False, False, None, 100.0, False),
  (['-a', '-v'], True, False, None, 100.0, True),
  (['-a', '-nt', '-k', 'ignored'], True, False, None, 100.0, False),
  (['-a', '-cr', '90'], True, False, None, 90.0, False),
  (['-nt', '-k', 'selected'], False, True, 'selected', 100.0, False),
  # Explicit flags enable every task without -a.
  (['-v', '-s', '-hko', '-c', '-cr', '100', '-ruff', '-mypy', '-d', '-i', '-osmoke', '-pkg'],
   True, False, None, 100.0, True),
])
def test_arguments(
  monkeypatch: pytest.MonkeyPatch,
  args: list[str],
  all_tasks: bool,
  skip_test: bool,
  expression: str | None,
  rate: float,
  verbose: bool,
) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', *args])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))

  assert runner['skip_test'] is skip_test
  assert runner['expression'] == expression
  assert runner['minimum_cov_rate'] == rate
  assert runner['verbose'] is verbose
  for flag in ('run_slow_test', 'run_hko_test', 'do_cov', 'do_ruff', 'do_mypy', 'do_demo', 'do_interpreter', 'do_osmoke', 'do_package'):
    assert runner[flag] is all_tasks, flag


@pytest.mark.parametrize('args, reported_rate, test_result, success', [
  ([], 99.9, 0, False),
  ([], 100.0, 0, True),
  (['-cr', '90'], 95.0, 0, True),
  ([], 100.0, 2, False),
])
def test_coverage_result(
  monkeypatch: pytest.MonkeyPatch,
  args: list[str],
  reported_rate: float,
  test_result: int,
  success: bool,
) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-c', *args])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))

  cov = Mock()
  cov.report.return_value = reported_rate
  run_coverage = runner['run_coverage']
  # run_path returns a copy; patch the function's globals, not the shared coverage module.
  monkeypatch.setitem(
    run_coverage.__globals__,
    'coverage',
    SimpleNamespace(Coverage=Mock(return_value=cov)),
  )

  assert (run_coverage(lambda: test_result) == 0) is success
  cov.report.assert_called_once()
  options = run_coverage.__globals__['coverage'].Coverage.call_args.kwargs
  package = Path(__file__).parents[1] / 'bazi'
  assert options['source'] == [str(package)]
  assert options['omit'] == [
    str(package / 'calendar/hko_data/encoder.py'),
    str(package / 'calendar/celestial_data/generator.py'),
  ]


@pytest.mark.parametrize('complete', [False, True])
def test_coverage_enumerates_unimported_runtime_modules(tmp_path: Path, complete: bool) -> None:
  shutil.copyfile(Path(__file__).parents[1] / 'run_tests.py', tmp_path / 'run_tests.py')
  package = tmp_path / 'bazi'
  for directory in (package, package / 'nested', package / 'calendar/hko_data', package / 'calendar/celestial_data'):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / '__init__.py').write_text('', encoding='utf-8')
  for relative in ('executed.py', 'unimported.py', 'nested/unimported_runtime.py',
                   'nested/__init__.py', 'calendar/hko_data/encoder.py', 'calendar/celestial_data/generator.py'):
    (package / relative).write_text('VALUE = 1\n', encoding='utf-8')
  script = '''
import importlib
import runpy
import sys

complete = sys.argv.pop() == 'True'
sys.argv = ['run_tests.py', '-c']
runner = runpy.run_path('run_tests.py')
def execute():
  importlib.import_module('bazi.executed')
  if complete:
    importlib.import_module('bazi.unimported')
    importlib.import_module('bazi.nested.unimported_runtime')
  return 0
sys.exit(runner['run_coverage'](execute))
'''
  # A child owns the nested collector and its files; never interrupt the outer collector.
  result = subprocess.run(
    [sys.executable, '-c', script, str(complete)],
    cwd=tmp_path,
    env={key: value for key, value in os.environ.items() if not key.startswith('COVERAGE_')},
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=30,
    check=False,
  )
  print(result.stdout, result.stderr, f'CHILD EXIT: {result.returncode}')
  assert result.returncode == (0 if complete else 0x42), result.stdout + result.stderr
  for module in ('executed.py', 'unimported.py', 'unimported_runtime.py', '__init__.py'):
    assert module in result.stdout
  for omitted in ('encoder.py', 'generator.py', 'run_tests.py'):
    assert omitted not in result.stdout
  assert ('100%' in result.stdout.split('TOTAL')[1]) is complete


@pytest.mark.parametrize('result', [0, 7])
def test_runner_emojis_leave_regression_inputs_unchanged(monkeypatch: pytest.MonkeyPatch, result: int) -> None:
  state = random.getstate()
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt'])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  pairs = runner['emoji_pair_generator']()
  for _ in range(100):
    runner['random_emoji']()
    next(pairs)
    runner['devider']()
  statuses = runner['SubTaskStatuses']()
  statuses.set('test', result, 0.0)
  monkeypatch.setitem(runner['main'].__globals__, 'run_subtasks', lambda: statuses)
  with pytest.raises(SystemExit) as caught:
    runner['main']()
  assert caught.value.code == result
  assert random.getstate() == state


@pytest.mark.parametrize('args, result', [(['-nt'], 0), (['-nt', '-pkg'], 7), (['-nt', '--package'], 7)])
def test_package_registration(monkeypatch: pytest.MonkeyPatch, args: list[str], result: int) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', *args])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  main = runner['main']
  proc = Mock(return_value=7)
  monkeypatch.setitem(main.__globals__, 'run_proc_and_print', proc)
  with pytest.raises(SystemExit) as caught:
    main()
  assert caught.value.code == result
  if result:
    proc.assert_called_once_with([
      sys.executable, str(Path(__file__).parents[1] / 'run_package_checks.py'),
    ], print_details=True)
  else:
    proc.assert_not_called()


def test_package_output_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
  output = tmp_path / 'tested pair'
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt', '-pkg', '--package-output-dir', str(output)])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  run_package_checks = runner['run_package_checks']
  proc = Mock(return_value=0)
  monkeypatch.setitem(run_package_checks.__globals__, 'run_proc_and_print', proc)
  assert run_package_checks() == 0
  proc.assert_called_once_with([
    sys.executable, str(Path(__file__).parents[1] / 'run_package_checks.py'),
    '--output-dir', str(output),
  ], print_details=True)


def test_demo_and_interpreter_gate_pass_fixed_seeds(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt'])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  proc = Mock(return_value=0)
  monkeypatch.setitem(runner['run_demo'].__globals__, 'run_proc_and_print', proc)
  assert runner['run_demo']() == runner['run_interpreter']() == 0
  assert [call.args[0] for call in proc.call_args_list] == [
    [sys.executable, str(Path(__file__).parents[1] / script), '--seed', '236']
    for script in ('run_demo.py', 'run_relationship_analyzer.py', 'run_interpreter.py')
  ]


def test_pytest_arguments_keep_failure_replay_details(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt'])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  run_tests = runner['run_tests']
  main = Mock(return_value=0)
  monkeypatch.setitem(run_tests.__globals__, 'pytest', SimpleNamespace(main=main))
  assert run_tests() == 0
  arguments = main.call_args.args[0]
  assert '-x' in arguments and '--showlocals' in arguments
