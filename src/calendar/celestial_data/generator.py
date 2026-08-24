# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# bazi/src/calendar/celestial_data/generator.py
#
# Regenerate the committed tables under `celestial_data/data/` from the
# celestial-calendar Python package, following the frozen contract in `SCHEMA.md`.
#
# This module is an offline tool, only used when the tables need to be regenerated.
# It is not needed at runtime: the runtime side (`loader.py`) is pure Python and only
# reads the committed tables. `celestial_calendar` must never leak into any runtime module.
# Same split as `hko_data/encoder.py` (offline) vs `hko_data/decoder.py` (runtime).
#
# Run from the repo root:
#   python -m src.calendar.celestial_data.generator

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Final

import celestial_calendar as celestial

from ...defines import Ganzhi, Jieqi


# ---------------------------------------------------------------------------
# Pinned package (version gate)

CELESTIAL_VERSION: Final[str] = '0.6.1'
RELEASE_ASSET: Final[str] = 'celestial-calendar==0.6.1 / PyPI wheel'

# Table windows (SCHEMA.md): jieqi rows are keyed by Gregorian year, lunar rows by lunar year.
JIEQI_START_YEAR: Final[int] = 1901
JIEQI_END_YEAR:   Final[int] = 2200
LUNAR_START_YEAR: Final[int] = 1901
LUNAR_END_YEAR:   Final[int] = 2099 # BOTH algos clamp to this window; algo2 natively
                                    # reports [410, 2500].

EXPECTED_JIEQI_ROWS: Final[int] = (JIEQI_END_YEAR - JIEQI_START_YEAR + 1) * 24
EXPECTED_LUNAR_ROWS: Final[int] = LUNAR_END_YEAR - LUNAR_START_YEAR + 1


# ---------------------------------------------------------------------------
# Version gate: a ΔT refresh or celestial update can change every generated moment.
if celestial.__version__ != CELESTIAL_VERSION:
  raise RuntimeError(
    f'Version gate failed: imported celestial-calendar {celestial.__version__}, '
    f'expected {CELESTIAL_VERSION}.'
  )


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
  month_len_bits:  int             # Public month_lengths encoded LSB-first.
  days_counts:     tuple[int, ...] # Decoded from `month_len_bits`; redundant on purpose.
  ganzhi:          Ganzhi


def _ut1_moment_to_utc8(moment: celestial.CivilDateTime) -> datetime:
  '''
  UT1 -> UTC+08:00: add exactly 8h to the full moment and re-derive the date
  (the addition rolls the date near midnight -- it must not be applied to the
  time-of-day alone). Then truncate to whole seconds: rounding could carry
  `23:59:59.6` into the next day and silently move a date-level attribution;
  truncation can never change the date.
  '''
  utc8: datetime = (
    datetime(moment.year, moment.month, moment.day)
    + timedelta(days=moment.fraction)
    + timedelta(hours=8)
  )
  return utc8.replace(microsecond=0)


def _gen_jieqi_rows() -> list[JieqiRow]:
  jieqi_list: Final[list[Jieqi]] = list(Jieqi)
  assert len(jieqi_list) == 24

  # Cross-check gate, part 1: celestial's jieqi order must be bazi's `list(Jieqi)` order exactly.
  for idx, jq in enumerate(jieqi_list):
    name: str = celestial.jieqi_name(celestial.Jieqi(idx))
    if name != jq.value:
      raise RuntimeError(f'Cross-check gate failed: jieqi_name({idx}) is {name}, expected {jq.value}.')

  rows: list[JieqiRow] = []
  for year in range(JIEQI_START_YEAR, JIEQI_END_YEAR + 1):
    for idx, jq in enumerate(jieqi_list):
      source_jieqi: celestial.Jieqi = celestial.Jieqi(idx)
      query: celestial.JieqiMoment = celestial.jieqi_moment(year, source_jieqi)
      if query.jieqi is not source_jieqi or query.moment_ut1.year != year:
        raise RuntimeError(
          f'Query echo mismatch: asked for ({year}, {idx}), '
          f'got ({query.moment_ut1.year}, {query.jieqi.value}).'
        )
      rows.append(JieqiRow(
        year=year,
        jq_idx=idx,
        name=jq.value,
        moment=_ut1_moment_to_utc8(query.moment_ut1),
      ))

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


def _gen_lunar_rows(algo: int) -> list[LunarRow]:
  assert algo in (1, 2)

  algorithm: celestial.LunarAlgorithm = (
    celestial.LunarAlgorithm.ALGO1 if algo == 1 else celestial.LunarAlgorithm.ALGO2
  )
  year_range: celestial.LunarYearRange = celestial.supported_lunar_year_range(algorithm)
  if year_range.start > LUNAR_START_YEAR or year_range.end < LUNAR_END_YEAR:
    raise RuntimeError(
      f'algo{algo} natively covers [{year_range.start}, {year_range.end}], '
      f'which does not contain the required window [{LUNAR_START_YEAR}, {LUNAR_END_YEAR}].'
    )

  sexagenary_cycle: Final[list[Ganzhi]] = Ganzhi.list_sexagenary_cycle()

  rows: list[LunarRow] = []
  for lunar_year in range(LUNAR_START_YEAR, LUNAR_END_YEAR + 1): # The clamp; see LUNAR_END_YEAR.
    info: celestial.LunarYearInfo = celestial.lunar_year_info(algorithm, lunar_year)
    leap_month: int = 0 if info.leap_month is None else info.leap_month
    days_counts: tuple[int, ...] = info.month_lengths
    month_count: int = 12 if leap_month == 0 else 13
    month_len_bits: int = _encode_days_counts(days_counts)

    # Cross-check gate, part 2: the bitmask must round-trip, with no stray high bits.
    if len(days_counts) != month_count or _decode_month_len_bits(month_len_bits, month_count) != days_counts:
      raise RuntimeError(
        f'Cross-check gate failed: algo{algo} {lunar_year} bitmask 0x{month_len_bits:04x} '
        f'does not round-trip through {days_counts}.'
      )

    rows.append(LunarRow(
      lunar_year=lunar_year,
      first_solar_date=date(info.first_day.year, info.first_day.month, info.first_day.day),
      leap_month=leap_month,
      month_len_bits=month_len_bits,
      days_counts=days_counts,
      ganzhi=sexagenary_cycle[(lunar_year - 4) % 60],
    ))

  # Row-count gate, part 1.
  if len(rows) != EXPECTED_LUNAR_ROWS:
    raise RuntimeError(f'Row-count gate failed: {len(rows)} lunar rows for algo{algo}, expected {EXPECTED_LUNAR_ROWS}.')
  return rows


