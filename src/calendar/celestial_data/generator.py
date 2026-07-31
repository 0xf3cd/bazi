# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# bazi/src/calendar/celestial_data/generator.py
#
# Regenerate the committed tables under `celestial_data/data/` from the
# celestial-calendar dynamic library, following the frozen contract in `SCHEMA.md`.
#
# This module is an offline tool, only used when the tables need to be regenerated.
# It is not needed at runtime: the runtime side (`loader.py`) is pure Python and only
# reads the committed tables. `ctypes` and the dylib must never leak into any runtime
# module (the CI matrix includes PyPy, where the dylib does not exist).
# Same split as `hko_data/encoder.py` (offline) vs `hko_data/decoder.py` (runtime).
#
# Run from the repo root:
#   python -m src.calendar.celestial_data.generator [--dylib PATH]

import argparse
import ctypes
import hashlib
import json

from ctypes import c_bool, c_char, c_double, c_int32, c_uint8, c_uint16, c_uint32
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Final

from ...defines import Ganzhi, Jieqi


# ---------------------------------------------------------------------------
# Pinned library (version gate)

CELESTIAL_VERSION: Final[str] = '0.4.0'
RELEASE_ASSET: Final[str] = 'celestial-calendar v0.4.0 / macos_arm64.zip'

# The ABI exports no version symbol, so the version gate pins the exact release
# artifact instead: the sha256 of the dylib being loaded (recorded in the release's
# `SHA256SUMS` / `build_info.json`), cross-checked against `build_info.json` when
# it sits next to the dylib. Hash equality implies the exact 0.4.0 build.
EXPECTED_DYLIB_SHA256: Final[str] = '4e102e614e392607720ea24e6b9979bec11cc09338e071ca3f335c0f9914e2d5'

DEFAULT_DYLIB_PATH: Final[Path] = (
  Path.home() / '.cache' / 'celestial-release' / 'v0.4.0-macos-arm64' / 'libcelestial_calendar.0.4.0.dylib'
)

# Table windows (SCHEMA.md): jieqi rows are keyed by Gregorian year, lunar rows by lunar year.
JIEQI_START_YEAR: Final[int] = 1901
JIEQI_END_YEAR:   Final[int] = 2100
LUNAR_START_YEAR: Final[int] = 1901
LUNAR_END_YEAR:   Final[int] = 2099 # BOTH algos clamp to this window; algo2 natively
                                    # reports [410, 5000], a placeholder sentinel.

EXPECTED_JIEQI_ROWS: Final[int] = (JIEQI_END_YEAR - JIEQI_START_YEAR + 1) * 24
EXPECTED_LUNAR_ROWS: Final[int] = LUNAR_END_YEAR - LUNAR_START_YEAR + 1


# ---------------------------------------------------------------------------
# ctypes bindings (layouts verified against `celestial.h`; see SCHEMA.md "ctypes landmine")

class JieqiMomentQuery(ctypes.Structure):
  _fields_ = [
    ('valid',  c_bool),
    ('jq_idx', c_uint8),
    ('y',      c_int32),
    ('m',      c_uint32),
    ('d',      c_uint32),
    ('frac',   c_double),
  ]

class LunarYearInfo(ctypes.Structure):
  # The name mirrors the C struct in `celestial.h` and is unrelated to the identically named
  # `TypedDict` in `loader.py`, which mirrors hko_data's record instead.
  #
  # `month_len` is a scalar uint16, NOT an array: declaring it as `c_uint16 * 13`
  # inflates the struct past the register-return threshold, breaks the struct-by-value
  # ABI, and every call then silently returns `valid = false` (no crash).
  _fields_ = [
    ('valid',      c_bool),
    ('year',       c_int32),
    ('month',      c_uint8),
    ('day',        c_uint8),
    ('leap_month', c_uint8),
    ('month_len',  c_uint16),
  ]

class SupportedLunarYearRange(ctypes.Structure):
  _fields_ = [
    ('valid', c_bool),
    ('start', c_int32),
    ('end',   c_int32),
  ]

# Layout sanity checks, cheap insurance against the landmine above.
assert ctypes.sizeof(JieqiMomentQuery) == 24
assert ctypes.sizeof(LunarYearInfo) == 16


