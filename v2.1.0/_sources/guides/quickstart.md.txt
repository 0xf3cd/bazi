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
