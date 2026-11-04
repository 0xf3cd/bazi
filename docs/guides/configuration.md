# 配置与时间口径

默认配置能排出一张盘，但同一个出生时间在不同口径下可以得到不同结果。
这一页按“什么时候需要改”组织，每一节给一个可运行的例子。字段的完整列表在
{py:class}`~bazi.school.BaziConfig` 和 {py:class}`~bazi.school.BaziSchool` 的 API 参考中，这里不重复。

配置只表示你选择了哪一种口径，不判断哪一种更对。库没有替你选“最准确”的读法。

## 默认输入：东八区节表与输入钟

不传 `longitude` 时，`Bazi.create` 接收无时区 `datetime` 或等价字符串，不从中推断地点或时区：

- **年月柱**按选定精度，将输入标签与东八区（UTC+8）的节气表比较。默认示例因此按东八区公历钟填写。
- **日柱、时柱**按输入标签的日时读取，再应用所选换日点；即使使用 `DAY`，小时也没有被丢弃。
- **起运与流运**同样使用东八区参考标签；默认盘的 `reference_datetime` 就是输入钟时，不另作时区换算。

非 UTC+8 地区的当地民用标签不能直接当作东八区标签，夏令时也不会由默认入口补算。
若选择按北京时间排盘，先换为 UTC+8，再去掉时区交给默认入口；这样日时柱也会按北京时间读取，
不再保留当地民用钟。需要真太阳时则使用[地点盘](https://github.com/0xf3cd/bazi/blob/main/docs/guides/configuration.md#真太阳时时区经度和节气时刻)，它会修正日时所读的钟。

**当前没有“保留当地民用钟、按物理节界归年月、但不作太阳时修正”的对应入口。**
不要只把带时区输入的 `tzinfo` 去掉，也不要把时区转换和真太阳时当成等价操作。

## 精度：你知道出生到哪一步

`BaziPrecision` 决定出生时间与节气比较到什么粒度。默认的 `DAY` 只比日期，整个交节日都归新一节；
`HOUR` 按两小时的时辰比，`MINUTE` 比到分钟。这是同一条规则的三个粒度，不是对同一真值的三种估计。

下面以东八区 2000 年立春当天（20:40:23 交节）为例，分别读取年、月、日、时柱：

```{testcode} config-precision
from datetime import datetime

from bazi.bazi import Bazi
from bazi.school import BaziConfig

for birth in (datetime(2000, 2, 4, 20, 39), datetime(2000, 2, 4, 20, 40)):
  for precision in ('day', 'hour', 'minute'):
    config = BaziConfig.from_values(precision=precision)
    bazi = Bazi.create(birth, 'male', config)
    print(birth.strftime('%H:%M'), precision, ' '.join(map(str, bazi.pillars)))
```

```{testoutput} config-precision
20:39 day 庚辰 戊寅 壬辰 庚戌
20:39 hour 庚辰 戊寅 壬辰 庚戌
20:39 minute 己卯 丁丑 壬辰 庚戌
20:40 day 庚辰 戊寅 壬辰 庚戌
20:40 hour 庚辰 戊寅 壬辰 庚戌
20:40 minute 庚辰 戊寅 壬辰 庚戌
```

`MINUTE` 从 20:40 这一分钟的起点便归新节，`HOUR` 从包含交节时刻的戌时起点归新，`DAY` 则整天归新。
这三档只改变年月的交节归属，例中的日时柱不变。只知道日期时可选默认 `DAY`，但日时是否有可靠输入仍需另行判断；
知道时分且在意交节当天归属时，再选择适合的粒度。完整边界约定见 {py:class}`~bazi.school.BaziPrecision`。

## 海外与夏令时：三种输入方式的区别

以下使用纽约冬令时与夏令时的当地钟各一例。第一种故意演示误用：丢掉时区后，默认入口不会知道它是纽约时间。
第二种改用东八区钟，第三种显式启用经度 −74 的真太阳时。经度只作演示，不对应真实个人。
`ZoneInfo` 需要系统时区数据库；环境缺少时可安装 `tzdata`。

```{testcode} config-overseas
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from bazi.bazi import Bazi
from bazi.school import BaziConfig

config = BaziConfig.from_values(precision='minute')
zone = ZoneInfo('America/New_York')
utc8 = timezone(timedelta(hours=8))
for civil in (
  datetime(2000, 2, 4, 8, 30, tzinfo=zone),
  datetime(2000, 8, 7, 1, 4, tzinfo=zone),
):
  print('当地民用钟', civil.isoformat())
  local_label = civil.replace(tzinfo=None)
  reference_label = civil.astimezone(utc8).replace(tzinfo=None)
  cases = (
    ('当地标签（误用）', local_label, None),
    ('东八区标签', reference_label, None),
    ('地点盘真太阳时', civil, -74),
  )
  for label, birth, longitude in cases:
    bazi = Bazi.create(birth, 'male', config, longitude=longitude)
    print(label, ' '.join(map(str, bazi.pillars)))
```

```{testoutput} config-overseas
当地民用钟 2000-02-04T08:30:00-05:00
当地标签（误用） 己卯 丁丑 壬辰 甲辰
东八区标签 庚辰 戊寅 壬辰 辛亥
地点盘真太阳时 庚辰 戊寅 壬辰 甲辰
当地民用钟 2000-08-07T01:04:00-04:00
当地标签（误用） 庚辰 癸未 丁酉 辛丑
东八区标签 庚辰 甲申 丁酉 丁未
地点盘真太阳时 庚辰 甲申 丁酉 庚子
```

这两个瞬间均已过相应物理节界，但当地标签被当成东八区钟比较时仍归旧年月。
转换为东八区钟改变了时柱；真太阳时又是另一种日时读取方式，夏令时例中甚至从丑时改为子时。
冬令时例的当地标签与真太阳时恰好同为辰时，不表示两种钟等价。

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

两种读法下时支都是子，时干跟随各自的日柱。

## 流派选项：什么时候换取法

使用的书本或对照软件采用另一种查法时，再修改相应字段。一次只改要比较的选项，便于看出差异来自哪里。
字段名以 `_def` 结尾的选择取法定义，以 `_anchor` 结尾的选择查法依据的柱位。
完整定义及出处见 {py:class}`~bazi.school.BaziSchool` 和 {doc}`rule-coverage`。

| 字段 | 什么时候需要改 |
| --- | --- |
| `day_rollover` | 出生在23时，采用子正00:00换日而非默认23:00换日时；示例见上节。 |
| `anhe_def` | 对照的暗合表不同，例如是否加入寅丑，或使用盲派的三组暗合。 |
| `xing_def` | 需要区分丑未戌、寅巳申必须三支齐现，还是三取二即成刑时。{py:func}`~bazi.utils.dizhi_utils.xing` 区分谁刑谁，批量查询只返回参与组合。 |
| `gong_def` | 要改用另一套拱局取法时。各取法区分同干、透化神、见禄字等条件，以及狭义／广义拱合范围。 |
| `yangren_def`、`feiren_def` | 羊刃要换用只收阳干、十干禄前一辰或十干帝旺位的取法时；飞刃取 `feiren_def` 对应羊刃位的对冲支。两字段独立选择。 |
| `tianyi_def` | 庚与甲戊同组还是与辛同组，或要查阳贵／阴贵表时。阳贵／阴贵须显式选表，不随出生时刻自动切换。 |
| `wenchang_def` | 采用辛子还是辛戌的文昌表时。 |
| `taiji_def` | 壬癸都取巳申，还是壬取巳、癸取申时。 |
| `guoyin_def` | 采用禄位偏移七位还是八位的国印表时；表值与取锚分开选择。 |
| `peiou_xing_def` | 采用正财／正官，还是按阴阳干选择配偶星时。 |
| `tuwang_def` | 季月要用整月土旺，或按十二日／十八日分段时；算法与时间边界见下节。 |
| `hongyan_anchor` | 红艳要按年干而非默认日干查时；此字段支持年、日二选一。 |
| `tianyi_anchor` | 天乙要只按年干、只按日干，或分别按年日两干查时。 |
| `yima_anchor`、`huagai_anchor`、`jiangxing_anchor`、`jiesha_anchor`、`wangshen_anchor` | 驿马、华盖、将星、劫煞、亡神要只按日支查，而非默认分别按年日两支查时。各字段独立选择。 |
| `wenchang_anchor` | 文昌要只按日干查，而非默认分别按年日两干查时。 |
| `jinyu_anchor` | 金舆要从默认日干改为分别按年日两干查时。 |
| `zaisha_anchor` | 灾煞要从默认年支改为分别按年日两支查时。 |
| `taiji_anchor`、`guoyin_anchor` | 太极、国印要只按年干查，而非默认分别按年日两干查时。 |
| `kongwang_anchor` | 旬空要改用年柱，或分别按年日两柱的完整干支查时；配置示例见本页后文。 |

`Anchor.YEAR_AND_DAY` 表示分别查年、日两柱，不是把两柱合成一个条件。
各字段支持的选项不同，传入不支持的锚会抛 `ValueError`；能构造某个选项与该读法的文献依据是两回事，出处见上述 API 参考。
修改配置后须重建依赖它的命盘，见本页“替换一项配置”。

## 使用《命理探原》日锚预设

希望采用本库整理的日锚预设时，用 {py:meth}`~bazi.school.BaziSchool.mingli_tanyuan` 构造流派，再传给 `BaziConfig`：

```{testcode} config-school-preset
from bazi.school import BaziConfig, BaziSchool

school = BaziSchool.mingli_tanyuan()
config = BaziConfig(school=school)
print('天乙、驿马、文昌', school.tianyi_anchor.name, school.yima_anchor.name, school.wenchang_anchor.name)
print('羊刃取法未变', school.yangren_def is BaziSchool().yangren_def)
assert config.school is school
```

```{testoutput} config-school-preset
天乙、驿马、文昌 DAY DAY DAY
羊刃取法未变 True
```

与默认流派相比，天乙、驿马、华盖、将星、劫煞、亡神、文昌改为日锚。
金舆也显式取日干，但当前默认已经是日干；其余选项保持默认。该方法的 API 说明列出各锚的来源与限度。

## 月令五行状态与土旺口径

`chart.wuxing_states` 返回五行到旺、相、休、囚、死的冻结映射。状态类型是
{py:class}`~bazi.defines.wuxing.WuxingState`，也可从 `bazi.defines` 导入中文别名 `五行状态`。
它描述五行随出生月令变化的状态。

非季月按春木、夏火、秋金、冬水取本令；辰、未、戌、丑月由 `BaziSchool.tuwang_def` 选择：

| `TuwangDef` | 季月取法 |
| --- | --- |
| `WHOLE_MONTH`（默认） | 整月土旺，本库默认的简化取法。 |
| `AFTER_TWELVE_DAYS` | 开月节后十二日转土，此前按该季节本令。 |
| `BEFORE_EIGHTEEN_DAYS` | 下一四立前十八日转土，此前按该季节本令。 |

```{testcode} config-tuwang
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Wuxing
from bazi.school import BaziConfig, BaziPrecision, BaziSchool, TuwangDef

for definition in TuwangDef:
  config = BaziConfig(precision=BaziPrecision.MINUTE, school=BaziSchool(tuwang_def=definition))
  chart = BaziChart(Bazi.create('2026-04-17 12:00', 'male', config))
  print(definition.value, ' '.join(f'{element}{chart.wuxing_states[element]}' for element in Wuxing))
```

```{testoutput} config-tuwang
whole_month 木囚 火休 土旺 金相 水死
after_twelve_days 木囚 火休 土旺 金相 水死
before_eighteen_days 木旺 火相 土死 金囚 水休
```

真实节月的长短不同，后十二日与前十八日的阈值也会不同；上例在同一出生时刻得到不同状态。
十二日取法见《三命通会》卷二醉醒子段，十八日取法见《协纪辨方书》卷一。
具体出处见 {py:class}`~bazi.school.TuwangDef`。

分段的一天按连续24小时：先在后端东八区节气标签上加十二天或减十八天，得到转土阈值，
再将出生时间与阈值按本盘精度比较，相等归土旺。地点盘会把算出的阈值转换到同一真太阳钟后比较。
HKO 的节气数据只有日期精度，零点仅为占位。

此属性使用原局的出生时刻与月令。

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

默认路径使用上文的无时区标签，不做太阳时修正。要启用真太阳时，需要同时满足：

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
print(default_chart.bazi.config.precision, minute_chart.bazi.config.precision)
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
- 已创建的判别结果保留当时的输入配置，不会随新对象变化。
- `Bazi` 按值比较，`BaziChart` 按对象身份比较，换配置后两者都与原来的不等。

`BaziConfig()` 等于 `DEFAULT_CONFIG`，但不是同一个对象；`BaziConfig().school` 与 `DEFAULT_SCHOOL` 是同一个实例。

## 六甲旬空取锚

{py:attr}`~bazi.school.BaziSchool.kongwang_anchor` 默认取 `Anchor.DAY`，也支持 `YEAR` 与
`YEAR_AND_DAY`。它取完整干支，不只取日支；双锚分别保留年、日来源，即使两柱干支相同也不合并。
基础二支定义不决定取哪根柱，古籍查法与本库默认的出处边界见 {doc}`rule-coverage`。

```{testcode} kongwang-configuration
from bazi.school import Anchor, BaziConfig, BaziSchool

config = BaziConfig(school=BaziSchool(kongwang_anchor=Anchor.YEAR_AND_DAY))
assert config.school.kongwang_anchor is Anchor.YEAR_AND_DAY
assert BaziSchool().kongwang_anchor is Anchor.DAY
```

该字段参与命盘相等性与哈希。本库不提供命盘或前提判别记录的恢复、迁移接口；
需要结论时，用原输入和完整配置重新构造命盘。不传 `kongwang_anchor` 则使用默认日柱 `Anchor.DAY`，
所需读法为 `YEAR` 或 `YEAR_AND_DAY` 时需显式配置。旧调用的升级边界见 {doc}`../release-notes`。

## 术语索引

| 术语 | 在本库 API 里的含义 |
| --- | --- |
| 精度 `BaziPrecision` | 出生与节气比较的粒度：`DAY`、`HOUR`、`MINUTE` |
| 历法后端 `CalendarBackend` | 节气与干支历的数据来源：`hko`、`celestial`、`celestial-algo2` |
| 换日 `DayRollover` | 日柱在 23:00 还是 00:00 更换 |
| 起运年份 `DayunYearRule` | 大运年份标签的投影方式，不改变物理时刻 |
| 流派 `BaziSchool` | 换日、关系与神煞取法等分歧项的集合，每个字段都参与相等性 |
| 六甲旬空取锚 `kongwang_anchor` | 选择年柱、日柱或分别使用双锚 |
| 季月土旺 `tuwang_def` | 整季月土旺，或按交节后十二日／下一四立前十八日分段 |
| 真太阳时 | 由经度、民用偏移与均时差换算的钟；见 `Bazi.location_time` |
| `civil_timezone` | 出生地民用时区，仅在启用经度时使用 |

字段与枚举成员的完整说明由 API 参考生成，见 {py:class}`~bazi.school.BaziConfig`。
