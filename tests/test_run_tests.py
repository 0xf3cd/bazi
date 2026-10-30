# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import runpy
import ast
import re
import sys
import os
import random
import shutil
import subprocess
from pathlib import Path, PurePosixPath, PureWindowsPath
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
  (['-v', '-s', '-hko', '-c', '-cr', '100', '-ruff', '-mypy', '-osmoke', '-docs', '-pkg'],
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
  for flag in ('run_slow_test', 'run_hko_test', 'do_cov', 'do_ruff', 'do_mypy', 'do_osmoke', 'do_docs', 'do_package'):
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
def test_coverage_enumerates_unimported_modules(tmp_path: Path, complete: bool) -> None:
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
def test_emojis_leave_regression_inputs(monkeypatch: pytest.MonkeyPatch, result: int) -> None:
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


@pytest.mark.parametrize('args, result', [(['-nt'], 0), (['-nt', '-docs'], 7), (['-nt', '--docs'], 7)])
def test_docs_registration(monkeypatch: pytest.MonkeyPatch, args: list[str], result: int) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', *args])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  main = runner['main']
  monkeypatch.setitem(main.__globals__, 'check_doc_environment', Mock())
  proc = Mock(return_value=7)
  monkeypatch.setitem(main.__globals__, 'run_proc_and_print', proc)
  with pytest.raises(SystemExit) as caught:
    main()
  assert caught.value.code == result
  if not result:
    proc.assert_not_called()
    return
  (command,), kwargs = proc.call_args
  assert command[:4] == [sys.executable, '-B', str(Path(__file__).parents[1] / 'run_docs.py'), '--output-dir']
  assert kwargs == {'print_details': True}
  assert not Path(command[4]).is_relative_to(Path(__file__).parents[1]) and not Path(command[4]).exists()


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


@pytest.mark.parametrize('flag', ['-pkg', '-a'])
def test_environment_report_forwarding(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, flag: str) -> None:
  values = [str(tmp_path / name) for name in ('pair', 'report.json', 'receipt.txt')]
  options = ['--package-output-dir', values[0], '--environment-report', values[1], '--outer-installer-report', values[2]]
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt', flag, *options])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  function = runner['run_package_checks']
  proc = Mock(return_value=0)
  monkeypatch.setitem(function.__globals__, 'run_proc_and_print', proc)
  assert function() == 0
  proc.assert_called_once_with([sys.executable, str(Path(__file__).parents[1] / 'run_package_checks.py'),
    '--output-dir', values[0], *options[2:]], print_details=True)


@pytest.mark.parametrize('options', [
  ['--environment-report', 'report'], ['--outer-installer-report', 'receipt'],
  ['--environment-report', 'report', '--outer-installer-report', 'receipt'],
])
def test_environment_report_requires_pair(monkeypatch: pytest.MonkeyPatch, options: list[str]) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt', '-pkg', *options])
  with pytest.raises(SystemExit) as caught:
    runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  assert caught.value.code == 2


def test_environment_export_requires_package(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt', '--package-output-dir', str(tmp_path / 'pair'),
    '--environment-report', str(tmp_path / 'report.json'), '--outer-installer-report', str(tmp_path / 'receipt.txt')])
  with pytest.raises(SystemExit) as caught:
    runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  assert caught.value.code == 2


@pytest.mark.parametrize('flag', ['--demo', '-i', '--interpreter'])
def test_removed_script_flags_are_rejected(monkeypatch: pytest.MonkeyPatch, flag: str) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', flag])
  with pytest.raises(SystemExit) as caught:
    runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  assert caught.value.code == 2


