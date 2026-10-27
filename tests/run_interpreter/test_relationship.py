# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from pathlib import Path

import pytest


from cli_runner import MATCH_ARGS, run_cli, assert_cli_error


# #233 婚恋判据 CLI: guard matrix and legal combinations.

PALACE = 'editorial.spouse_palace_xingchong.v1'
TOUGAN = 'editorial.spouse_star_tougan.v1'

REL_BASE = ('match', PALACE, '--birth-time', '2000-01-01 12:00', '--gender', 'male',
            '--observation-scope', 'natal')
REL_TRANSIT_BASE = ('match', TOUGAN, '--birth-time', '2000-01-01 12:00', '--gender', 'male',
                    '--observation-scope', 'natal_and_transits')


@pytest.mark.parametrize('args', [
  ('--observation-scope', 'natal_and_transits'),
  ('--transit-entry', 'at_year'),
  ('--gz-month', '辰'),
  ('--solar-date', '2024-04-10'),
  ('--solar-moment', '2024-04-10T12:00:00'),
  ('--transit-kinds', 'liunian'),
])
def test_relationship_inputs_need_a_criterion(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, 'match', *args)
  assert result.returncode == 2 and 'a criterion ID is required' in result.stderr
  assert 'usage: python run_interpreter.py match' in result.stderr
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('extra', [
  ('--query-knowledge',),
  ('--seed', '7'),
  ('--export-knowledge-json', 'k.json'),
])
def test_relationship_rejects_unknown_options(tmp_path: Path, extra: tuple[str, ...]) -> None:
  output = tmp_path / 'match.json'
  result = run_cli(tmp_path, *REL_BASE, '--transit-kinds', 'liunian', '--observation-scope', 'natal_and_transits', *extra)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert_cli_error(result, 'match', 'unrecognized arguments')
  assert not output.exists()


@pytest.mark.parametrize('extra', [
  ('--transit-entry', 'at_year'),
  ('--gz-month', '辰'),
  ('--solar-date', '2024-04-10'),
  ('--solar-moment', '2024-04-10T12:00:00'),
  ('--transit-kinds', 'liunian'),
])
def test_context_criteria_reject_new_flags(tmp_path: Path, extra: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, *MATCH_ARGS, *extra)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'usage: python run_interpreter.py match' in result.stderr
  assert 'Context criteria cannot combine transit entry, coordinate or kind inputs' in result.stderr
  assert list(tmp_path.iterdir()) == []


def test_context_scope_rejects_natal_transits(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *MATCH_ARGS, '--observation-scope', 'natal_and_transits')
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'usage: python run_interpreter.py match' in result.stderr and 'Unsupported value: natal_and_transits' in result.stderr


def test_relationship_rejects_natal_liunian(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *REL_BASE, '--observation-scope', 'natal_and_liunian')
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'usage: python run_interpreter.py match' in result.stderr and 'Unsupported value: natal_and_liunian' in result.stderr


@pytest.mark.parametrize('extra,error', [
  (('--ganzhi-year', '2024'), 'Transit coordinates require --transit-entry'),
  (('--gz-month', '辰'), 'Transit coordinates require --transit-entry'),
  (('--solar-date', '2024-04-10'), 'Transit coordinates require --transit-entry'),
  (('--solar-moment', '2024-04-10T12:00:00'), 'Transit coordinates require --transit-entry'),
  (('--transit-kinds', 'liunian'), 'Natal scope cannot include transit inputs'),
  (('--transit-entry', 'at_year'), 'Missing coordinate field'),
])
def test_relationship_natal_rejects_transits(tmp_path: Path, extra: tuple[str, ...], error: str) -> None:
  result = run_cli(tmp_path, *REL_BASE, *extra)
  assert_cli_error(result, 'match', error)


