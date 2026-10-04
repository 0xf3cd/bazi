# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
import subprocess
import sys
from pathlib import Path

import pytest

from run_interpreter import interpret, save_chart_examples
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Shishen, Tiangan
from bazi.descriptions import ShishenDescription, TianganDescription
from bazi.interpreter import Interpreter


def _assert_headings(
  section: str,
  headings: tuple[tuple[str, list[str]], ...],
) -> None:
  for heading, descriptions in headings:
    assert (heading + ''.join(descriptions) in section) is bool(descriptions)
  present_headings = tuple(heading for heading, descriptions in headings if descriptions)
  positions = tuple(section.index(heading) for heading in present_headings)
  assert positions == tuple(sorted(positions))


def _shishen_from_section(section: str) -> Shishen:
  matching_shishens = tuple(
    shishen for shishen in Shishen
    if section.startswith(f'原局中，{shishen}有')
  )
  assert len(matching_shishens) == 1
  return matching_shishens[0]


@pytest.mark.parametrize(('tiangan_fields', 'shishen_fields'), [
  (
    {'general': ['日主解读。'], 'personality': []},
    {
      'general': [],
      'in_good_status': ['状态良好。'],
      'in_bad_status': [],
      'relationship': ['关系描述。'],
    },
  ),
  (
    {'general': [], 'personality': ['日主个性。']},
    {
      'general': ['十神解读。'],
      'in_good_status': [],
      'in_bad_status': ['状态不好。'],
      'relationship': [],
    },
  ),
  (
    {'general': ['日主解读。'], 'personality': ['日主个性。']},
    {
      'general': ['十神解读。'],
      'in_good_status': ['状态良好。'],
      'in_bad_status': ['状态不好。'],
      'relationship': ['关系描述。'],
    },
  ),
  (
    {'general': [], 'personality': []},
    {
      'general': ['十神解读。'],
      'in_good_status': ['状态良好。'],
      'in_bad_status': [],
      'relationship': [],
    },
  ),
  (
    {'general': [], 'personality': []},
    {
      'general': [],
      'in_good_status': [],
      'in_bad_status': [],
      'relationship': [],
    },
  ),
], ids=['alternating-a', 'alternating-b', 'all-content', 'leading-content', 'all-empty'])
def test_interpret_description_headings_follow_content(
  tiangan_fields: TianganDescription,
  shishen_fields: ShishenDescription,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))

  def tiangan_description(_: Tiangan) -> TianganDescription:
    return tiangan_fields

  def shishen_description(_: Shishen) -> ShishenDescription:
    return shishen_fields

  monkeypatch.setattr(
    Interpreter,
    'interpret_tiangan',
    staticmethod(tiangan_description),
  )
  monkeypatch.setattr(
    Interpreter,
    'interpret_shishen',
    staticmethod(shishen_description),
  )

  sections = interpret(chart).split('\n' + '-' * 60 + '\n')
  assert len(sections) > 3
  _, _, day_master_section, *shishen_sections = sections

  day_master_headings = (
    ('解读：', tiangan_fields['general']),
    ('日主的个性：', tiangan_fields['personality']),
  )
  _assert_headings(day_master_section, day_master_headings)

  for section in shishen_sections:
    shishen = _shishen_from_section(section)
    shishen_headings = (
      ('解读：', shishen_fields['general']),
      (f'{shishen}代表的特点：', shishen_fields['in_good_status']),
      (f'当{shishen}状态不好时，可能会有以下特点：', shishen_fields['in_bad_status']),
      (f'{shishen}的恋爱/交友观：', shishen_fields['relationship']),
    )
    _assert_headings(section, shishen_headings)


def test_interpret_real_descriptions_follow_content() -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  sections = interpret(chart).split('\n' + '-' * 60 + '\n')
  assert len(sections) > 3
  _, _, day_master_section, *shishen_sections = sections

  day_master_description = Interpreter.interpret_tiangan(chart.bazi.day_master)
  day_master_headings = (
    ('解读：', day_master_description['general']),
    ('日主的个性：', day_master_description['personality']),
  )
  _assert_headings(day_master_section, day_master_headings)

  rendered_shishens: set[Shishen] = set()
  for section in shishen_sections:
    shishen = _shishen_from_section(section)
    rendered_shishens.add(shishen)
    description = Interpreter.interpret_shishen(shishen)
    shishen_headings = (
      ('解读：', description['general']),
      (f'{shishen}代表的特点：', description['in_good_status']),
      (f'当{shishen}状态不好时，可能会有以下特点：', description['in_bad_status']),
      (f'{shishen}的恋爱/交友观：', description['relationship']),
    )
    _assert_headings(section, shishen_headings)

  assert Shishen.劫财 in rendered_shishens
  assert Interpreter.interpret_shishen(Shishen.劫财) == {
    'general': [],
    'in_good_status': [],
    'in_bad_status': [],
    'relationship': [],
  }


def _run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
  return subprocess.run(
    [sys.executable, str(Path(__file__).parents[1] / 'run_interpreter.py'), *args],
    cwd=cwd,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=False,
  )


def test_cli_help_and_seeded_default_are_read_only(tmp_path: Path) -> None:
  help_result = _run_cli(tmp_path, '--help')
  assert help_result.returncode == 0
  assert '--show-sources' in help_result.stdout
  first = _run_cli(tmp_path, '--seed', '42')
  second = _run_cli(tmp_path, '--seed', '42')
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
  assert '仅供参考' not in result.stdout
  assert 'legacy.' not in result.stdout


def test_cli_reference_export_retains_unverified_and_unevaluated_states(tmp_path: Path) -> None:
  result = _run_cli(
    tmp_path,
    '--birth-time', '2000-01-01 12:00', '--gender', 'male',
    '--include-reference-only', '--show-sources',
    '--output-dir', str(tmp_path), '--export-knowledge-base',
  )
  assert result.returncode == 0
  assert '来源尚未核实' in result.stdout
  assert '适用条件需整盘判断，尚未判断' in result.stdout
  assert '仅供参考' in result.stdout
  saved = tmp_path / 'interpretation_examples' / '0.txt'
  assert saved.read_text(encoding='utf-8') == re.sub(r'\x1b\[[0-9;]*m', '', result.stdout).removesuffix('\n')
  assert len(list((tmp_path / 'knowledge_base' / 'tiangan').glob('*.txt'))) == 10
  assert len(list((tmp_path / 'knowledge_base' / 'shishen').glob('*.txt'))) == 10
  ding = (tmp_path / 'knowledge_base' / 'tiangan' / '丁.txt').read_text(encoding='utf-8')
  assert '丁火有烛灯之象' in ding
  assert '《刻京台增补渊海子平大全》' in ding


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
  assert '适用条件需整盘判断，尚未判断' in text
  assert '来源尚未核实' in text
  assert '来源：' not in text


def test_example_helper_accepts_export_selection(tmp_path: Path) -> None:
  save_chart_examples(1, tmp_path, include_reference_only=True, show_sources=True)
  example = (tmp_path / 'interpretation_examples' / '0.txt').read_text(encoding='utf-8')
  assert '仅供参考' in example
  assert '\x1b' not in example
