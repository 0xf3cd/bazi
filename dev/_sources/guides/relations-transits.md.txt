# 关系与流运

这一页做两件事：取某一年的流运，查它与原局婚姻宫的地支关系；再从命盘取有限几步大运和流年。
结果是结构事实，描述“哪些干支落在哪些位置、满足哪种关系”，不是对事件的预测。

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

## 范围提醒

- 月、日期和时刻查询按东八区无时区标签和物理节气边界；`at_moment` 还要求 `celestial` 系后端和 `HOUR` / `MINUTE` 精度，否则返回 `None`。
- `at_year` 在出生年之前返回 `None`，远年份仍可返回流年，不能用它的 `None` 判断历法表上界。月、日期与时刻查询不满足各自支持范围时返回 `None`；类型与取值校验另见各入口的 API 说明。
- 这里的关系和神煞只说明“在所选流派的定义下，这些干支满足了某个结构条件”，不是旺衰、格局或某件事会不会发生。
  要看某条知识条目的前提在这张盘上是否成立，见 {doc}`knowledge`。