def test_natal_transits_requires_kinds(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'usage: python run_interpreter.py match' in result.stderr and 'requires explicit transit kinds' in result.stderr


@pytest.mark.parametrize('flag,value,error', [
  ('--ganzhi-year', 'bad', 'invalid int value'), ('--gz-month', '子丑', 'not a valid Dizhi'),
  ('--gz-month', 'YOU', 'not a valid Dizhi'),
  ('--solar-date', '2024-04-10T12:00:00', 'Invalid isoformat string'),
  ('--solar-date', '20240410', 'Expected canonical ISO date'),
  ('--solar-moment', '2024-04-10 12:00:00', 'Expected canonical naive moment'),
  ('--solar-moment', '2024-04-10T12:00:00.25', 'Expected canonical naive moment'),
  ('--solar-moment', '2024-04-10T12:00:00+08:00', 'Expected canonical naive moment'),
  ('--solar-moment', 'bad', 'Invalid isoformat string'),
])
def test_coordinate_values_must_be_canonical(tmp_path: Path, flag: str, value: str, error: str) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-entry', 'at_date', '--transit-kinds', 'liunian', flag, value)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'usage: python run_interpreter.py match' in result.stderr and error in result.stderr


@pytest.mark.parametrize('entry_args', [
  ('--transit-entry', 'at_year', '--ganzhi-year', '2024', '--gz-month', '辰'),
  ('--transit-entry', 'at_year', '--ganzhi-year', '2024', '--solar-date', '2024-04-10'),
  ('--transit-entry', 'at_year', '--ganzhi-year', '2024', '--solar-moment', '2024-04-10T12:00:00'),
  ('--transit-entry', 'at_month', '--ganzhi-year', '2024', '--gz-month', '辰', '--solar-date', '2024-04-10'),
  ('--transit-entry', 'at_month', '--ganzhi-year', '2024', '--gz-month', '辰', '--solar-moment', '2024-04-10T12:00:00'),
  ('--transit-entry', 'at_date', '--solar-date', '2024-04-10', '--ganzhi-year', '2024'),
  ('--transit-entry', 'at_date', '--solar-date', '2024-04-10', '--gz-month', '辰'),
  ('--transit-entry', 'at_moment', '--solar-moment', '2024-04-10T12:00:00', '--ganzhi-year', '2024'),
  ('--transit-entry', 'at_moment', '--solar-moment', '2024-04-10T12:00:00', '--solar-date', '2024-04-10'),
])
def test_entry_fields_are_mutually_exclusive(tmp_path: Path, entry_args: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian', *entry_args)
  assert_cli_error(result, 'match', 'Unexpected coordinate field')


@pytest.mark.parametrize('entry_args, missing', [
  (('--transit-entry', 'at_year'), '--ganzhi-year'),
  (('--transit-entry', 'at_month', '--ganzhi-year', '2024'), '--gz-month'),
  (('--transit-entry', 'at_month', '--gz-month', '辰'), '--ganzhi-year'),
  (('--transit-entry', 'at_date'), '--solar-date'),
  (('--transit-entry', 'at_moment'), '--solar-moment'),
])
def test_entry_fields_are_required(tmp_path: Path, entry_args: tuple[str, ...], missing: str) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian', *entry_args)
  assert result.returncode == 2 and 'error:' in result.stderr, missing
  field = {'--ganzhi-year': 'ganzhi_year', '--gz-month': 'ganzhi_month', '--solar-date': 'solar_date', '--solar-moment': 'solar_moment'}[missing]
  assert 'usage: python run_interpreter.py match' in result.stderr
  assert f'Missing coordinate field for {entry_args[1]}: {field}' in result.stderr


@pytest.mark.parametrize('entry_args, kinds', [
  (('--transit-entry', 'at_year', '--ganzhi-year', '2024'), 'liuyue'),
  (('--transit-entry', 'at_year', '--ganzhi-year', '2024'), 'liuri'),
  (('--transit-entry', 'at_month', '--ganzhi-year', '2024', '--gz-month', '辰'), 'xiaoyun,liuri'),
])
def test_kinds_must_be_within_entry_support(tmp_path: Path, entry_args: tuple[str, ...], kinds: str) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', kinds, *entry_args)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'usage: python run_interpreter.py match' in result.stderr and 'Unsupported transit kinds for' in result.stderr


@pytest.mark.parametrize('kinds,error', [
  ('liunian,liunian', 'Duplicate transit kinds'), ('bogus', 'Unsupported transit kind'),
  ('liunian,', 'Unsupported transit kind'), (',liunian', 'Unsupported transit kind'),
  ('', 'Unsupported transit kind'),
])
def test_kinds_reject_duplicates_unknown_empty(tmp_path: Path, kinds: str, error: str) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', kinds,
                    '--transit-entry', 'at_year', '--ganzhi-year', '2024')
  assert_cli_error(result, 'match', error)


def test_coordinate_fields_require_entry(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian', '--ganzhi-year', '2024')
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'usage: python run_interpreter.py match' in result.stderr and 'Transit coordinates require --transit-entry' in result.stderr


def test_kinds_without_coordinate_is_unknown(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian')
  assert result.returncode == 0, result.stderr
  assert '事实判别：UNKNOWN；missing_transit_coordinate' in result.stdout
  assert '请求种类=[liunian]；取得种类=[]；未取得种类=[liunian]' in result.stdout
  assert '关联参考' not in result.stdout


def test_unordered_kinds_are_normalized(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian,dayun',
                    '--transit-entry', 'at_year', '--ganzhi-year', '2024')
  assert result.returncode == 0, result.stderr
  assert '请求种类=[dayun,liunian]；取得种类=[dayun,liunian]' in result.stdout


def test_natal_month_hidden_literal(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'match', TOUGAN, '--birth-time', '2000-01-09 12:00', '--gender', 'male', '--observation-scope', 'natal')
  assert result.returncode == 0, result.stderr
  assert '证据出现：natal.月；丁丑；藏干；辛' in result.stdout.splitlines()


def test_extra_month_field_names_library_field(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian', '--transit-entry', 'at_year', '--ganzhi-year', '2024', '--gz-month', '辰')
  assert_cli_error(result, 'match', 'Unexpected coordinate field for at_year: ganzhi_month')


@pytest.mark.parametrize('entry_args', [
  ('--transit-entry', 'at_year', '--ganzhi-year', '2024'),
  ('--transit-entry', 'at_month', '--ganzhi-year', '2024', '--gz-month', '辰'),
  ('--transit-entry', 'at_date', '--solar-date', '2024-04-10'),
  ('--transit-entry', 'at_moment', '--solar-moment', '2024-04-10T12:00:00'),
])
@pytest.mark.parametrize('flag', [(), ('--include-reference-only',)])
def test_legal_relationship_combinations(tmp_path: Path, entry_args: tuple[str, ...], flag: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, *REL_TRANSIT_BASE, '--transit-kinds', 'liunian', *entry_args, *flag)
  assert result.returncode == 0, result.stderr
  assert '事实判别：' in result.stdout and '证据：原局内部；' in result.stdout
  assert '证据：原局×岁运；' in result.stdout and '证据：岁运内部；' in result.stdout
  # at_moment requires a HOUR/MINUTE natal chart; with DAY precision the unavailable entry is an EXIT 0 UNKNOWN, not an error.
  if entry_args[1] == 'at_moment':
    assert '事实判别：UNKNOWN；transit_unavailable' in result.stdout
  assert ('关联参考' in result.stdout) == bool(flag)
  if flag:
    assert '该判据的条件参考，不表示事实已成立或完整前提已满足' in result.stdout
