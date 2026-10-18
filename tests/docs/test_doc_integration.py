# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import runpy
import sys
from pathlib import Path

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import run_docs
import run_docs_site
from run_package_checks import source_files


def test_builder_and_archive_share_release_label_grammar():
  assert run_docs.RELEASE_LABEL is run_docs_site.RELEASE_LABEL


@pytest.mark.parametrize('label', ['v01.2.3', 'v1.02.3', 'v1.2.03', 'v1.2.3-rc1', '../v1.2.3', 'main'])
def test_builder_rejects_noncanonical_release_labels(monkeypatch, tmp_path, label):
  monkeypatch.setattr(run_docs, 'git_output', lambda *args: 'a' * 40 if args[0] == 'rev-parse' else '')
  output = tmp_path / 'output'
  with pytest.raises(ValueError, match='Expected dev or a vMAJOR.MINOR.PATCH tag'):
    run_docs.build(output, label)
  assert not output.exists()


def test_archive_and_version_guide_travel_with_source_distribution():
  assert {
    'run_docs.py', 'run_doc_checks.py', 'run_docs_site.py',
    '.github/workflows/docs-publish.yml', 'docs/versioning.md',
    'tests/test_docs_site.py', 'tests/test_docs_workflows.py',
  } <= set(source_files(ROOT))


def test_version_navigation_points_to_the_shared_selection_page(monkeypatch):
  monkeypatch.setenv('BAZI_DOC_ROOT', str(ROOT))
  monkeypatch.setenv('BAZI_DOC_VERSION', '开发版')
  config = runpy.run_path(str(ROOT / 'docs/conf.py'))
  assert config['html_theme_options']['extra_nav_links'] == {
    '全部版本': 'https://0xf3cd.github.io/bazi/versions/',
  }
  assert 'versioning' in (ROOT / 'docs/index.md').read_text(encoding='utf-8')
