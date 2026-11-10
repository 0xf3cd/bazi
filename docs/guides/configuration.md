# 配置与时间口径

本页说明出生时间怎么填、配置有哪些合法值，以及修改配置会改变什么。
`BaziConfig` 选择精度、历法后端和大运年份标记，`BaziSchool` 选择换日及各项流派取法。
先构造流派，再放进命盘配置，最后传给排盘入口：

```{testcode} config-create
from bazi.bazi import Bazi
from bazi.school import BaziConfig, BaziSchool, DayRollover

school = BaziSchool(day_rollover=DayRollover.ZIZHENG)
config = BaziConfig.from_values(precision='minute', backend='celestial', school=school)
bazi = Bazi.create('1995-08-03 23:30', 'male', config)
print('精度', bazi.config.precision)
print('日柱', bazi.day_pillar, '时柱', bazi.hour_pillar)
```

```{testoutput} config-create
精度 minute
日柱 丙寅 时柱 戊子
```

配置只表示你选择了哪一种口径，不判断哪一种更对。库没有替你选“最准确”的读法。

## 配置速查

构造器接收下表的枚举成员，导入路径列在各组前。`BaziConfig.from_values` 另外接受精度、后端与大运年份规则的字符串，
如上例；`school` 仍须传 `BaziSchool`。省略字段时采用“默认”列，不会替你判断哪个流派更合适。

### 命盘配置 `BaziConfig`

`BaziConfig`、`BaziPrecision`、`BaziSchool`、`DayunYearRule` 从 `bazi.school` 导入，
`CalendarBackend` 从 `bazi.calendar.backend` 导入。

| 字段 | 类型 | 可选成员 | 默认成员／值 | 影响 |
| --- | --- | --- | --- | --- |
| `precision` | `BaziPrecision` | `DAY`、`HOUR`、`MINUTE` | `DAY` | 出生时刻与节气比较的粒度；小时仍用于时柱。 |
| `backend` | `CalendarBackend` | `HKO`、`CELESTIAL`、`CELESTIAL_ALGO2` | `CELESTIAL` | 历法数据来源；HKO 只能配合 DAY。 |
| `school` | `BaziSchool` | `BaziSchool` 实例 | `DEFAULT_SCHOOL` | 下列流派字段的集合。 |
| `dayun_year_rule` | `DayunYearRule` | `JIE_PROJECTED`、`FIXED_DECADE` | `JIE_PROJECTED` | 大运年份标签，不改变物理交运时刻。 |

### 流派取法 `BaziSchool`

`DayRollover`、`PeiouXingDef`、`TuwangDef` 从 `bazi.school` 导入，
`DizhiRules`、`ShenshaRules` 从 `bazi.rules` 导入。表中类型后的成员均使用该类型，例如 `ShenshaRules.WenchangDef.XIN_XU`。

| 字段 | 类型 | 可选成员 | 默认成员 | 影响 |
| --- | --- | --- | --- | --- |
| `day_rollover` | `DayRollover` | `WAN_ZISHI`、`ZIZHENG` | `WAN_ZISHI` | 23:00 或 00:00 换日柱。 |
| `anhe_def` | `DizhiRules.AnheDef` | `NORMAL`、`NORMAL_EXTENDED`、`MANGPAI` | `NORMAL_EXTENDED` | 暗合组合。 |
| `xing_def` | `DizhiRules.XingDef` | `STRICT`、`LOOSE` | `LOOSE` | 三刑须三支齐现，或三取二也成立。 |
| `gong_def` | `DizhiRules.GongDef` | `SAME_STEM_NARROW`、`SAME_STEM_WIDE`、`TRANSFORMING_NARROW`、`LU_NARROW` | `SAME_STEM_NARROW` | 拱局的同干、化神、禄字及结构范围条件。 |
| `yangren_def` | `ShenshaRules.YangrenDef` | `ZIPING`、`LUMING`、`DIWANG` | `ZIPING` | 羊刃取法。 |
| `feiren_def` | `ShenshaRules.YangrenDef` | `ZIPING`、`LUMING`、`DIWANG` | `ZIPING` | 以所选羊刃位的对冲支取飞刃，独立于上一字段。 |
| `tianyi_def` | `ShenshaRules.TianyiDef` | `GENG_WITH_JIA_WU`、`GENG_WITH_XIN`、`YANGGUI`、`YINGUI` | `GENG_WITH_JIA_WU` | 庚的分组或显式阳贵／阴贵表，不按出生时刻自动选表。 |
| `wenchang_def` | `ShenshaRules.WenchangDef` | `XIN_ZI`、`XIN_XU` | `XIN_ZI` | 辛取子或辛取戌。 |
| `taiji_def` | `ShenshaRules.TaijiDef` | `REN_GUI_BOTH`、`REN_SI_GUI_SHEN` | `REN_GUI_BOTH` | 壬癸都取巳申，或壬取巳、癸取申。 |
| `guoyin_def` | `ShenshaRules.GuoyinDef` | `WUXING_JINGJI`、`MODERN` | `MODERN` | 禄位偏移七位或八位。 |
| `peiou_xing_def` | `PeiouXingDef` | `ZHENGCAI_ZHENGGUAN`、`YINYANGGAN` | `ZHENGCAI_ZHENGGUAN` | 正财／正官或按阴阳干选配偶星。 |
| `tuwang_def` | `TuwangDef` | `WHOLE_MONTH`、`AFTER_TWELVE_DAYS`、`BEFORE_EIGHTEEN_DAYS` | `WHOLE_MONTH` | 季月整月土旺，或按十二日／十八日分段。 |

