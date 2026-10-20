# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_flat_hints.py

import shlex
from pathlib import Path, PureWindowsPath

import pytest

import run_interpreter

from command_runner import GUANSHA, XINGCHONG, BIRTH, run, prepare


def _outputs(cwd: Path) -> dict[str, bytes]:
  out = cwd / 'out'
  return {path.relative_to(cwd).as_posix(): path.read_bytes() for path in sorted(out.rglob('*')) if path.is_file()} if out.exists() else {}


def _hint_commands(stderr: str) -> list[list[str]]:
  lines = [line for line in stderr.splitlines() if line.startswith('提示：')]
  assert len(lines) == 1, stderr
  commands = lines[0].split('请改用：', 1)[1].split(' && ')
  parsed = [shlex.split(command) for command in commands]
  assert all(tokens[:2] == ['python', 'run_interpreter.py'] for tokens in parsed)
  return [tokens[2:] for tokens in parsed]


# 旧平铺调用 -> 提示给出的等价新命令（去掉 python run_interpreter.py 前缀）。
LEGACY_CASES = [
  (('--seed', '42'), [['chart', '--seed', '42']]),
  (('--seed', '3', '--count', '2'), [['chart', '--seed', '3', '--count', '2']]),
  (
    ('--birth-time', '2000-01-01 12:00', '--gender', 'female', '--precision', 'hour', '--include-reference-only', '--show-sources'),
    [['chart', '--birth-time', '2000-01-01 12:00', '--gender', 'female', '--precision', 'hour', '--include-reference-only', '--show-sources']],
  ),
  (
    ('--birth-time', '2000-01-01 12:00', '--gender', 'male', '--export-chart-json', 'out/c.json'),
    [['chart', '--birth-time', '2000-01-01 12:00', '--gender', 'male', '--export-chart-json', 'out/c.json']],
  ),
  (('--seed', '5', '--output-dir', 'out'), [['chart', '--seed', '5', '--output-dir', 'out']]),
  (
    ('--seed', '5', '--output-dir', 'out', '--export-knowledge-base'),
    [['chart', '--seed', '5', '--output-dir', 'out'], ['knowledge', '--export-knowledge-base', '--output-dir', 'out']],
  ),
  (
    ('--seed', '5', '--output-dir', 'out', '--export-knowledge-base', '--show-sources', '--include-reference-only'),
    [
      ['chart', '--seed', '5', '--include-reference-only', '--show-sources', '--output-dir', 'out'],
      ['knowledge', '--export-knowledge-base', '--output-dir', 'out', '--include-reference-only', '--show-sources'],
    ],
  ),
  (
    ('--birth-time', '2000-01-01T12:00:00+08:00', '--gender', 'male', '--precision', 'minute', '--longitude', '120', '--civil-timezone=+08:00'),
    [['chart', '--birth-time', '2000-01-01T12:00:00+08:00', '--gender', 'male', '--precision', 'minute', '--longitude', '120.0', '--civil-timezone=+08:00']],
  ),
  (
    ('--birth-time', '2000-01-01T12:00:00-05:00', '--gender', 'female', '--precision', 'hour', '--longitude', '-75', '--civil-timezone', 'America/New_York'),
    [['chart', '--birth-time', '2000-01-01T12:00:00-05:00', '--gender', 'female', '--precision', 'hour', '--longitude', '-75.0', '--civil-timezone=America/New_York']],
  ),
  (
    ('--query-knowledge', '--object', 'tiangan.ding', '--include-reference-only'),
    [['knowledge', '--object', 'tiangan.ding', '--include-reference-only']],
  ),
  (('--query-knowledge',), [['knowledge', '--all']]),
  (('--validate-knowledge',), [['knowledge', '--validate-knowledge']]),
  (
    ('--query-knowledge', '--topic', '定义', '--applicability', 'unconditional', '--export-knowledge-json', 'out/k.json'),
    [['knowledge', '--topic', '定义', '--applicability', 'unconditional', '--export-knowledge-json', 'out/k.json']],
  ),
  (('--export-knowledge-json', 'out/all.json'), [['knowledge', '--export-knowledge-json', 'out/all.json']]),
  (
    ('--query-knowledge', '--object', 'tiangan.ding', '--knowledge-source', 'src.json'),
    [['knowledge', '--object', 'tiangan.ding', '--knowledge-source', 'src.json']],
  ),
  (
    ('--match-context', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal', '--export-context-json', 'out/m.json'),
    [['match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal', '--export-context-json', 'out/m.json']],
  ),
  (
    ('--match-context', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal_and_liunian', '--ganzhi-year', '2024', '--include-reference-only'),
    [['match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal_and_liunian', '--ganzhi-year', '2024', '--include-reference-only']],
  ),
  (
    ('--match-context', XINGCHONG, *BIRTH, '--gender', 'female', '--observation-scope', 'natal_and_transits', '--transit-entry', 'at_month', '--ganzhi-year', '2024', '--gz-month', '午', '--transit-kinds', 'liuyue,liunian'),
    [['match', XINGCHONG, *BIRTH, '--gender', 'female', '--observation-scope', 'natal_and_transits', '--ganzhi-year', '2024', '--transit-entry', 'at_month', '--gz-month', '午', '--transit-kinds', 'liuyue,liunian']],
  ),
  (
    ('--match-context', XINGCHONG, *BIRTH, '--gender', 'male', '--observation-scope', 'natal_and_transits', '--transit-entry', 'at_date', '--solar-date', '2024-04-10', '--transit-kinds', 'liuri'),
    [['match', XINGCHONG, *BIRTH, '--gender', 'male', '--observation-scope', 'natal_and_transits', '--transit-entry', 'at_date', '--solar-date', '2024-04-10', '--transit-kinds', 'liuri']],
  ),
]


@pytest.mark.parametrize('legacy, expected', LEGACY_CASES)
def test_legacy_call_hints_its_new_command(tmp_path: Path, legacy: tuple[str, ...], expected: list[list[str]]) -> None:
  result = run(prepare(tmp_path), *legacy)
  assert result.returncode == 0, result.stderr
  assert _hint_commands(result.stderr) == expected


@pytest.mark.parametrize('legacy, expected', LEGACY_CASES)
def test_hint_command_reproduces_the_legacy_run(tmp_path: Path, legacy: tuple[str, ...], expected: list[list[str]]) -> None:
  old = run(prepare(tmp_path / 'old'), *legacy)
  new_cwd = prepare(tmp_path / 'new')
  runs = [run(new_cwd, *tokens) for tokens in _hint_commands(old.stderr)]
  assert all(run.returncode == 0 and '提示：' not in run.stderr for run in runs), [run.stderr for run in runs]
  assert ''.join(run.stdout for run in runs) == old.stdout
  assert _outputs(new_cwd) == _outputs(tmp_path / 'old')
  if len(expected) == 2:
    assert (new_cwd / 'out' / 'knowledge_base' / 'tiangan').is_dir()


def test_legacy_failures_print_no_hint(tmp_path: Path) -> None:
  for args in (('--object', 'tiangan.ding'), ('--match-context', 'nope', *BIRTH), ('--count', '0')):
    result = run(tmp_path, *args)
    assert result.returncode == 2 and '提示：' not in result.stderr


def test_legacy_hint_stays_readable_without_utf8(tmp_path: Path) -> None:
  result = run(tmp_path, '--seed', '1', env={'PYTHONIOENCODING': 'ascii:backslashreplace'})
  assert result.returncode == 0
  assert 'python run_interpreter.py chart --seed 1' in result.stderr


def test_bare_call_still_draws_a_random_chart(tmp_path: Path) -> None:
  result = run(tmp_path)
  assert result.returncode == 0 and result.stdout.startswith('random seed: ')
  assert _hint_commands(result.stderr) == [['chart']]


def test_hint_writes_paths_with_forward_slashes() -> None:
  assert run_interpreter._option('--export-chart-json', PureWindowsPath('out\\c.json')) == ['--export-chart-json', 'out/c.json']
  assert run_interpreter._option('--output-dir', PureWindowsPath('C:\\work\\out')) == ['--output-dir', 'C:/work/out']
  assert run_interpreter._option('--output-dir', Path('out')) == ['--output-dir', 'out']


@pytest.mark.parametrize('extra', [('--validate-knowledge',), ('--export-knowledge-json', 'out/k.json')])
def test_legacy_filters_still_need_query_flag(tmp_path: Path, extra: tuple[str, ...]) -> None:
  result = run(tmp_path, *extra, '--object', 'tiangan.ding')
  assert result.returncode == 2 and 'Knowledge filters require --query-knowledge' in result.stderr
  assert result.stdout == '' and '提示：' not in result.stderr and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('chart_flag', [('--seed', '1'), ('--output-dir', 'out'), ('--export-knowledge-base',)])
def test_legacy_knowledge_rejects_chart_flags(tmp_path: Path, chart_flag: tuple[str, ...]) -> None:
  result = run(tmp_path, '--query-knowledge', *chart_flag)
  assert result.returncode == 2 and 'Knowledge mode cannot be combined with chart input' in result.stderr
  assert '提示：' not in result.stderr and list(tmp_path.iterdir()) == []
