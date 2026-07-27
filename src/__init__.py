from importlib import import_module
from typing import Any, Final

from . import Calendar

from . import Common
from . import Defines
from . import Rules
from . import Utils
from . import Descriptions

__all__ = [
  'Common', 'Defines', 'Calendar', 'Bazi', 'BaziChart', 'Rules', 'Utils', 
  'Analyzer', 'Descriptions', 'Interpreter', 'Transits', 'TransitChart',
]

# Since #66, `Bazi` / `BaziChart` resolve their calendar backend lazily (see
# `Calendar/CalendarBackend.py`), so importing them no longer loads any calendar
# data -- that now happens on the first `Bazi` construction. Keep these submodules
# lazy (PEP 562) regardless: `import src` stays cheap, and the offline encoder
# (`python -m src.Calendar.HkoData.Encoder`) can never accidentally pull in the
# chart layer.
_LAZY_SUBMODULES: Final[frozenset[str]] = frozenset({
  'Bazi', 'BaziChart', 'Analyzer', 'Interpreter', 'Transits', 'TransitChart',
})

def __getattr__(name: str) -> Any:
  if name in _LAZY_SUBMODULES:
    return import_module(f'.{name}', __name__)
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
