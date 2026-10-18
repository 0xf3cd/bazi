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


def test_knowledge_guide_states_and_counts_match_the_corpus() -> None:
  from typing import get_args

  from bazi.knowledge import Applicability, KnowledgeBase, OutputPolicy, SourceState

  guide = (ROOT / 'docs/guides/knowledge.md').read_text(encoding='utf-8')
  knowledge = KnowledgeBase.load()
  entries = tuple(knowledge.entries.values())
  # Every declared value must remain documented, including values with zero corpus hits.
  for field, schema in (('source_state', SourceState), ('applicability', Applicability), ('output', OutputPolicy)):
    row = next(line for line in guide.splitlines() if line.startswith(f'| `{field}` |'))
    values = re.findall(r'`([^`]+)`', row.strip('|').split('|')[-1])
    assert sorted(values) == sorted(get_args(schema)), field
  witnessed = sum(entry.source_state == 'witnessed' for entry in entries)
  reference = sum(entry.source_state == 'witnessed' and entry.output == 'reference_only' for entry in entries)
  assert f'`witnessed` 条目有 {witnessed} 条，其中 {reference} 条仍是 `reference_only`' in guide
