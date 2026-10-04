# Bazi
> 排盘、五行、十神、纳音、刑冲破害、合会

A Python 3.11+ library for Four Pillars charts and their relations. Runtime uses
only the standard library and five bundled calendar tables; no network access or
data generation is needed.

## Features

- Charts: four pillars, 阴阳五行, 十神, 藏干, 纳音 and 十二长生, with calendar
  backend, birth-time precision and school configuration recorded in JSON.
- Transits: precise 大运 intervals, 小运 and 流年, with year/month/date/moment queries.
- Relations and 神煞: at-birth and transit analysis, including configurable rule variants.
- Descriptions: static 天干 and 十神 lookup, either as text or immutable claims with
  source witnesses, attribution, output policy and applicability conditions.
- Source-checkout demos: random charts, transit tables, relationship analysis and
  description display/export. The Interpreter runner also accepts fixed birth inputs.

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

Birth times are naive local civil times; timezone-aware inputs are rejected.
Defaults remain `CELESTIAL` with day precision. `hko` provides date-level calendar
data; `celestial` and `celestial-algo2` use the bundled astronomical tables.
Backend differences and supported date ranges are documented in the calendar
modules; selecting a backend does not install its offline generator.

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
| `bazi.interpreter` | `Interpreter.interpret_*` text lookup, `query_*` structured lookup, `source` witness lookup |
| `bazi.descriptions` | `DescriptionClaim`, `DescriptionSource`, `DescriptionSourceRecord`, output and condition enums |
| `bazi.defines`, `bazi.utils` | Domain enums and relation utilities, documented in their modules |

`bazi.descriptions.SHISHEN_DESCRIPTIONS` and `TIANGAN_DESCRIPTIONS` contain only
default-output descriptions. `Interpreter` methods use the same default; pass
`include_reference_only=True` to also include claims not eligible for default output.

### Structured description queries

```python
from bazi.defines import Tiangan
from bazi.interpreter import Interpreter

fields = Interpreter.query_tiangan(Tiangan.丁, include_reference_only=True)
for claim in fields['general']:
  print(claim.claim_id, claim.text, claim.output.value, claim.conditions)
  for source_id in claim.sources:
    witness = Interpreter.source(source_id)
    print(witness.work, witness.edition, witness.locator, witness.url)
    print(witness.supports, witness.limitations)
```

`query_tiangan` and `query_shishen` return a `frozendict` of field names to tuples
of frozen `DescriptionClaim` objects. Source lookup returns a frozen record with
the work, attribution, edition, locator, URL, text layer, lineage, excerpt and
evidentiary boundaries. Text-returning methods retain their existing field/list shape.

The corpus contains 291 claims: 19 default definitions and 272 reference-only
claims. Default queries select only default-output claims without conditions.
Complete queries also include named historical imagery, repository editorial text
and legacy text whose sources this audit has not verified. An empty `sources`
tuple and `Legacy corpus; source unverified` attribution preserve that last state;
they do not establish that no source exists or that the claim is false.

`CHART_CONTEXT_REQUIRED` records a prerequisite, not an evaluated result. Reference
queries include these claims without determining whether they apply to a chart.
Witness records establish textual attribution and its boundaries. Description
selection is independent of the calculation variants in `BaziSchool`.
More specific good/bad-state conditions are tracked in [#228](https://github.com/0xf3cd/bazi/issues/228).

### Run a chart locally

The following commands run from a source checkout with the development environment
installed. Each runner creates a random chart:

| Command | Output |
| --- | --- |
| `python run_demo.py` | Chart, 大运 / 小运 / 流年 and chart JSON |
| `python run_relationship_analyzer.py` | 夫妻宫, 配偶星, at-birth 神煞 and ten years of 流年神煞 |
| `python run_interpreter.py` | One chart with static descriptions; no file export by default |

For a repeatable random example with source records:

```sh
python run_interpreter.py --seed 42 --show-sources
```

For a fixed birth and complete reference text:

```sh
python run_interpreter.py \
  --birth-time "2000-01-01 12:00" \
  --gender male \
  --include-reference-only \
  --show-sources
```

For explicit chart and description exports:

```sh
python run_interpreter.py \
  --seed 42 \
  --count 5 \
  --output-dir output_data \
  --export-knowledge-base
```

| Interpreter flag | Effect |
| --- | --- |
| `--birth-time <time>`, `--gender male\|female` | Fixed local civil birth; supply both together |
| `--seed <integer>` | Reproducible random charts |
| `--count <positive integer>` | Random chart count; default 1 |
| `--include-reference-only` | Include reference text and label unevaluated conditions |
| `--show-sources` | Show IDs, attribution, witnesses and evidentiary boundaries; does not expand text selection |
| `--output-dir <path>` | Save the displayed charts as `interpretation_examples/0.txt`, etc. below this path |
| `--export-knowledge-base` | Write all 天干 / 十神 descriptions under `knowledge_base/`; default root `output_data/` |
| `-h`, `--help` | Show help |

Fixed birth inputs accept one chart and cannot be combined with a seed. Exported
TXT files have terminal color codes removed. Reference-only text is labelled,
including unverified attribution and conditions that have not been evaluated.
The runner assembles enum lookups and counts three non-day-master stems plus four
branch 主气 positions; its percentages describe those seven positions. Paragraph
selection does not evaluate 旺衰, 喜忌 or 格局.

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
with `celestial-calendar==0.6.1`. These optional tools are not runtime dependencies.
If an installed table is missing, reinstall the distribution instead.

## License

Author-owned material is available under the standard [MIT License](LICENSE).
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) describes the separate scope of
calendar data, quotations and other third-party material. Those materials are not
relicensed by the author's MIT grant. Both notices are included in built artifacts.

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for version changes and
[RELEASING.md](RELEASING.md) for the manual release procedure.
