# Bazi

> 排盘、五行、十神、纳音、刑冲破害、合会

面向中文用户的 Python 3.11+ 八字排盘库，提供四柱、流运、关系与解释知识查询。
运行时只用标准库、六份随库历法表及知识语料，无需联网或生成数据。
本文说明当前检出；使用已发布包时，请读对应 release tag 的 README。

## 安装与快速排盘

已发布版本用 `python -m pip install bazi==1.0.0` 安装。
若要构建、验证当前源码并保留可安装工件对，在源码检出中运行：

```sh
python -m pip install -r Requirements.txt
python run_package_checks.py --output-dir ../bazi-tested
python -m pip install ../bazi-tested/bazi-1.0.0-py3-none-any.whl
```

输出目录须为空且在仓外。安装包为 bazi，从定义模块导入，没有安装 CLI、src 兼容包或根类入口。
下文每个 Python 块均可独立复制运行。

```python
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.school import BaziConfig

config = BaziConfig.from_values(backend='celestial', precision='day')
chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male', config))
restored = BaziChart.from_json(chart.json)
assert restored.json == chart.json
print(chart.json['pillars'])
print(chart.traits, chart.shishen, chart.hidden_tiangan)
print(chart.nayin, chart.shier_zhangsheng)
```

功能入口：

| 模块 | 主要接口与用途 |
| --- | --- |
| `bazi.bazi` | `Bazi`、`BaziGender`、`LocationTime`、`LocationTimeJson`：四柱与出生时间事实 |
| `bazi.bazi_chart` | `BaziChart`、`BaziJson`：阴阳五行、十神、藏干、纳音、十二长生、大运及 JSON 恢复 |
| `bazi.school` | `BaziConfig`、`BaziSchool`：出生精度、历法、流派及大运年份投影 |
| `bazi.calendar` | `CalendarBackend`、`CalendarDate`、`CalendarType`、`calendar_utils_of`：历法换算 |
| `bazi.calendar.dates` | `GanzhiYearMonth`、`JieqiTime`：干支年月坐标与节时刻 |
| `bazi.transit_chart`、`bazi.transits` | `TransitChart`、`TransitSet`、`TransitKind`：按年、月、日期、时刻查流运 |
| `bazi.analyzer.relationship` | `RelationshipAnalyzer`：原局与流运的亲密关系、神煞分析 |
| `bazi.knowledge` | `KnowledgeBase`、`KnowledgeEntry`、`KnowledgeObject`、`KnowledgeRole`、`KnowledgeRelation`、`KnowledgeContext`、`KnowledgeSource`、`LegacyDescription`、`object_id`、`DEFAULT_SOURCE_PATH`：不可变知识记录、查询与导出 |
| `bazi.context_matching` | `ContextProfile`、`ChartOccurrence`、`CriterionResult`、`EntryMatch`、`ContextResult`、`evaluate_context`：显式范围前提判别 |
| `bazi.defines`、`bazi.utils` | 领域枚举与关系工具，具体契约见各模块说明 |

