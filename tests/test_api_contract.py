# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import ast
import json
import re
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from api_contract import PUBLIC_NAMES, DECLARED_MEMBERS, PRIVATE_BASE_MEMBERS, BASES, INTERNAL_MODULES, STATIC_MODULES, REEXPORTS, ALIASES
from api_contract import EXPLICIT_EXPORT_ADDITIONS


ROOT = Path(__file__).resolve().parents[1]
EXPLICIT_EXPORT_BASELINE = json.loads((ROOT / 'tests/data/v200_explicit_exports.json').read_text(encoding='utf-8'))
EXPLICIT_EXPORTS: dict[str, list[str]] = EXPLICIT_EXPORT_BASELINE['explicit_exports']


def _scope_nodes(nodes: list[ast.stmt]) -> Iterator[ast.AST]:
  def visit(node: ast.AST) -> Iterator[ast.AST]:
    yield node
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
      for name, value in ast.iter_fields(node):
        if name != 'body':
          if isinstance(value, ast.AST):
            yield from visit(value)
          elif isinstance(value, list):
            for child in value:
              if isinstance(child, ast.AST):
                yield from visit(child)
    else:
      for child in ast.iter_child_nodes(node):
        yield from visit(child)
  for node in nodes:
    yield from visit(node)


def _names(nodes: list[ast.stmt]) -> set[str]:
  names: set[str] = set()
  for node in _scope_nodes(nodes):
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
      names.add(node.name)
    elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr, ast.For, ast.AsyncFor)):
      for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
        names.update(child.id for child in ast.walk(target) if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store))
    elif isinstance(node, (ast.With, ast.AsyncWith)):
      for item in node.items:
        if item.optional_vars is not None:
          names.update(child.id for child in ast.walk(item.optional_vars) if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store))
    elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name is not None:
      names.add(node.name)
    elif isinstance(node, ast.MatchMapping) and node.rest is not None:
      names.add(node.rest)
    elif isinstance(node, getattr(ast, 'TypeAlias', ())):
      name = vars(node)['name']
      assert isinstance(name, ast.Name)
      names.add(name.id)
  return {name for name in names if not name.startswith('_')}


def _declared_all(nodes: list[ast.stmt]) -> set[str]:
  names: set[str] = set()
  for node in _scope_nodes(nodes):
    values: ast.AST | None = None
    single = False
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
      targets = node.targets if isinstance(node, ast.Assign) else [node.target]
      for target in targets:
        for child in ast.walk(target):
          if isinstance(child, ast.Subscript) and isinstance(child.ctx, ast.Store):
            base = child.value
            while isinstance(base, ast.Subscript):
              base = base.value
            assert not (isinstance(base, ast.Name) and base.id == '__all__'), 'Unsupported __all__ assignment target'
          if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store) and child.id == '__all__':
            assert child is target, 'Unsupported __all__ assignment target'
            if isinstance(node, ast.AugAssign):
              assert isinstance(node.op, ast.Add), 'Unsupported __all__ operator'
            values = node.value
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == '__all__':
      assert node.func.attr in ('append', 'extend') and len(node.args) == 1 and not node.keywords, 'Unsupported __all__ mutation'
      values = node.args[0]
      single = node.func.attr == 'append'
    if values is not None:
      try:
        value = ast.literal_eval(values)
      except (ValueError, TypeError, SyntaxError) as error:
        raise AssertionError('Unsupported dynamic __all__ declaration') from error
      sequence = [value] if single else value
      assert isinstance(sequence, (list, tuple)) and all(isinstance(name, str) for name in sequence), 'Expected literal __all__ names'
      names.update(sequence)
  return names


def _check_explicit_exports(source: str, module: str) -> None:
  if module in EXPLICIT_EXPORTS:
    actual = _declared_all(ast.parse(source).body)
    expected = set(EXPLICIT_EXPORTS[module]) | EXPLICIT_EXPORT_ADDITIONS.get(module, frozenset())
    assert actual == expected, (module, 'Explicit exports differ from the approved surface', actual ^ expected)


