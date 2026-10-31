# 发布说明

## bazi 2.5.0

本版提供安装后的 `bazi` 命令，知识关联改用参考 ID 与默认展示布尔值，流运查询统一由 `TransitChart` 承接。
升级前请核对下方的知识结构、流运入口和脚本迁移；移除的接口不保留兼容入口，命理规则与默认取法不变。

### 知识关联与默认展示

- `ContextResult.reference_ids: tuple[str, ...]` 替代 `references` 和条目包装类型。用 `knowledge.entry(id)` 查文字，用判据目录的 `entry_role` 区分完整前提与条件参考；判别状态只从 `criterion` 读取。删除 `MatchReason`、`EntryMatch`、`RelatedEntry`、`PremiseMatches`、`ConditionReferences` 与 `CriterionInfo.binding_effect`，不留兼容入口。
- 参考按稳定 ID 关联，不再比较条目及来源的内容摘要。正常求值按声明序返回现有且通过默认展示／性别筛选的条目 ID；编辑正文、引文或来源说明不会制造 UNKNOWN。自定义库负责保持同 ID 的领域含义。
- `KnowledgeEntry.show_by_default: bool` 替代 `output`／`OutputPolicy`，`include_reference_only` 不变。编辑源升为整数 schema 3，条目键改为 `show_by_default`，值为 JSON boolean；旧 schema 1／2 直接拒绝，不自动迁移。312 条知识及 19 条默认展示、默认展示准入和命理规则不变。
- 构造、`replace`、`asdict` 及位置式类模式须同步迁移；直接构造的参考 ID 保留顺序和重复，具体改法如下。

### 知识结构迁移

| 原接口或编辑源 | 当前做法 |
| --- | --- |
| `KnowledgeEntry.output='default'`／`'reference_only'` | `show_by_default=True`／`False`，只接受确切 bool |
| schema 1／2、条目的 `output` 键 | 自行改为精确整数 `schema_version=3` 和 JSON boolean `show_by_default`，再加载校验 |
| `result.references` 及条目包装类型 | `result.reference_ids`，用 `result.knowledge.entry(id)` 取条目 |
| `CriterionInfo.binding_effect`、包装层状态与原因 | 用 `criterion(result.criterion.criterion_id).entry_role` 区分参考语义，状态和原因只从 `result.criterion` 读取 |

旧 schema、旧键、遗漏或额外键均拒绝，不提供运行时迁移层。`show_by_default` 的 `0`、`1`、字符串和 None
会抛 `TypeError`；默认展示只控制查询，不认证知识正确或适用于当前命盘。`include_reference_only` 及默认展示准入条件不变。

显式构造 `ContextResult` 与 `dataclasses.replace` 改传 `reference_ids=`，`asdict` 返回该 ID 元组。
直接构造保留顺序与重复，检查 str 类型、非空 ID 和知识库中的存在性，不强制 ID 属于判据 claims；
正常求值仍按判据声明序与筛选规则返回 ID。
`ContextResult` 第四位置字段由参考包装改为 ID 元组，`KnowledgeEntry` 倒数第二字段由策略改为 bool。
**旧位置式类模式可能静默失配或读取不同含义**，构造调用、解构和模式须一起修改，不能只改关键字。

### 流运查询入口

- `DayunDatabase`、`TransitDatabase` 改为包内实现，不再支持从 `bazi.transits` 导入；`bazi.transit_chart.TransitDatabase` 也不再可用，不保留兼容别名。调用方改用 `TransitChart(chart).at_year(year)`，再从返回的 `TransitSet` 读取 `xiaoyun` 或 `dayun`，没有相应流运时字段为 `None`；早于出生干支年的查询则返回 `None`。
- 需要每步大运的年份标签与物理起止时刻时，遍历 `chart.dayun`，读取 `DayunTuple` 的 `ganzhi_year`、`start_moment`、`end_moment`；`TransitSet.dayun` 只给出干支。
- 按干支月、公历日期或时刻查询，分别用 `at_month(year, Dizhi成员)`、`at_date(date)`、`at_moment(datetime)`。四个入口的范围、缺项、异常条件，以及大运年份标签与物理交运边界的读法不变。`TransitKind`、`TransitSet` 和 `BaziChart.random` 保留。

### 安装版命令与脚本迁移

安装包新增唯一的 `bazi` 命令，运行时仍只用标准库与随包数据。安装后无需进入源码目录，也不必另装 colorama；源码调用改为：