def test_full_runner_registers_current_tasks(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-a'])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  subtasks = runner['run_subtasks']
  coverage = Mock(return_value=0)
  for name in ('run_o_smoke', 'run_ruff', 'run_mypy', 'run_docs', 'run_package_checks'):
    monkeypatch.setitem(subtasks.__globals__, name, Mock(return_value=0))
  monkeypatch.setitem(subtasks.__globals__, 'run_coverage', coverage)
  statuses = subtasks()
  assert list(statuses) == ['coverage with tests', 'o_smoke', 'ruff', 'mypy', 'docs', 'package']
  coverage.assert_called_once_with(runner['run_tests'])
  assert not {'do_demo', 'do_interpreter', 'DEMO_SCRIPTS', 'run_demo', 'run_interpreter'} & runner.keys()
  assert not {'-d', '--demo', '-i', '--interpreter'} & runner['argparser']._option_string_actions.keys()


def test_pytest_args_keep_replay_details(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt'])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  run_tests = runner['run_tests']
  main = Mock(return_value=0)
  monkeypatch.setitem(run_tests.__globals__, 'pytest', SimpleNamespace(main=main))
  assert run_tests() == 0
  arguments = main.call_args.args[0]
  assert '-x' in arguments and '--showlocals' in arguments


@pytest.mark.parametrize('arguments, docs, tests', [
  (['-a', '--runtime-only'], False, True),
  (['-a', '-nt', '--runtime-only'], False, True),
  (['-nt', '--runtime-only'], False, False),
  (['-nt', '-docs'], True, False),
])
def test_runtime_scope_is_explicit(
  monkeypatch: pytest.MonkeyPatch, arguments: list[str], docs: bool, tests: bool,
) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', *arguments])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  assert runner['do_docs'] is docs
  assert runner['skip_test'] is not tests
  if '-a' in arguments:
    for flag in ('run_slow_test', 'run_hko_test', 'do_cov', 'do_ruff', 'do_mypy', 'do_osmoke', 'do_package'):
      assert runner[flag] is True, flag


@pytest.mark.parametrize('flag', ['-docs', '--docs'])
def test_runtime_scope_rejects_requested_docs(monkeypatch: pytest.MonkeyPatch, flag: str) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '--runtime-only', flag])
  with pytest.raises(SystemExit) as caught:
    runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  assert caught.value.code == 2


@pytest.mark.parametrize('runtime', [False, True])
def test_runtime_scope_is_reported(
  monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], runtime: bool,
) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt', *(['--runtime-only'] if runtime else [])])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  report = runner['print_args']
  report()
  output = re.sub(r'\x1b\[[0-9;]*m', '', capsys.readouterr().out)
  assert f'-- runtime_only:     {runtime}' in output


@pytest.mark.parametrize('version, missing', [
  ((3, 11), None), ((3, 12), None), ((3, 13), 'sphinx'), ((3, 14), 'myst_parser'),
  ((3, 13), 'docutils'), ((3, 13), 'markdown_it'),
])
def test_doc_preflight_precedes_all_tasks(
  monkeypatch: pytest.MonkeyPatch, version: tuple[int, int], missing: str | None,
) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-a'])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  main = runner['main']
  tasks = Mock()
  monkeypatch.setitem(main.__globals__, 'run_subtasks', tasks)
  monkeypatch.setitem(main.__globals__, 'find_spec', lambda name: None if name == missing else object())
  monkeypatch.setattr(sys, 'version_info', version)
  with pytest.raises(SystemExit) as caught:
    main()
  assert caught.value.code == 2
  tasks.assert_not_called()


@pytest.mark.parametrize('version', [(3, 13), (3, 14)])
def test_doc_preflight_accepts_complete_env(monkeypatch: pytest.MonkeyPatch, version: tuple[int, int]) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt'])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  check = runner['check_doc_environment']
  probe = Mock(return_value=object())
  monkeypatch.setitem(check.__globals__, 'find_spec', probe)
  monkeypatch.setattr(sys, 'version_info', version)
  check()
  assert [call.args[0] for call in probe.call_args_list] == list(runner['DOC_MODULES'])


@pytest.mark.parametrize('path, expected', [
  ('docs/_ext/extension.py', True), ('tests/docs/test_tool.py', True),
  ('run_docs.py', True), ('run_doc_checks.py', True),
  ('bazi/docs/feature.py', False), ('tests/docs_extra.py', False),
  ('tests/test_docs_site.py', False), ('tests/test_docs_workflows.py', False),
  ('run_docs_extra.py', False),
])
def test_doc_ownership_uses_path_components(
  monkeypatch: pytest.MonkeyPatch, path: str, expected: bool,
) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt'])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  for path_type in (PurePosixPath, PureWindowsPath):
    assert runner['is_doc_tool'](path_type(path)) is expected


