# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_command_internals.py

from pathlib import Path

import pytest

import run_interpreter
from run_interpreter import main

from command_runner import GUANSHA, XINGCHONG, BIRTH, prepare


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
    (('knowledge', '--object', 'tiangan.ding', '--export-knowledge-json', 'o2/k.json'), 0),
    (('knowledge', '--validate-knowledge'), 0),
    (('knowledge', '--export-knowledge-base', '--output-dir', 'o3'), 0),
    (('knowledge', '--output-dir', 'o4'), 2), (('knowledge', '--show-sources'), 2),
    (('knowledge', '--export-knowledge-base', '--show-sources', '--output-dir', 'o6'), 0),
    (('match', '--export-context-json', 'o7/m.json'), 2), (('--query-knowledge', '--seed', '1'), 2),
    (('knowledge', '--knowledge-source', 'missing.json', '--export-knowledge-base', '--output-dir', 'o8'), 2),
    (('knowledge', '--export-knowledge-json', 'o9/knowledge_base/tiangan/甲.txt', '--export-knowledge-base', '--output-dir', 'o9'), 2),
    (('knowledge', '--list-values', 'topic', '--all'), 2), (('knowledge', '--all', '--object', 'tiangan.ding'), 2),
    (('knowledge', '--knowledge-source', 'o10/knowledge_base/tiangan/甲.txt', '--export-knowledge-base', '--output-dir', 'o10'), 2),
    (('knowledge', '--knowledge-source', 'missing.json'), 2),
    (('knowledge', '--list-values', 'topic', '--knowledge-source', 'missing.json'), 2),
    (('match',), 0), (('match', GUANSHA), 0), (('match', XINGCHONG), 0), (('match', 'nope'), 2),
    (('match', GUANSHA, '--gender', 'female'), 2), (('match', '--gender', 'female'), 2),
    (('match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal'), 0),
    (('match', 'editorial.guansha_coexistence_female.v1'), 0),
    (('knowledge', '--export-knowledge-base', '--output-dir', 'src.json'), 2),
    (('--seed', '1'), 0), (('--query-knowledge', '--topic', '定义'), 0), (('--object', 'tiangan.ding'), 2),
    (('--seed', '1', '--output-dir', 'o5', '--export-knowledge-base'), 0),
    (('--match-context', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal'), 0),
    (('--birth-time', '2000-01-01T12:00:00+08:00', '--gender', 'male', '--precision', 'minute', '--longitude', '120', '--civil-timezone=+08:00'), 0),
  ]
  for args, code in cases:
    assert _call(monkeypatch, tmp_path, *args) in ((0, None) if code == 0 else (code,)), args
  assert (tmp_path / 'o3' / 'knowledge_base').is_dir() and (tmp_path / 'o1' / 'interpretation_examples').is_dir()
  assert '提示：' in capsys.readouterr().err


@pytest.mark.parametrize('zone, text', [('Asia/Shanghai', 'Asia/Shanghai'), ('+05:30', '+05:30'), ('-05:00', '-05:00'), ('+05:30:15', '+05:30:15')])
def test_zone_text_round_trips_both_forms(zone: str, text: str) -> None:
  assert run_interpreter._zone_text(run_interpreter._civil_timezone(zone)) == text


def test_option_renders_every_value_kind() -> None:
  from datetime import date, datetime
  assert run_interpreter._option('--x', None) == [] and run_interpreter._option('--x', False) == []
  assert run_interpreter._option('--x', True) == ['--x']
  assert run_interpreter._option('--x', date(2024, 4, 10)) == ['--x', '2024-04-10']
  assert run_interpreter._option('--x', datetime(2024, 4, 10, 12)) == ['--x', '2024-04-10T12:00:00']
  assert run_interpreter._option('--x', 120.0) == ['--x', '120.0']