def _surface(source: str, module: str) -> tuple[set[str], dict[str, set[str]], dict[str, tuple[str, ...]]]:
  tree = ast.parse(source)
  names = _names(tree.body)
  members: dict[str, set[str]] = {}
  bases: dict[str, tuple[str, ...]] = {}

  def visit(nodes: list[ast.stmt], prefix: str) -> None:
    for node in _scope_nodes(nodes):
      if not isinstance(node, ast.ClassDef):
        continue
      qualified = prefix + '.' + node.name
      if node.name.startswith('_') and qualified not in PRIVATE_BASE_MEMBERS:
        continue
      declared_bases = tuple(ast.unparse(base) for base in node.bases)
      if qualified in members:
        assert bases.get(qualified, ()) == declared_bases, ('Conflicting candidate bases', qualified)
      members.setdefault(qualified, set()).update(_names(node.body))
      if node.bases:
        bases[qualified] = declared_bases
      visit(node.body, qualified)

  visit(tree.body, module)
  names.update(_declared_all(tree.body))
  return names, members, bases


def _check_surface(source: str, module: str) -> None:
  _check_explicit_exports(source, module)
  names, members, bases = _surface(source, module)
  assert names <= set(PUBLIC_NAMES[module].split()), (module, names - set(PUBLIC_NAMES[module].split()))
  if module in STATIC_MODULES:
    assert names == set(PUBLIC_NAMES[module].split()), (module, set(PUBLIC_NAMES[module].split()) - names)
  declared = DECLARED_MEMBERS | PRIVATE_BASE_MEMBERS
  def owner(qualified: str) -> str:
    return max((name for name in PUBLIC_NAMES if qualified.startswith(name + '.')), key=len)
  expected_members = {key: set(value.split()) for key, value in declared.items() if owner(key) == module}
  expected_bases = {key: value for key, value in BASES.items() if owner(key) == module}
  assert members == expected_members, module
  assert bases == expected_bases, module


def test_public_modules_describe_their_purpose() -> None:
  for module in PUBLIC_NAMES:
    path = ROOT.joinpath(*module.split('.'))
    path = path / '__init__.py' if path.is_dir() else path.with_suffix('.py')
    assert ast.get_docstring(ast.parse(path.read_text(encoding='utf-8'))), module


def test_removed_persistence_is_absent() -> None:
  import importlib
  import importlib.util
  import bazi
  from bazi.bazi import Bazi, LocationTime
  from bazi.bazi_chart import BaziChart
  from bazi.context_matching import NatalObservation, ContextResult, evaluate_context
  from bazi.knowledge import KnowledgeBase
  from bazi.school import BaziSchool
  from bazi.transits import TransitSet
  for module, name in (
    ('bazi.bazi', 'LocationTimeJson'), ('bazi.bazi_chart', 'BaziJson'),
    ('bazi.school', '_ConfigJson'), ('bazi.school', '_config_json'),
  ):
    assert not hasattr(importlib.import_module(module), name)
  for owner, names in (
    (BaziChart, ('json', 'from_json', '_from_data')), (LocationTime, ('json',)),
    (BaziSchool, ('from_json',)), (TransitSet, ('json',)),
    (ContextResult, ('input_json', 'export_json', 'from_json', '_from_data')),
    (KnowledgeBase, ('export_json', 'from_json', '_export_data')),
  ):
    assert all(not hasattr(owner, name) for name in names)
  assert importlib.util.find_spec('bazi.record_migration') is None
  assert 'record_migration' not in dir(bazi) and 'record_migration' not in bazi.__all__
  with pytest.raises(AttributeError):
    bazi.record_migration # noqa: B018 # Removed lazy attribute must fail at runtime.
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))
  result = evaluate_context(
    chart,
    criterion_id='editorial.guansha_coexistence.v1',
    observation=NatalObservation(),
  )
  assert result.bazi == chart.bazi
  assert result.render()
  assert KnowledgeBase.load().entries


def test_removed_structure_fields_are_absent() -> None:
  import bazi.context_matching as matching
  from bazi.analyzer.relationship import KongwangHit, StarAppearance
  from bazi.context_matching import CriterionInfo, ContextResult, ChartOccurrence
  for name in ('ContextProfile', 'RelationshipProfile', 'Pillar', 'ObservationScope', 'RelationshipScope'):
    assert not hasattr(matching, name)
  for owner, names in (
    (ContextResult, ('profile', 'occurrences', 'relationship', 'related', 'entries')),
    (CriterionInfo, ('profile_type', 'profile_kind')),
    (KongwangHit, ('origin', 'pillar', 'kind')),
    (StarAppearance, ('origin', 'pillar', 'kind')),
    (ChartOccurrence, ('origin', 'pillar', 'kind', 'ganzhi_year')),
  ):
    assert all(not hasattr(owner, name) for name in names)