| 原入口 | 当前命令 |
| --- | --- |
| `python run_demo.py --seed 236` | `bazi demo --seed 236` |
| `python run_relationship_analyzer.py --seed 236` | `bazi relationship --seed 236` |
| `python run_interpreter.py chart …` | `bazi chart …` |
| `python run_interpreter.py knowledge …` | `bazi knowledge …` |
| `python run_interpreter.py match …` | `bazi match …` |

- 三个旧脚本删除，不留兼容壳。保留完整演示、终端颜色、随机种子、地点输入、知识与判据查询、TXT 和知识源覆盖保护；不改变领域计算或规则。
- 默认知识 TXT 导出目录从源码所在目录改为**调用时当前目录**下的 `output_data/`。`chart` 仍须显式给 `--output-dir` 才导出，不会默认写文件。裸调用只显示帮助；未知任务／选项及已删除的三个 JSON 导出参数继续以退出码 2 拒绝，普通与优化模式相同。
- `run_tests.py` 删除独立的 `-d`／`--demo`、`-i`／`--interpreter` 任务；CLI 全部计入库覆盖率，并由专项测试和 direct／rebuilt wheel 的实际安装命令验证。

从 v2.2.0 及更早的平铺参数迁移时，先选任务：`--seed 236` 改为 `bazi chart --seed 236`，
`--query-knowledge` 改为 `bazi knowledge --all`，`--query-knowledge --object tiangan.ding` 改为
`bazi knowledge --object tiangan.ding`，`--match-context 判据ID …` 改为 `bazi match 判据ID …`。
同时展示命盘与导出知识须分成 `bazi chart …`、`bazi knowledge --export-knowledge-base …` 两条命令，
各自检查输出目标；一条失败不撤销另一条已写出的文件。

### 文档与阅读入口

版本历史和迁移集中在本页，Pages 构建时直接读取同一份正本。README 与接口契约聚焦当前用法，
快速开始补齐流年查询、有限流年与前提匹配的独立示例；开发和受测工件保留步骤分别归贡献指南与发布流程。

## bazi 2.4.0

本版删除公开 JSON 存取与迁移接口，并调整位置、观察请求和分析结果的构造。升级前请保留原出生输入、完整配置和旧记录，核对下方“存取接口移除”和“结构接口迁移”两节。本节记录 v2.4.0 当时的接口；后续知识结构变化另见上方 v2.5.0。

### 兼容与调用调整

- 删除命盘／前提判别结果的公开 JSON 保存恢复、知识快照导出与恢复及 `record_migration` 模块，不保留兼容入口或替代保存格式。`BaziJson`、`LocationTimeJson`、`BaziSchool.from_json`、`TransitSet.json` 一并删除。请保留旧原件；需要当前结论时，用原出生输入与完整配置重新排盘、求值。
- `ContextResult` 的构造及 `replace` 使用 `_bazi` 参数，验证后保存 `Bazi` 输入的独立深拷贝；`bazi` 属性每次返回独立深拷贝。输入完整身份仍参与相等与哈希，原 `input_json` 字段删除。
- 知识库保留 `KnowledgeBase.load(path)`、完整引用校验和查询／渲染。JSON 只作当前编辑源，`schema_version` 只接受精确整数 2，不自动迁移旧版来源。
- 源码脚本删除 `--export-chart-json`、`--export-context-json`、`--export-knowledge-json`；保留 TXT、知识编辑源读取和源文件覆盖保护。
- 位置共享 `Zhu`／`柱`，明藏共享 `TianganLayer`／`天干层次`；空亡和配偶星出现改用 position，前提证据保留具体流年年份。文本柱位及明藏层改为中文值，如 `natal.月`、`藏干`。
  同名 anchor／layer 字段改为非 str 枚举，旧字符串比较、in 判断和关键字类模式可能静默不命中；须改用枚举成员，不能只迁移构造调用。
- 观察请求改为 NatalObservation、LiunianObservation、TransitObservation，岁运坐标改为年／月／日期／时刻四类；删除旧 profile 和通用坐标构造。CriterionResult、EntryMatch 的定义或状态改为派生属性，ContextResult 用 evidence／references 组合证据和两种参考；不保留旧字段兼容壳。构造、replace、asdict 与位置式类模式均须迁移，后者可能静默失配，详见下表。
  CriterionInfo 删除 profile_type／profile_kind，第三构造字段改为 analysis_kind；可接受的观察请求类从 observation_types 读取。
