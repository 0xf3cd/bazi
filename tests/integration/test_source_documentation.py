# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import os
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

from bazi.bazi_chart import BaziChart
from bazi.bazi import Bazi
from bazi.chart_text import basic_text


ROOT = Path(__file__).parents[2]
README = (ROOT / 'README.md').read_text(encoding='utf-8')
BLOCKS = tuple(re.findall(r'^```python\n(.*?)^```$', README, re.MULTILINE | re.DOTALL))


def test_readme_has_python_examples() -> None:
  assert BLOCKS
  assert len(BLOCKS) == len(re.findall(r'^[ \t]*(?:`{3,}|~{3,})[ \t]*(?:python[0-9]*|py)\b', README, re.MULTILINE | re.IGNORECASE))


def _run_readme(block: str, cwd: Path) -> subprocess.CompletedProcess[str]:
  script = cwd / 'first_chart.py'
  script.write_text(block, encoding='utf-8')
  return subprocess.run(
    [sys.executable, '-B', str(script)],
    cwd=cwd,
    env={**os.environ, 'PYTHONPATH': str(ROOT)},
    capture_output=True, text=True, encoding='utf-8', timeout=60, check=False,
  )


@pytest.mark.parametrize('block', BLOCKS, ids=[f'example-{index}' for index in range(len(BLOCKS))])
def test_readme_python_example(block: str, tmp_path: Path) -> None:
  result = _run_readme(block, tmp_path)
  assert result.returncode == 0, result.stdout + result.stderr
  assert 'object at 0x' not in result.stdout


def test_first_chart_saves_readable_records(tmp_path: Path) -> None:
  result = _run_readme(BLOCKS[0], tmp_path)
  assert result.returncode == 0, result.stdout + result.stderr
  expected = re.search(r'^```text\n(.*?)^```$', README, re.MULTILINE | re.DOTALL)
  assert expected is not None and result.stdout == expected[1]
  assert {path.name for path in tmp_path.iterdir()} == {'first_chart.py', 'chart.txt'}
  expected_chart = BaziChart(Bazi.create('1990-05-17T10:30:00', 'female'))
  assert tuple(map(str, expected_chart.bazi.pillars)) == ('庚午', '辛巳', '壬午', '乙巳')
  assert str(expected_chart.bazi.gender) == 'female' and str(expected_chart.bazi.config.precision) == 'day'
  text = (tmp_path / 'chart.txt').read_text(encoding='utf-8')
  assert text == basic_text(expected_chart) and '\x1b' not in text


@pytest.mark.parametrize('arguments', [
  ('run_tests.py',), ('run_package_checks.py',),
  ('-c', 'from bazi.cli import main; raise SystemExit(main())', 'demo'),
  ('-c', 'from bazi.cli import main; raise SystemExit(main())', 'relationship'),
  ('-m', 'bazi.calendar.celestial_data.generator'),
])
def test_source_cli_help_rendering(arguments: tuple[str, ...]) -> None:
  if arguments[0] == '-m' and importlib.util.find_spec('celestial_calendar') is None:
    pytest.skip('The offline generator requires optional celestial-calendar.')
  result = subprocess.run(
    [sys.executable, '-B', *arguments, '--help'],
    cwd=ROOT,
    capture_output=True, text=True, encoding='utf-8', timeout=60, check=False,
  )
  assert result.returncode == 0, result.stdout + result.stderr
  assert re.search('[\u4e00-\u9fff]', result.stdout)


def test_knowledge_guide_matches_the_corpus() -> None:
  from typing import get_args

  from bazi.knowledge import Applicability, KnowledgeBase, SourceState

  guide = (ROOT / 'docs/guides/knowledge.md').read_text(encoding='utf-8')
  knowledge = KnowledgeBase.load()
  entries = tuple(knowledge.entries.values())
  # Every declared value must remain documented, including values with zero corpus hits.
  for field, schema in (('source_state', SourceState), ('applicability', Applicability)):
    row = next(line for line in guide.splitlines() if line.startswith(f'| `{field}` |'))
    values = re.findall(r'`([^`]+)`', row.strip('|').split('|')[-1])
    assert sorted(values) == sorted(get_args(schema)), field
  witnessed = sum(entry.source_state == 'witnessed' for entry in entries)
  row = next(line for line in guide.splitlines() if line.startswith('| `show_by_default` |'))
  assert re.findall(r'`([^`]+)`', row.strip('|').split('|')[-1]) == ['True', 'False']
  reference = sum(entry.source_state == 'witnessed' and not entry.show_by_default for entry in entries)
  assert f'`witnessed` 条目有 {witnessed} 条，其中 {reference} 条仍不默认展示' in guide
