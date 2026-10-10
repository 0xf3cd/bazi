# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

from run_interpreter import interpret, main, _object_text
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart, BaziJson
from bazi.defines import Shishen
from bazi.interpreter import Interpreter
from bazi.knowledge import KnowledgeBase
from bazi.context_matching import ContextProfile, ContextResult, evaluate_context
from bazi.school import BaziConfig


KNOWLEDGE_BASE = KnowledgeBase.load()

MATCH_ARGS = ('--match-context', 'editorial.guansha_coexistence.v1', '--birth-time', '2000-01-03 12:00', '--gender', 'female', '--observation-scope', 'natal')


def test_matching_cli_text_export_reload_and_library_agree(tmp_path: Path) -> None:
  output = tmp_path / 'match.json'
  result = _run_cli(tmp_path, *MATCH_ARGS, '--include-reference-only', '--export-context-json', str(output))
  assert result.returncode == 0, result.stderr
  expected = evaluate_context(BaziChart(Bazi.create('2000-01-03 12:00', 'female')), criterion_id='editorial.guansha_coexistence.v1', profile=ContextProfile('natal'), include_reference_only=True)
  assert output.read_text(encoding='utf-8') == expected.export_json()
  assert result.stdout == expected.render() + '\n' + f'已导出前提判别记录：{output}\n'
  assert ContextResult.from_json(output.read_text(encoding='utf-8')) == expected
  assert '也许' in result.stdout and '仅供参考' in result.stdout
  assert 'Does not establish a classical rule or real-world prediction.' in result.stdout


@pytest.mark.parametrize('scope,year,status', [
  ('natal', None, 'NOT_SATISFIED'), ('natal_and_liunian', None, 'UNKNOWN'),
  ('natal_and_liunian', '1998', 'UNKNOWN'), ('natal_and_liunian', '0', 'UNKNOWN'),
  ('natal_and_liunian', '-1', 'UNKNOWN'), ('natal_and_liunian', '2024', 'SATISFIED'),
])
def test_matching_cli_verdicts_and_reference_opt_in(tmp_path: Path, scope: str, year: str | None, status: str) -> None:
  args = ('--match-context', 'editorial.guansha_coexistence.v1', '--birth-time', '2000-01-01 12:00', '--gender', 'female', '--observation-scope', scope)
  result = _run_cli(tmp_path, *args, *(('--ganzhi-year', year) if year else ()))
  assert result.returncode == 0 and f'结构前提：{status}' in result.stdout
  assert '原作参考前提：' not in result.stdout and '也许' not in result.stdout
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('extra', [
  ('--seed', '42'), ('--count', '1'), ('--output-dir', 'out'), ('--export-knowledge-base',),
  ('--query-knowledge',), ('--validate-knowledge',), ('--export-knowledge-json', 'k.json'),
  ('--object', 'tiangan.ding'), ('--context', 'legacy.chart_context'), ('--topic', '取象'),
  ('--source', 'editorial'), ('--viewpoint', '仓内原作'), ('--applicability', 'described'), ('--time-scope', '行运'),
  ('--ganzhi-year', '2024'), ('--ganzhi-year', 'bad'),
])
def test_matching_cli_invalid_combinations_do_not_export(tmp_path: Path, extra: tuple[str, ...]) -> None:
  output = tmp_path / 'match.json'
  result = _run_cli(tmp_path, *MATCH_ARGS, *extra, '--export-context-json', str(output))
  assert result.returncode == 2 and 'error:' in result.stderr
  assert not output.exists()


