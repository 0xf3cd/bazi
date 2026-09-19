# celestial_data table schema (schema_version 2)

Frozen data contract between the **generator** (`generator.py`, offline, needs the
celestial-calendar Python package) and the **loader** (`loader.py`, runtime, pure Python).
Both sides implement this file independently; disagreement is a bug in whichever side
deviates from the text below.

Runtime must stay independent of celestial-calendar: the package is consumed only when the
tables are regenerated. Same shape as `hko_data/encoder.py` (offline) vs `decoder.py` (runtime).

## Files

| Path | Rows | Source API |
|---|---|---|
| `data/jieqi_moments.txt` | 7200 | `celestial_calendar.jieqi_moment(year, jieqi)` |
| `data/lunar_years_algo1.txt` | 199 | `celestial_calendar.lunar_year_info(ALGO1, year)` |
| `data/lunar_years_algo2.txt` | 199 | `celestial_calendar.lunar_year_info(ALGO2, year)` |

Test fixtures in `tests/calendar/celestial_fixtures/` use identical basenames and format,
carry `fixture: true`, and hold a 5-year slice (`1901, 1914, 1917, 1979, 2024`).
The loader is path-parameterised so the same code reads either.

## File format

UTF-8 text, trailing newline. LF is the on-disk convention; readers normalise line endings (`splitlines()`), so a CRLF file loads — and hashes — identically. Every line starting with `#` is header;
data lines follow, one record per line, fields separated by single spaces.
No blank lines. Rows are emitted in ascending `(year, jq_idx)` / `(lunar_year)` order.

Header lines of the form `# key: value` are the machine-readable provenance. Continuation
lines (`#` + two spaces) are prose attached to the preceding key. Required keys:

```
schema_version      2
celestial_version   0.6.1                     # pinned; see the version gate below
release_asset       celestial-calendar==0.6.1 / PyPI wheel
generated_by        path of the generating script
generated_on        YYYY-MM-DD
source_api          the public Python call the rows came from
timescale           per-table, see below -- the three tables are three different conventions
rounding            jieqi table only
year_range          inclusive
rows                exact row count; the loader asserts it against the lines it parsed
columns             space-separated column names, in order
```

Optional keys: `timescale_caveat` and `rounding` (jieqi table), `algo` (lunar tables),
`fixture` (fixtures only). **The key set is closed** — a column name must never become a
key of its own, because `# leap_month: 1..12, or 0 when …` reads to the loader as a
provenance key whose value is a sentence. Per-column prose belongs on continuation lines
under `columns`. `tests/calendar/test_celestial_tables.py` asserts the parsed key set of
every shipped table and fixture against this list, so the three statements of the contract
— this document, the generator, and the loader's regex — cannot drift apart silently.

## `jieqi_moments.txt`

```
columns: year jq_idx name date time
1901 00 立春 1901-02-04 19:39:57
```

- `year` — Gregorian year, `1901..2200` inclusive.
- `jq_idx` — `0..23`, zero-padded. **Identical to bazi's `list(Jieqi)` index**
  (`0 = 立春 … 23 = 大寒`); verified at generation against `celestial_calendar.jieqi_name`, which must
  equal `list(Jieqi)[jq_idx].value`. Even indices are 节 (month boundaries), odd are 气.
  Note HKO's own on-disk order is the 小寒-first `Jieqi.as_list(ganzhi_year=False)` — do
  not confuse the two.
- `name` — the Chinese name. Redundant with `jq_idx` on purpose: the loader cross-checks
  them, so a hand-edited row is caught.
- `date` / `time` — `YYYY-MM-DD` / `HH:MM:SS`.
- **Timescale: UTC+08:00**, obtained by adding exactly 8h to celestial's UT1 moment and
  re-deriving the date (the addition rolls the date near midnight — it must not be applied
  to the time-of-day alone).
- **Rounding: truncate to whole seconds.** Chosen over round-half because rounding
  `23:59:59.6` carries into the next day and silently moves a date-level attribution;
  truncation can never change the date. Cost is bounded: the stored moment is at most 1s
  earlier than the true one.
