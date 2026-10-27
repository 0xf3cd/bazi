# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
from pathlib import Path

import pytest

from run_interpreter import interpret
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import NatalObservation, evaluate_context
from bazi.school import BaziConfig

from cli_runner import MATCH_ARGS, run_cli, assert_cli_error


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('precision,pillars', [
  ('hour', ('庚辰', '戊寅')), ('minute', ('己卯', '丁丑')),
])
def test_naive_cli_precision(tmp_path: Path, optimized: bool, precision: str, pillars: tuple[str, str]) -> None:
  birth = '2000-02-04T20:39:59.123456'
  config = BaziConfig.from_values(precision=precision)
  expected = BaziChart(Bazi.create(birth, 'female', config))
  args = ('--birth-time', birth, '--gender', 'female', '--precision', precision)
  result = run_cli(tmp_path, 'chart', *args, optimized=optimized)
  assert result.returncode == 0, result.stderr
  assert expected.bazi.solar_datetime.isoformat() == '2000-02-04T20:39:00'
  assert tuple(map(str, expected.bazi.pillars))[:2] == pillars
  assert interpret(expected) in result.stdout
  result = run_cli(tmp_path, 'match', 'editorial.guansha_coexistence.v1', *args,
                    '--observation-scope', 'natal', '--include-reference-only', optimized=optimized)
  assert result.returncode == 0, result.stderr
  expected_record = evaluate_context(expected, criterion_id='editorial.guansha_coexistence.v1',
                                     observation=NatalObservation(), include_reference_only=True)
  assert result.stdout == expected_record.render() + '\n'
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('precision', ['hour', 'minute'])
@pytest.mark.parametrize('basis', ['+14:00', 'Pacific/Kiritimati'])
def test_location_chart_matching_text(tmp_path: Path, optimized: bool, precision: str, basis: str) -> None:
  args = ('--birth-time', '2023-12-31T22:00:00+00:00', '--gender', 'female',
          '--longitude', '-157.4', '--precision', precision, '--civil-timezone', basis)
  result = run_cli(tmp_path, 'chart', *args, optimized=optimized)
  assert result.returncode == 0, result.stderr
  assert '2024-01-01T12:00:00+14:00' in result.stdout
  assert '2024-01-01T11:27:21.883333' in result.stdout
  assert '民用出生时刻' in result.stdout and '真太阳出生时刻' in result.stdout
  result = run_cli(tmp_path, 'match', 'editorial.guansha_coexistence.v1', *args,
                    '--observation-scope', 'natal', optimized=optimized)
  assert result.returncode == 0, result.stderr
  assert '民用时刻=2024-01-01T12:00:00+14:00' in result.stdout
  assert '真太阳时=2024-01-01T11:27:21.883333' in result.stdout


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('precision', ['hour', 'minute'])
def test_negative_fixed_offset_equals_syntax(tmp_path: Path, optimized: bool, precision: str) -> None:
  args = ('--birth-time', '2024-01-02T01:00:00+00:00', '--gender', 'female',
          '--longitude', '-74', '--precision', precision, '--civil-timezone=-05:00')
  result = run_cli(tmp_path, 'chart', *args, optimized=optimized)
  assert result.returncode == 0, result.stderr
  assert '2024-01-01T20:00:00-05:00' in result.stdout
  assert '2024-01-01T20:00:25.933333' in result.stdout
  result = run_cli(tmp_path, 'match', 'editorial.guansha_coexistence.v1', *args,
                    '--observation-scope', 'natal', optimized=optimized)
  assert result.returncode == 0, result.stderr
  assert '民用时刻=2024-01-01T20:00:00-05:00' in result.stdout


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('matching', [False, True])
@pytest.mark.parametrize('zone', ['America', 'Asia', 'Etc', 'Unknown/Region', '+99:00'])
def test_bad_civil_zone_is_an_argument_error(tmp_path: Path, optimized: bool, matching: bool, zone: str) -> None:
  args = ('--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'female', '--longitude', '-157.4',
          '--precision', 'minute', '--civil-timezone', zone)
  task = ('match', 'editorial.guansha_coexistence.v1') if matching else ('chart',)
  extra = ('--observation-scope', 'natal') if matching else ()
  result = run_cli(tmp_path, *task, *args, *extra, optimized=optimized)
  assert result.returncode == 2
  assert 'error: argument --civil-timezone:' in result.stderr
  assert 'Traceback' not in result.stderr
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('optimized', [False, True])
def test_location_midnight_labels_in_outputs(tmp_path: Path, optimized: bool) -> None:
  result = run_cli(tmp_path, 'chart', '--birth-time', '2024-06-01T23:50:00+08:00', '--gender', 'male',
                    '--longitude', '125', '--precision', 'minute', '--output-dir', str(tmp_path), optimized=optimized)
  assert result.returncode == 0, result.stderr
  assert '真太阳时日期：2024-06-02' in result.stdout
  assert '真太阳时（分钟显示）：2024-06-02T00:12:00' in result.stdout
  assert '民用出生时刻（固定出生地偏移）：2024-06-01T23:50:00+08:00' in result.stdout
  assert '生于 2024-06-02' not in result.stdout and '出生时间：2024-06-02' not in result.stdout
  saved = tmp_path / 'interpretation_examples/0.txt'
  assert saved.read_text(encoding='utf-8') == re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).removesuffix('\n')


