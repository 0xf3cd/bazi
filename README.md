# Bazi
> 排盘、五行、十神、纳音、刑冲破害、合会

A Python 3.11+ library for Four Pillars charts and their relations. Runtime uses
only the standard library and six bundled calendar tables; no network access or
data generation is needed.

## Installation

To build and validate the current checkout and retain an installable pair:

```sh
python -m pip install -r Requirements.txt
python run_package_checks.py --output-dir ../bazi-tested
python -m pip install ../bazi-tested/bazi-1.0.0-py3-none-any.whl
```

The output directory must be empty and outside the checkout. For a published
version, install from the registry with `python -m pip install bazi==1.0.0`.
There is no installed CLI, `src` compatibility package or root-class facade.

```python
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.school import BaziConfig
from bazi.transit_chart import TransitChart
from bazi.analyzer.relationship import RelationshipAnalyzer

config = BaziConfig.from_values(backend='celestial', precision='day')
chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male', config))
restored = BaziChart.from_json(chart.json)
assert restored.json == chart.json
print(chart.json['pillars'])
print(TransitChart(chart).at_year(2024))
print(RelationshipAnalyzer(chart).at_birth.shensha)
```

Without a longitude, birth times are naive local civil times and timezone-aware
inputs remain rejected. This is the unchanged default path. To opt into apparent
solar time, pass an aware datetime and an east-positive `longitude` in `[-180, 180]`
to `Bazi` or `Bazi.create`; latitude is not consumed by this correction. The caller
owns the datetime's timezone, DST fold and historical offset. The library does not
infer a historical timezone.

The location-aware path supports only `CELESTIAL` with `HOUR` or `MINUTE` precision.
Its public clock, solar date, lunar/ganzhi date, day rollover and hour pillar use
local apparent solar time. Jie attribution, Dayun intervals and transit ordering use
the normalized absolute instant. Existing transit query moments remain naive
UTC+08:00 labels and receive no moving-location correction. Historical pre-1929
time-basis choices remain outside this API and are tracked by issue #118. Defaults
remain `CELESTIAL` with day precision. `hko` provides date-level calendar data;
`celestial` and `celestial-algo2` use the bundled astronomical tables. Backend
differences and supported date ranges are documented in the calendar modules;
selecting a backend does not install its offline generator.

```python
from datetime import datetime

from bazi.bazi import Bazi
from bazi.school import BaziConfig

located = Bazi.create(
  datetime.fromisoformat('2000-01-01T07:00:00-05:00'),
  'male',
  BaziConfig.from_values(precision='minute'),
  longitude=116.4,
)
print(located.solar_datetime)  # local apparent-solar clock
```

## Interfaces

Use the defining modules rather than expecting classes at the package root:

| Module | Principal interfaces |
| --- | --- |
| `bazi.bazi` | `Bazi`, `BaziGender` |
| `bazi.bazi_chart` | `BaziChart`, `BaziJson`, JSON restoration with `from_json` |
| `bazi.school` | `BaziConfig`, `BaziSchool`, precision and school options |
| `bazi.calendar` | `CalendarBackend`, `CalendarDate`, `CalendarType`, `calendar_utils_of` |
| `bazi.transit_chart`, `bazi.transits` | `TransitChart`, `TransitSet`, `TransitKind` |
| `bazi.analyzer.relationship` | `RelationshipAnalyzer` |
| `bazi.interpreter` | `Interpreter.interpret_tiangan`, `Interpreter.interpret_shishen` |
| `bazi.defines`, `bazi.utils` | Domain enums and relation utilities, documented in their modules |

`bazi.descriptions.SHISHEN_DESCRIPTIONS` and `TIANGAN_DESCRIPTIONS` contain only
default-output descriptions. `Interpreter` methods use the same default; pass
`include_reference_only=True` to also include claims not eligible for default output.

Domain names use Pinyin; enums also provide Chinese aliases. JSON retains Chinese
domain values and records configuration. `py.typed` exposes the inline type hints.
Private names, offline generation tools and undocumented internals are not a
promise of a stable public interface.

[External chart comparisons](https://github.com/0xf3cd/bazi/blob/9c3a473563ce595d675efdc134428fe52243491b/EXTERNAL_BASELINE.md) document a synthetic boundary
baseline with configuration-specific results and an offline regression test.

## Instructions

`Requirements.txt` is the development setup, not the installed library's dependency
list. It includes test, lint, typing and distribution-verification tools.
Source-tree mypy also needs `celestial-calendar==0.6.1`, as installed by CPython CI.

```sh
python -m pip install -r Requirements.txt
python -m pip install celestial-calendar==0.6.1
python run_tests.py -a -v
```

The full gate runs every test (including slow and HKO-data tests), requires 100%
coverage, runs ruff and strict source mypy, demos, Interpreter, optimized input
checks, and isolated wheel/sdist-derived-wheel checks. The artifact checks use two
fresh dependency-free consumers and a separate installed mypy environment.
The artifact checks (`run_package_checks.py`, `-pkg` and `-a`) may download tools
and their dependencies from the package index to seed isolated build and typing
environments, even after the development requirements are installed.
Builds and consumers live in external temporary directories. Root demo scripts may
write to `output_data/`; the installed library's read-only behavior is checked separately.

| Flag | Effect |
| --- | --- |
| `-a`, `--all` | Full gate; overrides `-nt` and `-k` |
| `-nt`, `--no-test` | Skip tests and coverage |
| `-s`, `-hko` | Include slow tests or HKO-data tests |
| `-k <expression>` | Select pytest tests; ignores `-s` and `-hko` |
| `-v` | Verbose output |
| `-c` | Coverage report, also written to `covhtml/` |
| `-cr <rate>`, `--coverage-rate <rate>` | Minimum coverage (default 100) |
| `-r`, `--ruff` | Run `ruff check` |
| `-m`, `-mypy`, `--mypy` | Run source mypy with the runner's strict flags |
| `-d` | Run both demo scripts |
| `-i` | Run Interpreter examples |
| `-osmoke`, `--o-smoke` | Run source public-contract smoke with `python -O` |
| `-pkg`, `--package` | Run isolated distribution checks |
| `--package-output-dir <path>` | With `-pkg` or `-a`, retain only the verified sdist and its rebuilt wheel |

A bare `python run_tests.py` omits slow/HKO tests and all optional tasks. It is not
the full verification gate. Do not run autoformatters; use `ruff check .`.

## Offline Generation

The committed data is read, not regenerated, during packaging or installed use.
The source tree and sdist contain the raw HKO inputs; the wheel does not.
Maintainers can regenerate from those sources with `python -m bazi.calendar.hko_data.encoder`
(`requests` is needed only if inputs must be downloaded), or `python -m bazi.calendar.celestial_data.generator`
with `celestial-calendar==0.6.1`. The latter also writes the daily equation-of-time
table; `--eot-only` limits regeneration to that byte-stable file. These optional tools
are not runtime dependencies.
If an installed table is missing, reinstall the distribution instead.

## License

Author-owned material is available under the standard [MIT License](LICENSE).
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) describes the separate scope of
calendar data, quotations and other third-party material. Those materials are not
relicensed by the author's MIT grant. Both notices are included in built artifacts.

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for version changes and
[RELEASING.md](RELEASING.md) for the manual release procedure.