### 神煞查法依据的柱位

`Anchor` 从 `bazi.school` 导入。`YEAR_AND_DAY` 表示分别查年、日两柱，不把两柱合成一个条件。
各字段只接受本行列出的成员；不能把所有 `Anchor` 值用于每个字段。

| 字段 | 类型 | 可选成员 | 默认成员 | 依据 |
| --- | --- | --- | --- | --- |
| `hongyan_anchor` | `Anchor` | `YEAR`、`DAY` | `DAY` | 年干或日干。 |
| `tianyi_anchor` | `Anchor` | `YEAR`、`DAY`、`YEAR_AND_DAY` | `YEAR_AND_DAY` | 年干、日干或分别查两干。 |
| `yima_anchor` | `Anchor` | `DAY`、`YEAR_AND_DAY` | `YEAR_AND_DAY` | 日支或分别查年日支。 |
| `huagai_anchor` | `Anchor` | `DAY`、`YEAR_AND_DAY` | `YEAR_AND_DAY` | 日支或分别查年日支。 |
| `jiangxing_anchor` | `Anchor` | `DAY`、`YEAR_AND_DAY` | `YEAR_AND_DAY` | 日支或分别查年日支。 |
| `jiesha_anchor` | `Anchor` | `DAY`、`YEAR_AND_DAY` | `YEAR_AND_DAY` | 日支或分别查年日支。 |
| `wangshen_anchor` | `Anchor` | `DAY`、`YEAR_AND_DAY` | `YEAR_AND_DAY` | 日支或分别查年日支。 |
| `jinyu_anchor` | `Anchor` | `DAY`、`YEAR_AND_DAY` | `DAY` | 日干或分别查年日干。 |
| `zaisha_anchor` | `Anchor` | `YEAR`、`YEAR_AND_DAY` | `YEAR` | 年支或分别查年日支。 |
| `wenchang_anchor` | `Anchor` | `DAY`、`YEAR_AND_DAY` | `YEAR_AND_DAY` | 日干或分别查年日干。 |
| `taiji_anchor` | `Anchor` | `YEAR`、`YEAR_AND_DAY` | `YEAR_AND_DAY` | 年干或分别查年日干。 |
| `guoyin_anchor` | `Anchor` | `YEAR`、`YEAR_AND_DAY` | `YEAR_AND_DAY` | 年干或分别查年日干。 |
| `kongwang_anchor` | `Anchor` | `YEAR`、`DAY`、`YEAR_AND_DAY` | `DAY` | 年柱、日柱或分别查完整两柱干支。 |

这些表列合法配置，不把默认值当作文献结论；具体读法和出处见 {doc}`rule-coverage` 与
{py:class}`~bazi.school.BaziSchool`。`longitude` 和 `civil_timezone` 则是 `Bazi.create` 的出生入口参数，
不属于配置字段，见{ref}`真太阳时输入 <configuration-location>`。

