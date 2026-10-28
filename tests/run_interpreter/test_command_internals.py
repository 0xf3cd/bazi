# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_command_internals.py

from datetime import timedelta
from pathlib import Path
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

import pytest

import run_interpreter
import cli_runner
from run_interpreter import main

from cli_runner import GUANSHA, XINGCHONG, BIRTH, prepare


# ---- 进程内：同一批分支再走一遍，便于对脚本做覆盖测量（根脚本不在库覆盖闸门内）。

def _call(monkeypatch: pytest.MonkeyPatch, cwd: Path, *args: str) -> int | str | None:
  monkeypatch.chdir(cwd)
  try:
    return main(list(args))
  except SystemExit as stop:
    return stop.code


def test_inprocess_commands_cover_every_branch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
  prepare(tmp_path)
  cases: list[tuple[tuple[str, ...], int | None]] = [
    (('-h',), 0), (('chart', '--seed', '1'), 0), (('chart', '--seed', '1', '--output-dir', 'o1'), 0),
    (('knowledge',), 0), (('knowledge', '--list-values', 'topic'), 0), (('knowledge', '--all'), 0),
    (('knowledge', '--object', 'tiangan.ding'), 0),
    (('knowledge', '--validate-knowledge'), 0),
    (('knowledge', '--export-knowledge-base', '--output-dir', 'o3'), 0),
    (('knowledge', '--output-dir', 'o4'), 2), (('knowledge', '--show-sources'), 2),
    (('knowledge', '--export-knowledge-base', '--show-sources', '--output-dir', 'o6'), 0),
    (('match', '--knowledge-source', 'src.json'), 2), (('knowledge', '--seed', '1'), 2),
    (('knowledge', '--knowledge-source', 'missing.json', '--export-knowledge-base', '--output-dir', 'o8'), 2),
    (('knowledge', '--list-values', 'topic', '--all'), 2), (('knowledge', '--all', '--object', 'tiangan.ding'), 2),
    (('knowledge', '--knowledge-source', 'o10/knowledge_base/tiangan/甲.txt', '--export-knowledge-base', '--output-dir', 'o10'), 2),
    (('knowledge', '--knowledge-source', 'missing.json'), 2),
    (('knowledge', '--list-values', 'topic', '--knowledge-source', 'missing.json'), 2),
    (('match',), 0), (('match', GUANSHA), 0), (('match', XINGCHONG), 0), (('match', 'nope'), 2),
    (('match', GUANSHA, '--gender', 'female'), 2), (('match', '--gender', 'female'), 2),
    (('match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal'), 0),
    (('match', 'editorial.guansha_coexistence_female.v1'), 0),
    (('knowledge', '--export-knowledge-base', '--output-dir', 'src.json'), 2),
    (('chart', '--seed', '1'), 0), (('knowledge', '--topic', '定义'), 0), (('knowledge', '--object', 'tiangan.ding'), 0),
    (('chart', '--seed', '1', '--output-dir', 'o5'), 0),
    (('knowledge', '--export-knowledge-base', '--output-dir', 'o5'), 0),
    (('match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal'), 0),
    (('chart', '--birth-time', '2000-01-01T12:00:00+08:00', '--gender', 'male', '--precision', 'minute', '--longitude', '120', '--civil-timezone=+08:00'), 0),
    ((), 0),
  ]
  for args, code in cases:
    assert _call(monkeypatch, tmp_path, *args) in ((0, None) if code == 0 else (code,)), args
  assert (tmp_path / 'o3' / 'knowledge_base').is_dir() and (tmp_path / 'o1' / 'interpretation_examples').is_dir()
  assert '提示：' not in capsys.readouterr().err


@pytest.mark.parametrize('zone,seconds', [('Asia/Shanghai', None), ('+05:30', 19800), ('-05:00', -18000), ('+05:30:15', 19815)])
def test_civil_timezone_parses_both_forms(zone: str, seconds: int | None) -> None:
  parsed = run_interpreter._civil_timezone(zone)
  if seconds is None:
    assert isinstance(parsed, ZoneInfo) and parsed.key == zone
  else:
    assert parsed.utcoffset(None) == timedelta(seconds=seconds)


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('custom_script', [False, True])
@pytest.mark.parametrize('custom_env', [False, True])
def test_runner_preserves_subprocess_options(
  monkeypatch: pytest.MonkeyPatch, tmp_path: Path, optimized: bool, custom_script: bool, custom_env: bool,
) -> None:
  calls: list[tuple[list[str], dict[str, object]]] = []
  expected = subprocess.CompletedProcess(['script'], 0, 'output', '')
  def capture(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    calls.append((command, kwargs))
    return expected
  monkeypatch.setattr(subprocess, 'run', capture)
  monkeypatch.setenv('BAZI_RUNNER_TEST', 'inherited')
  script = tmp_path / 'custom.py' if custom_script else None
  env = {'BAZI_RUNNER_TEST': 'override'} if custom_env else None
  assert cli_runner.run_cli(tmp_path, 'chart', '--seed', '42', script=script, optimized=optimized, env=env) is expected
  assert calls == [(
    [sys.executable, *(['-O'] if optimized else []), str(cli_runner.SCRIPT if script is None else script), 'chart', '--seed', '42'],
    {'cwd': tmp_path, 'capture_output': True, 'text': True, 'encoding': 'utf-8', 'timeout': 45, 'check': False,
     'env': None if env is None else {**os.environ, **env}},
  )]


def test_error_helper_rejects_usage_only_match() -> None:
  result = subprocess.CompletedProcess(
    ['script'], 2, '',
    'usage: python run_interpreter.py chart --longitude\npython run_interpreter.py chart: error: wrong reason\n',
  )
  with pytest.raises(AssertionError):
    cli_runner.assert_cli_error(result, 'chart', '--longitude')