- 两个后端共用 `bazi.calendar.dates` 中定义的 `LunarYearInfo`，三个旧导入路径仍能取得同一个类型；字典／列表行为不变。包内月查询复用已有 `GanzhiYearMonth`，不改变便捷入口既有的输入检查或查询准入。

### 存取接口移除

删除 `BaziJson`、`LocationTimeJson`、`BaziChart.json/from_json`、`LocationTime.json`、
`BaziSchool.from_json`、`TransitSet.json`、`ContextResult.input_json/export_json/from_json`、
`KnowledgeBase.export_json/from_json` 及整个 `bazi.record_migration` 模块。
`--export-chart-json`、`--export-context-json`、`--export-knowledge-json` 也不再提供；
普通运行与 `python -O` 均按未知选项拒绝，不创建输出文件。TXT、知识编辑源读取与领域查询保留。

旧结果需保留原件。本库不从旧记录猜补配置或重建历史结果；要得到升级后实现的结论，
用原出生输入与完整配置重新排盘、求值。重新构造时，不传 `BaziSchool.kongwang_anchor`
会使用默认日柱 `Anchor.DAY`；需要 `YEAR` 或 `YEAR_AND_DAY` 时必须显式配置。
知识编辑源不是历史结果快照；v2.4.0 接受 schema 2，后续 schema 3 的迁移另见上方知识结构迁移。

### 结构接口迁移

以下旧新对照只描述 v2.3.0→v2.4.0；命理规则、默认流派、历法算法和时钟口径不变，不留旧构造器或兼容属性。

| 原调用或字段 | v2.4.0 调用或字段 |
| --- | --- |
| 原局英文柱位／`Pillar` | `bazi.defines.Zhu`，中文类别名 `柱`；按年、月、日、时排列 |
| 明藏层字符串 | `TianganLayer.明干`／`藏干`，中文类别名 `天干层次` |
| `KongwangHit`／`StarAppearance` 的 origin/pillar/kind | 合为 `position: Zhu \| TransitKind`；`StarAppearance(position, ganzhi, layer, stem)` 的 layer 为 TianganLayer |
| `ContextProfile`／`RelationshipProfile`、`profile=` | `NatalObservation`／`LiunianObservation`／`TransitObservation`、`observation=` |
| `TransitCoordinate(entry=..., ...)` | 明确构造 `YearCoordinate`／`MonthCoordinate`／`DateCoordinate`／`MomentCoordinate`；TransitCoordinate 只作联合类型 |
| `info.profile_kind`／第三构造字段 `profile_type` | `info.analysis_kind`，取 `'context'`／`'relationship'`；请求类元组从 `info.observation_types` 读取 |
| `info.profile_type` 的单个请求类 | `info.observation_types` 中的可接受请求类元组，不再直接当作一个类调用 |

`Zhu` 的成员为 `NIAN/YUE/RI/SHI` 与 `年/月/日/时`；TianganLayer 为 `MINGGAN/CANGGAN` 与 `明干/藏干`。
原局 `ChartOccurrence.index` 为 0–3，流年为 4；流年 position 使用保存具体 `ganzhi_year` 的 `LiunianPosition`。
关系组合用的 `bazi.utils.dizhi_utils.GanzhiOccurrence.index` 仍是调用方输入序列的位置，不限四柱。
`KongwangResult.anchor` 只接受年、日；多锚选择策略 `Anchor.YEAR_AND_DAY` 不是柱位。

`NatalObservation()` 供全部判据共用；`LiunianObservation(ganzhi_year=None)` 供原局加单流年，
`TransitObservation(kinds, coordinate=None)` 供婚恋结构岁运查询。ScopeName 按 natal、natal_and_liunian、natal_and_transits 排序。
年坐标使用 `YearCoordinate(ganzhi_year)`；月坐标使用 `MonthCoordinate(ganzhi_year, ganzhi_month)`，月为 `Dizhi`，
两者的年份均拒绝 bool 与 int 子类。日期使用 `DateCoordinate(solar_date)`，只接受确切的 date，不接 datetime 或 date 子类；
时刻使用 `MomentCoordinate(solar_moment)`，只接受确切、无时区的 datetime，保留微秒请求身份，求值按秒解释。
四类从 `context_matching` 导入，日期与时刻按东八区解释。
缺字段或多余字段抛 `TypeError`；畸形坐标、空／重复／不支持的种类立即失败，普通运行与 `-O` 一致。
缺坐标仍是合法观察请求，求值为 UNKNOWN。这些严格请求不改变便捷入口 `TransitChart.at_year/at_month`
的 `isinstance(year, int)` 检查；bool 和 int 子类在那里仍通过类型检查。

