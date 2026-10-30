# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_doc_commands.py

import re
import shlex
from pathlib import Path

import pytest

from bazi import cli


from cli_runner import ROOT, GUANSHA, run_cli


def _doc_commands(markdown: str) -> list[list[str]]:
  found: list[list[str]] = []
  for block in re.findall(r'```(?:sh|bash)\n(.*?)```', markdown, flags=re.DOTALL):
    text = re.sub(r'\\\n\s*', ' ', block)
    for line in text.splitlines():
      tokens = shlex.split(line)
      if tokens and tokens[0] == 'bazi':
        found.append(tokens[1:])
  return found


def _check_doc_command(tokens: list[str]) -> None:
  if not tokens or tokens[0] not in cli._COMMANDS:
    raise AssertionError(f'Not a subcommand form: {tokens}')
  try:
    cli._command_parser().parse_args(tokens)
  except SystemExit as stop:
    if stop.code != 0:
      raise


DOC_FILES = ('README.md', 'API_CONTRACT.md', 'docs/guides/knowledge.md', 'docs/guides/quickstart.md', 'docs/guides/integration.md',
             'docs/guides/configuration.md', 'docs/guides/relations-transits.md', 'CONTRIBUTING.md')


def test_documented_commands_parse_as_subcommands() -> None:
  commands = [tokens for name in DOC_FILES for tokens in _doc_commands((ROOT / name).read_text(encoding='utf-8'))]
  assert len(commands) >= 3
  assert len(_doc_commands((ROOT / 'README.md').read_text(encoding='utf-8'))) >= 3
  for tokens in commands:
    _check_doc_command(tokens)


@pytest.mark.parametrize('tokens', _doc_commands((ROOT / 'README.md').read_text(encoding='utf-8')))
def test_readme_task_commands_execute(tokens: list[str], tmp_path: Path) -> None:
  result = run_cli(tmp_path, *tokens)
  assert result.returncode == 0, result.stdout + result.stderr


def test_readme_chart_saves_displayed_text(tmp_path: Path) -> None:
  commands = _doc_commands((ROOT / 'README.md').read_text(encoding='utf-8'))
  exporting = [tokens for tokens in commands if tokens[0] == 'chart' and '--output-dir' in tokens]
  assert len(exporting) == 1
  result = run_cli(tmp_path, *exporting[0])
  assert result.returncode == 0, result.stdout + result.stderr
  paths = {path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob('*') if path.is_file()}
  assert paths == {'output_data/interpretation_examples/0.txt'}
  assert all(value in result.stdout for value in ('年柱：天干庚', '月柱：天干辛', '日柱：天干壬', '时柱：天干乙'))
  text = (tmp_path / 'output_data/interpretation_examples/0.txt').read_text(encoding='utf-8')
  assert '\x1b' not in text and text in re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)


def test_doc_gate_covers_every_file_with_commands() -> None:
  mentions = {
    path.relative_to(ROOT).as_posix()
    for path in (*ROOT.glob('*.md'), *(ROOT / 'docs').rglob('*.md'))
    if _doc_commands(path.read_text(encoding='utf-8'))
  }
  assert mentions
  assert mentions <= set(DOC_FILES), mentions - set(DOC_FILES)


@pytest.mark.parametrize('block', [
  '```sh\nbazi --seed 1\n```',
  '```sh\nbazi chart --no-such-flag\n```',
  '```sh\nbazi chart --seed \\\n  one\n```',
  '```sh\nbazi\n```',
  '```sh\nbazi chrat --seed 1\n```',
])
def test_doc_command_check_rejects_bad_examples(block: str) -> None:
  commands = _doc_commands(block)
  assert len(commands) == 1
  with pytest.raises((AssertionError, SystemExit)) as rejected:
    _check_doc_command(commands[0])
  if isinstance(rejected.value, SystemExit):
    assert rejected.value.code == 2


def test_doc_command_check_accepts_a_good_example() -> None:
  commands = _doc_commands(f'```sh\nbazi \\\n  match {GUANSHA} \\\n  --birth-time "2000-01-01 12:00" --gender male --observation-scope natal\n```')
  assert commands[0][0] == 'match'
  _check_doc_command(commands[0])


