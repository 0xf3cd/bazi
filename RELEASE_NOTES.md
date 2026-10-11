# Release notes

## Unreleased

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

- Apparent-solar charts accept an aware birth time, longitude and optional birth-region
  `civil_timezone`, with civil, UTC and apparent times retained in JSON. The wheel also
  bundles `equation_of_time.bin`. Dayun and transit queries use UTC+08:00 labels.
  The Interpreter runner supports fixed location charts and exports.
- The chart renderer in `run_interpreter.py` omits headings whose selected knowledge text is empty.
- Knowledge queries expose immutable entries and source witnesses. The source-checkout runner supports fixed
  births, seeded random charts, reference text, source display and explicit exports;
  its default invocation now displays one chart without exporting files.

## bazi 1.0.0

- Installable `bazi` package with modular imports, Python 3.11+, inline typing and
  no runtime dependencies. Source imports now use `bazi.*`, not `src.*`.
- The wheel bundles the two encoded HKO tables and three celestial tables. The
  source archive also includes raw HKO inputs and source-verification tests.
- Existing calendar backends, rules, school defaults, JSON restoration, transits,
  relationship analysis and Interpreter remain available without data regeneration.
- Standard MIT permission covers author-owned material; third-party notices state
  the separate scope of embedded data and quotations.
- The manual release workflow defaults to rehearsal. Publication requires protected
  environment approval and publishes only the tested sdist and its rebuilt wheel.

No `src` shim, root-class facade or installed command-line entrypoint is provided.
See `README.md` for principal module interfaces and `RELEASING.md` for release
prerequisites.
