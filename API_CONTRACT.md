# 公开接口契约

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
`DECLARED_MEMBERS` 包含方法、属性、类型别名和字段；继承关系另由 `BASES` 登记。

- 包的 `__all__` 不是公开 API 全集；`bazi.data_types` 等定义模块同样可直接导入。
- 领域枚举的中文与拉丁成员别名共用值；中文类型别名也保留，如 `天干` 与 `Tiangan`。
- 第三方模块在源码中的偶然导入不是本库提供的 API。普通模块的依赖导入不自动成为规范重导出。
- 下划线名字及 `_validation` 是包内约定，不承诺包外调用；共享接口的归属见
  [`tests/data/internal_interfaces.json`](tests/data/internal_interfaces.json)。
  `ContextResult` 的生成构造函数及 `dataclasses.replace` 参数 `_bazi` 是公开构造接口，读取使用 `bazi` 属性。
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

两值不扩四柱、`BaziData` 或柱位，不改 `school`、盘身份、旧文本输出，也不加入原有
五行、十神、神煞、关系或流运分析。读取它们不使任何解释条目的前提自动成立。

## 返回值、拷贝与相等性

### 共享与输入

- 查询结果和规则集合使用 `tuple`、`frozenset`、`frozendict` 等不可变结构；
  `frozendict` 只冻结映射本身，不深拷贝其中的值。具体接口的可变边界仍看其类型与说明。
- 命盘隔离传入的 `Bazi`，`chart.bazi` 每次返回独立深拷贝；不把 Python 属性只读等同于所有对象都深冻结。
- `Bazi` 按值比较；`BaziChart` 按对象身份比较。两个命盘的 `bazi` 值可以相等，命盘对象本身仍不相等。
  知识库按内容及顺序比较，`ContextResult` 按其值字段比较。
- `ContextResult` 是 frozen dataclass；构造参数 `_bazi: Bazi` 验证后深拷贝，公开 `bazi` 属性每次返回独立深拷贝。
  构造及 `replace` 使用 `_bazi`，不支持 `input_json`。相等／哈希使用 `Bazi` 的完整身份，包含性别、完整配置，
  地点盘另含精确瞬间、固定民用偏移及经度。修改输入或属性返回的副本不改变已有结果。
  显示直接读取领域值，不重新排盘；直接构造只检查结构自洽，不认证输入、观察、证据之间的事实一致性。
- 求值显式传入的 `KnowledgeBase` 被共享；未传时每次独立加载编辑源。已有结果不随源文件修改而变化。
- 每次访问 `chart.dayun`、`chart.liunian` 都获得新生成器。保存到变量的有限生成器会耗尽；
  流年生成器可无限延续，不要直接对它调用 `tuple`／`list`。`chart.xiaoyun` 是缓存元组，可重复遍历。

## 对象摘要、报错指路与文本展示

- `dir(bazi)` 列出 `__all__` 声明的全部子模块，以及 `chart_text`，包括尚未导入的按需子模块；`dir()` 本身不触发导入。
  `chart_text` 不进 `__all__`（v2.0.0 的显式导出清单保持不变），但同样按需导入。
- `Bazi`、`BaziChart`、`TransitChart`、`RelationshipAnalyzer`、`AtBirthAnalysis`、`TransitAnalysis` 的 `repr`
  是一行摘要：出生时刻、性别、四柱，配置不是默认值或是地点盘时再附加对应部分；后五个对象以所持命盘的摘要为主体。
  摘要大小与命盘数据无关，不计算流运或其他派生值。**它只服务交互探索与调试，格式不属于兼容承诺，
  不是记录格式，也不应被程序解析**。
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
  出生后没有大运起于历法支持范围内时，`transit_text` 与 `chart_text` 抛 `ValueError`，与 `BaziChart.xiaoyun` 一致；`basic_text` 不受影响。
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
这一支持窗口只适用于源码脚本，不改变上面的 Python API 契约。
裸调用打印顶层帮助并返回 0；随机命盘须显式选择 `chart`。旧平铺选项报错并指向三个任务的新写法。

| 旧写法（已移除） | 新写法 |
| --- | --- |
| `--seed 236` | `chart --seed 236` |
| `--query-knowledge --object tiangan.ding` | `knowledge --object tiangan.ding` |
| `--query-knowledge` | `knowledge --all` |
| `--match-context 判据ID …` | `match 判据ID …` |
| `--seed 236 --output-dir out --export-knowledge-base` | 先运行 `chart --seed 236 --output-dir out`，再运行 `knowledge --export-knowledge-base --output-dir out` |

表中参数均接在 `python run_interpreter.py` 后。最后一行是两条独立命令，分别检查各自的导出目标，
不提供跨命令的冲突预检或整体回滚；TXT 输出的知识源覆盖保护仍保留。

## 已删除的存取接口

当前源码不提供命盘／前提判别结果的保存恢复，也不导出知识快照。不保留兼容壳或替代记录格式。
已删除 `BaziJson`、`LocationTimeJson`、`BaziChart.json/from_json`、`LocationTime.json`、
`BaziSchool.from_json`、`TransitSet.json`、`ContextResult.input_json/export_json/from_json`、
`KnowledgeBase.export_json/from_json` 及整个 `bazi.record_migration` 模块。
源码脚本的 `--export-chart-json`、`--export-context-json`、`--export-knowledge-json` 也已删除；
普通运行与 `python -O` 均按未知选项拒绝，不创建输出文件。TXT、知识编辑源读取与领域查询保留。

旧结果需保留原件；要得到当前实现下的结论，使用原出生输入与完整配置重新排盘、求值。
本库不从旧记录猜补配置或重建历史结果。

## 知识编辑源与文本边界

`KnowledgeBase.load(Path | None)` 每次读取并校验当前编辑源；省略路径读取随库 `knowledge_data.json`。
已有内存对象不随文件编辑变化。编辑源须含 `schema_version` 及 `objects`、`contexts`、`sources`、`entries` 四份注册表；
版本只接受精确整数 2，拒绝 bool、浮点数、字符串、容器、旧版与未知版，不自动迁移。
重复键、字段差异、断引用、不合法状态及无法按 UTF-8 编码的孤立代理项均拒绝，不修复原文。
非整数版本的 `ValueError` 仅显示类型，不展开未知容器。类型错误抛 `TypeError`，值或引用错误抛 `ValueError`；
JSON 解析错误保留 `JSONDecodeError` 的原文与位置，实际解析递归失败转为 `ValueError`，不设固定深度上限。

字符串键在解析时检查 UTF-8，值使用显式栈遍历，不对整树重新编码。中文、非 BMP 字符、合法 JSON 代理对转义及字面的反斜杠文字保留。
知识和前提文字渲染同样检查 UTF-8，包括直接构造对象和展示参数；普通文字查询不因此收紧。
条目绑定摘要只识别所绑定的内容，不是保存格式或软件版本，也不认证条文真伪。
