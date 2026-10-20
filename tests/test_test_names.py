# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import ast
from pathlib import Path
from typing import Final


TESTS_DIR: Final = Path(__file__).parent
NAME_LIMIT: Final = 45


def overlong_test_names(source: str) -> list[str]:
  return [
    node.name
    for node in ast.walk(ast.parse(source))
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name.startswith('test')
    and len(node.name) > NAME_LIMIT
  ]


def python_files(root: Path) -> list[Path]:
  return sorted(root.rglob('*.py'))


def overlong_in_tree(root: Path) -> dict[str, list[str]]:
  return {
    path.relative_to(root).as_posix(): names
    for path in python_files(root)
    if (names := overlong_test_names(path.read_text(encoding='utf-8')))
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
  ])
  assert sorted(overlong_test_names(source)) == sorted([over, bare, over + 'b'])


def test_tree_scan_reports_nested_long_names(tmp_path: Path) -> None:
  over = 'test_' + 'a' * 41
  (tmp_path / 'sub').mkdir()
  (tmp_path / 'test_ok.py').write_text('def test_short(): pass\n', encoding='utf-8')
  (tmp_path / 'sub' / 'test_deep.py').write_text(f'def {over}(): pass\n', encoding='utf-8')
  assert overlong_in_tree(tmp_path) == {'sub/test_deep.py': [over]}


def test_every_test_name_fits_the_limit() -> None:
  assert Path(__file__) in python_files(TESTS_DIR)
  assert overlong_in_tree(TESTS_DIR) == {}, f'test names must be at most {NAME_LIMIT} characters'
