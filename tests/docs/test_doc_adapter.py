# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import UTC, datetime
from unittest.mock import Mock
from typing import Any, cast

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

from markdown_it.renderer import RendererHTML
from docutils import nodes
from docutils.utils import new_document
from myst_parser.config.main import MdParserConfig
from myst_parser.parsers.mdit import create_md_parser
from sphinx import addnodes

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'docs/_ext'))
sys.path.insert(0, str(ROOT))

from house_docstrings import HouseDocstring, prepare_markdown, render_attribute_values, source_attribute_docs
from run_doc_checks import TASK_EXAMPLES, Page, check_doctests, check_header_paragraphs, source_doctests
from source_links import missing_reference
import run_docs


@pytest.mark.parametrize('target, plain', [
  ('bazi.common.K', True),
  ('bazi.data_types.T', True),
  ('bazi.utils.relation_discovery.T', True),
  ('bazi.common.check_declared_types', False),
  ('bazi.utils.relation_discovery.RelationDiscovery', False),
  ('bazi.common.missing', False),
  ('unknown.T', False),
])
def test_only_internal_typevars_use_plain_text(target, plain):
  content = nodes.literal('', target.rsplit('.', 1)[-1])
  node = addnodes.pending_xref('', reftarget=target)
  result = missing_reference(Mock(), Mock(), node, content)
  assert result is (content if plain else None)


@pytest.mark.parametrize('mode', ['__main__', 'run_docs'])
@pytest.mark.parametrize('version', ['3.11', '3.12'])
def test_version_guard_is_only_for_the_cli(mode: str, version: str) -> None:
  code = '''import runpy
import sys
sys.version_info = tuple(map(int, sys.argv[3].split('.'))) + (0, 'final', 0)
try:
  runpy.run_path(sys.argv[1], run_name=sys.argv[2])
except SystemExit:
  assert 'markdown_it' not in sys.modules
  raise
'''
  result = subprocess.run(
    [sys.executable, '-c', code, str(ROOT / 'run_docs.py'), mode, version],
    capture_output=True, text=True, encoding='utf-8', check=False,
  )
  assert result.returncode == (2 if mode == '__main__' else 0), result.stderr
  if mode == '__main__':
    assert 'Documentation builds require Python 3.13 or later' in result.stderr
    assert 'Traceback' not in result.stderr


@pytest.mark.parametrize('header', ['Args', 'Return', 'Returns', 'Note', 'Examples', 'Raises', 'Usage'])
def test_plain_paragraph_after_each_header(header):
  parser = create_md_parser(MdParserConfig(), RendererHTML)
  assert prepare_markdown(['摘要', header + ':', '正文'], parser) == ['摘要', '', header + ':', '', '正文']


@pytest.mark.parametrize('source', [
  ['```text', 'Args:', '- literal', 'Returns:', 'Usage:'],
  ['<pre>', 'Args:', '- literal', 'Returns:', 'Usage:', '</pre>'],
  ['<div>', 'Args:', 'Usage:'],
  ['- first', '  Return: continuation', '- second'],
  ['- first', 'lazy continuation', '- second'],
])
def test_code_html_lazy_continuations_unchanged(source):
  parser = create_md_parser(MdParserConfig(), RendererHTML)
  assert prepare_markdown(source, parser) == source


@pytest.mark.parametrize('source, expected', [
  (['摘要', 'Usage: 调用 bazi.Bazi.create。'], ['摘要', '', 'Usage: 调用 bazi.Bazi.create。']),
  (['Note: 单行说明', '第二行仍属同一段'], ['Note: 单行说明', '第二行仍属同一段']),
])
def test_inline_headers_stay_in_their_paragraph(source, expected):
  parser = create_md_parser(MdParserConfig(), RendererHTML)
  assert prepare_markdown(source, parser) == expected


def test_colon_fence_uses_enabled_parser():
  parser = create_md_parser(MdParserConfig(enable_extensions={'colon_fence'}), RendererHTML)
  source = [':::{code-block} text', 'Args:', '- literal', 'Returns:', ':::']
  assert prepare_markdown(source, parser) == source


