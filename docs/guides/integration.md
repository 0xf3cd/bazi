# 集成开发

这一页面向把 `bazi` 接进自己程序的开发者：怎么导入、读取内存结果，以及前提匹配返回什么。
导入与行为承诺以对应版本源码根目录的 `API_CONTRACT.md` 为准；签名、字段和局部返回说明查 API 参考。
第一次排盘及保存文本先看 {doc}`quickstart`；升级旧源码调用则从 [README 迁移入口](https://github.com/0xf3cd/bazi/blob/main/README.md#从-v220-迁移到-v230)开始。

## 导入

库没有根类，也没有安装后的命令行入口。类型和函数从定义模块导入：

```{testcode} integration-imports
from bazi import bazi as bazi_module
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.school import BaziConfig

print(Bazi is bazi_module.Bazi)

try:
  from bazi import Bazi as root_class
except ImportError as error:
  print('ImportError')
```

```{testoutput} integration-imports
True
ImportError
```

包的 `__all__` 只列子模块，不是公开 API 的全集；`bazi.data_types` 等定义模块同样可以直接导入。
带下划线的名字是包内约定，不承诺包外调用。

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

源码里的 `run_demo.py` 就是用终端颜色码实现这两个钩子的；传给钩子的永远是单个字形，不是整段文字。

## 四柱之外：胎元与命宫

这两个属性返回 `Ganzhi`，首次访问后缓存；四柱仍只有年、月、日、时，不增加柱位。

```{testcode} integration-auxiliary
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
original = chart.bazi
print(chart.taiyuan)
print(chart.minggong)
print(len(chart.bazi.pillars), chart.bazi == original)
```

```{testoutput} integration-auxiliary
丁卯
甲戌
4 True
```

胎元取月干顺移一、月支顺移三，只作符号派生，不倒推实际受孕时间。
命宫按现有节月，达到中气后月序循环进一，再用掌诀与本盘年干五虎遁配干；大寒后进正月不提前换年。
时支、精度、地点盘与后端的边界约定见[胎元与命宫契约](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md#胎元与命宫附加查询)。

这两项不进入现有五行、十神、神煞、关系或流运分析，也不进入盘身份、`school` 或旧文本输出。
低层纯计算见 {py:func}`~bazi.utils.bazi_utils.taiyuan` 与 {py:func}`~bazi.utils.bazi_utils.minggong`；
后者需要已调整的有效命宫月支，不接收裸整数月序。来源与其他读法候选可查知识对象
`concept.taiyuan`、`concept.minggong`，均须显式包含参考条目，不自动认定解释成立。

## 内存对象与输入隔离

命盘与判别结果没有保存、恢复或格式迁移接口。`BaziChart.bazi` 每次返回独立深拷贝；
`Bazi` 按完整输入身份比较，`BaziChart` 按对象身份比较。知识库按内容和顺序比较。
知识 JSON 只作当前编辑来源，读取方法见 {doc}`knowledge`。

`ContextResult` 是 frozen dataclass。构造参数 `_bazi` 接收 `Bazi` 输入并在构造时深拷贝；
`bazi` 属性每次返回独立深拷贝。`dataclasses.replace(result, _bazi=...)`
也会验证并复制输入。相等与哈希包括输入的性别、完整配置及地点时间身份，不使用显示文本作身份。
`knowledge` 复用显式传入的不可变实例；未传时，每次求值独立加载当前编辑源，已有结果不随源文件变化。
`ContextResult.render()` 直接读取结果持有的领域值，不重新排盘或重建知识对象。

## 前提匹配：结构事实，不是判断

`evaluate_context` 求值已注册的判据，例如“选定范围内正官与七杀各至少出现一次”。
`entry_role='premise'` 的判据检查关联条目的完整前提，`references` 为 `PremiseMatches`；
`entry_role='condition'` 只检查局部事实，`references` 为 `ConditionReferences`，不能据此认定条目全文的前提成立。
条目都从 `references.entries` 读取；即使没有条目，两个外层类型也保留不同含义。
`SATISFIED` 表示该判据的结构事实成立，不是旺衰、格局或现实事件的判断，也不说明条文本身为真。

```{testcode} integration-context
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import NatalObservation, PremiseMatches, criterion, evaluate_context

info = criterion('editorial.guansha_coexistence.v1')
print(info.definition)

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
result = evaluate_context(
  chart,
  criterion_id=info.criterion_id,
  observation=NatalObservation(),
)
print(result.criterion.status, result.criterion.reason, result.criterion.scope_complete)
print(dict(result.criterion.observations))
assert isinstance(result.references, PremiseMatches)
print('默认返回的关联条目', len(result.references.entries))
```

```{testoutput} integration-context
选定范围内正官与七杀各至少出现一次。
SATISFIED premise_satisfied True
{'observed_coexistence': True, 'female': True}
默认返回的关联条目 0
```

默认只返回满足默认输出资格的条目，这里没有；加 `include_reference_only=True` 才会包含仅供参考的条目，
但前提满足也不会授予默认输出资格。判据目录与绑定识别见[接口契约的判据目录](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md#判据目录)；条目的来源状态见 {doc}`knowledge`。

### 选择观察范围与读取证据

`observation=` 接收具体观察请求，没有隐式范围默认值：

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
  ConditionReferences, TransitObservation, YearCoordinate, evaluate_context,
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
assert isinstance(result.references, ConditionReferences)
assert result.evidence.transits is not None
print(result.criterion.status, result.criterion.scope_complete)
print(tuple(kind.value for kind in result.evidence.transits))
print(type(result.references).__name__, len(result.references.entries))
```

```{testoutput} integration-transits
SATISFIED True
('dayun', 'liunian')
ConditionReferences 1
```

`CriterionResult` 只存 criterion_id、reason、observations，definition、status、scope_complete 从注册定义和原因派生；
`EntryMatch` 只存 claim_id、reason，status 也为派生属性。`asdict` 不包含这些属性，固定 scope／entry 标签也不属于 dataclass 构造字段。
直接构造只检查结构，不认证观察、原因、请求年份和手填证据的事实对应关系；通常应使用 evaluate_context 取得结果。
旧构造与位置模式的迁移细目见[结构接口迁移](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md#结构接口迁移)。
