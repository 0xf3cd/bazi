# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_command_help.py

import re
from pathlib import Path
from typing import get_args

import pytest

from bazi.context_matching import ScopeName, TransitEntry, criteria
from bazi import cli

from cli_runner import BIRTH, COMMANDS, run_cli, run_guarded_script


@pytest.mark.parametrize('args', [('--help',), ('-h',)])
def test_top_level_help_lists_tasks(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, *args)
  assert result.returncode == 0 and '提示：' not in result.stderr
  for task in COMMANDS:
    assert re.search(rf'^\s+{task}\s+\S', result.stdout, flags=re.MULTILINE)
    assert f'bazi {task}' in result.stdout


@pytest.mark.parametrize('task', ['chart', 'match'])
def test_birth_help_explains_the_default_clock(task):
  parser = cli._subcommand_parsers(cli._command_parser())[task]
  action = next(action for action in parser._actions if '--birth-time' in action.option_strings)
  assert '东八区' in (action.help or '') and '不换算时区' in (action.help or '')


@pytest.mark.parametrize('task', COMMANDS)
def test_task_help_fits_one_screen(tmp_path: Path, task: str) -> None:
  result = run_cli(tmp_path, task, '--help', env={'COLUMNS': '80'})
  assert result.returncode == 0
  assert len(result.stdout.splitlines()) <= 45, result.stdout
  assert '更多选项' in result.stdout


def test_chart_command_shows_a_seeded_chart(tmp_path: Path) -> None:
  first, second = (run_cli(tmp_path, 'chart', '--seed', '42') for _ in range(2))
  assert first.returncode == 0 and first.stdout == second.stdout and first.stderr == ''
  assert first.stdout.startswith('random seed: 42\n')
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('flag, value, needs', [
  ('--precision', 'hour', '--birth-time'), ('--longitude', '120', '--birth-time'),
  ('--civil-timezone', '+08:00', '经度'),
])
def test_chart_help_names_what_these_options_need(tmp_path: Path, flag: str, value: str, needs: str) -> None:
  result = run_cli(tmp_path, 'chart', flag, value)
  assert result.returncode == 2 and 'require fixed birth input' in result.stderr
  action = next(a for a in cli._subcommand_parsers(cli._command_parser())['chart']._actions if flag in a.option_strings)
  assert needs in (action.help or '')


def test_chart_command_has_no_knowledge_options(tmp_path: Path) -> None:
  for flag in (('--object', 'tiangan.ding'), ('--observation-scope', 'natal')):
    result = run_cli(tmp_path, 'chart', *flag)
    assert result.returncode == 2 and 'unrecognized arguments' in result.stderr


def test_gz_month_help_names_the_year(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'match', 'editorial.spouse_star_tougan.v1', *BIRTH, '--gender', 'female',
                '--observation-scope', 'natal_and_transits', '--transit-entry', 'at_month', '--ganzhi-month', '午')
  assert result.returncode == 2 and 'ganzhi_year' in result.stderr
  action = next(a for a in cli._subcommand_parsers(cli._command_parser())['match']._actions if '--ganzhi-month' in a.option_strings)
  assert '--ganzhi-year' in (action.help or '')


def test_options_agree_with_library_directories() -> None:
  subparsers = cli._subcommand_parsers(cli._command_parser())
  assert tuple(subparsers) == COMMANDS
  dests = {name: {action.dest: action for action in sub._actions} for name, sub in subparsers.items()}
  assert tuple(dests['knowledge']['list_values'].choices or ()) == tuple(cli._LIST_DIMENSIONS)
  scopes = tuple(dests['match']['observation_scope'].choices or ())
  assert scopes == get_args(ScopeName) == ('natal', 'natal_and_liunian', 'natal_and_transits')
  assert set(scopes) == {scope for info in criteria().values() for scope in info.scopes}
  entries = tuple(dests['match']['transit_entry'].choices or ())
  assert entries == get_args(TransitEntry)
  assert set(entries) == {entry for info in criteria().values() for entry in info.transit_entries}
  assert not {'object_id', 'observation_scope'} & set(dests['chart'])
  assert not {'seed', 'object_id'} & set(dests['match'])


def test_bare_call_is_identical_to_help(tmp_path: Path) -> None:
  bare = run_cli(tmp_path)
  help_result = run_cli(tmp_path, '--help')
  assert bare.returncode == help_result.returncode == 0
  assert bare.stdout == help_result.stdout and bare.stderr == help_result.stderr == ''
  assert 'random seed:' not in bare.stdout and '出生时间：' not in bare.stdout
  assert list(tmp_path.iterdir()) == []
  guarded = run_guarded_script(tmp_path, ())
  assert guarded.returncode == 0 and guarded.stdout == bare.stdout and guarded.stderr == ''


def test_unknown_task_is_rejected(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'chrat')
  assert result.returncode == 2 and 'invalid choice' in result.stderr
  assert result.stdout == ''
  assert list(tmp_path.iterdir()) == []
