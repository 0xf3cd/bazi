# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

from api_contract import PUBLIC_NAMES, DECLARED_MEMBERS, PRIVATE_BASE_MEMBERS, BASES, INTERNAL_MODULES, STATIC_MODULES, REEXPORTS, ALIASES


ROOT = Path(__file__).resolve().parents[1]


def _names(nodes: list[ast.stmt]) -> set[str]:
  names: set[str] = set()
  for node in nodes:
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
      names.add(node.name)
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
      for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
        if isinstance(target, ast.Name):
          names.add(target.id)
  return {name for name in names if not name.startswith('_')}


def _surface(source: str, module: str) -> tuple[set[str], dict[str, set[str]], dict[str, tuple[str, ...]]]:
  tree = ast.parse(source)
  names = _names(tree.body)
  members: dict[str, set[str]] = {}
  bases: dict[str, tuple[str, ...]] = {}

  def visit(nodes: list[ast.stmt], prefix: str) -> None:
    for node in nodes:
      if not isinstance(node, ast.ClassDef):
        continue
      qualified = prefix + '.' + node.name
      if node.name.startswith('_') and qualified not in PRIVATE_BASE_MEMBERS:
        continue
      members[qualified] = _names(node.body)
      if node.bases:
        bases[qualified] = tuple(ast.unparse(base) for base in node.bases)
      visit(node.body, qualified)

  visit(tree.body, module)
  for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__all__' for t in node.targets):
      names.update(ast.literal_eval(node.value))
  return names, members, bases


def _check_surface(source: str, module: str) -> None:
  names, members, bases = _surface(source, module)
  assert names <= set(PUBLIC_NAMES[module].split()), (module, names - set(PUBLIC_NAMES[module].split()))
  declared = DECLARED_MEMBERS | PRIVATE_BASE_MEMBERS
  def owner(qualified: str) -> str:
    return max((name for name in PUBLIC_NAMES if qualified.startswith(name + '.')), key=len)
  expected_members = {key: set(value.split()) for key, value in declared.items() if owner(key) == module}
  expected_bases = {key: value for key, value in BASES.items() if owner(key) == module}
  assert members == expected_members, module
  assert bases == expected_bases, module


def test_all_modules_and_declared_candidates_are_classified() -> None:
  modules: set[str] = set()
  for path in (ROOT / 'bazi').rglob('*.py'):
    module = '.'.join(path.relative_to(ROOT).with_suffix('').parts).removesuffix('.__init__')
    modules.add(module)
    if module not in INTERNAL_MODULES:
      _check_surface(path.read_text(encoding='utf-8'), module)
  assert modules == set(PUBLIC_NAMES) | set(INTERNAL_MODULES)
  assert not set(PUBLIC_NAMES) & set(INTERNAL_MODULES)
  assert set(STATIC_MODULES) <= set(PUBLIC_NAMES)
  for words in (*PUBLIC_NAMES.values(), *DECLARED_MEMBERS.values(), *PRIVATE_BASE_MEMBERS.values()):
    assert len(words.split()) == len(set(words.split()))


def test_public_surface_resolves_without_loading_tables_or_offline_tools() -> None:
  # A fresh process prevents earlier calendar tests from hiding an eager import.
  script = '''
import importlib, inspect, sys
sys.path.insert(0, 'tests')
from api_contract import PUBLIC_NAMES, DECLARED_MEMBERS, PRIVATE_BASE_MEMBERS, STATIC_MODULES, ALIASES, REEXPORTS

def guard(event, args):
  if event == 'open' and isinstance(args[0], str):
    path = args[0].replace('\\\\', '/')
    if '/bazi/calendar/' in path and '/data/' in path:
      raise RuntimeError('Unexpected calendar data read')
sys.addaudithook(guard)

def resolve(qualified):
  module = max((m for m in PUBLIC_NAMES if qualified.startswith(m + '.')), key=len)
  value = importlib.import_module(module)
  for part in qualified[len(module) + 1:].split('.'):
    value = getattr(value, part)
  return value

for module, words in PUBLIC_NAMES.items():
  if module in STATIC_MODULES:
    continue
  value = importlib.import_module(module)
  for name in words.split():
    qualified = module + '.' + name
    if qualified in STATIC_MODULES:
      continue
    if qualified in PUBLIC_NAMES:
      importlib.import_module(qualified)
    else:
      assert hasattr(value, name), qualified
for qualified, words in (DECLARED_MEMBERS | PRIVATE_BASE_MEMBERS).items():
  if any(qualified.startswith(module + '.') for module in STATIC_MODULES):
    continue
  value = resolve(qualified)
  annotations = getattr(value, '__annotations__', {})
  for name in words.split():
    assert name in annotations or inspect.getattr_static(value, name, None) is not None, (qualified, name)
for alias, canonical in (ALIASES | REEXPORTS).items():
  assert resolve(alias) is resolve(canonical), alias
assert not any(name in sys.modules for name in STATIC_MODULES)
print('PASS safe public imports, declared fields and aliases')
'''
  result = subprocess.run([sys.executable, '-B', '-c', script], cwd=ROOT, text=True, capture_output=True, check=False)
  assert result.returncode == 0, result.stdout + result.stderr
  assert 'PASS safe public imports' in result.stdout