# ---------------------------------------------------------------------------
# Rendering (header keys are the machine-readable provenance required by SCHEMA.md)

def _common_header(generated_on: date, source_api: str) -> list[str]:
  return [
    '# schema_version: 2',
    f'# celestial_version: {CELESTIAL_VERSION}',
    f'# release_asset: {RELEASE_ASSET}',
    '# generated_by: src/calendar/celestial_data/generator.py',
    f'# generated_on: {generated_on.isoformat()}',
    f'# source_api: {source_api}',
  ]


def _render_jieqi_table(rows: list[JieqiRow], generated_on: date) -> str:
  header: list[str] = [
    '# celestial-calendar jieqi moment table',
    *_common_header(generated_on, 'celestial_calendar.jieqi_moment(year, jieqi)'),
    '# timescale: UTC+08:00, derived from celestial UT1 moments by adding exactly 8h',
    '# timescale_caveat: UT1-UTC <= 0.9s (1972+); pre-1972 UT1 is a proxy (celestial Phase C).',
    '#   Normally only affects births within +/-0.9s of a jieqi moment -- but when the moment',
    '#   itself sits near midnight, 0.9s flips the whole *date* attribution.',
    '#   Measured worst case in window: 1979 大寒 is 4s from midnight.',
    '# rounding: truncate to whole seconds (sub-second discarded; never carries into the next date)',
    f'# year_range: {JIEQI_START_YEAR}..{JIEQI_END_YEAR} inclusive',
    '#   TT moments still come from solar-longitude roots; their conversion to UT1 in',
    '#   2101..2200 uses the Stephenson-Morrison-Hohenkerk integrated-lod Delta T extrapolation:',
    '#   it is continuous, but has no precision guarantee or independent HKO comparison.',
    '# columns: year jq_idx name date time',
    '#   jq_idx is 0..23, identical to the bazi `list(Jieqi)` index (0=立春 .. 23=大寒), and',
    '#   `name` is cross-checked against celestial_calendar.jieqi_name at generation.',
    '#   Rows ascend by (year, jq_idx), which is not date order: 小寒/大寒 (idx 22/23) of',
    '#   year Y fall in January of Y.',
    f'# rows: {len(rows)}',
  ]
  lines: list[str] = [
    f'{row.year} {row.jq_idx:02d} {row.name} {row.moment:%Y-%m-%d} {row.moment:%H:%M:%S}'
    for row in rows
  ]
  return '\n'.join(header + lines) + '\n'


def _render_lunar_table(rows: list[LunarRow], algo: int, generated_on: date) -> str:
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
    *_common_header(generated_on, 'celestial_calendar.lunar_year_info(algorithm, lunar_year)'),
    f'# algo: {algo}',
    f'#   {algo_note[algo]}',
    f'# timescale: {timescale_note[algo]}',
    f'# year_range: {LUNAR_START_YEAR}..{LUNAR_END_YEAR} inclusive -- BOTH algos clamped to this window.',
    '#   algo2 natively reports [410, 2500].  Clamping keeps one',
    '#   range contract for both algos.  Widening is a follow-up issue.',
    '# columns: lunar_year first_solar_date leap_month month_len_bits days_counts ganzhi',
    '#   leap_month -- 1..12, or 0 when the year has no leap month.  hko_data spells the same',
    '#   thing as `None`; the loader normalizes.',
    '#   month_len_bits -- encoded from the public `month_lengths` tuple, LSB-first',
    '#   (bit i = the (i+1)-th lunar month in sequence; a leap month occupies its own',
    '#   slot; 1 = 30 days, 0 = 29 days).',
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
  jieqi_rows: list[JieqiRow] = _gen_jieqi_rows()
  algo1_rows: list[LunarRow] = _gen_lunar_rows(algo=1)
  algo2_rows: list[LunarRow] = _gen_lunar_rows(algo=2)

  data_dir: Path = Path(__file__).parent / 'data'
  data_dir.mkdir(parents=True, exist_ok=True)

  generated_on: date = date.today()
  _write_table(
    data_dir / 'jieqi_moments.txt',
    _render_jieqi_table(jieqi_rows, generated_on),
    EXPECTED_JIEQI_ROWS,
  )
  _write_table(
    data_dir / 'lunar_years_algo1.txt',
    _render_lunar_table(algo1_rows, 1, generated_on),
    EXPECTED_LUNAR_ROWS,
  )
  _write_table(
    data_dir / 'lunar_years_algo2.txt',
    _render_lunar_table(algo2_rows, 2, generated_on),
    EXPECTED_LUNAR_ROWS,
  )


if __name__ == '__main__':
  main()
