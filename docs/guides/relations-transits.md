# 关系与流运

本页先查询流运，再用原局或所选流运查关系、神煞、通根与透干。
结果是结构事实，描述“哪些干支落在哪些位置、满足哪种关系”，不是对事件的预测。

## 查年、月、日或时刻的流运

`TransitChart` 接收 `BaziChart`，返回指定坐标下的 `TransitSet`。下面显式使用 `minute` 精度，
使四种入口都支持；默认 `DAY` 命盘不支持 `at_moment()`。
所有出生输入和日期／时刻查询都按东八区参考钟填写，地点盘的流运查询也不改用真太阳钟。

```{testcode} transits-query
from datetime import date, datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Dizhi
from bazi.school import BaziConfig
from bazi.transit_chart import TransitChart

config = BaziConfig.from_values(precision='minute')
chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female', config))
transits = TransitChart(chart)
queries = (
  ('年', transits.at_year(2024)),
  ('月', transits.at_month(2024, Dizhi.午)),
  ('日', transits.at_date(date(2024, 6, 15))),
  ('时刻', transits.at_moment(datetime(2024, 6, 15, 12))),
)
for label, result in queries:
  if result is not None:
    print(label, ' '.join(f'{kind.value}:{ganzhi}' for kind, ganzhi in result.items))
```

```{testoutput} transits-query
年 dayun:丁丑 liunian:甲辰
月 dayun:丁丑 liunian:甲辰 liuyue:庚午
日 dayun:丁丑 liunian:甲辰 liuyue:庚午 liuri:庚戌
时刻 dayun:丁丑 liunian:甲辰 liuyue:庚午 liuri:庚戌
```

本例各查询均能取得结果，但参数和边界各不相同：

| 入口 | 参数含义 | 查询层级及 `None` 的含义 |
| --- | --- | --- |
| `at_year(gz_year)` | 干支年标签，以年份数字填写 | 返回该年流年及可取得的小运／大运；早于出生干支年为 `None`，远年份仍可有流年。大运按所选年份标签解释。 |
| `at_month(gz_year, gz_month)` | 干支年和月份地支，如 `Dizhi.午` | 增加流月；出生干支月前或节令表范围外为 `None`，大运按物理交运月边界解释。午月不等于公历六月。 |
| `at_date(solar_date)` | 东八区公历 `date`，不能传 `datetime` | 增加流月、流日；出生公历日前或历法范围外为 `None`，大运按物理交运日边界解释。 |
| `at_moment(solar_moment)` | 东八区无时区 `datetime` | 返回流年、流月、流日及可取得的小运／大运，不增加流时。出生前、节令表范围外或配置不支持为 `None`；须用 celestial 系后端及 HOUR／MINUTE 精度。 |

`None` 是整次查询不可取得；返回结果中某种流运的字段为 `None`，则只是缺这一层。
流运种类从 `bazi.transits` 导入 `TransitKind`；例如 `result.select(TransitKind.LIUNIAN)` 只保留流年，
所选种类有缺项时抛 `ValueError`。`at_moment` 按秒比较，流日应用所选换日点，可能与同公历日的 `at_date` 不同。
完整时间与类型边界见 {py:class}`~bazi.transit_chart.TransitChart`。

## 列出几步大运和流年

大运生成器有限，流年生成器无限。用 `islice` 限定要读的数量，不要直接把 `chart.liunian` 转成 `list` 或 `tuple`：

```{testcode} transits-generators
from itertools import islice

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
for step in islice(chart.dayun, 2):
  print('大运', step.ganzhi_year, step.ganzhi, step.start_moment.date(), step.end_moment.date())
for step in islice(chart.liunian, 3):
  print('流年', step.ganzhi_year, step.ganzhi)
print('小运', [(step.xusui, str(step.ganzhi)) for step in chart.xiaoyun[:2]])
```

```{testoutput} transits-generators
大运 1994 庚辰 1994-02-23 2004-02-23
大运 2004 己卯 2004-02-23 2014-02-23
流年 1990 庚午
流年 1991 辛未
流年 1992 壬申
小运 [(1, '甲辰'), (2, '癸卯')]
```

