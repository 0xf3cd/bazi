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
  queries, premise and source display, and reloadable exports through `KnowledgeBase`.
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
inputs are rejected. To opt into apparent
solar time, pass an aware datetime and an east-positive `longitude` in `[-180, 180]`
to `Bazi` or `Bazi.create`; latitude is not consumed by this correction. The caller
owns the datetime's timezone, DST fold and historical offset. The birth-region civil
basis defaults to that timezone; pass `civil_timezone` (a `tzinfo`) when the input
expresses the instant in another zone. The actual offset at birth is frozen into a
fixed-offset civil datetime. The library does not infer a geographic or historical timezone.

The location-aware path supports only `CELESTIAL` with `HOUR` or `MINUTE` precision.
It preserves the input's seconds and microseconds. The apparent clock is the local
civil clock plus `longitude / 15 - civil UTC offset`, wrapped to `[-12h, 12h)`, plus
EOT evaluated at the exact UTC instant. Crossing midnight changes the apparent date.
Longitudes +180 and -180 identify the same meridian.
Its public clock, solar date, lunar/ganzhi date, day rollover and hour pillar use
local apparent solar time. Previous/next Jie lookup uses the absolute instant;
year/month attribution truncates both apparent clocks to the selected precision and
compares them at the same longitude and frozen birth-region offset, with ties on the new side.

Location identity and JSON preserve the exact UTC instant, civil basis, longitude,
gender and config. With the same explicit `civil_timezone`, alternate display offsets
of the same instant are equal, hash-equal and JSON-equal. Different civil bases remain
distinct; seconds remain distinct even when the displayed `solar_datetime` minute agrees.
Location JSON contains `time_basis='apparent_solar'`, `civil_time` (fixed-offset aware),
`canonical_instant` (UTC), `longitude` and `apparent_time` (untruncated computed naive clock).
The civil and UTC representations must denote the same instant.
EOT uses daily decisecond samples with linear interpolation; retaining microsecond
digits does not imply microsecond astronomical accuracy. Restoring a chart reconstructs
and checks all derived values. The supported birth-date window
applies to the apparent date (`1901-02-19` through `2099-12-31`), so its accepted UTC
instants depend on longitude and civil basis.

Dayun intervals and transit ordering use the absolute instant. Dayun boundaries
and existing transit query moments are naive UTC+08:00 labels, not apparent clocks,
and receive no moving-location correction. A New York birth at January 1, 20:00 UTC-05:00
can have an apparent birth date of January 1 but a UTC+08:00 date of January 2;
`TransitChart.at_date` uses the latter coordinate. Historical pre-1929 time-basis choices
remain outside this API and are tracked by issue #118.

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

Defaults are `CELESTIAL` with day precision. `hko` provides date-level calendar data;
`celestial` and `celestial-algo2` use the bundled astronomical tables. Backend differences
and supported date ranges are documented in the calendar modules; selecting a backend
does not install its offline generator.

### 出生归属与时间读取

年/月柱与大运数节共用出生精度归属：DAY 的整个交节日归新，HOUR 按时辰、MINUTE 按分钟
相等归新。`Bazi.month_jies` 返回出生月所属开月节及其下一节，保留后端原始时刻。
提前归属时，开月节可以在出生之后；逆排数节的负间隔钳零，首运年标签不早于出生干支年。
HKO 仍采用午夜节时刻，地点 DAY、地点 ALGO2 仍不支持。

例如默认盘输入 `2000-02-04 10:00`，年/月柱为庚辰/戊寅，所属节为立春
`2000-02-04T20:40:23`，下一节为惊蛰 `2000-03-05T14:42:39`。男性顺排起运为
`2010-02-25T07:09:05`；女性逆排钳在出生时刻 `2000-02-04T10:00:00`。
旧版 DAY 在真实交节前数向旧节的例外已删除，派生起运、小运及大运 JSON 因此可能改变。
`BaziChart.from_json` 按当前版本重算并核对完整记录；迁移旧记录时须从原出生输入重新建盘，
不能把旧派生值视作跨版本兼容记录。