def test_runtime_mypy_has_all_non_doc_targets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt'])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  names = (
    'run_package_checks.py', 'run_docs.py', 'run_doc_checks.py', 'run_docs_site.py',
    'tests/test_runtime.py', 'tests/nested/test_more.py', 'tests/docs/test_tool.py',
    'docs/_ext/tool.py', 'bazi/__init__.py',
  )
  for name in names:
    target = tmp_path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.touch()
  targets = runner['mypy_targets'](tmp_path, True)
  assert set(targets) == {
    tmp_path / name for name in ('bazi', 'run_package_checks.py', 'run_docs_site.py', 'tests/test_runtime.py', 'tests/nested/test_more.py')
  }
  assert runner['mypy_targets'](tmp_path, False) == (tmp_path,)


def test_runtime_pytest_uses_the_owned_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '--runtime-only'])
  runner = runpy.run_path(str(Path(__file__).parents[1] / 'run_tests.py'))
  run_tests = runner['run_tests']
  main = Mock(return_value=0)
  monkeypatch.setitem(run_tests.__globals__, 'pytest', SimpleNamespace(main=main))
  assert run_tests() == 0
  arguments = main.call_args.args[0]
  assert [arg for arg in arguments if arg.startswith('--ignore=')] == [
    f'--ignore={Path(__file__).parents[1] / "tests/docs"}',
  ]


def doc_dependents(root: Path, modules: tuple[str, ...]) -> set[Path]:
  files = set(root.glob('*.py'))
  for directory in ('bazi', 'tests', 'docs'):
    files.update((root / directory).rglob('*.py'))
  imports: dict[Path, set[str]] = {}
  aliases: dict[str, set[Path]] = {}
  for path in files:
    aliases.setdefault(path.stem, set()).add(path)
    aliases.setdefault('.'.join(path.relative_to(root).with_suffix('').parts), set()).add(path)
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
      if isinstance(node, ast.Import):
        names.update(alias.name for alias in node.names)
      elif isinstance(node, ast.ImportFrom) and node.module is not None and not node.level:
        names.add(node.module)
      elif (
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'importorskip'
        and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)
      ):
        names.add(node.args[0].value)
    imports[path] = names
  dependent = {path for path, names in imports.items() if any(name.split('.')[0] in modules for name in names)}
  while True:
    updated = dependent | {
      path for path, names in imports.items() if any(aliases.get(name, set()) & dependent for name in names)
    }
    if updated == dependent:
      return {path.relative_to(root) for path in dependent}
    dependent = updated


def test_doc_import_closure_stays_owned(monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(sys, 'argv', ['run_tests.py', '-nt'])
  root = Path(__file__).parents[1]
  runner = runpy.run_path(str(root / 'run_tests.py'))
  dependent = doc_dependents(root, runner['DOC_MODULES'])
  assert {Path('run_docs.py'), Path('run_doc_checks.py')} <= dependent
  assert all(runner['is_doc_tool'](path) for path in dependent), dependent
  targets = runner['mypy_targets'](root, True)
  checked: set[Path] = set()
  for target in targets:
    checked.update(target.rglob('*.py') if target.is_dir() else (target,))
  assert {root / 'tests/test_docs_site.py', root / 'tests/test_docs_workflows.py'} <= checked
  assert all(not runner['is_doc_tool'](path.relative_to(root)) for path in checked)


@pytest.mark.parametrize('statement', ['import sphinx', 'from run_doc_checks import check'])
def test_doc_import_closure_finds_new_scripts(tmp_path: Path, statement: str) -> None:
  (tmp_path / 'run_doc_checks.py').write_text('from sphinx import application\n', encoding='utf-8')
  (tmp_path / 'unexpected.py').write_text(statement + '\n', encoding='utf-8')
  assert doc_dependents(tmp_path, ('sphinx',)) == {Path('run_doc_checks.py'), Path('unexpected.py')}
