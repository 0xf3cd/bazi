# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''
Reader for the pre-generated celestial-calendar tables described in `SCHEMA.md`.

This is the **loading layer**, deliberately kept free of any bazi calendar semantics:
it parses a table file, validates it against the schema, and answers point queries.
`CelestialCalendarUtils` sits on top as the query layer.  Keeping the two apart means
that swapping the data source (issue #2 wants live FFI for true solar time) only
replaces this file.

Pure Python on purpose -- the CI matrix includes PyPy, where the dynamic library the
generator uses does not exist.
'''

import re

from datetime import date, datetime
from pathlib import Path
from typing import Final, Optional, TypedDict

from ...Defines import Ganzhi, Jieqi


SCHEMA_VERSION: Final[str] = '1'

DATA_DIR: Final[Path] = Path(__file__).parent / 'data'

JIEQI_COLUMNS: Final[str] = 'year jq_idx name date time'
LUNAR_COLUMNS: Final[str] = 'lunar_year first_solar_date leap_month month_len_bits days_counts ganzhi'

# Table `jq_idx` is defined to be this index.  Asserted at generation time against the
# library's own `get_jieqi_name`, and re-checked per row by `JieqiMomentTable`.
JIEQI_BY_INDEX: Final[list[Jieqi]] = Jieqi.as_list(ganzhi_year=True)
assert len(JIEQI_BY_INDEX) == 24
assert JIEQI_BY_INDEX[0] is Jieqi.立春

# `# key: value` -- exactly one space after the hash.  Continuation lines in the header
# are indented further, so they cannot be mistaken for keys.
_HEADER_KEY: Final[re.Pattern[str]] = re.compile(r'^# (\w+): ?(.*)$')


class LunarYearInfo(TypedDict):
  '''
  Mirrors `HkoData.LunarYearInfo` key for key, so that parity tests can compare the two
  backends' lunar year records as plain dicts.
  '''
  first_solar_day: date
  leap: bool
  leap_month: Optional[int]
  days_counts: list[int]
  ganzhi: Ganzhi


def _parse(path: Path, expected_columns: str) -> tuple[dict[str, str], list[list[str]]]:
  '''
  Split a table file into its provenance header and its data rows, and enforce the
  schema-level invariants that are common to every table.

  Explicit raises (not asserts) throughout: a corrupt or stale data file is a fail-fast
  contract for library consumers, and it must survive `python -O`.
  '''
  if not path.is_file():
    raise RuntimeError(
      f'Celestial data table is missing: {path}. '
      'Run `python -m src.Calendar.CelestialData.Generator` from the repo root to regenerate it.'
    )

  header: dict[str, str] = {}
  rows: list[list[str]] = []
  for line in path.read_text(encoding='utf-8').splitlines():
    if line.startswith('#'):
      matched = _HEADER_KEY.match(line)
      if matched is not None:
        header[matched.group(1)] = matched.group(2).strip()
    else:
      rows.append(line.split())

  if header.get('schema_version') != SCHEMA_VERSION:
    raise ValueError(f'{path}: expected schema_version {SCHEMA_VERSION}, got {header.get("schema_version")!r}')
  if header.get('columns') != expected_columns:
    raise ValueError(f'{path}: expected columns {expected_columns!r}, got {header.get("columns")!r}')
  if header.get('rows') != str(len(rows)):
    raise ValueError(f'{path}: header claims {header.get("rows")!r} rows, parsed {len(rows)}')

  return header, rows


class JieqiMomentTable:
  '''
  The 24 jieqi moments of every supported year, in UTC+08:00 at second granularity.

  A moment of year Y is the one whose *date* falls in calendar year Y -- so 小寒/大寒
  land in January of Y, and rows within a year are not date-sorted.
  '''

  def __init__(self, path: Path = DATA_DIR / 'jieqi_moments.txt', contiguous_years: bool = True) -> None:
    '''
    Args:
    - contiguous_years: whether every year in `[min, max]` must be present, with all 24
      moments.  True for shipped tables -- a hole would make `supported_year_range()` lie
      and turn a supposedly supported year into a `KeyError`.  Test fixtures are sparse
      slices by design and pass False.  Deliberately a constructor argument rather than a
      header key, so that editing a data file cannot weaken the check.
    '''
    self._provenance, rows = _parse(path, JIEQI_COLUMNS)
    self._moments: dict[tuple[int, Jieqi], datetime] = {}

    for year_str, idx_str, name, date_str, time_str in rows:
      jieqi: Jieqi = JIEQI_BY_INDEX[int(idx_str)]
      if name != jieqi.value:
        raise ValueError(f'{path}: jq_idx {idx_str} is {jieqi.value}, but the row says {name!r}')
      key = (int(year_str), jieqi)
      if key in self._moments:
        raise ValueError(f'{path}: duplicate row for {key[0]} {name}')
      self._moments[key] = datetime.fromisoformat(f'{date_str} {time_str}')

    years = {year for year, _ in self._moments}
    self._year_range: Final[range] = range(min(years), max(years) + 1)
    if contiguous_years and len(self._moments) != len(self._year_range) * 24:
      raise ValueError(f'{path}: {len(self._moments)} moments do not cover {self._year_range} x 24')

  @property
  def provenance(self) -> dict[str, str]:
    return dict(self._provenance)

  def supported_year_range(self) -> range:
    '''Note: Gregorian/Solar year / 公历年'''
    return self._year_range

  def get(self, solar_year: int, jieqi: Jieqi) -> datetime:
    return self._moments[(solar_year, jieqi)]


class LunarYearTable:
  '''The first solar day, leap month and month lengths of every supported lunar year.'''

  def __init__(self, path: Path, contiguous_years: bool = True) -> None:
    '''
    Args:
    - contiguous_years: see `JieqiMomentTable.__init__`.
    '''
    self._provenance, rows = _parse(path, LUNAR_COLUMNS)
    self._years: dict[int, LunarYearInfo] = {}

    for year_str, first_str, leap_str, bits_str, counts_str, ganzhi_str in rows:
      leap_month: int = int(leap_str)
      days_counts: list[int] = [int(c) for c in counts_str.split(',')]
      bits: int = int(bits_str, 16)
      decoded: list[int] = [30 if (bits >> i) & 1 else 29 for i in range(len(days_counts))]
      if decoded != days_counts:
        raise ValueError(f'{path}: year {year_str} has month_len_bits {bits_str} '
                         f'(= {decoded}) but days_counts {days_counts}')
      if len(days_counts) != (13 if leap_month else 12):
        raise ValueError(f'{path}: year {year_str} has leap_month {leap_month} '
                         f'but {len(days_counts)} months')

      year: int = int(year_str)
      if year in self._years:
        raise ValueError(f'{path}: duplicate row for year {year}')
      self._years[year] = LunarYearInfo(
        first_solar_day=date.fromisoformat(first_str),
        leap=leap_month != 0,
        # The table spells "no leap month" as 0; HkoData spells it as None. Normalise to
        # HkoData's spelling so the two backends' records compare as plain dicts.
        leap_month=leap_month if leap_month else None,
        days_counts=days_counts,
        ganzhi=Ganzhi.from_str(ganzhi_str),
      )

    self._year_range: Final[range] = range(min(self._years), max(self._years) + 1)
    if contiguous_years and len(self._years) != len(self._year_range):
      raise ValueError(f'{path}: {len(self._years)} years do not cover {self._year_range}')

  @property
  def provenance(self) -> dict[str, str]:
    return dict(self._provenance)

  def supported_year_range(self) -> range:
    '''Note: Lunar year / 农历年'''
    return self._year_range

  def get(self, lunar_year: int) -> LunarYearInfo:
    return self._years[lunar_year]
