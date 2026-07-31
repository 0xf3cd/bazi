# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_celestial_tables.py
#
# Parity layers a/b for the committed CelestialData tables (`src/Calendar/CelestialData/data/`):
# the tables are checked against HkoData DIRECTLY, not through any protocol implementation
# -- so the tables are verified before any consumer exists, and a bad table cannot silently
# poison the charts downstream. The table parser below is deliberately a minimal independent
# reader (not `Loader.py`): writer (`Generator.py`), loader (`Loader.py`), and this reader
# are three independent implementations of the same `SCHEMA.md`, so the schema itself is tested.
#
# NOTE: parity proves EQUIVALENCE, not truth (parity 证的是等价性,不是真值). HkoData and
# celestial algo1 share the HKO official-almanac lineage (official dispositions such as the
# 2033 issue agree by construction); the truth side is covered by celestial's own
# HKO x DE441 dual-axis validation (0.525 min).

import unittest

from datetime import date, datetime
from pathlib import Path
from typing import Final, NamedTuple

from src.Defines import Jieqi, Ganzhi
from src.Calendar import HkoData

# NOTE on the import form: the test suite has no `__init__.py`, so pytest (prepend mode)
# puts this directory itself on sys.path -- the parity data module is imported as a bare
# sibling module. (`from tests.calendar... import` would NOT work at runtime: a stray
# regular `tests` package in site-packages shadows the repo's `tests/` directory.)
from celestial_parity_data import (
  JIEQI_DATE_DIVERGENCES, ALGO2_DIVERGENT_YEARS,
)


DATA_DIR: Final[Path] = Path(__file__).parents[2] / 'src' / 'Calendar' / 'CelestialData' / 'data'

JIEQI_TABLE_PATH: Final[Path] = DATA_DIR / 'jieqi_moments.txt'
ALGO1_TABLE_PATH: Final[Path] = DATA_DIR / 'lunar_years_algo1.txt'
ALGO2_TABLE_PATH: Final[Path] = DATA_DIR / 'lunar_years_algo2.txt'

FIXTURE_DIR: Final[Path] = Path(__file__).parent / 'celestial_fixtures'

JIEQI_LIST: Final[list[Jieqi]] = list(Jieqi)
SEXAGENARY_CYCLE: Final[list[Ganzhi]] = Ganzhi.list_sexagenary_cycle()

# SCHEMA.md's closed provenance namespace, restated here as the assertable form of it.
_COMMON_HEADER_KEYS: Final[frozenset[str]] = frozenset({
  'schema_version', 'celestial_version', 'release_asset', 'dylib_sha256', 'generated_by',
  'generated_on', 'source_api', 'timescale', 'year_range', 'columns', 'rows',
})
JIEQI_HEADER_KEYS: Final[frozenset[str]] = _COMMON_HEADER_KEYS | {'rounding', 'timescale_caveat'}
LUNAR_HEADER_KEYS: Final[frozenset[str]] = _COMMON_HEADER_KEYS | {'algo'}


# ---------------------------------------------------------------------------
# Minimal independent table reader (SCHEMA.md; header continuation lines are folded away)

def _read_table(path: Path) -> tuple[dict[str, str], list[list[str]]]:
  header: dict[str, str] = {}
  rows: list[list[str]] = []
  for line in path.read_text(encoding='utf-8').splitlines():
    if line.startswith('#'):
      # `# key: value` lines are the machine-readable header. Continuation lines
      # (`#` + two spaces, SCHEMA.md) and the title line (no `: `) are prose -- skipped.
      body: str = line[1:]
      if body.startswith(' '):
        body = body[1:]
        if body.startswith(' '):
          continue
        if ': ' in body:
          key, value = body.split(': ', 1)
          header[key] = value
    else:
      rows.append(line.split(' '))
  return header, rows


class _JieqiRow(NamedTuple):
  year:   int
  jq_idx: int
  name:   str
  moment: datetime

def _parse_jieqi_rows(raw_rows: list[list[str]]) -> list[_JieqiRow]:
  return [
    _JieqiRow(
      year=int(fields[0]),
      jq_idx=int(fields[1]),
      name=fields[2],
      moment=datetime.fromisoformat(f'{fields[3]}T{fields[4]}'),
    )
    for fields in raw_rows
  ]


class _LunarRow(NamedTuple):
  lunar_year:       int
  first_solar_date: date
  leap_month:       int
  month_len_bits:   int
  days_counts:      tuple[int, ...]
  ganzhi:           str

