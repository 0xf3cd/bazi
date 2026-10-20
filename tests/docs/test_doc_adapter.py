# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

from markdown_it.renderer import RendererHTML
from myst_parser.config.main import MdParserConfig
from myst_parser.parsers.mdit import create_md_parser

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'docs/_ext'))
sys.path.insert(0, str(ROOT))

from house_docstrings import prepare_markdown, source_attribute_docs
from run_doc_checks import EXAMPLE_GROUPS, Page, check_doctests, check_header_paragraphs
import run_docs


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


def doctest_output(singular):
  sections = []
  word = 'test' if singular else 'tests'
  for document, groups in EXAMPLE_GROUPS.items():
    sections.append(f'Document: {document}\n------------------------------\n')
    sections.extend(f'   1 {word} in {group}\n' for group in sorted(groups))
  count = sum(map(len, EXAMPLE_GROUPS.values()))
  return ''.join(sections) + f'Doctest summary\n===============\n   {count} tests\n     0 failures in tests\n     0 failures in setup code\n     0 failures in cleanup code\n'


@pytest.mark.parametrize('singular', [False, True])
def test_doctest_count_accepts_both_wordings(tmp_path, singular):
  (tmp_path / 'output.txt').write_text(doctest_output(singular), encoding='utf-8')
  assert check_doctests(tmp_path) == sum(map(len, EXAMPLE_GROUPS.values()))


@pytest.mark.parametrize('old,new', [
  ('1 tests in quickstart-chart', '1 tests in omitted-chart'),
  pytest.param(f'{sum(map(len, EXAMPLE_GROUPS.values()))} tests', '0 tests', id='total-count'),
  ('0 failures in setup code', '1 failure in setup code'),
  ('0 failures in cleanup code', '1 failure in cleanup code'),
])
def test_missing_examples_failed_setup_rejected(tmp_path, old, new):
  output = doctest_output(False)
  assert old in output
  (tmp_path / 'output.txt').write_text(output.replace(old, new, 1), encoding='utf-8')
  with pytest.raises(AssertionError):
    check_doctests(tmp_path)


@pytest.fixture
def build_environment(tmp_path, monkeypatch):
  root = tmp_path / 'project'
  (root / 'docs').mkdir(parents=True)
  (root / 'docs/index.md').write_text('# Example\n', encoding='utf-8')
  (root / 'CONTRIBUTING.md').write_text('# Contributing\n', encoding='utf-8')
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
    return subprocess.CompletedProcess(command, 0)

  commands = Mock(side_effect=run)
  monkeypatch.setattr(run_docs.subprocess, 'run', commands)
  output = tmp_path / 'output'
  if accepted:
    run_docs.build(output, label)
    assert json.loads((output / 'html/build.json').read_text(encoding='utf-8')) == {
      'version': label, 'commit': sha, 'dirty': bool(status), 'python': sys.version.split()[0],
    }
    assert commands.call_count == 3
  else:
    with pytest.raises(ValueError, match='clean checkout of the matching tag'):
      run_docs.build(output, label)
    assert not output.exists()
    commands.assert_not_called()
  expected = [('rev-parse', 'HEAD'), ('status', '--porcelain')]
  if label != 'dev':
    expected.append(('rev-parse', f'refs/tags/{label}^{{}}'))
  assert [call.args for call in git.call_args_list] == expected