@pytest.mark.parametrize('source', ['guide.md', None])
def test_directive_requires_a_source_path(monkeypatch: pytest.MonkeyPatch, source: str | None) -> None:
  directive = cast(Any, HouseDocstring.__new__(HouseDocstring))
  directive.get_source_info = Mock(return_value=(source, 1))
  directive.error = Mock(return_value=ValueError('missing source'))
  directive.state = Mock()
  directive.content = []
  document = Mock()
  document.children = []
  create = Mock(return_value=document)
  monkeypatch.setattr('house_docstrings.new_document', create)
  monkeypatch.setattr('house_docstrings.create_md_parser', Mock(return_value=Mock(parse=Mock(return_value=[]))))
  monkeypatch.setattr('house_docstrings.MystParser', Mock())
  if source is None:
    with pytest.raises(ValueError, match='missing source'):
      directive.run()
    create.assert_not_called()
    directive.error.assert_called_once_with('Documentation directive has no source path')
  else:
    assert directive.run() == []
    create.assert_called_once_with(source, settings=directive.state.document.settings)
    directive.error.assert_not_called()


def test_ownership_complete_without_imports(tmp_path):
  package = tmp_path / 'sample'
  package.mkdir()
  (package / '__init__.py').write_text("'''Module purpose, not the next assignment.'''\nx = 1\n", encoding='utf-8')
  (package / 'items.py').write_text(
    "raise RuntimeError('Do not import this source')\n"
    "\n'''Above description.'''\nabove = 1\n"
    "\nbelow = 2\n'''Below description.'''\n"
    "\nempty = 3\n"
    "class Nested:\n  '''Class purpose.'''\n  value = 4\n",
    encoding='utf-8',
  )
  assert source_attribute_docs(package) == {
    'sample.x': [], 'sample.items.above': ['Above description.'],
    'sample.items.below': ['Below description.'], 'sample.items.empty': [], 'sample.items.Nested.value': [],
  }


def test_ambiguous_source_ownership_is_rejected(tmp_path):
  (tmp_path / 'items.py').write_text("first = 1\n'''Ambiguous.'''\nsecond = 2\n", encoding='utf-8')
  with pytest.raises(ValueError, match='Ambiguous attribute description'):
    source_attribute_docs(tmp_path)


@pytest.mark.parametrize('name, value, expected', [
  ('bazi.school.BaziSchool.xing_def', '1', 'DizhiRules.XingDef.LOOSE'),
  ('bazi.school.BaziSchool.wenchang_def', '0', 'ShenshaRules.WenchangDef.XIN_ZI'),
  ('bazi.rules.DizhiRelationDefinitions.anhe_def', '1', 'DizhiRules.AnheDef.NORMAL_EXTENDED'),
  ('bazi.rules.ShenshaRules.TIANYI', '{many entries}', None),
  ('bazi.rules.ShenshaRules.TianyiDef.GENG_WITH_JIA_WU', '0', '0'),
  ('bazi.defines.tiangan.Tiangan.JIA', "'甲'", "'甲'"),
])
def test_field_defaults_and_tables_render(name, value, expected):
  document = new_document('api')
  signature = addnodes.desc_signature(ids=[name])
  annotation = addnodes.desc_annotation('', nodes.Text(' = ' + value))
  type_annotation = addnodes.desc_annotation('', nodes.Text(': type'))
  signature.extend([type_annotation, annotation])
  document += signature
  render_attribute_values(Mock(), document)
  assert signature[0] is type_annotation
  assert [node.astext() for node in signature.children] == (
    [': type'] if expected is None else [': type', ' = ' + expected]
  )


def api_pages(*paragraphs: str) -> dict[str, Page]:
  page = Page()
  page.feed('<html><body>' + ''.join(paragraphs) + '</body></html>')
  return {'api/example.html': page}


def test_bare_header_glued_to_next_is_rejected():
  with pytest.raises(AssertionError, match='api/example.html'):
    check_header_paragraphs(api_pages('<p>Examples:\n正文。</p>'))