@pytest.mark.parametrize('args', [
  ('--match-context', 'editorial.guansha_coexistence.v1'),
  ('--match-context', 'typo', '--birth-time', '2000-01-03 12:00', '--gender', 'female', '--observation-scope', 'natal'),
  ('--match-context', 'editorial.guansha_coexistence.v1', '--birth-time', 'bad', '--gender', 'female', '--observation-scope', 'natal'),
  ('--match-context', 'editorial.guansha_coexistence.v1', '--birth-time', '2000-01-03 12:00', '--gender', 'female'),
  ('--observation-scope', 'natal'), ('--ganzhi-year', '2024'), ('--export-context-json', 'out.json'),
])
def test_matching_cli_missing_and_bad_requests_fail(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = _run_cli(tmp_path, *args)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert list(tmp_path.iterdir()) == []


def test_matching_missing_knowledge_source_is_an_argparse_error(tmp_path: Path) -> None:
  output = tmp_path / 'match.json'
  result = _run_cli(tmp_path, *MATCH_ARGS, '--knowledge-source', str(tmp_path / 'missing.json'), '--export-context-json', str(output))
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'Traceback' not in result.stderr
  assert 'No such file or directory' in result.stderr
  assert not output.exists()


def test_matching_custom_source_unknown_binding_and_alias_guards(tmp_path: Path) -> None:
  data = json.loads(KNOWLEDGE_BASE.export_json())
  next(e for e in data['entries'] if e['claim_id'] == 'editorial.shishen.zhengguan.legal_trouble')['premise'] = '不同前提'
  source = tmp_path / 'edited.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  output = tmp_path / 'result.json'
  result = _run_cli(tmp_path, *MATCH_ARGS, '--include-reference-only', '--knowledge-source', str(source), '--export-context-json', str(output))
  assert result.returncode == 0 and 'binding_unrecognized' in result.stdout
  assert '不同前提' in result.stdout
  restored = ContextResult.from_json(output.read_text(encoding='utf-8'))
  assert restored.entries[0].status == 'UNKNOWN'
  aliases = [source, tmp_path / 'symlink.json', tmp_path / 'hardlink.json']
  aliases[1].symlink_to(source)
  aliases[2].hardlink_to(source)
  before = source.read_bytes()
  for alias in aliases:
    result = _run_cli(tmp_path, *MATCH_ARGS, '--knowledge-source', str(source), '--export-context-json', str(alias))
    assert result.returncode == 2 and 'overwrite' in result.stderr
    assert source.read_bytes() == before
  bundled = Path(__file__).parents[1] / 'bazi/knowledge_data.json'
  result = _run_cli(tmp_path, *MATCH_ARGS, '--export-context-json', str(bundled))
  assert result.returncode == 2 and 'overwrite' in result.stderr


def test_matching_export_io_error_and_undefined_text(tmp_path: Path) -> None:
  output = tmp_path / 'directory'
  output.mkdir()
  result = _run_cli(tmp_path, *MATCH_ARGS, '--export-context-json', str(output))
  assert result.returncode == 2 and 'error:' in result.stderr
  result = _run_cli(tmp_path, *MATCH_ARGS, '--match-context', 'tiangan.geng_regulated_transit', '--include-reference-only')
  assert result.returncode == 0 and 'UNKNOWN' in result.stdout
  for text in ('有制有化尚未定义，不据基础生克关系认定成立。', '后天有教养是盘外前提，不能从命盘查表还原。'):
    assert text in result.stdout


@pytest.mark.parametrize('include_reference_only', [False, True])
def test_chart_display_uses_knowledge_topics_and_retains_selection(include_reference_only: bool) -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  text = interpret(chart, include_reference_only=include_reference_only)
  assert '定义：' + Interpreter.interpret_tiangan(chart.bazi.day_master)['general'][0] in text
  assert '原局中，劫财有' in text
  assert '当劫财状态不好时' not in text
  assert '能量状态佳' not in text and 'in_good_status' not in text
  assert ('仅供参考' in text) is include_reference_only
  assert ('前提待梳理' in text) is include_reference_only


def test_empty_knowledge_projection_keeps_chart_counts(monkeypatch: pytest.MonkeyPatch) -> None:
  empty = KnowledgeBase.from_json(KNOWLEDGE_BASE.export_json(()))
  monkeypatch.setattr(KnowledgeBase, 'load', staticmethod(lambda path=None: empty))
  text = interpret(BaziChart(Bazi.create('2000-01-01 12:00', 'male')))
  assert '原局中，劫财有' in text
  assert '定义：' not in text and '仅供参考' not in text


def _run_cli(cwd: Path, *args: str, script: Path | None = None, optimized: bool = False) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, *(['-O'] if optimized else []), str(Path(__file__).parents[1] / 'run_interpreter.py' if script is None else script), *args],
    cwd=cwd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
  )


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('precision,pillars', [
  ('hour', ('庚辰', '戊寅')), ('minute', ('己卯', '丁丑')),
])
def test_legacy_naive_cli_precision_and_exports(tmp_path: Path, optimized: bool, precision: str, pillars: tuple[str, str]) -> None:
  birth = '2000-02-04T20:39:59.123456'
  config = BaziConfig.from_values(precision=precision)
  expected = BaziChart(Bazi.create(birth, 'female', config))
  output = tmp_path / 'legacy-chart.json'
  args = ('--birth-time', birth, '--gender', 'female', '--precision', precision)
  result = _run_cli(tmp_path, *args, '--export-chart-json', str(output), optimized=optimized)
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
  result = _run_cli(tmp_path, *args, '--match-context', 'editorial.guansha_coexistence.v1',
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
def test_location_chart_and_matching_cli_export_restore(tmp_path: Path, optimized: bool, precision: str, basis: str) -> None:
  output = tmp_path / 'chart.json'
  args = ('--birth-time', '2023-12-31T22:00:00+00:00', '--gender', 'female',
          '--longitude', '-157.4', '--precision', precision, '--civil-timezone', basis)
  result = _run_cli(tmp_path, *args, '--export-chart-json', str(output), optimized=optimized)
  assert result.returncode == 0, result.stderr
  chart = BaziChart.from_json(json.loads(output.read_text(encoding='utf-8')))
  data = cast(BaziJson.LocationBaziChartJsonDict, chart.json)
  assert data['civil_time'] == '2024-01-01T12:00:00+14:00'
  assert data['apparent_time'] == '2024-01-01T11:27:21.883333'
  assert '民用出生时刻' in result.stdout and '真太阳出生时刻' in result.stdout
  matched = tmp_path / 'matching.json'
  result = _run_cli(tmp_path, *args, '--match-context', 'editorial.guansha_coexistence.v1',
                    '--observation-scope', 'natal', '--export-context-json', str(matched), optimized=optimized)
  assert result.returncode == 0, result.stderr
  restored = ContextResult.from_json(matched.read_text(encoding='utf-8'))
  assert json.loads(restored.input_json)['civil_time'] == data['civil_time']
  assert json.loads(restored.input_json)['apparent_time'] == data['apparent_time']


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('precision', ['hour', 'minute'])
def test_negative_fixed_offset_equals_syntax_in_chart_and_matching(tmp_path: Path, optimized: bool, precision: str) -> None:
  args = ('--birth-time', '2024-01-02T01:00:00+00:00', '--gender', 'female',
          '--longitude', '-74', '--precision', precision, '--civil-timezone=-05:00')
  output = tmp_path / 'chart.json'
  result = _run_cli(tmp_path, *args, '--export-chart-json', str(output), optimized=optimized)
  assert result.returncode == 0, result.stderr
  chart = BaziChart.from_json(json.loads(output.read_text(encoding='utf-8')))
  data = cast(BaziJson.LocationBaziChartJsonDict, chart.json)
  assert data['civil_time'] == '2024-01-01T20:00:00-05:00'
  assert data['apparent_time'] == '2024-01-01T20:00:25.933333'
  matched = tmp_path / 'matching.json'
  result = _run_cli(tmp_path, *args, '--match-context', 'editorial.guansha_coexistence.v1',
                    '--observation-scope', 'natal', '--export-context-json', str(matched), optimized=optimized)
  assert result.returncode == 0, result.stderr
  restored = ContextResult.from_json(matched.read_text(encoding='utf-8'))
  assert json.loads(restored.input_json)['civil_time'] == data['civil_time']


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('matching', [False, True])
@pytest.mark.parametrize('zone', ['America', 'Asia', 'Etc', 'Unknown/Region', '+99:00'])
def test_bad_civil_zone_is_an_argument_error_without_exports(tmp_path: Path, optimized: bool, matching: bool, zone: str) -> None:
  args = ('--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'female', '--longitude', '-157.4',
          '--precision', 'minute', '--civil-timezone', zone)
  export = tmp_path / 'record.json'
  extra = ('--match-context', 'editorial.guansha_coexistence.v1', '--observation-scope', 'natal',
           '--export-context-json', str(export)) if matching else ('--export-chart-json', str(export))
  result = _run_cli(tmp_path, *args, *extra, optimized=optimized)
  assert result.returncode == 2
  assert 'error: argument --civil-timezone:' in result.stderr
  assert 'Traceback' not in result.stderr
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('optimized', [False, True])
def test_location_midnight_labels_in_display_and_txt(tmp_path: Path, optimized: bool) -> None:
  result = _run_cli(tmp_path, '--birth-time', '2024-06-01T23:50:00+08:00', '--gender', 'male',
                    '--longitude', '125', '--precision', 'minute', '--output-dir', str(tmp_path), optimized=optimized)
  assert result.returncode == 0, result.stderr
  assert '真太阳时日期：2024-06-02' in result.stdout
  assert '真太阳时（分钟显示）：2024-06-02T00:12:00' in result.stdout
  assert '民用出生时刻（固定出生地偏移）：2024-06-01T23:50:00+08:00' in result.stdout
  assert '生于 2024-06-02' not in result.stdout and '出生时间：2024-06-02' not in result.stdout
  saved = tmp_path / 'interpretation_examples/0.txt'
  assert saved.read_text(encoding='utf-8') == re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).removesuffix('\n')