def test_legacy_renderer_keeps_birth_labels() -> None:
  from run_demo import get_basic_info
  chart = BaziChart(Bazi.create('2024-06-01T23:50:00', 'male', BaziConfig.from_values(precision='minute')))
  assert '生于 2024-06-01' in get_basic_info(chart)
  text = interpret(chart)
  assert text.startswith('出生时间：2024-06-01, 23:50\n')
  assert '真太阳时' not in text and '民用出生时刻' not in get_basic_info(chart)


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('args,error', [
  (('chart', '--longitude', '0'), 'require fixed birth input'),
  (('chart', '--precision', 'hour'), 'require fixed birth input'),
  (('chart', '--civil-timezone', '+14:00'), 'require fixed birth input'),
  (('chart', '--export-chart-json', 'out.json'), 'unrecognized arguments'),
  (('knowledge', '--longitude', '0'), 'unrecognized arguments'),
  (('knowledge', '--validate-knowledge', '--precision', 'minute'), 'unrecognized arguments'),
  (('knowledge', '--export-knowledge-json', 'out.json', '--civil-timezone', '+14:00'), 'unrecognized arguments'),
  (('knowledge', '--export-chart-json', 'out.json'), 'unrecognized arguments'),
  (('chart', '--birth-time', '2024-01-01T12:00:00', '--gender', 'male', '--longitude', '0', '--precision', 'hour'), 'Longitude requires a timezone-aware birth_time'),
  (('chart', '--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'male', '--longitude', '-157.4'), 'Longitude requires BaziPrecision.HOUR or BaziPrecision.MINUTE'),
  (('chart', '--birth-time', '2024-01-01T12:00:00', '--gender', 'male', '--civil-timezone', '+14:00'), 'civil_timezone requires longitude'),
  (('chart', '--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'male', '--longitude', '-157.4', '--precision', 'minute', '--civil-timezone', 'Unknown/Region'), 'argument --civil-timezone'),
  (('chart', '--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'male', '--longitude', '-157.4', '--precision', 'minute', '--civil-timezone', '+99:00'), 'argument --civil-timezone'),
  ((*MATCH_ARGS, '--longitude', '0'), 'Longitude requires a timezone-aware birth_time'),
  ((*MATCH_ARGS, '--civil-timezone', 'Unknown/Region'), 'argument --civil-timezone'),
  ((*MATCH_ARGS, '--export-chart-json', 'out.json'), 'unrecognized arguments'),
])
def test_invalid_task_inputs_fail_early(tmp_path: Path, optimized: bool, args: tuple[str, ...], error: str) -> None:
  result = run_cli(tmp_path, *args, optimized=optimized)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert_cli_error(result, args[0], error)
  assert 'Traceback' not in result.stderr
  assert list(tmp_path.iterdir()) == []
