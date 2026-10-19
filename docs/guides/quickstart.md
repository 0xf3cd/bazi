# 快速开始

这一页带你排出第一张盘，读出四柱，并指出下一步该去哪一页。

## 安装

```sh
python -m pip install bazi
```

需要 Python 3.11 或更高版本。运行时只用标准库和随包数据，不联网。

本页说明对应当前开发源码。已发布版本的接口以该版本 tag 下的文档为准，两者可能不同。

```{note}
本库没有安装后的命令行入口，也没有 `from bazi import Bazi` 这样的根类。
请从定义模块导入，下面每个示例都这样写。
```

## 排第一张盘

示例用虚构的出生时间。`Bazi.create` 接收无时区的民用时刻和性别，`BaziChart` 在它之上提供十神、大运等派生信息。

```{testcode} quickstart-chart
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

bazi = Bazi.create(datetime(1990, 5, 17, 10, 30), 'female')
chart = BaziChart(bazi)

print('四柱', ' '.join(str(pillar) for pillar in bazi.pillars))
print('日主', bazi.day_master)
print('性别', chart.json['gender'])
print('精度与后端', chart.json['precision'], chart.json['backend'])
```

```{testoutput} quickstart-chart
四柱 庚午 辛巳 壬午 乙巳
日主 壬
性别 female
精度与后端 day celestial
```

- `bazi.pillars` 依次是年、月、日、时柱，每柱是一个 `Ganzhi`。
- 性别字符串接受 `男`、`女`、`male`、`female`；`chart.json` 里统一存拉丁写法。
- `chart.json` 是每次新建的字典，字段和配置都在里面。需要保存或交换时见 {doc}`integration`。

## 把盘排成文本

`bazi.chart_text` 把命盘排成可读的纯文本：不写文件，不依赖终端着色库，同一张盘每次得到同样的文字。
`basic_text` 给出日元、出生时刻，以及四柱各自的十神、阴阳五行、藏干、纳音和十二长生。

```{testcode} quickstart-text
from datetime import datetime

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.chart_text import basic_text

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
print(basic_text(chart).strip())
```

```{testoutput} quickstart-text
日元壬水，female，生于 1990-05-17

出生时刻：1990-05-17T10:30:00

     天干                  地支                  地支藏干
年：  庚 [阳金] <偏印>      午 [阳火] <正财>     丁 [阴火] <财> 己 [阴土] <官>
  -- 纳音：路旁土  -- 十二长生：胎
月：  辛 [阴金] <正印>      巳 [阴火] <偏财>     丙 [阳火] <才> 庚 [阳金] <枭> 戊 [阳土] <杀>
  -- 纳音：白蜡金  -- 十二长生：绝
日：  壬 [阳水] <日主>      午 [阳火] <正财>     丁 [阴火] <财> 己 [阴土] <官>
  -- 纳音：杨柳木  -- 十二长生：胎
时：  乙 [阴木] <伤官>      巳 [阴火] <偏财>     丙 [阳火] <才> 庚 [阳金] <枭> 戊 [阳土] <杀>
  -- 纳音：覆灯火  -- 十二长生：绝
```

- 返回值是字符串，前后各有一个换行，可以直接 `print`。需要完整的文本，包括流运，用 `chart_text(chart)`。
- 十神、藏干等内容与 `chart.shishen`、`chart.hidden_tiangan` 等结构化结果一致，只是排成了文字。
- 流运文本把流年的数量交给调用方，见 {doc}`relations-transits`；要加终端颜色，见 {doc}`integration`。

## 在交互里看一眼

在 Python 交互环境里直接输入对象，会看到一行摘要：出生时刻、性别和四柱。配置不是默认值，或是地点盘时，摘要才会多出对应部分。
摘要不会去算流运，也不展开整张盘；它只用来探索和调试，格式以后可能调整，要保存或交换请用 `chart.json`（见 {doc}`integration`）。

```{testcode} quickstart-explore
from datetime import datetime

import bazi
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.transit_chart import TransitChart

chart = BaziChart(Bazi.create(datetime(1990, 5, 17, 10, 30), 'female'))
print(repr(chart))
print([name for name in dir(bazi) if name in ('knowledge', 'transit_chart')])

try:
  TransitChart(chart.bazi)
except TypeError as error:
  print(error)

try:
  bazi.Bazi
except AttributeError as error:
  print(error)
```

```{testoutput} quickstart-explore
BaziChart(Bazi(1990-05-17T10:30:00, female, 庚午 辛巳 壬午 乙巳))
['knowledge', 'transit_chart']
Expected BaziChart, got <class 'bazi.bazi.Bazi'>; wrap it with BaziChart(bazi)
module 'bazi' has no attribute 'Bazi'; use: from bazi.bazi import Bazi
```

`dir(bazi)` 会列出按需导入的子模块，导入后才加载它们。传错对象时，报错在原来的“期望什么，收到什么”之后，接着说明该用哪个入口。

## 默认值是一种选定的口径

没有传配置时，库使用 `DAY` 精度、`celestial` 历法后端，晚子时 23:00 换日柱，以立春换年。
这是本库选定的一套取法，不是八字唯一的读法：精度、历法后端和流派取法各有其他选项。

出生在交节日前后、子时前后，或要采用其他流派时，先读 {doc}`configuration`，再决定要不要改默认值。

## 下一步

- 想改变精度、换日点、大运年份口径，或使用真太阳时：{doc}`configuration`。
- 想查流年、流月，或看原局与流运之间的关系：{doc}`relations-transits`。
- 想把结果存成 JSON、重新加载，或接入自己的程序：{doc}`integration`。
- 不排盘，只查知识条目和出处：{doc}`knowledge`。

逐个类和方法的签名在 API 参考中，入口见 {py:class}`~bazi.bazi.Bazi` 和 {py:class}`~bazi.bazi_chart.BaziChart`。
