# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''源码链接绑定构建提交；标准库类型链接使用构建解释器的文档版本。'''

import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment

import bazi


EXTERNAL_TYPES = {
  'datetime.datetime': 'datetime', 'datetime.date': 'datetime', 'datetime.tzinfo': 'datetime',
  'random.Random': 'random', 'pathlib.Path': 'pathlib', 'struct.Struct': 'struct',
  **{f'collections.abc.{name}': 'collections.abc' for name in ('Mapping', 'Sequence', 'Generator', 'Set', 'Callable')},
}


def missing_reference(
  app: Sphinx, env: BuildEnvironment, node: nodes.Element, content: nodes.Node,
) -> nodes.reference | None:
  target = node['reftarget']
  if target not in EXTERNAL_TYPES:
    return None
  version = f'{sys.version_info.major}.{sys.version_info.minor}'
  uri = f'https://docs.python.org/{version}/library/{EXTERNAL_TYPES[target]}.html#{target}'
  return nodes.reference('', '', content, refuri=uri, internal=False)


def linkcode_resolve(domain: str, info: dict[str, str]) -> str | None:
  if domain != 'py' or not info.get('module'):
    return None
  module = importlib.import_module(info['module'])
  obj: Any = module
  for name in info.get('fullname', '').split('.'):
    if not name:
      continue
    if not hasattr(obj, name):
      return None
    obj = getattr(obj, name)
  if isinstance(obj, property):
    obj = obj.fget
  try:
    path = inspect.getsourcefile(obj)
    lines, start = inspect.getsourcelines(obj)
  except (TypeError, OSError):
    path = getattr(module, '__file__', None)
    lines, start = [], 0
  if path is None:
    return None
  root = Path(bazi.__file__).resolve().parent.parent
  try:
    relative = Path(path).resolve().relative_to(root)
  except ValueError:
    return None
  ref = quote(os.environ['BAZI_DOC_REF'], safe='')
  anchor = f'#L{start}-L{start + len(lines) - 1}' if lines else ''
  return f'https://github.com/0xf3cd/bazi/blob/{ref}/{relative.as_posix()}{anchor}'
