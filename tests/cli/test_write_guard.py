# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
from pathlib import Path

import pytest

from bazi import cli

from cli_runner import run_cli, run_guarded_script, MATCH_ARGS


@pytest.mark.parametrize('args', [
  ('chart',), ('chart', '--seed', '42'), ('chart', '--seed', '42', '--knowledge'),
  ('knowledge', '丁'), MATCH_ARGS, (*MATCH_ARGS, '--knowledge'),
])
def test_default_tasks_are_read_only(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = run_guarded_script(tmp_path, args)
  assert result.returncode == 0, result.stderr
  assert list(tmp_path.iterdir()) == []


def test_explicit_output_hits_write_guard(tmp_path: Path) -> None:
  result = run_guarded_script(tmp_path, ('chart', '--output', 'chart.txt'))
  assert result.returncode == 2 and 'Unexpected default file export' in result.stderr
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('mode', ['w', 'a', 'x', 'r+'])
def test_write_guard_checks_high_level_modes(mode: str, tmp_path: Path) -> None:
  target = tmp_path / 'target.txt'
  target.write_text('existing data', encoding='utf-8')
  checkout = tmp_path / 'checkout'
  package = checkout / 'bazi'
  package.mkdir(parents=True)
  (package / '__init__.py').write_text('', encoding='utf-8')
  (package / 'cli.py').write_text(f"def main():\n  open('target.txt', {mode!r}, encoding='utf-8')\n", encoding='utf-8')
  result = run_guarded_script(tmp_path, (), checkout_root=checkout)
  assert result.returncode != 0 and 'Unexpected default file export' in result.stderr
  assert target.read_text(encoding='utf-8') == 'existing data'


def test_output_only_replaces_named_file(tmp_path: Path) -> None:
  notes = tmp_path / 'notes.txt'
  notes.write_text('personal notes', encoding='utf-8')
  target = tmp_path / 'chart.txt'
  target.write_text('old output', encoding='utf-8')
  result = run_cli(tmp_path, 'chart', '--seed', '42', '--output', str(target))
  assert result.returncode == 0
  assert target.read_text(encoding='utf-8') == re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
  assert notes.read_text(encoding='utf-8') == 'personal notes'
  assert set(tmp_path.iterdir()) == {notes, target}


def test_bad_output_path_uses_cli_error_exit(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'chart', '--output', str(tmp_path))
  assert result.returncode == 2 and not result.stdout and 'error:' in result.stderr
  assert 'Traceback' not in result.stderr


def test_output_io_failure_uses_error_exit(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
  def fail(*args: object, **kwargs: object) -> None:
    raise OSError('Output I/O failure')
  monkeypatch.setattr(Path, 'write_text', fail)
  with pytest.raises(SystemExit) as caught:
    cli.main(['chart', '--output', 'chart.txt'])
  assert caught.value.code == 2 and 'error: Output I/O failure' in capsys.readouterr().err


def test_print_errors_propagate(monkeypatch: pytest.MonkeyPatch) -> None:
  error = BrokenPipeError('Print failure')
  def fail(*args: object, **kwargs: object) -> None:
    raise error
  monkeypatch.setitem(cli.main.__globals__, 'print', fail)
  with pytest.raises(BrokenPipeError) as caught:
    cli.main(['chart', '--birth-time', '2000-01-01 12:00', '--gender', 'male'])
  assert caught.value is error


@pytest.mark.parametrize('error_type', [TypeError, ValueError, RuntimeError])
def test_internal_render_errors_propagate(monkeypatch: pytest.MonkeyPatch, error_type: type[Exception]) -> None:
  error = error_type('Internal rendering failure')
  def fail(*args: object, **kwargs: object) -> str:
    raise error
  monkeypatch.setattr(cli, '_get_basic_info', fail)
  with pytest.raises(error_type) as caught:
    cli.main(['chart', '--seed', '42'])
  assert caught.value is error