@pytest.mark.parametrize('addition', [
  '\ndef unregistered_api():\n  pass\n',
  '\n新别名 = KnowledgeBase\n',
  '\nclass UnregisteredType:\n  field: str\n',
])
def test_new_public_candidates_cannot_escape_registration(addition: str) -> None:
  source = (ROOT / 'bazi/knowledge.py').read_text(encoding='utf-8')
  _check_surface(source, 'bazi.knowledge')
  with pytest.raises(AssertionError):
    _check_surface(source + addition, 'bazi.knowledge')


def test_new_field_and_enum_alias_cannot_escape_registration() -> None:
  for module, path, class_name in (
    ('bazi.knowledge', 'bazi/knowledge.py', 'KnowledgeObject'),
    ('bazi.defines.tiangan', 'bazi/defines/tiangan.py', 'Tiangan'),
  ):
    source = (ROOT / path).read_text(encoding='utf-8')
    _check_surface(source, module)
    declaration = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == class_name)
    lines = source.splitlines(keepends=True)
    assert declaration.end_lineno is not None
    lines.insert(declaration.end_lineno, '  unregistered_field: str\n' if class_name == 'KnowledgeObject' else '  新别名 = JIA\n')
    with pytest.raises(AssertionError):
      _check_surface(''.join(lines), module)


def test_public_contract_covers_existing_consumers_and_explicit_exports() -> None:
  # Existing consumer imports are additional evidence, not the definition of the public surface.
  for path in (*ROOT.glob('run_*.py'), *(ROOT / 'tests').rglob('*.py')):
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
      if not isinstance(node, ast.ImportFrom) or not node.module or not node.module.startswith('bazi'):
        continue
      for alias in node.names:
        if not alias.name.startswith('_'):
          assert alias.name in PUBLIC_NAMES[node.module].split(), (path, node.module, alias.name)
  for module in PUBLIC_NAMES:
    path = ROOT.joinpath(*module.split('.')) / '__init__.py'
    if not path.exists():
      continue
    for node in ast.parse(path.read_text(encoding='utf-8')).body:
      if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__all__' for t in node.targets):
        for name in ast.literal_eval(node.value):
          qualified = module + '.' + name
          assert qualified in PUBLIC_NAMES or qualified in REEXPORTS, qualified
  for alias_path, canonical in (ALIASES | REEXPORTS).items():
    for qualified in (alias_path, canonical):
      owner = max((module for module in PUBLIC_NAMES if qualified.startswith(module + '.')), key=len)
      assert qualified[len(owner) + 1:] in PUBLIC_NAMES[owner].split(), qualified


@pytest.mark.parametrize('code', re.findall(r'```python\n(.*?)\n```', (ROOT / 'API_CONTRACT.md').read_text(encoding='utf-8'), re.DOTALL))
def test_contract_examples_run_independently(code: str, tmp_path: Path) -> None:
  script = f'import sys\nsys.path.insert(0, {str(ROOT)!r})\n' + code
  result = subprocess.run([sys.executable, '-B', '-c', script], cwd=tmp_path, text=True, capture_output=True, check=False)
  assert result.returncode == 0, result.stdout + result.stderr
