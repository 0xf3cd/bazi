# 公历、农历与节气

日期换算与节气查询从 `bazi.calendar.utils` 导入，无需创建命盘。

## 公历与农历往返

```{testcode} calendar-lunar-roundtrip
from datetime import date

from bazi.calendar.utils import to_lunar, to_date

solar = date(2023, 3, 22)
lunar = to_lunar(solar)
print(lunar)
print(to_date(lunar))
assert to_date(lunar) == solar
```

```{testoutput} calendar-lunar-roundtrip
(2023-3-1, LUNAR)
2023-03-22
```

`lunar` 是不可变的 `CalendarDate`，有 `year`、`month`、`day` 和 `date_type` 字段。
**农历月号按年内实际月序编号，闰月占独立序号，不是农历月名。**
上例的 `month=3` 是 2023 年的第 3 个月，即闰二月；这一年的 `month=4` 才是三月。
构造农历输入时也使用同一月序：

```{testcode} calendar-lunar-input
from datetime import date

from bazi.calendar.dates import CalendarDate, CalendarType
from bazi.calendar.utils import to_date

leap_month_start = CalendarDate(2023, 3, 1, CalendarType.农历)
assert to_date(leap_month_start) == date(2023, 3, 22)
```

`to_solar` 返回公历 `CalendarDate`，`to_date` 返回标准库 `date`；
`to_lunar` 返回农历日期，`to_ganzhi` 返回以立春换年的干支历日期。
它们都接收 `date` 或 `CalendarDate`。传 `datetime` 时只读年月日，不使用日内时刻，也不换算时区。
`to_ganzhi` 按交节日划分年月；需要按时辰或分钟判断出生归属时，用 `Bazi.create` 与
{doc}`configuration` 中的精度设置。

## 支持范围

```{testcode} calendar-date-range
from bazi.calendar.dates import CalendarType
from bazi.calendar.utils import get_min_supported_date, get_max_supported_date, to_date

print(to_date(get_min_supported_date(CalendarType.公历)))
print(to_date(get_max_supported_date(CalendarType.公历)))
```

```{testoutput} calendar-date-range
1901-02-19
2099-12-31
```

日期换算包含上述两端。将参数换成 `CalendarType.农历` 或 `CalendarType.干支历`，可取得同一范围在
相应历法下的端点。`CalendarDate` 构造时检查字段类型，换算时再检查日期是否合法、是否在支持范围内；
错型抛 `TypeError`，非法或越界日期抛 `ValueError`。

## 查询节气与相邻的节

```{testcode} calendar-jie
from bazi.calendar.utils import jieqi_moment, prev_jie, next_jie
from bazi.defines import Jieqi

moment = jieqi_moment(2000, Jieqi.立春)
print(moment)
print(prev_jie(moment).jieqi, next_jie(moment).jieqi)
```

```{testoutput} calendar-jie
2000-02-04 20:40:23
立春 惊蛰
```

`jieqi_moment` 的年份是公历年，可查二十四节气；该年的小寒、大寒都在该年一月。
结果为东八区无时区 `datetime` 标签，截断到秒。`prev_jie` 和 `next_jie` 只查开月的十二节，
不含中气，返回 `JieqiTime`，可读 `.jieqi` 和 `.moment`。
恰好交节时，`prev_jie` 返回当前节，`next_jie` 返回下一节。

相邻节查询接收同一东八区无时区标签。`supported_jie_boundaries()` 返回首末节时刻，
查询输入须在 `[首端, 末端)` 内；节气表覆盖公历 1901 至 2200 年，
不因此扩大上面的日期换算或出生输入范围。

## 数据来源与精度

随包表由 [celestial-calendar](https://github.com/0xf3cd/celestial-calendar) 离线生成，
运行时只读这些表，不联网，也不需要安装生成工具。
农历表在 1901 至 2099 年的月长与[香港天文台历书](https://www.hko.gov.hk/en/gts/time/conversion.htm)
数据对拍；HKO 原件与解码保留为测试对照。

节气标签由计算所得的 UT1 时刻加八小时得到，1929 年前也按东八区表达，不改为北京地方平时。
表中截断到秒只是记录粒度，不表示天文计算误差小于一秒。
1972 年起 UT1 与 UTC 的差不超过 0.9 秒；此前采用 UT1 代理。
2101 至 2200 年使用 ΔT 外推，连续性不等于精度保证，也没有 HKO 独立对照。
出生归属还受 `DAY`／`HOUR`／`MINUTE` 比较粒度影响，见 {doc}`configuration`。

来源头、时标和编码约定见[历法数据维护](../contributing.md#历法数据维护)所列的数据格式说明。
