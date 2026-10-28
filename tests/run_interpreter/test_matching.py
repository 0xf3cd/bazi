# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import inspect
import json
from pathlib import Path
from typing import get_args

import pytest

from run_interpreter import _LIST_DIMENSIONS, _COORDINATE_FLAGS, _command_parser, _subcommand_parsers
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.knowledge import DEFAULT_SOURCE_PATH, Applicability, KnowledgeBase
from bazi.context_matching import NatalObservation, LiunianObservation, criteria, evaluate_context

from cli_runner import MATCH_ARGS, MATCH_BIRTH, run_cli, assert_cli_error


def test_cli_filters_match_library_directories() -> None:
  parsers = _subcommand_parsers(_command_parser())
  actions = {action.dest: action for action in parsers['knowledge']._actions}
  matching = {action.dest: action for action in parsers['match']._actions}
  flags = {
    'object_id': '--object', 'context_id': '--context', 'source_id': '--source',
    'topic': '--topic', 'viewpoint': '--viewpoint', 'applicability': '--applicability', 'time_scope': '--time-scope',
  }
  assert set(inspect.signature(KnowledgeBase.query).parameters) - {'self', 'include_reference_only'} == set(flags)
  assert set(inspect.signature(KnowledgeBase.search).parameters) - {'self', 'keyword', 'include_reference_only'} == set(flags)
  assert set(_LIST_DIMENSIONS.values()) == set(flags)
  for dimension, flag in flags.items():
    assert actions[dimension].option_strings == [flag]
  assert tuple(actions['applicability'].choices or ()) == get_args(Applicability)
  scopes = tuple(matching['observation_scope'].choices or ())
  assert scopes == ('natal', 'natal_and_liunian', 'natal_and_transits')
  assert set(scopes) == {scope for info in criteria().values() for scope in info.scopes}
  entries = tuple(matching['transit_entry'].choices or ())
  assert entries == ('at_year', 'at_month', 'at_date', 'at_moment')
  assert set(entries) == {entry for info in criteria().values() for entry in info.transit_entries}
  actual_flags = {flag for action in matching.values() for flag in action.option_strings}
  for info in criteria().values():
    for names in info.transit_entries.values():
      assert all(_COORDINATE_FLAGS[name] in actual_flags for name in names)
  assert not {'find_objects', 'search', 'criteria'} & (set(actions) | set(matching))


def test_text_agrees_with_library(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *MATCH_ARGS, '--include-reference-only')
  assert result.returncode == 0, result.stderr
  expected = evaluate_context(BaziChart(Bazi.create('2000-01-03 12:00', 'female')), criterion_id='editorial.guansha_coexistence.v1', observation=NatalObservation(), include_reference_only=True)
  assert result.stdout == expected.render() + '\n'
  assert '也许' in result.stdout and '仅供参考' in result.stdout
  assert '不确立古籍规则，也不作现实预测。' in result.stdout
  assert any(line.startswith('证据：natal.月；') for line in result.stdout.splitlines())


