# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_match_command.py

from pathlib import Path

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import NatalObservation, criteria, evaluate_context
from run_interpreter import _command_parser, _subcommand_parsers

from cli_runner import GUANSHA, BIRTH, run_cli


def test_bare_match_lists_every_criterion(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'match')
  assert result.returncode == 0
  for criterion_id, info in criteria().items():
    assert criterion_id in result.stdout and info.definition in result.stdout


@pytest.mark.parametrize('criterion_id', sorted(criteria()))
def test_match_with_only_an_id_describes_it(tmp_path: Path, criterion_id: str) -> None:
  info = criteria()[criterion_id]
  result = run_cli(tmp_path, 'match', criterion_id)
  assert result.returncode == 0 and result.stderr == ''
  assert info.definition in result.stdout and f'match {criterion_id} --birth-time' in result.stdout
  assert all(scope in result.stdout for scope in info.scopes)
  assert all(f'--transit-entry {entry}' in result.stdout for entry in info.transit_entries)
  if 'natal_and_liunian' in info.scopes:
    assert '--observation-scope natal_and_liunian 还需要：--ganzhi-year' in result.stdout
  gate = info.required_gender
  assert (gate is not None) == ('性别门槛：' in result.stdout)
  assert gate is None or f'性别门槛：{gate.value}（--gender {gate}）' in result.stdout
  assert list(tmp_path.iterdir()) == []


def test_match_unknown_id_points_to_the_list(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'match', 'nope')
  assert result.returncode == 2 and 'Unsupported' in result.stderr and 'match 可列出全部判据' in result.stderr


@pytest.mark.parametrize('given, missing', [
  (('--birth-time', '2000-01-03 12:00'), ('--gender', '--observation-scope')),
  (('--gender', 'female'), ('--birth-time', '--observation-scope')),
  (('--observation-scope', 'natal'), ('--birth-time', '--gender')),
  (('--include-reference-only',), ('--birth-time', '--gender', '--observation-scope')),
])
def test_match_names_every_missing_input(tmp_path: Path, given: tuple[str, ...], missing: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, 'match', GUANSHA, *given)
  assert result.returncode == 2
  assert f'missing {" and ".join(missing)};' in result.stderr
  assert 'example: python run_interpreter.py match <判据ID> --birth-time' in result.stderr
  assert list(tmp_path.iterdir()) == []


EVALUATION_INPUTS = [
  ('birth_time', ('--birth-time', '2000-01-03 12:00')), ('gender', ('--gender', 'female')),
  ('observation_scope', ('--observation-scope', 'natal')), ('ganzhi_year', ('--ganzhi-year', '2024')),
  ('transit_entry', ('--transit-entry', 'at_year')), ('gz_month', ('--gz-month', '午')),
  ('solar_date', ('--solar-date', '2024-04-10')), ('solar_moment', ('--solar-moment', '2024-04-10T12:00:00')),
  ('transit_kinds', ('--transit-kinds', 'liuri')), ('longitude', ('--longitude', '120')),
  ('precision', ('--precision', 'hour')), ('civil_timezone', ('--civil-timezone', '+08:00')),
  ('knowledge_source', ('--knowledge-source', 'src.json')),
  ('include_reference_only', ('--include-reference-only',)),
]


def test_every_option_is_an_evaluation_input() -> None:
  dests = {action.dest for action in _subcommand_parsers(_command_parser())['match']._actions}
  assert dests - {'help', 'criterion'} == {dest for dest, _ in EVALUATION_INPUTS}


@pytest.mark.parametrize('dest, args', EVALUATION_INPUTS, ids=[dest for dest, _ in EVALUATION_INPUTS])
def test_match_evaluation_inputs_need_an_id(tmp_path: Path, dest: str, args: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, 'match', *args)
  assert result.returncode == 2 and 'criterion ID is required for evaluation' in result.stderr
  assert result.stdout == '' and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('dest, args', EVALUATION_INPUTS, ids=[dest for dest, _ in EVALUATION_INPUTS])
def test_id_with_one_input_asks_for_the_rest(tmp_path: Path, dest: str, args: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, 'match', GUANSHA, *args)
  assert result.returncode == 2 and 'missing --' in result.stderr and 'example: ' in result.stderr
  assert result.stdout == '' and list(tmp_path.iterdir()) == []


def test_match_new_form_equals_the_library(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'match', GUANSHA, *BIRTH, '--gender', 'female', '--observation-scope', 'natal')
  expected = evaluate_context(
    BaziChart(Bazi.create('2000-01-03 12:00', 'female')), criterion_id=GUANSHA, observation=NatalObservation(),
  ).render()
  assert result.returncode == 0 and result.stdout == expected + '\n'


def test_match_keeps_the_input_validation(tmp_path: Path) -> None:
  for args in (
    ('--observation-scope', 'natal_and_transits'),
    ('--observation-scope', 'natal', '--transit-entry', 'at_year'),
  ):
    result = run_cli(tmp_path, 'match', GUANSHA, *BIRTH, '--gender', 'female', *args)
    assert result.returncode == 2 and 'error:' in result.stderr
