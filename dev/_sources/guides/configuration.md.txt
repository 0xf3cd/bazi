# 配置与时间口径

默认配置能排出一张盘，但同一个出生时间在不同口径下可以得到不同结果。
这一页按“什么时候需要改”组织，每一节给一个可运行的例子。字段的完整列表在
{py:class}`~bazi.school.BaziConfig` 和 {py:class}`~bazi.school.BaziSchool` 的 API 参考中，这里不重复。

配置只表示你选择了哪一种口径，不判断哪一种更对。库没有替你选“最准确”的读法。

## 精度：你知道出生到哪一步

`BaziPrecision` 决定出生时间与节气比较到什么粒度。默认的 `DAY` 只比日期，整个交节日都归新一节；
`HOUR` 按两小时的时辰比，`MINUTE` 比到分钟。这是同一条规则的三个粒度，不是对同一真值的三种估计。

下面以 2000 年立春当天（20:40:23 交节）为例，出生在 20:00：

```{testcode} config-precision
from datetime import datetime

from bazi.bazi import Bazi
from bazi.school import BaziConfig

birth = datetime(2000, 2, 4, 20, 0)
for precision in ('day', 'hour', 'minute'):
  config = BaziConfig.from_values(precision=precision)
  bazi = Bazi.create(birth, 'male', config)
  print(precision, bazi.year_pillar, bazi.month_pillar)
```

```{testoutput} config-precision
day 庚辰 戊寅
hour 庚辰 戊寅
minute 己卯 丁丑
```

只知道日期时用默认的 `DAY`；知道时分且在意交节当天的归属，才改成 `HOUR` 或 `MINUTE`。
三档的边界例子见 {py:class}`~bazi.school.BaziPrecision`。

## 历法后端：节气数据从哪里来

`CalendarBackend` 选择历法数据。`celestial` 是默认，也是文档推荐的选择；
`hko` 基于香港天文台数据，只有日期级精度，所以只能配合 `DAY`；
`celestial-algo2` 采用第二套阴历算法，199 个支持年份中有 6 年与 `celestial` 不同。
差异的来源和范围见 {py:class}`~bazi.calendar.backend.CalendarBackend`。

`HOUR` 或 `MINUTE` 需要真实的节气时刻，因此和 `hko` 组合会被拒绝（`ValueError`）。

## 换日：23:00 还是 24:00

`BaziSchool.day_rollover` 决定子时前半段属于哪一天。默认 `WAN_ZISHI`（晚子时）在 23:00 就换日柱，
`ZIZHENG`（子正）到 00:00 才换。年柱和月柱不受影响，它们按精度独立判断。

```{testcode} config-rollover
from dataclasses import replace
from datetime import datetime

from bazi.bazi import Bazi
from bazi.school import DEFAULT_CONFIG, BaziSchool, DayRollover

birth = datetime(1995, 8, 3, 23, 30)
zizheng = replace(DEFAULT_CONFIG, school=BaziSchool(day_rollover=DayRollover.ZIZHENG))
for name, config in (('晚子时', DEFAULT_CONFIG), ('子正', zizheng)):
  bazi = Bazi.create(birth, 'male', config)
  print(name, '日柱', bazi.day_pillar, '时柱', bazi.hour_pillar)
```

```{testoutput} config-rollover
晚子时 日柱 丁卯 时柱 庚子
子正 日柱 丙寅 时柱 戊子
```

两种读法下时支都是子，时干跟随各自的日柱。其他流派选项（关系定义、神煞取锚、配偶星取法）
的取值和出处写在 {py:class}`~bazi.school.BaziSchool` 的字段说明里；本库保留各家读法，不合成一个“正确”规则。

## 起运口径：只改年份标签

`DayunYearRule` 只改变每步大运的年份标签，不改变四柱，也不改变大运的物理起止时刻。
`JIE_PROJECTED` 按每个边界所属的节投影干支年；`FIXED_DECADE` 从首个标签起固定每十年一步。

```{testcode} config-dayun-rule
from itertools import islice
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.school import BaziConfig

birth = datetime(1910, 4, 7, 6, 1)
for rule in ('jie_projected', 'fixed_decade'):
  config = BaziConfig.from_values(dayun_year_rule=rule)
  chart = BaziChart(Bazi.create(birth, 'male', config))
  steps = list(islice(chart.dayun, 3))
  print(rule, [step.ganzhi_year for step in steps], [str(step.ganzhi) for step in steps])
```

```{testoutput} config-dayun-rule
jie_projected [1919, 1930, 1939] ['辛巳', '壬午', '癸未']
fixed_decade [1919, 1929, 1939] ['辛巳', '壬午', '癸未']
```

大运干支和起止时刻在两种规则下相同；示例列出的前三步中，第二步的标签相差一年。

## 真太阳时：时区、经度和节气时刻

默认路径把输入当作当地民用时刻，不做任何太阳时修正。要启用真太阳时，需要同时满足：

- `birth_time` 是带时区的 `datetime`，时区由你负责；库不会根据经度推断时区，夏令时和历史偏移也由调用方处理。
- 传入 `longitude`，东经为正，范围 `[-180, 180]`。库只使用经度，不接受纬度。
- 配置使用 `celestial` 后端和 `HOUR` 或 `MINUTE` 精度。
- 如果输入的时区不是出生地的民用时区，用 `civil_timezone` 另行指定。

三个口径各管一件事：

