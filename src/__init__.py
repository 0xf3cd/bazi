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
  'Analyzer', 'Descriptions', 'Interpreter', 'TransitChart',
]

# `Bazi` / `BaziChart` (and everything built on top of them) instantiate the HKO
# decoder databases at import time, which requires the encoded data files to be
# present. Import them lazily (PEP 562) so the offline encoder
# (`python -m src.Calendar.HkoData.Encoder`) can still run when the data is missing.
_LAZY_SUBMODULES: Final[frozenset[str]] = frozenset({
  'Bazi', 'BaziChart', 'Analyzer', 'Interpreter', 'TransitChart',
})

def __getattr__(name: str) -> Any:
  if name in _LAZY_SUBMODULES:
    return import_module(f'.{name}', __name__)
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
