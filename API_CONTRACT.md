# 公开接口与记录兼容契约

本库从定义模块导入类型与函数，没有安装 CLI 或根类入口。例如：

```python
from datetime import datetime
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Tiangan
from bazi.school import BaziConfig

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male', BaziConfig()))
assert chart.bazi.day_master in Tiangan
```

## 支持范围与导入路径

完整名称、类成员、字段、枚举别名、继承关系及规范定义路径登记在
[`tests/api_contract.py`](tests/api_contract.py)，供测试和参考文档共同使用。
`PUBLIC_NAMES` 登记定义模块的自有名称和既有包入口；`REEXPORTS`、`ALIASES` 区分重导出与别名。
`DECLARED_MEMBERS` 包含方法、属性、类型别名和字段；继承关系另由 `BASES` 登记，
公开命盘记录从私有基类继承的字段也在清单中，不因基类名带下划线而遗漏。

- 包的 `__all__` 不是公开 API 全集；`bazi.data_types` 等定义模块同样可直接导入。
- 领域枚举的中文与拉丁成员别名共用值；中文类型别名也保留，如 `天干` 与 `Tiangan`。
- 第三方模块在源码中的偶然导入不是本库提供的 API。普通模块的依赖导入不自动成为规范重导出。
- 下划线名字及 `_validation` 是包内约定，不承诺包外调用；共享接口的归属见
  [`tests/data/internal_interfaces.json`](tests/data/internal_interfaces.json)。不以去掉下划线扩大公开面。
- `STATIC_MODULES` 单独标记离线编码／生成工具与导入即读取数据表的后端实现。
  离线工具按源码入口查阅，不是安装 CLI；检查清单不执行下载、生成或数据表加载。
- 清单不改变现有导入和 wildcard 行为。新增自有对象、字段、枚举别名或继承关系须同步登记；
  运行时签名和类型以定义模块为准，不在清单中伪造签名。

### 字符串输入不等于枚举别名

`Bazi.create` 的性别字符串只接受 `男`、`女`、`male`、`female`（拉丁大小写不敏感），
也可直接传 `BaziGender`。枚举中的 `乾`、`坤`、`阳`、`阴`、`YANG`、`YIN` 不是性别字符串入口。

`BaziConfig` 构造函数接收声明类型；需要字符串解析时使用 `BaziConfig.from_values`。
精度支持 `分`／`分钟`／`时`／`小时`／`天`／`日` 和
`m`／`min`／`minute`／`h`／`hour`／`d`／`day`，拉丁大小写不敏感。
后端与大运年份规则分别由 `CalendarBackend.from_str`、`DayunYearRule.from_str` 解释成员名或值；
流派档案仍传 `BaziSchool`，不接受字符串。不统一这些既有输入域。

## 返回值、拷贝与相等性

- 查询结果和规则集合使用 `tuple`、`frozenset`、`frozendict` 等不可变结构；
  `frozendict` 只冻结映射本身，不深拷贝其中的值。具体接口的可变边界仍看其类型与说明。
- `BaziChart.json` 是独立的可变 JSON 字典，修改它不修改命盘。命盘隔离传入的 `Bazi`，
  `chart.bazi` 也按其既有防御性拷贝约定返回；不把 Python 属性只读等同于所有对象都深冻结。
- `Bazi` 按值比较；`BaziChart` 按对象身份比较。恢复后的两个命盘可以 `json` 和 `bazi` 值相等，
  但命盘对象本身不相等。知识库按内容及顺序比较，前提结果按其值字段比较。
- 每次访问 `chart.dayun`、`chart.liunian` 都获得新生成器。保存到变量的有限生成器会耗尽；
  流年生成器可无限延续，不要直接对它调用 `tuple`／`list`。`chart.xiaoyun` 是缓存元组，可重复遍历。

## 三类 JSON 分别保存与恢复

| 记录 | 输出／输入 | 版本与恢复含义 |
|---|---|---|
| 命盘 | `BaziChart.json` 输出字典；`BaziChart.from_json` 接收映射 | 无内置版本字段。按记录中的输入、配置与当前实现重建，再逐项核对派生字段；只保证与当前版本一致。 |
| 知识库 | `KnowledgeBase.export_json` 输出 JSON 文本；`from_json` 接收文本 | `schema_version=1`。恢复语料并校验结构、引用和各状态，不计算命盘前提。 |
| 前提判别结果 | `ContextResult.export_json` 输出 JSON 文本；`from_json` 接收文本 | `record_version=4`。恢复记录并校验结构和值类型，不重新判别，不认证输入、观察、证据与绑定之间的事实一致性。 |

命盘映射严格区分默认盘与地点盘。缺键、多键、不支持的值、非规范拼写及重算不一致会拒绝；
类型错误抛 `TypeError`，字段／值／一致性错误抛 `ValueError`。同时违反多个约束时不保证报错顺序。
命盘 JSON 无版本字段，若需长期保存软件版本，可在调用方的外层记录中保存；不要给命盘映射加自定义键。

以下三段各自独立运行，文件由调用方管理。

### 命盘：文本先解析成映射

```python
import json
from datetime import datetime
from pathlib import Path
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
path = Path('chart.json')
path.write_text(json.dumps(chart.json, ensure_ascii=False), encoding='utf-8')
restored = BaziChart.from_json(json.loads(path.read_text(encoding='utf-8')))
assert restored.json == chart.json
assert restored.bazi == chart.bazi
assert restored != chart
```

### 知识库：直接保存导出的文本

```python
from pathlib import Path
from bazi.knowledge import KnowledgeBase

knowledge = KnowledgeBase.load()
path = Path('knowledge.json')
path.write_text(knowledge.export_json(), encoding='utf-8')
restored = KnowledgeBase.from_json(path.read_text(encoding='utf-8'))
assert restored == knowledge
```

知识 JSON 拒绝重复键、字段差异、不支持的版本、断引用及不合法的条目状态。
导出默认保留全部条目，包括仅供参考的条目；显式选择条目时仍保留全部对象、情境与来源注册表。
`load` 每次重新读取文件；已有知识快照不随文件编辑而变化。

### 前提结果：恢复不等于重新求值

```python
from datetime import datetime
from pathlib import Path
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.context_matching import ContextProfile, ContextResult, evaluate_context

chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
result = evaluate_context(
  chart,
  criterion_id='editorial.guansha_coexistence.v1',
  profile=ContextProfile('natal'),
  include_reference_only=True,
)
path = Path('context.json')
path.write_text(result.export_json(), encoding='utf-8')
restored = ContextResult.from_json(path.read_text(encoding='utf-8'))
assert restored == result
```

前提记录只接受版本 4，旧版本或错误类型的版本值会拒绝。恢复仍检查 profile 类型、坐标结构、
字段和值域等约束；能恢复不代表判别真实，也不等于绑定重新识别。
需要当前规则下的结论时，应使用原输入与配置重新构造命盘并调用 `evaluate_context`，
不要只改 `record_version` 冒充迁移。知识 schema 版本与前提 record 版本也不能互换。

旧记录不兼容时保留原件、记录原软件版本及失败原因；没有自动迁移接口。
确需修改接口或记录语义时须先说明兼容影响和迁移方式，不为统一字典与文本的外观而改变既有行为。
