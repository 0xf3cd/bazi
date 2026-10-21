# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
import json
from pathlib import Path
from typing import cast

import pytest

from run_interpreter import interpret
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart, BaziJson
from bazi.context_matching import ContextProfile, ContextResult, evaluate_context
from bazi.school import BaziConfig

from cli_runner import MATCH_ARGS, run_cli, assert_cli_error


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('precision,pillars', [
  ('hour', ('庚辰', '戊寅')), ('minute', ('己卯', '丁丑')),
])
def test_naive_cli_precision_and_exports(tmp_path: Path, optimized: bool, precision: str, pillars: tuple[str, str]) -> None:
  birth = '2000-02-04T20:39:59.123456'
  config = BaziConfig.from_values(precision=precision)
  expected = BaziChart(Bazi.create(birth, 'female', config))
  output = tmp_path / 'legacy-chart.json'
  args = ('--birth-time', birth, '--gender', 'female', '--precision', precision)
  result = run_cli(tmp_path, 'chart', *args, '--export-chart-json', str(output), optimized=optimized)
  assert result.returncode == 0, result.stderr
  assert output.is_file()
  data = json.loads(output.read_text(encoding='utf-8'))
  assert set(data) == {
    'birth_time', 'gender', 'precision', 'backend', 'dayun_year_rule', 'school', 'pillars', 'nayin',
    'shier_zhangsheng', 'tiangan_traits', 'dizhi_traits', 'tiangan_shishen', 'dizhi_shishen', 'hidden_tiangan', 'transits',
  }
  assert data['birth_time'] == '2000-02-04T20:39:00' and data['precision'] == precision
  assert (data['pillars']['year'], data['pillars']['month']) == pillars
  restored = BaziChart.from_json(data)
  assert restored.bazi.config == config and restored.json == data == expected.json

  matched = tmp_path / 'legacy-context.json'
  result = run_cli(tmp_path, 'match', 'editorial.guansha_coexistence.v1', *args,
                    '--observation-scope', 'natal', '--include-reference-only', '--export-context-json', str(matched), optimized=optimized)
  assert result.returncode == 0, result.stderr
  assert matched.is_file()
  record = ContextResult.from_json(matched.read_text(encoding='utf-8'))
  identity = json.loads(record.input_json)
  assert set(identity) == {'birth_time', 'gender', 'config', 'pillars'}
  assert identity['birth_time'] == '2000-02-04T20:39:00' and identity['config']['precision'] == precision
  assert tuple(identity['pillars'][:2]) == pillars
  expected_record = evaluate_context(expected, criterion_id='editorial.guansha_coexistence.v1',
                                     profile=ContextProfile('natal'), include_reference_only=True)
  assert record == expected_record
  assert record.export_json() == matched.read_text(encoding='utf-8') == expected_record.export_json()


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('precision', ['hour', 'minute'])
@pytest.mark.parametrize('basis', ['+14:00', 'Pacific/Kiritimati'])
def test_location_chart_matching_export_restore(tmp_path: Path, optimized: bool, precision: str, basis: str) -> None:
  output = tmp_path / 'chart.json'
  args = ('--birth-time', '2023-12-31T22:00:00+00:00', '--gender', 'female',
          '--longitude', '-157.4', '--precision', precision, '--civil-timezone', basis)
  result = run_cli(tmp_path, 'chart', *args, '--export-chart-json', str(output), optimized=optimized)
  assert result.returncode == 0, result.stderr
  chart = BaziChart.from_json(json.loads(output.read_text(encoding='utf-8')))
  data = cast(BaziJson.LocationBaziChartJsonDict, chart.json)
  assert data['civil_time'] == '2024-01-01T12:00:00+14:00'
  assert data['apparent_time'] == '2024-01-01T11:27:21.883333'
  assert '民用出生时刻' in result.stdout and '真太阳出生时刻' in result.stdout
  matched = tmp_path / 'matching.json'
  result = run_cli(tmp_path, 'match', 'editorial.guansha_coexistence.v1', *args,
                    '--observation-scope', 'natal', '--export-context-json', str(matched), optimized=optimized)
  assert result.returncode == 0, result.stderr
  restored = ContextResult.from_json(matched.read_text(encoding='utf-8'))
  assert json.loads(restored.input_json)['civil_time'] == data['civil_time']
  assert json.loads(restored.input_json)['apparent_time'] == data['apparent_time']


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('precision', ['hour', 'minute'])
def test_negative_fixed_offset_equals_syntax(tmp_path: Path, optimized: bool, precision: str) -> None:
  args = ('--birth-time', '2024-01-02T01:00:00+00:00', '--gender', 'female',
          '--longitude', '-74', '--precision', precision, '--civil-timezone=-05:00')
  output = tmp_path / 'chart.json'
  result = run_cli(tmp_path, 'chart', *args, '--export-chart-json', str(output), optimized=optimized)
  assert result.returncode == 0, result.stderr
  chart = BaziChart.from_json(json.loads(output.read_text(encoding='utf-8')))
  data = cast(BaziJson.LocationBaziChartJsonDict, chart.json)
  assert data['civil_time'] == '2024-01-01T20:00:00-05:00'
  assert data['apparent_time'] == '2024-01-01T20:00:25.933333'
  matched = tmp_path / 'matching.json'
  result = run_cli(tmp_path, 'match', 'editorial.guansha_coexistence.v1', *args,
                    '--observation-scope', 'natal', '--export-context-json', str(matched), optimized=optimized)
  assert result.returncode == 0, result.stderr
  restored = ContextResult.from_json(matched.read_text(encoding='utf-8'))
  assert json.loads(restored.input_json)['civil_time'] == data['civil_time']


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('matching', [False, True])
@pytest.mark.parametrize('zone', ['America', 'Asia', 'Etc', 'Unknown/Region', '+99:00'])
def test_bad_civil_zone_is_an_argument_error(tmp_path: Path, optimized: bool, matching: bool, zone: str) -> None:
  args = ('--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'female', '--longitude', '-157.4',
          '--precision', 'minute', '--civil-timezone', zone)
  export = tmp_path / 'record.json'
  task = ('match', 'editorial.guansha_coexistence.v1') if matching else ('chart',)
  extra = ('--observation-scope', 'natal',
           '--export-context-json', str(export)) if matching else ('--export-chart-json', str(export))
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
  (('chart', '--export-chart-json', 'out.json'), 'require fixed birth input'),
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
def test_invalid_location_modes_fail_early(tmp_path: Path, optimized: bool, args: tuple[str, ...], error: str) -> None:
  result = run_cli(tmp_path, *args, optimized=optimized)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert_cli_error(result, args[0], error)
  assert 'Traceback' not in result.stderr
  assert list(tmp_path.iterdir()) == []
