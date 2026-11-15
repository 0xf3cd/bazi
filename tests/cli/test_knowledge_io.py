# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
import shutil
from pathlib import Path

import pytest

from bazi import cli
from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase

from cli_runner import ROOT, KNOWLEDGE_BASE, MATCH_ARGS, run_cli, run_guarded_script


def test_query_needs_no_birth_input_or_writes(tmp_path: Path) -> None:
  result = run_guarded_script(tmp_path, (
    'knowledge', '丁', '--topic', '历史象', '--source', 'yuanhai_ziping_stem_symbols_p70', '--show-sources',
  ))
  assert result.returncode == 0, result.stderr
  for text in ('tiangan.ding.lamp_symbol', '丁火有烛灯之象。', '第 70 页', '支持范围：', '来源说明：'):
    assert text in result.stdout
  assert '出生时刻：' not in result.stdout and '丁为阴火。' not in result.stdout
  assert list(tmp_path.iterdir()) == []


def test_open_premises_survive_default_reading(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'knowledge', '庚', '--topic', '性格')
  assert result.returncode == 0, result.stderr
  for text in ('后天有教养', '盘外前提', '有制有化尚未定义'):
    assert text in result.stdout
  ding = run_cli(tmp_path, 'knowledge', '丁')
  assert ding.returncode == 0 and '丁为阴火。' in ding.stdout and '丁火有烛灯之象。' in ding.stdout


def test_validation_and_empty_query(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'knowledge', '--validate-knowledge')
  assert result.returncode == 0 and result.stdout == '校验通过：326 条目，40 来源。\n'
  empty = run_cli(tmp_path, 'knowledge', 'wuxing.tu')
  assert empty.returncode == 0 and empty.stdout == '无匹配条目。\n'
  assert list(tmp_path.iterdir()) == []


def test_edit_validate_reload_cycle(tmp_path: Path) -> None:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  next(e for e in data['entries'] if e['claim_id'] == 'tiangan.ding.lamp_symbol')['limits'] = ['本次编辑的限度。']
  source = tmp_path / 'source.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  result = run_cli(tmp_path, 'knowledge', '丁', '--knowledge-source', str(source), '--validate-knowledge')
  assert result.returncode == 0, result.stderr
  restored = KnowledgeBase.load(source)
  assert result.stdout == '校验通过：326 条目，40 来源。\n' + ''.join(
    restored.render(entry) + '\n\n' for entry in restored.query('丁')
  )
  assert '本次编辑的限度。' in result.stdout
  assert restored.sources == KNOWLEDGE_BASE.sources
  assert set(tmp_path.iterdir()) == {source}


def test_minimal_source_and_ambiguous_name(tmp_path: Path) -> None:
  source = tmp_path / 'custom.json'
  objects = [{'object_id': 'custom.ding', 'kind': 'tiangan', 'name': '丁'}]
  data = {
    'schema_version': 4,
    'objects': objects,
    'sources': [],
    'entries': [{'claim_id': 'custom', 'objects': ['custom.ding'], 'text': '自定义文字。'}],
  }
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  result = run_cli(tmp_path, 'knowledge', '丁', '--knowledge-source', str(source))
  assert result.returncode == 0 and result.stdout == '条目：custom\n自定义文字。\n\n'
  objects.append({'object_id': 'other.ding', 'kind': 'concept', 'name': '丁'})
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  result = run_cli(tmp_path, 'knowledge', '丁', '--knowledge-source', str(source))
  assert result.returncode == 2 and 'custom.ding, other.ding' in result.stderr


@pytest.mark.parametrize('task', [('knowledge', '--validate-knowledge'), ('chart', '--knowledge'), (*MATCH_ARGS, '--knowledge')])
def test_bad_source_is_read_only(tmp_path: Path, task: tuple[str, ...]) -> None:
  source = tmp_path / 'source.json'
  payload = '{"schema_version":4,"schema_version":4}'
  source.write_text(payload, encoding='utf-8')
  result = run_cli(tmp_path, *task, '--knowledge-source', str(source))
  assert result.returncode == 2 and 'Duplicate JSON key' in result.stderr and not result.stdout
  assert source.read_text(encoding='utf-8') == payload and set(tmp_path.iterdir()) == {source}


def test_missing_bundled_source_is_explicit(tmp_path: Path) -> None:
  shutil.copytree(ROOT / 'bazi', tmp_path / 'bazi', ignore=shutil.ignore_patterns('__pycache__'))
  corpus = tmp_path / 'bazi/knowledge_data.json'
  custom = tmp_path / 'custom.json'
  custom.write_bytes(corpus.read_bytes())
  corpus.unlink()
  for task in (('chart', '--seed', '42'), MATCH_ARGS):
    result = run_cli(tmp_path, *task, checkout_root=tmp_path)
    assert result.returncode == 0, result.stderr
  result = run_cli(tmp_path, 'knowledge', '--validate-knowledge', checkout_root=tmp_path)
  assert result.returncode == 2 and 'No such file' in result.stderr
  result = run_cli(tmp_path, 'knowledge', '--validate-knowledge', '--knowledge-source', str(custom), checkout_root=tmp_path)
  assert result.returncode == 0 and '校验通过：' in result.stdout


@pytest.mark.parametrize('source_id', tuple(KNOWLEDGE_BASE.sources))
def test_cli_can_query_every_registered_source(tmp_path: Path, source_id: str) -> None:
  result = run_cli(tmp_path, 'knowledge', '--source', source_id)
  selected = KNOWLEDGE_BASE.query(source_id=source_id)
  expected = ''.join(KNOWLEDGE_BASE.render(entry) + '\n\n' for entry in selected) if selected else '无匹配条目。\n'
  assert result.returncode == 0 and result.stdout == expected


@pytest.mark.parametrize('bundled', [False, True])
@pytest.mark.parametrize('symlink', [False, True])
def test_chart_output_protects_editing_source(
  tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], bundled: bool, symlink: bool,
) -> None:
  source = tmp_path / 'source.json'
  source.write_bytes(DEFAULT_SOURCE_PATH.read_bytes())
  before = source.read_bytes()
  target = tmp_path / 'output.txt' if symlink else source
  if symlink:
    try:
      target.symlink_to(source)
    except OSError as error:
      pytest.skip(f'Symlink unavailable: {error}')
  if bundled:
    monkeypatch.setattr(cli, 'DEFAULT_SOURCE_PATH', source)
  args = [] if bundled else ['--knowledge', '--knowledge-source', str(source)]
  with pytest.raises(SystemExit) as caught:
    cli.main(['chart', '--output', str(target), *args])
  assert caught.value.code == 2 and 'must not overwrite' in capsys.readouterr().err
  assert source.read_bytes() == before
