# Bazi
> 排盘、五行、十神、纳音、刑冲破害、合会

A Python 3.11+ library for Four Pillars charts and their relations. Runtime uses
only the standard library, six bundled calendar tables and a knowledge corpus; no network access or
data generation is needed.

This README describes the current checkout. For a published package, consult the
README at its matching release tag.

## Features

- Charts: four pillars, 阴阳五行, 十神, 藏干, 纳音 and 十二长生, with calendar
  backend, birth-time precision and school configuration recorded in JSON.
- Transits: precise 大运 intervals, 小运 and 流年, with year/month/date/moment queries.
- Relations and 神煞: at-birth and transit analysis, including configurable rule variants.
- Interpretation knowledge: editable JSON, validated references, object/context/topic/source
  queries, premise and source display, and reloadable exports. Legacy 天干 / 十神 lookups remain available.
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

Without a longitude, birth times are naive local civil times and timezone-aware
inputs remain rejected. This is the unchanged default path. To opt into apparent
solar time, pass an aware datetime and an east-positive `longitude` in `[-180, 180]`
to `Bazi` or `Bazi.create`; latitude is not consumed by this correction. The caller
owns the datetime's timezone, DST fold and historical offset. The birth-region civil
basis defaults to that timezone; pass `civil_timezone` (a `tzinfo`) when the input
expresses the instant in another zone. The actual offset at birth is frozen into a
fixed-offset civil datetime. The library does not infer a geographic or historical timezone.

The location-aware path supports only `CELESTIAL` with `HOUR` or `MINUTE` precision.
It preserves the input's seconds and microseconds. The apparent clock is the local
civil clock plus `longitude / 15 - civil UTC offset`, wrapped to `[-12h, 12h)`, plus
EOT evaluated at the exact UTC instant. Thus Kiritimati's January 1 noon at UTC+14
and longitude -157.4 stays on January 1 around 11:27. Ordinary midnight carry still
changes the apparent date. Longitudes +180 and -180 identify the same meridian.
Its public clock, solar date, lunar/ganzhi date, day rollover and hour pillar use
local apparent solar time. Previous/next Jie lookup uses the absolute instant;
year/month attribution compares the birth and Jie in apparent-solar precision buckets
at the same longitude and frozen birth-region offset, with ties on the new side.

Location identity and JSON preserve the exact UTC instant, civil basis, longitude,
gender and config. With the same explicit `civil_timezone`, alternate display offsets
of the same instant are equal, hash-equal and JSON-equal. Different civil bases remain
distinct; seconds remain distinct even when the displayed `solar_datetime` minute agrees.
Location JSON contains `time_basis='apparent_solar'`, `civil_time` (fixed-offset aware),
`canonical_instant` (UTC), `longitude` and `apparent_time` (untruncated computed naive clock).
EOT uses daily decisecond samples with linear interpolation; retaining microsecond
digits does not imply microsecond astronomical accuracy. Restoring a chart reconstructs
and checks all derived values; legacy JSON is unchanged. The supported birth-date window
applies to the apparent date (`1901-02-19` through `2099-12-31`), so its accepted UTC
instants depend on longitude and civil basis.
The larger Jie table does not expand that birth window.

Dayun intervals and transit ordering use the absolute coordinate. Dayun boundaries
and existing transit query moments are naive UTC+08:00 labels, not apparent clocks,
and receive no moving-location correction. Historical pre-1929 time-basis choices
remain outside this API and are tracked by issue #118. Defaults remain `CELESTIAL`
with day precision. `hko` provides date-level calendar data; `celestial` and
`celestial-algo2` use the bundled astronomical tables. Backend differences and
supported date ranges are documented in the calendar modules; selecting a backend
does not install its offline generator.

```python
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from bazi.bazi import Bazi
from bazi.school import BaziConfig

located = Bazi.create(
  datetime(2023, 12, 31, 22, tzinfo=UTC),
  'male',
  BaziConfig.from_values(precision='minute'),
  longitude=-157.4,
  civil_timezone=ZoneInfo('Pacific/Kiritimati'),
)
assert located.solar_datetime == datetime(2024, 1, 1, 11, 27)
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
| `bazi.interpreter` | `Interpreter.interpret_*` text lookup, `query_tiangan` / `query_shishen` claims, `query_source` witnesses |
| `bazi.descriptions` | `DescriptionClaim`, `DescriptionClaims`, `DescriptionSourceRecord`; `DescriptionSource`, `DescriptionLineage`, `DescriptionTextLayer`, `DescriptionOutput`, `DescriptionCondition` |
| `bazi.knowledge` | `KnowledgeBase`, `KnowledgeEntry`, `KnowledgeObject`, `KnowledgeRole`, `KnowledgeRelation`, `KnowledgeContext`, `KnowledgeSource`, `LegacyDescription` |
| `bazi.context_matching` | `ContextProfile`, `ChartOccurrence`, `CriterionResult`, `EntryMatch`, `ContextResult`, `evaluate_context` |
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

### Structured description queries

```python
from bazi.defines import Tiangan
from bazi.interpreter import Interpreter

