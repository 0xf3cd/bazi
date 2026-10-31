# Bazi

面向中文用户的 Python 3.11+ 八字排盘库，提供四柱、五行、十神、纳音、关系与流运查询。
也可不创建命盘，直接查阅知识条目、原文出处与适用限度。运行时只用标准库及随包数据，不联网。

## 从这里开始

- 第一次使用：按下面的[安装包路线](#安装包排第一张盘)运行 Python 程序。
- 想在终端操作：看[命令行](#命令行)的安装与用法。

## 安装包：排第一张盘

### 1. 准备环境

需要 Python 3.11 或更高版本。在终端中选一个空文件夹作为工作目录，例如：

```sh
mkdir bazi-example
cd bazi-example
python -m venv .venv
```

激活刚创建的环境，再安装包；后面的 `python` 都使用这个环境：

| 终端 | 激活命令 |
| --- | --- |
| macOS／Linux 的 sh、bash、zsh | `. .venv/bin/activate` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows cmd | `.venv\Scripts\activate.bat` |

如果系统只提供 `python3`，创建环境时用 `python3 -m venv .venv`。PowerShell 若不允许激活脚本，可不激活，直接用 `.venv\Scripts\python` 代替下文的 `python`；不需要修改执行策略。

```sh
python -m pip install bazi
```

普通使用不需要安装 pytest、mypy 或文档工具。本文对应当前源码；`pip install bazi` 安装包索引中已发布的版本，其接口以[对应 tag](https://github.com/0xf3cd/bazi/tags) 下的说明为准。终端使用及源码安装见[命令行](#命令行)。

### 2. 填写出生信息

在工作目录中创建 UTF-8 文件 `first_chart.py`，复制下面的完整程序。不要把文件命名为 `bazi.py`，否则会遮蔽安装包。

示例出生信息是虚构的。本例按东八区（UTC+8）的公历钟填写 `datetime(年, 月, 日, 时, 分)`，性别用 `female`（女）或 `male`（男）。默认入口不做时区换算：年月柱与东八区节气表比较，日柱、时柱按输入的钟读取；默认 `DAY` 只按日期比较节气，小时仍用于时柱。海外当地钟不能直接当作本例输入；转成北京时间也会改变日柱、时柱所用的钟，见[配置与时间口径](https://github.com/0xf3cd/bazi/blob/main/docs/guides/configuration.md#默认输入东八区节表与输入钟)。

```python
from datetime import datetime
from pathlib import Path

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.chart_text import basic_text

bazi = Bazi.create(datetime(1990, 5, 17, 10, 30), 'female')
chart = BaziChart(bazi)

print('四柱', ' '.join(str(pillar) for pillar in bazi.pillars))
print('日主', bazi.day_master)
print('性别', bazi.gender)
print('精度与后端', bazi.config.precision, bazi.config.backend)

Path('chart.txt').write_text(basic_text(chart), encoding='utf-8')
print('已保存 chart.txt')
```

```text
四柱 庚午 辛巳 壬午 乙巳
日主 壬
性别 female
精度与后端 day celestial
已保存 chart.txt
```

### 3. 运行、读盘与保存

在终端中保持当前目录为 `first_chart.py` 所在文件夹，运行：

```sh
python first_chart.py
```

上面的输出依次给出年、月、日、时四柱，日主为壬。`chart.txt` 是可直接打开的基本命盘文本，不含流运；文件写在运行命令时的当前目录，重复运行会覆盖同名文件，请先保留需要的旧结果。

类型从定义模块导入；安装包没有根类入口。终端操作见下方 `bazi` 命令的安装与用法。

在交互环境里直接输入对象会看到一行摘要；模块 `bazi.chart_text` 提供把命盘排成纯文本的函数，见[快速开始](https://github.com/0xf3cd/bazi/blob/main/docs/guides/quickstart.md)。

## 按任务继续

| 想做什么 | 从这里开始 |
| --- | --- |
| 排第一张盘，了解默认值和输出 | [快速开始](https://github.com/0xf3cd/bazi/blob/main/docs/guides/quickstart.md) |
| 改精度、换日点、真太阳时或流派取法 | [配置与时间口径](https://github.com/0xf3cd/bazi/blob/main/docs/guides/configuration.md) |
| 查原局与流运的关系，取有限几步大运和流年 | [关系与流运](https://github.com/0xf3cd/bazi/blob/main/docs/guides/relations-transits.md) |
| 不排盘，只查条目、来源、过滤和编辑源加载 | [独立知识库指南](https://github.com/0xf3cd/bazi/blob/main/docs/guides/knowledge.md) |
| 导入、内存对象与前提匹配 | [集成开发](https://github.com/0xf3cd/bazi/blob/main/docs/guides/integration.md)、[接口契约](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md) |
| 按对象、来源、情境或判据浏览知识 | [知识目录](https://github.com/0xf3cd/bazi/blob/main/docs/catalog/index.rst) |
| 逐模块查签名、参数与条件 | [文档入口](https://github.com/0xf3cd/bazi/blob/main/docs/index.md)，构建后进入 API Reference |
| 提交勘误、出处或流派读法 | [贡献指南](https://github.com/0xf3cd/bazi/blob/main/CONTRIBUTING.md) |

完整文档由源码与知识注册表生成；本地构建见[贡献指南](https://github.com/0xf3cd/bazi/blob/main/CONTRIBUTING.md#只构建并检查文档)。安装包带有 `py.typed` 内联类型标注。

## 能力与解释边界

默认使用 `celestial` 后端、`DAY` 精度、晚子时 23:00 换日柱；这些是选定的口径，不是唯一读法。
`BaziSchool` 保留关系、神煞与配偶星等不同取法，出处随字段说明保留。需要比较其他排盘器时，见[外部排盘对照](https://github.com/0xf3cd/bazi/blob/main/EXTERNAL_BASELINE.md)。

知识条目分别记录来源状态、默认展示选择和前提整理状态。来源已核定不证明条文本身为真，
也不证明适用于某张命盘。前提判别不计算旺衰、喜忌、格局或现实事件；部分判据只检查前提的一部分，限度见知识目录。

本库不提供命盘或判别结果（`ContextResult`）的保存恢复接口；知识 JSON 仅作当前编辑来源，不承诺历史结果恢复。
当前内存结果的读取、观察范围与参考条目用法见[集成指南](https://github.com/0xf3cd/bazi/blob/main/docs/guides/integration.md#前提匹配结构事实不是判断)，完整输入、返回与错误条件见[接口契约](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md)。
已有调用或旧脚本的升级条件统一见[发布与迁移](https://github.com/0xf3cd/bazi/blob/main/RELEASE_NOTES.md)。

## 命令行

安装包提供唯一的 `bazi` 命令，不额外安装终端着色库。在上面的 Python 3.11+ 独立环境中，安装或更新到包含此命令的版本：

```sh
python -m pip install --upgrade "bazi>=2.5.0"
```

要使用仓库当前源码，下载或克隆[源码](https://github.com/0xf3cd/bazi)，进入源码根目录，在同一环境中安装：

```sh
python -m pip install .
```

安装后可以离开源码目录，在自己的工作目录运行以下命令。未激活环境时，直接指定该虚拟环境中 `bin/bazi`（macOS／Linux）或 `Scripts\bazi.exe`（Windows）的完整路径。地点盘若使用 IANA 时区，需要系统时区数据库，缺少时可运行 `python -m pip install tzdata`；输入口径见[配置指南](https://github.com/0xf3cd/bazi/blob/main/docs/guides/configuration.md)。

| 命令 | 输出 |
| --- | --- |
| `bazi demo` | 随机命盘与完整大运／小运／流年文本 |
| `bazi relationship` | 夫妻宫、配偶星、原局神煞、旬空及连续十年流年报告 |
| `bazi chart` | 命盘与解释条目，可选固定出生输入或随机命盘 |
| `bazi knowledge` | 知识概览、查询、校验与 TXT 导出 |
| `bazi match` | 判据目录、输入说明与前提求值 |

裸调用 `bazi` 只打印帮助，不写文件。先选任务，再按需加选项：`chart` 出一张随机命盘，`knowledge` 给知识库概览，`match` 列出全部判据。两个演示任务同样支持种子重放：

```sh
bazi demo --seed 236
bazi relationship --seed 236
```

展示上面同一张命盘，并把结果保存到当前目录下的 `output_data/`：

```sh
bazi chart \
  --birth-time "1990-05-17 10:30" \
  --gender female \
  --output-dir output_data
```

上面多行命令使用 sh／bash 的 `\` 续行；在 Windows PowerShell 或 cmd 中，去掉行末 `\` 并合并成一行执行。终端会展示带颜色的命盘与条目，TXT 保存在 `output_data/interpretation_examples/0.txt`，不带终端颜色码。相对路径以运行命令时的目录为准。

`--birth-time` 与 `--gender` 必须同时给或同时不给；都不给就随机生成，并在第一行打印种子。要重放同一张随机盘，可用 `chart --seed 236`；固定输入不要加 `--seed`。

不排盘，查询知识：

```sh
bazi knowledge --object tiangan.ding
bazi knowledge --list-values topic
```

保存知识 TXT：

```sh
bazi knowledge --export-knowledge-base
```

`bazi knowledge --export-knowledge-base` 默认在**调用时当前目录**的 `output_data/knowledge_base/` 下保存知识 TXT；改用 `--output-dir out` 则写到 `out/knowledge_base/`。该命令不向终端打印结果。命盘只有显式给出 `--output-dir` 才写文件，不会默认导出。两个演示任务不写文件，也不把结果写入安装目录。

检查前提：先看有哪些判据和各自需要什么，再对命盘求值：

```sh
bazi match
bazi match editorial.guansha_coexistence.v1
bazi match editorial.guansha_coexistence.v1 \
  --birth-time "2000-01-01 12:00" \
  --gender female \
  --observation-scope natal_and_liunian \
  --ganzhi-year 2024
```

其余选项可以省略，用到再加；各任务认的选项不同：

| 选项 | 适用任务 | 作用 |
| --- | --- | --- |
| `--include-reference-only` | `chart`、`knowledge`、`match` | 默认省略仅供参考的条目；加此选项一起显示 |
| `--show-sources` | `chart` 展示；`knowledge` 文本导出 | 显示来源 |
| `--output-dir` | `chart`；`knowledge` 文本导出 | 保存 TXT 的目录 |
| `--knowledge-source` | `knowledge`；`match` | 读取自己的知识编辑源 |

各任务的全部选项见该任务的 `--help`，例如 `bazi chart --help`。

命盘展示中的十神百分比只统计三个非日主明干与四支主气位置，不代表旺衰或力量。
TXT 导出拒绝覆盖知识源；用 `--output-dir` 导出命盘 TXT 时，会覆盖
`interpretation_examples/{序号}.txt` 路径上已有的同名文件，其他文件保留。

## 开发

运行本库只需 Python 3.11+；文档构建和完整开发检查需要 Python 3.13+。
开发环境、`python run_tests.py -a -v`、单独构建文档及历法数据维护见[贡献指南](https://github.com/0xf3cd/bazi/blob/main/CONTRIBUTING.md)。
保留已验证安装工件与发布步骤见[发布流程](https://github.com/0xf3cd/bazi/blob/main/RELEASING.md)。

## 贡献与许可

本库由个人维护，接受 issue 勘误与出处补充；PR 先开 issue 讨论，方向获同意后再提交，要求见[贡献指南](https://github.com/0xf3cd/bazi/blob/main/CONTRIBUTING.md)。

作者自有材料采用标准 [MIT License](https://github.com/0xf3cd/bazi/blob/main/LICENSE)。[第三方材料说明](https://github.com/0xf3cd/bazi/blob/main/THIRD_PARTY_NOTICES.md) 另列历法数据、引文等权利范围，
不由作者的 MIT 授权重新许可；两份声明都随工件分发。