def _parse_lunar_rows(raw_rows: list[list[str]]) -> list[_LunarRow]:
  return [
    _LunarRow(
      lunar_year=int(fields[0]),
      first_solar_date=date.fromisoformat(fields[1]),
      leap_month=int(fields[2]),
      month_len_bits=int(fields[3], 16),
      days_counts=tuple(int(count) for count in fields[4].split(',')),
      ganzhi=fields[5],
    )
    for fields in raw_rows
  ]


def _load_jieqi_table() -> tuple[dict[str, str], list[list[str]], list[_JieqiRow]]:
  header, raw_rows = _read_table(JIEQI_TABLE_PATH)
  return header, raw_rows, _parse_jieqi_rows(raw_rows)

def _load_lunar_table(path: Path) -> tuple[dict[str, str], list[_LunarRow]]:
  header, raw_rows = _read_table(path)
  return header, _parse_lunar_rows(raw_rows)


# ---------------------------------------------------------------------------

class TestHeaderKeysAreClosed(unittest.TestCase):
  '''
  SCHEMA.md declares the provenance namespace closed, and a column name must never take a
  key of its own: `# leap_month: 1..12, or 0 when the year has no leap month.` reads to every
  parser here and in `Loader` as a provenance key whose value happens to be a sentence.
  Prose about a column belongs on continuation lines under `columns`.

  The contract is stated in three independent places -- this file, the generator, and the
  loader's regex -- so nothing but a test can keep them from drifting apart.
  '''

  def test_shipped_tables(self) -> None:
    for path, expected in ((JIEQI_TABLE_PATH, JIEQI_HEADER_KEYS),
                           (ALGO1_TABLE_PATH, LUNAR_HEADER_KEYS),
                           (ALGO2_TABLE_PATH, LUNAR_HEADER_KEYS)):
      with self.subTest(table=path.name):
        header, _ = _read_table(path)
        self.assertEqual(frozenset(header), expected)

  def test_fixtures(self) -> None:
    # The fixtures carry one key more and are otherwise the same format, which is the whole
    # point of them: a Loader that passes on a fixture is reading the shipped layout.
    for name, expected in (('jieqi_moments.txt', JIEQI_HEADER_KEYS),
                           ('lunar_years_algo1.txt', LUNAR_HEADER_KEYS),
                           ('lunar_years_algo2.txt', LUNAR_HEADER_KEYS)):
      with self.subTest(fixture=name):
        header, _ = _read_table(FIXTURE_DIR / name)
        self.assertEqual(frozenset(header), expected | {'fixture'})


