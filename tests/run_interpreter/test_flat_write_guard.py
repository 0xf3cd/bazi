# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
from pathlib import Path

import pytest

from run_interpreter import main

from flat_runner import run_cli, run_guarded_script


@pytest.mark.parametrize(('args', 'writes'), [
  ((), False),
  (('--seed', '42'), False),
  (('--output-dir', 'exported'), True),
  (('--export-knowledge-base',), True),
])
def test_default_cli_rejects_filesystem_writes(
  tmp_path: Path,
  args: tuple[str, ...],
  writes: bool,
) -> None:
  result = run_guarded_script(
    Path(__file__).parents[2] / 'run_interpreter.py',
    tmp_path,
    args,
  )
  if writes:
    assert result.returncode == 2
    assert 'Unexpected default' in result.stderr
    assert not any(path.is_file() for path in tmp_path.rglob('*'))
  else:
    assert result.returncode == 0, result.stderr
    assert result.stdout.count('出生时间：') == 1
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('mode', ['w', 'a', 'x', 'r+'])
def test_write_guard_checks_high_level_modes(
  mode: str,
  tmp_path: Path,
) -> None:
  target = tmp_path / 'target.txt'
  target.write_text('existing data', encoding='utf-8')
  script = tmp_path / 'probe.py'
  script.write_text(
    f"open('target.txt', {mode!r}, encoding='utf-8')\n",
    encoding='utf-8',
  )
  result = run_guarded_script(script, tmp_path, ())
  assert result.returncode != 0
  assert 'Unexpected default file export' in result.stderr
  assert target.read_text(encoding='utf-8') == 'existing data'


def test_exports_retain_other_existing_files(tmp_path: Path) -> None:
  first = run_cli(tmp_path, '--seed', '42', '--count', '2', '--output-dir', str(tmp_path))
  assert first.returncode == 0
  output = tmp_path / 'interpretation_examples'
  earlier = (output / '1.txt').read_bytes()
  (output / '0.txt').write_text('sentinel', encoding='utf-8')
  (output / 'notes.txt').write_text('personal notes', encoding='utf-8')
  second = run_cli(tmp_path, '--seed', '42', '--output-dir', str(tmp_path))
  assert second.returncode == 0
  assert (output / '0.txt').read_text(encoding='utf-8') == re.sub(
    r'\x1b\[[0-9;]*m', '', second.stdout.removeprefix('random seed: 42\n'),
  ).removesuffix('\n')
  assert (output / '1.txt').read_bytes() == earlier
  assert (output / 'notes.txt').read_text(encoding='utf-8') == 'personal notes'


def test_bad_export_path_uses_cli_error_exit(tmp_path: Path) -> None:
  output = tmp_path / 'file'
  output.write_text('existing data', encoding='utf-8')
  result = run_cli(tmp_path, '--seed', '42', '--output-dir', str(output))
  assert result.returncode == 2
  assert not result.stdout
  assert 'error:' in result.stderr
  assert 'Traceback' not in result.stderr
  assert output.read_text(encoding='utf-8') == 'existing data'


@pytest.mark.parametrize('error_type', [TypeError, ValueError, OSError])
def test_internal_rendering_errors_propagate(
  error_type: type[Exception],
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  error = error_type('Internal rendering failure')

  def broken_render(*args: object, **kwargs: object) -> str:
    raise error

  monkeypatch.setitem(main.__globals__, '_chart_text', broken_render)
  with pytest.raises(error_type, match='Internal rendering failure') as caught:
    main(['--birth-time', '2000-01-01 12:00', '--gender', 'male'])
  assert caught.value is error


@pytest.mark.parametrize('stage', ['directory', 'chart', 'knowledge'])
def test_export_io_failures_use_error_exit(
  stage: str,
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  def fail(*args: object, **kwargs: object) -> None:
    raise OSError('Export I/O failure')

  if stage == 'directory':
    monkeypatch.setattr(Path, 'mkdir', fail)
  elif stage == 'chart':
    monkeypatch.setitem(main.__globals__, '_write_chart', fail)
  else:
    monkeypatch.setitem(main.__globals__, 'save_knowledge_base', fail)

  with pytest.raises(SystemExit) as caught:
    main([
      '--birth-time', '2000-01-01 12:00', '--gender', 'male',
      '--output-dir', str(tmp_path), '--export-knowledge-base',
    ])
  assert caught.value.code == 2
  assert 'error: Export I/O failure' in capsys.readouterr().err


def test_print_errors_propagate(monkeypatch: pytest.MonkeyPatch) -> None:
  error = BrokenPipeError('Print failure')

  def fail(*args: object, **kwargs: object) -> None:
    raise error

  monkeypatch.setitem(main.__globals__, 'print', fail)
  with pytest.raises(BrokenPipeError) as caught:
    main(['--birth-time', '2000-01-01 12:00', '--gender', 'male'])
  assert caught.value is error