def test_bare_header_glued_to_prev_is_rejected():
  with pytest.raises(AssertionError, match='api/example.html'):
    check_header_paragraphs(api_pages('<p>摘要。\nExamples:</p>', '<p>正文。</p>'))


@pytest.mark.parametrize('paragraphs', [
  ['<p>Examples:</p>', '<p>正文。</p>'],
  ['<p>Usage: 调用 bazi.Bazi.create。</p>', '<p>Examples:</p>'],
  ['<p>摘要。</p>', '<p>Args: 返回年柱。</p>', '<p>Returns:</p>'],
])
def test_split_inline_headers_accepted(paragraphs):
  assert check_header_paragraphs(api_pages(*paragraphs)) > 0


def test_only_api_pages_are_checked():
  glued = Page()
  glued.feed('<p>Examples:\n知识原文。</p>')
  clean = Page()
  clean.feed('<p>Examples:</p>')
  assert check_header_paragraphs({'guides/knowledge.html': glued, 'api/example.html': clean}) == 1


@pytest.fixture
def doctest_source(tmp_path):
  source = tmp_path / 'source'
  (source / 'guides').mkdir(parents=True)
  (source / 'readme-example.rst').write_text(
    '.. testsetup:: readme-first\n\n   x = 1\n\n'
    '.. testcode:: readme-first\n\n   assert x == 1\n\n'
    '.. testcleanup:: readme-first\n\n   del x\n',
    encoding='utf-8',
  )
  for name, groups in (
    ('quickstart', ('quickstart-chart',)), ('relations-transits', ('transits-query',)),
    ('calendar', ('calendar-lunar-roundtrip',)),
    ('integration', ('integration-context',)), ('knowledge', ('load', 'edit')),
  ):
    (source / 'guides' / (name + '.md')).write_text(
      ''.join('```{testcode} ' + group + '\nassert True\n```\n\n' for group in groups),
      encoding='utf-8',
    )
  with (source / 'guides/knowledge.md').open('a', encoding='utf-8') as stream:
    stream.write('```{testsetup} edit\nx = 1\n```\n\n```{testcleanup} edit\ndel x\n```\n')
  return source


def doctest_output(singular=False):
  sections = []
  word = 'test' if singular else 'tests'
  groups_by_document = {
    'readme-example': ('readme-first', 'readme-first (cleanup code)'),
    'guides/quickstart': ('quickstart-chart',),
    'guides/calendar': ('calendar-lunar-roundtrip',),
    'guides/relations-transits': ('transits-query',),
    'guides/integration': ('integration-context',),
    'guides/knowledge': ('load', 'edit', 'edit (cleanup code)'),
  }
  for document, groups in groups_by_document.items():
    sections.append(f'Document: {document}\n------------------------------\n')
    sections.extend(f'   1 {word} in {group}\n' for group in sorted(groups))
  return ''.join(sections) + 'Doctest summary\n===============\n   7 tests\n     0 failures in tests\n     0 failures in setup code\n     0 failures in cleanup code\n'


@pytest.mark.parametrize('singular', [False, True])
def test_doctest_count_accepts_both_wordings(tmp_path, doctest_source, singular):
  (tmp_path / 'output.txt').write_text(doctest_output(singular), encoding='utf-8')
  assert check_doctests(tmp_path, doctest_source) == 7


@pytest.mark.parametrize('phase', ['setup', 'cleanup'])
def test_doctest_phases_are_not_examples(tmp_path, doctest_source, phase):
  with (doctest_source / 'guides/quickstart.md').open('a', encoding='utf-8') as stream:
    stream.write('```{test' + phase + '} quickstart-chart\npass\n```\n')
  output = doctest_output(False).replace(
    '   1 tests in quickstart-chart\n',
    f'   1 tests in quickstart-chart\n   1 tests in quickstart-chart ({phase} code)\n',
  )
  (tmp_path / 'output.txt').write_text(output, encoding='utf-8')
  assert check_doctests(tmp_path, doctest_source) == 7