def test_legacy_renderer_keeps_generic_birth_labels() -> None:
  from run_demo import get_basic_info
  chart = BaziChart(Bazi.create('2024-06-01T23:50:00', 'male', BaziConfig.from_values(precision='minute')))
  assert '生于 2024-06-01' in get_basic_info(chart)
  text = interpret(chart)
  assert text.startswith('出生时间：2024-06-01, 23:50\n')
  assert '真太阳时' not in text and '民用出生时刻' not in get_basic_info(chart)


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('args', [
  ('--longitude', '0'), ('--precision', 'hour'), ('--civil-timezone', '+14:00'), ('--export-chart-json', 'out.json'),
  ('--query-knowledge', '--longitude', '0'), ('--validate-knowledge', '--precision', 'minute'),
  ('--export-knowledge-json', 'out.json', '--civil-timezone', '+14:00'),
  ('--query-knowledge', '--export-chart-json', 'out.json'),
  ('--birth-time', '2024-01-01T12:00:00', '--gender', 'male', '--longitude', '0', '--precision', 'hour'),
  ('--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'male', '--longitude', '-157.4'),
  ('--birth-time', '2024-01-01T12:00:00', '--gender', 'male', '--civil-timezone', '+14:00'),
  ('--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'male', '--longitude', '-157.4', '--precision', 'minute', '--civil-timezone', 'Unknown/Region'),
  ('--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'male', '--longitude', '-157.4', '--precision', 'minute', '--civil-timezone', '+99:00'),
  (*MATCH_ARGS, '--longitude', '0'),
  (*MATCH_ARGS, '--civil-timezone', 'Unknown/Region'),
  (*MATCH_ARGS, '--export-chart-json', 'out.json'),
])
def test_location_cli_invalid_modes_fail_before_export(tmp_path: Path, optimized: bool, args: tuple[str, ...]) -> None:
  result = _run_cli(tmp_path, *args, optimized=optimized)
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'Traceback' not in result.stderr
  assert list(tmp_path.iterdir()) == []


def test_location_chart_export_cannot_overwrite_knowledge(tmp_path: Path) -> None:
  source = Path(__file__).parents[1] / 'bazi/knowledge_data.json'
  alias = tmp_path / 'alias.json'
  alias.symlink_to(source)
  before = source.read_bytes()
  result = _run_cli(tmp_path, '--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'male',
                    '--longitude', '-157.4', '--precision', 'minute', '--export-chart-json', str(alias))
  assert result.returncode == 2 and 'overwrite' in result.stderr
  assert source.read_bytes() == before


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('located', [False, True])
def test_chart_json_rejects_txt_output_collision_before_writes(tmp_path: Path, optimized: bool, located: bool) -> None:
  output = tmp_path / 'output'
  target = output / 'interpretation_examples' / '0.txt'
  birth = '2024-01-01T12:00:00+14:00' if located else '2024-01-01T12:00:00'
  location = ('--longitude', '-157.4') if located else ()
  result = _run_cli(tmp_path, '--birth-time', birth, '--gender', 'female', '--precision', 'minute',
                    *location, '--output-dir', str(output), '--export-chart-json', str(target), optimized=optimized)
  assert result.returncode == 2 and 'overlap generated TXT' in result.stderr
  assert '已导出命盘' not in result.stdout and not output.exists()


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('alias', ['direct', 'file-symlink', 'hardlink', 'directory-symlink'])
def test_chart_json_collision_preserves_existing_aliases(tmp_path: Path, optimized: bool, alias: str) -> None:
  output = tmp_path / 'output'
  txt = output / 'interpretation_examples' / '0.txt'
  txt.parent.mkdir(parents=True)
  txt.write_bytes(b'existing text must survive')
  target = txt
  if alias == 'file-symlink':
    target = tmp_path / 'chart.json'
    target.symlink_to(txt)
  elif alias == 'hardlink':
    target = tmp_path / 'chart.json'
    target.hardlink_to(txt)
  elif alias == 'directory-symlink':
    directory = tmp_path / 'output-alias'
    directory.symlink_to(output, target_is_directory=True)
    target = directory / 'interpretation_examples' / '0.txt'
  before = txt.read_bytes()
  result = _run_cli(tmp_path, '--birth-time', '2024-01-01T12:00:00+14:00', '--gender', 'female',
                    '--longitude', '-157.4', '--precision', 'minute', '--output-dir', str(output),
                    '--export-chart-json', str(target), optimized=optimized)
  assert result.returncode == 2 and 'overlap generated TXT' in result.stderr
  assert txt.read_bytes() == before and target.read_bytes() == before
  assert '已导出命盘' not in result.stdout


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('family,member', [('tiangan', '甲'), ('shishen', '比肩')])
def test_chart_json_rejects_knowledge_txt_collision(tmp_path: Path, optimized: bool, family: str, member: str) -> None:
  output = tmp_path / 'output'
  target = output / 'knowledge_base' / family / f'{member}.txt'
  result = _run_cli(tmp_path, '--birth-time', '2024-01-01T12:00:00', '--gender', 'female',
                    '--output-dir', str(output), '--export-knowledge-base',
                    '--export-chart-json', str(target), optimized=optimized)
  assert result.returncode == 2 and 'overlap generated TXT' in result.stderr
  assert not output.exists() and '已导出命盘' not in result.stdout


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('family,member', [('tiangan', '甲'), ('shishen', '比肩')])
def test_default_knowledge_txt_collision_uses_a_disposable_checkout(
  knowledge_checkout: Path, optimized: bool, family: str, member: str,
) -> None:
  output = knowledge_checkout / 'output_data'
  target = output / 'knowledge_base' / family / f'{member}.txt'
  result = _run_cli(knowledge_checkout, '--birth-time', '2024-01-01T12:00:00', '--gender', 'female',
                    '--export-knowledge-base', '--export-chart-json', str(target),
                    optimized=optimized, script=knowledge_checkout / 'run_interpreter.py')
  assert result.returncode == 2 and 'overlap generated TXT' in result.stderr
  assert not output.exists() and '已导出命盘' not in result.stdout


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('located', [False, True])
def test_distinct_chart_json_and_txt_outputs_are_both_retained(tmp_path: Path, optimized: bool, located: bool) -> None:
  output = tmp_path / 'output'
  target = output / 'chart.json'
  birth = '2024-01-01T12:00:00+14:00' if located else '2024-01-01T12:00:00'
  location = ('--longitude', '-157.4') if located else ()
  result = _run_cli(tmp_path, '--birth-time', birth, '--gender', 'female', '--precision', 'minute',
                    *location, '--output-dir', str(output), '--export-chart-json', str(target), optimized=optimized)
  assert result.returncode == 0, result.stderr
  data = json.loads(target.read_text(encoding='utf-8'))
  assert BaziChart.from_json(data).json == data
  text = (output / 'interpretation_examples' / '0.txt').read_text(encoding='utf-8')
  displayed = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).split('已导出命盘：', 1)[0].removesuffix('\n')
  assert text == displayed and '已导出命盘' not in text


@pytest.mark.parametrize('columns', ['50', '80'])
@pytest.mark.parametrize('optimized', [False, True])
def test_cli_help_and_seeded_default_are_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, columns: str, optimized: bool) -> None:
  monkeypatch.setenv('COLUMNS', columns)
  help_result = _run_cli(tmp_path, '--help', optimized=optimized)
  assert help_result.returncode == 0
  assert '--show-sources' in help_result.stdout
  assert '--civil-timezone=-05:00' in re.sub(r'\n\s*', '', help_result.stdout)
  first = _run_cli(tmp_path, '--seed', '42', optimized=optimized)
  second = _run_cli(tmp_path, '--seed', '42', optimized=optimized)
  assert first.returncode == second.returncode == 0
  assert first.stdout == second.stdout
  assert first.stdout.count('出生时间：') == 1
  assert '来源：' not in first.stdout
  assert list(tmp_path.iterdir()) == []


def test_cli_source_display_does_not_expand_reference_selection(tmp_path: Path) -> None:
  result = _run_cli(
    tmp_path, '--birth-time', '2000-01-01 12:00', '--gender', 'male', '--show-sources',
  )
  assert result.returncode == 0
  assert '出生时间：2000-01-01, 12:0' in result.stdout
  assert '来源：' in result.stdout
  assert '支持范围：' in result.stdout
  assert '局限：' in result.stdout
  assert '条目：tiangan.wu.definition；署名：《渊海子平》与《命理探源》天干定义' in result.stdout
  assert '仅供参考' not in result.stdout
  assert 'legacy.' not in result.stdout


@pytest.mark.parametrize('chart_args', [
  ('--birth-time', '2000-01-01 12:00', '--gender', 'male'),
  ('--seed', '42'),
])
def test_cli_reference_export_retains_unverified_and_unevaluated_states(tmp_path: Path, chart_args: tuple[str, ...]) -> None:
  result = _run_cli(
    tmp_path,
    *chart_args,
    '--include-reference-only', '--show-sources',
    '--output-dir', str(tmp_path), '--export-knowledge-base',
  )
  assert result.returncode == 0
  assert '来源尚未核实' in result.stdout
  assert '命盘适用性未判断' in result.stdout
  assert '仅供参考' in result.stdout
  saved = tmp_path / 'interpretation_examples' / '0.txt'
  assert saved.read_text(encoding='utf-8') == re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).removesuffix('\n')
  assert len(list((tmp_path / 'knowledge_base' / 'tiangan').glob('*.txt'))) == 10
  assert len(list((tmp_path / 'knowledge_base' / 'shishen').glob('*.txt'))) == 10
  ding = (tmp_path / 'knowledge_base' / 'tiangan' / '丁.txt').read_text(encoding='utf-8')
  assert '丁火有烛灯之象' in ding
  assert '《刻京台增补渊海子平大全》' in ding
  for path in (tmp_path / 'knowledge_base' / 'shishen').glob('*.txt'):
    text = path.read_text(encoding='utf-8')
    assert text.startswith(f'{path.stem}知识条目：\n')
    assert '能量状态佳时所代表的特点' not in text
    assert '能量状态不佳时所代表的特点' not in text


