# Bazi

面向中文用户的 Python 3.11+ 八字排盘库，提供四柱、五行、十神、纳音、关系与流运查询。
也可不创建命盘，直接查阅知识条目、原文出处与适用限度。运行时只用标准库及随包数据，不联网。

## 从这里开始

- 第一次使用：按下面的[安装包路线](#安装包排第一张盘)运行 Python 程序。
- 已有源码，想直接运行脚本：看[源码脚本](#源码脚本)，安装包不提供命令行入口。
- 从 v2.3.0 升级：先看[v2.4.0 升级说明](#从-v230-升级到-v240)，其中列出存取接口删除和结构调用变化。
- 从 v2.2.0 升级：先看[v2.2.0→v2.3.0 迁移说明](#从-v220-迁移到-v230)，再看[v2.4.0 升级说明](#从-v230-升级到-v240)，无需重走新手步骤。

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

普通使用不需要安装 pytest、mypy 或文档工具。本文及下方指南对应 v2.4.0；`pip install bazi` 安装包索引中已发布的版本，其接口以[对应 tag](https://github.com/0xf3cd/bazi/tags) 下的说明为准。下例使用的基本排盘与文本接口在 v2.2.0 已提供。

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

类型从定义模块导入；安装包没有根类入口或命令行程序。

在交互环境里直接输入对象会看到一行摘要；模块 `bazi.chart_text` 提供把命盘排成纯文本的函数，见[快速开始](https://github.com/0xf3cd/bazi/blob/main/docs/guides/quickstart.md)。

## 按任务继续

| 想做什么 | 从这里开始 |
| --- | --- |
| 排第一张盘，了解默认值和输出 | [快速开始](https://github.com/0xf3cd/bazi/blob/main/docs/guides/quickstart.md) |
| 从 v2.2.0 更新到已发布 v2.3.0 的源码调用 | [迁移说明](#从-v220-迁移到-v230) |
| 从 v2.3.0 升级到 v2.4.0 | [存取接口删除与结构调用调整](#从-v230-升级到-v240) |
| 改精度、换日点、真太阳时或流派取法 | [配置与时间口径](https://github.com/0xf3cd/bazi/blob/main/docs/guides/configuration.md) |
| 查原局与流运的关系，取有限几步大运和流年 | [关系与流运](https://github.com/0xf3cd/bazi/blob/main/docs/guides/relations-transits.md) |
| 不排盘，只查条目、来源、过滤和编辑源加载 | [独立知识库指南](https://github.com/0xf3cd/bazi/blob/main/docs/guides/knowledge.md) |
| 导入、内存对象与前提匹配 | [集成开发](https://github.com/0xf3cd/bazi/blob/main/docs/guides/integration.md)、[接口契约](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md) |
| 按对象、来源、情境或判据浏览知识 | [知识目录](https://github.com/0xf3cd/bazi/blob/main/docs/catalog/index.rst) |
| 逐模块查签名、参数与条件 | [文档入口](https://github.com/0xf3cd/bazi/blob/main/docs/index.md)，构建后进入 API Reference |
| 提交勘误、出处或流派读法 | [贡献指南](https://github.com/0xf3cd/bazi/blob/main/CONTRIBUTING.md) |

完整文档由源码与知识注册表生成；构建方法见[开发](#开发)。安装包带有 `py.typed` 内联类型标注。

## 能力与解释边界

默认使用 `celestial` 后端、`DAY` 精度、晚子时 23:00 换日柱；这些是选定的口径，不是唯一读法。
`BaziSchool` 保留关系、神煞与配偶星等不同取法，出处随字段说明保留。需要比较其他排盘器时，见[外部排盘对照](https://github.com/0xf3cd/bazi/blob/main/EXTERNAL_BASELINE.md)。

知识条目分别记录来源状态、默认展示选择和前提整理状态。来源已核定不证明条文本身为真，
也不证明适用于某张命盘。前提判别不计算旺衰、喜忌、格局或现实事件；部分判据只检查前提的一部分，限度见知识目录。

v2.4.0 不提供命盘或判别结果（`ContextResult`）的保存恢复接口，知识 JSON 仅作当前编辑来源，不承诺历史结果恢复；升级前请读[升级说明](#从-v230-升级到-v240)。
v2.4.0 也调整了位置、观察请求和分析结果：原局用 `Zhu` 柱位，求值用 `observation=`。当前开发版进一步以 `reference_ids` 返回参考条目 ID，证据仍从 `evidence` 读取。新调用见[集成指南](https://github.com/0xf3cd/bazi/blob/main/docs/guides/integration.md#前提匹配结构事实不是判断)，旧构造与 dataclass 操作的影响见[结构接口迁移](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md#结构接口迁移)。
详细条件见[接口契约](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md)；各版本变化见[发布说明](https://github.com/0xf3cd/bazi/blob/main/RELEASE_NOTES.md)。

## 源码脚本

下载或克隆[源码](https://github.com/0xf3cd/bazi)后，在终端进入含 `run_interpreter.py` 的根目录。使用 Python 3.11+ 的独立环境（创建与激活方法同[上文](#1-准备环境)）。运行下面的普通排盘命令只需安装终端着色依赖，不需要整套开发工具：

```sh
python -m pip install colorama==0.4.6
```

源码根中的 `bazi/` 就是这些脚本使用的库，无须先 `pip install .`；只安装 PyPI 包不会得到这些脚本。地点盘若使用 IANA 时区，需要系统时区数据库，缺少时可运行 `python -m pip install tzdata`。地点盘的输入口径见[配置指南](https://github.com/0xf3cd/bazi/blob/main/docs/guides/configuration.md)。

| 命令 | 输出 |
| --- | --- |
| `python run_demo.py` | 命盘与大运／小运／流年的文本 |
| `python run_relationship_analyzer.py` | 夫妻宫、配偶星、原局神煞及十年流年神煞 |
| `python run_interpreter.py` | 三个任务：`chart` 展示命盘，`knowledge` 查询知识，`match` 判别前提 |

前两个默认生成随机命盘。`run_interpreter.py` 先选任务，再按需要加选项；拿不准时只写任务名，
它会告诉你下一步：`chart` 出一张随机命盘，`knowledge` 给知识库概览，`match` 列出全部判据。

展示上面同一张命盘，并把结果保存到源码根下的 `output_data/`：

```sh
python run_interpreter.py chart \
  --birth-time "1990-05-17 10:30" \
  --gender female \
  --output-dir output_data
```

上面多行命令使用 sh／bash 的 `\` 续行；在 Windows PowerShell 或 cmd 中，去掉行末 `\` 并合并成一行执行。终端会展示带颜色的命盘与条目，TXT 保存在 `output_data/interpretation_examples/0.txt`，不带终端颜色码。相对路径以运行命令时的目录为准。

给了 `--birth-time` 就要同时给 `--gender`；都不给就随机生成，随机种子打印在第一行，例如用 `chart --seed 236` 重放种子236。固定输入不要加 `--seed`。

不排盘，查询知识：

```sh
python run_interpreter.py knowledge --object tiangan.ding
python run_interpreter.py knowledge --list-values topic
```

保存知识 TXT：

```sh
python run_interpreter.py knowledge --export-knowledge-base --output-dir output_data
```

此命令把知识 TXT 按对象分类保存在 `output_data/knowledge_base/` 下，不向终端打印结果。

检查前提：先看有哪些判据和各自需要什么，再对命盘求值：

```sh
python run_interpreter.py match
python run_interpreter.py match editorial.guansha_coexistence.v1
python run_interpreter.py match editorial.guansha_coexistence.v1 \
  --birth-time "2000-01-01 12:00" \
  --gender female \
  --observation-scope natal_and_liunian \
  --ganzhi-year 2024
```

其余选项可以省略，用到再加；各任务认的选项不同：

| 选项 | 适用任务 | 作用 |
| --- | --- | --- |
| `--include-reference-only` | 三个任务 | 同时显示仅供参考的条目 |
| `--show-sources` | `chart` 展示；`knowledge` 文本导出 | 显示来源 |
| `--output-dir` | `chart`；`knowledge` 文本导出 | 保存 TXT 的目录 |
| `--knowledge-source` | `knowledge`；`match` | 读取自己的知识编辑源 |

每个任务的全部选项见 `python run_interpreter.py <任务> --help`。

命盘展示中的十神百分比只统计三个非日主明干与四支主气位置，不代表旺衰或力量。
TXT 导出拒绝覆盖知识源；用 `--output-dir` 导出命盘 TXT 时，会覆盖
`interpretation_examples/{序号}.txt` 路径上已有的同名文件，其他文件保留。

## 从 v2.2.0 迁移到 v2.3.0

本节说明已发布 v2.3.0 的源码脚本调用变化；v2.4.0 的存取接口移除另见[升级说明](#从-v230-升级到-v240)。要更新 bazi 包，可在原环境运行下面的命令；它只安装包索引中已发布的版本，不会下载或更新本地的源码脚本：

```sh
python -m pip install --upgrade bazi
```

使用源码脚本的读者需另行取得对应版本的完整源码，再在该源码根运行命令。v2.3.0 起移除不带任务名的旧平铺写法；裸调用只打印帮助，随机命盘用 `chart`。

例如 `--seed 236` 改为 `chart --seed 236`，`--query-knowledge` 改为 `knowledge --all`，
带筛选的 `--query-knowledge --object tiangan.ding` 改为 `knowledge --object tiangan.ding`，
`--match-context 判据ID …` 改为 `match 判据ID …`。上面的新写法都接在 `python run_interpreter.py` 后。

原来同时展示命盘并导出知识 TXT 的调用，拆成 `chart …` 和 `knowledge --export-knowledge-base …` 两条独立命令；
两条命令各自检查输出路径，不会预先检查彼此是否写到同一个位置；一条失败不会撤销另一条已写出的文件。弃用与移除时间线及完整对照见 [源码脚本兼容说明](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md#源码脚本)。

## 从 v2.3.0 升级到 v2.4.0

本次删除命盘／判别结果与知识快照的公开 JSON 存取、迁移模块及三类 JSON 导出参数，不保留兼容入口。请保留旧原件；需要当前结论时，按原出生输入和完整配置重新构造命盘并求值。

`profile=` 改为 `observation=`，柱位和明藏层改用枚举，岁运坐标按年／月／日期／时刻分别构造。直接构造、`replace`、`asdict` 和位置式类模式的调整见[结构接口迁移](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md#结构接口迁移)；旧字符串比较和位置式类模式可能静默失配。

重新构造命盘时，不传 `BaziSchool.kongwang_anchor` 则使用默认日柱 `Anchor.DAY`；所需读法为 `YEAR` 或 `YEAR_AND_DAY` 时需显式配置，该字段仍参与命盘身份。例子见[六甲旬空取锚](https://github.com/0xf3cd/bazi/blob/main/docs/guides/configuration.md#六甲旬空取锚)。

知识编辑源仍可用 `KnowledgeBase.load(path)` 读取，当前开发版只接受 `schema_version=3`，条目用布尔字段 `show_by_default`；边界见[接口契约](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md#知识编辑源与文本边界)。

## 开发

运行本库仍只需 Python 3.11+。**构建文档和运行完整开发检查需要 Python 3.13+**；这不会提高安装包的运行时要求。已经生成的 HTML 可直接用浏览器阅读，不需要 Python 或文档工具。

在独立的 Python 3.13+ 环境中安装开发与文档依赖，运行完整检查：

```sh
python -m pip install -r Requirements.txt
python -m pip install -r docs/requirements.txt
python -m pip install celestial-calendar==0.6.1
python run_tests.py -a -v
```

完整检查包含所有测试及 100% 库覆盖率、ruff、mypy、示例、`python -O` 输入检查、安装工件验证和文档检查。
在 Python 3.11／3.12 环境中，只安装 `Requirements.txt` 和 `celestial-calendar==0.6.1`，不安装 `docs/requirements.txt`，再运行 `python run_tests.py -a -v --runtime-only`。此命令保留全部库检查，只省去文档工具的类型检查、`tests/docs/` 测试及文档构建；它不能代替完整检查。
裸 `python run_tests.py` 不含 `slow`／`hkodata` 和可选任务，不能替代完整检查。
工件验证可能联网下载构建及类型工具；源码示例可能写入 `output_data/`。

只构建并检查文档：

```sh
python run_docs.py
```

检查严格 HTML 构建、API 地址、完整知识目录、内部链接与教程示例；通过后可本地打开 `output_data/docs/html/index.html`。
构建命令不部署站点，也不启用 Pages。更多测试选项见 `python run_tests.py --help`，外部贡献要求见[贡献指南](https://github.com/0xf3cd/bazi/blob/main/CONTRIBUTING.md)。

### 保留已验证的安装包

```sh
python run_package_checks.py --output-dir ../bazi-tested
python -m pip install ../bazi-tested/bazi-*-py3-none-any.whl
```

输出目录须为空且在仓外。发布步骤见[发布流程](https://github.com/0xf3cd/bazi/blob/main/RELEASING.md)。
重建历法表见 [HKO 编码器](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/hko_data/encoder.py)、[天文表生成器](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/celestial_data/generator.py)
及[数据格式](https://github.com/0xf3cd/bazi/blob/main/bazi/calendar/celestial_data/SCHEMA.md)。安装后缺表应重装包，不运行生成器修补。

## 贡献与许可

本库由个人维护，接受 issue 勘误与出处补充；PR 先开 issue 讨论，方向获同意后再提交，要求见[贡献指南](https://github.com/0xf3cd/bazi/blob/main/CONTRIBUTING.md)。

作者自有材料采用标准 [MIT License](https://github.com/0xf3cd/bazi/blob/main/LICENSE)。[第三方材料说明](https://github.com/0xf3cd/bazi/blob/main/THIRD_PARTY_NOTICES.md) 另列历法数据、引文等权利范围，
不由作者的 MIT 授权重新许可；两份声明都随工件分发。