@pytest.mark.parametrize('phase', ['setup', 'cleanup'])
def test_orphan_doctest_phase_is_rejected(tmp_path, doctest_source, phase):
  output = doctest_output(False).replace(
    '   1 tests in readme-first\n',
    f'   1 tests in readme-first\n   1 tests in missing-example ({phase} code)\n',
  )
  (tmp_path / 'output.txt').write_text(output, encoding='utf-8')
  with pytest.raises(AssertionError, match='Orphan doctest'):
    check_doctests(tmp_path, doctest_source)


@pytest.mark.parametrize('old,new', [
  ('1 tests in quickstart-chart', '1 tests in omitted-chart'),
  ('7 tests', '0 tests'),
  ('0 failures in tests', '1 failure in tests'),
  ('0 failures in setup code', '1 failure in setup code'),
  ('0 failures in cleanup code', '1 failure in cleanup code'),
  ('   1 tests in quickstart-chart\n', ''),
  ('   1 tests in quickstart-chart\n', '   1 tests in quickstart-chart\n   1 tests in extra\n'),
  ('   1 tests in quickstart-chart\n', '   1 tests in quickstart-chart\n   1 tests in quickstart-chart (setup code)\n'),
  ('   1 tests in quickstart-chart\n', '   1 tests in quickstart-chart\n   1 tests in quickstart-chart\n'),
  ('Document: guides/quickstart\n------------------------------\n', 'Document: guides/quickstart\n---\nDocument: guides/quickstart\n---\n'),
  ('   1 tests in edit (cleanup code)\n', ''),
])
def test_missing_examples_failed_setup_rejected(tmp_path, doctest_source, old, new):
  output = doctest_output(False)
  assert old in output
  (tmp_path / 'output.txt').write_text(output.replace(old, new, 1), encoding='utf-8')
  with pytest.raises(AssertionError):
    check_doctests(tmp_path, doctest_source)


@pytest.mark.parametrize('suffix', ['.md', '.rst'])
def test_optional_examples_follow_source(tmp_path, doctest_source, suffix):
  extra = doctest_source / ('extra' + suffix)
  extra.write_text(
    '```{testcode} extra\nassert True\n```\n' if suffix == '.md' else '.. testcode:: extra\n\n   assert True\n',
    encoding='utf-8',
  )
  output = doctest_output().replace('Doctest summary', 'Document: extra\n---\n   1 tests in extra\nDoctest summary').replace('7 tests', '8 tests')
  (tmp_path / 'output.txt').write_text(output, encoding='utf-8')
  assert check_doctests(tmp_path, doctest_source) == 8
  extra.unlink()
  (tmp_path / 'output.txt').write_text(doctest_output(), encoding='utf-8')
  assert check_doctests(tmp_path, doctest_source) == 7


@pytest.mark.parametrize('document, group', [
  (document, group) for document, groups in TASK_EXAMPLES.items() for group in sorted(groups)
])
def test_task_removal_cannot_shrink_both_sides(tmp_path, doctest_source, document, group):
  name, _, phase = group.partition(' (')
  phase = phase.removesuffix(' code)') or 'code'
  suffix = '.rst' if document == 'readme-example' else '.md'
  path = doctest_source / (document + suffix)
  text = path.read_text(encoding='utf-8')
  if phase == 'code':
    kinds = '(?:code|setup|cleanup)'
  else:
    kinds = phase
  pattern = (
    r'^\.\. test' + kinds + ':: ' + re.escape(name) + r'\n(?:\n|   [^\n]*\n)*'
    if suffix == '.rst' else r'^```\{test' + kinds + r'\} ' + re.escape(name) + r'\n.*?```\n'
  )
  changed = re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL)
  assert changed != text
  path.write_text(changed, encoding='utf-8')
  output = doctest_output()
  output = re.sub(r'^   1 tests in ' + re.escape(name) + (r'(?: \((?:setup|cleanup) code\))?' if phase == 'code' else ' \\(' + phase + r' code\)') + r'\n', '', output, flags=re.MULTILINE)
  if phase == 'code':
    output = output.replace('6 tests', '5 tests')
  (tmp_path / 'output.txt').write_text(output, encoding='utf-8')
  with pytest.raises(AssertionError, match='Missing task examples'):
    check_doctests(tmp_path, doctest_source)


