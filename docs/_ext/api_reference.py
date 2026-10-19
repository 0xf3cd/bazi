# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''从显式公开契约生成 API 参考页；签名与说明仍由 autodoc 读取源码。

名字解析只按契约中的基类表达式汇总声明成员：外部基类在 EXTERNAL_BASES 显式列出，
本库基类解析不到或多于一个候选立即抛错，不能静默漏掉继承成员。生成的 rst 由
run_docs 在构建前写入源目录，本模块不注册 Sphinx 指令。
'''

import importlib
import inspect
from pathlib import Path
from typing import Final

from api_contract import ALIASES, BASES, DECLARED_MEMBERS, PRIVATE_BASE_MEMBERS, PUBLIC_NAMES, REEXPORTS


'''外部基类不贡献契约成员；显式登记跳过项，不靠查不到时落空。'''
EXTERNAL_BASES: Final[frozenset[str]] = frozenset({
  'TypedDict', 'NamedTuple', 'Protocol', 'Enum', 'IntFlag', 'Generic', 'Mapping',
})


def inherited_members(cls: str) -> set[str]:
  '''按契约基类表达式递归汇总声明成员；解析失败立即抛错。'''
  declared = DECLARED_MEMBERS | PRIVATE_BASE_MEMBERS
  names = set(declared.get(cls, '').split())
  for base in BASES.get(cls, ()):
    base = base.split('[', 1)[0]
    if base in EXTERNAL_BASES:
      continue
    parts = cls.split('.')[:-1]
    qualified = None
    while parts:
      candidate = '.'.join([*parts, base])
      if candidate in declared:
        qualified = candidate
        break
      parts.pop()
    if qualified is None:
      candidates = [name for name in declared if name.endswith('.' + base)]
      if len(candidates) != 1:
        raise ValueError(f'Expected exactly one contract base class for {base}, got {len(candidates)}: {cls}')
      qualified = candidates[0]
    names |= inherited_members(qualified)
  return names


def generate_api(source: Path) -> None:
  '''参考页只消费显式公开契约，签名与说明仍由 autodoc 读取源码。'''
  out = source / 'api'
  out.mkdir()
  pages = []
  for module, names in PUBLIC_NAMES.items():
    filename = module.replace('.', '-')
    pages.append(filename)
    lines = [module, '=' * len(module), '', '.. automodule:: ' + module, '']
    loaded = importlib.import_module(module)
    for name in names.split():
      qualified = module + '.' + name
      if qualified in PUBLIC_NAMES:
        lines.extend([':py:mod:`' + qualified + '`', ''])
        continue
      if qualified in ALIASES:
        lines.extend([
          '.. py:currentmodule:: ' + module, '', '.. py:data:: ' + name, '',
          '   :py:obj:`' + ALIASES[qualified] + '` 的别名。', '',
        ])
        continue
      if qualified in REEXPORTS:
        lines.extend([
          '.. py:currentmodule:: ' + module, '', '.. py:data:: ' + name, '',
          '   :py:obj:`' + REEXPORTS[qualified] + '` 的重导出。', '',
        ])
        continue
      value = getattr(loaded, name)
      directive = 'autoclass' if inspect.isclass(value) else 'autofunction' if inspect.isroutine(value) else 'autodata'
      lines.append('.. ' + directive + ':: ' + qualified)
      members = sorted(inherited_members(qualified)) if directive == 'autoclass' else ()
      if members:
        lines.extend(['   :members: ' + ', '.join(members), '   :undoc-members:'])
      if directive == 'autodata':
        lines.append('   :no-value:')
      lines.append('')
    (out / (filename + '.rst')).write_text('\n'.join(lines), encoding='utf-8')
  index = 'API Reference\n=============\n\n.. toctree::\n   :maxdepth: 1\n\n'
  (out / 'index.rst').write_text(index + ''.join('   ' + page + '\n' for page in pages), encoding='utf-8')
