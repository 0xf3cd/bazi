from importlib import import_module
from typing import Any, Final

from . import calendar
from . import school

from . import common
from . import defines
from . import rules
from . import utils
from . import descriptions

__all__ = [
  'common', 'defines', 'calendar', 'school', 'bazi', 'bazi_chart', 'rules', 'utils',
  'analyzer', 'descriptions', 'interpreter', 'transits', 'transit_chart',
]

# Since #66, `Bazi` / `BaziChart` resolve their calendar backend lazily (see
# `calendar/backend.py`), so importing them no longer loads any calendar
# data -- that now happens on the first `Bazi` construction. Keep these submodules
# lazy (PEP 562) regardless: `import src` stays cheap, and the offline encoder
# (`python -m src.calendar.hko_data.encoder`) can never accidentally pull in the
# chart layer.
_LAZY_SUBMODULES: Final[frozenset[str]] = frozenset({
  'bazi', 'bazi_chart', 'analyzer', 'interpreter', 'transits', 'transit_chart',
})

def __getattr__(name: str) -> Any:
  if name in _LAZY_SUBMODULES:
    return import_module(f'.{name}', __name__)
  raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
