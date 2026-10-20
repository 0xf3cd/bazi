# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''在 autodoc 回写注解前，按运行时语义求值公开模块的 TypedDict 字段。

Python 3.14 首次读取子类注解时才合并基类字段。Sphinx 回写基类
__annotations__ 会清除其 __annotate__，使随后求值的子类丢失继承字段。
此扩展只预先读取，不改类型或字段；全量地址检查另行核对生成结果。
'''

import importlib
import inspect
import typing
from collections.abc import Iterator
from typing import Any

from sphinx.application import Sphinx

from api_contract import PUBLIC_NAMES


def _classes(owner: object, qualname: str) -> Iterator[type[Any]]:
  for value in vars(owner).values():
    if inspect.isclass(value) and value.__qualname__ == f'{qualname}.{value.__name__}'.lstrip('.'):
      yield value
      yield from _classes(value, value.__qualname__)


def materialize_typeddict_fields(app: Sphinx) -> None:
  '''模块集合直接取自公开契约；文档构建导入这些模块，但不执行离线下载与生成入口。'''
  for name in PUBLIC_NAMES:
    module = importlib.import_module(name)
    for cls in _classes(module, ''):
      if cls.__module__ == name and typing.is_typeddict(cls):
        _ = cls.__annotations__


def setup(app: Sphinx) -> dict[str, bool]:
  app.connect('builder-inited', materialize_typeddict_fields)
  return {'parallel_read_safe': True, 'parallel_write_safe': True}
