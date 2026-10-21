# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
from pathlib import Path

import pytest

from run_interpreter import interpret
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.knowledge import KnowledgeBase, object_id

from cli_runner import KNOWLEDGE_BASE, run_cli, assert_cli_error


@pytest.mark.parametrize('include_reference_only', [False, True])
def test_chart_display_uses_knowledge_topics(include_reference_only: bool) -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  text = interpret(chart, include_reference_only=include_reference_only)
  assert '定义：' + KNOWLEDGE_BASE.query(object_id=object_id(chart.bazi.day_master))[0].text in text
  assert '原局中，劫财有' in text
  assert '当劫财状态不好时' not in text
  assert '能量状态佳' not in text and 'in_good_status' not in text
  assert ('仅供参考' in text) is include_reference_only
  assert ('前提待梳理' in text) is include_reference_only


def test_empty_projection_keeps_chart_counts(monkeypatch: pytest.MonkeyPatch) -> None:
  empty = KnowledgeBase.from_json(KNOWLEDGE_BASE.export_json(()))
  monkeypatch.setattr(KnowledgeBase, 'load', staticmethod(lambda path=None: empty))
  text = interpret(BaziChart(Bazi.create('2000-01-01 12:00', 'male')))
  assert '原局中，劫财有' in text
  assert '定义：' not in text and '仅供参考' not in text


@pytest.mark.parametrize('flag', ['-h', '--help'])
def test_chart_help_with_input_is_read_only(tmp_path: Path, flag: str) -> None:
  result = run_cli(tmp_path, 'chart', '--seed', '1', flag)
  assert result.returncode == 0 and '--seed' in result.stdout and '--query-knowledge' not in result.stdout
  assert list(tmp_path.iterdir()) == []


@pytest.fixture
def terminal_columns(monkeypatch: pytest.MonkeyPatch, columns: str) -> None:
  monkeypatch.setenv('COLUMNS', columns)


@pytest.mark.usefixtures('terminal_columns')
@pytest.mark.parametrize('columns', ['50', '80'])
@pytest.mark.parametrize('optimized', [False, True])
def test_help_is_read_only(tmp_path: Path, columns: str, optimized: bool) -> None:
  help_result = run_cli(tmp_path, 'chart', '--seed', '1', '--help', optimized=optimized)
  assert help_result.returncode == 0
  assert '--show-sources' in help_result.stdout
  assert '--civil-timezone=-05:00' in re.sub(r'\n\s*', '', help_result.stdout)
  match_help = run_cli(tmp_path, 'match', '--help', optimized=optimized)
  assert match_help.returncode == 0
  for phrase in ('--observation-scope', '--ganzhi-year', '--transit-entry', '--transit-kinds'):
    assert phrase in match_help.stdout
  assert list(tmp_path.iterdir()) == []


@pytest.mark.usefixtures('terminal_columns')
@pytest.mark.parametrize('columns', ['50', '80'])
@pytest.mark.parametrize('optimized', [False, True])
def test_seeded_default_is_read_only(tmp_path: Path, columns: str, optimized: bool) -> None:
  first = run_cli(tmp_path, 'chart', '--seed', '42', optimized=optimized)
  second = run_cli(tmp_path, 'chart', '--seed', '42', optimized=optimized)
  assert first.returncode == second.returncode == 0
  assert first.stdout == second.stdout
  assert first.stdout.count('出生时间：') == 1
  assert '来源：' not in first.stdout
  assert list(tmp_path.iterdir()) == []


def test_source_display_keeps_reference_selection(tmp_path: Path) -> None:
  result = run_cli(
    tmp_path, 'chart', '--birth-time', '2000-01-01 12:00', '--gender', 'male', '--show-sources',
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
def test_reference_export_keeps_unverified(tmp_path: Path, chart_args: tuple[str, ...]) -> None:
  result = run_cli(
    tmp_path, 'chart',
    *chart_args,
    '--include-reference-only', '--show-sources',
    '--output-dir', str(tmp_path),
  )
  assert result.returncode == 0
  assert '来源尚未核实' in result.stdout
  assert '命盘适用性未判断' in result.stdout
  assert '仅供参考' in result.stdout
  saved = tmp_path / 'interpretation_examples' / '0.txt'
  displayed = result.stdout
  if chart_args[0] == '--seed':
    assert displayed.startswith('random seed: 42\n')
    displayed = displayed.removeprefix('random seed: 42\n')
  assert saved.read_text(encoding='utf-8') == re.sub(r'\x1b\[[0-9;]*m', '', displayed).removesuffix('\n')
  knowledge = run_cli(tmp_path, 'knowledge', '--export-knowledge-base', '--output-dir', str(tmp_path),
                      '--include-reference-only', '--show-sources')
  assert knowledge.returncode == 0 and knowledge.stdout == '' and knowledge.stderr == ''
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
  result = run_cli(tmp_path, 'chart', '--seed', '42', '--count', '2', '--output-dir', str(tmp_path))
  assert result.returncode == 0
  assert result.stdout.count('出生时间：') == 2
  assert {p.name for p in (tmp_path / 'interpretation_examples').iterdir()} == {'0.txt', '1.txt'}
  assert not (tmp_path / 'knowledge_base').exists()


@pytest.mark.parametrize('args,error', [
  (('--birth-time', '2000-01-01 12:00'), '--birth-time and --gender must be supplied together'),
  (('--gender', 'male'), '--birth-time and --gender must be supplied together'),
  (('--gender', 'other'), 'invalid choice'),
  (('--count', '0'), '--count must be positive'),
  (('--count', '-1'), '--count must be positive'),
  (('--count', 'invalid'), 'invalid int value'),
  (('--birth-time', 'invalid', '--gender', 'male'), 'Invalid isoformat string'),
  (('--birth-time', '2000-01-01 12:00', '--gender', 'male', '--seed', '42'), 'require random input'),
  (('--birth-time', '2000-01-01 12:00', '--gender', 'male', '--count', '2'), 'require random input'),
  (('--unknown',), 'unrecognized arguments'),
])
def test_invalid_inputs_export_nothing(tmp_path: Path, args: tuple[str, ...], error: str) -> None:
  result = run_cli(tmp_path, 'chart', *args)
  assert_cli_error(result, 'chart', error)
  assert not result.stdout
  assert list(tmp_path.iterdir()) == []


def test_source_reference_rendering_independent() -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  text = interpret(chart, include_reference_only=True)
  assert '仅供参考' in text
  assert '命盘适用性未判断' in text
  assert '来源尚未核实' in text
  assert '来源：' not in text


def test_reference_claims_get_distinct_lines() -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  result = interpret(chart, include_reference_only=True)
  general = tuple(
    entry for entry in KNOWLEDGE_BASE.query(object_id=object_id(chart.bazi.day_master), include_reference_only=True)
    if entry.legacy is not None and entry.legacy.field == 'general'
  )
  assert len(general) > 1
  lines = result.splitlines()
  assert f'定义：{general[0].text}' in lines
  assert any(general[1].text in line and '仅供参考' in line for line in lines)
  assert '来源：' not in result


def test_reference_only_without_source_display(tmp_path: Path) -> None:
  result = run_cli(
    tmp_path, 'chart',
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
