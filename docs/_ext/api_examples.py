# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''从源码发现 API 示例，核对页面代码后在独立进程执行。'''

import ast
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from markdown_it import MarkdownIt

from house_docstrings import source_attribute_docs


'''出生精度的 Examples 是三个粒度的文字对照，不是待执行程序。'''
PROSE_EXAMPLES: Final[frozenset[str]] = frozenset({'bazi.school.BaziPrecision'})

@dataclass(frozen=True)
class ApiExample:
  module: str
  owner: str
  code: str
  output: str | None


def collect_examples(package: Path) -> tuple[ApiExample, ...]:
  '''从全部 AST docstring 与属性说明发现示例，每例须有 Python 围栏及输出或断言。'''
  documents: dict[str, tuple[str, str]] = {}

  def walk(node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef, name: str, module: str) -> None:
    documents[name] = module, ast.get_docstring(node) or ''
    for child in node.body:
      if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        walk(child, name + '.' + child.name, module)

  modules = []
  for path in sorted(package.rglob('*.py')):
    module = '.'.join(path.relative_to(package.parent).with_suffix('').parts).removesuffix('.__init__')
    modules.append(module)
    walk(ast.parse(path.read_text(encoding='utf-8')), module, module)
  for name, lines in source_attribute_docs(package).items():
    module = max((module for module in modules if name.startswith(module + '.')), key=len)
    documents[name] = module, '\n'.join(lines)

  parser = MarkdownIt('commonmark')
  examples = []
  prose: set[str] = set()
  for name, (module, text) in documents.items():
    fences = [token for token in parser.parse(text) if token.type in ('fence', 'code_block')]
    has_heading = re.search(r'^(?:Examples|Usage)[:：]', text, re.MULTILINE) is not None
    if not fences and not has_heading:
      continue
    if name in PROSE_EXAMPLES:
      assert has_heading and not fences, ('Prose example gained code', name)
      prose.add(name)
      continue
    assert [token.info for token in fences] in (['python'], ['python', 'text']), ('API example fences', name)
    code = fences[0].content
    output = fences[1].content if len(fences) == 2 else None
    tree = ast.parse(code, filename=name)
    assert output is not None or any(isinstance(node, ast.Assert) for node in ast.walk(tree)), ('Missing expected result', name)
    examples.append(ApiExample(module, name, code, output))
  assert prose == PROSE_EXAMPLES, ('Prose example coverage', sorted(PROSE_EXAMPLES - prose))
  return tuple(examples)


def check_example_blocks(examples: tuple[ApiExample, ...], pages: Mapping[str, Sequence[str]]) -> None:
  '''实际 HTML 必须显示受测代码与输出；多出的普通围栏也不能漏验。'''
  expected: dict[str, Counter[str]] = defaultdict(Counter)
  for example in examples:
    page = 'api/' + example.module.replace('.', '-') + '.html'
    expected[page][example.code] += 1
    if example.output is not None:
      expected[page][example.output] += 1
  assert expected.keys() <= pages.keys(), ('Missing API example pages', expected.keys() - pages.keys())
  for filename, blocks in pages.items():
    if filename.startswith('api/'):
      actual = Counter(blocks)
      wanted = expected.get(filename, Counter())
      assert actual == wanted, ('Rendered API examples', filename, 'extra', actual - wanted, 'missing', wanted - actual)


def run_example(example: ApiExample, root: Path, timeout: float = 30) -> None:
  '''每例独立工作目录与进程，不借用上一例的变量或导入。'''
  with tempfile.TemporaryDirectory(prefix='bazi-api-example-') as directory:
    try:
      result = subprocess.run(
        [sys.executable, '-B', '-c', example.code],
        cwd=directory, env=os.environ | {'PYTHONPATH': str(root), 'PYTHONIOENCODING': 'utf-8'},
        capture_output=True, text=True, encoding='utf-8', timeout=timeout, check=False,
      )
    except subprocess.TimeoutExpired as error:
      raise RuntimeError('API example timed out: ' + example.owner) from error
    assert result.returncode == 0, (example.owner, result.stdout, result.stderr)
    assert result.stdout == (example.output or ''), ('API example output', example.owner, result.stdout, example.output)
    assert not result.stderr, ('API example stderr', example.owner, result.stderr)
