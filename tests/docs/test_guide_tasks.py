# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import ast
import os
import re
import subprocess
import sys
import typing
from dataclasses import fields, replace
from enum import Enum
from pathlib import Path

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

from markdown_it import MarkdownIt

from run_doc_checks import Page, check_task_navigation
from run_docs import generate_installation
from bazi.school import BaziConfig, BaziSchool


ROOT = Path(__file__).resolve().parents[2]


def _check_configuration_table(source: str) -> None:
  section = source.split('## 配置速查\n', 1)[1].split('\n## 出生时间怎么填', 1)[0]
  rows: dict[str, list[str]] = {}
  for line in section.splitlines():
    if not line.startswith('| `'):
      continue
    cells = [cell.strip() for cell in line.strip('|').split('|')]
    name = cells[0].strip('`')
    assert name not in rows, ('Duplicate configuration field', name)
    rows[name] = cells
  expected = {field.name for cls in (BaziConfig, BaziSchool) for field in fields(cls)}
  assert rows.keys() == expected, ('Configuration fields', rows.keys() ^ expected)
  for cls in (BaziConfig, BaziSchool):
    hints = typing.get_type_hints(cls)
    for field in fields(cls):
      _, type_cell, choices_cell, default_cell, _ = rows[field.name]
      typ = hints[field.name]
      assert type_cell == f'`{typ.__qualname__}`', field.name
      if field.name == 'school':
        assert choices_cell == '`BaziSchool` 实例' and default_cell == '`DEFAULT_SCHOOL`'
        continue
      allowed = set()
      for member in typ:
        try:
          replace(cls(), **{field.name: member})
        except ValueError:
          continue
        allowed.add(member.name)
      assert set(re.findall(r'`([^`]+)`', choices_cell)) == allowed, ('Configuration choices', field.name)
      assert isinstance(field.default, Enum)
      assert default_cell == f'`{field.default.name}`', ('Configuration default', field.name)


def test_configuration_table_matches_live_choices():
  _check_configuration_table((ROOT / 'docs/guides/configuration.md').read_text(encoding='utf-8'))


@pytest.mark.parametrize('mutation', ['missing', 'default', 'anchor'])
def test_configuration_table_detects_drift(mutation):
  source = (ROOT / 'docs/guides/configuration.md').read_text(encoding='utf-8')
  row = next(line for line in source.splitlines() if line.startswith('| `hongyan_anchor` |'))
  changed = {
    'missing': '',
    'default': row.replace('| `DAY` |', '| `YEAR` |'),
    'anchor': row.replace('`YEAR`、`DAY`', '`YEAR`、`DAY`、`YEAR_AND_DAY`'),
  }[mutation]
  with pytest.raises(AssertionError):
    _check_configuration_table(source.replace(row, changed))


@pytest.mark.parametrize('version, requirement', [
  ('dev', 'git+https://github.com/0xf3cd/bazi.git@' + 'a' * 40),
  ('v99.0.0', 'bazi==99.0.0'),
])
def test_installation_uses_the_build_identity(tmp_path, version, requirement):
  generate_installation(tmp_path, version, 'a' * 40)
  source = (tmp_path / 'installation.inc').read_text(encoding='utf-8')
  blocks = [token.content.strip() for token in MarkdownIt().parse(source) if token.type == 'fence']
  assert blocks == [f'python -m pip install "{requirement}"']
  assert ('本页为开发版' in source) == (version == 'dev')


def _task_pages(version: str = 'dev') -> dict[str, Page]:
  names = (
    'quickstart', 'cli', 'configuration', 'relations-transits', 'knowledge', 'integration',
  )
  pages = {f'guides/{name}.html': Page() for name in names}
  pages['api-contract.html'] = Page()
  index = Page()
  index.feed(''.join(f'<a href="{name}">task</a>' for name in pages))
  pages['index.html'] = index
  requirement = 'git+https://github.com/0xf3cd/bazi.git@' + 'a' * 40 if version == 'dev' else 'bazi==99.0.0'
  for name in ('quickstart', 'knowledge', 'cli'):
    pages[f'guides/{name}.html'].feed(f'<pre>python -m pip install "{requirement}"</pre>')
  return pages


@pytest.mark.parametrize('version', ['dev', 'v99.0.0'])
def test_same_version_navigation_is_accepted(version):
  pages = _task_pages(version)
  pages['contributing.html'] = Page()
  pages['contributing.html'].feed('<a href="https://github.com/0xf3cd/bazi/blob/main/AGENTS.md">当前贡献政策</a>')
  check_task_navigation(pages, version, 'a' * 40)


@pytest.mark.parametrize('mutation', ['main', 'latest', 'missing-page', 'missing-link', 'wrong-install'])
def test_task_navigation_detects_wrong_paths(mutation):
  pages = _task_pages()
  if mutation == 'main':
    pages['guides/integration.html'].feed('<a href="https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md">contract</a>')
  elif mutation == 'latest':
    pages['guides/quickstart.html'].feed('<a href="https://0xf3cd.github.io/bazi/latest/guides/cli.html">cli</a>')
  elif mutation == 'missing-page':
    del pages['api-contract.html']
  elif mutation == 'missing-link':
    pages['index.html'].links.remove('api-contract.html')
  else:
    pages['guides/knowledge.html'].code_blocks[:] = ['python -m pip install bazi']
  with pytest.raises(AssertionError):
    check_task_navigation(pages, 'dev', 'a' * 40)


def _run_example(code: str, expected: str, directory: Path, timeout: float = 15) -> None:
  result = subprocess.run(
    [sys.executable, '-c', code], cwd=directory,
    env=os.environ | {'PYTHONPATH': str(ROOT)},
    capture_output=True, text=True, encoding='utf-8', timeout=timeout, check=False,
  )
  assert result.returncode == 0, result.stderr
  assert result.stdout == expected


@pytest.mark.parametrize('name', ['traits', 'liunian'])
def test_chart_api_examples_run_independently(tmp_path, name):
  source = ast.parse((ROOT / 'bazi/bazi_chart.py').read_text(encoding='utf-8'))
  cls = next(node for node in source.body if isinstance(node, ast.ClassDef) and node.name == 'BaziChart')
  method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)
  doc = ast.get_docstring(method)
  assert doc is not None
  blocks = [token for token in MarkdownIt().parse(doc) if token.type == 'fence']
  assert [token.info for token in blocks] == ['python', 'text']
  _run_example(blocks[0].content, blocks[1].content, tmp_path)


def test_example_gate_rejects_missing_input(tmp_path):
  with pytest.raises(AssertionError, match='NameError'):
    _run_example('print(chart.traits)', '', tmp_path)


def test_example_gate_stops_an_infinite_loop(tmp_path):
  with pytest.raises(subprocess.TimeoutExpired) as stopped:
    _run_example("print('started', flush=True)\nwhile True:\n  pass\n", '', tmp_path, timeout=1)
  assert stopped.value.stdout == b'started\n'
