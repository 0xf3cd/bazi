# 快速开始

这一页带你排盘、查看和保存结果。已有 Python 环境就从安装开始；需要新建环境时，可先看页尾的{ref}`环境准备 <quickstart-environment>`。

## 安装

需要 Python 3.11 或更高版本。可直接使用已有的 Python、conda、虚拟环境或交互环境。

```{include} ../installation.inc
```

运行时只用标准库和随包数据，不联网。普通使用不需要测试或文档构建工具。
终端操作见 {doc}`cli`；下面使用 Python API，类型从定义模块导入。

## 排第一张盘

示例用虚构的出生时间，按东八区（UTC+8）公历钟填写。默认入口的年月与东八区节气表比较，
日时按输入的钟读取，不自动换算时区；海外当地钟的用法见 {doc}`configuration`。
`BaziChart` 在 `Bazi` 之上提供十神、藏干、纳音和流运等信息。

```{testcode} quickstart-chart
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
print('四柱', ' '.join(map(str, chart.bazi.pillars)))
print('日主', chart.bazi.day_master)
print('性别', chart.bazi.gender)
```

```{testoutput} quickstart-chart
四柱 庚午 辛巳 壬午 乙巳
日主 壬
性别 female
```

把出生时间换成你的公历出生钟时；也可传无时区的 `datetime(年, 月, 日, 时, 分)`。
性别接受 `男`、`女`、`male`、`female`，输出为拉丁写法。
四柱依次为年、月、日、时，日主是日柱的天干。

上例可直接在 Python 交互环境中运行；直接输入 `chart` 还会看到一行对象摘要。
若喜欢脚本，把程序保存为 UTF-8 文件 `show_chart.py`，在该文件所在目录运行：

```sh
python show_chart.py
```

两种运行方式都使用刚才安装包的同一个环境。文件不要命名为 `bazi.py`，以免遮蔽安装包。

## 查看完整命盘文本

`basic_text(chart)` 返回纯文本，包含出生时刻、四柱十神、阴阳五行、藏干、纳音和十二长生。
下面是完整的独立例子：

```{testcode} quickstart-text
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.chart_text import basic_text

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
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

藏干十神采用单字简称，如财、才、官、杀；完整名称见 {py:class}`~bazi.defines.shishen.Shishen`。
文本用于阅读；程序要读取字段时直接使用命盘属性，不解析这些文字，见 {doc}`integration`。

## 保存文本

下面把同一张盘存为 `chart.txt`。路径相对运行代码时的当前目录，重复运行会覆盖同名文件；需保留的旧结果请先另存。

```{testsetup} quickstart-save
import os
import tempfile

_save_cwd = os.getcwd()
_save_directory = tempfile.TemporaryDirectory()
os.chdir(_save_directory.name)
```

```{testcode} quickstart-save
from pathlib import Path

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.chart_text import basic_text

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
path = Path('chart.txt')
path.write_text(basic_text(chart), encoding='utf-8')
print('已保存', path)
```

```{testoutput} quickstart-save
已保存 chart.txt
```

```{testcleanup} quickstart-save
os.chdir(_save_cwd)
_save_directory.cleanup()
```

打开 `chart.txt` 即可阅读。这是展示文本，不是可恢复的命盘记录；以后要重新排盘，保留出生输入和完整配置。
不写 Python 也可用 `bazi chart` 保存 TXT，见 {doc}`cli`。

## 下一步

默认采用 `DAY` 精度、`celestial` 后端、23:00 换日柱，以立春换年；`DAY` 不会丢弃出生小时。
这些是选定的口径，其他读法可以显式配置。

| 想做什么 | 入口 |
| --- | --- |
| 选精度、换日点、历法后端、真太阳时或流派 | {doc}`configuration` |
| 查某年／月／日／时刻的流运，列几步大运，再查关系 | {doc}`relations-transits` |
| 读取十神、藏干、纳音或检查知识前提 | {doc}`integration` |
| 不排盘，只读知识文字、出处或编辑本地副本 | {doc}`knowledge` |
| 用命令排盘、查知识或求值 | {doc}`cli` |
| 升级旧调用 | {doc}`../release-notes` |

(quickstart-environment)=
## 可选：新建环境

如果已有合适环境，跳过本节即可。需要单独的工作目录和虚拟环境时，在终端运行：

```sh
mkdir bazi-example
cd bazi-example
python -m venv .venv
```

若系统只提供 `python3`，创建时用 `python3 -m venv .venv`。随后按终端激活：

| 终端 | 命令 |
| --- | --- |
| macOS／Linux 的 sh、bash、zsh | `. .venv/bin/activate` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows cmd | `.venv\Scripts\activate.bat` |

激活后回到本页“安装”。PowerShell 若不允许激活脚本，可不激活，直接用 `.venv\Scripts\python` 代替 `python`；无需修改执行策略。
