# 公开接口与记录兼容契约

本库从定义模块导入类型与函数，没有安装 CLI，也不支持 `from bazi import Bazi`
（`import bazi; bazi.Bazi` 的 `AttributeError` 会指出该从哪个定义模块导入；`from bazi import Bazi` 由解释器报 `ImportError`，不带这条指路）。例如：

```python
from datetime import datetime
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Tiangan
from bazi.school import BaziConfig

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male', BaziConfig()))
assert chart.bazi.day_master in Tiangan
```

## 支持范围与导入路径

完整名称、类成员、字段、枚举别名、继承关系及规范定义路径登记在
[`tests/api_contract.py`](tests/api_contract.py)，供测试和参考文档共同使用。
`PUBLIC_NAMES` 登记定义模块的自有名称和既有包入口；`REEXPORTS`、`ALIASES` 区分重导出与别名。
`DECLARED_MEMBERS` 包含方法、属性、类型别名和字段；继承关系另由 `BASES` 登记，
公开命盘记录从私有基类继承的字段也在清单中，不因基类名带下划线而遗漏。

- 包的 `__all__` 不是公开 API 全集；`bazi.data_types` 等定义模块同样可直接导入。
- 领域枚举的中文与拉丁成员别名共用值；中文类型别名也保留，如 `天干` 与 `Tiangan`。
- 第三方模块在源码中的偶然导入不是本库提供的 API。普通模块的依赖导入不自动成为规范重导出。
- 下划线名字及 `_validation` 是包内约定，不承诺包外调用；共享接口的归属见
  [`tests/data/internal_interfaces.json`](tests/data/internal_interfaces.json)。
- `STATIC_MODULES` 单独标记离线编码／生成工具与导入即读取数据表的后端实现。
  离线工具按源码入口查阅，不是安装 CLI；检查清单不执行下载、生成或数据表加载。
- 清单不改变现有导入和 wildcard 行为；运行时签名和类型以定义模块为准。

### 字符串输入不等于枚举别名

`Bazi.create` 的性别字符串只接受 `男`、`女`、`male`、`female`（拉丁大小写不敏感），
也可直接传 `BaziGender`。枚举中的 `乾`、`坤`、`阳`、`阴`、`YANG`、`YIN` 不是性别字符串入口。

`BaziConfig` 构造函数接收声明类型；需要字符串解析时使用 `BaziConfig.from_values`。
精度支持 `分`／`分钟`／`时`／`小时`／`天`／`日` 和
`m`／`min`／`minute`／`h`／`hour`／`d`／`day`，拉丁大小写不敏感。
后端与大运年份规则分别由 `CalendarBackend.from_str`、`DayunYearRule.from_str` 解释成员名或值；
流派档案仍传 `BaziSchool`，不接受字符串。不统一这些既有输入域。

## 关系与附加查询

### 六甲旬空

`shensha_utils.xunkong(ganzhi)` 返回该旬二支冻结集，`kongwang(anchor_ganzhi, target_dizhi)` 返回
目标支是否命中。错误外层或内部干支字段类型抛 `TypeError`，阴阳不配锚抛 `ValueError`，在 `python -O`
下同样检查；不改变 `Ganzhi` 自身的构造域。目标不附加天干、纳音或冲合条件。

`BaziSchool.kongwang_anchor` 尾部追加，默认 `Anchor.DAY`，支持 `YEAR`、`YEAR_AND_DAY`。
`AtBirthAnalysis.kongwang` 与 `TransitAnalysis.kongwang(transits)` 返回 `tuple[KongwangResult, ...]`，
逐锚记录 `anchor`（`year`／`day`）、`ganzhi`、由锚计算的 `xunkong` 和 `hits`。
`KongwangHit` 的 `origin='natal'` 时有 `pillar`、无 `kind`，`origin='transit'` 时相反；`ganzhi` 保留完整目标。
无命中也返回该锚二支，双锚同值与重复目标位置不合并。原局排除锚自身柱，流运只从本命锚单向查询。
详情命中投影为地支集合，等于 `shensha['kongwang']`。不删除支、不改其他关系，不实现解释性取消或吉凶判断。

