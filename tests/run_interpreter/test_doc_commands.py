# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_doc_commands.py

import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from run_interpreter import _COMMANDS, _command_parser

from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextResult

from cli_runner import ROOT, GUANSHA, run_cli


def _doc_commands(markdown: str) -> list[list[str]]:
  found: list[list[str]] = []
  for block in re.findall(r'```(?:sh|bash)\n(.*?)```', markdown, flags=re.DOTALL):
    text = re.sub(r'\\\n\s*', ' ', block)
    for line in text.splitlines():
      tokens = shlex.split(line)
      if 'run_interpreter.py' in tokens:
        found.append(tokens[tokens.index('run_interpreter.py') + 1:])
  return found


def _check_doc_command(tokens: list[str]) -> None:
  if not tokens or tokens[0] not in _COMMANDS:
    raise AssertionError(f'Not a subcommand form: {tokens}')
  _command_parser().parse_args(tokens)


DOC_FILES = ('README.md', 'API_CONTRACT.md', 'docs/guides/knowledge.md', 'docs/guides/quickstart.md', 'docs/guides/integration.md',
             'docs/guides/configuration.md', 'docs/guides/relations-transits.md', 'CONTRIBUTING.md')


def test_documented_commands_parse_as_subcommands() -> None:
  commands = [tokens for name in DOC_FILES for tokens in _doc_commands((ROOT / name).read_text(encoding='utf-8'))]
  assert len(commands) >= 3
  for tokens in commands:
    _check_doc_command(tokens)


@pytest.mark.parametrize('tokens', _doc_commands((ROOT / 'README.md').read_text(encoding='utf-8')))
def test_readme_task_commands_execute(tokens: list[str], tmp_path: Path) -> None:
  result = run_cli(tmp_path, *tokens)
  assert result.returncode == 0, result.stdout + result.stderr
  if '--export-context-json' in tokens:
    path = tmp_path / tokens[tokens.index('--export-context-json') + 1]
    text = path.read_text(encoding='utf-8')
    assert json.loads(ContextResult.from_json(text).export_json()) == json.loads(text)


def test_readme_chart_exports_roundtrip(tmp_path: Path) -> None:
  commands = _doc_commands((ROOT / 'README.md').read_text(encoding='utf-8'))
  exporting = [tokens for tokens in commands if tokens[0] == 'chart' and '--export-chart-json' in tokens]
  assert len(exporting) == 1
  result = run_cli(tmp_path, *exporting[0])
  assert result.returncode == 0, result.stdout + result.stderr
  paths = {path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob('*') if path.is_file()}
  assert paths == {'output_data/interpretation_examples/0.txt', 'output_data/chart.json'}
  record = json.loads((tmp_path / 'output_data/chart.json').read_text(encoding='utf-8'))
  restored = BaziChart.from_json(record)
  assert restored.json == record
  assert record['pillars'] == {'year': '庚午', 'month': '辛巳', 'day': '壬午', 'hour': '乙巳'}
  text = (tmp_path / 'output_data/interpretation_examples/0.txt').read_text(encoding='utf-8')
  assert '\x1b' not in text and text in re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)


def test_source_chart_needs_only_colorama(tmp_path: Path) -> None:
  spec = importlib.util.find_spec('colorama')
  assert spec is not None and spec.origin is not None
  shutil.copytree(Path(spec.origin).parent, tmp_path / 'colorama')
  result = subprocess.run(
    [sys.executable, '-S', str(ROOT / 'run_interpreter.py'), 'chart',
     '--birth-time', '1990-05-17 10:30', '--gender', 'female'],
    cwd=tmp_path, env={**os.environ, 'PYTHONPATH': str(tmp_path)},
    capture_output=True, text=True, encoding='utf-8', timeout=60, check=False,
  )
  assert result.returncode == 0, result.stdout + result.stderr
  assert '年柱：天干庚' in result.stdout


def test_doc_gate_covers_every_file_with_commands() -> None:
  mentions = {
    path.relative_to(ROOT).as_posix()
    for path in (*ROOT.glob('*.md'), *(ROOT / 'docs').rglob('*.md'))
    if any('run_interpreter.py' in block
           for block in re.findall(r'```(?:sh|bash)\n(.*?)```', path.read_text(encoding='utf-8'), flags=re.DOTALL))
  }
  assert mentions <= set(DOC_FILES), mentions - set(DOC_FILES)


@pytest.mark.parametrize('block', [
  '```sh\npython run_interpreter.py --seed 1\n```',
  '```sh\npython run_interpreter.py chart --no-such-flag\n```',
  '```sh\npython run_interpreter.py chart --seed \\\n  one\n```',
  '```sh\npython run_interpreter.py\n```',
])
def test_doc_command_check_rejects_bad_examples(block: str) -> None:
  commands = _doc_commands(block)
  assert len(commands) == 1
  with pytest.raises((AssertionError, SystemExit)):
    _check_doc_command(commands[0])


def test_doc_command_check_accepts_a_good_example() -> None:
  commands = _doc_commands(f'```sh\npython run_interpreter.py \\\n  match {GUANSHA} \\\n  --birth-time "2000-01-01 12:00" --gender male --observation-scope natal\n```')
  assert commands[0][0] == 'match'
  _check_doc_command(commands[0])


def _migration_tokens(command: str) -> list[str]:
  return shlex.split(command.replace('…', '').replace('判据ID', GUANSHA))


def _inline_task_commands(markdown: str) -> list[list[str]]:
  snippets = re.findall(r'(?<!`)`([^`\n]+)`(?!`)', markdown)
  return [
    _migration_tokens(text) for text in snippets
    if (parts := text.split(maxsplit=1)) and (
      parts[0] in _COMMANDS or re.match(r'^[A-Za-z][A-Za-z0-9_-]*\s+(?:--|判据ID(?:\s|$))', text)
    )
  ]


@pytest.mark.parametrize('name', ['README.md', 'API_CONTRACT.md', 'docs/guides/knowledge.md'])
def test_inline_task_examples_are_parseable(name: str) -> None:
  commands = _inline_task_commands((ROOT / name).read_text(encoding='utf-8'))
  assert len(commands) >= 3
  for tokens in commands:
    _check_doc_command(tokens)


def test_migration_table_new_commands_parse() -> None:
  text = (ROOT / 'API_CONTRACT.md').read_text(encoding='utf-8')
  section = re.search(r'### 源码脚本\n(.*?)(?=\n## |\Z)', text, flags=re.DOTALL)
  assert section is not None
  rows = re.findall(r'^\| `[^`]+` \| (.*) \|$', section[1], flags=re.MULTILINE)
  assert len(rows) >= 5
  for row in rows:
    commands = re.findall(r'`([^`]+)`', row)
    assert commands
    for command in commands:
      _check_doc_command(_migration_tokens(command))


@pytest.mark.parametrize('command', [
  'knowledge --allx', 'chart --no-such-flag', 'knwoledge --all', 'Knowledge --all', 'know-ledge --all',
])
def test_migration_typos_are_rejected(command: str) -> None:
  commands = _inline_task_commands(f'改为 `{command}`。')
  assert len(commands) == 1
  with pytest.raises((AssertionError, SystemExit)):
    _check_doc_command(commands[0])