def _inline_tokens(command: str) -> list[str]:
  tokens = shlex.split(command.replace('…', '').replace('<判据ID>', GUANSHA).replace('判据ID', GUANSHA))
  return tokens[1:] if tokens and tokens[0] == 'bazi' else tokens


def _inline_task_commands(markdown: str) -> list[list[str]]:
  snippets = re.findall(r'(?<!`)`([^`\n]+)`(?!`)', markdown)
  return [
    _inline_tokens(text) for text in snippets
    if (parts := text.split(maxsplit=1)) and (
      (parts[0] == 'bazi' and len(parts) > 1) or parts[0] in cli._COMMANDS
      or re.match(r'^[A-Za-z][A-Za-z0-9_-]*\s+(?:--|判据ID(?:\s|$))', text)
    )
  ]


@pytest.mark.parametrize('name', ['README.md', 'API_CONTRACT.md', 'docs/guides/knowledge.md'])
def test_inline_task_examples_are_parseable(name: str) -> None:
  commands = _inline_task_commands((ROOT / name).read_text(encoding='utf-8'))
  assert len(commands) >= 3
  for tokens in commands:
    _check_doc_command(tokens)


@pytest.mark.parametrize('command,tokens', [
  ('bazi demo --seed 236', ['demo', '--seed', '236']),
  ('bazi relationship --seed 236', ['relationship', '--seed', '236']),
  ('bazi chart --seed 1', ['chart', '--seed', '1']),
  ('knowledge --all', ['knowledge', '--all']),
  ('bazi match <判据ID>', ['match', GUANSHA]),
  ('match 判据ID …', ['match', GUANSHA]),
])
def test_inline_examples_keep_the_task(command: str, tokens: list[str]) -> None:
  commands = _inline_task_commands(f'运行 `{command}`。')
  assert commands == [tokens]
  _check_doc_command(commands[0])


@pytest.mark.parametrize('task', cli._COMMANDS)
@pytest.mark.parametrize('flag', ['-h', '--help'])
def test_help_examples_are_valid(task: str, flag: str, capsys: pytest.CaptureFixture[str]) -> None:
  command = f'bazi {task} {flag}'
  commands = _doc_commands(f'```sh\n{command}\n```') + _inline_task_commands(f'运行 `{command}`。')
  assert commands == [[task, flag], [task, flag]]
  for tokens in commands:
    _check_doc_command(tokens)
  captured = capsys.readouterr()
  assert captured.out.count(f'usage: bazi {task}') == 2 and captured.err == ''


@pytest.mark.parametrize('task', ['chrat', 'knwoledge'])
@pytest.mark.parametrize('flag', ['-h', '--help'])
def test_unknown_help_still_requires_a_task(task: str, flag: str, capsys: pytest.CaptureFixture[str]) -> None:
  with pytest.raises(AssertionError, match='Not a subcommand form'):
    _check_doc_command([task, flag])
  captured = capsys.readouterr()
  assert captured.out == captured.err == ''


def test_fenced_examples_cover_five_tasks() -> None:
  commands = _doc_commands('```bash\nbazi demo --seed 1\nbazi relationship --seed 1\n'
                           'bazi chart --seed 1\nbazi knowledge --all\nbazi match\n```')
  assert [tokens[0] for tokens in commands] == ['demo', 'relationship', 'chart', 'knowledge', 'match']
  for tokens in commands:
    _check_doc_command(tokens)


@pytest.mark.parametrize('command', [
  'knowledge --allx', 'chart --no-such-flag', 'knwoledge --all', 'Knowledge --all', 'know-ledge --all',
  'bazi knowledge --allx', 'bazi chrat --seed 1', 'bazi demo --seed one',
])
def test_inline_typos_are_rejected(command: str) -> None:
  commands = _inline_task_commands(f'改为 `{command}`。')
  assert len(commands) == 1
  with pytest.raises((AssertionError, SystemExit)) as rejected:
    _check_doc_command(commands[0])
  if isinstance(rejected.value, SystemExit):
    assert rejected.value.code == 2
