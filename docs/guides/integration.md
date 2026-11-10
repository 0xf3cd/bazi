# 集成开发

这一页面向把 `bazi` 接进自己程序的开发者：读取结构化命盘字段、定制文本，以及检查知识前提。
精确的输入与行为约定见 {doc}`../api-contract`，签名与字段查 API 参考。
第一次排盘及保存文本先看 {doc}`quickstart`；升级旧调用先看 {doc}`../release-notes`。

## 读取十神、藏干和纳音

库没有根类；类型和函数从定义模块导入。安装后的 `bazi` 命令用于终端操作，不改变这些导入路径：

```{testcode} integration-fields
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
print('年干十神', chart.shishen.year.tiangan)
print('月支藏干', ' '.join(map(str, chart.hidden_tiangan.month)))
print('日柱纳音', chart.nayin.day)
```

```{testoutput} integration-fields
年干十神 偏印
月支藏干 丙 庚 戊
日柱纳音 杨柳木
```

这些属性以 {py:class}`~bazi.data_types.BaziData` 保存四柱数据，字段为 `year`、`month`、`day`、`hour`，
也可按年、月、日、时顺序遍历。十神和阴阳五行的每柱结果再以 {py:class}`~bazi.data_types.GanzhiData`
区分 `tiangan` 与 `dizhi`；日主自身的天干十神位置为 `None`。

把四柱干支、纳音与天干十神放在一起遍历：

```{testcode} integration-pillars
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Zhu

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
for position, pillar, nayin, shishen in zip(Zhu, chart.bazi.pillars, chart.nayin, chart.shishen):
  print(position, pillar, nayin, shishen.tiangan or '日主')
```

```{testoutput} integration-pillars
年 庚午 路旁土 偏印
月 辛巳 白蜡金 正印
日 壬午 杨柳木 日主
时 乙巳 覆灯火 伤官
```

`BaziData` 支持字段访问和迭代，不提供下标访问。完整属性见 {py:class}`~bazi.bazi_chart.BaziChart`。

## 命盘文本与终端颜色

`bazi.chart_text` 的 `basic_text`、`transit_text`、`chart_text` 返回纯文本，库本身不加颜色。
要加颜色或标记，传一个 `TextStyle`：`glyph` 收到单个天干或地支，`day_master_mark` 收到“日主”二字，各自返回显示文字；
两个字段都可以不设，不设就原样输出。钩子的返回值原样放进文本，库不做检查，版式由你负责。下面的例子给日主加上星号，再把每个字形用方括号括起来：

```{testcode} integration-text-style
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.chart_text import TextStyle, basic_text

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
style = TextStyle(glyph=lambda s: f'[{s}]', day_master_mark=lambda label: f'*{label}*')
text = basic_text(chart, style=style)
print(next(line for line in text.splitlines() if line.startswith('日：')))
```

```{testoutput} integration-text-style
日：  [壬] [阳水] <*日主*>      [午] [阳火] <正财>     [丁] [阴火] <财> [己] [阴土] <官>
```

`bazi demo` 用终端颜色码实现这两个钩子；传给字形钩子的永远是单个字形，不是整段文字。

## 四柱之外：胎元与命宫

这两个属性返回 `Ganzhi`，首次访问后缓存；四柱仍只有年、月、日、时，不增加柱位。

```{testcode} integration-auxiliary
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
print('胎元', chart.taiyuan)
print('命宫', chart.minggong)
```

```{testoutput} integration-auxiliary
胎元 丁卯
命宫 甲戌
```

