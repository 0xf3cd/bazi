# bazi 1.0.0

- DAY 出生月柱与大运数节统一使用日期级干支年月的所属节和下一节；删除真实交节前仍数向
  旧节的 DAY 例外。逆排提前归属窗口负间隔钳零，首运标签以出生干支年为下限。
  此默认变化会改变起运、小运与大运派生 JSON；旧记录需以原出生输入重新建盘后核验。
- 新增不可变 `GanzhiYearMonth` 领域坐标，以及 `Bazi.ganzhi_year_month`、
  `reference_datetime`、`location_time` 只读接口。地点时间事实区分 UTC 瞬间、固定出生偏移、
  未截断真太阳钟与分钟显示钟；展示直接格式化模型事实，真实前后节仍查物理时刻。

- Installable `bazi` package with modular imports, Python 3.11+, inline typing and
  no runtime dependencies. Source imports now use `bazi.*`, not `src.*`.
- The wheel bundles the two encoded HKO tables and four celestial tables. The
  source archive also includes raw HKO inputs and source-verification tests.
- Existing calendar backends, rules, school defaults, JSON restoration, transits,
  relationship analysis and Interpreter remain available without data regeneration.
- Apparent-solar charts accept an aware birth time, longitude and optional birth-region
  `civil_timezone`, with civil, UTC and apparent times retained in JSON. Dayun and transit
  queries use UTC+08:00 labels. The Interpreter runner supports fixed location charts and exports.
- Standard MIT permission covers author-owned material; third-party notices state
  the separate scope of embedded data and quotations.
- The manual release workflow defaults to rehearsal. Publication requires protected
  environment approval and publishes only the tested sdist and its rebuilt wheel.
- Among reference-only claims, a finite description-corpus pass corrected three wording
  defects and retained seven source-unverified semantic ambiguities; default description
  output is unchanged. The chart renderer in `run_interpreter.py` now omits headings
  whose selected description list is empty. No public description fields were added.
- Structured description queries expose immutable claims and source witnesses alongside
  the existing text lookups. The source-checkout Interpreter runner supports fixed
  births, seeded random charts, reference text, source display and explicit exports;
  its default invocation now displays one chart without exporting files.

No `src` shim, root-class facade or installed command-line entrypoint is provided.
See `README.md` for principal module interfaces and `RELEASING.md` for release
prerequisites.