每步大运覆盖 `[start_moment, end_moment)`，年份是标签，不表示占据整个标签年；规则见 {doc}`configuration`。
每次访问 `dayun`／`liunian` 都新建生成器，从头开始读取。把生成器保存到变量后，继续遍历这个变量会从上次位置接着读。
大运数量取决于后端支持范围。
`xiaoyun` 则是缓存元组，可反复遍历。排成流运文字的例子在本页{ref}`流运文本 <transits-text>`。

后续按任务选择：原局关系看下节，神煞看{ref}`原局神煞 <relations-shensha>`，
原局与流运的关系看{ref}`流运关系 <relations-transit-house>`，按位置查全部关系看{ref}`跨组位置 <relations-positions>`。

## 原局日主关系：按天干值汇总

{py:attr}`~bazi.analyzer.relationship.AtBirthAnalysis.day_master_relations` 比较日主与年、月、时的明干，
返回关系到天干组合元组的冻结映射：

```{testcode} relations-day-master
from bazi.analyzer.relationship import RelationshipAnalyzer
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
print('四柱', ' '.join(map(str, chart.bazi.pillars)))
found = RelationshipAnalyzer(chart).at_birth.day_master_relations
for relation, combos in found.items():
  print(relation, [''.join(map(str, sorted(combo, key=lambda stem: stem.index))) for combo in combos])
```

```{testoutput} relations-day-master
四柱 庚午 辛巳 壬午 乙巳
生 ['庚壬', '辛壬', '乙壬']
```

每个组合是无序的 `frozenset`：庚生壬与壬生乙都归在“生”下，集合自身不保存方向。
它也不携带柱位，同一对干在多柱出现时合并；排序只用于显示，不能读成生克方向。
需要有向判断时用 {py:func}`~bazi.utils.tiangan_utils.sheng`／{py:func}`~bazi.utils.tiangan_utils.ke`；
需要按柱位比较时由 `chart.bazi.four_tiangans` 取年、月、日、时干，各柱十神见 `chart.shishen`。
配偶星证据中的 `stem_relations` 仅覆盖含配偶星目标干的明干组合，不是通用的日主关系接口。

## 六甲旬空：先选结果，再查柱位

只需要命中了哪些地支时，读取分析层的 `shensha['kongwang']`，结果是地支并集。
需要知道“依据哪根柱查得、命中哪个位置”时，使用
{py:attr}`~bazi.analyzer.relationship.AtBirthAnalysis.kongwang` 或
{py:meth}`~bazi.analyzer.relationship.TransitAnalysis.kongwang`。下面把年柱和日柱分别作为查法依据，
先查原局，再查传入的大运与流年：

```{testcode} kongwang-details
from bazi.analyzer.relationship import RelationshipAnalyzer
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Ganzhi
from bazi.school import Anchor, BaziConfig, BaziSchool
from bazi.transits import TransitSet

chart = BaziChart(
  Bazi.create(
    '1984-03-29 12:00',
    'male',
    BaziConfig(school=BaziSchool(kongwang_anchor=Anchor.YEAR_AND_DAY)),
  ),
)
analyzer = RelationshipAnalyzer(chart)
for result in analyzer.at_birth.kongwang:
  print(
    str(result.anchor),
    str(result.ganzhi),
    sorted(map(str, result.xunkong)),
    [(str(hit.position), str(hit.ganzhi)) for hit in result.hits],
  )

transits = TransitSet(
  dayun=Ganzhi.from_str('甲戌'),
  liunian=Ganzhi.from_str('甲戌'),
)
for result in analyzer.transits.kongwang(transits):
  print(
    str(result.anchor),
    [(hit.position.value, str(hit.ganzhi)) for hit in result.hits],
  )
```

```{testoutput} kongwang-details
年 甲子 ['亥', '戌'] [('日', '壬戌')]
日 壬戌 ['丑', '子'] [('年', '甲子')]
年 [('dayun', '甲戌'), ('liunian', '甲戌')]
日 []
```