## 出生时间怎么填

不传 `longitude` 时，`Bazi.create` 接收无时区 `datetime` 或等价字符串，不从中推断地点或时区：

- **年月柱**按选定精度，将输入标签与东八区（UTC+8）的节气表比较。默认示例因此按东八区公历钟填写。
- **日柱、时柱**按输入标签的日时读取，再应用所选换日点；即使使用 `DAY`，小时也没有被丢弃。
- **起运与流运**同样使用东八区参考标签；默认盘的 `reference_datetime` 就是输入钟时，不另作时区换算。

非 UTC+8 地区的当地民用标签不能直接当作东八区标签，夏令时也不会由默认入口补算。
若选择按北京时间排盘，先换为 UTC+8，再去掉时区交给默认入口；这样日时柱也会按北京时间读取，
不再保留当地民用钟。需要真太阳时则使用{ref}`地点盘 <configuration-location>`，它会修正日时所读的钟。

**当前没有“保留当地民用钟、按物理节界归年月、但不作太阳时修正”的对应入口。**
不要只把带时区输入的 `tzinfo` 去掉，也不要把时区转换和真太阳时当成等价操作。

## 选择节气比较精度

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

## 海外出生时间与夏令时

以下使用纽约冬令时与夏令时的当地钟各一例。可以换成东八区钟排盘，或显式启用经度 −74 的真太阳时。
经度只作演示，不对应真实个人。
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
  reference_label = civil.astimezone(utc8).replace(tzinfo=None)
  cases = (
    ('东八区标签', reference_label, None),
    ('地点盘真太阳时', civil, -74),
  )
  for label, birth, longitude in cases:
    bazi = Bazi.create(birth, 'male', config, longitude=longitude)
    print(label, ' '.join(map(str, bazi.pillars)))
```

```{testoutput} config-overseas
当地民用钟 2000-02-04T08:30:00-05:00
东八区标签 庚辰 戊寅 壬辰 辛亥
地点盘真太阳时 庚辰 戊寅 壬辰 甲辰
当地民用钟 2000-08-07T01:04:00-04:00
东八区标签 庚辰 甲申 丁酉 丁未
地点盘真太阳时 庚辰 甲申 丁酉 庚子
```

这两个瞬间均已过相应物理节界，两条合法路径的年月柱一致，时柱按各自所用的钟读取。
不要直接对当地时间调用 `replace(tzinfo=None)` 后交给默认入口：它会把纽约钟误当东八区钟，
例中甚至会归到旧年月。时区换算与真太阳时修正是不同操作。

## 历法后端：节气数据从哪里来

`CalendarBackend` 选择历法数据。`celestial` 是默认，也是文档推荐的选择；
`hko` 基于香港天文台数据，只有日期级精度，所以只能配合 `DAY`；
`celestial-algo2` 采用第二套阴历算法，199 个支持年份中有 6 年与 `celestial` 不同。
差异的来源和范围见 {py:class}`~bazi.calendar.backend.CalendarBackend`。

`HOUR` 或 `MINUTE` 需要真实的节气时刻，因此和 `hko` 组合会被拒绝（`ValueError`）。

```{testcode} config-backend
from bazi.bazi import Bazi
from bazi.school import BaziConfig

config = BaziConfig.from_values(backend='hko')
bazi = Bazi.create('1990-05-17 10:30', 'female', config)
print(bazi.config.backend, ' '.join(map(str, bazi.pillars)))
```

```{testoutput} config-backend
hko 庚午 辛巳 壬午 乙巳
```

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

## 使用《命理探原》日锚预设

希望采用本库整理的日锚预设时，用 {py:meth}`~bazi.school.BaziSchool.mingli_tanyuan` 构造流派，再传给 `BaziConfig`：

```{testcode} config-school-preset
from bazi.analyzer.relationship import RelationshipAnalyzer
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.school import BaziConfig, BaziSchool

school = BaziSchool.mingli_tanyuan()
config = BaziConfig(school=school)
print('天乙、驿马、文昌', school.tianyi_anchor.name, school.yima_anchor.name, school.wenchang_anchor.name)
chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female', config))
found = RelationshipAnalyzer(chart).at_birth.shensha['tianyi']
print('天乙贵人', ' '.join(map(str, sorted(found, key=lambda branch: branch.index))))
```

```{testoutput} config-school-preset
天乙、驿马、文昌 DAY DAY DAY
天乙贵人 巳
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