def test_modules_and_candidates_classified() -> None:
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


@pytest.mark.parametrize('injection, rejected_name', [
  ('', None),
  ("importlib.import_module('bazi.knowledge').UnregisteredDynamic = type('UnregisteredDynamic', (), {'__module__': 'bazi.knowledge'})", 'UnregisteredDynamic'),
  ("importlib.import_module('bazi.knowledge').KnowledgeRole.unregistered_dynamic = property(lambda self: None)", 'unregistered_dynamic'),
  ("importlib.import_module('bazi').__all__.append('Any')", 'Any'),
  ("importlib.import_module('bazi').__all__.remove('bazi_chart')", 'bazi_chart'),
  ("importlib.import_module('bazi.calendar').__all__.append('solar_time')", 'solar_time'),
])
def test_surface_resolves_without_heavy_loads(injection: str, rejected_name: str | None) -> None:
  # A fresh process prevents earlier calendar tests from hiding an eager import.
  script = '''
import importlib, inspect, json, sys
from pathlib import Path
sys.path.insert(0, 'tests')
from api_contract import PUBLIC_NAMES, DECLARED_MEMBERS, PRIVATE_BASE_MEMBERS, STATIC_MODULES, ALIASES, REEXPORTS, EXPLICIT_EXPORT_ADDITIONS
explicit_exports = json.loads(Path('tests/data/v200_explicit_exports.json').read_text(encoding='utf-8'))['explicit_exports']

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
  exported = set(getattr(value, '__all__', ()))
  if module in explicit_exports:
    expected_exports = set(explicit_exports[module]) | EXPLICIT_EXPORT_ADDITIONS.get(module, frozenset())
    assert exported == expected_exports, (module, exported ^ expected_exports)
  assert exported <= set(words.split()), (module, exported - set(words.split()))
  own_definitions = {name for name, member in vars(value).items()
                     if not name.startswith('_') and (inspect.isclass(member) or inspect.isfunction(member))
                     and member.__module__ == module}
  assert own_definitions <= set(words.split()), (module, own_definitions - set(words.split()))
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
  actual_members = {name for name in vars(value) if not name.startswith('_')}
  assert actual_members <= set(words.split()), (qualified, actual_members - set(words.split()))
  for name in words.split():
    assert name in annotations or inspect.getattr_static(value, name, None) is not None, (qualified, name)
for alias, canonical in (ALIASES | REEXPORTS).items():
  assert resolve(alias) is resolve(canonical), alias
assert not any(name in sys.modules for name in STATIC_MODULES)
print('PASS safe public imports, declared fields and aliases')
'''
  script = script.replace('for module, words in PUBLIC_NAMES.items():', injection + '\nfor module, words in PUBLIC_NAMES.items():', 1)
  result = subprocess.run([sys.executable, '-B', '-c', script], cwd=ROOT, text=True, capture_output=True, check=False)
  if rejected_name is None:
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS safe public imports' in result.stdout
  else:
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'AssertionError' in result.stderr, result.stdout + result.stderr
    assert rejected_name in result.stderr, result.stdout + result.stderr


@pytest.mark.parametrize('addition', [
  '\ndef unregistered_api():\n  pass\n',
  '\n新别名 = KnowledgeBase\n',
  '\nclass UnregisteredType:\n  field: str\n',
  '\nif True:\n  def unregistered_api():\n    pass\n',
  '\nif True:\n  新别名 = KnowledgeBase\n',
  '\ntry:\n  新别名 = KnowledgeBase\nexcept Exception:\n  pass\n',
  '\nfirst, (second, *rest) = (1, (2, 3))\n',
  '\nif True:\n  class UnregisteredType:\n    field: str\n',
  '\nfor unregistered_loop in (1,):\n  pass\n',
  '\nwith open(__file__) as unregistered_file:\n  pass\n',
  '\nif (unregistered_walrus := True):\n  pass\n',
  '\nmatch {"key": 1}:\n  case {"key": unregistered_capture}:\n    pass\n',
  '\nmatch []:\n  case [*unregistered_star]:\n    pass\n',
  '\nmatch {"key": 1}:\n  case {**unregistered_rest}:\n    pass\n',
])
def test_new_public_candidates_must_register(addition: str) -> None:
  source = (ROOT / 'bazi/knowledge.py').read_text(encoding='utf-8')
  _check_surface(source, 'bazi.knowledge')
  with pytest.raises(AssertionError):
    _check_surface(source + addition, 'bazi.knowledge')


