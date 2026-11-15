# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from pathlib import Path

import pytest

from bazi import cli
from bazi.knowledge import KnowledgeBase

from cli_runner import run_cli


def test_bare_knowledge_gives_an_overview(tmp_path: Path) -> None:
  library = KnowledgeBase.load()
  result = run_cli(tmp_path, 'knowledge')
  assert result.returncode == 0 and result.stderr == ''
  assert f'{len(library.entries)} 条目，{len(library.objects)} 对象，{len(library.sources)} 来源' in result.stdout
  for flag, dimension in cli._LIST_DIMENSIONS.items():
    assert f'--{flag}：{len(library.filter_values(dimension))} 个值' in result.stdout
  assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('flag,dimension', sorted(cli._LIST_DIMENSIONS.items()))
def test_list_values_matches_the_library(tmp_path: Path, flag: str, dimension: str) -> None:
  result = run_cli(tmp_path, 'knowledge', '--list-values', flag)
  assert result.returncode == 0 and result.stderr == ''
  assert result.stdout.splitlines() == list(KnowledgeBase.load().filter_values(dimension))


@pytest.mark.parametrize('tokens,filters', [
  (('丁',), {'subject': '丁'}),
  (('--object', 'tiangan.ding'), {'subject': 'tiangan.ding'}),
  (('文昌', '--viewpoint', 'XIN_XU'), {'subject': '文昌', 'viewpoint': 'XIN_XU'}),
  (('--topic', '定义'), {'topic': '定义'}),
  (('--source', 'repository_guoyin_variants'), {'source_id': 'repository_guoyin_variants'}),
  (('--all',), {}),
])
def test_queries_return_all_matching_material(
  tmp_path: Path, tokens: tuple[str, ...], filters: dict[str, str],
) -> None:
  library = KnowledgeBase.load()
  expected = library.query(**filters)
  result = run_cli(tmp_path, 'knowledge', *tokens)
  assert result.returncode == 0 and result.stderr == ''
  assert result.stdout == ''.join(library.render(entry) + '\n\n' for entry in expected)


@pytest.mark.parametrize('keyword', ['枭印', '没有这段文字', '丁.*火'])
def test_literal_search_matches_library(tmp_path: Path, keyword: str) -> None:
  library = KnowledgeBase.load()
  expected = library.search(keyword)
  result = run_cli(tmp_path, 'knowledge', '--search', keyword)
  assert result.returncode == 0 and result.stderr == ''
  assert result.stdout == (''.join(library.render(entry) + '\n\n' for entry in expected) if expected else '无匹配条目。\n')


@pytest.mark.parametrize('tokens,error', [
  (('丁', '--object', '丁'), 'Use either'),
  (('--all', '丁'), '--all'),
  (('--all', '--search', '丁'), '--all'),
  (('--list-values', 'topic', '--all'), '--list-values only lists'),
  (('--list-values', 'source', '--validate-knowledge'), '--list-values only lists'),
  (('--show-sources',), '--show-sources requires a query'),
  (('不存在',), 'Unknown object'),
  (('--topic', '不存在'), 'Unknown topic'),
  (('--source', '不存在'), 'Unknown source_id'),
  (('--viewpoint', '不存在'), 'Unknown viewpoint'),
])
def test_invalid_query_options_fail(tmp_path: Path, tokens: tuple[str, ...], error: str) -> None:
  result = run_cli(tmp_path, 'knowledge', *tokens)
  assert result.returncode == 2 and error in result.stderr
  assert not result.stdout and not list(tmp_path.iterdir())