```python
from bazi.calendar.dates import GanzhiYearMonth

assert chart.bazi.ganzhi_year_month == GanzhiYearMonth(1999, 11)
reference = located.reference_datetime
facts = located.location_time
assert facts is not None
print(facts.canonical_instant, facts.civil_time, facts.apparent_time)
print(located.solar_datetime, reference)
```

`GanzhiYearMonth` 是可排序的不可变干支年月坐标，月序为 1（寅）至 12（丑），不带归属粒度
或历法支持窗口；`from_dizhi` 接月支，`from_jie` 接真实开月节，拒绝中气。
出生坐标由 `ganzhi_year_month` 提供，物理大运边界和时刻流运仍按真实节归属；月、日期、
时刻查询各自保留支持端点，不与出生日期窗口合并。

`reference_datetime` 为节表、大运及流运共用参考时刻：默认盘采用分钟截断民用标签，地点盘
采用保留秒/微秒的 naive UTC+08 标签。`location_time` 为不可变 `LocationTime`，默认盘返回
`None`；地点盘提供 UTC 绝对瞬间、固定出生偏移民用钟、经度及未截断真太阳钟，`json` 返回
独立时间字段字典。分钟显示钟仍为 `solar_datetime`。读取这些事实不生成整盘 JSON。
真实“出生时刻前一节/后一节”用 `reference_datetime` 查询历法 `prev_jie` / `next_jie`，
不会用提前归属节替代物理前后节。

## Interfaces

Use the defining modules rather than expecting classes at the package root:

| Module | Principal interfaces |
| --- | --- |
| `bazi.bazi` | `Bazi`, `BaziGender`, `LocationTime`, `LocationTimeJson` |
| `bazi.bazi_chart` | `BaziChart`, `BaziJson`, JSON restoration with `from_json` |
| `bazi.school` | `BaziConfig`, `BaziSchool`, precision and school options |
| `bazi.calendar` | `CalendarBackend`, `CalendarDate`, `CalendarType`, `calendar_utils_of` |
| `bazi.calendar.dates` | `GanzhiYearMonth`, `JieqiTime` |
| `bazi.transit_chart`, `bazi.transits` | `TransitChart`, `TransitSet`, `TransitKind` |
| `bazi.analyzer.relationship` | `RelationshipAnalyzer` |
| `bazi.knowledge` | `KnowledgeBase`, `KnowledgeEntry`, `KnowledgeObject`, `KnowledgeRole`, `KnowledgeRelation`, `KnowledgeContext`, `KnowledgeSource`, `LegacyDescription`, `object_id`, `DEFAULT_SOURCE_PATH` |
| `bazi.context_matching` | `ContextProfile`, `ChartOccurrence`, `CriterionResult`, `EntryMatch`, `ContextResult`, `evaluate_context` |
| `bazi.defines`, `bazi.utils` | Domain enums and relation utilities, documented in their modules |

知识记录以 `KnowledgeBase` 为唯一模型。默认查询仅选 `output='default'` 的条目；
`include_reference_only=True` 同时查阅不具默认输出资格的参考条目。

Domain names use Pinyin; enums also provide Chinese aliases. JSON retains Chinese
domain values and records configuration. `py.typed` exposes the inline type hints.
Private names, offline generation tools and undocumented internals are not a
promise of a stable public interface.

