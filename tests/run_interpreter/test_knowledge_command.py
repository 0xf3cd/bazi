# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_knowledge_command.py

import json
import os
import shutil
from pathlib import Path

import pytest

import run_interpreter
from run_interpreter import _LIST_DIMENSIONS, main
from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase

from cli_runner import run_cli


def test_bare_knowledge_gives_an_overview(tmp_path: Path) -> None:
  library = KnowledgeBase.load()
  result = run_cli(tmp_path, 'knowledge')
  assert result.returncode == 0 and result.stderr == ''
  assert f'{len(library.entries)} 条目（默认可见 {len(library.query())} 条' in result.stdout
  for flag, dimension in _LIST_DIMENSIONS.items():
    assert f'--{flag}：{len(library.filter_values(dimension))} 个值' in result.stdout
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('flag, dimension', sorted(_LIST_DIMENSIONS.items()))
def test_list_values_matches_the_library(tmp_path: Path, flag: str, dimension: str) -> None:
  result = run_cli(tmp_path, 'knowledge', '--list-values', flag)
  assert result.returncode == 0
  assert result.stdout.splitlines() == list(KnowledgeBase.load().filter_values(dimension))


def test_filters_query_without_a_flag(tmp_path: Path) -> None:
  library = KnowledgeBase.load()
  result = run_cli(tmp_path, 'knowledge', '--object', 'tiangan.ding')
  expected = ''.join(library.render(entry) + '\n\n' for entry in library.query(object_id='tiangan.ding'))
  assert result.returncode == 0 and result.stdout == expected


def test_all_lists_the_default_view(tmp_path: Path) -> None:
  library = KnowledgeBase.load()
  result = run_cli(tmp_path, 'knowledge', '--all')
  assert result.returncode == 0
  assert result.stdout.count('\n\n') >= len(library.query()) - 1 and library.query()[0].claim_id in result.stdout


def test_exports_the_base_texts_only(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'knowledge', '--export-knowledge-base', '--output-dir', 'out')
  assert result.returncode == 0 and result.stdout == '' and result.stderr == ''
  assert len(list((tmp_path / 'out' / 'knowledge_base').rglob('*.txt'))) == 20
  assert not (tmp_path / 'out' / 'interpretation_examples').exists()


@pytest.mark.parametrize('args', [('--output-dir', 'out'), ('--show-sources',)])
def test_export_options_need_the_export(tmp_path: Path, args: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, 'knowledge', *args)
  assert result.returncode == 2 and f'{args[0]} only applies with --export-knowledge-base' in result.stderr
  assert list(tmp_path.iterdir()) == []


def test_export_shows_sources_on_request(tmp_path: Path) -> None:
  for name, extra in (('plain', ()), ('sourced', ('--show-sources',))):
    result = run_cli(tmp_path, 'knowledge', '--export-knowledge-base', '--output-dir', name, *extra)
    assert result.returncode == 0 and result.stderr == ''
  plain = (tmp_path / 'plain' / 'knowledge_base' / 'tiangan' / '甲.txt').read_text(encoding='utf-8')
  sourced = (tmp_path / 'sourced' / 'knowledge_base' / 'tiangan' / '甲.txt').read_text(encoding='utf-8')
  assert plain.startswith('甲知识条目：') and sourced.startswith('甲知识条目：') and len(sourced) > len(plain)


def test_validate_and_export_combine(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'knowledge', '--validate-knowledge', '--export-knowledge-json', 'out/k.json')
  assert result.returncode == 0
  assert result.stdout.startswith('校验通过：') and result.stdout.endswith(f'已导出知识：{Path("out") / "k.json"}\n')
  assert (tmp_path / 'out' / 'k.json').read_text(encoding='utf-8') == KnowledgeBase.load().export_json()