fields = Interpreter.query_tiangan(Tiangan.丁, include_reference_only=True)
for claim in fields['general']:
  print(claim.claim_id, claim.text, claim.output.value, claim.conditions)
  for source_id in claim.sources:
    witness = Interpreter.query_source(source_id)
    print(witness.work, witness.edition, witness.locator, witness.url)
    print(witness.supports, witness.limitations)
```

`query_tiangan` and `query_shishen` return a `frozendict` of field names to tuples
of frozen `DescriptionClaim` objects. Source lookup returns a frozen record with
the work, attribution, edition, locator, URL, text layer, lineage, excerpt and
evidentiary boundaries. Text-returning methods retain their existing field/list shape.

Default queries select only default-output claims without legacy conditions.
Complete queries also include named historical imagery, repository editorial text
and legacy text marked source-unverified. An empty `sources`
tuple and `Legacy corpus; source unverified` attribution preserve that last state;
they do not establish that no source exists or that the claim is false.

`CHART_CONTEXT_REQUIRED` records a prerequisite, not an evaluated result. Reference
queries include these claims without determining whether they apply to a chart.
Witness records establish textual attribution and its boundaries. Description
selection is independent of the calculation variants in `BaziSchool`.
The `in_good_status` / `in_bad_status` fields are compatibility placements, not core
knowledge categories. The new API exposes premise organization without assigning chart states.

### Maintain and query interpretation knowledge

`bazi/knowledge_data.json` is the unique editing source. Loading validates its schema,
IDs, role bindings, references and output policies, then builds in-memory indexes.
The same file is bundled in wheels and source archives; exports and legacy projections
are derived from it. No database service or runtime dependency is required.

```python
from pathlib import Path

from bazi.knowledge import KnowledgeBase

knowledge = KnowledgeBase.load()
entries = knowledge.query(
  object_id='tiangan.geng',
  context_id='tiangan.geng_regulated_transit',
  topic='性格',
  include_reference_only=True,
)
for entry in entries:
  print(knowledge.render(entry, manual_context=True))

exported = knowledge.export_json(entries)
restored = KnowledgeBase.from_json(exported)
assert tuple(restored.entries.values()) == entries

# Load an edited source without changing the bundled corpus.
edited = KnowledgeBase.load(Path('edited-knowledge.json'))
```

The 五行 / 国印 reference examples preserve existing rule documentation and its limits; repository attribution
is not a newly verified classical witness.

| Entry information | Meaning |
| --- | --- |
| `roles`, `relations` | Named discussion objects and directed **textual** relationships; not computed or effective chart interactions |
| `topics`, `viewpoint` | Lookup topics and the interpretation's adopted viewpoint |
| `applicability='unconditional'` | The knowledge statement has no chart prerequisite, such as a definition or historical image |
| `applicability='described'` | Premise text is recorded; its terms can still lack computational definitions |
| `applicability='unresolved'` | Applicability premises remain to be reconstructed; an empty old condition tuple did not settle them |
| `premise`, `contexts`, `limits`, `exceptions` | Full premise text, named lookup contexts with time scopes, unresolved terms and boundaries |
| `sources`, `source_state`, `attribution` | Witness references and witnessed / editorial / unverified / repository-attributed status |
| `output`, `legacy` | Presentation eligibility and traceable old field/order/condition metadata |

Manual context selection only retrieves knowledge. It does not decide whether a chart
meets that context. Multiple context tags do not imply an AND/OR expression. For example,
the 庚金 transit entry retains both 行运有制有化 and 后天有教养; the first is undefined
here and the second is a premise outside the chart. Basic 生克 does not establish either.

Queries intersect `object_id`, `context_id`, `topic`, `source_id`, `viewpoint`,
`applicability` and `time_scope`. Object lookup includes every bound role. Results retain
source order and are transitively immutable. Unknown filter values raise `ValueError`;
a valid filter with no matches returns an empty tuple. Reference entries require
`include_reference_only=True`. `entry(claim_id)` resolves a stable ID directly.

`export_json()` exports the whole corpus, including reference records and their policies;
`export_json(entries)` exports a selection. Both preserve the object, context and source
registries for reload and evidence display. Exporting a reference record does not change
its presentation eligibility. The frozen legacy test fixture is a migration oracle,
not another editing source.

From a source checkout, edit the JSON and validate it:

```sh
python run_interpreter.py --validate-knowledge
python run_interpreter.py \
  --query-knowledge \
  --object tiangan.ding \
  --topic 历史象 \
  --source yuanhai_ziping_stem_symbols_p70 \
  --include-reference-only