### 胎元与命宫附加查询

`chart.taiyuan` 与 `chart.minggong` 是无参缓存属性，返回不可变的 `Ganzhi`，只在首次访问时计算。
计算口径和可运行示例见[集成指南](docs/guides/integration.md#四柱之外胎元与命宫)；字段说明以
[`BaziChart.taiyuan`](bazi/bazi_chart.py)／`minggong` 的 docstring 为准。时支固定取本盘时柱，
DAY 也保留输入小时，地点盘取真太阳钟，换日设置（`day_rollover`）不改变时支。

中气按本盘出生精度相等归新：DAY 比日期，HOUR 比完整日期中的时辰起点，MINUTE 比分钟起点；
地点盘先把边界换到与出生相同的真太阳钟。HKO 仍只支持 DAY，不把零点占位视作真实时刻。
时间政策是本库执行口径，不冒称古籍规定；300 日胎元和其他命宫月界仅存知识候选，未编码。

纯函数从 `bazi.utils.bazi_utils` 导入：`taiyuan(month_pillar)` 先检查外层 `Ganzhi`，再检查
`tiangan`／`dizhi` 字段类型，错型立即抛 `TypeError`；通过后检查是否属于合法六十甲子，
阴阳不配的组合抛 `ValueError`。`minggong(year_tiangan, month_dizhi, hour_dizhi)` 逐参接收
`Tiangan`、已调整的有效命宫月支 `Dizhi`、本盘时支 `Dizhi`，非相应枚举抛 `TypeError`。
普通运行与 `python -O` 下的校验行为相同；`Ganzhi` 构造器本身仍接受全部 10×12 个干支组合。

两值不扩四柱、`BaziData` 或柱位，不改 `school`、盘身份、JSON、旧文本输出，也不加入原有
五行、十神、神煞、关系或流运分析。读取它们不使任何解释条目的前提自动成立。

## 返回值、拷贝与相等性

### 共享与记录

- 查询结果和规则集合使用 `tuple`、`frozenset`、`frozendict` 等不可变结构；
  `frozendict` 只冻结映射本身，不深拷贝其中的值。具体接口的可变边界仍看其类型与说明。
- `BaziChart.json` 是独立的可变 JSON 字典，修改它不修改命盘。命盘隔离传入的 `Bazi`，
  `chart.bazi` 也按其既有防御性拷贝约定返回；不把 Python 属性只读等同于所有对象都深冻结。
- `Bazi` 按值比较；`BaziChart` 按对象身份比较。恢复后的两个命盘可以 `json` 和 `bazi` 值相等，
  但命盘对象本身不相等。知识库按内容及顺序比较，前提判别记录 `ContextResult` 按其值字段比较。
- 每次访问 `chart.dayun`、`chart.liunian` 都获得新生成器。保存到变量的有限生成器会耗尽；
  流年生成器可无限延续，不要直接对它调用 `tuple`／`list`。`chart.xiaoyun` 是缓存元组，可重复遍历。

## 对象摘要、报错指路与文本展示

- `dir(bazi)` 列出 `__all__` 声明的全部子模块，以及 `chart_text` 和 `record_migration`，包括尚未导入的按需子模块；`dir()` 本身不触发导入。
  后两者不进 `__all__`（v2.0.0 的显式导出清单保持不变），但同样按需导入。
- `Bazi`、`BaziChart`、`TransitChart`、`RelationshipAnalyzer`、`AtBirthAnalysis`、`TransitAnalysis` 的 `repr`
  是一行摘要：出生时刻、性别、四柱，配置不是默认值或是地点盘时再附加对应部分；后五个对象以所持命盘的摘要为主体。
  摘要大小与命盘数据无关，不计算流运或其他派生值。**它只服务交互探索与调试，格式不属于兼容承诺，
  不是记录格式，也不应被程序解析**；保存与交换用 `BaziChart.json`，由测试钉住当前格式只为防止意外改动。
- 接收命盘的入口（`TransitChart`、`DayunDatabase`、`TransitDatabase`、三个分析类、`spouse_evidence`、
  `evaluate_context`、`bazi.chart_text` 的函数）在收到非 `BaziChart` 时立即抛 `TypeError`。三个分析类原先不检查类型，
  传入 `Bazi` 等对象会推迟到首次访问才抛 `AttributeError`；`DayunDatabase`、`TransitDatabase` 原先在构造时就抛
  `AttributeError`。现在统一为构造时的 `TypeError`，只依赖鸭子类型的调用方须传真正的 `BaziChart`。
- 类型错误消息保持 `Expected X, got <type>` 开头，对常见误用在其后以分号追加指路，如
  `Expected BaziChart, got <class 'bazi.bazi.Bazi'>; wrap it with BaziChart(bazi)`。
  异常类型与开头不变；要判断错误种类，匹配开头，不要匹配全文。
- `bazi.chart_text` 把命盘排成纯文本，不写文件，不依赖终端着色库，固定输入的输出可重放：
  `basic_text`（日元、出生时刻，四柱及其十神、阴阳五行、藏干、纳音、十二长生；地点盘另列民用、真太阳与节气表出生时刻）、`transit_text`（节、交运、大运、小运、流年；
  流年无限延续，由 `dayun_count`、`liunian_count` 限定，默认 10 与 100）、`chart_text`（两者相接）。
  出生后没有大运起于历法支持范围内时，`transit_text` 与 `chart_text` 抛 `ValueError`，与 `BaziChart.xiaoyun`、`json` 一致；`basic_text` 不受影响。
  `TextStyle` 的两个钩子返回值原样放进文本，不做检查，默认原样输出；版式由调用方负责。排版随版本调整时在发布说明中说明。

## 名称、关键词与过滤值发现

`KnowledgeBase.find_objects(name)` 按非空名称精确匹配，重名全部返回，顺序与对象注册顺序一致。
名称无匹配返回 `()`；不把中文名称当成唯一 ID，不做模糊匹配或大小写转换。
空或全空白名称抛 `ValueError`，错型抛 `TypeError`；有效名称的两侧空白不会被剥除。

`search(keyword, ...)` 先应用 `query` 的七维交集与参考条目政策，再作 Unicode `casefold` 字面子串匹配。
检索字段为条目正文、前提、署名、主题、口径、例外、限度及角色对象名称；
不搜对象／条目 ID、来源全文或情境标签，不解释正则，也不判断命盘适用性。
空或全空白关键词抛 `ValueError`，错型抛 `TypeError`；有效关键词的两侧空白不会被剥除。
结果保持语料顺序，默认仍排除仅供参考的条目。来源全文可直接查看 `sources`，关联条目用 `query(source_id=...)`。

`filter_values(dimension)` 给出七维合法值全集，按 Unicode 字符串序排列。
维度为 `object_id`、`context_id`、`source_id`、`topic`、`viewpoint`、`applicability`、`time_scope`，
不包含布尔选项 `include_reference_only`。未知维度抛 `ValueError`。
目录包括仅参考条目独有值、未引用的注册对象／来源／情境及其时间范围；空库的 applicability 仍有三个合法值。
合法值不保证默认输出有命中；`query` 与该目录共用合法值定义。

查询示例见[独立知识库指南](docs/guides/knowledge.md#按名称或-id-找对象)；完整签名与字段说明由定义模块的 API 参考生成。

## 判据目录

`context_matching.criteria()` 返回 `frozendict[str, CriterionInfo]`，
`criterion(id)` 返回单项；未知 ID 抛 `ValueError`，错型抛 `TypeError`。
两者不加载知识库、不创建命盘，也不执行判别。目录值冻结，直接构造 `CriterionInfo` 只校验值的形状；
需要已注册定义时应使用查询入口，不把自填说明当成程序认证。

绑定识别会核对条目及其引用的对象、情境、来源记录的内容摘要（SHA-256）是否符合默认约定；
它不认证条文真伪或现实适用性。

| 目录信息 | 含义 |
|---|---|
| `criterion_id`、`definition`、`observation_keys` | 稳定标识、现有判据定义及实际观察键，不包含用于绑定识别的内部内容摘要。 |
| `profile_type`、`profile_kind`、`scopes` | 需要的 profile 类型与合法范围，没有隐式范围默认值。 |
| `required_inputs`、`optional_inputs`、`scope_inputs` | 求值入口的必填／可选参数及各范围取得完整观察所需的额外 profile 字段。 |
| `transit_entries`、`transit_kinds` | 关系 profile 的坐标入口、必填坐标字段和结构上可支持的种类上限；不保证某盘实际可取得。ContextProfile 不接 TransitCoordinate。 |
| `unknown_conditions` | 缺所需年份／坐标或流运不可用等事实判别 UNKNOWN 条件；范围完整性先于性别门槛与事实。关系流运范围的 `kinds=()` 在构造时抛 `ValueError`，不产生 UNKNOWN。 |
| `entry_role`、`binding_effect` | `premise` 判关联条目的完整显式前提；`condition` 只判局部事实，不认定条目全文前提已成立。 |
| `required_gender`、`claim_genders` | 分别限制判据和关联条目的性别；具体效果见下文。 |
| `claim_ids` | 默认语料的条目约定；自定义库不保证有这些条目，同 ID 也不能认证语义相同。 |

只有 `editorial.guansha_coexistence_female.v1` 的 `required_gender` 为女命；范围完整时，
男命得到 `NOT_SATISFIED/female_gate_false`。普通官杀并见判据没有此门槛，两者都保留 `female` 观察键。
只向男命返回的两条婚恋条目由 `claim_genders` 限制：女命不返回这些关联条目，不改变事实判别。

绑定未识别不改变 `CriterionResult`。
`binding_effect='entry_unknown'` 表示 premise 条目的
`EntryMatch` 可为 `UNKNOWN/binding_unrecognized`；`'related_unrecognized'` 表示 condition 条目的
`RelatedEntry.recognized=False`。参考条目仍须显式选择，判据前提满足也不会授予默认输出资格。

目录使用示例见[知识库指南](docs/guides/knowledge.md#不建命盘浏览判据目录)。本节保留绑定识别、范围和条目关联的合同，不重复维护调用示例。

## 源码脚本

发现接口与判据目录通过 Python 调用。源码脚本 `run_interpreter.py` 不随 wheel 安装，
它的 `knowledge` 与 `match` 任务提供同样的目录查阅：`knowledge --list-values topic` 对应 `filter_values('topic')`，
`match` 与 `match 判据ID` 对应 `criteria()` 与 `criterion(id)`；不提供名称精确匹配和关键词检索参数。
本源码脚本的旧平铺调用在 v2.2.0 保留并提示迁移，**v2.3.0 起移除**。
这一支持窗口只适用于源码脚本，不改变上面的 Python API 与记录兼容契约。
裸调用打印顶层帮助并返回 0；随机命盘须显式选择 `chart`。旧平铺选项报错并指向三个任务的新写法。

| 旧写法（已移除） | 新写法 |
| --- | --- |
| `--seed 236` | `chart --seed 236` |
| `--query-knowledge --object tiangan.ding` | `knowledge --object tiangan.ding` |
| `--query-knowledge` | `knowledge --all` |
| `--match-context 判据ID …` | `match 判据ID …` |
| `--seed 236 --output-dir out --export-knowledge-base` | 先运行 `chart --seed 236 --output-dir out`，再运行 `knowledge --export-knowledge-base --output-dir out` |

表中参数均接在 `python run_interpreter.py` 后。最后一行是两条独立命令，分别检查各自的导出目标，
不提供跨命令的冲突预检或整体回滚；各任务的 JSON／TXT 输出冲突与知识源覆盖保护仍保留。

## 三类 JSON 分别保存与恢复

| 记录 | 输出／输入 | 版本与恢复含义 |
|---|---|---|
| 命盘 | `BaziChart.json` 输出字典；`BaziChart.from_json` 接收映射 | `schema_version=1`。按记录中的输入、配置与当前实现重建，再逐项核对派生字段；只保证与当前版本一致。 |
| 知识库 | `KnowledgeBase.export_json` 输出 JSON 文本；`from_json` 接收文本 | `schema_version=2`。恢复语料并校验结构、引用和各状态，不计算命盘前提。 |
| 前提判别记录 | `ContextResult.export_json` 输出 JSON 文本；`from_json` 接收文本 | `record_version=5`，内嵌知识 schema 2。恢复记录并校验结构和值类型，不重新判别，不认证输入、观察、证据与绑定之间的事实一致性。 |

命盘映射严格区分默认盘与地点盘。缺键、多键、不支持的值、非规范拼写及重算不一致会拒绝；
类型错误抛 `TypeError`，字段／值／一致性错误抛 `ValueError`。同时违反多个约束时不保证报错顺序。
格式版本不是软件版本。需要长期保存生成软件版本时，写在调用方的外层记录中，不给命盘映射加自定义键。
普通读取只接受上表格式，不静默迁移。缺版本、旧版、未知版与不兼容结构均拒绝，并保留具体原因和处理指引；
指引不表示损坏的记录一定能修复。bool、浮点数或字符串不能冒充整数版本。

以下三段各自独立运行，文件由调用方管理。

### 命盘：文本先解析成映射

```python
import json
from datetime import datetime
from pathlib import Path
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
path = Path('chart.json')
path.write_text(json.dumps(chart.json, ensure_ascii=False), encoding='utf-8')
restored = BaziChart.from_json(json.loads(path.read_text(encoding='utf-8')))
assert restored.json == chart.json
assert restored.bazi == chart.bazi
assert restored != chart
```

### 知识库：直接保存导出的文本

```python
from pathlib import Path
from bazi.knowledge import KnowledgeBase

knowledge = KnowledgeBase.load()
path = Path('knowledge.json')
path.write_text(knowledge.export_json(), encoding='utf-8')
restored = KnowledgeBase.from_json(path.read_text(encoding='utf-8'))
assert restored == knowledge
```

知识 JSON 拒绝重复键、字段差异、不支持的版本、断引用及不合法的条目状态。
导出默认保留全部条目，包括仅供参考的条目；显式选择条目时仍保留全部对象、情境与来源注册表。
`load` 每次重新读取文件；已有知识快照不随文件编辑而变化。

### 前提判别记录：恢复不等于重新求值

```python
from datetime import datetime
from pathlib import Path
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextProfile, ContextResult, evaluate_context

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
result = evaluate_context(
  chart,
  criterion_id='editorial.guansha_coexistence.v1',
  profile=ContextProfile('natal'),
  include_reference_only=True,
)
path = Path('context.json')
path.write_text(result.export_json(), encoding='utf-8')
restored = ContextResult.from_json(path.read_text(encoding='utf-8'))
assert restored == result
```

前提判别记录只接受版本 5，旧版本或错误类型的版本值会拒绝。恢复仍检查 profile 类型、坐标结构、
字段和值域等约束；能恢复不代表判别真实，也不等于绑定重新识别。
需要当前规则下的结论时，应使用原输入与配置重新构造命盘并调用 `evaluate_context`，
不要只改 `record_version` 冒充迁移。知识库的 `schema_version` 与前提判别记录的 `record_version` 也不能互换。

### 主动迁移：生成新记录，保留原件

从 `bazi.record_migration` 导入三个入口；它们不写文件，也不由普通读取自动调用：

| 入口 | 首批支持的旧源 | 目标与不做什么 |
| --- | --- | --- |
| `migrate_chart_json(映射)` | 完整无版本命盘，包括默认盘、地点盘 | schema 1；仍按当前实现重建核对，不改变输入、配置或派生值 |
| `migrate_knowledge_json(文本)` | 合法知识 schema 1 | schema 2；保留原知识快照，不换成当前默认语料 |
| `migrate_context_json(文本)` | 完整 record 4，内嵌知识必须是 schema 1 | record 5／schema 2；保留原判别、观察、证据、绑定和输入拼写，不重新求值 |

已有目标格式也可调用：校验后返回新结果，`changes` 为空。混版、未知版本、record 1–3、损坏字段、
失效判据定义或不支持的文本拒绝，类型错误为 `TypeError`，结构／值／版本错误为 `ValueError`。
命盘迁移的 `json_text` 仍须先 `json.loads` 才能交给命盘读取入口。JSON 空白和字段排列可以规范化，字段值不因格式迁移改变。
此前合法的前提配置别名、school 扩展键及观察键继续保留，不借迁移统一它们。

返回的 `MigrationResult` 是 frozen dataclass，包含 `json_text`、`source_version`、`target_version`、
`tool_version` 与不可变的 `changes` 元组。每个 `MigrationChange` 说明字段路径 `path`、转换前后的
`before`／`after` 及依据 `reason`；无版本命盘的来源和原缺字段均以 `None` 表示。
`tool_version` 取自分发元数据：安装清单（`RECORD`）须列出当前迁移模块，记录的路径及 SHA-256 须与正在使用的文件相符才报告，
无法核定（包括没有可核哈希的 editable 安装）为 `None`。它不认证元数据真伪或历史执行，不代替原记录的生成软件版本。

调用方读取源文件后主动迁移，再独占创建新文件。下面先生成一份当前格式，示范可独立运行的文件管理；
实际处理旧命盘时改用已有源文件，迁移调用不变。当前格式只校验，变更清单为空：

```python
import json
from datetime import datetime
from pathlib import Path
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.record_migration import migrate_chart_json

source = Path('chart.json')
with source.open('x', encoding='utf-8') as original:
  json.dump(BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male')).json, original, ensure_ascii=False)
original_bytes = source.read_bytes()
result = migrate_chart_json(json.loads(source.read_text(encoding='utf-8')))
with Path('chart-schema1.json').open('x', encoding='utf-8') as target:
  target.write(result.json_text)
assert source.read_bytes() == original_bytes
for change in result.changes:
  print(change.path, change.before, change.after, change.reason)
```

`'x'` 在目标已存在时拒绝，避免覆盖原件或已有结果。迁移不会冻结旧算法，也不把记录恢复变成重新求值；
需要当前结论时仍显式重建并调用 `evaluate_context`，另存新结果。

新增 `kongwang_anchor` 与其他流派字段一起进入命盘身份及 JSON。旧命盘与旧前提记录缺此字段时拒绝，
不自动补 `DAY`；以原输入、完整原配置及显式选择的新锚重建当前盘。前提记录须重新求值后另存，
不给旧观察补键或改 `record_version` 冒充重新求值。迁移函数也不猜这个缺项。

### 文本边界与升版责任

JSON 文本拒绝重复键和孤立代理项，字符串键和值均检查，包括内嵌知识、观察键和 input 扩展字段。
中文、非 BMP 字符、合法 JSON 代理对转义及字面的反斜杠文字可往返，不替换或修复原文。
导入用公开导出的同一条带缩进编码检查 UTF-8 保存能力；导出与相关知识／前提文字渲染也检查输出，
包括直接构造对象和渲染展示参数。普通文字查询不因此收紧。解析或编码超出运行环境递归能力时抛 `ValueError`，
不承诺固定层数。源码 CLI 使用现有参数错误通道退出；序列化校验失败不打开或截断目标，不承诺一般 I/O 失败整体回滚。

本次是记录兼容变化：旧完整记录须先主动迁移；此前可导入但不能保存的文本会提前拒绝，普通运行和 `-O` 一致。
格式版本覆盖字段、嵌套配置、profile／坐标、判据 ID／definition、观察与证据结构以及文本接受规则。
改变这些恢复要求时应评估格式升版；知识语料勘误不自动等于格式升版。条目绑定摘要识别所绑定的内容，
不是格式号或软件版本，不能替代它们。
