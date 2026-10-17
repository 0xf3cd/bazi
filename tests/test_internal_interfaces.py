# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import ast
import json
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _dependencies(root: Path) -> tuple[Counter[str], Counter[str]]:
  imports: Counter[str] = Counter()
  members: Counter[str] = Counter()
  for path in (root / 'bazi').rglob('*.py'):
    name = path.relative_to(root).as_posix()
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
      if isinstance(node, ast.ImportFrom) and node.level:
        for alias in node.names:
          if alias.name.startswith('_') and not alias.name.startswith('__'):
            imports[f'{name}|{"." * node.level}{node.module or ""}|{alias.name}'] += 1
      if (
        isinstance(node, ast.Attribute) and node.attr.startswith('_') and not node.attr.startswith('__')
        and (not isinstance(node.value, ast.Name) or node.value.id not in ('self', 'cls'))
      ):
        members[f'{name}|{ast.unparse(node)}'] += 1
  return imports, members


def test_private_dependencies_have_explicit_owners() -> None:
  # This is a static candidate guard, not a proof about dynamic getattr or all cross-object access.
  ledger = json.loads((ROOT / 'tests/data/internal_interfaces.json').read_text(encoding='utf-8'))
  assert all(reason.strip() for group in ('imports', 'members') for reason in ledger[group].values())
  expected_imports = Counter({key: 1 for key in ledger['imports']})
  expected_members = Counter({key: ledger['repeated_members'].get(key, 1) for key in ledger['members']})
  assert set(ledger['repeated_members']) <= set(ledger['members'])
  assert _dependencies(ROOT) == (expected_imports, expected_members)


def test_candidate_scan_includes_imports_and_nested_member_access(tmp_path: Path) -> None:
  package = tmp_path / 'bazi'
  package.mkdir()
  source = package / 'sample.py'
  source.write_text(
    'from .owner import _shared\n'
    'from .owner import Public\n'
    'def use(self, cls, other):\n'
    '  self._own\n'
    '  cls._own\n'
    '  other._shared\n'
    '  self._database._shared\n'
    '  other.__class__\n',
    encoding='utf-8',
  )
  expected = (
    Counter({'bazi/sample.py|.owner|_shared': 1}),
    Counter({'bazi/sample.py|other._shared': 1, 'bazi/sample.py|self._database._shared': 1}),
  )
  assert _dependencies(tmp_path) == expected
  for injected in ('from .owner import _new\n', 'other._new\n', 'other._shared\n'):
    original = source.read_text(encoding='utf-8')
    source.write_text(original + injected, encoding='utf-8')
    with pytest.raises(AssertionError):
      assert _dependencies(tmp_path) == expected
    source.write_text(original, encoding='utf-8')
