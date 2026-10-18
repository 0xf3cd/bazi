'''八字排盘与知识查询。

排盘从 bazi.bazi.Bazi 和 bazi.bazi_chart.BaziChart 开始；
独立查阅知识使用 bazi.knowledge.KnowledgeBase，无需创建命盘。
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
_LAZY_SUBMODULES: Final[frozenset[str]] = frozenset({
  'bazi', 'bazi_chart', 'analyzer', 'knowledge', 'context_matching', 'transits', 'transit_chart',
})

def __getattr__(name: str) -> Any:
  if name in _LAZY_SUBMODULES:
    return import_module(f'.{name}', __name__)
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