def test_new_field_enum_alias_must_register() -> None:
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


def test_scope_candidates_skip_function_locals() -> None:
  source = '''
def function():
  local = 1
  class Local:
    pass
class Public:
  if True:
    field: str
    def method(self):
      local = 1
  try:
    alias = field
  except Exception:
    fallback = None
'''
  names, members, bases = _surface(source, 'example')
  assert names == {'function', 'Public'}
  assert members == {'example.Public': {'field', 'method', 'alias', 'fallback'}}
  assert bases == {}
  assert _names(ast.parse('result = [item for item in ()]').body) == {'result'}
  assert _names(ast.parse('function = lambda: (local := 1)').body) == {'function'}
  assert _names(ast.parse('result = [(outer := item) for item in ()]').body) == {'result', 'outer'}


@pytest.mark.parametrize('earlier', [
  'class KnowledgeRole:\n  unregistered_dead_member: str\n',
  'class KnowledgeRole(object):\n  name: str\n  object_id: str\n',
])
def test_repeated_classes_cannot_hide_candidates(earlier: str) -> None:
  source = (ROOT / 'bazi/knowledge.py').read_text(encoding='utf-8')
  anchor = '@dataclass(frozen=True)\nclass KnowledgeRole:'
  assert source.count(anchor) == 1
  changed = source.replace(anchor, 'if False:\n' + '\n'.join('  ' + line for line in earlier.splitlines()) + '\n\n' + anchor)
  compile(changed, '<repeated-class-candidate>', 'exec')
  with pytest.raises(AssertionError):
    _check_surface(changed, 'bazi.knowledge')


def test_repeated_classes_combine_members() -> None:
  names, members, bases = _surface('if True:\n  class Public:\n    first: str\nelse:\n  class Public:\n    second: str\n', 'example')
  assert names == {'Public'}
  assert members == {'example.Public': {'first', 'second'}}
  assert bases == {}


@pytest.mark.parametrize('first, second', [('', '(Base)'), ('(Base)', ''), ('(Base)', '(Other)')])
def test_repeated_class_base_conflict_fails(first: str, second: str) -> None:
  with pytest.raises(AssertionError, match='Conflicting candidate bases'):
    _surface(f'class Public{first}:\n  first: str\nclass Public{second}:\n  second: str\n', 'example')


def test_same_base_repeats_combine_candidates() -> None:
  names, members, bases = _surface('class Public(Base):\n  first: str\nclass Public(Base):\n  second: str\n', 'example')
  assert names == {'Public'}
  assert members == {'example.Public': {'first', 'second'}}
  assert bases == {'example.Public': ('Base',)}


@pytest.mark.parametrize('source, expected', [
  ('def function(arg=(outer := 1)):\n  local = 1\n', {'function', 'outer'}),
  ('function = lambda arg=(outer := 1): (local := arg)', {'function', 'outer'}),
  ('@(outer := lambda function: function)\ndef function():\n  local = 1\n', {'function', 'outer'}),
  ('class Public((outer := object)):\n  local = 1\n', {'Public', 'outer'}),
  ('class Public(metaclass=(outer := type)):\n  local = 1\n', {'Public', 'outer'}),
  ("with __import__('contextlib').nullcontext((1, 2)) as (first, second):\n  pass\n", {'first', 'second'}),
])
def test_outer_expression_bindings_are_candidates(source: str, expected: set[str]) -> None:
  code = compile(source, '<outer-binding-candidate>', 'exec')
  namespace: dict[str, object] = {}
  exec(code, namespace) # noqa: S102 -- Execute only the fixed test fixtures above.
  assert {name for name in namespace if not name.startswith('_')} == expected
  assert _names(ast.parse(source).body) == expected


def test_defaults_bind_in_enclosing_namespace() -> None:
  source = 'class Public:\n  def method(self, arg=(outer := 1)):\n    local = 1\n'
  namespace: dict[str, object] = {}
  exec(compile(source, '<class-default-binding>', 'exec'), namespace) # noqa: S102 -- Execute only this fixed source fixture.
  assert {name for name in namespace if not name.startswith('_')} == {'Public'}
  assert {name for name in vars(namespace['Public']) if not name.startswith('_')} == {'method', 'outer'}
  assert _surface(source, 'example') == ({'Public'}, {'example.Public': {'method', 'outer'}}, {})
  assert _declared_all(ast.parse('def function():\n  __all__ = ["local"]\n').body) == set()
  assert _declared_all(ast.parse('mapping[__all__[0]] = 1').body) == set()
  assert _declared_all(ast.parse('other.__all__ = ["external"]').body) == set()


