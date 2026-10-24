# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import os
import runpy
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from myst_parser.mdit_to_docutils.base import compute_unique_slug

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import run_docs
import run_docs_site
from run_package_checks import source_files


def _check_navigation(source: Path, root: Path) -> None:
  links = [
    child.attrGet('href') or ''
    for token in MarkdownIt('commonmark').parse(source.read_text(encoding='utf-8'))
    for child in token.children or () if child.type == 'link_open'
  ]
  assert links
  for link in links:
    assert isinstance(link, str)
    url = urlsplit(link)
    if link.startswith('#'):
      path = source
    elif url.scheme or url.netloc:
      assert url.scheme == 'https' and url.netloc, link
      if not link.startswith('https://github.com/0xf3cd/bazi/blob/main/'):
        continue
      path = root / unquote(url.path.removeprefix('/0xf3cd/bazi/blob/main/'))
    else:
      path = source.parent / unquote(url.path)
    assert path.resolve().is_relative_to(root) and path.is_file(), link
    if url.fragment:
      headings = SyntaxTreeNode(MarkdownIt('commonmark').parse(path.read_text(encoding='utf-8')))
      slugs: set[str] = set()
      for heading in headings.children:
        if heading.type == 'heading':
          slugs.add(compute_unique_slug(heading, slugs))
      assert unquote(url.fragment) in slugs, (source, link, slugs)


@pytest.mark.parametrize('name', [
  'README.md', 'RELEASE_NOTES.md', 'API_CONTRACT.md', 'AGENTS.md', 'CONTRIBUTING.md',
  'docs/guides/quickstart.md', 'docs/guides/integration.md', 'docs/guides/configuration.md',
])
def test_navigation_links_resolve(name):
  _check_navigation(ROOT / name, ROOT)


@pytest.mark.parametrize('heading, valid', [('从 v2.2.0 迁移到 v2.3.0', True), ('迁移指南', False)])
@pytest.mark.parametrize('prefix', ['https://github.com/0xf3cd/bazi/blob/main/', '../'])
def test_navigation_detects_heading_rename(tmp_path, heading, valid, prefix):
  target = tmp_path / 'target.md'
  target.write_text('# ' + heading + '\n', encoding='utf-8')
  (tmp_path / 'docs').mkdir()
  source = tmp_path / 'docs/README.md'
  source.write_text(
    f'[迁移]({prefix}target.md#从-v220-迁移到-v230)\n',
    encoding='utf-8',
  )
  if not valid:
    with pytest.raises(AssertionError):
      _check_navigation(source, tmp_path)
  else:
    _check_navigation(source, tmp_path)


@pytest.mark.parametrize('between', ['说明文字。\n', '```sh\npython first_chart.py\n```\n'])
def test_readme_output_must_follow_code(monkeypatch, tmp_path, between):
  (tmp_path / 'README.md').write_text(
    '```python\nprint("example")\n```\n' + between + '```text\nexample\n```\n',
    encoding='utf-8',
  )
  monkeypatch.setattr(run_docs, 'ROOT', tmp_path)
  with pytest.raises(ValueError, match='must be followed by a text output fence'):
    run_docs.generate_readme_example(tmp_path)


@pytest.mark.parametrize('failing', [False, True])
def test_readme_doctest_preserves_caller(monkeypatch, tmp_path, failing):
  project = tmp_path / 'project'
  project.mkdir()
  caller = tmp_path / 'caller'
  caller.mkdir()
  marker = caller / 'chart.txt'
  marker.write_bytes(b'keep exactly')
  temporary = tmp_path / 'temporary'
  temporary.mkdir()
  body = "from pathlib import Path\nPath('chart.txt').write_text('example', encoding='utf-8')\nprint('example')\n"
  if failing:
    body += "raise RuntimeError('sample failure')\n"
  (project / 'README.md').write_text('```python\n' + body + '```\n\n```text\nexample\n```\n', encoding='utf-8')
  (project / 'conf.py').write_text('project = "example"\nroot_doc = "readme-example"\nextensions = ["sphinx.ext.doctest"]\n', encoding='utf-8')
  monkeypatch.setattr(run_docs, 'ROOT', project)
  run_docs.generate_readme_example(project)
  with (project / 'readme-example.rst').open('a', encoding='utf-8') as stream:
    stream.write(
      '\n.. testcode:: after-readme\n\n   from pathlib import Path\n'
      f'   print(Path.cwd() == Path({str(caller)!r}))\n'
      '\n.. testoutput:: after-readme\n\n   True\n',
    )
  output = tmp_path / 'output'
  result = subprocess.run(
    [sys.executable, '-B', '-m', 'sphinx', '-E', '-b', 'doctest', '-n', '-W', '--keep-going',
     '-d', str(tmp_path / 'doctrees'), str(project), str(output)],
    cwd=caller, env={**os.environ, 'TMPDIR': str(temporary)}, capture_output=True, text=True, encoding='utf-8',
    timeout=60, check=False,
  )
  assert result.returncode == int(failing), result.stdout + result.stderr
  report = (output / 'output.txt').read_text(encoding='utf-8')
  assert '0 failures in setup code' in report and '0 failures in cleanup code' in report
  assert 'after-readme' in report
  if failing:
    assert 'RuntimeError: sample failure' in report
  assert marker.read_bytes() == b'keep exactly'
  assert set(caller.iterdir()) == {marker}
  assert not list(temporary.iterdir())


def test_release_label_grammar_is_shared():
  assert run_docs.RELEASE_LABEL is run_docs_site.RELEASE_LABEL


@pytest.mark.parametrize('label', ['v01.2.3', 'v1.02.3', 'v1.2.03', 'v1.2.3-rc1', '../v1.2.3', 'main'])
def test_builder_rejects_noncanonical_labels(monkeypatch, tmp_path, label):
  monkeypatch.setattr(run_docs, 'git_output', lambda *args: 'a' * 40 if args[0] == 'rev-parse' else '')
  output = tmp_path / 'output'
  with pytest.raises(ValueError, match='Expected dev or a vMAJOR.MINOR.PATCH tag'):
    run_docs.build(output, label)
  assert not output.exists()


def test_sdist_includes_doc_site_inputs():
  assert {
    'run_docs.py', 'run_doc_checks.py', 'run_docs_site.py',
    '.github/workflows/docs-publish.yml', 'docs/versioning.md',
    'tests/test_docs_site.py', 'tests/test_docs_workflows.py',
  } <= set(source_files(ROOT))


def test_version_nav_links_selection_page(monkeypatch):
  monkeypatch.setenv('BAZI_DOC_ROOT', str(ROOT))
  monkeypatch.setenv('BAZI_DOC_VERSION', '开发版')
  config = runpy.run_path(str(ROOT / 'docs/conf.py'))
  assert config['html_theme_options']['extra_nav_links'] == {
    '全部版本': 'https://0xf3cd.github.io/bazi/versions/',
  }
  assert 'versioning' in (ROOT / 'docs/index.md').read_text(encoding='utf-8')