python run_interpreter.py \
  --export-knowledge-json output_data/knowledge.json
```

| Knowledge flag | Effect |
| --- | --- |
| `--query-knowledge` | Query and display entries without creating a chart; includes source details |
| `--validate-knowledge` | Validate the full editing source |
| `--knowledge-source <path>` | Read an edited or exported JSON instead of the bundled source |
| `--object`, `--context`, `--topic`, `--source`, `--viewpoint`, `--applicability`, `--time-scope` | Query filters; `--context` is explicitly manual |
| `--export-knowledge-json <path>` | Export all records, or the selected records with `--query-knowledge` |
| `--include-reference-only` | Also select reference records in a query |

Knowledge modes accept no chart-input, `--output-dir` or legacy TXT-export flags.
Without a knowledge-mode flag, chart runner behavior and the existing parameter
combinations remain available. JSON export refuses to overwrite the editing source,
including through a filesystem alias.

### Evaluate an explicitly scoped editorial premise

Two registered criteria evaluate repository-editorial premises:

- `editorial.guansha_coexistence.v1`: 正官 and 七杀 each occur at least once.
- `editorial.guansha_coexistence_female.v1`: the same coexistence AND female input.

These bind respectively to the two `legal_trouble` and two `infidelity` editorial
entries. The four entries are **reference-only**, with their original “也许” / “可能” text,
editorial attribution and full source boundaries. Satisfying a premise is not evidence
that a workplace, legal or relationship event happens.

```python
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextProfile, ContextResult, evaluate_context

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
result = evaluate_context(
  chart,
  criterion_id='editorial.guansha_coexistence.v1',
  profile=ContextProfile('natal_and_liunian', ganzhi_year=2024),
  include_reference_only=True,
)
print(result.render())
restored_record = ContextResult.from_json(result.export_json())
assert restored_record == result
```

The stem inventory is fixed: year/month/hour visible stems, every actual hidden
stem in all four natal branches, and the selected LIUNIAN's visible and hidden
stems when requested. The day-master visible stem is deliberately excluded;
a hidden stem equal to the day master is still classified 比肩. Hidden-stem percentages
are not weights. Repetitions are retained with pillar, query-local index, Ganzhi,
origin, layer, stem and 十神. No strength/count threshold, adjacency, 去留 or
effective 制化 condition is added.

`ContextProfile` requires `observation_scope='natal'` or `'natal_and_liunian'`.
The latter includes only LIUNIAN and requires a Ganzhi-year coordinate for a complete verdict.

This coordinate is a year label, not a Gregorian timestamp. `TransitChart.at_year(N)`
uses the year label `N` (2024 → 甲辰). Labels before the birth's Ganzhi year, including
zero and negative values, are unavailable; later labels have no upper bound.
Years accept only exact `int`, excluding `bool` and int subclasses. Natal scope rejects a year.

A missing year, unavailable query or missing required kind yields `UNKNOWN`, even if partial
natal observations already contain both classifications. Scope completeness takes precedence
over the female gate: a male input with a missing required year also yields `UNKNOWN`
with `missing_transit_coordinate`. Wrong types, unknown IDs and illegal combinations
raise `TypeError` / `ValueError`.

`SATISFIED` and `NOT_SATISFIED` describe a complete, explicitly selected premise.
`UNKNOWN` preserves known partial observations without claiming a complete
verdict. Four registered criteria (`tiangan.ding_weak_and_overcontrolled`,
`tiangan.geng_regulated_transit`, `shishen.pianyin_favorable_or_balanced`,
`shishen.xiaoyin_duoshi`) have undefined predicates, with their recorded
premises and limits. `described` / `unresolved` are knowledge organization,
not computed truth values.

Structural evaluation and entry matching are separate. For the four editorial
entries, a custom knowledge base with the same ID but a different entry, object,
premise, context, source or output binding yields `binding_unrecognized` for that
entry, rather than authenticating meaning by ID or keywords. Equal exported/reloaded bindings are usable.
Reference selection is opt-in; satisfying a premise never grants default
output eligibility. Independent `KnowledgeBase.render` performs no evaluation.
Missing bound entries produce no `EntryMatch` or display line. The four criteria with
undefined predicates display supplied same-ID entries under `predicate_undefined`.

Results are immutable. JSON preserves criterion definition, profile,
complete birth/gender/config identity, year/kind,
all occurrences and the complete supplied knowledge snapshot. Restoration is
record recovery, **not recalculation or authentication of a stored verdict**.
It does not cross-check verdict, evidence, input and entry bindings against each other.
Location input snapshots retain the same five time fields as chart JSON, including
the fixed civil basis and untruncated computed apparent clock. Their restoration validates the
roster and each field's spelling without recalculating the chart or recorded observations.

From a source checkout:

```sh
python run_interpreter.py \
  --match-context editorial.guansha_coexistence.v1 \
  --birth-time "2000-01-01 12:00" \
  --gender female \
  --observation-scope natal_and_liunian \
  --ganzhi-year 2024 \
  --include-reference-only \
  --export-context-json output_data/context.json
