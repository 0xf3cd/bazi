# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import sys
from pathlib import Path

import pytest

pytest.importorskip('sphinx', reason='Documentation dependencies are checked by the separate docs task.')

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'docs/_ext'))

import api_examples
from api_examples import ApiExample, check_example_blocks, collect_examples, run_example


@pytest.fixture
def example_package(tmp_path, monkeypatch):
  package = tmp_path / 'sample'
  package.mkdir()
  monkeypatch.setattr(api_examples, 'PROSE_EXAMPLES', frozenset())
  return package


def write_example(package, body):
  (package / '__init__.py').write_text("def demo():\n  '''Examples:\n" + body + "\n  '''\n", encoding='utf-8')


@pytest.mark.parametrize('definition, owner', [
  ("'''{doc}'''", 'sample'),
  ("def demo():\n  '''{doc}'''", 'sample.demo'),
  ("async def demo():\n  '''{doc}'''", 'sample.demo'),
  ("class Demo:\n  '''{doc}'''", 'sample.Demo'),
  ("class Demo:\n  @property\n  def value(self):\n    '''{doc}'''", 'sample.Demo.value'),
  ("value = 1\n'''{doc}'''", 'sample.value'),
  ("raise RuntimeError('Do not import this source')\n'''{doc}'''\nvalue = 1", 'sample.value'),
])
def test_source_shapes_are_discovered(example_package, definition, owner):
  doc = '```python\nassert True\n```'
  (example_package / '__init__.py').write_text(definition.format(doc=doc), encoding='utf-8')
  assert collect_examples(example_package) == (ApiExample('sample', owner, 'assert True\n', None),)


@pytest.mark.parametrize('body, message', [
  ('  ```python\n  assert True\n  ```', None),
  ('  ```python\n  print("result")\n  ```\n  ```text\n  result\n  ```', None),
  ('  No runnable example.', 'API example fences'),
  ('  ```\n  assert True\n  ```', 'API example fences'),
  ('  ```text\n  assert True\n  ```', 'API example fences'),
  ('  ```javascript\n  assert True\n  ```', 'API example fences'),
  ('  ```python\n  x = 1\n  ```', 'Missing expected result'),
  ('  ```python\n  assert True\n  ```\n  ```python\n  assert True\n  ```', 'API example fences'),
])
def test_each_example_needs_code_and_expectation(example_package, body, message):
  write_example(example_package, body)
  if message is None:
    assert len(collect_examples(example_package)) == 1
  else:
    with pytest.raises(AssertionError, match=message):
      collect_examples(example_package)


def test_removed_examples_leave_no_registration(example_package):
  write_example(example_package, '  ```python\n  assert True\n  ```')
  assert len(collect_examples(example_package)) == 1
  (example_package / '__init__.py').write_text('def demo():\n  pass\n', encoding='utf-8')
  assert collect_examples(example_package) == ()


def test_new_examples_are_discovered(example_package):
  write_example(example_package, '  ```python\n  assert True\n  ```')
  (example_package / 'extra.py').write_text("'''```python\nassert True\n```'''", encoding='utf-8')
  assert {example.owner for example in collect_examples(example_package)} == {'sample.demo', 'sample.extra'}


@pytest.mark.parametrize('defect', [None, 'missing-page', 'missing-code', 'changed-output', 'extra-code'])
def test_visible_code_and_output_match(defect):
  example = ApiExample('sample', 'sample.demo', "print('result')\n", 'result\n')
  assert example.output is not None
  pages = {'api/sample.html': [example.code, example.output]}
  if defect == 'missing-page':
    pages.clear()
  elif defect == 'missing-code':
    pages['api/sample.html'].pop(0)
  elif defect == 'changed-output':
    pages['api/sample.html'][-1] = 'wrong\n'
  elif defect == 'extra-code':
    pages['api/sample.html'].append('assert False\n')
  if defect is None:
    check_example_blocks((example,), pages)
  else:
    with pytest.raises(AssertionError):
      check_example_blocks((example,), pages)


def test_indented_programs_are_not_filtered(example_package):
  write_example(example_package, '  Indented program:\n\n      assert False')
  with pytest.raises(AssertionError, match='API example fences'):
    collect_examples(example_package)


@pytest.mark.parametrize('code, output, message', [
  ('assert 2 + 2 == 4\n', None, None),
  ("print('result')\n", 'result\n', None),
  ('assert False\n', None, 'sample.demo'),
  ("print('wrong')\n", 'result\n', 'API example output'),
  ("import sys\nsys.stderr.write('warning')\n", None, 'API example stderr'),
  ('print(missing_input)\n', None, 'sample.demo'),
])
def test_execution_checks_failures_and_output(code, output, message):
  example = ApiExample('sample', 'sample.demo', code, output)
  if message is None:
    run_example(example, ROOT)
  else:
    with pytest.raises(AssertionError, match=message):
      run_example(example, ROOT)


def test_nonterminating_example_times_out():
  example = ApiExample('sample', 'sample.demo', 'while True:\n  pass\n', None)
  with pytest.raises(RuntimeError, match='API example timed out: sample.demo'):
    run_example(example, ROOT, timeout=0.2)


def test_examples_do_not_share_state(tmp_path, monkeypatch):
  marker = tmp_path / 'marker'
  marker.write_bytes(b'keep caller file')
  monkeypatch.chdir(tmp_path)
  first = ApiExample('sample', 'sample.first', "from pathlib import Path\nPath('marker').touch()\nx = 1\n", None)
  second = ApiExample('sample', 'sample.second', "from pathlib import Path\nassert not Path('marker').exists()\nassert 'x' not in globals()\n", None)
  run_example(first, ROOT)
  run_example(second, ROOT)
  assert marker.read_bytes() == b'keep caller file'
  assert set(tmp_path.iterdir()) == {marker}
