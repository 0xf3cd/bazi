# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from pathlib import Path

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

from run_doc_checks import Page, check_release_notes


TITLES = ('发布说明', 'Unreleased', '知识结构迁移', '安装版命令与脚本迁移', '存取接口移除', '结构接口迁移', '源码脚本的平铺参数')


def release_page(
  titles: tuple[str, ...] = TITLES,
  paragraph: str = '请保留原出生输入与完整配置。',
  field: str = 'reference_ids',
) -> Page:
  page = Page()
  page.feed(''.join(f'<h2>{title}<a>¶</a></h2>' for title in titles) + f'<p>{paragraph}</p>'
    + f'<table><tr><th>字段</th><th>含义</th></tr><tr><td><p><code>{field}</code></p></td><td><p>参考 ID</p></td></tr></table>')
  return page


@pytest.fixture
def release_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
  path = tmp_path / 'RELEASE_NOTES.md'
  path.write_text('\n\n'.join('## ' + title for title in TITLES)
    + '\n\n请保留原出生输入与完整配置。\n\n| 字段 | 含义 |\n| --- | --- |\n| `reference_ids` | 参考 ID |\n', encoding='utf-8')
  monkeypatch.setattr('run_doc_checks.ROOT', tmp_path)
  return path


def page_set(release: Page) -> dict[str, Page]:
  index = Page()
  index.feed('<a href="release-notes.html">发布与迁移</a>')
  return {'index.html': index, 'release-notes.html': release}


def test_release_source_is_rendered(release_source: Path) -> None:
  assert check_release_notes(page_set(release_page())) == len(TITLES)


@pytest.mark.parametrize('fault', ['page', 'navigation', 'heading', 'paragraph', 'table'])
def test_missing_release_content_is_rejected(release_source: Path, fault: str) -> None:
  pages = page_set(release_page())
  if fault == 'page':
    del pages['release-notes.html']
  elif fault == 'navigation':
    pages['index.html'] = Page()
  elif fault == 'heading':
    pages['release-notes.html'] = release_page(TITLES[:-1])
  elif fault == 'paragraph':
    pages['release-notes.html'] = release_page(paragraph='')
  else:
    pages['release-notes.html'] = release_page(field='references')
  with pytest.raises((AssertionError, KeyError)):
    check_release_notes(pages)


@pytest.mark.parametrize('title', TITLES[2:])
def test_source_and_html_cannot_omit_migration(release_source: Path, title: str) -> None:
  release_source.write_text(release_source.read_text(encoding='utf-8').replace('## ' + title, ''), encoding='utf-8')
  pages = page_set(release_page(tuple(value for value in TITLES if value != title)))
  with pytest.raises(AssertionError, match='Missing release migration sections'):
    check_release_notes(pages)
