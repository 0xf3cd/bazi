# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import re
from pathlib import Path

import pytest

from bazi.defines import Tiangan, Shishen
from bazi.knowledge import KnowledgeBase, object_id

from cli_runner import run_cli


@pytest.mark.parametrize('reference', [False, True])
@pytest.mark.parametrize('sources', [False, True])
def test_chart_and_knowledge_share_export_dir(tmp_path: Path, reference: bool, sources: bool) -> None:
  flags = (*(['--include-reference-only'] if reference else []), *(['--show-sources'] if sources else []))
  chart = run_cli(tmp_path, 'chart', '--seed', '5', '--output-dir', 'out', *flags)
  assert chart.returncode == 0 and chart.stderr == '', chart.stderr
  assert chart.stdout.startswith('random seed: 5\n') and chart.stdout.count('出生时间：') == 1
  saved = tmp_path / 'out/interpretation_examples/0.txt'
  before = saved.read_bytes()
  assert before.decode('utf-8') == re.sub(
    r'\x1b\[[0-9;]*m', '', chart.stdout.removeprefix('random seed: 5\n'),
  ).removesuffix('\n')
  assert ('仅供参考' in chart.stdout) is reference
  assert ('来源：' in chart.stdout) is sources

  exported = run_cli(tmp_path, 'knowledge', '--export-knowledge-base', '--output-dir', 'out', *flags)
  assert exported.returncode == 0 and exported.stdout == exported.stderr == '', exported.stderr
  files = {path.relative_to(tmp_path / 'out').as_posix() for path in (tmp_path / 'out').rglob('*') if path.is_file()}
  assert files == {
    'interpretation_examples/0.txt',
    *(f'knowledge_base/tiangan/{tg}.txt' for tg in Tiangan),
    *(f'knowledge_base/shishen/{ss}.txt' for ss in Shishen),
  }
  assert len(files) == 21 and saved.read_bytes() == before
  knowledge = KnowledgeBase.load()
  for category, subjects in (('tiangan', tuple(Tiangan)), ('shishen', tuple(Shishen))):
    for subject in subjects:
      text = (tmp_path / 'out/knowledge_base' / category / f'{subject}.txt').read_text(encoding='utf-8')
      expected = knowledge.render_subject(object_id(subject), include_reference_only=reference, show_sources=sources)
      assert text == f'{subject}知识条目：\n{expected}\n'
      assert '\x1b' not in text
  ding = (tmp_path / 'out/knowledge_base/tiangan/丁.txt').read_text(encoding='utf-8')
  assert ('丁火有烛灯之象' in ding) is reference
  assert ('来源：' in ding) is sources