当版结果的构造字段如下，派生属性不进入构造、`fields`、`asdict` 或位置模式：

| 类型 | v2.4.0 构造字段 | 派生属性 |
| --- | --- | --- |
| `CriterionResult` | criterion_id、reason、observations | definition、status、scope_complete |
| `EntryMatch` | claim_id、reason | status |
| `ContextResult` | observation、criterion、evidence、references、_bazi、knowledge | bazi |
| `PremiseMatches`／`ConditionReferences` | entries | 无 |

`dataclasses.replace` 不能再传 status、definition、scope_complete；固定的 scope／entry 改为 ClassVar，
不进入构造、repr、fields、asdict、相等／hash 或位置模式。需要派生结论时显式读属性，不把 asdict 当作完整导出记录。
`ContextResult.evidence` 保存明藏干分类元组或 `RelationshipEvidence`，references 保存完整前提匹配或条件参考，
即使 entries 为空也保留两种包装。旧总结果字段 occurrences／relationship／entries／related 删除。
出生输入经 `_bazi` 构造参数验证并深拷，属性 `bazi` 每次返回新深拷；显式知识对象仍复用。
部分流运不可取得时保留已取得证据。scope_complete 由 reason 派生，不认证手填原因与观察、请求年份或证据一致；
实际求值由 `evaluate_context` 计算，直接构造仍校验婚恋范围与取得集合是否自洽。

字段顺序同时改变 `__match_args__`。旧关键字或参数数量通常抛 `TypeError`，但**旧位置式类模式可能静默不匹配，
或把新字段读成旧含义**：旧 `case CriterionResult(id, definition, status)` 会读取 criterion_id、reason、observations；
旧 `case CriterionInfo(_, _, profile_type)` 会把类别字符串绑定给 profile_type，不能再把它当请求类。
构造、解构与模式必须一起迁移。references 和 EntryMatch 等包装在后续版本还会变化，不要把此历史表当作当前接口清单。

同名的 anchor／layer 字段改为不继承 str 的枚举，旧字符串比较、`in` 和关键字类模式不会报错，却不再命中：

| 旧读取／模式 | v2.4.0 读取／模式 |
| --- | --- |
| `result.anchor == 'year'` | `result.anchor is Zhu.年` |
| `result.anchor in ('year', 'day')` | `result.anchor in (Zhu.年, Zhu.日)` |
| `appearance.layer == 'visible'` | `appearance.layer is TianganLayer.明干` |
| `occurrence.layer == 'hidden'` | `occurrence.layer is TianganLayer.藏干` |
| `case StarAppearance(layer='visible')` | `case StarAppearance(layer=TianganLayer.明干)` |