第一行表示：年柱甲子所属旬的空亡二支为亥、戌，原局日柱壬戌命中戌。
流运例中，大运和流年虽然同为甲戌，仍分别保留两次命中；以日柱为依据的结果没有命中，仍返回一条记录。

| 字段 | 读法 |
| --- | --- |
| `anchor`、`ganzhi` | 查法依据的柱位（`Zhu.年`／`Zhu.日`）及其完整干支 |
| `xunkong` | 依据该干支查得的旬空二支，类型为 `frozenset[Dizhi]` |
| `hits` | 每项保留目标的完整 `ganzhi`；`position` 是原局柱位 `Zhu` 或流运种类 `TransitKind` |

原局查询排除作为依据的那根柱；流运查询只用本命年／日柱查传入流运，不反向以流运查原局。
同支不同柱、同干支不同流运种类、同值的年日双锚均分别保留。这里只记录原始命中，不删除目标地支，
不以冲合刑取消命中，也不改变五行、十神、纳音或其他关系；出空、填实、吉凶、单支筛选、截路及四大空亡均不在此接口中判断。

若已持有干支，只需做一次低层查表，使用 {py:func}`~bazi.utils.shensha_utils.xunkong` 返回旬空二支，
或用 {py:func}`~bazi.utils.shensha_utils.kongwang` 检查某目标支。两者要求查法依据是合法六十甲子，
目标只按地支判断，不附加天干或纳音条件。阴阳不配的依据会被拒绝，但 `Ganzhi` 自身的构造范围不变。

配偶星的 `StarAppearance` 同样用 `position` 区分原局柱位与流运种类；`layer` 为
`TianganLayer.明干`／`TianganLayer.藏干`。这两个类型从 `bazi.defines` 导入，中文类别名分别为
`柱` 和 `天干层次`。打印原局柱位 `Zhu` 或明藏层 `TianganLayer` 用 `str(value)` 取得中文值，
不依赖枚举的 repr；流运种类 `TransitKind` 用 `.value` 取得 `dayun`、`liunian` 等标签。

(relations-shensha)=
## 原局神煞与中文名

{py:data}`~bazi.analyzer.relationship.SHENSHA_LABELS` 保存支集神煞的22个名称，
{py:data}`~bazi.analyzer.relationship.WHOLE_PILLAR_SHENSHA_LABELS` 保存魁罡、天赦两个整柱名称。
两表均从 `relationship` 模块导入；整柱结果是完整日柱或 `None`。

```{testcode} relations-shensha-labels
from bazi.analyzer.relationship import (
  RelationshipAnalyzer, SHENSHA_LABELS, WHOLE_PILLAR_SHENSHA_LABELS,
)
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
result = RelationshipAnalyzer(chart).at_birth.shensha
for key, label in SHENSHA_LABELS.items():
  branches = result[key]
  if branches:
    print(label, ''.join(map(str, sorted(branches, key=lambda branch: branch.index))))
for key, label in WHOLE_PILLAR_SHENSHA_LABELS.items():
  print(label, result[key] or '无')
```

```{testoutput} relations-shensha-labels
飞刃 午
天乙贵人 巳
将星 午
亡神 巳
太极贵人 巳
魁罡 无
天赦 无
```

支集结果按地支值汇总，不区分同支的不同柱。旬空需要逐锚和位置时用上文的 `kongwang`。

(relations-transit-house)=
## 查流运与婚姻宫的关系

`TransitChart` 按干支年、月、日期或时刻返回一个 `TransitSet`；`RelationshipAnalyzer` 对它做关系查询。
下面取 2024 年的流运，查它与婚姻宫的地支关系。

```{testcode} relations-house
from datetime import datetime

from bazi.analyzer.relationship import RelationshipAnalyzer
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
year = TransitChart(chart).at_year(2024)
assert year is not None

print([str(ganzhi) for ganzhi in year.ganzhis])
print([kind.value for kind in year])
print([str(ganzhi) for ganzhi in year.select(TransitKind.LIUNIAN).ganzhis])

found = RelationshipAnalyzer(chart).transits.house_relations(year)
for relation, combos in found.items():
  for combo in combos:
    print(relation, ''.join(str(dizhi) for dizhi in sorted(combo, key=lambda dizhi: dizhi.index)))
```

