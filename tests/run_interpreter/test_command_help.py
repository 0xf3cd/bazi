# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_command_help.py

import re
from pathlib import Path
from typing import get_args

import pytest

from bazi.context_matching import ObservationScope, TransitEntry, criteria
from bazi.knowledge import Applicability
from run_interpreter import _COMMANDS, _LIST_DIMENSIONS, _command_parser, _subcommand_parsers

from command_runner import BIRTH, run


@pytest.mark.parametrize('args', [('--help',), ('-h',)])
def test_top_level_help_lists_three_tasks(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = run(tmp_path, *args)
  assert result.returncode == 0 and '提示：' not in result.stderr
  for task in _COMMANDS:
    assert re.search(rf'^\s+{task}\s+\S', result.stdout, flags=re.MULTILINE)
    assert f'python run_interpreter.py {task}' in result.stdout


@pytest.mark.parametrize('task', _COMMANDS)
def test_task_help_fits_one_screen(tmp_path: Path, task: str) -> None:
  result = run(tmp_path, task, '--help', env={'COLUMNS': '80'})
  assert result.returncode == 0
  assert len(result.stdout.splitlines()) <= 45, result.stdout
  assert '更多选项' in result.stdout


def test_chart_command_shows_a_seeded_chart(tmp_path: Path) -> None:
  first, second = (run(tmp_path, 'chart', '--seed', '42') for _ in range(2))
  assert first.returncode == 0 and first.stdout == second.stdout and first.stderr == ''
  assert first.stdout.startswith('random seed: 42\n')
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('flag, value, needs', [
  ('--precision', 'hour', '--birth-time'), ('--longitude', '120', '--birth-time'),
  ('--civil-timezone', '+08:00', '经度'), ('--export-chart-json', 'out/c.json', '--birth-time'),
])
def test_chart_help_names_what_these_options_need(tmp_path: Path, flag: str, value: str, needs: str) -> None:
  result = run(tmp_path, 'chart', flag, value)
  assert result.returncode == 2 and 'require fixed birth input' in result.stderr
  action = next(a for a in _subcommand_parsers(_command_parser())['chart']._actions if flag in a.option_strings)
  assert needs in (action.help or '')


def test_chart_command_has_no_knowledge_options(tmp_path: Path) -> None:
  for flag in (('--object', 'tiangan.ding'), ('--export-knowledge-base',), ('--observation-scope', 'natal')):
    result = run(tmp_path, 'chart', *flag)
    assert result.returncode == 2 and 'unrecognized arguments' in result.stderr


def test_gz_month_help_names_the_year(tmp_path: Path) -> None:
  result = run(tmp_path, 'match', 'editorial.spouse_star_tougan.v1', *BIRTH, '--gender', 'female',
                '--observation-scope', 'natal_and_transits', '--transit-entry', 'at_month', '--gz-month', '午')
  assert result.returncode == 2 and 'gz_year' in result.stderr
  action = next(a for a in _subcommand_parsers(_command_parser())['match']._actions if '--gz-month' in a.option_strings)
  assert '--ganzhi-year' in (action.help or '')


def test_options_agree_with_library_directories() -> None:
  subparsers = _subcommand_parsers(_command_parser())
  assert tuple(subparsers) == _COMMANDS
  dests = {name: {action.dest: action for action in sub._actions} for name, sub in subparsers.items()}
  assert set(dests['knowledge']['applicability'].choices or ()) == set(get_args(Applicability))
  assert tuple(dests['knowledge']['list_values'].choices or ()) == tuple(_LIST_DIMENSIONS)
  scopes = tuple(dests['match']['observation_scope'].choices or ())
  assert scopes == (*get_args(ObservationScope), 'natal_and_transits')
  assert set(scopes) == {scope for info in criteria().values() for scope in info.scopes}
  entries = tuple(dests['match']['transit_entry'].choices or ())
  assert entries == get_args(TransitEntry)
  assert set(entries) == {entry for info in criteria().values() for entry in info.transit_entries}
  assert not {'object_id', 'observation_scope', 'export_knowledge_base'} & set(dests['chart'])
  assert not {'seed', 'object_id', 'export_chart_json'} & set(dests['match'])
