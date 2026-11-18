# 第三方材料

LICENSE 的 MIT 授权只及 Ningqi Wang 自有材料，不重新许可本项目中的第三方数据、引文或参考材料。

- `tests/calendar/hko_data/data/` 的原始历法输入与编码表来自香港天文台公历／农历对照表：
  <https://www.hko.gov.hk/en/gts/time/conversion.htm>。
  使用条款见 <https://www.hko.gov.hk/en/readme/readme.htm>。
  原件、编码表及同目录树下的编解码工具随源码与 sdist 保留，用于独立对拍，不进入 wheel。
- `bazi/calendar/celestial_data/data/` 的表及测试夹具 `tests/calendar/celestial_fixtures/` 由
  [celestial-calendar](https://github.com/0xf3cd/celestial-calendar) 生成。
  表中保留原生成头部，记录版本、算法与来源；农历表为 `lunar_years.txt`。
  运行时使用的表进入 wheel；测试夹具、根目录生成器 `run_calendar_generation.py` 与数据格式说明
  `bazi/calendar/celestial_data/SCHEMA.md` 随源码包分发，不进入 wheel。
- 自有代码的 MIT 授权不授予第三方引文、参考材料或解释语料的权利，包括 `bazi/knowledge_data.json`
  及测试中的语料快照 `tests/data/description_legacy_baseline.json`、`tests/data/corpus_allowed_changes.json`、
  `tests/data/source_errata_baseline.json`。
  已有引用保留，用于识别来源，不表示授权许可。
- 源码与测试的 docstring、注释引用的古籍原文及今人注释，出处写在引用处，例如 `bazi/rules.py`
  引《五行精纪注释》的【原文】与【注释】。这些引用用于说明规则依据，不表示授权许可。
- `bazi/references/calendar.md` 是本仓自写的要点，整理自知乎用户子非鱼的回答
  <https://www.zhihu.com/question/22318210/answer/21004490>；原文权利归原作者，本仓不转载原文。
- `tests/integration/external_baseline.json` 的外部排盘观测记录来源、配置及采集日期，
  是参考观测，与作者自有的比较测试及 bazi 快照分开。

进入 wheel 或源码包不解决第三方材料权利问题；不对合并分发内容声明统一许可证。