class TestJieqiTableShape(unittest.TestCase):
  '''The jieqi table itself: row count, ordering, jq_idx <-> name, the 小寒/大寒 January note.'''

  def test_header_and_row_count(self) -> None:
    header, raw_rows, _ = _load_jieqi_table()
    self.assertEqual(header['columns'], 'year jq_idx name date time')
    self.assertEqual(header['rows'], '4800') # 200 years x 24 jieqis, exact.
    self.assertEqual(len(raw_rows), 4800)
    self.assertEqual(header['schema_version'], '1')
    self.assertEqual(header['celestial_version'], '0.4.0')
    self.assertEqual(header['timescale'].split(',')[0], 'UTC+08:00')
    self.assertEqual(header['rounding'].split(' ')[0], 'truncate')

  def test_row_sequence_and_names(self) -> None:
    _, raw_rows, rows = _load_jieqi_table()
    for i, (fields, row) in enumerate(zip(raw_rows, rows)):
      self.assertEqual(fields[1], f'{i % 24:02d}') # jq_idx is zero-padded.
      self.assertEqual(row.year, 1901 + i // 24)   # Rows ascend by (year, jq_idx).
      self.assertEqual(row.jq_idx, i % 24)
      self.assertEqual(row.name, JIEQI_LIST[row.jq_idx].value)
      self.assertEqual(row.moment.microsecond, 0)  # Truncated to whole seconds.
      if row.jq_idx in (22, 23): # 小寒/大寒 of year Y fall in January of Y (SCHEMA.md note).
        self.assertEqual((row.moment.year, row.moment.month), (row.year, 1))
      else:
        self.assertEqual(row.moment.year, row.year)


class TestJieqiDateParity(unittest.TestCase):
  '''
  Layer b: the table's jieqi DATES vs HkoData, over the whole window (200 x 24 = 4800).
  The divergences must be exactly the frozen whitelist in `celestial_parity_data.py`
  -- the entry count itself is asserted, so a new unexplained divergence turns this red.
  '''

  def test_whitelist_self_consistency(self) -> None:
    self.assertEqual(len(JIEQI_DATE_DIVERGENCES), 7)
    self.assertEqual(len({ (d.year, d.jq_idx) for d in JIEQI_DATE_DIVERGENCES }), 7) # No duplicate keys.
    for divergence in JIEQI_DATE_DIVERGENCES:
      self.assertEqual(divergence.name, JIEQI_LIST[divergence.jq_idx].value)
      self.assertEqual(divergence.is_jie, divergence.jq_idx % 2 == 0)
      self.assertEqual(divergence.celestial_moment.microsecond, 0)
      # Every entry is a midnight-adjacent date flip, never more than one day.
      self.assertEqual(abs((divergence.celestial_moment.date() - divergence.hko_date).days), 1)
    # The only two 节 (month boundaries) are 1917 大雪 and 1927 白露 -- the entries that
    # propagate into the ganzhi-calendar methods.
    self.assertEqual(
      { (d.year, d.name) for d in JIEQI_DATE_DIVERGENCES if d.is_jie },
      { (1917, '大雪'), (1927, '白露') },
    )

  def test_dates_vs_hko(self) -> None:
    hko_jieqi: HkoData.DecodedJieqiDates = HkoData.DecodedJieqiDates()
    _, _, rows = _load_jieqi_table()

    divergences: dict[tuple[int, int], tuple[datetime, date]] = {}
    for row in rows:
      hko_date: date = hko_jieqi.get(row.year, JIEQI_LIST[row.jq_idx])
      if row.moment.date() != hko_date:
        divergences[(row.year, row.jq_idx)] = (row.moment, hko_date)

    # The divergence keys are exactly the whitelist keys -- no more, no fewer.
    self.assertEqual(
      set(divergences),
      { (d.year, d.jq_idx) for d in JIEQI_DATE_DIVERGENCES },
    )

    # ...and each divergence carries exactly the whitelisted values on both sides.
    for divergence in JIEQI_DATE_DIVERGENCES:
      moment, hko_date = divergences[(divergence.year, divergence.jq_idx)]
      self.assertEqual(moment, divergence.celestial_moment)
      self.assertEqual(hko_date, divergence.hko_date)


# ---------------------------------------------------------------------------

class TestLunarTableShape(unittest.TestCase):
  '''The lunar tables themselves: row count, bitmask <-> days_counts round-trip, ganzhi formula.'''

  def _check_shape(self, path: Path) -> list[_LunarRow]:
    header, rows = _load_lunar_table(path)
    self.assertEqual(header['columns'], 'lunar_year first_solar_date leap_month month_len_bits days_counts ganzhi')
    self.assertEqual(header['rows'], '199') # 1901..2099, BOTH algos clamped to this window.
    self.assertEqual(header['year_range'].split(' ')[0], '1901..2099')
    self.assertEqual(len(rows), 199)

    for i, row in enumerate(rows):
      self.assertEqual(row.lunar_year, 1901 + i) # Ascending, contiguous.
      self.assertTrue(0 <= row.leap_month <= 12)
      self.assertEqual(len(row.days_counts), 12 if row.leap_month == 0 else 13)

      # The bitmask must round-trip through days_counts, with no stray high bits.
      self.assertEqual(row.month_len_bits >> len(row.days_counts), 0)
      reencoded: int = 0
      for bit, count in enumerate(row.days_counts):
        self.assertIn(count, (29, 30))
        reencoded |= (1 << bit) if count == 30 else 0
      self.assertEqual(reencoded, row.month_len_bits)

      # The ganzhi column follows the (lunar_year - 4) mod 60 formula.
      self.assertEqual(row.ganzhi, str(SEXAGENARY_CYCLE[(row.lunar_year - 4) % 60]))

      # Lunar new year falls in January/February of the same Gregorian year.
      self.assertEqual(row.first_solar_date.year, row.lunar_year)
      self.assertIn(row.first_solar_date.month, (1, 2))
    return rows

  def test_algo1_shape(self) -> None:
    self._check_shape(ALGO1_TABLE_PATH)

  def test_algo2_shape(self) -> None:
    self._check_shape(ALGO2_TABLE_PATH)


class TestLunarParity(unittest.TestCase):
  '''
  Layer a: the lunar tables vs HkoData, field by field
  (`first_solar_date` / `leap_month` / `days_counts` / `ganzhi`).
  algo1 is HKO-lineage and must match 199/199; algo2 diverges on exactly the six
  whitelisted years (`ALGO2_DIVERGENT_YEARS`).
  '''

  def _hko_differences(self, rows: list[_LunarRow]) -> dict[int, list[str]]:
    '''Field-level differences against HkoData, keyed by lunar year (empty means a match).'''
    hko_lunar: HkoData.DecodedLunarYears = HkoData.DecodedLunarYears()
    differences: dict[int, list[str]] = {}
    for row in rows:
      hko: HkoData.LunarYearInfo = hko_lunar.get(row.lunar_year)
      diffs: list[str] = []
      if row.first_solar_date != hko['first_solar_day']:
        diffs.append(f'first_solar_date {row.first_solar_date} vs HKO {hko["first_solar_day"]}')
      # HkoData spells "no leap month" as None; the table uses 0. Normalise when comparing.
      if (row.leap_month if row.leap_month != 0 else None) != hko['leap_month']:
        diffs.append(f'leap_month {row.leap_month} vs HKO {hko["leap_month"]}')
      if list(row.days_counts) != hko['days_counts']:
        diffs.append(f'days_counts {list(row.days_counts)} vs HKO {hko["days_counts"]}')
      if row.ganzhi != str(hko['ganzhi']):
        diffs.append(f'ganzhi {row.ganzhi} vs HKO {hko["ganzhi"]}')
      if diffs:
        differences[row.lunar_year] = diffs
    return differences

  def test_algo1_matches_hko_strictly(self) -> None:
    _, rows = _load_lunar_table(ALGO1_TABLE_PATH)
    self.assertEqual(len(rows), 199)
    # 199/199: any field-level difference in any year fails the test, with details.
    self.assertEqual(self._hko_differences(rows), {})

  def test_algo2_diverges_exactly_on_whitelist_years(self) -> None:
    _, rows = _load_lunar_table(ALGO2_TABLE_PATH)
    self.assertEqual(len(rows), 199)
    differences: dict[int, list[str]] = self._hko_differences(rows)
    self.assertEqual(sorted(differences), list(ALGO2_DIVERGENT_YEARS))
    self.assertEqual(len(differences), 6)

  def test_ganzhi_matches_hko(self) -> None:
    hko_lunar: HkoData.DecodedLunarYears = HkoData.DecodedLunarYears()
    for path in (ALGO1_TABLE_PATH, ALGO2_TABLE_PATH):
      _, rows = _load_lunar_table(path)
      mismatches: list[str] = [
        f'{row.lunar_year}: {row.ganzhi} vs HKO {hko_lunar.get(row.lunar_year)["ganzhi"]}'
        for row in rows
        if row.ganzhi != str(hko_lunar.get(row.lunar_year)['ganzhi'])
      ]
      self.assertEqual(mismatches, []) # 199/199 for both tables.


class TestAlgo1Algo2MutualDiff(unittest.TestCase):
  '''
  The documentary algo1 x algo2 diff: since algo1 matches HKO 199/199, algo2's
  differences from HKO are exactly its differences from algo1 -- the same six years
  as celestial `src/test/lunar/diff_test.cpp`.
  '''

  def test_divergent_years(self) -> None:
    _, algo1_rows = _load_lunar_table(ALGO1_TABLE_PATH)
    _, algo2_rows = _load_lunar_table(ALGO2_TABLE_PATH)
    self.assertEqual([r.lunar_year for r in algo1_rows], [r.lunar_year for r in algo2_rows])

    divergent_years: list[int] = []
    for algo1_row, algo2_row in zip(algo1_rows, algo2_rows):
      # The ganzhi column derives from the lunar year alone, so it never diverges.
      self.assertEqual(algo1_row.ganzhi, algo2_row.ganzhi)
      if (algo1_row.first_solar_date, algo1_row.leap_month, algo1_row.month_len_bits, algo1_row.days_counts) != \
         (algo2_row.first_solar_date, algo2_row.leap_month, algo2_row.month_len_bits, algo2_row.days_counts):
        divergent_years.append(algo1_row.lunar_year)

    self.assertEqual(divergent_years, list(ALGO2_DIVERGENT_YEARS))


if __name__ == '__main__':
  unittest.main()
