# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from bazi import cli
from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase

from cli_runner import ROOT, KNOWLEDGE_BASE, run_cli, run_guarded_script, assert_cli_error


def test_knowledge_export_defaults_are_isolated(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  # cli was imported before chdir: the export directory must follow this call's cwd.
  monkeypatch.chdir(tmp_path)
  assert cli.main([
    'knowledge', '--export-knowledge-base',
  ]) == 0
  output = tmp_path / 'output_data'
  assert not (output / 'interpretation_examples').exists()
  assert len(list((output / 'knowledge_base' / 'tiangan').glob('*.txt'))) == 10
  assert len(list((output / 'knowledge_base' / 'shishen').glob('*.txt'))) == 10
  assert list(tmp_path.iterdir()) == [output]
  ding = (output / 'knowledge_base' / 'tiangan' / '丁.txt').read_text(encoding='utf-8')
  assert '丁为阴火。' in ding
  assert '丁火有烛灯之象' not in ding
  assert '仅供参考' not in ding
  assert '来源：' not in ding


def test_query_needs_no_birth_input_or_writes(tmp_path: Path) -> None:
  result = run_cli(
    tmp_path, 'knowledge', '--object', 'tiangan.ding', '--topic', '历史象',
    '--source', 'yuanhai_ziping_stem_symbols_p70', '--include-reference-only',
  )
  assert result.returncode == 0, result.stderr
  assert 'tiangan.ding.lamp_symbol' in result.stdout
  assert '丁火有烛灯之象。' in result.stdout and '第 70 页' in result.stdout
  assert '支持范围：' in result.stdout and '局限：' in result.stdout
  assert '出生时间：' not in result.stdout
  assert '丁为阴火。' not in result.stdout
  assert list(tmp_path.iterdir()) == []
  guarded = run_guarded_script(
    tmp_path,
    ('knowledge', '--object', 'tiangan.ding'),
  )
  assert guarded.returncode == 0, guarded.stderr


def test_manual_context_keeps_open_premises(tmp_path: Path) -> None:
  result = run_cli(
    tmp_path, 'knowledge', '--object', 'tiangan.geng',
    '--context', 'tiangan.geng_regulated_transit', '--topic', '性格',
    '--applicability', 'described', '--time-scope', '行运', '--include-reference-only',
  )
  assert result.returncode == 0, result.stderr
  for text in ('人工给定情境', '命盘适用性未判断', '后天有教养', '盘外前提', '有制有化尚未定义', '来源尚未核实'):
    assert text in result.stdout
  assert '出生时间：' not in result.stdout


def test_default_query_omits_reference_entries(tmp_path: Path) -> None:
  default = run_cli(tmp_path, 'knowledge', '--object', 'tiangan.ding')
  assert default.returncode == 0
  assert '丁为阴火。' in default.stdout and '烛灯' not in default.stdout


def test_ding_query_keeps_reference_text(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'knowledge', '--object', 'tiangan.ding', '--include-reference-only')
  assert result.returncode == 0 and result.stderr == ''
  assert '丁为阴火。' in result.stdout and '丁火有烛灯之象' in result.stdout and '仅供参考' in result.stdout
  assert list(tmp_path.iterdir()) == []


def test_validation_alone_is_read_only(tmp_path: Path) -> None:
  result = run_cli(tmp_path, 'knowledge', '--validate-knowledge')
  assert result.returncode == 0 and result.stderr == ''
  assert result.stdout == '校验通过：312 条目，23 来源见证，10 情境。\n'
  assert list(tmp_path.iterdir()) == []


def test_known_object_can_have_no_entries(tmp_path: Path) -> None:
  empty = run_cli(tmp_path, 'knowledge', '--object', 'wuxing.mu')
  assert empty.returncode == 0 and empty.stdout == '无匹配条目。\n'


def test_query_selects_reference_viewpoint(tmp_path: Path) -> None:
  variant = run_cli(
    tmp_path, 'knowledge', '--object', 'shensha.guoyin',
    '--viewpoint', 'WUXING_JINGJI', '--include-reference-only',
  )
  assert variant.returncode == 0 and '#194' in variant.stdout
  assert 'shensha.guoyin.modern' not in variant.stdout


def test_edit_validate_reload_cycle(tmp_path: Path) -> None:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  record = next(entry for entry in data['entries'] if entry['claim_id'] == 'tiangan.ding.lamp_symbol')
  record['limits'] = ['本次编辑的限度。']
  source = tmp_path / 'source.json'
  source.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  query = run_cli(
    tmp_path, 'knowledge', '--knowledge-source', str(source), '--validate-knowledge',
    '--object', 'tiangan.ding', '--topic', '历史象', '--include-reference-only',
  )
  assert query.returncode == 0, query.stderr
  assert '校验通过：312 条目，23 来源见证，10 情境。' in query.stdout
  assert '本次编辑的限度。' in query.stdout
  restored = KnowledgeBase.load(source)
  assert restored.entry('tiangan.ding.lamp_symbol').limits == ('本次编辑的限度。',)
  assert restored.sources == KNOWLEDGE_BASE.sources
  default = run_cli(tmp_path, 'knowledge', '--object', 'tiangan.ding', '--knowledge-source', str(source))
  assert default.returncode == 0 and default.stderr == ''
  assert default.stdout == ''.join(restored.render(entry) + '\n\n' for entry in restored.query(object_id='tiangan.ding'))
  assert '丁为阴火。' in default.stdout and '仅供参考' not in default.stdout
  again = run_cli(tmp_path, 'knowledge', '--all', '--knowledge-source', str(source), '--include-reference-only')
  assert again.returncode == 0 and '本次编辑的限度。' in again.stdout and '第 70 页' in again.stdout
  assert set(tmp_path.iterdir()) == {source}


@pytest.mark.parametrize('args,error', [
  (('--birth-time', '2000-01-01 12:00', '--gender', 'male'), 'unrecognized arguments'),
  (('--validate-knowledge', '--birth-time', ''), 'unrecognized arguments'),
  (('--seed', '42'), 'unrecognized arguments'), (('--count', '1'), 'unrecognized arguments'),
  (('--output-dir', 'output'), '--output-dir only applies with --export-knowledge-base'),
  (('--knowledge-source', 'source.json'), 'No such file or directory'),
  (('--object', 'typo'), 'Unknown object_id: typo'), (('--context', 'typo'), 'Unknown context_id: typo'),
  (('--applicability', 'typo'), 'invalid choice'),
  (('--validate-knowledge', '--knowledge-source', 'missing.json'), 'No such file or directory'),
])
def test_bad_inputs_do_not_create_exports(tmp_path: Path, args: tuple[str, ...], error: str) -> None:
  result = run_cli(tmp_path, 'knowledge', *args)
  assert result.returncode == 2
  assert 'error:' in result.stderr and 'Traceback' not in result.stderr
  assert_cli_error(result, 'knowledge', error)
  assert list(tmp_path.iterdir()) == []


def test_validation_rejects_corrupt_source(tmp_path: Path) -> None:
  source = tmp_path / 'corrupt.json'
  source.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
  result = run_cli(tmp_path, 'knowledge', '--validate-knowledge', '--knowledge-source', str(source))
  assert result.returncode == 2 and 'Duplicate JSON key' in result.stderr
  assert not (tmp_path / 'out.json').exists()


@pytest.mark.parametrize('optimized', [False, True])
@pytest.mark.parametrize('bad', ['surrogate', 'parser_limit', 'nested'])
def test_cli_text_failures_have_no_traceback(tmp_path: Path, optimized: bool, bad: str) -> None:
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  data['entries'][0]['text'] = '\ud800'
  if bad == 'surrogate':
    text = json.dumps(data)
  elif bad == 'parser_limit':
    text = '{"parser_limit": true}'
  else:
    text = '[' * 200 + '0' + ']' * 200
  source, target = tmp_path / 'source.json', tmp_path / 'out.json'
  source.write_text(text, encoding='utf-8')
  args = ('knowledge', '--knowledge-source', str(source), '--validate-knowledge')
  if bad == 'parser_limit':
    code = '''
import json
import sys

original_loads = json.loads
def loads(text, *args, **kwargs):
  if text == '{"parser_limit": true}':
    raise RecursionError('injected parser limit')
  return original_loads(text, *args, **kwargs)
json.loads = loads
sys.path.insert(0, sys.argv.pop(1))
from bazi.cli import main
raise SystemExit(main())
'''
    result = subprocess.run(
      [sys.executable, *(['-O'] if optimized else []), '-B', '-c', code,
       str(ROOT), *args],
      cwd=tmp_path, capture_output=True, text=True, encoding='utf-8', timeout=45, check=False,
    )
  else:
    result = run_cli(tmp_path, *args, optimized=optimized)
  assert result.returncode == 2 and 'Traceback' not in result.stderr
  if bad != 'nested':
    assert ('surrogate' if bad == 'surrogate' else 'depth') in result.stderr
  else:
    assert 'depth' in result.stderr or 'Expected JSON object' in result.stderr
  assert not target.exists()


@pytest.fixture
def knowledge_checkout(tmp_path: Path) -> Path:
  shutil.copytree(ROOT / 'bazi', tmp_path / 'bazi', ignore=shutil.ignore_patterns('__pycache__'))
  return tmp_path


def test_validation_reads_corrupt_bundled_source(knowledge_checkout: Path) -> None:
  corpus = knowledge_checkout / 'bazi/knowledge_data.json'
  custom = knowledge_checkout / 'custom.json'
  custom.write_bytes(corpus.read_bytes())
  corpus.write_text('{"schema_version":1,"schema_version":1}', encoding='utf-8')
  invalid = run_cli(knowledge_checkout, 'knowledge', '--validate-knowledge', checkout_root=knowledge_checkout)
  assert invalid.returncode == 2
  assert 'Duplicate JSON key' in invalid.stderr and 'Traceback' not in invalid.stderr
  valid = run_cli(knowledge_checkout, 'knowledge', '--validate-knowledge', '--knowledge-source', str(custom), checkout_root=knowledge_checkout)
  assert valid.returncode == 0 and '校验通过：' in valid.stdout
  corpus.unlink()
  independent = run_cli(
    knowledge_checkout, 'knowledge', '--knowledge-source', str(custom), '--validate-knowledge', checkout_root=knowledge_checkout,
  )
  assert independent.returncode == 0, independent.stderr
  assert KnowledgeBase.load(custom).entries == KNOWLEDGE_BASE.entries


@pytest.mark.parametrize('mutation', ['new-source', 'zhushi', 'removed-unused-source'])
def test_loading_is_independent_of_projection(
  knowledge_checkout: Path,
  mutation: str,
) -> None:
  corpus = knowledge_checkout / 'bazi/knowledge_data.json'
  data = json.loads(corpus.read_text(encoding='utf-8'))
  if mutation == 'new-source':
    witness = dict(data['sources'][1])
    witness.update(source_id='independent_probe', lineage='independent_probe')
    data['sources'].append(witness)
    next(entry for entry in data['entries'] if entry['claim_id'] == 'tiangan.ding.lamp_symbol')['sources'].append('independent_probe')
  elif mutation == 'zhushi':
    data['sources'][1]['text_layer'] = 'zhushi'
  else:
    data['sources'] = [source for source in data['sources'] if source['source_id'] != 'yuanhai_ziping_stem_table']
  corpus.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
  result = run_cli(knowledge_checkout, 'knowledge', '--validate-knowledge', checkout_root=knowledge_checkout)
  assert result.returncode == 0 and '校验通过：' in result.stdout
  imported = subprocess.run(
    [sys.executable, '-B', '-c', 'from bazi.knowledge import KnowledgeBase; KnowledgeBase.load()'],
    cwd=knowledge_checkout, capture_output=True, text=True, encoding='utf-8', check=False,
  )
  assert imported.returncode == 0, imported.stderr
  if mutation == 'new-source':
    queried = run_cli(
      knowledge_checkout, 'knowledge', '--source', 'independent_probe',
      '--include-reference-only', checkout_root=knowledge_checkout,
    )
    assert queried.returncode == 0, queried.stderr
    assert '条目：tiangan.ding.lamp_symbol' in queried.stdout
    assert '来源：independent_probe' in queried.stdout


@pytest.mark.parametrize('source_id', tuple(KNOWLEDGE_BASE.sources))
def test_cli_can_query_every_registered_source(tmp_path: Path, source_id: str) -> None:
  result = run_cli(tmp_path, 'knowledge', '--source', source_id, '--include-reference-only')
  assert result.returncode == 0, result.stderr
  selected = KNOWLEDGE_BASE.query(source_id=source_id, include_reference_only=True)
  assert result.stdout == ''.join(KNOWLEDGE_BASE.render(entry) + '\n\n' for entry in selected) if selected else result.stdout == '无匹配条目。\n'


@pytest.mark.parametrize('show_sources', [False, True])
def test_chart_txt_share_subject_projection(knowledge_checkout: Path, show_sources: bool) -> None:
  tmp_path = knowledge_checkout
  data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  data['entries'].reverse()
  corpus = json.dumps(data, ensure_ascii=False)
  (knowledge_checkout / 'bazi/knowledge_data.json').write_text(corpus, encoding='utf-8')
  knowledge = KnowledgeBase.load(knowledge_checkout / 'bazi/knowledge_data.json')
  relation = KNOWLEDGE_BASE.entry('legacy.shishen.SH-052')
  assert relation in KNOWLEDGE_BASE.query(object_id='shishen.qisha', include_reference_only=True)
  result = run_cli(
    tmp_path, 'chart', '--birth-time', '2000-01-03 12:00', '--gender', 'female', '--include-reference-only',
    *(['--show-sources'] if show_sources else []),
    '--output-dir', str(tmp_path),
    checkout_root=knowledge_checkout,
  )
  assert result.returncode == 0, result.stderr
  exported = run_cli(tmp_path, 'knowledge', '--include-reference-only', '--export-knowledge-base',
                      '--output-dir', str(tmp_path), *(['--show-sources'] if show_sources else []),
                       checkout_root=knowledge_checkout)
  assert exported.returncode == 0 and exported.stdout == '' and exported.stderr == ''
  for subject, kind in (('七杀', 'shishen.qisha'), ('食神', 'shishen.shishen')):
    text = (tmp_path / 'knowledge_base/shishen' / (subject + '.txt')).read_text(encoding='utf-8')
    expected = knowledge.render_subject(kind, include_reference_only=True, show_sources=show_sources)
    assert text == subject + '知识条目：\n' + expected + '\n'
    assert expected in result.stdout
    selected = tuple(entry for entry in knowledge.query(object_id=kind, include_reference_only=True)
                     if entry.legacy is None or entry.legacy.object_id == kind)
    positions = tuple(text.index(entry.text) for entry in selected)
    assert positions == tuple(sorted(positions))
  assert relation.text not in KNOWLEDGE_BASE.render_subject('shishen.qisha', include_reference_only=True)
  assert relation.text in KNOWLEDGE_BASE.render_subject('shishen.shishen', include_reference_only=True)