def test_text_export_reads_the_given_source(tmp_path: Path) -> None:
  data = json.loads(KnowledgeBase.load().export_json())
  record = next(entry for entry in data['entries'] if entry['claim_id'] == 'tiangan.ding.lamp_symbol')
  record['limits'] = ['本次编辑的限度。']
  (tmp_path / 'src.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  for name, extra in (('custom', ('--knowledge-source', 'src.json')), ('default', ())):
    result = run_cli(tmp_path, 'knowledge', '--export-knowledge-base', '--output-dir', name, '--include-reference-only', *extra)
    assert result.returncode == 0 and result.stderr == ''
  assert '本次编辑的限度。' in (tmp_path / 'custom' / 'knowledge_base' / 'tiangan' / '丁.txt').read_text(encoding='utf-8')
  assert '本次编辑的限度。' not in (tmp_path / 'default' / 'knowledge_base' / 'tiangan' / '丁.txt').read_text(encoding='utf-8')


def test_text_export_bad_source_writes_nothing(tmp_path: Path) -> None:
  (tmp_path / 'bad.json').write_text('{}', encoding='utf-8')
  for source in ('missing.json', 'bad.json'):
    result = run_cli(tmp_path, 'knowledge', '--knowledge-source', source, '--export-knowledge-base', '--output-dir', 'out')
    assert result.returncode == 2 and 'error:' in result.stderr and 'Traceback' not in result.stderr
    assert result.stdout == '' and not (tmp_path / 'out').exists()


@pytest.mark.parametrize('target, output_dir', [
  ('out/knowledge_base/tiangan/甲.txt', ('--output-dir', 'out')),
  ('out/knowledge_base/shishen/正官.txt', ('--output-dir', 'out')),
  ('out/./knowledge_base/../knowledge_base/tiangan/甲.txt', ('--output-dir', 'out')),
])
def test_json_export_must_not_overlap_text_export(tmp_path: Path, target: str, output_dir: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, 'knowledge', '--object', 'tiangan.ding', '--export-knowledge-json', target, '--export-knowledge-base', *output_dir)
  assert result.returncode == 2 and '--export-knowledge-json must not overlap generated TXT outputs' in result.stderr
  assert result.stdout == '' and list(tmp_path.iterdir()) == []


def test_json_export_must_not_hit_default_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
  default = tmp_path / 'default'
  monkeypatch.setattr(run_interpreter, '_DEFAULT_OUTPUT_DIR', default)
  with pytest.raises(SystemExit) as raised:
    main(['knowledge', '--object', 'tiangan.ding', '--export-knowledge-base',
          '--export-knowledge-json', str(default / 'knowledge_base' / 'shishen' / '正官.txt')])
  assert raised.value.code == 2 and list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('alias', ['direct', 'symlink', 'hardlink'])
def test_text_export_cannot_overwrite_source(tmp_path: Path, alias: str) -> None:
  source = tmp_path / 'src.json'
  target = tmp_path / 'out' / 'knowledge_base' / 'tiangan' / '甲.txt'
  target.parent.mkdir(parents=True)
  shutil.copyfile(DEFAULT_SOURCE_PATH, source)
  if alias == 'direct':
    source = target
    shutil.copyfile(DEFAULT_SOURCE_PATH, source)
  elif alias == 'symlink':
    try:
      target.symlink_to(source)
    except (OSError, NotImplementedError):
      pytest.skip('symlinks unavailable')
  else:
    os.link(source, target)
  before = source.read_bytes()
  result = run_cli(tmp_path, 'knowledge', '--knowledge-source', str(source), '--export-knowledge-base', '--output-dir', 'out')
  assert result.returncode == 2 and 'Export must not overwrite the editing source' in result.stderr
  assert result.stdout == '' and source.read_bytes() == before
  assert [path.name for path in (tmp_path / 'out').rglob('*') if path.is_file()] == ['甲.txt']


@pytest.mark.parametrize('alias', ['direct', 'symlink', 'hardlink'])
@pytest.mark.parametrize('args, target', [
  (('knowledge', '--export-knowledge-base'), 'knowledge_base/tiangan/甲.txt'),
  (('knowledge', '--export-knowledge-base'), 'knowledge_base/shishen/正官.txt'),
  (('chart', '--seed', '1'), 'interpretation_examples/0.txt'),
])
def test_text_exports_cannot_overwrite_bundled(
  tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
  alias: str, args: tuple[str, ...], target: str,
) -> None:
  out = tmp_path / 'out'
  source, link = tmp_path / 'bundled.json', out / target
  link.parent.mkdir(parents=True)
  shutil.copyfile(DEFAULT_SOURCE_PATH, source)
  if alias == 'direct':
    source = link
    shutil.copyfile(DEFAULT_SOURCE_PATH, source)
  elif alias == 'symlink':
    try:
      link.symlink_to(source)
    except (OSError, NotImplementedError):
      pytest.skip('symlinks unavailable')
  else:
    os.link(source, link)
  monkeypatch.setattr(run_interpreter, 'DEFAULT_SOURCE_PATH', source)
  before = source.read_bytes()
  with pytest.raises(SystemExit) as raised:
    main([*args, '--output-dir', str(out)])
  assert raised.value.code == 2 and 'Export must not overwrite the editing source' in capsys.readouterr().err
  assert source.read_bytes() == before


@pytest.mark.parametrize('flag, dimension', sorted(_LIST_DIMENSIONS.items()))
def test_all_does_not_combine_with_conditions(tmp_path: Path, flag: str, dimension: str) -> None:
  value = KnowledgeBase.load().filter_values(dimension)[0]
  result = run_cli(tmp_path, 'knowledge', '--all', f'--{flag}', value)
  assert result.returncode == 2 and '--all cannot be combined with query conditions' in result.stderr
  assert result.stdout == '' and list(tmp_path.iterdir()) == []


def test_json_and_text_exports_side_by_side(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'knowledge', '--object', 'tiangan.ding', '--export-knowledge-json', 'out/k.json',
                '--export-knowledge-base', '--output-dir', 'out')
  assert result.returncode == 0 and result.stderr == ''
  library = KnowledgeBase.load()
  assert (tmp_path / 'out' / 'k.json').read_text(encoding='utf-8') == library.export_json(library.query(object_id='tiangan.ding'))
  assert len(list((tmp_path / 'out' / 'knowledge_base').rglob('*.txt'))) == 20


@pytest.mark.parametrize('extra', [
  ('--object', 'tiangan.ding'), ('--all',), ('--validate-knowledge',),
  ('--export-knowledge-json', 'out/k.json'), ('--export-knowledge-base',),
])
def test_list_values_stands_alone(tmp_path: Path, extra: tuple[str, ...]) -> None:
  result = run_cli(tmp_path, 'knowledge', '--list-values', 'topic', *extra)
  assert result.returncode == 2 and '--list-values only lists values' in result.stderr
  assert result.stdout == '' and list(tmp_path.iterdir()) == []


def test_bad_values_exit_with_an_error(tmp_path: Path) -> None:
  for args in (('--list-values', 'nope'), ('--applicability', 'maybe'), ('--knowledge-source', 'missing.json')):
    result = run_cli(tmp_path, 'knowledge', *args)
    assert result.returncode == 2 and 'error:' in result.stderr and 'Traceback' not in result.stderr


@pytest.mark.parametrize('args', [
  ('--validate-knowledge', '--export-knowledge-base'),
  ('--validate-knowledge', '--topic', '历史象'),
  ('--object', 'tiangan.ding'),
])
def test_knowledge_tasks_need_no_old_mode_flag(tmp_path: Path, args: tuple[str, ...], monkeypatch: pytest.MonkeyPatch) -> None:
  monkeypatch.setattr(run_interpreter, '_DEFAULT_OUTPUT_DIR', tmp_path / 'out')
  monkeypatch.chdir(tmp_path)
  assert main(['knowledge', *args]) == 0
  if '--export-knowledge-base' in args:
    assert len(list((tmp_path / 'out' / 'knowledge_base').rglob('*.txt'))) == 20
  else:
    assert list(tmp_path.iterdir()) == []
