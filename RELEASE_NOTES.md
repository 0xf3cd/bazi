# 发布说明

## Unreleased

- 删除命盘／前提判别结果的公开 JSON 保存恢复、知识快照导出与恢复及 `record_migration` 模块，不保留兼容入口或替代保存格式。`BaziJson`、`LocationTimeJson`、`BaziSchool.from_json`、`TransitSet.json` 一并删除。请保留旧原件；需要当前结论时，用原出生输入与完整配置重新排盘、求值，见 [未发布升级说明](https://github.com/0xf3cd/bazi/blob/main/README.md#未发布升级说明)。
- `ContextResult` 的构造及 `replace` 使用 `_bazi` 参数，验证后保存 `Bazi` 输入的独立深拷贝；`bazi` 属性每次返回独立深拷贝。输入完整身份仍参与相等与哈希，原 `input_json` 字段删除。
- 知识库保留 `KnowledgeBase.load(path)`、完整引用校验和查询／渲染。JSON 只作当前编辑源，`schema_version` 只接受精确整数 2，不自动迁移旧版来源。
- 源码脚本删除 `--export-chart-json`、`--export-context-json`、`--export-knowledge-json`；保留 TXT、知识编辑源读取和源文件覆盖保护。

## bazi 2.3.0

本版含旧记录与源码脚本调用的破坏性变更，升级前请保留原记录及出生输入，见 [迁移说明](https://github.com/0xf3cd/bazi/blob/main/README.md#从-v220-迁移到-v230)。

### 兼容与迁移

- `BaziSchool` 尾部新增 `kongwang_anchor`，默认 `Anchor.DAY`，也可选 `YEAR`、`YEAR_AND_DAY`。该字段进入命盘身份与 JSON。
- 缺少 `kongwang_anchor` 的旧命盘或前提判别记录拒绝恢复，不自动补默认值。须按原出生输入、完整配置及显式选择的新锚重建命盘；前提判别记录须重新求值后另存。没有自动迁移接口，不要只补字段或改版本号。
- 知识库的 `schema_version=1`、前提判别记录的 `record_version=4` 不变；版本值不变不表示缺字段的旧记录可恢复。
- 源码脚本 `run_interpreter.py` 移除 v2.2.0 保留的旧平铺写法，裸调用只打印帮助。原 `--seed 236` 改为 `chart --seed 236`，`--query-knowledge` 改为 `knowledge --all`；其他对照见 [源码脚本兼容说明](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md#源码脚本)。这些变化不新增安装后的 CLI；更新 bazi 包不会更新本地源码脚本。

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
  无需重建数据。此处 Interpreter 指该版本的类，后续已退役；现役 runner 为 `run_interpreter.py`。
- 标准 MIT 授权涵盖作者自有材料，第三方说明另列内嵌数据与引文的权利范围。
- 手动发布 workflow 默认演练，正式发布须经受保护环境批准，只发布已测试 sdist 及其重建 wheel。

不提供 src 兼容包、根类入口或安装命令行入口。模块接口见 README.md，发布前提见 RELEASING.md。
