# 集成开发

这一页面向把 `bazi` 接进自己程序的开发者：怎么导入、怎么保存和恢复三类 JSON 记录，以及前提匹配返回什么。
公开接口的完整约定写在对应版本源码根目录的 `API_CONTRACT.md`，这里只走最常用的几条路径。
第一次排盘及保存文件先看 {doc}`quickstart`；升级旧源码调用则从 [README 迁移入口](https://github.com/0xf3cd/bazi/blob/main/README.md#从-v220-迁移到-v230)开始。

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
record = chart.json
print(chart.taiyuan)
print(chart.minggong)
print(len(chart.bazi.pillars), chart.json == record)
```

```{testoutput} integration-auxiliary
丁卯
甲戌
4 True
```

胎元取月干顺移一、月支顺移三，只作符号派生，不倒推实际受孕时间。
命宫按现有节月，达到中气后月序循环进一，再用掌诀与本盘年干五虎遁配干；大寒后进正月不提前换年。
时支取本盘时柱：DAY 仍使用输入小时，地点盘取真太阳钟，换日设置（`day_rollover`）不改时支。
中气归属沿用本盘精度：DAY 比日期，HOUR 比完整日期中的时辰起点，MINUTE 比分钟起点，相等归新；
地点盘先把中气转换到与出生相同的真太阳钟。HKO 仍仅支持 DAY。

这两项不进入现有五行、十神、神煞、关系或流运分析，也不进入盘身份、`school`、JSON 或旧文本输出。
低层纯计算见 {py:func}`~bazi.utils.bazi_utils.taiyuan` 与 {py:func}`~bazi.utils.bazi_utils.minggong`；
后者需要已调整的有效命宫月支，不接收裸整数月序。来源与其他读法候选可查知识对象
`concept.taiyuan`、`concept.minggong`，均须显式包含参考条目，不自动认定解释成立。

## 三类记录，三种恢复

| 记录 | 导出 | 恢复 | 版本 |
| --- | --- | --- | --- |
| 命盘 | `BaziChart.json`（字典） | `BaziChart.from_json(映射)` | 无版本字段 |
| 知识库 | `KnowledgeBase.export_json()`（文本） | `KnowledgeBase.from_json(文本)` | `schema_version` 为 1 |
| 前提判别记录 | `ContextResult.export_json()`（文本） | `ContextResult.from_json(文本)` | `record_version` 为 4 |

三类记录不能互换。入口要求的 Python 类型不符时抛 `TypeError`；同为文本的知识库与前提判别记录互换时抛 `ValueError`。
`schema_version` 与 `record_version` 是各自独立的版本号，也不能互相替代。

### 命盘：重算后核对，不是原结果的冻结

命盘 JSON 保存输入、配置和派生字段。`from_json` 用这些输入和**当前版本**的实现重新构造命盘，
再逐项核对记录里的派生字段，不一致就拒绝。所以它只保证与当前版本一致，不是历史结果的冻结副本。

```{testcode} integration-chart-json
import json
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
text = json.dumps(chart.json, ensure_ascii=False)

restored = BaziChart.from_json(json.loads(text))
print('json 相等', restored.json == chart.json)
print('bazi 相等', restored.bazi == chart.bazi)
print('命盘对象相等', restored == chart)

tampered = json.loads(text)
tampered['pillars']['year'] = '甲子'
try:
  BaziChart.from_json(tampered)
except ValueError:
  print('改动年柱被拒绝')

extra = json.loads(text)
extra['version'] = '2.0.0'
try:
  BaziChart.from_json(extra)
except ValueError:
  print('多余字段被拒绝')
```

```{testoutput} integration-chart-json
json 相等 True
bazi 相等 True
命盘对象相等 False
改动年柱被拒绝
多余字段被拒绝
```

恢复后的两个命盘可以 `json` 和 `bazi` 值相等，但 `BaziChart` 按对象身份比较，对象本身不相等。
命盘 JSON 没有版本字段，也不要往里加自定义键；需要记录软件版本时，写在你自己的外层记录里。

### 知识库和前提判别记录

知识库导出的是全部对象、情境、来源和条目的文本，恢复后与原库按内容和顺序相等。
前提判别记录只接受 `record_version` 为 4，恢复时校验结构和值类型，**不会重新判别**，也不核对输入、观察与证据之间的事实一致性。

```{testcode} integration-other-json
import json
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextProfile, ContextResult, evaluate_context
from bazi.knowledge import KnowledgeBase

knowledge = KnowledgeBase.load()
knowledge_text = knowledge.export_json()
print(json.loads(knowledge_text)['schema_version'], KnowledgeBase.from_json(knowledge_text) == knowledge)

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
result = evaluate_context(
  chart,
  criterion_id='editorial.guansha_coexistence.v1',
  profile=ContextProfile('natal'),
  include_reference_only=True,
)
result_text = result.export_json()
print(json.loads(result_text)['record_version'], ContextResult.from_json(result_text) == result)

old = json.loads(result_text)
old['record_version'] = 3
try:
  ContextResult.from_json(json.dumps(old))
except ValueError:
  print('旧版本被拒绝')

for name, load in (
  ('知识库读判别记录', lambda: KnowledgeBase.from_json(result_text)),
  ('判别记录读知识库', lambda: ContextResult.from_json(knowledge_text)),
):
  try:
    load()
  except ValueError:
    print(name, 'ValueError')
```

```{testoutput} integration-other-json
1 True
4 True
旧版本被拒绝
知识库读判别记录 ValueError
判别记录读知识库 ValueError
```

不要只改 `record_version` 来“迁移”旧记录。旧记录不兼容时，保留原件，记下原来的软件版本和失败原因；
需要当前规则下的结论时，用原始输入和配置重新构造命盘，再调用 `evaluate_context`。库没有自动迁移接口。

## 前提匹配：结构事实，不是判断

`evaluate_context` 求值已注册的判据，例如“选定范围内正官与七杀各至少出现一次”。
`entry_role='premise'` 的判据检查关联条目的完整前提；`entry_role='condition'` 只检查局部事实，关联条目作为条件参考放在 `related`，不能据此认定条目全文的前提成立。
`SATISFIED` 表示该判据的结构事实成立，不是旺衰、格局或现实事件的判断，也不说明条文本身为真。

```{testcode} integration-context
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextProfile, criterion, evaluate_context

info = criterion('editorial.guansha_coexistence.v1')
print(info.definition)

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
result = evaluate_context(
  chart,
  criterion_id=info.criterion_id,
  profile=ContextProfile('natal'),
)
print(result.criterion.status, result.criterion.reason, result.criterion.scope_complete)
print(dict(result.criterion.observations))
print('默认返回的关联条目', len(result.entries))
```

```{testoutput} integration-context
选定范围内正官与七杀各至少出现一次。
SATISFIED premise_satisfied True
{'observed_coexistence': True, 'female': True}
默认返回的关联条目 0
```

默认只返回满足默认输出资格的条目，这里没有；加 `include_reference_only=True` 才会包含仅供参考的条目，
但前提满足也不会授予默认输出资格。判据目录、绑定识别和条目的来源状态在知识教程里展开，见 {doc}`knowledge`。
