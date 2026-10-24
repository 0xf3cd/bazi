'''八字排盘与知识查询。

排盘从 bazi.bazi.Bazi 和 bazi.bazi_chart.BaziChart 开始；
独立查阅知识使用 bazi.knowledge.KnowledgeBase，无需创建命盘。
命盘的纯文本展示在 bazi.chart_text。
类型从各定义模块导入，本包不提供根类或安装后的命令行入口。'''

from importlib import import_module
from typing import Any, Final

from . import calendar
from . import school

from . import common
from . import defines
from . import rules
from . import utils

__all__ = [
  'common', 'defines', 'calendar', 'school', 'bazi', 'bazi_chart', 'rules', 'utils',
  'analyzer', 'knowledge', 'context_matching', 'transits', 'transit_chart',
]

# Bazi / BaziChart 延迟解析历法后端，首次构造 Bazi 才加载历法数据，见 calendar/backend.py。
# 子模块仍按 PEP 562 延迟导入，减少 import bazi 的成本，也避免离线 HKO encoder 引入命盘层。
# chart_text 不在 __all__：v2.0.0 的显式导出清单保持不变；它仍是入口子模块，同样按需导入。
_LAZY_SUBMODULES: Final[frozenset[str]] = frozenset({
  'bazi', 'bazi_chart', 'analyzer', 'knowledge', 'context_matching', 'transits', 'transit_chart', 'chart_text',
  'record_migration',
})

# 本包没有根类入口；常见入口类的属性访问会指向定义模块。
_ENTRY_MODULES: Final[common.frozendict[str, str]] = common.frozendict({
  'Bazi':                 'bazi.bazi',
  'BaziChart':            'bazi.bazi_chart',
  'TransitChart':         'bazi.transit_chart',
  'RelationshipAnalyzer': 'bazi.analyzer.relationship',
  'AtBirthAnalysis':      'bazi.analyzer.relationship',
  'TransitAnalysis':      'bazi.analyzer.relationship',
  'BaziConfig':           'bazi.school',
  'KnowledgeBase':        'bazi.knowledge',
})

def __getattr__(name: str) -> Any:
  if name in _LAZY_SUBMODULES:
    return import_module(f'.{name}', __name__)
  if name in _ENTRY_MODULES:
    raise AttributeError(
      f'module {__name__!r} has no attribute {name!r}; use: from {_ENTRY_MODULES[name]} import {name}'
    )
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

def __dir__() -> list[str]:
  # 懒加载子模块尚未导入时不在模块字典里，补上才能被 dir() 与补全发现。
  return sorted({*globals(), *_LAZY_SUBMODULES})