def _check_library_version(dylib_path: Path) -> str:
  '''
  Version gate: refuse to generate from anything but the pinned 0.4.0 release artifact.
  Returns the dylib's sha256 (for the provenance header).
  '''
  digest: str = hashlib.sha256(dylib_path.read_bytes()).hexdigest()
  if digest != EXPECTED_DYLIB_SHA256:
    raise RuntimeError(
      f'Version gate failed: {dylib_path} has sha256 {digest}, '
      f'expected the pinned {CELESTIAL_VERSION} artifact {EXPECTED_DYLIB_SHA256}. '
      'A ΔT refresh or a celestial update changes the numbers; regenerate deliberately.'
    )

  build_info_path: Path = dylib_path.parent / 'build_info.json'
  if build_info_path.exists():
    build_info = json.loads(build_info_path.read_text(encoding='utf-8'))
    if build_info.get('build_version') != CELESTIAL_VERSION:
      raise RuntimeError(
        f'Version gate failed: build_info.json reports {build_info.get("build_version")}, '
        f'expected {CELESTIAL_VERSION}.'
      )
  return digest


def _load_library(dylib_path: Path) -> ctypes.CDLL:
  lib: ctypes.CDLL = ctypes.CDLL(str(dylib_path))

  lib.set_log_verbosity.argtypes = [c_uint8]
  lib.set_log_verbosity.restype = c_bool
  lib.query_jieqi_moment.argtypes = [c_int32, c_uint8]
  lib.query_jieqi_moment.restype = JieqiMomentQuery
  lib.get_jieqi_name.argtypes = [c_uint8, ctypes.POINTER(c_char), c_uint32]
  lib.get_jieqi_name.restype = c_bool
  lib.get_supported_lunar_year_range.argtypes = [c_uint8]
  lib.get_supported_lunar_year_range.restype = SupportedLunarYearRange
  lib.get_lunar_year_info.argtypes = [c_uint8, c_int32]
  lib.get_lunar_year_info.restype = LunarYearInfo

  if not lib.set_log_verbosity(c_uint8(0)): # Keep the library's stdout logging out of the tables' diff noise.
    raise RuntimeError('Failed to silence the library logging.')
  return lib


# ---------------------------------------------------------------------------
# Table rows

@dataclass(frozen=True)
class JieqiRow:
  year:   int
  jq_idx: int      # Identical to bazi's `list(Jieqi)` index (0 = 立春 .. 23 = 大寒).
  name:   str      # Redundant with `jq_idx` on purpose; the loader cross-checks them.
  moment: datetime # UTC+08:00, truncated to whole seconds.

@dataclass(frozen=True)
class LunarRow:
  lunar_year:      int
  first_solar_date: date
  leap_month:      int             # 1..12, or 0 when the year has no leap month.
  month_len_bits:  int             # Raw uint16 from the ABI, LSB-first.
  days_counts:     tuple[int, ...] # Decoded from `month_len_bits`; redundant on purpose.
  ganzhi:          Ganzhi


def _jieqi_name(lib: ctypes.CDLL, jq_idx: int) -> str:
  buf = (c_char * 32)()
  if not lib.get_jieqi_name(c_uint8(jq_idx), buf, c_uint32(32)):
    raise RuntimeError(f'get_jieqi_name({jq_idx}) failed.')
  return buf.value.decode('utf-8')


def _ut1_moment_to_utc8(query: JieqiMomentQuery) -> datetime:
  '''
  UT1 -> UTC+08:00: add exactly 8h to the full moment and re-derive the date
  (the addition rolls the date near midnight -- it must not be applied to the
  time-of-day alone). Then truncate to whole seconds: rounding could carry
  `23:59:59.6` into the next day and silently move a date-level attribution;
  truncation can never change the date.
  '''
  moment: datetime = datetime(query.y, query.m, query.d) + timedelta(days=query.frac) + timedelta(hours=8)
  return moment.replace(microsecond=0)