def test_cli_exports_exact_displayed_chart_count(tmp_path: Path) -> None:
  result = _run_cli(tmp_path, '--seed', '42', '--count', '2', '--output-dir', str(tmp_path))
  assert result.returncode == 0
  assert result.stdout.count('出生时间：') == 2
  assert {p.name for p in (tmp_path / 'interpretation_examples').iterdir()} == {'0.txt', '1.txt'}
  assert not (tmp_path / 'knowledge_base').exists()


@pytest.mark.parametrize('args', [
  ('--birth-time', '2000-01-01 12:00'),
  ('--gender', 'male'),
  ('--gender', 'other'),
  ('--count', '0'),
  ('--count', '-1'),
  ('--count', 'invalid'),
  ('--birth-time', 'invalid', '--gender', 'male'),
  ('--birth-time', '2000-01-01 12:00', '--gender', 'male', '--seed', '42'),
  ('--birth-time', '2000-01-01 12:00', '--gender', 'male', '--count', '2'),
  ('--unknown',),
])
def test_cli_rejects_invalid_inputs_without_exports(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = _run_cli(tmp_path, *args)
  assert result.returncode == 2
  assert 'error:' in result.stderr
  assert not result.stdout
  assert list(tmp_path.iterdir()) == []


def test_source_and_reference_rendering_are_independent() -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  text = interpret(chart, include_reference_only=True)
  assert '仅供参考' in text
  assert '命盘适用性未判断' in text
  assert '来源尚未核实' in text
  assert '来源：' not in text


def _run_guarded_script(
  script: Path,
  cwd: Path,
  args: tuple[str, ...],
) -> subprocess.CompletedProcess[str]:
  guard = '''
import os
import runpy
import sys
from pathlib import Path

script = sys.argv[1]
sys.path.insert(0, str(Path(script).parent))
sys.argv = sys.argv[1:]

def deny_writes(event, args):
  if event == 'open':
    _, mode, flags = args
    # PyPy FileIO reports closefd rather than OS flags when a mode is present.
    writable = (
      any(char in mode for char in 'wax+')
      if mode is not None
      else bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
    )
    if writable:
      raise PermissionError('Unexpected default file export')
  if event in ('os.mkdir', 'os.remove', 'os.rename', 'os.rmdir', 'os.truncate'):
    raise PermissionError('Unexpected default filesystem change')

sys.addaudithook(deny_writes)
runpy.run_path(script, run_name='__main__')
'''
  return subprocess.run(
    [sys.executable, '-B', '-c', guard, str(script), *args],
    cwd=cwd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
  )


@pytest.mark.parametrize(('args', 'writes'), [
  ((), False),
  (('--seed', '42'), False),
  (('--output-dir', 'exported'), True),
  (('--export-knowledge-base',), True),
])
def test_default_cli_rejects_all_filesystem_writes(
  tmp_path: Path,
  args: tuple[str, ...],
  writes: bool,
) -> None:
  result = _run_guarded_script(
    Path(__file__).parents[1] / 'run_interpreter.py',
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
def test_write_guard_checks_high_level_modes_without_directory_operations(
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
  result = _run_guarded_script(script, tmp_path, ())
  assert result.returncode != 0
  assert 'Unexpected default file export' in result.stderr
  assert target.read_text(encoding='utf-8') == 'existing data'


def test_reference_claims_have_distinct_lines_without_source_blocks() -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  result = interpret(chart, include_reference_only=True)
  general = Interpreter.query_tiangan(chart.bazi.day_master, include_reference_only=True)['general']
  assert len(general) > 1
  lines = result.splitlines()
  assert f'定义：{general[0].text}' in lines
  assert any(general[1].text in line and '仅供参考' in line for line in lines)
  assert '来源：' not in result


def test_exports_retain_other_existing_files(tmp_path: Path) -> None:
  first = _run_cli(tmp_path, '--seed', '42', '--count', '2', '--output-dir', str(tmp_path))
  assert first.returncode == 0
  output = tmp_path / 'interpretation_examples'
  earlier = (output / '1.txt').read_bytes()
  (output / '0.txt').write_text('sentinel', encoding='utf-8')
  (output / 'notes.txt').write_text('personal notes', encoding='utf-8')
  second = _run_cli(tmp_path, '--seed', '42', '--output-dir', str(tmp_path))
  assert second.returncode == 0
  assert (output / '0.txt').read_text(encoding='utf-8') == re.sub(
    r'\x1b\[[0-9;]*m', '', second.stdout,
  ).removesuffix('\n')
  assert (output / '1.txt').read_bytes() == earlier
  assert (output / 'notes.txt').read_text(encoding='utf-8') == 'personal notes'


def test_bad_export_path_uses_cli_error_exit(tmp_path: Path) -> None:
  output = tmp_path / 'file'
  output.write_text('existing data', encoding='utf-8')
  result = _run_cli(tmp_path, '--seed', '42', '--output-dir', str(output))
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


def test_cli_reference_only_without_source_display(tmp_path: Path) -> None:
  result = _run_cli(
    tmp_path,
    '--birth-time', '2000-01-01 12:00', '--gender', 'female', '--include-reference-only',
  )
  assert result.returncode == 0
  assert result.stdout.count('出生时间：') == 1
  assert '性别：female' in result.stdout
  assert '仅供参考' in result.stdout
  assert '命盘适用性未判断' in result.stdout
  assert '来源尚未核实' in result.stdout
  assert '来源：' not in result.stdout
  assert '条目：' not in result.stdout
  assert list(tmp_path.iterdir()) == []


def test_knowledge_export_defaults_are_isolated(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  monkeypatch.setitem(main.__globals__, '_DEFAULT_OUTPUT_DIR', tmp_path)
  assert main([
    '--birth-time', '2000-01-01 12:00', '--gender', 'male', '--export-knowledge-base',
  ]) == 0
  assert not (tmp_path / 'interpretation_examples').exists()
  assert len(list((tmp_path / 'knowledge_base' / 'tiangan').glob('*.txt'))) == 10
  assert len(list((tmp_path / 'knowledge_base' / 'shishen').glob('*.txt'))) == 10
  ding = (tmp_path / 'knowledge_base' / 'tiangan' / '丁.txt').read_text(encoding='utf-8')
  assert '丁为阴火。' in ding
  assert '丁火有烛灯之象' not in ding
  assert '仅供参考' not in ding
  assert '来源：' not in ding


def test_print_errors_propagate(monkeypatch: pytest.MonkeyPatch) -> None:
  error = BrokenPipeError('Print failure')

  def fail(*args: object, **kwargs: object) -> None:
    raise error

  monkeypatch.setitem(main.__globals__, 'print', fail)
  with pytest.raises(BrokenPipeError) as caught:
    main(['--birth-time', '2000-01-01 12:00', '--gender', 'male'])
  assert caught.value is error


def test_batch_generation_is_interleaved_with_rendering(
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  events: list[str] = []
  bazi = Bazi.create('2000-01-01 12:00', 'male')

  def generate() -> Bazi:
    events.append('generate')
    return bazi

  def render(chart: BaziChart, **kwargs: object) -> str:
    events.append('render')
    return 'chart'

  monkeypatch.setattr(Bazi, 'random', staticmethod(generate))
  monkeypatch.setitem(main.__globals__, '_chart_text', render)
  assert main(['--count', '3']) == 0
  assert events == ['generate', 'render', 'generate', 'render', 'generate', 'render']
  assert capsys.readouterr().out == 'chart\nchart\nchart\n'


def test_knowledge_query_runs_without_birth_input_or_filesystem_writes(tmp_path: Path) -> None:
  result = _run_cli(
    tmp_path, '--query-knowledge', '--object', 'tiangan.ding', '--topic', '历史象',
    '--source', 'yuanhai_ziping_stem_symbols_p70', '--include-reference-only',
  )
  assert result.returncode == 0, result.stderr
  assert 'tiangan.ding.lamp_symbol' in result.stdout
  assert '丁火有烛灯之象。' in result.stdout and 'p. 70' in result.stdout
  assert '支持范围：' in result.stdout and '局限：' in result.stdout
  assert '出生时间：' not in result.stdout
  assert '丁为阴火。' not in result.stdout
  assert list(tmp_path.iterdir()) == []
  guarded = _run_guarded_script(
    Path(__file__).parents[1] / 'run_interpreter.py', tmp_path,
    ('--query-knowledge', '--object', 'tiangan.ding'),
  )
  assert guarded.returncode == 0, guarded.stderr


def test_manual_context_preserves_undefined_and_external_premises(tmp_path: Path) -> None:
  result = _run_cli(
    tmp_path, '--query-knowledge', '--object', 'tiangan.geng',
    '--context', 'tiangan.geng_regulated_transit', '--topic', '性格',
    '--applicability', 'described', '--time-scope', '行运', '--include-reference-only',
  )
  assert result.returncode == 0, result.stderr
  for text in ('人工给定情境', '命盘适用性未判断', '后天有教养', '盘外前提', '有制有化尚未定义', '来源尚未核实'):
    assert text in result.stdout
  assert '出生时间：' not in result.stdout


def test_knowledge_default_and_known_empty_queries(tmp_path: Path) -> None:
  default = _run_cli(tmp_path, '--query-knowledge', '--object', 'tiangan.ding')
  assert default.returncode == 0
  assert '丁为阴火。' in default.stdout and '烛灯' not in default.stdout
  empty = _run_cli(tmp_path, '--query-knowledge', '--object', 'wuxing.mu')
  assert empty.returncode == 0 and empty.stdout == '无匹配条目。\n'
  variant = _run_cli(
    tmp_path, '--query-knowledge', '--object', 'shensha.guoyin',
    '--viewpoint', 'WUXING_JINGJI', '--include-reference-only',
  )
  assert variant.returncode == 0 and '#194' in variant.stdout
  assert 'shensha.guoyin.modern' not in variant.stdout


def test_knowledge_edit_validate_export_reload_cycle(tmp_path: Path) -> None:
  data = json.loads(KNOWLEDGE_BASE.export_json())
  record = next(entry for entry in data['entries'] if entry['claim_id'] == 'tiangan.ding.lamp_symbol')
  record['limits'] = ['本次编辑的限度。']
  source, exported, complete = (tmp_path / name for name in ('source.json', 'selection.json', 'complete.json'))
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  query = _run_cli(
    tmp_path, '--knowledge-source', str(source), '--validate-knowledge', '--query-knowledge',
    '--object', 'tiangan.ding', '--topic', '历史象', '--include-reference-only',
    '--export-knowledge-json', str(exported),
  )
  assert query.returncode == 0, query.stderr
  assert '校验通过：295 条目，9 来源见证，7 情境。' in query.stdout
  assert '本次编辑的限度。' in query.stdout
  restored = KnowledgeBase.load(exported)
  assert tuple(restored.entries) == ('tiangan.ding.lamp_symbol',)
  assert restored.sources == KNOWLEDGE_BASE.sources
  again = _run_cli(tmp_path, '--query-knowledge', '--knowledge-source', str(exported), '--include-reference-only')
  assert again.returncode == 0 and '本次编辑的限度。' in again.stdout and 'p. 70' in again.stdout
  full = _run_cli(tmp_path, '--export-knowledge-json', str(complete))
  assert full.returncode == 0 and '出生时间：' not in full.stdout
  assert KnowledgeBase.load(complete).entries == KNOWLEDGE_BASE.entries


@pytest.mark.parametrize('args', [
  ('--query-knowledge', '--birth-time', '2000-01-01 12:00', '--gender', 'male'),
  ('--validate-knowledge', '--birth-time', ''),
  ('--query-knowledge', '--seed', '42'), ('--query-knowledge', '--count', '1'),
  ('--validate-knowledge', '--export-knowledge-base'), ('--query-knowledge', '--output-dir', 'output'),
  ('--object', 'tiangan.ding'), ('--knowledge-source', 'source.json'),
  ('--validate-knowledge', '--topic', '历史象'), ('--query-knowledge', '--object', 'typo'),
  ('--query-knowledge', '--context', 'typo'), ('--query-knowledge', '--applicability', 'typo'),
  ('--validate-knowledge', '--knowledge-source', 'missing.json'),
])
def test_knowledge_bad_inputs_do_not_create_exports(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = _run_cli(tmp_path, *args)
  assert result.returncode == 2
  assert 'error:' in result.stderr and 'Traceback' not in result.stderr
  assert list(tmp_path.iterdir()) == []


def test_knowledge_validation_rejects_corrupt_source_before_export(tmp_path: Path) -> None:
  source = tmp_path / 'corrupt.json'
  source.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
  result = _run_cli(tmp_path, '--validate-knowledge', '--knowledge-source', str(source), '--export-knowledge-json', str(tmp_path / 'out.json'))
  assert result.returncode == 2 and 'Duplicate JSON key' in result.stderr
  assert not (tmp_path / 'out.json').exists()


@pytest.fixture
def knowledge_checkout(tmp_path: Path) -> Path:
  root = Path(__file__).parents[1]
  shutil.copytree(root / 'bazi', tmp_path / 'bazi', ignore=shutil.ignore_patterns('__pycache__'))
  for name in ('run_interpreter.py', 'run_demo.py'):
    shutil.copyfile(root / name, tmp_path / name)
  return tmp_path


def test_validation_reads_corrupt_bundled_source_in_a_fresh_process(knowledge_checkout: Path) -> None:
  corpus = knowledge_checkout / 'bazi/knowledge_data.json'
  custom = knowledge_checkout / 'custom.json'
  custom.write_bytes(corpus.read_bytes())
  corpus.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
  script = knowledge_checkout / 'run_interpreter.py'
  invalid = _run_cli(knowledge_checkout, '--validate-knowledge', script=script)
  assert invalid.returncode == 2
  assert 'Duplicate JSON key' in invalid.stderr and 'Traceback' not in invalid.stderr
  valid = _run_cli(knowledge_checkout, '--validate-knowledge', '--knowledge-source', str(custom), script=script)
  assert valid.returncode == 0 and '校验通过：' in valid.stdout
  corpus.unlink()
  exported = knowledge_checkout / 'output.json'
  exported.write_text('old output', encoding='utf-8')
  independent = _run_cli(
    knowledge_checkout, '--knowledge-source', str(custom), '--export-knowledge-json', str(exported), script=script,
  )
  assert independent.returncode == 0, independent.stderr
  assert KnowledgeBase.load(exported).entries == KNOWLEDGE_BASE.entries


@pytest.mark.parametrize('mutation', ['new-source', 'zhushi', 'removed-unused-source'])
def test_modern_knowledge_loading_is_independent_of_legacy_projection(
  knowledge_checkout: Path,
  mutation: str,
) -> None:
  corpus = knowledge_checkout / 'bazi/knowledge_data.json'
  data = json.loads(corpus.read_text(encoding='utf-8'))
  if mutation == 'new-source':
    witness = dict(data['sources'][1])
    witness.update(source_id='independent_probe', lineage='independent_probe')
    data['sources'].append(witness)
    next(entry for entry in data['entries'] if entry['claim_id'] == 'tiangan.ding.lamp_symbol')['sources'].append('independent_probe')
  elif mutation == 'zhushi':
    data['sources'][1]['text_layer'] = 'zhushi'
  else:
    data['sources'] = [source for source in data['sources'] if source['source_id'] != 'yuanhai_ziping_stem_table']
  corpus.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  result = _run_cli(knowledge_checkout, '--validate-knowledge', script=knowledge_checkout / 'run_interpreter.py')
  assert result.returncode == 0 and '校验通过：' in result.stdout
  imported = subprocess.run(
    [sys.executable, '-B', '-c', 'import bazi, sys; assert "bazi.descriptions" not in sys.modules; from bazi.knowledge import KnowledgeBase; KnowledgeBase.load()'],
    cwd=knowledge_checkout, capture_output=True, text=True, encoding='utf-8', check=False,
  )
  assert imported.returncode == 0, imported.stderr


@pytest.mark.parametrize('alias', ['direct', 'hardlink', 'symlink'])
def test_custom_knowledge_export_cannot_overwrite_bundled_source(
  knowledge_checkout: Path,
  alias: str,
) -> None:
  corpus = knowledge_checkout / 'bazi/knowledge_data.json'
  custom = knowledge_checkout / 'custom.json'
  custom.write_bytes(corpus.read_bytes())
  target = corpus
  if alias != 'direct':
    target = knowledge_checkout / 'alias.json'
    if alias == 'hardlink':
      target.hardlink_to(corpus)
    else:
      try:
        target.symlink_to(corpus)
      except OSError:
        pytest.skip('Symbolic links unavailable')
  before = corpus.read_bytes()
  result = _run_cli(
    knowledge_checkout, '--knowledge-source', str(custom), '--export-knowledge-json', str(target),
    script=knowledge_checkout / 'run_interpreter.py',
  )
  assert result.returncode == 2 and 'overwrite the editing source' in result.stderr
  assert corpus.read_bytes() == before


def test_object_text_keeps_legacy_subject_while_queries_include_other_roles() -> None:
  relation = KNOWLEDGE_BASE.entry('legacy.shishen.SH-052')
  assert relation in KNOWLEDGE_BASE.query(object_id='shishen.qisha', include_reference_only=True)
  assert relation.text not in _object_text(KNOWLEDGE_BASE, Shishen.七杀, True, False)
  assert relation.text in _object_text(KNOWLEDGE_BASE, Shishen.食神, True, False)


def test_knowledge_export_cannot_truncate_its_editing_source(tmp_path: Path) -> None:
  source = tmp_path / 'source.json'
  source.write_text(KNOWLEDGE_BASE.export_json(), encoding='utf-8')
  before = source.read_bytes()
  for target in (source, tmp_path / 'hardlink.json'):
    if target != source:
      target.hardlink_to(source)
    result = _run_cli(
      tmp_path, '--knowledge-source', str(source), '--query-knowledge', '--object', 'tiangan.ding',
      '--export-knowledge-json', str(target),
    )
    assert result.returncode == 2 and 'overwrite the editing source' in result.stderr
    assert source.read_bytes() == before


def test_knowledge_export_io_error_uses_cli_error_exit(tmp_path: Path) -> None:
  blocker = tmp_path / 'file'
  blocker.write_text('existing', encoding='utf-8')
  result = _run_cli(tmp_path, '--export-knowledge-json', str(blocker / 'out.json'))
  assert result.returncode == 2 and 'error:' in result.stderr
  assert 'Traceback' not in result.stderr and blocker.read_text(encoding='utf-8') == 'existing'