- `小寒`/`大寒` (idx 22/23) of year Y fall in **January of Y**, so rows within a year are
  not date-sorted. This matches HKO's `jieqi_date(Y, 小寒)` convention (verified 1901 /
  2024 / 2099).
- UT1−UTC ≤ 0.9s for 1972+; before 1972 UT1 is a proxy (celestial Phase C convention).
  Normally this only matters for births within ±0.9s of a jieqi moment — but when the
  moment itself sits near midnight, 0.9s flips the whole **date**. Measured worst case in
  the window: 1979 大寒 is 4s from midnight.
- The TT jieqi moments are still computed from solar-longitude roots. Their conversion to
  UT1 in years 2101–2200 uses the Stephenson-Morrison-Hohenkerk integrated-lod ΔT
  extrapolation: it is continuous, but has no precision guarantee or independent HKO comparison.

## `lunar_years_algo{1,2}.txt`

```
columns: lunar_year first_solar_date leap_month month_len_bits days_counts ganzhi
1901 1901-02-19 0 0x0752 29,30,29,29,30,29,30,29,30,30,30,29 辛丑
```

- `lunar_year` — `1901..2099` inclusive, **both algos clamped to this window**. algo2
  natively reports `[410, 2500]`. Clamping keeps a single range contract for both algos
  instead of four range semantics; widening is a follow-up issue.
- `first_solar_date` — Gregorian date of lunar 1/1.
- `leap_month` — `1..12`, or **`0` for no leap month**. HkoData spells the same thing as
  `None`; the loader normalises when comparing.
- `month_len_bits` — encoded as hex from the package's public `month_lengths` tuple.
  **LSB-first**: bit *i* is the
  *(i+1)*-th lunar month in sequence (a leap month occupies its own slot), `1` = 30 days,
  `0` = 29 days. Agrees with HkoData `days_counts` 199/199 for algo1 — checked by
  `tests/calendar/test_celestial_tables.py`, not at generation.
- `days_counts` — decoded from `month_len_bits`, 12 or 13 entries. Redundant on purpose:
  the loader asserts the two agree, so hand-editing either one fails.
- `ganzhi` — `(lunar_year - 4) mod 60` over `Ganzhi.list_sexagenary_cycle()`. Not consumed
  at runtime (HKO's `LunarYearInfo` carries it, so parity needs the column to exist); its
  199/199 agreement with HkoData is a test, not a generation gate. The generator imports
  nothing from `hko_data` — the three gates it does enforce are listed below.
- **algo1 is the default.** It is the HKO official-almanac lineage — the lunar surface is a
  display concern and should track the official almanac; the four pillars are jieqi-based
  and never consume the lunar calendar. algo2 (leap-second aware UTC+8 via `jde_to_utc8`,
  celestial #84) is opt-in.
- The two algos are known to disagree on exactly **6 years in this window**:
  `1914, 1915, 1916, 1920, 2057, 2097` (celestial `src/test/lunar/diff_test.cpp`;
  independently reproduced against HkoData by the test suite — algo1 matches HKO 199/199,
  so algo2's differences from HKO are exactly its differences from algo1).

## Generator hard gates

Fail loudly at generation time; a bad table is only discoverable afterwards otherwise.

1. **Version gate** — the imported package's public `__version__` must equal the pinned
   `0.6.1`; raise otherwise. A ΔT refresh or celestial update can change every moment.
2. **Row-count gate** — exactly 7200 / 199 / 199, and the emitted `rows:` header must
   match the lines written.
3. **Cross-check gate** — `jieqi_name(Jieqi(idx)) == list(Jieqi)[idx].value` for all 24;
   the public `month_lengths` tuple must round-trip through the on-disk bitmask encoding.

## Boundary convention (consumer side, recorded here as shared semantics)

A birth moment exactly equal to a jieqi moment belongs to the **new** pillar: the
comparison is `birth >= jieqi`. #72's golden cases are all non-edge, so this needs its own
directed assertion.
