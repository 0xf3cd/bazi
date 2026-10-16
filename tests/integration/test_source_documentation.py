# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import os
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[2]
README = (ROOT / 'README.md').read_text(encoding='utf-8')
BLOCKS = tuple(re.findall(r'^```python\n(.*?)^```$', README, re.MULTILINE | re.DOTALL))


def test_readme_has_python_examples() -> None:
  assert BLOCKS
  assert len(BLOCKS) == len(re.findall(r'^[ \t]*(?:`{3,}|~{3,})[ \t]*(?:python[0-9]*|py)\b', README, re.MULTILINE | re.IGNORECASE))


@pytest.mark.parametrize('block', BLOCKS, ids=[f'example-{index}' for index in range(len(BLOCKS))])
def test_readme_python_example(block: str, tmp_path: Path) -> None:
  result = subprocess.run(
    [sys.executable, '-B', '-c', block],
    cwd=tmp_path,
    env={**os.environ, 'PYTHONPATH': str(ROOT)},
    capture_output=True, text=True, encoding='utf-8', timeout=60, check=False,
  )
  assert result.returncode == 0, result.stdout + result.stderr
  assert 'object at 0x' not in result.stdout


@pytest.mark.parametrize('arguments', [
  ('run_tests.py',), ('run_demo.py',), ('run_relationship_analyzer.py',), ('run_package_checks.py',),
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


def test_readme_knowledge_counts_match_the_corpus() -> None:
  from typing import get_args

  from bazi.knowledge import KnowledgeBase, OutputPolicy, SourceState
  knowledge = KnowledgeBase.load()
  entries = tuple(knowledge.entries.values())
  table = re.search(r'^\| `output` \|.*?(?=\n\n)', README, re.MULTILINE | re.DOTALL)
  assert table is not None
  header, _, *body = table[0].splitlines()
  cells = [[cell.strip().strip('`') for cell in line.strip('|').split('|')] for line in (header, *body)]
  states = cells[0][1:-1]
  # Columns and rows cover every declared value, so a new state or policy cannot drop out of the table.
  assert sorted(states) == sorted(get_args(SourceState))
  assert [row[0] for row in cells[1:-1]] == list(get_args(OutputPolicy))
  for output, *counts, total in cells[1:-1]:
    selected = [entry for entry in entries if entry.output == output]
    assert [int(count) for count in counts] == [sum(entry.source_state == state for entry in selected) for state in states]
    assert int(total) == len(selected)
  assert cells[-1][0] == '合计' and cells[-1][1:] == [str(sum(entry.source_state == state for entry in entries)) for state in states] + [str(len(entries))]
  unresolved = sum(entry.applicability == 'unresolved' for entry in entries)
  assert f'其中 {unresolved} 条前提待梳理' in README
  assert (
    f'另有对象 {len(knowledge.objects)} 个、情境 {len(knowledge.contexts)} 个、来源 {len(knowledge.sources)} 个。'
  ) in README
