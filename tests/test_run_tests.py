# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import runpy
import sys
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
  (['-v', '-s', '-hko', '-c', '-cr', '100', '-ruff', '-mypy', '-d', '-i', '-osmoke'],
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
  for flag in ('run_slow_test', 'run_hko_test', 'do_cov', 'do_ruff', 'do_mypy', 'do_demo', 'do_interpreter', 'do_osmoke'):
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
