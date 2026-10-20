# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_doc_commands.py

import re
import shlex

import pytest

from run_interpreter import _COMMANDS, _command_parser

from command_runner import ROOT, GUANSHA


# ---- 文档里的命令只解析、不执行：新形式才算数。

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


DOC_FILES = ('README.md', 'docs/guides/knowledge.md', 'docs/guides/quickstart.md', 'docs/guides/integration.md',
             'docs/guides/configuration.md', 'docs/guides/relations-transits.md', 'CONTRIBUTING.md')


def test_documented_commands_parse_as_subcommands() -> None:
  commands = [tokens for name in DOC_FILES for tokens in _doc_commands((ROOT / name).read_text(encoding='utf-8'))]
  assert len(commands) >= 3
  for tokens in commands:
    _check_doc_command(tokens)


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
