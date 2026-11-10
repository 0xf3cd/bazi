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
  index = '''API 参考
========

按要完成的任务选择入口；完整模块索引在下方。函数签名给出类型，Args / Return 说明参数与结果的含义。
示例可整块运行：带输出的代码后紧随 text 对照，其余代码用 assert 写出预期结果。

排盘、配置与文本
----------------

- :py:class:`bazi.bazi.Bazi` 创建八字，:py:class:`bazi.bazi_chart.BaziChart` 读取四柱与派生结果。
- :py:class:`bazi.school.BaziConfig` 和 :py:class:`bazi.school.BaziSchool` 选择精度、历法与流派。
- :py:mod:`bazi.chart_text` 输出命盘文字；终端调用见 :doc:`../guides/cli`。

关系、神煞与流运
----------------

- :py:mod:`bazi.utils.tiangan_utils`、:py:mod:`bazi.utils.dizhi_utils` 查询单组关系或搜索组合。
- :py:mod:`bazi.utils.shensha_utils` 查单项神煞，:py:mod:`bazi.analyzer.relationship` 读取命盘分析。
- :py:class:`bazi.transit_chart.TransitChart` 按年、月、日期或时刻查询流运；
  :py:mod:`bazi.analyzer.facts` 保留通根、透干的具体位置。

知识、出处与前提匹配
--------------------

- :py:class:`bazi.knowledge.KnowledgeBase` 查条文与出处；按中文名浏览见 :doc:`../catalog/index`。
- :py:mod:`bazi.context_matching` 查判据、选择观察范围并求值；操作步骤见 :doc:`../guides/integration`。
- :py:mod:`bazi.rules` 给出规则表及定义选项，表值按键查阅，不在页面展开全部内容。

历法、领域值与结果结构
----------------------

- :py:mod:`bazi.calendar` 选择历法后端，:py:mod:`bazi.calendar.utils_protocol` 说明两后端的共同接口。
- :py:mod:`bazi.defines` 定义天干、地支等领域值；:py:mod:`bazi.data_types` 定义四柱数据容器。
- :py:mod:`bazi.utils.bazi_utils` 提供十神、纳音、藏干等纯查询。
- :doc:`../api-contract` 说明对象身份、输入校验与结果不可变性。

离线数据工具
------------

以下入口用于在源码仓重建随库表，不是排盘或修复安装的步骤；安装版缺表应重新安装。
构建文档只导入这些模块读取说明，不执行下载或生成入口。

- :py:mod:`bazi.calendar.hko_data.encoder` 下载并编码 HKO 历书；下载时另需 requests。
- :py:mod:`bazi.calendar.celestial_data.generator` 生成 celestial 数据；另需与
  :py:data:`bazi.calendar.celestial_data.generator.CELESTIAL_VERSION` 一致的 celestial-calendar。

完整模块索引
------------

.. toctree::
   :maxdepth: 1

'''
  (out / 'index.rst').write_text(index + ''.join('   ' + page + '\n' for page in pages), encoding='utf-8')