## 选择大运年份的标记方式

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

(configuration-location)=
## 按真太阳时排盘

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
带时区却不给经度、有经度却没有时区，或地点盘使用 DAY 精度，均在创建时抛 `ValueError`。
本入口不接受纬度参数。完整输入与错误条件见 {py:meth}`~bazi.bazi.Bazi.create`。

## 替换一项配置

`BaziConfig` 和 `BaziSchool` 都是 frozen dataclass，不能原地修改。要换一项，用 `dataclasses.replace` 得到新对象；
原对象和默认对象保持不变。

```{testcode} config-replace
from dataclasses import replace
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.rules import ShenshaRules
from bazi.school import BaziConfig, BaziPrecision, BaziSchool

base = BaziConfig(school=BaziSchool.mingli_tanyuan())
minute = replace(base, precision=BaziPrecision.MINUTE)
changed = replace(minute, school=replace(minute.school, wenchang_def=ShenshaRules.WenchangDef.XIN_XU))
print('天乙锚、文昌表', changed.school.tianyi_anchor.name, changed.school.wenchang_def.name)

birth = datetime(2000, 2, 4, 20, 0)
for config in (base, changed):
  chart = BaziChart(Bazi.create(birth, 'male', config))
  print(config.precision, ' '.join(map(str, chart.bazi.pillars)))
```

```{testoutput} config-replace
天乙锚、文昌表 DAY XIN_XU
day 庚辰 戊寅 壬辰 庚戌
minute 己卯 丁丑 壬辰 庚戌
```

配置属于 `Bazi` 本身，所以换了配置就要重新生成依赖它的对象：

- 新的 `Bazi`，再包成新的 `BaziChart`；`TransitChart` 和 `RelationshipAnalyzer` 也持有原来的命盘，需要对新命盘重建。
- 已创建的判别结果保留当时的输入配置，不会随新对象变化。
- 要修改已选流派中的一项，用 `replace(config.school, 字段=成员)`，如上例；重新构造默认 `BaziSchool` 会重置其他选择。

拷贝、相等与共享的精确约定见 {doc}`../api-contract`。

## 按年柱、日柱或两柱查旬空

{py:attr}`~bazi.school.BaziSchool.kongwang_anchor` 默认取 `Anchor.DAY`，也支持 `YEAR` 与
`YEAR_AND_DAY`。它取完整干支，不只取日支；双锚分别保留年、日来源，即使两柱干支相同也不合并。
基础二支定义不决定取哪根柱，古籍查法与本库默认的出处边界见 {doc}`rule-coverage`。

```{testcode} kongwang-configuration
from bazi.analyzer.relationship import RelationshipAnalyzer
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.school import Anchor, BaziConfig, BaziSchool

for anchor in (Anchor.YEAR, Anchor.DAY, Anchor.YEAR_AND_DAY):
  config = BaziConfig(school=BaziSchool(kongwang_anchor=anchor))
  chart = BaziChart(Bazi.create('1984-03-29 12:00', 'male', config))
  for result in RelationshipAnalyzer(chart).at_birth.kongwang:
    branches = sorted(result.xunkong, key=lambda branch: branch.index)
    print(anchor.name, result.anchor, result.ganzhi, ' '.join(map(str, branches)))
```

```{testoutput} kongwang-configuration
YEAR 年 甲子 戌 亥
DAY 日 壬戌 子 丑
YEAR_AND_DAY 年 甲子 戌 亥
YEAR_AND_DAY 日 壬戌 子 丑
```

该字段参与命盘相等性与哈希。本库不提供命盘或前提判别记录的恢复、迁移接口；
需要结论时，用原输入和完整配置重新构造命盘。不传 `kongwang_anchor` 则使用默认日柱 `Anchor.DAY`，
所需读法为 `YEAR` 或 `YEAR_AND_DAY` 时需显式配置。旧调用的升级边界见 {doc}`../release-notes`。

双锚例子依次保留年柱和日柱的旬空二支。继续读取命中位置，见 {doc}`relations-transits`。