[External chart comparisons](https://github.com/0xf3cd/bazi/blob/9c3a473563ce595d675efdc134428fe52243491b/EXTERNAL_BASELINE.md) document a synthetic boundary
baseline with configuration-specific results and an offline regression test.

### 地支关系查询与迁移

`bazi.utils.dizhi_utils` 的六个批量入口统一使用关键字参数 `definitions`，类型为规则层的
冻结对象 `DizhiRelationDefinitions`。原来的独立 `anhe_def`、`xing_def`、`gong_def` 查询参数
已删除；把这些值传给对象构造函数，再传给查询入口。对象只承载暗合、刑、拱局定义，构造时
检查各字段类型。盘级字段及 JSON 保留，由 `BaziSchool.relation_definitions` 提供查询对象。

```python
from bazi.defines import Dizhi, DizhiRelation, Ganzhi
from bazi.rules import DizhiRules, DizhiRelationDefinitions
from bazi.school import BaziSchool
from bazi.utils import dizhi_utils

definitions = DizhiRelationDefinitions(
  anhe_def=DizhiRules.AnheDef.MANGPAI,
  xing_def=DizhiRules.XingDef.STRICT,
  gong_def=DizhiRules.GongDef.SAME_STEM_WIDE,
)
assert DizhiRelation.暗合 not in dizhi_utils.discover(
  [Dizhi.寅, Dizhi.午],
  definitions=definitions,
)
school = BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)
gong = dizhi_utils.discover_ganzhis(
  [Ganzhi.from_str('甲寅'), Ganzhi.from_str('甲午')],
  definitions=school.relation_definitions,
  relations=(DizhiRelation.拱合, DizhiRelation.拱会),
)
assert gong.to_dizhi_discovery()[DizhiRelation.拱合] == (frozenset({Dizhi.寅, Dizhi.午}),)
```

`search`、`discover`、`discover_mutual` 只接地支；纯地支查拱局仍抛 `ValueError`。
`search_ganzhis`、`discover_ganzhis`、`discover_mutual_ganzhis` 保留完整干支与输入位置。
后两个入口可用 `relations` 限定求值范围，默认全部；重复关系只查一次，空序列不求值。
输入容器须为 `Sequence`，迭代器在消耗前被拒绝。单组拱局要求相邻，跨组拱局直接查两侧
柱位对；填实与流派条件仍适用。拱局投影只含两个实支，不含所拱虚支。

非拱跨组的按值查法与具体出现查法各自保留，不能互换。关系合并按左侧、右侧的首次出现
顺序去重；规则映射按定义序，集合表按枚举序，刑按规则表中的首次组合出现顺序输出。

### 基础接口与流派字段迁移

`BaziSchool` 的位置参数顺序已调整：前六项为 `day_rollover`、`anhe_def`、`xing_def`、
`gong_def`、`yangren_def`、`feiren_def`，之后为神煞锚及相邻的定义字段。调用方应改用
关键字参数；JSON 键名、默认值和各读法不变，输出键序随字段声明序调整。
`BaziSchool.from_json` 仍要求全部字段，以键名解析，不依赖输入字典的键序。

`Shishen.str_mapping_table()` 已删除；字符串解析仍接受完整名称与十个单字简称，
枚举的 `abbr` 返回简称。需要简称映射时可用 `{s.abbr: str(s) for s in Shishen}`。
`Ganzhi` 仍可持有十干×十二支的120种组合，`next`／`prev` 只适用于六十甲子；
阴阳不配的组合明确抛 `ValueError`，包括零步。步数仍接受 `int`、`bool` 与 `int` 子类。

`Jieqi.jies()` 返回从立春开始的十二节元组，`ganzhi_year=False` 改为从小寒开始的公历年序；
中气不在其中，年序参数只接受 `bool`。干支年月坐标、两历法后端的月长和前后节查询共用
这一节序入口，各后端仍独立计算日期和时刻。

### 知识接口迁移

`bazi.descriptions`、`bazi.interpreter` 及其枚举、重复记录、字段表和 `Interpreter` 方法已删除，
这是破坏性 API 变更。调用方改用现代记录；新接口不再返回旧字段字典或可变文字列表。
源码脚本 `run_interpreter.py` 继续提供命盘展示、知识查询和导出，没有安装 CLI。

```python
from bazi.defines import Tiangan
from bazi.knowledge import KnowledgeBase, object_id

knowledge = KnowledgeBase.load()
identifier = object_id(Tiangan.丁)
for entry in knowledge.query(object_id=identifier, include_reference_only=True):
  print(entry.claim_id, entry.text, entry.output, entry.applicability)
  print(entry.legacy)  # Traceable old field, ordinal, conditions and field premise.
  for source_id in entry.sources:
    witness = knowledge.sources[source_id]
    print(witness.work, witness.edition, witness.locator, witness.url)
    print(witness.supports, witness.limitations)

print(knowledge.render_subject(identifier, include_reference_only=True, show_sources=True))
```

`sources` 是完整的不可变来源注册表，包含未被条目引用的见证；新增来源无需补枚举。
来源记录的文本层、谱系、状态和证据限度各自保留。`query(source_id=...)` 选择关联条目，
与直接读取 `sources[source_id]` 不同。`object_id` 将天干、十神及其中文别名转为稳定 ID；
其他对象直接使用 `objects` 中注册的字符串标识。

`render_subject` 为命盘与 TXT 共用的带主题文字投影：有 `legacy` 的条目只在旧主体下展示，
其余条目包含所有绑定角色。它保留语料顺序；`query(object_id=...)` 则始终包含所有角色。
例如 SH-052 的主体是食神、关联角色含七杀：对象查询两边都能找到，主体展示只放在食神下。
旧字段位置与 `ordinal` 在 `LegacyDescription` 中保全，不与语料顺序合并；需要复核旧位置时，
按 `legacy.object_id`、`legacy.field` 选择并按 `legacy.ordinal` 排序。

参考查阅保留历史象、仓内整理和来源未核实文字，不判断命盘适用性。空 `sources` 和
`Legacy corpus; source unverified` 署名不表示没有来源或断言为假。旧 `chart_context_required`
记录前提，不是求值结果；`in_good_status` / `in_bad_status` 是旧位置，不是现代知识分类。
知识选择与 `BaziSchool` 的计算变体分开。

### Maintain and query interpretation knowledge

`bazi/knowledge_data.json` is the unique editing source. Loading validates its schema,
IDs, role bindings, references and output policies, then builds in-memory indexes.
The same file is bundled in wheels and source archives; exports and text projections
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

`DEFAULT_SOURCE_PATH` 是默认加载及源码 CLI 防覆盖共用的随库编辑源路径，指向当前安装或
检出中的 `knowledge_data.json`。自定义源仍通过 `KnowledgeBase.load(Path(...))` 读取。
公开 `render(entry, show_sources=..., manual_context=..., premise_verdict=...)` 只展示条目；
`premise_verdict` 是调用方提供的文字，优先于人工情境标注，不求值前提、不授予默认资格。
实际前提判别仍由 `evaluate_context` 执行；未定义的判据仍返回 `UNKNOWN`。

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
all occurrences and the complete supplied knowledge snapshot. In memory, results
share the validated `KnowledgeBase`; evaluation and rendering do not rebuild it.
Exports use `record_version=2`; version 1 is rejected. Re-evaluate the original
birth input and configuration to obtain a new record. Occurrence indices are
derived from pillar positions, and the fixed stem scope is not stored.
Restoration is
record recovery, **not recalculation or authentication of a stored verdict**.
It does not cross-check verdict, evidence, input and entry bindings against each other.
Location input snapshots retain the same five time fields as chart JSON, including
the fixed civil basis and untruncated computed apparent clock. Their restoration validates the
roster, canonical spellings and civil/UTC instant equivalence without recalculating the
chart or recorded observations.

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

All three runners accept `--seed <integer>`. Without it, they generate and print
the actual seed; replay by passing that value. Displays include birth time and gender.
The full gate passes seed 236 to each runner.

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
| `--civil-timezone <zone>` | Explicit birth-region IANA zone or fixed offset; requires longitude |
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
`--civil-timezone=-05:00`.
Chart JSON export, like context export,
refuses to overwrite the bundled knowledge source or its filesystem aliases.
Chart JSON paths that overlap TXT outputs generated by the same run are rejected
before any output is created, including symbolic-link and hard-link aliases.

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

Random pytest inputs use `--random-seed` (default base 236). Each `rng` fixture
prints its node ID, base seed and effective seed. The effective seed is the first
eight bytes of SHA-256 of UTF-8 `"<base>:<nodeid>"`, interpreted as an unsigned
big-endian integer. It initializes a real local `Random`, leaving global state alone.
Replay a single test with the same base and full node ID:

```sh
python -m pytest tests/test_bazi_chart.py::test_dayun_order --random-seed 236 -s
```

The collected relationship cases use seeds `base` through `base + 4`; their IDs
include the actual seed, birth time and gender. Changing the base changes these
cases too. From the repository root, rerun one case with the same base:

```sh
python -m pytest \
  'tests/integration/test_relationship_analysis.py::test_random_cases[seed=236-birth=2074-06-16T23:22:00-gender=male]' \
  --random-seed 236
```

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
