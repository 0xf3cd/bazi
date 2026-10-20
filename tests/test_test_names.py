# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import io
import tokenize
from pathlib import Path
from typing import Final


TESTS_DIR: Final = Path(__file__).parent
NAME_LIMIT: Final = 45


def overlong_test_names(source: bytes) -> list[str]:
  return [
    token.string
    for token in tokenize.tokenize(io.BytesIO(source).readline)
    if token.type == tokenize.NAME and token.string.startswith('test') and len(token.string) > NAME_LIMIT
  ]


def python_files(root: Path) -> list[Path]:
  return sorted(root.rglob('*.py'))


def overlong_in_tree(root: Path) -> dict[str, list[str]]:
  return {
    path.relative_to(root).as_posix(): names
    for path in python_files(root)
    if (names := overlong_test_names(path.read_bytes()))
  }


def test_name_limit_flags_only_longer_names() -> None:
  at_limit = 'test_' + 'a' * 40
  over = 'test_' + 'a' * 41
  bare = 'test' + 'd' * 60
  assert (len(at_limit), len(over)) == (45, 46)
  source = '\n'.join([
    f'def {at_limit}(): pass',
    f'async def {over}(): pass',
    f'def {bare}(): pass',
    'class TestGroup:',
    f'  def {over}b(self): pass',
    f'def helper_{"c" * 60}(): pass',
    f'holder_{"e" * 60} = 1',
    f'{at_limit} = helper',
    f'{over}c = helper',
    f'{over}d: int = 1',
    f'{over}e, other = 1, 2',
    f'from sample import helper as {over}f',
    f'for {over}g in []: pass',
    f'match helper:\n  case {over}h: pass',
  ]).encode()
  expected = [over, bare, over + 'b', over + 'c', over + 'd', over + 'e', over + 'f', over + 'g', over + 'h']
  assert sorted(overlong_test_names(source)) == sorted(expected)


def test_name_limit_ignores_comments_and_text() -> None:
  over = 'test_' + 'a' * 41
  source = '\n'.join([
    f'# {over}',
    f'text = "{over}"',
    'text = f"test text that is longer than the limit allows, {text}"',
  ]).encode()
  assert overlong_test_names(source) == []


def test_tree_scan_reports_nested_long_names(tmp_path: Path) -> None:
  over = 'test_' + 'a' * 41
  (tmp_path / 'sub').mkdir()
  (tmp_path / 'test_ok.py').write_text('def test_short(): pass\n', encoding='utf-8')
  (tmp_path / 'sub' / 'test_deep.py').write_text(f'def {over}(): pass\n', encoding='utf-8')
  assert overlong_in_tree(tmp_path) == {'sub/test_deep.py': [over]}


def test_tree_scan_honours_source_encoding(tmp_path: Path) -> None:
  over = 'test_' + 'a' * 41
  (tmp_path / 'test_bom.py').write_bytes(b'\xef\xbb\xbf' + f'def {over}(): pass\n'.encode())
  (tmp_path / 'test_latin.py').write_bytes(b'# -*- coding: latin-1 -*-\n# caf\xe9\n' + f'def {over}(): pass\n'.encode())
  assert overlong_in_tree(tmp_path) == {'test_bom.py': [over], 'test_latin.py': [over]}


def test_every_test_name_fits_the_limit() -> None:
  assert Path(__file__) in python_files(TESTS_DIR)
  assert overlong_in_tree(TESTS_DIR) == {}, f'identifiers starting with test must be at most {NAME_LIMIT} characters'
