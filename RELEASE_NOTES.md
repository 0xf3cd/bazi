# 发布说明

## Unreleased

- 自有 Markdown、API 说明、源码叙述注释与脚本 help 改为中文优先，保留原引文和技术拼写。
  README 按功能入口组织，每个 Python 示例可独立运行，自定义知识源示例显式准备临时文件。
- `BaziSchool` 重排位置参数及 JSON 输出键序，将关系定义和独立羊刃／飞刃定义放在前面；
  调用方改用关键字参数。键名、默认值与按键名恢复完整档案的契约保留。
- 删除 `Shishen.str_mapping_table()`。
  `Ganzhi.next`／`prev` 非六十甲子组合明确拒绝，含零步。
- 新增 `Jieqi.jies()` 十二节元组入口。

- 金舆、三套羊刃与对应飞刃、两套国印按既有定义派生；红鸾、天喜按起支逆数。
  表值、出处和流派选择保留，子平羊刃仍仅五阳干；同值的国印与飞刃仍为独立神煞。

- 地支批量查询统一接收规则层的冻结 `DizhiRelationDefinitions`；删除查询入口的独立定义
  参数，盘级字段与 JSON 保留。调用方通过 `definitions=...` 传入对象，或读取
  `BaziSchool.relation_definitions`。干支发现可用 `relations` 选择求值范围。
- `RelationDiscovery.merge` 按首次出现顺序去重；刑、集合型关系及生克查询输出不再取决于
  进程的 hash seed。现有使用方若依赖旧的无序组合序列，需改为使用新的稳定顺序。

- `ContextResult` 复用已验证的 `KnowledgeBase`，渲染不重建整库；导出保留完整知识快照。
  构造字段及属性 `knowledge_json` 改为 `knowledge: KnowledgeBase`；`ContextProfile.stem_scope`
  属性及记录字段删除。`ChartOccurrence` 构造移除 `index` 位置字段；`index` 由柱位派生，
  不进入记录，展示只保留柱位。新记录格式为版本2，版本1明确拒绝；知识内容和顺序仍参与结果值比较与 hash。

- DAY 出生月柱与大运数节统一使用日期级干支年月的所属节和下一节；删除真实交节前仍数向
  旧节的 DAY 例外。逆排提前归属窗口负间隔钳零，首运标签以出生干支年为下限。
  此默认变化会改变起运、小运与大运派生 JSON；旧记录需以原出生输入重新建盘后核验。
- 新增不可变 `GanzhiYearMonth` 领域坐标，以及 `Bazi.month_jies`、`ganzhi_year_month`、
  `reference_datetime`、`location_time` 只读接口。地点时间事实区分 UTC 瞬间、固定出生偏移、
  未截断真太阳钟与分钟显示钟；展示直接格式化模型事实，真实前后节仍查物理时刻。
- 知识 API 破坏性清理：删除 `bazi.descriptions`、`bazi.interpreter`、`Interpreter`、旧枚举、
  重复记录与字段表。`KnowledgeBase` 及现有记录是唯一模型；原文、稳定 ID、来源、限度和
  旧位置元数据保留，语料未扩充。调用方改用 `query`、`entry`、完整不可变 `sources` 注册表。
  新来源无需同步枚举；`LegacyDescription` 继续承载字段、序号与条件溯源。
- 新增 `object_id`、`DEFAULT_SOURCE_PATH` 和共用主体文字投影 `render_subject`。
  主体展示与全角色查询分开，旧位置顺序与语料顺序分开；公开 `render` 接受调用方的
  `premise_verdict` 展示文字，不求值前提或改变输出资格。前提判别仍由 `evaluate_context` 执行。
- 真太阳时命盘接受带时区出生时刻、经度及可选出生地区 `civil_timezone`，JSON 保留民用、UTC
  及真太阳时。wheel 增加 `equation_of_time.bin`；大运和流运查询采用 UTC+08:00 标签。
  `run_interpreter.py` 支持固定地点命盘及导出。
- `run_interpreter.py` 的命盘展示省略所选知识文字为空的标题。
- 知识查询提供不可变条目与来源见证。源码 runner 支持固定出生、带种子的随机命盘、参考文字、
  来源展示及显式导出；默认展示一个命盘，不导出文件。

## bazi 1.0.0

- 可安装的 bazi 包从定义模块导入，支持 Python 3.11+，提供内联类型标注，无运行时依赖。
  源码导入改用 `bazi.*`，不再用 `src.*`。
- 当时 wheel 包含两份 HKO 编码表与三份 celestial 表；源码包另含 HKO 原始输入和源码验证测试。
- 当时历法后端、规则、流派默认值、JSON 恢复、流运、亲密关系分析及 Interpreter 均可直接使用，
  无需重建数据。此处 Interpreter 指该版本的类，后续已退役；现役 runner 为 `run_interpreter.py`。
- 标准 MIT 授权涵盖作者自有材料，第三方说明另列内嵌数据与引文的权利范围。
- 手动发布 workflow 默认演练，正式发布须经受保护环境批准，只发布已测试 sdist 及其重建 wheel。

不提供 src 兼容包、根类入口或安装命令行入口。模块接口见 README.md，发布前提见 RELEASING.md。