领域名称用拼音，枚举另有中文别名。JSON 保留中文领域值与配置，py.typed 提供内联类型标注。
私有名称、离线生成工具及未记录的内部实现不承诺稳定公开接口。
[固定提交的外部排盘证据](https://github.com/0xf3cd/bazi/blob/9c3a473563ce595d675efdc134428fe52243491b/EXTERNAL_BASELINE.md)
记录合成边界、特定配置结果及离线回归；这是历史证据，当前仓内说明见
[EXTERNAL_BASELINE.md](https://github.com/0xf3cd/bazi/blob/main/EXTERNAL_BASELINE.md)。

## 配置与时间口径

默认配置为 CELESTIAL、DAY 精度。hko 提供日期级数据，celestial 与 celestial-algo2 读取随库天文表。
后端差异与支持范围见历法模块；选择后端不安装离线生成器。

```python
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.school import BaziConfig, BaziSchool, DayRollover, DayunYearRule

config = BaziConfig.from_values(
  precision='minute',
  school=BaziSchool(day_rollover=DayRollover.ZIZHENG),
  dayun_year_rule=DayunYearRule.FIXED_DECADE,
)
chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 23, 30), 'male', config))
assert BaziSchool.from_json(chart.json['school']) == config.school
print(chart.json['school'])
```

BaziSchool 声明换日、关系与神煞的可选读法，出处及支持锚见 school.py 和 rules.py。
知识条目选择与这些计算变体分开。

### 出生归属与时间读取

年/月柱与大运数节共用出生精度归属：DAY 的整个交节日归新，HOUR 按时辰、MINUTE 按分钟
相等归新。Bazi.month_jies 返回出生月所属开月节及其下一节，保留后端原始时刻。
提前归属时，开月节可以在出生之后；逆排数节的负间隔钳零，首运年标签不早于出生干支年。
HKO 仍采用午夜节时刻。

例如默认盘输入 2000-02-04 10:00，年/月柱为庚辰/戊寅，所属节为立春
2000-02-04T20:40:23，下一节为惊蛰 2000-03-05T14:42:39。
男性顺排起运为 2010-02-25T07:09:05；女性逆排钳在出生时刻 2000-02-04T10:00:00。

```python
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from bazi.bazi import Bazi
from bazi.calendar.dates import GanzhiYearMonth
from bazi.school import BaziConfig

ordinary = Bazi.create(datetime(2000, 1, 1, 12), 'male')
assert ordinary.ganzhi_year_month == GanzhiYearMonth(1999, 11)
located = Bazi.create(
  datetime(2023, 12, 31, 22, tzinfo=UTC),
  'male',
  BaziConfig.from_values(precision='minute'),
  longitude=-157.4,
  civil_timezone=ZoneInfo('Pacific/Kiritimati'),
)
reference = located.reference_datetime
facts = located.location_time
assert facts is not None
print(facts.canonical_instant, facts.civil_time, facts.apparent_time)
print(located.solar_datetime, reference)
```

GanzhiYearMonth 是可排序的不可变干支年月坐标，月序为 1（寅）至 12（丑），不带归属粒度
或历法支持窗口；from_dizhi 接月支，from_jie 接真实开月节，拒绝中气。
出生坐标由 ganzhi_year_month 提供。物理大运边界与时刻流运按真实节归属，月、日期、时刻查询
各有支持端点，不与出生日期窗口合并。

`reference_datetime` 为节表、大运及流运共用参考时刻：默认盘为分钟截断的民用标签，地点盘为
保留秒/微秒的无时区 UTC+08 标签。`location_time` 为不可变 `LocationTime`，默认盘返回 `None`；
地点盘提供 UTC 绝对瞬间、固定出生偏移民用钟、经度及未截断真太阳钟，`json` 每次返回独立时间字段字典。
`solar_datetime` 仍只显示分钟，读取上述事实不生成整盘 JSON。
真实出生前后节以 `reference_datetime` 查询历法 `prev_jie` / `next_jie`，不用提前归属节替代物理前后节。

### 地点与真太阳时

无经度时，出生输入为无时区当地民用时刻，拒绝带时区输入。
显式启用真太阳时须给 Bazi 或 Bazi.create 带时区 datetime，以及东经为正、范围 [-180, 180] 的
`longitude`；不使用纬度。输入时区、DST `fold` 及历史偏移由调用方负责。
出生地区民用基准默认采用输入时区；输入用其他时区表示瞬间时，须用 `civil_timezone`（`tzinfo`）指定出生基准。
本库冻结出生瞬间的实际偏移，得到固定偏移民用 datetime，不推断地理或历史时区。

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

地点路径只支持 CELESTIAL 的 HOUR / MINUTE，保留输入秒及微秒。
真太阳钟等于当地民用钟，加 `longitude / 15 - civil UTC offset`（回绕到 [-12h, 12h)），
再加精确 UTC 瞬间的 EOT。跨午夜会改变真太阳日期，+180 与 -180 为同一子午线。
公开显示钟、公历日期、农历／干支日期、换日和时柱均采用当地真太阳时。
物理前后节按绝对瞬间查询；年/月归属把出生与节的真太阳钟按同一经度、冻结出生偏移及所选精度
截断比较，相等归新。

地点身份与 JSON 保留精确 UTC 瞬间、民用基准、经度、性别与配置。
同一瞬间在相同显式 civil_timezone 下用不同显示偏移输入，相等性、哈希与 JSON 均相等。
不同民用基准仍有不同身份；秒不同仍有不同身份，即使 solar_datetime 分钟显示相同。
地点 JSON 含 time_basis='apparent_solar'、civil_time（固定偏移且带时区）、canonical_instant（UTC）、
longitude 与 apparent_time（未截断的无时区计算钟），民用与 UTC 表示须指向同一瞬间。

EOT 采用每日十分之一秒样本及线性插值，保留微秒位不表示天文精度到微秒。
命盘恢复重建并核全部派生值。出生支持窗口 1901-02-19 至 2099-12-31 按真太阳日期限制，
接受的 UTC 瞬间范围因此随经度与民用基准不同。

大运区间与流运顺序使用绝对瞬间。大运边界及现有流运查询时刻为无时区 UTC+08:00 标签，
不是真太阳钟，不做移动地点修正。例如纽约一月一日 20:00 UTC-05:00 出生，真太阳日期可为一月一日，
UTC+08:00 日期却为一月二日；TransitChart.at_date 使用后者。1929 年前历史时间基准选择另见 #118。

## 破坏性迁移

- 旧版 DAY 在真实交节前仍数向旧节的例外已删除，起运、小运及大运 JSON 可能改变。
  BaziChart.from_json 按当前版本重算并核完整记录；旧记录须从原出生输入重建，不能把旧派生值
  当跨版本兼容记录。
- BaziSchool 的位置参数顺序改为 day_rollover、anhe_def、xing_def、gong_def、yangren_def、
  feiren_def，其后为神煞锚及相邻定义。调用方应改用关键字参数；JSON 键名、默认值与读法不变，
  输出键序随声明序调整。from_json 仍要求全部字段，按键名解析，不依赖输入键序。
- Shishen.str_mapping_table() 已删除。from_str 仍接受完整名称及十个单字简称，abbr 返回简称；
  需要简称映射时用 `{s.abbr: str(s) for s in Shishen}`。
- ContextResult 的 knowledge_json 构造字段及属性已删除，改传 knowledge: KnowledgeBase；
  原完整知识 JSON 可先交给 KnowledgeBase.from_json。ContextProfile.stem_scope 属性已删除。
  ChartOccurrence 构造不再接受 index，第三个位置参数变为 ganzhi；建议使用具名参数。
  index 仍为按 pillar 派生的只读属性，不进入 JSON，展示只保留柱位。

## 运限与关系

大运各步有完整半开物理区间 `[start_moment, end_moment)`。
JIE_PROJECTED 逐边界按所属节投影干支年，首标签不早于出生干支年；FIXED_DECADE 从共同首标签起
每步加十年，只改变年表标签，不改变物理时刻线。年份视图的末区间延伸到末标签后十年，
可与物理 `end_moment` 不同。

```python
from datetime import date, datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Dizhi
from bazi.school import BaziConfig
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind
from bazi.analyzer.relationship import RelationshipAnalyzer

chart = BaziChart(Bazi.create(
  datetime(2000, 1, 1, 12),
  'male',
  BaziConfig.from_values(precision='minute'),
))
transits = TransitChart(chart)
year = transits.at_year(2024)
assert year is not None
print(year)
print(transits.at_month(2024, Dizhi.辰))
print(transits.at_date(date(2024, 4, 10)))
print(transits.at_moment(datetime(2024, 4, 10, 12)))
analyzer = RelationshipAnalyzer(chart)
print(analyzer.at_birth.shensha)
print(analyzer.transits.shensha(year.select(TransitKind.LIUNIAN)))
print(analyzer.transits.house_relations(year))
```

`TransitSet` 按小运、大运、流年、流月、流日的固定顺序持有具名干支；`select` 要求请求非空、
无重复且全部存在，返回仍按固定顺序。`at_year` 按年份标签解释大运；月、日期与时刻查询按物理边界。
`at_moment` 仅在支持真实节时刻且原盘为 HOUR / MINUTE 时可用，按整秒比较出生、查询与大运边界，
相等归新。月、日期与时刻入口在出生前或各自表范围外返回 None；不支持时刻查询也返回 None。

### 地支查询与迁移

bazi.utils.dizhi_utils 的六个批量入口统一接关键字 definitions，类型为规则层冻结
DizhiRelationDefinitions。原查询参数 anhe_def、xing_def、gong_def 已删除，改传对象；
对象只承载暗合、刑与拱局定义，构造时校验字段类型。盘级字段及 JSON 保留，
BaziSchool.relation_definitions 提供单次查询对象。

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

search、discover、discover_mutual 只接地支，纯地支查拱局仍抛 ValueError。
search_ganzhis、discover_ganzhis、discover_mutual_ganzhis 保留完整干支及输入位置；
后两者可用 relations 限定求值范围，默认全部，重复只查一次，空序列不求值。
容器须为 Sequence，迭代器在消耗前被拒。单组拱局要求相邻，跨组直接查两侧柱位对，
填实与流派条件仍适用；投影只含两个实支，不含所拱虚支。

非拱跨组的按值查法与具体出现查法不可互换。

| 返回结果 | 组合顺序 |
| --- | --- |
| 纯地支组合（search、discover、discover_mutual） | 映射表按定义序，集合表按组合成员枚举序；刑按规则表首次组合出现序，生克按施方、受方枚举序排序后折为无向组合。 |
| 非拱具体出现（search_ganzhis） | 先沿对应地支组合序，再按输入序号组合展开同值的多处出现。 |
| 拱局具体出现 | 单组按相邻柱位对序；跨组按左侧柱位优先的两侧柱位对序。 |

discover_ganzhis、discover_mutual_ganzhis 的关系键按 relations 首次出现顺序求值，键内组合沿对应查询顺序。
亲密关系分析的神煞锚与定义来自本盘流派，
拱局的日柱参与按具体位置判断，不以同值地支替代。

## 知识与前提匹配

`KnowledgeBase` 为知识记录的唯一模型。默认查询只选 `output='default'` 条目，
`include_reference_only=True` 才同时查阅不具默认输出资格的参考条目。
`bazi/knowledge_data.json` 是唯一编辑源；加载校验 schema、ID、角色绑定、引用及输出政策后建索引。
同一文件随 wheel 与源码包分发，导出及文字投影由它派生，无需数据库服务或运行时依赖。

### 知识接口与迁移

bazi.descriptions、bazi.interpreter、Interpreter 及旧枚举、重复记录和字段表已删除，是破坏性 API 变更。
改用现代不可变记录，不再返回旧字段字典或可变文字列表。
源码 run_interpreter.py 继续提供命盘展示、知识查询及导出，没有安装 CLI。

```python
from bazi.defines import Tiangan
from bazi.knowledge import KnowledgeBase, object_id

knowledge = KnowledgeBase.load()
identifier = object_id(Tiangan.丁)
for entry in knowledge.query(object_id=identifier, include_reference_only=True):
  print(entry.claim_id, entry.text, entry.output, entry.applicability)
  print(entry.legacy)  # 旧字段、序号、条件及字段前提的溯源记录。
  for source_id in entry.sources:
    witness = knowledge.sources[source_id]
    print(witness.work, witness.edition, witness.locator, witness.url)
    print(witness.supports, witness.limitations)
print(knowledge.render_subject(identifier, include_reference_only=True, show_sources=True))
```

sources 是完整不可变来源注册表，包含未被条目引用的见证，新增来源无需补枚举。
来源文本层、谱系、状态及证据限度分别保留；query(source_id=...) 筛关联条目，
直接 sources[source_id] 则读取见证。object_id 将天干、十神及其中文别名转为稳定 ID，
其他对象用 objects 中注册的字符串 ID。

render_subject 为命盘与 TXT 共用的带主题文字投影：有 legacy 的条目只在旧主体下展示，
其他条目含所有绑定角色，保留语料顺序。query(object_id=...) 始终包含所有角色。
例如 SH-052 主体为食神，关联角色含七杀，对象查询两侧均可找到，主体展示只放食神下。
LegacyDescription 保全旧字段位置与 ordinal；核旧位置时按 legacy.object_id、legacy.field 选择，
再按 legacy.ordinal 排序，不与语料顺序混同。

参考查阅保留历史象、仓内整理与来源未核实文字，不判断命盘适用性。空 sources 或
`Legacy corpus; source unverified` 署名不表示无来源或断言为假。
chart_context_required 是旧前提记录；in_good_status / in_bad_status 是旧位置，不是现代知识分类。
五行／国印参考例保留既有规则说明及限度，仓内署名不等于新核定的古籍见证。

### 查询、编辑与导出

```python
from pathlib import Path
from tempfile import TemporaryDirectory

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

# 显式准备自定义源副本；可在副本上编辑，示例直接重载，不改随库语料。
with TemporaryDirectory() as directory:
  path = Path(directory) / 'edited-knowledge.json'
  path.write_text(knowledge.export_json(), encoding='utf-8')
  edited = KnowledgeBase.load(path)
  assert edited == knowledge
```

| 条目信息 | 含义 |
| --- | --- |
| `roles`、`relations` | 具名讨论对象与有方向的文字关系，不表示已计算或生效的命盘作用 |
| `topics`、`viewpoint` | 查阅主题与解释采用的观点 |
| `applicability='unconditional'` | 无命盘前提的知识陈述，如定义、历史象 |
| `applicability='described'` | 已记录前提文字，术语仍可能没有计算定义 |
| `applicability='unresolved'` | 前提仍待重建，旧条件元组为空不解决此问题 |
| `premise`、`contexts`、`limits`、`exceptions` | 完整前提、带时间范围的具名情境、未解术语及边界 |
| `sources`、`source_state`、`attribution` | 来源引用及 witnessed / editorial / unverified / repository-attributed 状态 |
| `output`、`legacy` | 输出资格及旧字段、顺序、条件元数据 |

人工选择情境只检索知识，不判断命盘是否满足。多个情境标签不隐含 AND/OR。
例如庚金流运条目保留行运有制有化与后天有教养，前者在此未定义，后者为盘外前提，不能据基本生克认定任一前提满足。

`query` 对 `object_id`、`context_id`、`topic`、`source_id`、`viewpoint`、`applicability`、`time_scope` 取交集，
返回保留语料顺序、深度不可变的元组。未知过滤值抛 `ValueError`，合法但无匹配返回空元组；
参考条目须显式选择，`entry(claim_id)` 按稳定 ID 读取。
`export_json()` 导出全部语料，包括参考记录及其政策；`export_json(entries)` 导出所选条目。
两者均保留完整对象、情境、来源注册表，支持重载与证据展示；导出不改变输出资格。
冻结旧位置测试数据只作迁移参照，不是第二编辑源。

`DEFAULT_SOURCE_PATH` 为加载与源码 CLI 防覆盖共用的随库编辑源路径，指向当前安装或检出中的
`knowledge_data.json`；自定义源用 `KnowledgeBase.load(Path(...))`。
`render(entry, show_sources=..., manual_context=..., premise_verdict=...)` 只展示，
`premise_verdict` 为调用方文字，优先于人工情境标注，不求值或授予默认资格；实际判别由 `evaluate_context` 执行。

源码检出中可校验、查询并导出：

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

| 知识参数 | 用途 |
| --- | --- |
| `--query-knowledge` | 不建盘，查询并展示知识，包含来源详情 |
| `--validate-knowledge` | 校验完整编辑源 |
| `--knowledge-source <path>` | 读取自定义或导出的 JSON |
| `--object`、`--context`、`--topic`、`--source`、`--viewpoint`、`--applicability`、`--time-scope` | 查询过滤条件，context 明确为人工选择 |
| `--export-knowledge-json <path>` | 导出全部记录；配 query-knowledge 时导出所选记录 |
| `--include-reference-only` | 查询时包含参考条目 |

知识模式拒绝命盘输入、output-dir 和旧 TXT 导出参数；不选择知识模式时仍有命盘 runner 的原参数组合。
JSON 导出拒绝覆盖编辑源，包括文件系统别名。

### 显式范围前提判别

两个已定义判据只求仓内原作前提：editorial.guansha_coexistence.v1 要求正官、七杀各至少出现一次；
editorial.guansha_coexistence_female.v1 再要求女命输入。
它们分别绑定两个 legal_trouble 与两个 infidelity 原作条目。四条均 reference-only，保留原“也许”／
“可能”文字、原作署名及完整来源边界；前提满足不证明职场、法律或关系事件发生。

```python
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextProfile, ContextResult, evaluate_context
from bazi.knowledge import KnowledgeBase

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
knowledge = KnowledgeBase.load()
result = evaluate_context(
  chart,
  criterion_id='editorial.guansha_coexistence.v1',
  profile=ContextProfile('natal_and_liunian', ganzhi_year=2024),
  knowledge=knowledge,
  include_reference_only=True,
)
print(result.render())
restored_record = ContextResult.from_json(result.export_json())
assert restored_record == result
```

天干观察固定包含原局年、月、时明干、四支全部实际藏干，以及请求的单流年明干与藏干。
排除日主明干，但等于日主的藏干仍分类为比肩；藏干百分比不作权重。
重复观察保留柱位、查询内序号、干支、origin、layer、天干与十神，不另加力量／次数阈值、相邻、去留或有效制化条件。

ContextProfile 必须显式选 observation_scope='natal' 或 'natal_and_liunian'。
后者只含 LIUNIAN，完整判别需要干支年坐标；该坐标为年标签，不是公历时间戳。
TransitChart.at_year(N) 按标签 N 查（2024 为甲辰）；早于出生干支年的标签不可用，包括零与负值，
后续标签无上界。ContextProfile 年份只接确切 int，拒绝 bool 与 int 子类；natal 不接受年份。

缺年份、查询不可用或缺必需 kind 均返回 UNKNOWN，即使已知局部原局观察已见官杀。
范围完整性优先于女命条件：男命缺必需年份也为 UNKNOWN / missing_transit_coordinate。
错误类型、未知 ID 与非法组合抛 TypeError / ValueError。
SATISFIED / NOT_SATISFIED 描述完整的显式前提，UNKNOWN 保留局部事实但不声称完整判别。
四个判据 tiangan.ding_weak_and_overcontrolled、tiangan.geng_regulated_transit、
shishen.pianyin_favorable_or_balanced、shishen.xiaoyin_duoshi 尚无完整计算定义，仍保留前提与限度。
described / unresolved 为知识整理状态，不是计算真值。

结构求值与条目匹配分开。四条原作绑定若在自定义库中改变同 ID 的条目、对象、前提、情境、来源或
输出政策，该条返回 `binding_unrecognized`，不能仅凭 ID 或关键词判断语义一致；与原绑定等值的导出重载条目仍可绑定。
前提满足不授予默认输出资格，独立 KnowledgeBase.render 不求值。参考条目须显式设置 include_reference_only=True；
未选择参考条目或缺绑定条目时不生成其 EntryMatch 或显示行；
四个未定义判据对提供的同 ID 条目显示 predicate_undefined。

结果不可变，JSON 保留判据定义、profile、完整出生／性别／配置身份、年份／kind、全部观察及完整输入知识快照。
传入已加载的 KnowledgeBase 时复用该对象；省略 knowledge 时每次独立加载默认语料，渲染不重建知识对象。
导出 record_version=2，拒绝版本 1；旧记录须以原出生输入及配置重新求值。
恢复只取回记录，不重算或认证已存判别，不交叉验证判别、证据、输入与条目绑定的一致性。
地点输入快照保留与命盘 JSON 相同的五个时间字段，包括固定民用基准及未截断真太阳钟；
恢复校验字段集合、规范拼写及民用／UTC 瞬间相等，不重算命盘或观察。

源码匹配命令：

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

匹配须给固定出生／性别与显式观察范围，拒绝随机／count、旧 TXT 导出及知识模式／过滤参数。
可用 knowledge-source 给自定义知识；export-context-json 拒绝覆盖该源或随库语料，包括文件系统别名。
所选条目始终展示完整来源边界。

## 源码命盘示例与 help

先按[开发](#开发)安装环境，在源码检出中运行；以下默认均生成随机命盘：

| 命令 | 输出 |
| --- | --- |
| python run_demo.py | 命盘、大运／小运／流年及命盘 JSON |
| python run_relationship_analyzer.py | 夫妻宫、配偶星、原局神煞及十年流年神煞 |
| python run_interpreter.py | 单盘静态说明，默认不导出文件 |

三者均接受 seed，未给时生成并打印实际种子；展示含出生时刻与性别，完整门禁给各 runner 种子 236。
带来源的可重放示例：

```sh
python run_interpreter.py --seed 42 --show-sources
```

固定出生及完整参考文字：

```sh
python run_interpreter.py \
  --birth-time "2000-01-01 12:00" \
  --gender male \
  --include-reference-only \
  --show-sources
```

显式导出随机命盘与天干／十神文字：

```sh
python run_interpreter.py \
  --seed 42 \
  --count 5 \
  --output-dir output_data \
  --export-knowledge-base
```

| 命盘参数 | 用途 |
| --- | --- |
| `--birth-time <time>`、`--gender male\|female` | 固定出生，两者须一起给；带时区输入须给经度 |
| `--longitude <degrees>`、`--precision day\|hour\|minute` | 固定命盘计算；经度须配带时区输入及 hour/minute |
| `--civil-timezone <zone>` | 显式出生地区 IANA 时区或固定偏移，须给经度 |
| `--export-chart-json <path>` | 导出固定命盘为可重载 JSON |
| `--seed <integer>` | 重放随机命盘 |
| `--count <positive integer>` | 随机命盘数，默认 1 |
| `--include-reference-only` | 包含参考文字，标记未求值前提 |
| `--show-sources` | 展示 ID、署名、见证及证据限度，不扩大条目选择 |
| `--output-dir <path>` | 在路径下存 interpretation_examples/0.txt 等已展示命盘 |
| `--export-knowledge-base` | 将全部天干／十神文字写到 knowledge_base/，默认根目录 output_data/ |
| `-h`、`--help` | 显示帮助 |

固定出生只接一个命盘，不能配 seed。地点参数要求固定出生，随机或纯知识模式拒绝它们。
civil-timezone 接 IANA 名或 +14:00 等固定偏移，负偏移须用 `--civil-timezone=-05:00`。
地点 JSON 导出示例：

```sh
python run_interpreter.py \
  --birth-time "2024-01-01T12:00:00+14:00" \
  --gender female \
  --longitude -157.4 \
  --precision minute \
  --export-chart-json output_data/chart.json
```

前提匹配接相同经度、精度及民用时区参数。命盘 JSON 导出拒绝覆盖随库知识源及文件系统别名。
命盘 JSON 路径若与同次 TXT 输出重叠，在生成任何输出前即拒绝，包括符号链接与硬链接别名。

参考文字标明来源与前提状态。命盘展示和 TXT 以主题作前缀，包含前提及限度，不选旺衰、喜忌或格局。
十神百分比只计三个非日主明干加四支主气位置，说明文字不评估旺衰、喜忌或格局。
TXT 去掉终端色码；重复导出覆盖本次编号文件，其他文件及旧运行的更高序号文件保留。

## 开发

Requirements.txt 为开发环境，含测试、lint、类型与发行验证工具，不是安装库的依赖列表。
源码 mypy 另需 CPython CI 所用的 celestial-calendar==0.6.1。

```sh
python -m pip install -r Requirements.txt
python -m pip install celestial-calendar==0.6.1
python run_tests.py -a -v
```

完整门禁执行所有测试（含 slow 与 hkodata），要求 100% 覆盖率，运行 ruff、完整 flags 的源码 mypy、
两个 demo、`run_interpreter.py` 示例、`python -O` 公开输入契约冒烟及隔离 wheel／sdist 重建 wheel 检查。
工件检查使用两个无依赖的新消费者环境及独立安装 mypy 环境；run_package_checks.py、-pkg、-a
仍可能从包索引下载构建及类型工具与依赖，即使开发依赖已安装。
构建与消费者在仓外临时目录；根 demo 可写 output_data/，安装库只读行为另行验证。

| 参数 | 用途 |
| --- | --- |
| `-a`、`--all` | 完整门禁，覆盖 -nt 与 -k |
| `-nt`、`--no-test` | 跳过测试与覆盖率 |
| `-s`、`-hko` | 包含 slow 或 hkodata 测试 |
| `-k <expression>` | 筛选 pytest，忽略 -s 与 -hko |
| `-v` | 详细输出 |
| `-c` | 覆盖率报告，另写 covhtml/ |
| `-cr <rate>`、`--coverage-rate <rate>` | 最低覆盖率，默认 100 |
| `-r`、`--ruff` | 运行 ruff check |
| `-m`、`-mypy`、`--mypy` | 按 runner 完整 flags 运行源码 mypy |
| `-d` | 运行两个 demo |
| `-i` | 运行 `run_interpreter.py` 示例 |
| `-osmoke`、`--o-smoke` | 用 python -O 运行源码公开输入契约冒烟 |
| `-pkg`、`--package` | 隔离发行检查 |
| `--package-output-dir <path>` | 与 -pkg 或 -a 一起保留已验证 sdist 及其重建 wheel |

裸 python run_tests.py 排除 slow/hkodata，且不执行可选任务，不能替代完整门禁。
不用自动格式化器，只用 `ruff check .`。

pytest 随机输入使用 --random-seed，默认基准 236。每个 rng 夹具打印 node ID、基准种子与实际种子；
实际种子取 UTF-8 `"<base>:<nodeid>"` 的 SHA-256 前八字节，按大端无符号整数解释，
初始化局部 Random，不改全局状态。同基准与完整 node ID 可重放：

```sh
python -m pytest tests/test_bazi_chart.py::test_dayun_order --random-seed 236 -s
```

收集的随机关系案例用 base 至 base + 4，ID 含实际种子、出生与性别；改基准也会改变案例。
从仓根重放单例：

```sh
python -m pytest \
  'tests/integration/test_relationship_analysis.py::test_random_cases[seed=236-birth=2074-06-16T23:22:00-gender=male]' \
  --random-seed 236
```

### 离线数据生成

打包和安装后使用时只读取已提交数据，不重新生成。源码树及 sdist 含 HKO 原始输入，wheel 不含。
维护者可用 `python -m bazi.calendar.hko_data.encoder` 重建，仅下载原始输入时需要 requests；
天文表用 `python -m bazi.calendar.celestial_data.generator`，需要 celestial-calendar==0.6.1。
后者也生成每日均时差表，`--eot-only` 只生成 `equation_of_time.bin`，其输出逐字节稳定；这些工具不是运行时依赖。
在仓外目录生成候选 EOT 并比较，不覆盖随库表：

```sh
python -m bazi.calendar.celestial_data.generator \
  --eot-only \
  --output-dir ../bazi-calendar-check
cmp ../bazi-calendar-check/equation_of_time.bin \
  bazi/calendar/celestial_data/data/equation_of_time.bin
```

安装后缺表须重装分发包。

## 许可证

作者自有材料采用标准 [MIT License](https://github.com/0xf3cd/bazi/blob/main/LICENSE)。
[第三方材料说明](https://github.com/0xf3cd/bazi/blob/main/THIRD_PARTY_NOTICES.md) 另列历法数据、引文等权利范围，
不由作者的 MIT 授权重新许可；两份声明都随工件分发。
[发布说明](https://github.com/0xf3cd/bazi/blob/main/RELEASE_NOTES.md) 记录版本变更，
[发布流程](https://github.com/0xf3cd/bazi/blob/main/RELEASING.md) 说明手动发布步骤。