def test_group_counts_and_shared_setup(doctest_source):
  (doctest_source / 'extra.md').write_text(
    '```{testcode}\nassert True\n```\n\n```{testcode}\nassert True\n```\n\n'
    '```{testcode} first, second\nassert True\n```\n\n```{testsetup} *\nx = 1\n```\n\n'
    '```text\n.. testcode:: not-a-directive\n```\n',
    encoding='utf-8',
  )
  assert source_doctests(doctest_source)['extra'] == {
    'default': 2, 'first': 1, 'second': 1,
    'default (setup code)': 1, 'first (setup code)': 1, 'second (setup code)': 1,
  }


@pytest.mark.parametrize('defect', ['orphan', 'duplicate-document'])
def test_source_groups_reject_ambiguous_input(doctest_source, defect):
  if defect == 'orphan':
    (doctest_source / 'extra.md').write_text('```{testsetup} missing\npass\n```\n', encoding='utf-8')
  else:
    (doctest_source / 'readme-example.md').write_text('```{testcode} other\nassert True\n```\n', encoding='utf-8')
  with pytest.raises(AssertionError, match='Orphan source|Duplicate doctest source'):
    source_doctests(doctest_source)


@pytest.fixture
def build_environment(tmp_path, monkeypatch):
  root = tmp_path / 'project'
  (root / 'docs').mkdir(parents=True)
  (root / 'docs/index.md').write_text('# Example\n', encoding='utf-8')
  (root / 'CONTRIBUTING.md').write_text('# Contributing\n', encoding='utf-8')
  (root / 'RELEASE_NOTES.md').write_text('# Release notes\n', encoding='utf-8')
  (root / 'API_CONTRACT.md').write_text('# Contract\n', encoding='utf-8')
  (root / 'README.md').write_text("```python\nprint('example')\n```\n\n```text\nexample\n```\n", encoding='utf-8')
  monkeypatch.setattr(run_docs, 'ROOT', root)
  monkeypatch.setattr(run_docs, 'git_output', lambda *args: 'a' * 40 if args[0] == 'rev-parse' else '')
  monkeypatch.setattr(run_docs, 'generate_api', lambda source: None)
  return root


@pytest.mark.parametrize('failure', ['html', 'doctest', 'check', None])
def test_build_only_promotes_a_complete_candidate(build_environment, tmp_path, monkeypatch, failure):
  output = tmp_path / 'output'

  def run(command, **kwargs):
    if '-m' in command:
      builder = command[command.index('-b') + 1]
      destination = Path(command[-1])
      destination.mkdir(parents=True)
      (destination / 'result.txt').write_text(builder, encoding='utf-8')
    else:
      builder = 'check'
      source = Path(command[-3])
      assert (source / 'readme-example.rst').is_file()
      assert (source / 'index.md').is_file()
    if builder == failure:
      raise subprocess.CalledProcessError(1, command)
    return subprocess.CompletedProcess(command, 0)

  monkeypatch.setattr(run_docs.subprocess, 'run', run)
  if failure:
    with pytest.raises(subprocess.CalledProcessError):
      run_docs.build(output, 'dev')
    assert not output.exists()
  else:
    run_docs.build(output, 'dev')
    assert (output / 'html/result.txt').read_text(encoding='utf-8') == 'html'
    assert (output / 'doctest/result.txt').read_text(encoding='utf-8') == 'doctest'
    assert (output / 'html/build.json').is_file()
  assert not list(tmp_path.glob('.bazi-docs-*'))


def test_rejected_output_keeps_existing_files(build_environment, tmp_path):
  output = tmp_path / 'output'
  output.mkdir()
  marker = output / 'keep.txt'
  marker.write_bytes(b'keep exactly')
  with pytest.raises(ValueError, match='must be empty'):
    run_docs.build(output, 'dev')
  assert marker.read_bytes() == b'keep exactly'
  assert set(output.iterdir()) == {marker}