def _gen_jieqi_rows(lib: ctypes.CDLL) -> list[JieqiRow]:
  jieqi_list: Final[list[Jieqi]] = list(Jieqi)
  assert len(jieqi_list) == 24

  # Cross-check gate, part 1: the ABI's jieqi order must be bazi's `list(Jieqi)` order exactly.
  for idx, jq in enumerate(jieqi_list):
    name: str = _jieqi_name(lib, idx)
    if name != jq.value:
      raise RuntimeError(f'Cross-check gate failed: get_jieqi_name({idx}) is {name}, expected {jq.value}.')

  rows: list[JieqiRow] = []
  for year in range(JIEQI_START_YEAR, JIEQI_END_YEAR + 1):
    for idx, jq in enumerate(jieqi_list):
      query: JieqiMomentQuery = lib.query_jieqi_moment(year, idx)
      # Per-row valid gate: the struct contract signals failure with `valid == false`,
      # silently -- a wrong ctypes layout makes EVERY row invalid without crashing.
      if not query.valid:
        raise RuntimeError(f'Per-row valid gate failed: query_jieqi_moment({year}, {idx}) returned valid = false.')
      if query.jq_idx != idx or query.y != year:
        raise RuntimeError(f'Query echo mismatch: asked for ({year}, {idx}), got ({query.y}, {query.jq_idx}).')
      rows.append(JieqiRow(year=year, jq_idx=idx, name=jq.value, moment=_ut1_moment_to_utc8(query)))

  # Row-count gate, part 1.
  if len(rows) != EXPECTED_JIEQI_ROWS:
    raise RuntimeError(f'Row-count gate failed: {len(rows)} jieqi rows, expected {EXPECTED_JIEQI_ROWS}.')
  return rows


def _decode_month_len_bits(month_len_bits: int, month_count: int) -> tuple[int, ...]:
  '''LSB-first: bit i is the (i+1)-th lunar month in sequence; 1 = 30 days, 0 = 29 days.'''
  return tuple(30 if (month_len_bits >> i) & 1 else 29 for i in range(month_count))

def _encode_days_counts(days_counts: tuple[int, ...]) -> int:
  bits: int = 0
  for i, count in enumerate(days_counts):
    if count == 30:
      bits |= 1 << i
    elif count != 29:
      raise RuntimeError(f'A lunar month has 29 or 30 days, got {count}.')
  return bits


def _gen_lunar_rows(lib: ctypes.CDLL, algo: int) -> list[LunarRow]:
  assert algo in (1, 2)

  year_range: SupportedLunarYearRange = lib.get_supported_lunar_year_range(algo)
  if not year_range.valid:
    raise RuntimeError(f'get_supported_lunar_year_range({algo}) returned valid = false.')
  if year_range.start > LUNAR_START_YEAR or year_range.end < LUNAR_END_YEAR:
    raise RuntimeError(
      f'algo{algo} natively covers [{year_range.start}, {year_range.end}], '
      f'which does not contain the required window [{LUNAR_START_YEAR}, {LUNAR_END_YEAR}].'
    )

  sexagenary_cycle: Final[list[Ganzhi]] = Ganzhi.list_sexagenary_cycle()

  rows: list[LunarRow] = []
  for lunar_year in range(LUNAR_START_YEAR, LUNAR_END_YEAR + 1): # The clamp; see LUNAR_END_YEAR.
    info: LunarYearInfo = lib.get_lunar_year_info(algo, lunar_year)
    # Per-row valid gate.
    if not info.valid:
      raise RuntimeError(f'Per-row valid gate failed: get_lunar_year_info({algo}, {lunar_year}) returned valid = false.')
    if not 0 <= info.leap_month <= 12:
      raise RuntimeError(f'algo{algo} {lunar_year}: leap_month {info.leap_month} out of range.')

    month_count: int = 12 if info.leap_month == 0 else 13
    days_counts: tuple[int, ...] = _decode_month_len_bits(info.month_len, month_count)

    # Cross-check gate, part 2: the bitmask must round-trip, with no stray high bits.
    if info.month_len >> month_count != 0 or _encode_days_counts(days_counts) != info.month_len:
      raise RuntimeError(
        f'Cross-check gate failed: algo{algo} {lunar_year} bitmask 0x{info.month_len:04x} '
        f'does not round-trip through {days_counts}.'
      )

    rows.append(LunarRow(
      lunar_year=lunar_year,
      first_solar_date=date(info.year, info.month, info.day),
      leap_month=info.leap_month,
      month_len_bits=info.month_len,
      days_counts=days_counts,
      ganzhi=sexagenary_cycle[(lunar_year - 4) % 60],
    ))

  # Row-count gate, part 1.
  if len(rows) != EXPECTED_LUNAR_ROWS:
    raise RuntimeError(f'Row-count gate failed: {len(rows)} lunar rows for algo{algo}, expected {EXPECTED_LUNAR_ROWS}.')
  return rows