判断用枚举成员，打印 Zhu／TianganLayer 用 `str(value)`，TransitKind 用 `.value`；位置和明藏层显示因此成为 `natal.月`、`藏干`。
类型检查通过不证明旧字符串比较已迁移。钉版 mypy 对中文／拼音别名的 Literal 穷尽写法仍须覆盖两种拼写，
当前可运行例见[枚举字段的读取与穷尽分支](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md#枚举字段的读取与穷尽分支)。
目录年月字段改为 ganzhi_year／ganzhi_month，CLI flags 保持；错误消息使用完整字段名，边界错误仍退出 2。
`LunarYearInfo.__module__` 指向 calendar.dates，三个规范重导出仍是同一类型，不改变原字典／可变列表与独立副本行为。

### 输入、知识与来源

- 说明默认输入钟与东八区节气表的关系，区分当地钟时标签、北京时间转换和地点盘真太阳时；不改变排盘算法或默认时间口径。
- 前提文本区分原局与缺少流年年份的范围；性别错误消息列出合法输入，仍抛 `ValueError`，接受集合不变。
- 勘正红艳三格来源差异、天乙阳贵／阴贵的表值与用法边界，以及华盖、文昌和查法锚的引文定位；规则表、算法、锚点和默认不变。
- 知识来源用〔……〕区分不连续摘录，恢复所取刊页的句读；命宫中气来源据 NLC 刊页更新，并同步参考条目的引文与载体说明。条目引文的字面搜索随原字更新，不改变谱系、默认输出资格或绑定判据。

### 开发与发布

- NORMAL 暗合与通禄合共用同一组组合定义，两个公开关系名及查询结果键仍保留；其他暗合读法不合并，规则值和默认不变。
- 关系测试补充失败差异，发布结构测试按主题拆分，案例名说明被检查的行为；只整理测试，不改变库行为。
- 文档工具升级至 Sphinx 9.2.0，构建文档和完整开发检查需要 Python 3.13+。bazi 库仍支持 Python 3.11+，没有新增运行时依赖；Python 3.11／3.12 可用 `run_tests.py -a -v --runtime-only` 检查运行时。
- setuptools 升至 84.2.1，setup-python 升至 7.1.0，PyPI 发布 action 升至 1.14.3；两个 action 仍固定到提交 SHA。
- 发布工件附带实际构建与验证环境清单，并核对清单、源码和同次运行工件的对应关系。这不是依赖锁，不保证日后解析到相同环境或逐字节重建，见[发布流程](https://github.com/0xf3cd/bazi/blob/main/RELEASING.md#实际环境清单)。

## bazi 2.3.0

本版含旧记录与源码脚本调用的破坏性变更，升级前请保留原记录及出生输入，迁移条件见下文。

### 兼容与迁移

- `BaziSchool` 尾部新增 `kongwang_anchor`，默认 `Anchor.DAY`，也可选 `YEAR`、`YEAR_AND_DAY`。该字段进入命盘身份与 JSON。
- 缺少 `kongwang_anchor` 的旧命盘或前提判别记录拒绝恢复，不自动补默认值。须按原出生输入、完整配置及显式选择的新锚重建命盘；前提判别记录须重新求值后另存。没有自动迁移接口，不要只补字段或改版本号。
- 知识库的 `schema_version=1`、前提判别记录的 `record_version=4` 不变；版本值不变不表示缺字段的旧记录可恢复。
- 源码脚本 `run_interpreter.py` 移除 v2.2.0 保留的旧平铺写法，裸调用只打印帮助。原 `--seed 236` 改为 `chart --seed 236`，`--query-knowledge` 改为 `knowledge --all`；完整对照如下。这些变化不新增安装后的 CLI；更新 bazi 包不会更新本地源码脚本。

### 源码脚本的平铺参数

本表只适用于 v2.3.0 的源码脚本，参数均接在 `python run_interpreter.py` 之后。
迁往安装命令的后续变化见上方“安装版命令与脚本迁移”。

| 旧平铺写法（本版移除） | v2.3.0 子命令写法 |
| --- | --- |
| `--seed 236` | `chart --seed 236` |
| `--query-knowledge --object tiangan.ding` | `knowledge --object tiangan.ding` |
| `--query-knowledge` | `knowledge --all` |
| `--match-context 判据ID …` | `match 判据ID …` |
| `--seed 236 --output-dir out --export-knowledge-base` | 先运行 `chart --seed 236 --output-dir out`，再运行 `knowledge --export-knowledge-base --output-dir out` |

裸调用返回 0，不生成随机命盘；随机盘须显式选择 chart。旧平铺选项报错并指向三个任务的新写法。
表的最后一行是两条独立命令，各自检查导出目标，不提供跨命令冲突预检或整体回滚；
当版各任务的 JSON／TXT 输出冲突与知识源覆盖保护仍保留。

### 六甲旬空、胎元与命宫

- `shensha_utils.xunkong(ganzhi)` 返回所属旬的二支冻结集，`kongwang(anchor_ganzhi, target_dizhi)` 判断目标支是否命中。原局与流运分析新增旬空查询，按本命年柱、日柱或双锚保留命中柱位与来源；原局排除锚自身柱，流运从本命锚单向查询。旬空详情的命中地支集合与 `shensha['kongwang']` 一致，不删除地支、不取消其他关系，也不附带出空／填实或吉凶判断。
- `BaziChart.taiyuan`、`BaziChart.minggong` 为无参缓存属性，返回不可变 `Ganzhi`。胎元按月柱干顺移一、支顺移三，不推算实际受孕时刻；命宫按本盘精度处理中气进月，再配宫支与宫干。完整时间口径见 [接口契约](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md#胎元与命宫附加查询)。
- 胎元／命宫只作四柱外附加查询，不扩四柱、柱位、流派配置、命盘身份或 JSON，不改既有文本输出，也不加入原有关系与流运分析。三百日胎元及其他命宫月界读法仍未编码。

### 使用与开发文档

- README 与快速开始串起准备环境、填写输入、排盘、读结果及保存 UTF-8 TXT／JSON 的步骤；老用户有独立迁移入口，区分安装包与源码脚本。
- 新增计算规则、知识与出处的覆盖对账，以及国印两种读法的关联设计示例；不新增运行时关联查询接口，也不把设计示例升级为古籍见证。
- 文档工具升级至 Sphinx 9.1.0、MyST 5.1.0，构建文档与完整开发检查需要 Python 3.12+；bazi 库仍支持 Python 3.11+，已生成的 HTML 阅读不需要 Python。3.11 用 `run_tests.py -a -v --runtime-only`，不能代替完整文档门禁。
- ruff 升至 0.17.1，并按主题拆分部分复合测试、整理测试名；不改变原有测试保护的行为。docutils 仍为 0.22.4，不随类型桩升级到 0.23。

## bazi 2.2.0

### 交互探索与文本展示

- 新增公开模块 `bazi.chart_text`：`basic_text`、`transit_text`、`chart_text` 把命盘排成纯文本，不写文件，也不依赖终端着色库。`run_demo.py` 改用它，输出不变。
- `TextStyle` 的 `glyph`、`day_master_mark` 两个可选钩子供调用方加颜色或标记，默认原样输出。
- 流年无限延续，由 `liunian_count`（默认 100）限定；大运数由 `dayun_count`（默认 10）限定；小运有限，全部列出。
- `transit_text` 与 `chart_text` 在出生后没有大运起于历法支持范围内时抛 `ValueError`，与 `chart.xiaoyun` 一致；`basic_text` 不受影响。
- `Bazi`、`BaziChart`、`TransitChart`、`RelationshipAnalyzer`、`AtBirthAnalysis`、`TransitAnalysis` 有一行 `repr`，如 `Bazi(2000-01-01T12:00:00, male, 己卯 丙子 戊午 戊午)`：出生时刻、性别、四柱，经度或非默认配置存在时再附加。摘要大小与命盘数据无关，不触发流运计算；格式只服务交互探索，不属兼容承诺。
- `dir(bazi)` 列出按需导入的子模块（含 `chart_text`），不触发导入；八个常见入口类（`Bazi`、`BaziChart`、`TransitChart`、`RelationshipAnalyzer`、`AtBirthAnalysis`、`TransitAnalysis`、`BaziConfig`、`KnowledgeBase`）的属性访问，如 `bazi.Bazi`，会指出该从哪个定义模块导入。
- 接收命盘的入口收到错误对象时，错误消息保留 `Expected X, got Y` 的开头，其后追加指路，如 `build one with Bazi.create(birth_time, gender)`。

### 命令行

- 源码仓库里的 `run_interpreter.py` 改为三个任务：`chart` 展示命盘，不给出生信息就随机生成；`knowledge` 查询、校验、导出解释知识，不需要命盘；`match` 查看判据，或对给定命盘判别前提。参数都可选：只写 `knowledge` 给知识库概览，只写 `match` 列出全部判据，`match <判据ID>` 说明该判据需要的输入。
- `knowledge` 新增 `--all` 与 `--list-values 条件名`，`--export-knowledge-base` 归到这里。导出多了两道写前检查，不符合就报错：`--export-knowledge-json` 的目标不得落在 `--export-knowledge-base` 生成的文本文件上；文本导出不得写到知识库的编辑源（包内默认知识库或 `--knowledge-source`，含符号链接）。
- 旧的平铺写法这一版照常可用、输出不变，成功后在标准错误给出等价的新命令，本版无需改动调用；将来移除，计划见 #292。

### 兼容与行为变化

- 延续 2.1.0 的计算规则、默认值和记录格式；本版不要求迁移既有公开调用或重建记录。
- `DayunDatabase`、`TransitDatabase`、`AtBirthAnalysis`、`TransitAnalysis`、`RelationshipAnalyzer` 收到类型错误的对象时，现在一律在构造时抛 `TypeError`。原来 `DayunDatabase`、`TransitDatabase` 在构造时抛 `AttributeError`，三个分析类构造时不检查；捕获 `AttributeError` 的调用方需改为 `TypeError`。
- `run_interpreter.py` 的文本导出遇到指向包内知识库的符号链接时，原来会把该知识库文件截断，现在报错退出，文件保持不变。

### 开发

- 测试按主题拆出 `tests/run_interpreter/`、`tests/context_matching/`、`tests/analyzer/relationship/` 三个包，测试名都不超过 45 个字符；`tests/test_test_names.py` 检查以 `test` 开头的标识符长度，命名约定写入 `AGENTS.md`。
- 仓内删除未被引用的 `bazi/calendar/hko_data/hko_data_explorer.ipynb`，它不在发布包中。

## bazi 2.1.0

### 知识发现与接口

- `KnowledgeBase` 新增 `find_objects`、`search` 和 `filter_values`，支持按名称精确查对象、按关键词搜索条目及列出七个查询维度的合法值。参考条目与默认输出的区分不变，合法值不保证默认查询有匹配。
- `context_matching.criteria()` 与 `criterion()` 提供无需创建命盘的判据目录，列出输入、观察范围和适用限度；部分事实判据不因此变成完整前提判断。
- `API_CONTRACT.md` 说明公开导入路径、参数别名、返回值与生成器生命周期，以及命盘、知识库和前提判别记录各自的恢复条件。

### 文档与贡献

- 使用 Sphinx／MyST 从公开契约、源码说明和完整知识注册表生成 API 与知识目录。`run_tests.py -a` 纳入严格文档检查，并实际执行 README 与教程示例。
- README 改为任务导航，另有快速开始、配置与时间口径、关系与流运、独立知识库、集成开发五篇指南。README 的文件链接使用绝对 GitHub URL，可用于 PyPI 包介绍。
- 新增贡献指南、知识勘误与流派读法 issue 表单。接受 issue，PR 先讨论；表单收集线索，正式来源记录仍由维护者核定。
- 提供手动文档版本归档与部署流程，区分开发版、固定发布版和待就绪状态。实际站点发布及线上回读须另行执行，文档构建成功不代表站点已上线。

### 兼容与显示

- 延续 2.0.0 的计算规则、默认值和记录格式；本版不要求因上述新增入口而迁移既有公开调用或重建记录。
- 配置对象的 `repr` 只列非默认字段；枚举自身的 `repr`、构造参数与默认对象不变。API 网页按宽度换行；Python 3.11 原生 `help()` 保留真实签名，不折长行。

## bazi 2.0.0

本版含破坏性变更。旧版导出的命盘 JSON 缺少新增的必填流派字段，需以原出生输入重新建盘。

### 破坏性变更

- 旧描述 API 退役：删除 `bazi.descriptions`、`bazi.interpreter`、`Interpreter`、旧枚举、重复记录与字段表，
  改用知识库 `KnowledgeBase` 的 `query`、`entry` 与 `sources`（见下节）。原文、稳定 ID、来源、限度和
  旧位置元数据保留；`LegacyDescription` 承载旧字段、序号与条件溯源。
- `BaziSchool` 新增字段 `peiou_xing_def`（配偶星取法，见下节；直接构造时可省略，取默认值），并重排位置参数及 JSON 键序，
  将关系定义和独立羊刃／飞刃定义放在前面；顺序为 `day_rollover`、`anhe_def`、`xing_def`、`gong_def`、
  `yangren_def`、`feiren_def`，其后为神煞锚及相邻定义。调用方改用关键字参数。已有 JSON 键名、默认值与
  读法不变；`from_json` 仍要求全部字段，按键名解析，不依赖输入键序。
- `BaziJson.BaziChartJsonDict` 改为默认盘与地点盘两种 JSON 的联合类型别名，只能用于类型标注。
  构造字典或读取 `__required_keys__` 等字段元数据时，默认盘用 `BaziJson.DefaultBaziChartJsonDict`，
  地点盘用 `BaziJson.LocationBaziChartJsonDict`。
- DAY 出生月柱与大运数节统一使用日期级干支年月的所属节和下一节；删除真实交节前仍数向
  旧节的 DAY 例外。逆排提前归属窗口负间隔钳零，首运标签以出生干支年为下限。
  此默认变化会改变起运、小运与大运派生 JSON；旧记录需以原出生输入重新建盘后核验。
  `Bazi.bracketing_jies` 改名为 `month_jies`。
- 地支批量查询统一接收规则层的冻结 `DizhiRelationDefinitions`；删除查询入口的独立定义
  参数 `anhe_def`、`xing_def`、`gong_def`，盘级字段与 JSON 保留。调用方通过 `definitions=...` 传入对象，或读取
  `BaziSchool.relation_definitions`。干支发现可用 `relations` 选择求值范围。
- `RelationDiscovery.merge` 按首次出现顺序去重；刑、集合型关系及生克查询输出不再取决于
  进程的 hash seed。现有使用方若依赖旧的无序组合序列，需改为使用新的稳定顺序。
- 删除 `Shishen.str_mapping_table()`。`from_str` 仍接受完整名称及十个单字简称，`abbr` 返回简称；
  需要简称映射时用 `{s.abbr: str(s) for s in Shishen}`。
- 删除 `bazi.analyzer.relationship.find_shensha`，它原本标为内部辅助函数。

### 知识库与前提判别

- `KnowledgeBase` 管理对象、情境、来源与条目四份注册表：按对象、情境、主题及来源等条件取交集查询，
  返回不可变条目与来源见证；`render`／`render_subject` 展示原文、来源与限度，`export_json`／`from_json`
  导出与恢复。值比较与 hash 按四份注册表的内容与顺序。另有 `object_id` 与 `DEFAULT_SOURCE_PATH`。
  `render` 接受调用方给的 `premise_verdict` 展示文字，不求值前提，也不改变输出资格。
- 随库知识以仅供参考的旧语料为主，规模与来源状态的计数见 README；署名与来源说明均为中文。
  婚恋相关 45 条旧文校准了署名与限度，原文不变；新增 7 条知识与 4 个古籍来源。
- `evaluate_context` 在显式选择的范围内检查已注册判据，返回 `ContextResult`：
  - 两个官杀判据判条目的完整前提：正官与七杀共现，以及共现且为女命。
  - 丁火身弱、庚金行运、偏印喜用、枭印夺食四个判据只判可计算事实：日主为丁或庚，偏印（及食神）
    在范围内出现，藏干计入。身弱、喜用等条件留在条目文字中，条目作条件参考返回。
  - 妻宫刑冲、配偶星透干两个婚恋结构判据经 `RelationshipProfile` 选择原局，或原局加按
    `TransitCoordinate` 查询的岁运，保存参与者、柱位与明藏层证据；男命语境条文不自动关联女命。

  所需流年或岁运缺失、不可查询时返回 `UNKNOWN`。判别不计算旺衰、喜忌或有效制化，前提满足也不表示
  现实事件成立。结果可导出 JSON（`record_version=4`，含完整知识快照），用 `ContextResult.from_json`
  恢复；其他版本的记录拒绝恢复。
- `BaziSchool.peiou_xing_def` 选择配偶星取法，影响 `BaziChart.relationship_stars` 与配偶星判据。
  默认 `ZHENGCAI_ZHENGGUAN`（男命正财、女命正官）不变；`YINYANGGAN` 采用《三命通会》的阴阳干读法。

### 其他

- 真太阳时命盘接受带时区出生时刻、经度及可选出生地区 `civil_timezone`，JSON 保留民用、UTC
  及真太阳时。wheel 增加 `equation_of_time.bin`；大运和流运查询采用 UTC+08:00 标签。
- 新增不可变 `GanzhiYearMonth` 领域坐标，以及 `Bazi.ganzhi_year_month`、`reference_datetime`、
  `location_time` 只读接口。地点时间事实区分 UTC 瞬间、固定出生偏移、未截断真太阳钟与分钟显示钟；
  展示直接格式化模型事实，真实前后节仍查物理时刻。
- 新增 `Jieqi.jies()` 十二节元组入口。
- `frozendict` 及其子类（藏干、关系发现结果）的 `repr` 显示类名与内容，不再是对象地址。
- 源码脚本 `run_interpreter.py` 支持固定出生与固定地点命盘、带种子的随机命盘、参考文字、来源展示、
  前提判别与显式导出；默认展示一个命盘，不导出文件，所选知识文字为空的标题省略。
- 自有 Markdown、API 说明、源码叙述注释与脚本 help 改为中文优先，保留原引文和技术拼写。
  README 按功能入口组织，每个 Python 示例可独立运行。

## bazi 1.0.0

- 可安装的 bazi 包从定义模块导入，支持 Python 3.11+，提供内联类型标注，无运行时依赖。
  源码导入改用 `bazi.*`，不再用 `src.*`。
- 当时 wheel 包含两份 HKO 编码表与三份 celestial 表；源码包另含 HKO 原始输入和源码验证测试。
- 当时历法后端、规则、流派默认值、JSON 恢复、流运、亲密关系分析及 Interpreter 均可直接使用，
   无需重建数据。此处 Interpreter 指该版本的类，后续已退役。
- 标准 MIT 授权涵盖作者自有材料，第三方说明另列内嵌数据与引文的权利范围。
- 手动发布 workflow 默认演练，正式发布须经受保护环境批准，只发布已测试 sdist 及其重建 wheel。

该版本不提供 src 兼容包、根类入口或安装命令行入口。对应源码的 README.md 说明当时的模块接口，RELEASING.md 说明发布前提。