```{testoutput} relations-house
['丁丑', '甲辰']
['dayun', 'liunian']
['甲辰']
害 丑午
生 丑午
生 辰午
```

几点读法：

- `at_year` 在出生年之前返回 `None`，所以先判断再用。返回的 `TransitSet` 只含当前有的种类（这里是大运和流年），
  缺项就是 `None`。`select` 要求指定种类全部存在，缺项抛 `ValueError`。
- `TransitKind` 是流运种类的枚举，成员值是英文小写的拼音；`year.items` 按固定顺序给出种类与干支对。
- 关系的键是 `DizhiRelation` 成员，可用中文别名，如 `DizhiRelation.害`。
- 每个组合是一个 `frozenset` 的地支，不带次序，所以示例先按枚举序排序再打印。
  各关系的取法与流派定义看 {py:class}`~bazi.school.BaziSchool` 和 {py:class}`~bazi.defines.relations.DizhiRelation`。
- 结果不可变；需要另一组流运时重新查询或选择。精确约定见 {doc}`../api-contract`。

地支低层批量查法见 {py:func}`~bazi.utils.dizhi_utils.discover`。查自刑要保留输入地支的重复次数，
不能先转成集合再查；方向、按值合并与按位置保留是不同结果，不相互替代。

(relations-positions)=
## 全部跨组地支关系：保留具体位置

`house_relations` 只查婚姻宫，且按地支值汇总。要查全部原局与所选流运之间的关系，使用
{py:meth}`~bazi.analyzer.relationship.TransitAnalysis.all_relations`：

```{testcode} relations-all-positions
from bazi.analyzer.relationship import RelationshipAnalyzer
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import DizhiRelation
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
year = TransitChart(chart).at_year(2020)
assert year is not None
found = RelationshipAnalyzer(chart).transits.all_relations(year.select(TransitKind.LIUNIAN))
for combo in found[DizhiRelation.冲]:
  print(sorted(f'{item.position.value}:{item.ganzhi}' for item in combo))
```

```{testoutput} relations-all-positions
['liunian:庚子', '年:庚午']
['liunian:庚子', '日:壬午']
```

原局年、日两处午分别与流年子冲，不因同支合并。返回冻结映射 `RelationPositionDiscovery`，
键是 `DizhiRelation`，值是 `tuple[frozenset[RelationParticipant], ...]`；参与者记录 `position` 和完整 `ganzhi`。
原局位置用 `Zhu`，流运位置用 `TransitKind`。每个组合两侧都有参与者，不包含纯原局或纯流运组合。
三支关系和拱局仍按本盘流派判断；结果顺序与低层 `discover_mutual_ganzhis` 一致，只把序号换成位置。

## 通根与透干：明藏匹配事实

{py:func}`~bazi.analyzer.facts.tonggen` 查目标干在原局与所选流运藏干中的匹配，默认同五行；同五行包括同干，
`TianganMatch.SAME_TIANGAN` 则只取同干。返回 `TianganOccurrence` 元组，每条记录的 `position` 是位置，
`ganzhi` 是完整干支，`stem` 是匹配的实际藏干。

{py:func}`~bazi.analyzer.facts.tougan` 的 `target` 是要查的实际藏干，先按同干找到它，再按显式
`condition` 匹配明干。省略条件会抛 `TypeError`；未找到目标藏干就不返回透干记录。
返回 `TouganHit` 元组，每条分 `hidden`（藏干端）和 `visible`（明干端），两端都是 `TianganOccurrence`。