# ---------------------------------------------------------------------------
# Rendering (header keys are the machine-readable provenance required by SCHEMA.md)

def _common_header(generated_on: date, dylib_sha256: str, source_api: str) -> list[str]:
  return [
    '# schema_version: 1',
    f'# celestial_version: {CELESTIAL_VERSION}',
    f'# release_asset: {RELEASE_ASSET}',
    f'# dylib_sha256: {dylib_sha256}',
    '# generated_by: src/calendar/celestial_data/generator.py',
    f'# generated_on: {generated_on.isoformat()}',
    f'# source_api: {source_api}',
  ]


def _render_jieqi_table(rows: list[JieqiRow], generated_on: date, dylib_sha256: str) -> str:
  header: list[str] = [
    '# celestial-calendar jieqi moment table',
    *_common_header(generated_on, dylib_sha256, 'query_jieqi_moment(int32_t year, uint8_t jq_idx)'),
    '# timescale: UTC+08:00, derived from celestial UT1 moments by adding exactly 8h',
    '# timescale_caveat: UT1-UTC <= 0.9s (1972+); pre-1972 UT1 is a proxy (celestial Phase C).',
    '#   Normally only affects births within +/-0.9s of a jieqi moment -- but when the moment',
    '#   itself sits near midnight, 0.9s flips the whole *date* attribution.',
    '#   Measured worst case in window: 1979 大寒 is 4s from midnight.',
    '# rounding: truncate to whole seconds (sub-second discarded; never carries into the next date)',
    f'# year_range: {JIEQI_START_YEAR}..{JIEQI_END_YEAR} inclusive',
    '# columns: year jq_idx name date time',
    '#   jq_idx is 0..23, identical to the bazi `list(Jieqi)` index (0=立春 .. 23=大寒), and',
    '#   `name` is cross-checked against get_jieqi_name at generation.',
    '#   Rows ascend by (year, jq_idx), which is not date order: 小寒/大寒 (idx 22/23) of',
    '#   year Y fall in January of Y.',
    f'# rows: {len(rows)}',
  ]
  lines: list[str] = [
    f'{row.year} {row.jq_idx:02d} {row.name} {row.moment:%Y-%m-%d} {row.moment:%H:%M:%S}'
    for row in rows
  ]
  return '\n'.join(header + lines) + '\n'