胎元取月干顺移一、月支顺移三，只作符号派生，不倒推实际受孕时间。
命宫按现有节月，达到中气后月序循环进一，再用掌诀与本盘年干五虎遁配干；大寒后进正月不提前换年。
时支、精度、地点盘与后端的边界约定见[胎元与命宫契约](../api-contract.md#胎元与命宫附加查询)。

这两项不进入现有五行、十神、神煞、关系或流运分析，也不进入盘身份、`school` 或旧文本输出。
低层纯计算见 {py:func}`~bazi.utils.bazi_utils.taiyuan` 与 {py:func}`~bazi.utils.bazi_utils.minggong`；
后者需要已调整的有效命宫月支，不接收裸整数月序。来源与其他读法候选可查知识对象
`concept.taiyuan`、`concept.minggong`，均须显式包含参考条目，不自动认定解释成立。

(context-matching)=
## 前提匹配：结构事实，不是判断

`evaluate_context` 求值已注册的判据，例如“选定范围内正官与七杀各至少出现一次”。
`entry_role='premise'` 的判据检查关联条目的完整前提；`entry_role='condition'` 只检查局部事实，不能据此认定条目全文的前提成立。
`result.reference_ids` 给出参考条目的 ID 元组，用 `result.knowledge.entry(claim_id)` 读取文字。
两种语义由 `criterion(result.criterion.criterion_id).entry_role` 区分，即使 ID 元组为空也不改变。
`SATISFIED` 表示该判据的结构事实成立，不是旺衰、格局或现实事件的判断，也不说明条文本身为真。

```{testcode} integration-context
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import NatalObservation, criterion, evaluate_context

info = criterion('editorial.guansha_coexistence.v1')
print(info.definition)

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
result = evaluate_context(
  chart,
  criterion_id=info.criterion_id,
  observation=NatalObservation(),
)
print('状态', result.criterion.status, '范围完整', result.criterion.scope_complete)
print(dict(result.criterion.observations))
with_references = evaluate_context(
  chart,
  criterion_id=info.criterion_id,
  observation=NatalObservation(),
  include_reference_only=True,
)
for claim_id in with_references.reference_ids:
  print(with_references.knowledge.entry(claim_id).text)
```

```{testoutput} integration-context
选定范围内正官与七杀各至少出现一次。
状态 SATISFIED 范围完整 True
{'observed_coexistence': True, 'female': True}
如在命盘中也见七杀，则称为官杀混杂，也许代表在公司里受排挤、职场不顺，或有官司是非。
如在命盘中也见正官，则称为官杀混杂，也许代表在公司里受排挤、职场不顺，或有官司是非。
```

上例的结构事实成立，所以状态为 `SATISFIED`。最后两行是库中仅供参考的文字，前提满足不能推出这些职场或法律事件。
两个关联条目均不默认展示，因此第一次的 `result.reference_ids` 为空；第二次传入 `include_reference_only=True`
才读到文字，判据状态不变。空参考元组只说明本次没有返回关联条目，
不能据此读成“前提不成立”：条目也可能因自定义知识库缺失或性别筛选而未返回。
参考 ID 按判据声明序筛选，不按知识库条目顺序排列；筛选规则见[判据目录](../api-contract.md#判据目录)。
正文、引文与来源说明的编辑不改变判据状态；自定义库须保持同 ID 的领域含义，不再核对内容摘要。
条目的来源状态见 {doc}`knowledge`。

### 选择观察范围与读取证据

`observation=` 接收具体观察请求，没有隐式范围默认值。三种结果的读法是：

| 状态 | 读法 |
| --- | --- |
| `SATISFIED` | 判据定义的结构事实满足。 |
| `NOT_SATISFIED` | 所需观察完整，但事实或判据的性别条件不满足。 |
| `UNKNOWN` | 所需年份、坐标或流运观察不完整；已有的部分证据仍保留。 |

- `NatalObservation()` 只查原局，可供全部判据使用。
- `LiunianObservation(ganzhi_year=2024)` 查原局加单流年，供明藏干分类判据使用；省略年份时求值为 UNKNOWN。
- `TransitObservation(kinds, coordinate=None)` 供婚恋结构判据使用；kinds 必须是非空、无重复的 TransitKind 元组，坐标缺失时求值为 UNKNOWN。

多种岁运的坐标使用 `YearCoordinate(ganzhi_year)`、`MonthCoordinate(ganzhi_year, ganzhi_month)`、
`DateCoordinate(solar_date)` 或 `MomentCoordinate(solar_moment)`，均从 `bazi.context_matching` 导入。
年月是干支年月，日期和时刻均按东八区解释。日期不能传 datetime，时刻须是不带时区标签的 datetime；
时刻保留请求微秒身份，计算仍按秒解释。
这些严格请求不改变 `TransitChart.at_year/at_month` 原有的便捷输入政策。

`result.evidence` 在明藏干分类判据中为 `tuple[ChartOccurrence, ...]`，position 是 `Zhu` 或带年份的
`LiunianPosition`，layer 是 `TianganLayer`；婚恋结构判据中则为 `RelationshipEvidence`。
请求部分流运不可取得时，判据仍是 UNKNOWN，但已取得种类的证据保留，不能把 UNKNOWN 读成“没有发现”。

例如，显式查询某年的大运和流年，再分别读取结构证据与条件参考：

```{testcode} integration-transits
from bazi.analyzer.relationship import RelationshipEvidence
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import (
  TransitObservation, YearCoordinate, criterion, evaluate_context,
)
from bazi.transits import TransitKind

chart = BaziChart(Bazi.create('2000-01-09 12:00', 'male'))
result = evaluate_context(
  chart,
  criterion_id='editorial.spouse_palace_xingchong.v1',
  observation=TransitObservation(
    (TransitKind.DAYUN, TransitKind.LIUNIAN),
    YearCoordinate(ganzhi_year=2016),
  ),
  include_reference_only=True,
)
assert isinstance(result.evidence, RelationshipEvidence)
assert result.evidence.transits is not None
print(result.criterion.status, result.criterion.scope_complete)
print(tuple(kind.value for kind in result.evidence.transits))
print(criterion(result.criterion.criterion_id).entry_role, len(result.reference_ids))
for claim_id in result.reference_ids:
  print(result.knowledge.entry(claim_id).text)
```

```{testoutput} integration-transits
SATISFIED True
('dayun', 'liunian')
condition 1
《命理探原·论妻子》：「又有妻透成格。或妻宮有用〔小標點〕而坐下刑衝。未免得美妻而難偕老。」（〔〕内为整理记号，非原书文字。）
```

本例 `entry_role='condition'`，只检查妻宫刑冲这个局部条件，不认证条目全文或其中的现实事件。
想连同来源、前提和限度一起显示，用 `result.knowledge.render(entry)`；读取方法见 {doc}`knowledge`。

## 内存结果与对象契约

通常使用 `evaluate_context` 取得结果，不直接手填证据构造。命盘和判别结果没有保存、恢复或格式迁移接口，
知识 JSON 只作当前编辑来源。命盘对输入作拷贝隔离，已创建结果不随源文件的修改变化。
直接构造、拷贝、相等、`asdict` 与模式匹配的精确条件见 {doc}`../api-contract`。
