# celestial_data table schema (schema_version 1)

Frozen data contract between the **generator** (`generator.py`, offline, needs the
celestial-calendar dynamic library) and the **loader** (`loader.py`, runtime, pure Python).
Both sides implement this file independently; disagreement is a bug in whichever side
deviates from the text below.

Runtime must stay pure Python: CI runs the matrix on CPython 3.11 / 3.14 **and PyPy 3.11**,
and `ctypes` + a macOS dylib exist on neither. The library is consumed only when the
tables are regenerated. Same shape as `hko_data/encoder.py` (offline) vs `decoder.py` (runtime).

## Files

| Path | Rows | Source API |
|---|---|---|
| `data/jieqi_moments.txt` | 4800 | `query_jieqi_moment(int32_t year, uint8_t jq_idx)` |
| `data/lunar_years_algo1.txt` | 199 | `get_lunar_year_info(1, int32_t year)` |
| `data/lunar_years_algo2.txt` | 199 | `get_lunar_year_info(2, int32_t year)` |

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
schema_version      1
celestial_version   0.4.0                     # pinned; see the version gate below
release_asset       which release artifact the dylib came from
dylib_sha256        sha256 of the dylib actually loaded -- without it the table is not auditable
generated_by        path of the generating script
generated_on        YYYY-MM-DD
source_api          the C-ABI signature the rows came from
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

- `year` — Gregorian year, `1901..2100` inclusive.
- `jq_idx` — `0..23`, zero-padded. **Identical to bazi's `list(Jieqi)` index**
  (`0 = 立春 … 23 = 大寒`); verified at generation against `get_jieqi_name`, which must
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

## `lunar_years_algo{1,2}.txt`

```
columns: lunar_year first_solar_date leap_month month_len_bits days_counts ganzhi
1901 1901-02-19 0 0x0752 29,30,29,29,30,29,30,29,30,30,30,29 辛丑
```

- `lunar_year` — `1901..2099` inclusive, **both algos clamped to this window**. algo2
  natively reports `[410, 5000]`, which is a placeholder sentinel (`algo2.hpp:443-446`,
  "actually has no limit, simply use"). Clamping keeps a single range contract for both
  algos instead of four range semantics; widening is a follow-up issue.
- `first_solar_date` — Gregorian date of lunar 1/1.
- `leap_month` — `1..12`, or **`0` for no leap month**. HkoData spells the same thing as
  `None`; the loader normalises when comparing.
- `month_len_bits` — the raw `uint16` from the ABI, hex. **LSB-first**: bit *i* is the
  *(i+1)*-th lunar month in sequence (a leap month occupies its own slot), `1` = 30 days,
  `0` = 29 days. Agrees with HkoData `days_counts` 199/199 for algo1 — checked by
  `tests/calendar/test_celestial_tables.py`, not at generation.
- `days_counts` — decoded from `month_len_bits`, 12 or 13 entries. Redundant on purpose:
  the loader asserts the two agree, so hand-editing either one fails.
- `ganzhi` — `(lunar_year - 4) mod 60` over `Ganzhi.list_sexagenary_cycle()`. Not consumed
  at runtime (HKO's `LunarYearInfo` carries it, so parity needs the column to exist); its
  199/199 agreement with HkoData is a test, not a generation gate. The generator imports
  nothing from `hko_data` — the four gates it does enforce are listed below.
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

1. **Version gate** — the loaded library's version must equal the pinned `0.4.0`; raise
   otherwise. A ΔT refresh or celestial #70 changes the numbers, and the provenance header
   alone would only reveal it after the fact.
2. **Per-row valid gate** — `query_jieqi_moment` / `get_lunar_year_info` use the
   `valid == false` contract (they are *not* in the `last_error` pilot, which covers only
   the JD exports). Assert `valid` on every row. This gate has already earned its keep: a
   wrong `ctypes` struct layout (see below) makes every call silently return
   `valid = false` rather than crashing.
3. **Row-count gate** — exactly 4800 / 199 / 199, and the emitted `rows:` header must
   match the lines written.
4. **Cross-check gate** — `get_jieqi_name(idx) == list(Jieqi)[idx].value` for all 24;
   `days_counts` decoded from the bitmask must round-trip.

### ctypes landmine

`LunarYearInfo.month_len` is a **scalar `uint16`**, not an array. Declaring it as
`c_uint16 * 13` inflates the struct past the register-return threshold, breaks the
struct-by-value ABI, and every field reads as garbage — `valid` included, so the failure is
silent. Verified layouts:

```c
JieqiMomentQuery { bool valid; uint8_t jq_idx; int32_t y; uint32_t m; uint32_t d; double frac; }
LunarYearInfo    { bool valid; int32_t year; uint8_t month; uint8_t day;
                   uint8_t leap_month; uint16_t month_len; }   /* sizeof == 16 */
```

## Boundary convention (consumer side, recorded here as shared semantics)

A birth moment exactly equal to a jieqi moment belongs to the **new** pillar: the
comparison is `birth >= jieqi`. #72's golden cases are all non-edge, so this needs its own
directed assertion.