def _render_lunar_table(rows: list[LunarRow], algo: int, generated_on: date, dylib_sha256: str) -> str:
  # Machine-readable header lines carry the bare value only; prose goes to continuation
  # lines (`#` + two spaces) -- the convention `SCHEMA.md` states, so the loader never parses
  # prose as part of a value.  Per-column prose therefore hangs off `columns` rather than
  # taking a key of its own: a `# leap_month: 1..12, or 0 when ...` line reads to the
  # loader as a provenance key whose value is a sentence.
  algo_note: Final[dict[int, str]] = {
    1: 'HKO official almanac lineage -- the default.',
    2: 'Leap-second aware UTC+8 via jde_to_utc8, celestial #84.',
  }
  timescale_note: Final[dict[int, str]] = {
    1: 'HKO official civil dates (no astronomical timescale involved)',
    2: 'leap-second aware UTC+08:00',
  }
  header: list[str] = [
    f'# celestial-calendar lunar year table (algo{algo})',
    *_common_header(generated_on, dylib_sha256, 'get_lunar_year_info(uint8_t algo, int32_t year)'),
    f'# algo: {algo}',
    f'#   {algo_note[algo]}',
    f'# timescale: {timescale_note[algo]}',
    f'# year_range: {LUNAR_START_YEAR}..{LUNAR_END_YEAR} inclusive -- BOTH algos clamped to this window.',
    '#   algo2 natively reports [410, 5000], which is a placeholder sentinel',
    '#   (algo2.hpp:443-446 "actually has no limit, simply use").  Clamping keeps one',
    '#   range contract for both algos.  Widening is a follow-up issue.',
    '# columns: lunar_year first_solar_date leap_month month_len_bits days_counts ganzhi',
    '#   leap_month -- 1..12, or 0 when the year has no leap month.  hko_data spells the same',
    '#   thing as `None`; the loader normalizes.',
    '#   month_len_bits -- raw uint16 from the ABI, LSB-first (bit i = the (i+1)-th lunar',
    '#   month in sequence, leap month occupying its own slot; 1 = 30 days, 0 = 29 days).',
    '#   days_counts -- decoded from month_len_bits, 12 or 13 entries; redundant on purpose,',
    '#   so a hand-edit of either column is caught by the loader cross-check.',
    '#   ganzhi -- (lunar_year - 4) mod 60 over Ganzhi.list_sexagenary_cycle(); not consumed',
    '#   at runtime.  The 199/199 agreement with hko_data is checked by the test suite, not',
    '#   here: see tests/calendar/test_celestial_tables.py.',
    f'# rows: {len(rows)}',
  ]
  lines: list[str] = [
    f'{row.lunar_year} {row.first_solar_date} {row.leap_month} 0x{row.month_len_bits:04x} '
    f'{",".join(map(str, row.days_counts))} {row.ganzhi}'
    for row in rows
  ]
  return '\n'.join(header + lines) + '\n'


def _write_table(path: Path, text: str, expected_rows: int) -> None:
  path.write_text(text, encoding='utf-8', newline='\n') # LF endings, trailing newline, no blank lines.

  # Row-count gate, part 2: the emitted `rows:` header must match the data lines written.
  written_rows: int = sum(1 for line in path.read_text(encoding='utf-8').splitlines() if not line.startswith('#'))
  if written_rows != expected_rows:
    raise RuntimeError(f'Row-count gate failed: {path} holds {written_rows} data rows, header says {expected_rows}.')
  print(f'> Wrote {path} ({expected_rows} rows)')


# ---------------------------------------------------------------------------

def main() -> None:
  argparser = argparse.ArgumentParser(description='Regenerate the celestial_data tables from the celestial-calendar library.')
  argparser.add_argument('--dylib', type=Path, default=DEFAULT_DYLIB_PATH,
                         help=f'Path to the pinned libcelestial_calendar dylib. Default: {DEFAULT_DYLIB_PATH}')
  args = argparser.parse_args()

  dylib_path: Path = args.dylib.expanduser()
  if not dylib_path.is_file():
    raise RuntimeError(f'Dylib not found: {dylib_path}')

  dylib_sha256: str = _check_library_version(dylib_path) # Gate 1: version.
  lib: ctypes.CDLL = _load_library(dylib_path)

  jieqi_rows: list[JieqiRow] = _gen_jieqi_rows(lib)     # Gates 2-4 inside.
  algo1_rows: list[LunarRow] = _gen_lunar_rows(lib, algo=1)
  algo2_rows: list[LunarRow] = _gen_lunar_rows(lib, algo=2)

  data_dir: Path = Path(__file__).parent / 'data'
  data_dir.mkdir(parents=True, exist_ok=True)

  generated_on: date = date.today()
  _write_table(
    data_dir / 'jieqi_moments.txt',
    _render_jieqi_table(jieqi_rows, generated_on, dylib_sha256),
    EXPECTED_JIEQI_ROWS,
  )
  _write_table(
    data_dir / 'lunar_years_algo1.txt',
    _render_lunar_table(algo1_rows, 1, generated_on, dylib_sha256),
    EXPECTED_LUNAR_ROWS,
  )
  _write_table(
    data_dir / 'lunar_years_algo2.txt',
    _render_lunar_table(algo2_rows, 2, generated_on, dylib_sha256),
    EXPECTED_LUNAR_ROWS,
  )


if __name__ == '__main__':
  main()
