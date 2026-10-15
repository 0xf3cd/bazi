# Bazi

> 排盘、五行、十神、纳音、刑冲破害、合会

面向中文用户的 Python 3.11+ 八字排盘库，提供四柱、流运、关系与解释知识查询。
运行时只用标准库及随库数据，无需联网或生成数据。
本文对应当前源码；已发布版本请参阅[对应版本的 README](https://github.com/0xf3cd/bazi/blob/v1.0.0/README.md)。

## 安装与快速排盘

下文示例使用当前源码的接口。在仓库根目录安装：

```sh
python -m pip install .
```

已发布的 1.0.0 可用 `python -m pip install bazi==1.0.0` 安装，但接口与当前源码不同；
升级说明见[发布说明](https://github.com/0xf3cd/bazi/blob/main/RELEASE_NOTES.md)。
从定义模块导入所需类型，下文每个 Python 示例均可独立运行。

```python
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.school import BaziConfig

config = BaziConfig.from_values(backend='celestial', precision='day')
chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male', config))
print(chart.json['pillars'])
print(chart.traits, chart.shishen, chart.hidden_tiangan)
print(chart.nayin, chart.shier_zhangsheng)
```

### 功能入口

| 用途 | 入口与说明 |
| --- | --- |
| 四柱与出生时间 | [`Bazi`](https://github.com/0xf3cd/bazi/blob/main/bazi/bazi.py) |
| 十神、藏干、纳音、大运与命盘 JSON | [`BaziChart`](https://github.com/0xf3cd/bazi/blob/main/bazi/bazi_chart.py) |
| 出生精度、流派与历法选择 | [`BaziConfig`、`BaziSchool`](https://github.com/0xf3cd/bazi/blob/main/bazi/school.py) |
| 按年、月、日期、时刻查流运 | [`TransitChart`](https://github.com/0xf3cd/bazi/blob/main/bazi/transit_chart.py) |
| 原局与流运的亲密关系、神煞 | [`RelationshipAnalyzer`](https://github.com/0xf3cd/bazi/blob/main/bazi/analyzer/relationship.py) |
| 知识查询、来源与导出 | [`KnowledgeBase`](https://github.com/0xf3cd/bazi/blob/main/bazi/knowledge.py) |
| 检查知识条目的前提 | [`evaluate_context`](https://github.com/0xf3cd/bazi/blob/main/bazi/context_matching.py) |

领域名称用拼音，枚举另有中文别名。JSON 保留中文领域值与配置，`py.typed` 提供内联类型标注。
直接查天干、地支关系可用 [`bazi.utils`](https://github.com/0xf3cd/bazi/tree/main/bazi/utils)，
历法换算入口见 [`bazi.calendar`](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/backend.py)。

## 配置与时间口径

默认使用 `CELESTIAL` 后端与 `DAY` 精度，以立春换年、十二节换月，晚子时 23:00 换日柱。
`DAY` 将整个交节日归新；`HOUR` 按两小时一个时辰、`MINUTE` 按分钟比较，相等归新。
三档的具体例子见 [`BaziPrecision`](https://github.com/0xf3cd/bazi/blob/main/bazi/school.py)。

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
print(chart.json['school'])
```

`BaziSchool` 选择换日、关系与神煞的读法，定义及出处见
[`school.py`](https://github.com/0xf3cd/bazi/blob/main/bazi/school.py) 和
[`rules.py`](https://github.com/0xf3cd/bazi/blob/main/bazi/rules.py)。
`dayun_year_rule` 只改变大运的年份标签，不改变物理起止时刻。

出生日期支持 1901-02-19 至 2099-12-31。`hko` 只提供日期级数据，只能用于 `DAY` 排盘；
`celestial` 与 `celestial-algo2` 提供节气时刻。后端差异见
[`CalendarBackend`](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/backend.py)，
历法换算及节查询的各自范围见
[HKO](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/hko_data_utils.py) 和
[天文后端](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/celestial_utils.py)。

命盘 JSON 可用 `BaziChart.from_json(chart.json)` 恢复；它重算并核对完整记录，只保证与当前版本一致。
旧记录的迁移见[发布说明](https://github.com/0xf3cd/bazi/blob/main/RELEASE_NOTES.md#unreleased)。
需要核对其他排盘器时，见[外部排盘对照](https://github.com/0xf3cd/bazi/blob/main/EXTERNAL_BASELINE.md)。

### 地点与真太阳时

不传经度时，输入须为不带时区的当地民用时刻。
启用真太阳时须给带时区的 `datetime`、东经为正且在 [-180, 180] 内的 `longitude`，
并选择 `CELESTIAL` 的 `HOUR` 或 `MINUTE` 精度。
输入用其他时区表示出生瞬间时，用 `civil_timezone` 指定出生地时区；否则采用输入时区。
时区、夏令时及历史偏移由调用方负责，本库不根据经度推断时区。

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
print(located.location_time)
```

出生日期窗口按真太阳日期限制；`solar_datetime` 只显示分钟，完整时间事实由 `location_time` 提供。
流运查询和大运边界仍采用不带时区的 UTC+08:00 标签，不是真太阳钟。
时间字段见 [`Bazi`](https://github.com/0xf3cd/bazi/blob/main/bazi/bazi.py)，
均时差计算与精度见[数据格式说明](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/celestial_data/SCHEMA.md#equation_of_timebin)。

## 运限与关系

`TransitChart` 查询小运、大运、流年、流月和流日；`RelationshipAnalyzer` 分析原局或所选流运的关系与神煞。

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

`at_year` 的整数是干支年标签，按所选年份视图解释大运；月、日期与时刻查询按物理边界。
`at_moment` 要求真实节时刻及 `HOUR` / `MINUTE` 原盘。不支持、出生前或各自范围外的查询返回 `None`。
`TransitSet.select` 要求指定种类全部存在，缺项时抛 `ValueError`；详细条件见
[`TransitChart`](https://github.com/0xf3cd/bazi/blob/main/bazi/transit_chart.py) 和
[`TransitSet`](https://github.com/0xf3cd/bazi/blob/main/bazi/transits.py)。

### 配偶星取法

`BaziSchool.peiou_xing_def` 选择配偶星（夫妻星）的取法：默认男命取正财干、女命取正官干；
`YINYANGGAN` 为《三命通会·論六親》读法（男取我克五行的阴干、女取克我五行的阳干，
书证直例仅甲乙两干，其余十六格按原书原则类推，单源）。地支侧两读一致，取主气为目标干之地支。
取法影响 `relationship_stars` 及以其为目标的婚恋判别，不改变排盘与其他关系计算。

```python
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.school import BaziConfig, BaziSchool, PeiouXingDef

chart = BaziChart(Bazi.create(datetime(2000, 1, 8, 12), 'male'))
assert str(chart.relationship_stars.tiangan) == '戊'
yinyang = BaziChart(Bazi.create(
  datetime(2000, 1, 8, 12),
  'male',
  BaziConfig(school=BaziSchool(peiou_xing_def=PeiouXingDef.YINYANGGAN)),
))
assert str(yinyang.relationship_stars.tiangan) == '己'
```

### 直接查地支关系

纯地支用 `discover`；需要区分柱位或查拱局时，用 `discover_ganzhis` 保留完整干支。
用 `definitions` 传入流派定义，`relations` 可限定干支发现的关系种类：

```python
from bazi.defines import Dizhi, DizhiRelation, Ganzhi
from bazi.rules import DizhiRules
from bazi.school import BaziSchool
from bazi.utils import dizhi_utils

print(dizhi_utils.discover([Dizhi.寅, Dizhi.卯, Dizhi.辰]))
school = BaziSchool(gong_def=DizhiRules.GongDef.SAME_STEM_WIDE)
gong = dizhi_utils.discover_ganzhis(
  [Ganzhi.from_str('甲寅'), Ganzhi.from_str('甲午')],
  definitions=school.relation_definitions,
  relations=(DizhiRelation.拱合, DizhiRelation.拱会),
)
assert gong.to_dizhi_discovery()[DizhiRelation.拱合] == (frozenset({Dizhi.寅, Dizhi.午}),)
```

拱局结果只含两个实支，不含所拱虚支。输入容器、跨组语义及结果顺序见
[`dizhi_utils`](https://github.com/0xf3cd/bazi/blob/main/bazi/utils/dizhi_utils.py)。

## 知识与前提匹配

`KnowledgeBase` 查询知识条目、展示原文与来源，也可导出 JSON 后重新加载。
默认只查 `output='default'` 条目；`include_reference_only=True` 同时查阅仅供参考的条目。

```python
from bazi.defines import Tiangan
from bazi.knowledge import KnowledgeBase, object_id

knowledge = KnowledgeBase.load()
identifier = object_id(Tiangan.丁)
entries = knowledge.query(
  object_id=identifier,
  include_reference_only=True,
)
for entry in entries:
  print(knowledge.render(entry, show_sources=True))
exported = knowledge.export_json(entries)
restored = KnowledgeBase.from_json(exported)
assert tuple(restored.entries.values()) == entries
```

`query` 可按对象、情境、主题及来源等条件取交集，结果不可变且保留语料顺序。
人工选择情境只用于检索，不判断命盘是否满足；`render` 也不求值前提或改变输出资格。
条目保留来源状态与限度，仅供参考的文字不表示适用于当前命盘。

编辑自定义知识时，修改随库 JSON 的副本，再用 `KnowledgeBase.load(Path(...))` 加载。
字段、过滤条件及来源说明见 [`knowledge.py`](https://github.com/0xf3cd/bazi/blob/main/bazi/knowledge.py)。

### 检查条目前提

`evaluate_context` 在显式选择的原局或原局加单流年中检查已注册判据。
已定义的两个官杀判据分别检查正官与七杀共现，以及共现且输入为女命；
它们关联的知识条目均仅供参考，前提满足不证明职场、法律或关系事件发生。

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

示例显式传入 `knowledge`，可在多次求值间复用。省略它时，每次求值重新加载默认来源。
文件更新只影响后续加载，已有知识库和结果保留原内容；要更新共享内容，重新加载并传入新对象。

`SATISFIED` / `NOT_SATISFIED` 表示完整前提的判别；所需流年缺失或不可查询、判据未定义时返回 `UNKNOWN`。
它不计算旺衰、喜忌、格局或有效制化。观察范围和自定义知识的匹配条件见
[`context_matching.py`](https://github.com/0xf3cd/bazi/blob/main/bazi/context_matching.py)。

两条婚恋结构判据走 `RelationshipProfile`：显式选择原局，或原局加一组按坐标查询、
显式选定种类的岁运。宫刑冲判据检查日柱地支作为具体参与者卷入刑或冲；透干判据检查
配偶星目标干至少一处明干出现（藏干只记事实）。证据按统一序号保存参与者与位置：
原局四柱为 0–3，所选岁运自 4 起；拱局分原局内部、原局×岁运、岁运内部三段，互不因另一侧
填实而失效。

```python
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import RelationshipProfile, TransitCoordinate, evaluate_context
from bazi.transits import TransitKind

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
result = evaluate_context(
  chart,
  criterion_id='editorial.spouse_palace_xingchong.v1',
  profile=RelationshipProfile(
    'natal_and_transits',
    TransitCoordinate('at_year', gz_year=2024),
    (TransitKind.DAYUN, TransitKind.LIUNIAN),
  ),
  include_reference_only=True,
)
print(result.render())
```

缺查询坐标、入口不可查询或所求种类部分缺失时返回 `UNKNOWN`，已取得岁运的证据照常保存。
`--match-context` 的 CLI 增补 `--transit-entry`／`--gz-month`／`--solar-date`／`--solar-moment`／
`--transit-kinds`；`--ganzhi-year` 同时是官杀流年坐标与 `at_year`／`at_month` 的年份坐标。
婚恋判据关联的条文只是条件参考，不表示结构已命中或完整前提已满足；男命语境条文对女命
不自动关联，静态知识查询不受限。

导出采用 `record_version=3`，保存查询坐标、请求与取得的岁运种类、结构证据与条件参考条目；
版本 1／2 记录须从原出生输入及配置重新求值。
`ContextResult.from_json` 只恢复记录，不重算或认证已存判别；它与命盘 JSON 的重算恢复不同。

## 源码脚本

以下脚本需先按[开发](#开发)安装依赖，再在仓库根目录运行，不作为安装后的命令行入口。
三者默认均生成随机命盘：

| 命令 | 输出 |
| --- | --- |
| `python run_demo.py` | 命盘、大运／小运／流年及命盘 JSON |
| `python run_relationship_analyzer.py` | 夫妻宫、配偶星、原局神煞及十年流年神煞 |
| `python run_interpreter.py` | 单盘静态说明，默认不导出文件 |

固定出生，显示参考文字及来源：

```sh
python run_interpreter.py \
  --birth-time "2000-01-01 12:00" \
  --gender male \
  --include-reference-only \
  --show-sources
```

查询知识并导出所选条目：

```sh
python run_interpreter.py \
  --query-knowledge \
  --object tiangan.ding \
  --include-reference-only \
  --export-knowledge-json output_data/knowledge.json
```

检查前提并导出记录：

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

随机示例用 `--seed` 重放；全部参数见 `python run_interpreter.py --help`。
命盘展示中的十神百分比只统计三个非日主明干与四支主气位置，不代表旺衰或力量。
JSON 导出拒绝覆盖知识源；用 `--output-dir` 导出命盘 TXT 时，会覆盖
`interpretation_examples/{序号}.txt` 路径上已有的同名文件，其他文件保留。

## 开发

在独立 Python 环境中安装开发依赖并运行完整检查：

```sh
python -m pip install -r Requirements.txt
python -m pip install celestial-calendar==0.6.1
python run_tests.py -a -v
```

完整检查包含所有测试及 100% 覆盖率、ruff、mypy、示例、`python -O` 输入检查和安装工件验证。
裸 `python run_tests.py` 不含 `slow` / `hkodata` 和可选任务，不能替代完整检查。
工件验证可能联网下载构建及类型工具；源码示例可能写入 `output_data/`。
更多选项见 `python run_tests.py --help`，代码约定见 [AGENTS.md](https://github.com/0xf3cd/bazi/blob/main/AGENTS.md)。

### 构建已验证的安装包

若需保留验证过的 sdist 及其重建 wheel：

```sh
python run_package_checks.py --output-dir ../bazi-tested
python -m pip install ../bazi-tested/bazi-1.0.0-py3-none-any.whl
```

输出目录须为空且在仓外。发布步骤见[发布流程](https://github.com/0xf3cd/bazi/blob/main/RELEASING.md)。
重建历法表见 [HKO 编码器](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/hko_data/encoder.py)、
[天文表生成器](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/celestial_data/generator.py)
及[数据格式](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/celestial_data/SCHEMA.md)。
安装后缺表应重装包，不运行生成器修补。

## 许可证

作者自有材料采用标准 [MIT License](https://github.com/0xf3cd/bazi/blob/main/LICENSE)。
[第三方材料说明](https://github.com/0xf3cd/bazi/blob/main/THIRD_PARTY_NOTICES.md) 另列历法数据、引文等权利范围，
不由作者的 MIT 授权重新许可；两份声明都随工件分发。