- **时区**把输入换成绝对时刻，并给出出生地的民用偏移。
- **经度与均时差**把民用时刻换成真太阳钟。时柱和日柱按这个钟读取。
- **节气时刻**表以东八区无时区标签保存；地点盘会把节气时刻换到同一个真太阳钟上再与出生比较。
  大运起止和流运查询仍使用东八区标签（`reference_datetime`），不是真太阳钟。

下面的经度是演示用的合成坐标，不对应任何真实个人的位置。同一个民用时刻，换一个经度，时柱就不同：

```{testcode} config-location
from datetime import datetime, timedelta, timezone

from bazi.bazi import Bazi
from bazi.school import BaziConfig

config = BaziConfig.from_values(precision='minute')
civil = datetime(2001, 3, 15, 7, 10, tzinfo=timezone(timedelta(hours=8)))
for longitude in (87.6, 121.5):
  bazi = Bazi.create(civil, 'female', config, longitude=longitude)
  facts = bazi.location_time
  assert facts is not None
  print(longitude, '真太阳时', bazi.solar_datetime, '时柱', bazi.hour_pillar)
  print(' 民用时刻', facts.civil_time.isoformat())
```

```{testoutput} config-location
87.6 真太阳时 2001-03-15 04:51:00 时柱 壬寅
 民用时刻 2001-03-15T07:10:00+08:00
121.5 真太阳时 2001-03-15 07:06:00 时柱 甲辰
 民用时刻 2001-03-15T07:10:00+08:00
```

`solar_datetime` 只显示到分钟；完整的时间事实在 `location_time`，包含绝对时刻、民用钟、经度和未截断的真太阳钟。
下面几种输入会被拒绝，错误在构造时立即抛出：

```{testcode} config-location-errors
from datetime import datetime, timedelta, timezone

from bazi.bazi import Bazi
from bazi.school import BaziConfig

config = BaziConfig.from_values(precision='minute')
aware = datetime(2001, 3, 15, 7, 10, tzinfo=timezone(timedelta(hours=8)))
naive = datetime(2001, 3, 15, 7, 10)

attempts = {
  '带时区但没有经度': lambda: Bazi.create(aware, 'female', config),
  '有经度但没有时区': lambda: Bazi.create(naive, 'female', config, longitude=87.6),
  '精度为 DAY': lambda: Bazi.create(aware, 'female', BaziConfig(), longitude=87.6),
  '传入纬度': lambda: Bazi.create(aware, 'female', config, longitude=87.6, latitude=40.0),
}
for name, attempt in attempts.items():
  try:
    attempt()
  except (TypeError, ValueError) as error:
    print(name, type(error).__name__)
```

```{testoutput} config-location-errors
带时区但没有经度 ValueError
有经度但没有时区 ValueError
精度为 DAY ValueError
传入纬度 TypeError
```

## 替换一项配置

`BaziConfig` 和 `BaziSchool` 都是 frozen dataclass，不能原地修改。要换一项，用 `dataclasses.replace` 得到新对象；
原对象和默认对象保持不变。

```{testcode} config-replace
from dataclasses import replace
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.school import DEFAULT_CONFIG, DEFAULT_SCHOOL, BaziConfig, BaziPrecision, DayRollover

minute = replace(DEFAULT_CONFIG, precision=BaziPrecision.MINUTE)
print(minute.precision, DEFAULT_CONFIG.precision)
print('默认配置未变', minute != DEFAULT_CONFIG, BaziConfig() == DEFAULT_CONFIG)
print('流派对象共享', minute.school is DEFAULT_SCHOOL)

try:
  DEFAULT_CONFIG.precision = BaziPrecision.HOUR
except AttributeError as error:
  print('不能原地修改', type(error).__name__)

birth = datetime(2000, 2, 4, 20, 0)
default_chart = BaziChart(Bazi.create(birth, 'male', DEFAULT_CONFIG))
minute_chart = BaziChart(Bazi.create(birth, 'male', minute))
print(default_chart.json['precision'], minute_chart.json['precision'])
```

```{testoutput} config-replace
minute day
默认配置未变 True True
流派对象共享 True
不能原地修改 FrozenInstanceError
day minute
```

配置属于 `Bazi` 本身，所以换了配置就要重新生成依赖它的对象：

- 新的 `Bazi`，再包成新的 `BaziChart`；`TransitChart` 和 `RelationshipAnalyzer` 也持有原来的命盘，需要对新命盘重建。
- 已导出的命盘 JSON 记录了当时的配置，不会随之变化。
- `Bazi` 按值比较，`BaziChart` 按对象身份比较，换配置后两者都与原来的不等。

`BaziConfig()` 等于 `DEFAULT_CONFIG`，但不是同一个对象；`BaziConfig().school` 与 `DEFAULT_SCHOOL` 是同一个实例。

## 术语索引

| 术语 | 在本库 API 里的含义 |
| --- | --- |
| 精度 `BaziPrecision` | 出生与节气比较的粒度：`DAY`、`HOUR`、`MINUTE` |
| 历法后端 `CalendarBackend` | 节气与干支历的数据来源：`hko`、`celestial`、`celestial-algo2` |
| 换日 `DayRollover` | 日柱在 23:00 还是 00:00 更换 |
| 起运年份 `DayunYearRule` | 大运年份标签的投影方式，不改变物理时刻 |
| 流派 `BaziSchool` | 换日、关系与神煞取法等分歧项的集合，每个字段都参与相等性与 JSON |
| 真太阳时 | 由经度、民用偏移与均时差换算的钟；见 `Bazi.location_time` |
| `civil_timezone` | 出生地民用时区，仅在启用经度时使用 |

字段与枚举成员的完整说明由 API 参考生成，见 {py:class}`~bazi.school.BaziConfig`。