```

Matching requires fixed birth/gender and explicit observation scope. It rejects
random/count, legacy TXT export and knowledge-mode/filter flags. An optional
`--knowledge-source` supplies edited knowledge; `--export-context-json` refuses
to overwrite either that source or the bundled corpus, including filesystem
aliases. Matching always displays full source boundaries for selected entries.

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
| `--birth-time <time>`, `--gender male\|female` | Fixed birth; supply both together; aware input requires longitude |
| `--longitude <degrees>`, `--precision day\|hour\|minute` | Fixed chart calculation; longitude requires aware input and hour/minute precision |
| `--civil-timezone <zone>` | Explicit birth-region IANA zone or fixed offset; use `--civil-timezone=-05:00` for negative offsets; requires longitude |
| `--export-chart-json <path>` | Export the fixed chart as reloadable JSON |
| `--seed <integer>` | Reproducible random charts |
| `--count <positive integer>` | Random chart count; default 1 |
| `--include-reference-only` | Include reference text and label unevaluated conditions |
| `--show-sources` | Show IDs, attribution, witnesses and evidentiary boundaries; does not expand text selection |
| `--output-dir <path>` | Save the displayed charts as `interpretation_examples/0.txt`, etc. below this path |
| `--export-knowledge-base` | Write all 天干 / 十神 descriptions under `knowledge_base/`; default root `output_data/` |
| `-h`, `--help` | Show help |

Fixed birth inputs accept one chart and cannot be combined with a seed.

For a location chart with reloadable JSON:

```sh
python run_interpreter.py \
  --birth-time "2024-01-01T12:00:00+14:00" \
  --gender female \
  --longitude -157.4 \
  --precision minute \
  --export-chart-json output_data/chart.json
```

Matching accepts the same longitude, precision and civil-timezone flags. Location
flags require fixed birth input and are rejected in random and knowledge-only modes.
An aware input without longitude is still rejected; longitude requires an explicit
`hour` or `minute` precision. `--civil-timezone` accepts an IANA name or fixed offset
such as `+14:00`, and requires longitude. Negative offsets use equals syntax:
`--civil-timezone=-05:00`. The same spelling works in chart and matching modes.
Chart JSON export, like context export,
refuses to overwrite the bundled knowledge source or its filesystem aliases.

Reference-only text is labelled with source and premise states. Chart display and TXT
export prefix entries with knowledge topics and include the recorded
premises and limits. They do not select a chart's strength or fortune status.

Exported TXT files have terminal color codes removed.
Repeated exports overwrite the numbered files written by that run; other existing
files, including higher indices from earlier runs, are retained.

The 十神 percentages count three non-day-master stems plus four branch 主气
positions. Descriptions do not evaluate 旺衰, 喜忌 or 格局.

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
are not runtime dependencies. To regenerate and compare EOT without replacing the
bundled table, write a candidate into a directory outside the checkout:

```sh
python -m bazi.calendar.celestial_data.generator \
  --eot-only \
  --output-dir ../bazi-calendar-check
cmp ../bazi-calendar-check/equation_of_time.bin \
  bazi/calendar/celestial_data/data/equation_of_time.bin
```

If an installed table is missing, reinstall the distribution instead.

## License

Author-owned material is available under the standard [MIT License](LICENSE).
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) describes the separate scope of
calendar data, quotations and other third-party material. Those materials are not
relicensed by the author's MIT grant. Both notices are included in built artifacts.

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for version changes and
[RELEASING.md](RELEASING.md) for the manual release procedure.
