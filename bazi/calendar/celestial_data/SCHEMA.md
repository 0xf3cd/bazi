# celestial_data 数据格式（schema_version 2）

本文件规定离线生成器 `generator.py` 与运行时加载器 `loader.py` 的冻结数据契约。
两侧各自实现，偏离下述约定的一侧须修复。生成器需要 celestial-calendar Python 包；
运行时只用纯 Python，不依赖该包，与 HKO 的离线 `encoder.py`／运行时 `decoder.py` 分工相同。

## 文件

| 路径 | 行／样本数 | 来源 API |
| --- | --- | --- |
| `data/jieqi_moments.txt` | 7200 | `celestial_calendar.jieqi_moment(year, jieqi)` |
| `data/lunar_years_algo1.txt` | 199 | `celestial_calendar.lunar_year_info(ALGO1, year)` |
| `data/lunar_years_algo2.txt` | 199 | `celestial_calendar.lunar_year_info(ALGO2, year)` |
| `data/equation_of_time.bin` | 72643 | `celestial_calendar.apparent_solar_time(utc_midnight, 0)` |

`tests/calendar/celestial_fixtures/` 中的文本夹具同名同格式，标有 `fixture: true`，
只含五年切片 `1901, 1914, 1917, 1979, 2024`。加载器接受路径参数，可读取两者。

## 文本格式

UTF-8 文本，末尾换行，磁盘采用 LF；读取时 `splitlines()` 规范换行，所以 CRLF 文件加载与哈希结果相同。
井号开头的行均为头部，随后每行一条数据，字段用单空格分隔，无空行。
行按 `(year, jq_idx)` 或 `(lunar_year)` 升序写出。

`# key: value` 为机器可读来源行；井号加两个空格的续行为前键的叙述说明。
必需键如下，说明列不属于数据值：

| 键 | 值或约定 |
| --- | --- |
| `schema_version` | 2 |
| `celestial_version` | 0.6.1，须通过版本检查 |
| `release_asset` | `celestial-calendar==0.6.1` / PyPI wheel |
| `generated_by` | 生成脚本路径 |
| `generated_on` | YYYY-MM-DD |
| `source_api` | 产生记录的公共 Python 调用 |
| `timescale` | 按文本表规定，三表的约定不同 |
| `rounding` | 仅节气表 |
| `year_range` | 两端包含 |
| `rows` | 确切行数，加载器与解析所得数据行核对 |
| `columns` | 按顺序列出、空格分隔的列名 |

可选键为节气表的 `timescale_caveat` / `rounding`、农历表的 `algo`，以及只用于夹具的 `fixture`。
键集封闭：列名不能另作头部键，`# leap_month: 1..12, or 0 when …` 会把整句解析成来源键值。
各列说明应放在 `columns` 的续行。`tests/calendar/test_celestial_tables.py` 按此列表核对各随库表及夹具，
避免文档、生成器和加载器正则的三份契约静默分离。

## jieqi_moments.txt

```text
columns: year jq_idx name date time
1901 00 立春 1901-02-04 19:39:57
```

- `year`：公历年，1901..2200，两端包含。
- `jq_idx`：补零的 0..23，与 `list(Jieqi)` 下标相同，0 为立春、23 为大寒。
  生成时核 `celestial_calendar.jieqi_name` 等于 `list(Jieqi)[jq_idx].value`。
  偶数为节（开月边界），奇数为气。HKO 磁盘数据则从小寒开始，
  使用 `Jieqi.as_list(ganzhi_year=False)`，两者不可混同。
- `name`：中文节气名，与 `jq_idx` 冗余；加载器交叉校验，手改不一致的行会失败。
- `date` / `time`：YYYY-MM-DD / HH:MM:SS。
- 时间基准为 UTC+08:00：对 celestial UT1 完整时刻恰加八小时并重算日期，不能只改日内时刻。
- 截断到整秒，不四舍五入：23:59:59.6 舍入会变为次日，改变日期归属；截断不变日期，
  存储时刻比真实时刻提前不超过一秒。
- Y 年的小寒、大寒（序号 22/23）在 Y 年一月，年内行不按日期排序。
  与 HKO 的 `jieqi_date(Y, 小寒)` 约定一致，已核 1901 / 2024 / 2099。
- 1972 年起 UT1−UTC ≤ 0.9s；此前以 UT1 代理，沿 celestial Phase C 约定。
  通常只影响节时刻前后 ±0.9s 的出生，但节本身接近午夜时可改变整日归属。
  1979 大寒距午夜四秒。
