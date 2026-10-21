# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import runpy
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import run_docs
import run_docs_site
from run_package_checks import source_files


def test_readme_links_work_outside_repo():
  links = [
    child.attrGet('href') or ''
    for token in MarkdownIt('commonmark').parse((ROOT / 'README.md').read_text(encoding='utf-8'))
    for child in token.children or () if child.type == 'link_open'
  ]
  assert links
  for link in links:
    assert isinstance(link, str)
    if link.startswith('#'):
      continue
    url = urlsplit(link)
    assert url.scheme == 'https' and url.netloc, link
    if link.startswith('https://github.com/0xf3cd/bazi/blob/main/'):
      path = ROOT / unquote(url.path.removeprefix('/0xf3cd/bazi/blob/main/'))
      assert path.resolve().is_relative_to(ROOT) and path.is_file(), link


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