@pytest.mark.parametrize('scope,year,status', [
  ('natal', None, 'NOT_SATISFIED'), ('natal_and_liunian', None, 'UNKNOWN'),
  ('natal_and_liunian', '1998', 'UNKNOWN'), ('natal_and_liunian', '0', 'UNKNOWN'),
  ('natal_and_liunian', '-1', 'UNKNOWN'), ('natal_and_liunian', '2024', 'SATISFIED'),
])
def test_verdicts_follow_reference_opt_in(tmp_path: Path, scope: str, year: str | None, status: str) -> None:
  args = ('match', 'editorial.guansha_coexistence.v1', '--birth-time', '2000-01-01 12:00', '--gender', 'female', '--observation-scope', scope)
  result = run_cli(tmp_path, *args, *(('--ganzhi-year', year) if year else ()))
  assert result.returncode == 0 and f'结构前提：{status}' in result.stdout
  assert '原作参考前提：' not in result.stdout and '也许' not in result.stdout
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('extra,error', [
  (('--seed', '42'), 'unrecognized arguments'), (('--count', '1'), 'unrecognized arguments'),
  (('--output-dir', 'out'), 'unrecognized arguments'), (('--export-knowledge-base',), 'unrecognized arguments'),
  (('--query-knowledge',), 'unrecognized arguments'), (('--validate-knowledge',), 'unrecognized arguments'),
  (('--export-knowledge-json', 'k.json'), 'unrecognized arguments'),
  (('--object', 'tiangan.ding'), 'unrecognized arguments'), (('--context', 'legacy.chart_context'), 'unrecognized arguments'),
  (('--topic', '取象'), 'unrecognized arguments'), (('--source', 'editorial'), 'unrecognized arguments'),
  (('--viewpoint', '仓内原作'), 'unrecognized arguments'), (('--applicability', 'described'), 'unrecognized arguments'),
  (('--time-scope', '行运'), 'unrecognized arguments'),
  (('--ganzhi-year', '2024'), 'Natal scope cannot include a transit coordinate'),
  (('--ganzhi-year', 'bad'), 'invalid int value'),
])
def test_invalid_match_options_do_not_export(tmp_path: Path, extra: tuple[str, ...], error: str) -> None:
  result = run_cli(tmp_path, *MATCH_ARGS, *extra)
  assert_cli_error(result, 'match', error)
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('args,error', [
  (('match', 'editorial.guansha_coexistence.v1', '--include-reference-only'), 'missing --birth-time'),
  (('match', 'typo', '--birth-time', '2000-01-03 12:00', '--gender', 'female', '--observation-scope', 'natal'), 'Unsupported value: typo'),
  (('match', 'editorial.guansha_coexistence.v1', '--birth-time', 'bad', '--gender', 'female', '--observation-scope', 'natal'), 'Invalid isoformat string'),
  (('match', 'editorial.guansha_coexistence.v1', '--birth-time', '2000-01-03 12:00', '--gender', 'female'), 'missing --observation-scope'),
  (('match', '--observation-scope', 'natal'), 'a criterion ID is required'),
  (('match', '--ganzhi-year', '2024'), 'a criterion ID is required'),
])
def test_missing_or_bad_requests_fail(tmp_path: Path, args: tuple[str, ...], error: str) -> None:
  result = run_cli(tmp_path, *args)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'usage: python run_interpreter.py match' in result.stderr and error in result.stderr
  assert list(tmp_path.iterdir()) == []


def test_missing_source_is_an_argparse_error(tmp_path: Path) -> None:
  result = run_cli(tmp_path, *MATCH_ARGS, '--knowledge-source', str(tmp_path / 'missing.json'))
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'Traceback' not in result.stderr
  assert 'No such file or directory' in result.stderr
  assert list(tmp_path.iterdir()) == []


@pytest.fixture
def edited_source(tmp_path: Path) -> Path:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  next(e for e in data['entries'] if e['claim_id'] == 'editorial.shishen.zhengguan.legal_trouble')['premise'] = '不同前提'
  source = tmp_path / 'edited.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  return source


def test_custom_source_reports_binding_mismatch(tmp_path: Path, edited_source: Path) -> None:
  source = edited_source
  result = run_cli(tmp_path, *MATCH_ARGS, '--include-reference-only', '--knowledge-source', str(source))
  assert result.returncode == 0 and 'binding_unrecognized' in result.stdout
  assert '不同前提' in result.stdout
  assert '原作参考前提：editorial.shishen.zhengguan.legal_trouble；UNKNOWN' in result.stdout


@pytest.mark.parametrize('criterion_id,status', [
  ('tiangan.ding_weak_and_overcontrolled', 'NOT_SATISFIED'),
  ('tiangan.geng_regulated_transit', 'SATISFIED'),
  ('shishen.pianyin_favorable_or_balanced', 'SATISFIED'),
  ('shishen.xiaoyin_duoshi', 'SATISFIED'),
])
@pytest.mark.parametrize('year', [None, 2024])
@pytest.mark.parametrize('reference', [False, True])
def test_condition_criteria_agree_with_library(
  tmp_path: Path, criterion_id: str, status: str, year: int | None, reference: bool,
) -> None:
  scope = ('--observation-scope', 'natal') if year is None else ('--observation-scope', 'natal_and_liunian', '--ganzhi-year', str(year))
  result = run_cli(
    tmp_path, 'match', criterion_id, *MATCH_BIRTH, *scope,
    *(('--include-reference-only',) if reference else ()),
  )
  assert result.returncode == 0, result.stderr
  observation = NatalObservation() if year is None else LiunianObservation(year)
  expected = evaluate_context(BaziChart(Bazi.create('2000-01-03 12:00', 'female')), criterion_id=criterion_id, observation=observation, include_reference_only=reference)
  assert expected.criterion.status == status
  assert result.stdout == expected.render() + '\n'
  assert f'事实判别：{status}' in result.stdout
  assert ('完整前提未由程序判别' in result.stdout) is reference
