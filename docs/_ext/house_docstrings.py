# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''按源码归属呈现赋值说明，以 MyST 解析既有中文 docstring。'''

import ast
import inspect
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final, cast

from docutils import nodes
from docutils.utils import new_document
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from myst_parser.parsers.mdit import create_md_parser
from myst_parser.parsers.sphinx_ import MystParser
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

import bazi


'''docstring 节标题词表；源码实际使用 Args / Return / Note / Examples / Usage，Returns / Raises 保持既有格式兼容。'''
HEADER_WORDS: Final[tuple[str, ...]] = ('Args', 'Return', 'Returns', 'Note', 'Examples', 'Raises', 'Usage')

HEADER = re.compile(r'^(?:' + '|'.join(HEADER_WORDS) + ')[:：]')


def source_attribute_docs(package: Path) -> dict[str, list[str]]:
  '''上方说明优先；下方说明仅在不属于下一赋值时采用。无说明显式留空。'''
  docs: dict[str, list[str]] = {}

  def targets(node: ast.stmt) -> list[str]:
    if isinstance(node, ast.Assign):
      return [target.id for target in node.targets if isinstance(target, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
      return [node.target.id]
    return []

  def string(node: ast.stmt) -> str | None:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
      return node.value.value
    return None

  def owns_above(body: Sequence[ast.stmt], index: int) -> bool:
    return (1 <= index < len(body) - 1 and string(body[index]) is not None
            and bool(targets(body[index + 1])) and body[index].end_lineno == body[index + 1].lineno - 1)

  def walk(body: Sequence[ast.stmt], prefix: str) -> None:
    for index, node in enumerate(body):
      if isinstance(node, ast.ClassDef):
        walk(node.body, prefix + '.' + node.name)
      names = targets(node)
      if not names:
        continue
      text = None
      if owns_above(body, index - 1):
        text = string(body[index - 1])
        before = body[index - 2]
        if targets(before) and before.end_lineno == body[index - 1].lineno - 1:
          raise ValueError(f'Ambiguous attribute description: {prefix}:{body[index - 1].lineno}')
      elif index + 1 < len(body) and string(body[index + 1]) is not None and not owns_above(body, index + 1):
        text = string(body[index + 1])
      for name in names:
        docs[prefix + '.' + name] = inspect.cleandoc(text).splitlines() if text else []

  for path in sorted(package.rglob('*.py')):
    module = '.'.join(path.relative_to(package.parent).with_suffix('').parts).removesuffix('.__init__')
    walk(ast.parse(path.read_text(encoding='utf-8')).body, module)
  return docs


def prepare_markdown(content: list[str], parser: MarkdownIt) -> list[str]:
  '''仅在渲染器判为段落的区间分隔标题，不改代码或原始 HTML。'''
  editable: set[int] = set()
  for token in parser.parse('\n'.join(content)):
    if token.type == 'paragraph_open' and token.map is not None:
      editable.update(range(*token.map))
  lines: list[str] = []
  for index, line in enumerate(content):
    header = index in editable and HEADER.match(line)
    if header and lines and lines[-1].strip():
      lines.append('')
    lines.append(line)
    if header and line.rstrip().endswith((':', '：')):
      lines.append('')
  return lines


class HouseDocstring(SphinxDirective):
  has_content = True

  def run(self) -> list[nodes.Node]:
    document = new_document(self.get_source_info()[0], settings=self.state.document.settings)
    parser = create_md_parser(cast(Any, self.env).myst_config, RendererHTML)
    lines = prepare_markdown(list(self.content), parser)
    MystParser().parse('\n'.join(lines), document)
    return list(document.children)


def process_docstring(
  app: Sphinx, what: str, name: str, obj: Any, options: Any, lines: list[str],
) -> None:
  docs = cast(Any, app.env).bazi_attribute_docs
  if name in docs:
    lines[:] = docs[name]
  if lines:
    lines[:] = ['.. house-docstring::', '', *('   ' + line for line in lines), '']


def collect_attribute_docs(app: Sphinx) -> None:
  '''赋值归属表是构建期状态，挂在 env 生命周期上，不注册为 config。'''
  cast(Any, app.env).bazi_attribute_docs = source_attribute_docs(Path(bazi.__file__).resolve().parent)


def setup(app: Sphinx) -> dict[str, bool]:
  app.connect('builder-inited', collect_attribute_docs)
  app.add_directive('house-docstring', HouseDocstring)
  app.connect('autodoc-process-docstring', process_docstring)
  return {'parallel_read_safe': True, 'parallel_write_safe': True}