@pytest.mark.skipif(sys.version_info < (3, 12), reason='PEP 695 syntax requires Python 3.12')
def test_type_alias_candidates_are_classified() -> None:
  assert _names(ast.parse('type PublicAlias = str').body) == {'PublicAlias'}
  source = (ROOT / 'bazi/knowledge.py').read_text(encoding='utf-8')
  with pytest.raises(AssertionError, match='PublicAlias'):
    _check_surface(source + '\ntype PublicAlias = str\n', 'bazi.knowledge')


@pytest.mark.parametrize('declaration', [
  '__all__ = ["unregistered_export"]',
  '__all__: list[str] = ["unregistered_export"]',
  '__all__ = []\n__all__ += ["unregistered_export"]',
  '__all__ = []\n__all__.append("unregistered_export")',
  '__all__ = []\n__all__.extend(["unregistered_export"])',
  'if (__all__ := ["unregistered_export"]):\n  pass',
])
def test_declared_exports_must_register(declaration: str) -> None:
  source = (ROOT / 'bazi/__init__.py').read_text(encoding='utf-8')
  with pytest.raises(AssertionError, match='unregistered_export'):
    _check_surface(source + '\n' + declaration, 'bazi')


@pytest.mark.parametrize('declaration', [
  '__all__ = factory()', '__all__ *= 2', '__all__.clear()', '__all__ = [1]',
  '__all__[:] = ["changed"]', '__all__[0] = "changed"', '(__all__, _other) = (["changed"], None)',
  '(__all__, _other) = ["changed", "kept"]',
])
def test_unsupported_exports_fail_loudly(declaration: str) -> None:
  with pytest.raises(AssertionError):
    _declared_all(ast.parse(declaration).body)


def test_static_modules_reject_phantom_names(monkeypatch: pytest.MonkeyPatch) -> None:
  for module in STATIC_MODULES:
    source = ROOT.joinpath(*module.split('.')).with_suffix('.py').read_text(encoding='utf-8')
    _check_surface(source, module)
    with monkeypatch.context() as patcher:
      patcher.setitem(PUBLIC_NAMES, module, PUBLIC_NAMES[module] + ' phantom_func')
      with pytest.raises(AssertionError, match='phantom_func'):
        _check_surface(source, module)


def test_package_exports_keep_v200_names() -> None:
  assert EXPLICIT_EXPORT_BASELINE['source_sha'] == 'ddfe16e7c51d695167b09cc4c2f64ba46e7565c3'
  for module in EXPLICIT_EXPORTS:
    path = ROOT.joinpath(*module.split('.')) / '__init__.py'
    _check_explicit_exports(path.read_text(encoding='utf-8'), module)
  source = (ROOT / 'bazi/__init__.py').read_text(encoding='utf-8')
  tree = ast.parse(source)
  assignment = next(node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == '__all__' for target in node.targets))
  assert assignment.end_lineno is not None
  lines = source.splitlines(keepends=True)
  declaration = ''.join(lines[assignment.lineno - 1:assignment.end_lineno])
  assert declaration.count("'bazi_chart',") == 1
  with pytest.raises(AssertionError, match='Explicit exports differ'):
    _check_explicit_exports(source.replace(declaration, declaration.replace("'bazi_chart',", '')), 'bazi')
  del lines[assignment.lineno - 1:assignment.end_lineno]
  with pytest.raises(AssertionError, match='Explicit exports differ'):
    _check_explicit_exports(''.join(lines), 'bazi')
  module = 'bazi.calendar'
  assert 'solar_time' in PUBLIC_NAMES[module].split()
  assert 'solar_time' not in EXPLICIT_EXPORTS[module]
  calendar_source = (ROOT / 'bazi/calendar/__init__.py').read_text(encoding='utf-8')
  with pytest.raises(AssertionError, match='Explicit exports differ'):
    _check_explicit_exports(calendar_source + '\n__all__.append("solar_time")\n', module)


def test_contract_covers_consumers_and_exports() -> None:
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
    for name in _declared_all(ast.parse(path.read_text(encoding='utf-8')).body):
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