```{testcode} relations-tonggen-tougan
from bazi.analyzer.facts import TianganMatch, tonggen, tougan
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Tiangan
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
year = TransitChart(chart).at_year(2024)
assert year is not None
transits = year.select(TransitKind.LIUNIAN)
for root in tonggen(chart, Tiangan.甲, transits):
  print('根', root.position.value, root.ganzhi, root.stem)
print('严格同干', tonggen(chart, Tiangan.甲, transits, condition=TianganMatch.SAME_TIANGAN))
for hit in tougan(chart, Tiangan.癸, transits, condition=TianganMatch.SAME_WUXING):
  print('藏', hit.hidden.position.value, hit.hidden.ganzhi, hit.hidden.stem,
        '明', hit.visible.position.value, hit.visible.ganzhi, hit.visible.stem)
print('同干透出', tougan(chart, Tiangan.癸, transits, condition=TianganMatch.SAME_TIANGAN))
```

```{testoutput} relations-tonggen-tougan
根 liunian 甲辰 乙
严格同干 ()
藏 liunian 甲辰 癸 明 日 壬午 壬
同干透出 ()
```

辰藏乙与甲同五行，严格同干则不匹配。辰中癸与日干壬同五行，结果两端仍分别是癸、壬。
例中的 `position.value` 在原局给出中文柱位，在流运给出种类标签。

不传 `transits` 只查原局；传入后，原局和所选流运共同参与，两端可在任一侧，也保留同柱匹配。
位置先按年、月、日、时，随后按小运、大运、流年、流月、流日排列，只取实际传入的流运。
通根在每个位置按 {py:attr}`~bazi.rules.BaziRules.HIDDEN_TIANGANS` 表顺序返回，透干按藏干位置优先、
明干位置次序返回；相同干支的不同位置不合并，结果不可变。

两种条件都以藏干表为依据，乙逢午、丁逢酉的阴长生根不在查询范围内。

(transits-text)=
## 把流运排成文本
需要的是文字而不是对象时，`bazi.chart_text.transit_text` 把节、交运时间、大运、小运和流年排好。
流年可以无限延续，所以数量由你给：`dayun_count` 取前几步大运，`liunian_count` 取从出生干支年起的几年，默认分别是 10 和 100。
小运是有限的，全部列出。

```{testcode} transits-text
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.chart_text import transit_text

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
print(transit_text(chart, dayun_count=2, liunian_count=10).strip())
```

```{testoutput} transits-text
出生时刻前一节：立夏 - 1990-05-06T02:35:27
出生时刻后一节：芒种 - 1990-06-06T06:46:19
大运数节依据（逆排）：立夏 - 1990-05-06T02:35:27
交运时间： 1994-02-23T20:46:55

大运：            天干                 地支                 地支藏干
1994年标签：       庚 [阳金] <偏印>     辰 [阳土] <七杀>    戊 [阳土] <杀> 乙 [阴木] <伤> 癸 [阴水] <劫>
               -- 公历区间：1994-02-23 20:46 ～ 2004-02-23 20:46
               -- 纳音：白蜡金  -- 十二长生：墓

2004年标签：       己 [阴土] <正官>     卯 [阴木] <伤官>    乙 [阴木] <伤>
               -- 公历区间：2004-02-23 20:46 ～ 2014-02-23 20:46
               -- 纳音：城头土  -- 十二长生：死

小运：
1岁-甲辰  2岁-癸卯  3岁-壬寅  4岁-辛丑  5岁-庚子

流年：
1990-庚午  1991-辛未  1992-壬申  1993-癸酉  1994-甲戌  1995-乙亥  1996-丙子  1997-丁丑  1998-戊寅  1999-己卯
```

地点盘的节与大运区间仍用节气表时刻，文本会注明这一点，不采用真太阳时。

## 范围提醒

- 月、日期和时刻查询按东八区无时区标签和物理节气边界；`at_moment` 还要求 `celestial` 系后端和 `HOUR` / `MINUTE` 精度，否则返回 `None`。
- `at_year` 在出生年之前返回 `None`，远年份仍可返回流年，不能用它的 `None` 判断历法表上界。月、日期与时刻查询不满足各自支持范围时返回 `None`；类型与取值校验另见各入口的 API 说明。
- 这里的关系、神煞与明藏匹配只说明“在所选流派或匹配条件下，这些干支满足了某个结构条件”，不是旺衰、格局或某件事会不会发生。
  要看某条知识条目的前提在这张盘上是否成立，见 {doc}`knowledge`。
