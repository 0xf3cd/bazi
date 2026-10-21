# 关系与流运

本页先查询六甲旬空，再选取某一年的流运，查它与原局婚姻宫的地支关系；最后从命盘读取有限几步大运和流年。
结果是结构事实，描述“哪些干支落在哪些位置、满足哪种关系”，不是对事件的预测。

## 六甲旬空：保留取锚依据与目标位置

低层 {py:func}`~bazi.utils.shensha_utils.xunkong` 接收合法六十甲子的完整锚并返回冻结二支，
{py:func}`~bazi.utils.shensha_utils.kongwang` 检查某目标支。阴阳不配的锚会被拒绝，
但不改变 `Ganzhi` 本身允许构造干支组合的合同。目标只按地支判断，不附加天干或纳音条件。

分析层的 `shensha['kongwang']` 是命中地支的并集。要看依据哪一锚、命中哪个位置，使用
{py:attr}`~bazi.analyzer.relationship.AtBirthAnalysis.kongwang` 或
{py:meth}`~bazi.analyzer.relationship.TransitAnalysis.kongwang`。逐锚结果的 `anchor` 是年／日来源，
`ganzhi` 为完整锚，`xunkong` 为该旬二支；`hits` 中每项保留原局柱位或流运种类及完整目标干支。

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
    result.anchor,
    str(result.ganzhi),
    sorted(map(str, result.xunkong)),
    [(hit.pillar, str(hit.ganzhi)) for hit in result.hits],
  )

transits = TransitSet(
  dayun=Ganzhi.from_str('甲戌'),
  liunian=Ganzhi.from_str('甲戌'),
)
for result in analyzer.transits.kongwang(transits):
  print(
    result.anchor,
    [(hit.kind.value, str(hit.ganzhi)) for hit in result.hits],
  )
assert analyzer.transits.shensha(transits)['kongwang'] == frozenset(
  hit.ganzhi.dizhi for result in analyzer.transits.kongwang(transits) for hit in result.hits
)
```

```{testoutput} kongwang-details
year 甲子 ['亥', '戌'] [('day', '壬戌')]
day 壬戌 ['丑', '子'] [('year', '甲子')]
year [('dayun', '甲戌'), ('liunian', '甲戌')]
day []
```

原局排除锚自身柱；流运只用本命锚查流运支，不反向查询。无命中仍保留二支；同支不同柱、
同干支不同流运种类、同值的年日双锚均不合并。这里只标原始命中，不删除地支，不以冲合刑取消，
不改变五行、十神、纳音或其他关系，也不判断出空、填实与吉凶。单支筛选、截路、四大空亡未在此接口实现。

## 查一年的流运和一个关系

`TransitChart` 按干支年、月、日期或时刻返回一个 `TransitSet`；`RelationshipAnalyzer` 对它做关系查询。
下面取 2024 年的流运，查它与婚姻宫的地支关系。

```{testcode} relations-house
from datetime import datetime

from bazi.analyzer.relationship import RelationshipAnalyzer
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import DizhiRelation
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
year = TransitChart(chart).at_year(2024)
assert year is not None

print(year.json)
print([kind.value for kind in year])
print(year.select(TransitKind.LIUNIAN).json)

found = RelationshipAnalyzer(chart).transits.house_relations(year)
for relation, combos in found.items():
  for combo in combos:
    print(relation, ''.join(str(dizhi) for dizhi in sorted(combo, key=lambda dizhi: dizhi.index)))
print(DizhiRelation.害 is DizhiRelation.HAI, DizhiRelation.害.value)
```

```{testoutput} relations-house
{'dayun': '丁丑', 'liunian': '甲辰'}
['dayun', 'liunian']
{'liunian': '甲辰'}
害 丑午
生 丑午
生 辰午
True 害
```

几点读法：

- `at_year` 在出生年之前返回 `None`，所以先判断再用。返回的 `TransitSet` 只含当前有的种类（这里是大运和流年），
  缺项就是 `None`。`select` 要求指定种类全部存在，缺项抛 `ValueError`。
- `TransitKind` 是流运种类的枚举，成员值是英文小写的拼音；`year.json` 的键就是这些值，干支用中文。
- 关系的键是 `DizhiRelation` 成员，有拉丁名和中文别名，二者是同一个对象（`DizhiRelation.害 is DizhiRelation.HAI`）。
- 每个组合是一个 `frozenset` 的地支，不带次序，所以示例先按枚举序排序再打印。
  各关系的取法与流派定义看 {py:class}`~bazi.school.BaziSchool` 和 {py:class}`~bazi.defines.relations.DizhiRelation`。
- 结果是不可变的：`TransitSet` 是 frozen dataclass，关系结果是冻结映射，赋值会抛错。

```{testcode} relations-immutable
from datetime import datetime

from bazi.analyzer.relationship import RelationshipAnalyzer
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import DizhiRelation
from bazi.transit_chart import TransitChart

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
year = TransitChart(chart).at_year(2024)
assert year is not None
found = RelationshipAnalyzer(chart).transits.house_relations(year)

def rewrite_year():
  year.liunian = None


def rewrite_found():
  found[DizhiRelation.害] = ()


for name, mutate in (('改流运', rewrite_year), ('改关系', rewrite_found)):
  try:
    mutate()
  except (AttributeError, TypeError) as error:
    print(name, type(error).__name__)
```

```{testoutput} relations-immutable
改流运 FrozenInstanceError
改关系 TypeError
```

## 取有限的几步大运和流年

`chart.dayun` 和 `chart.liunian` 是生成器属性，**每次访问都新建一个**。三点要记住：

- 存进变量的生成器会被耗尽，之后再取是空的。要重新开始就再访问一次属性。
- `chart.dayun` 是有限的，数量取决于出生时间和历法后端的节气范围。
- `chart.liunian` 可以无限延续，不要对它直接调用 `list` 或 `tuple`。用 `itertools.islice` 取需要的个数。

```{testcode} transits-generators
from datetime import datetime
from itertools import islice

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))

for step in islice(chart.liunian, 3):
  print(step.ganzhi_year, step.ganzhi)

dayuns = chart.dayun
first_two = list(islice(dayuns, 2))
next_two = list(islice(dayuns, 2))
print([step.ganzhi_year for step in first_two], [step.ganzhi_year for step in next_two])
print(first_two[0].start_moment.date(), first_two[0].end_moment.date())

list(dayuns)
print('耗尽后', list(dayuns))
print('重新访问', next(iter(chart.dayun)).ganzhi_year)
print('小运', [(step.xusui, str(step.ganzhi)) for step in chart.xiaoyun[:2]])
```

```{testoutput} transits-generators
1990 庚午
1991 辛未
1992 壬申
[1994, 2004] [2014, 2024]
1994-02-23 2004-02-23
耗尽后 []
重新访问 1994
小运 [(1, '甲辰'), (2, '癸卯')]
```

`chart.xiaoyun` 不同：它是缓存的元组，可以反复遍历。大运的 `ganzhi_year` 是起运年份标签，
每步覆盖 `[start_moment, end_moment)`，不表示这步大运占据整个标签年；标签规则见 {doc}`configuration`。

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
- 这里的关系和神煞只说明“在所选流派的定义下，这些干支满足了某个结构条件”，不是旺衰、格局或某件事会不会发生。
  要看某条知识条目的前提在这张盘上是否成立，见 {doc}`knowledge`。