def test_release_copy_and_contribution_links(build_environment, tmp_path, monkeypatch):
  root = build_environment
  (root / 'CONTRIBUTING.md').write_text(
    '[构建](docs/versioning.md)\n[工件](RELEASING.md#本地保留已验证工件)\n[表](bazi/table.py)\n',
    encoding='utf-8',
  )
  (root / 'RELEASE_NOTES.md').write_text('# 发布说明\n\n保留 `reference_ids` 与原有标点。\n', encoding='utf-8')

  def run(command, **kwargs):
    if '-m' in command:
      source = Path(command[-2])
      assert (source / 'release-notes.md').read_bytes() == (root / 'RELEASE_NOTES.md').read_bytes()
      contributing = (source / 'contributing.md').read_text(encoding='utf-8')
      assert '](versioning.md)' in contributing and '](docs/versioning.md)' not in contributing
      assert f'](https://github.com/0xf3cd/bazi/blob/{"a" * 40}/RELEASING.md#本地保留已验证工件)' in contributing
      assert f'](https://github.com/0xf3cd/bazi/blob/{"a" * 40}/bazi/table.py)' in contributing
      Path(command[-1]).mkdir(parents=True)
    return subprocess.CompletedProcess(command, 0)

  monkeypatch.setattr(run_docs.subprocess, 'run', run)
  run_docs.build(tmp_path / 'output', 'dev')


def test_output_inside_source_is_rejected(build_environment):
  with pytest.raises(ValueError, match='outside its source'):
    run_docs.build(build_environment / 'docs/output', 'dev')


@pytest.mark.parametrize('label, status, tagged_sha, accepted', [
  ('v99.0.0', '', 'a' * 40, True),
  ('v99.0.0', ' M docs/index.md', 'a' * 40, False),
  ('v99.0.0', '', 'b' * 40, False),
  ('dev', '', None, True),
  ('dev', ' M docs/index.md', None, True),
])
def test_build_checks_tag_records_source_state(
  build_environment, tmp_path, monkeypatch, label, status, tagged_sha, accepted,
):
  sha = 'a' * 40
  timestamps = []
  git = Mock(side_effect=lambda *args: {
    ('rev-parse', 'HEAD'): sha,
    ('status', '--porcelain'): status,
    ('rev-parse', f'refs/tags/{label}^{{}}'): tagged_sha,
  }[args])
  monkeypatch.setattr(run_docs, 'git_output', git)

  def run(command, **kwargs):
    if '-m' in command:
      Path(command[-1]).mkdir(parents=True)
      version_page = (Path(command[-2]) / 'versions.md').read_text(encoding='utf-8')
      assert '](https://0xf3cd.github.io/bazi/versions/)' in version_page
      timestamps.append(version_page.split('构建时间（UTC）：', 1)[1].split('。', 1)[0])
    return subprocess.CompletedProcess(command, 0)

  commands = Mock(side_effect=run)
  monkeypatch.setattr(run_docs.subprocess, 'run', commands)
  output = tmp_path / 'output'
  if accepted:
    started = datetime.now(UTC).replace(microsecond=0)
    run_docs.build(output, label)
    assert json.loads((output / 'html/build.json').read_text(encoding='utf-8')) == {
      'version': label, 'commit': sha, 'dirty': bool(status), 'python': sys.version.split()[0],
      'built': timestamps[0],
    }
    assert commands.call_count == 3
    assert len(timestamps) == 2 and timestamps[0] == timestamps[1]
    assert re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', timestamps[0])
    assert started <= datetime.strptime(timestamps[0], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC) <= datetime.now(UTC)
  else:
    with pytest.raises(ValueError, match='clean checkout of the matching tag'):
      run_docs.build(output, label)
    assert not output.exists()
    commands.assert_not_called()
  expected = [('rev-parse', 'HEAD'), ('status', '--porcelain')]
  if label != 'dev':
    expected.append(('rev-parse', f'refs/tags/{label}^{{}}'))
  assert [call.args for call in git.call_args_list] == expected