- TT 节时刻仍由太阳黄经求根。2101–2200 年转 UT1 使用 Stephenson-Morrison-Hohenkerk
  integrated-lod ΔT 外推，连续但无精度保证，也无独立 HKO 对照。

## lunar_years_algo{1,2}.txt

```text
columns: lunar_year first_solar_date leap_month month_len_bits days_counts ganzhi
1901 1901-02-19 0 0x0752 29,30,29,29,30,29,30,29,30,30,30,29 辛丑
```

- `lunar_year`：1901..2099，两端包含，两算法都限制于此窗口。algo2 原生支持 [410, 2500]；
  当前共用一个范围契约，避免四种范围语义，扩大范围另立议题。
- `first_solar_date`：农历正月初一的公历日期。
- `leap_month`：1..12，无闰月为 0；HKO 记录用 `None`，加载器统一为 `None` 后比较。
- `month_len_bits`：由公共 `month_lengths` 元组编码为十六进制，低位优先。
  位 i 表示顺序第 i+1 个月，闰月独占一位；1 为三十日，0 为二十九日。
  algo1 与 HKO `days_counts` 相符 199/199，由 `tests/calendar/test_celestial_tables.py` 核对，不是生成检查。
- `days_counts`：从位图解码的十二或十三项月长，保留冗余；加载器核两列相等，任改一列导致不一致即失败。
- `ganzhi`：在 `Ganzhi.list_sexagenary_cycle()` 上按 `(lunar_year - 4) mod 60` 取值，运行时不使用。
  HKO `LunarYearInfo` 含此字段，所以差异比较保留它；199/199 相符由测试验证，不是生成检查。
  生成器不导入 `hko_data`，其检查范围见下节。
- 默认 algo1，沿 HKO 官方历书体系；农历为展示数据，四柱以节气为基础，不读取农历。
  algo2 经 `jde_to_utc8` 采用考虑闰秒的 UTC+8（celestial #84），须显式选择。
- 窗口内两算法恰有六年不同：1914、1915、1916、1920、2057、2097，见 celestial
  `src/test/lunar/diff_test.cpp`。测试另对 HKO 独立复现；algo1 匹配 HKO 199/199，
  因此 algo2 对 HKO 的差异恰等于对 algo1 的差异。

## equation_of_time.bin

每日 UTC 午夜节点，逻辑值为真太阳时减平太阳时，单位秒；正值表示日晷快于当地平太阳时。
生成时在零经度调用 `apparent_solar_time`，位移只含 EOT。

- 节点从 1901-02-17T00:00:00Z 至末尾插值哨兵 2100-01-06T00:00:00Z，两端包含。
  运行时查询采用不含末哨兵的半开范围，覆盖所有允许经度及民用偏移下映射到
  真太阳日期窗口 1901-02-19 至 2099-12-31 的 UTC 瞬间，并含精度归属所需下一节（2100 小寒）。
- 间隔恰为 86,400 UTC 秒。运行时按 UTC 日内比例线性插值，不把范围外查询钳到端点。
- 样本为大端有符号 int16，单位十分之一秒。生成时用 Python 的 ties-to-even `round`
  舍入到最近十分之一秒，量化误差不超过 0.05 秒；插值另有近似误差。
  `tests/calendar/test_celestial_loader.py` 的来源锚核编码值。
- 固定五十六字节大端头部为 `>8sIIII32s`：magic `BAZIEOT1`、公历起始日 `ordinal`、样本数、
  间隔秒数、每秒单位数 10、载荷 SHA-256。载荷恰有 `sample_count` 个 int16。
  运行时在普通及优化 Python 下均校验全部头部字段、字节数及摘要。

## 生成器检查

生成时立即拒绝不满足契约的表：

1. 版本：导入包的公共 `__version__` 须为固定 0.6.1；ΔT 或 celestial 更新可改变全部时刻。
2. 行数：7200 / 199 / 199 行及 72,643 个 EOT 样本；文本 `rows` 头部与 EOT 字节数须与写出内容相符。
3. 交叉校验：全部二十四项满足 `jieqi_name(Jieqi(idx)) == list(Jieqi)[idx].value`，
   公共 `month_lengths` 元组须能经磁盘位图往返。
4. EOT 完整性：各源值编码为十分之一秒后须能存入有符号 int16，载荷摘要写入固定头部。

## 边界约定

消费者共同语义：出生时刻恰等于节气时刻时归新柱，比较为 `birth >= jieqi`。
#72 的 golden 案例均非边界，所以另需定向断言。
