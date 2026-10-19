# Bazi

面向中文用户的 Python 3.11+ 八字排盘库，提供四柱、五行、十神、纳音、关系与流运查询。
也可不创建命盘，直接查阅知识条目、原文出处与适用限度。运行时只用标准库及随包数据，不联网。

## 安装与第一张盘

```sh
python -m pip install bazi
```

下面的基本排盘示例可独立运行。本文及下方各指南对应当前源码；已发布版本以[对应 tag](https://github.com/0xf3cd/bazi/tags) 下的说明为准。
从源码试用当前接口时，在仓库根目录运行 `python -m pip install .`。

```python
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

```text
四柱 庚午 辛巳 壬午 乙巳
日主 壬
性别 female
精度与后端 day celestial
```

类型从定义模块导入；安装包没有根类入口或命令行程序。领域名称用拼音，枚举另有中文别名。

在交互环境里直接输入对象会看到一行摘要；`bazi.chart_text` 可把命盘排成纯文本，见[快速开始](https://github.com/0xf3cd/bazi/blob/main/docs/guides/quickstart.md)。

## 按任务继续

| 想做什么 | 从这里开始 |
| --- | --- |
| 排第一张盘，了解默认值和输出 | [快速开始](https://github.com/0xf3cd/bazi/blob/main/docs/guides/quickstart.md) |
| 改精度、换日点、真太阳时或流派取法 | [配置与时间口径](https://github.com/0xf3cd/bazi/blob/main/docs/guides/configuration.md) |
| 查原局与流运的关系，取有限几步大运和流年 | [关系与流运](https://github.com/0xf3cd/bazi/blob/main/docs/guides/relations-transits.md) |
| 不排盘，只查条目、来源、过滤和导出重载 | [独立知识库指南](https://github.com/0xf3cd/bazi/blob/main/docs/guides/knowledge.md) |
| 导入、JSON 恢复、前提匹配与记录兼容 | [集成开发](https://github.com/0xf3cd/bazi/blob/main/docs/guides/integration.md)、[接口与记录契约](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md) |
| 按对象、来源、情境或判据浏览知识 | [知识目录](https://github.com/0xf3cd/bazi/blob/main/docs/catalog/index.rst) |
| 逐模块查签名、参数与条件 | [文档入口](https://github.com/0xf3cd/bazi/blob/main/docs/index.md)，构建后进入 API Reference |
| 提交勘误、出处或流派读法 | [贡献指南](https://github.com/0xf3cd/bazi/blob/main/CONTRIBUTING.md) |

完整文档由源码与知识注册表生成；构建方法见[开发](#开发)。安装包带有 `py.typed` 内联类型标注。

## 能力与解释边界

默认使用 `celestial` 后端、`DAY` 精度、晚子时 23:00 换日柱；这些是选定的口径，不是唯一读法。
`BaziSchool` 保留关系、神煞与配偶星等不同取法，出处随字段说明保留。需要比较其他排盘器时，见[外部排盘对照](https://github.com/0xf3cd/bazi/blob/main/EXTERNAL_BASELINE.md)。

知识条目分别记录来源状态、输出资格和前提整理状态。来源已核定不证明条文本身为真，
也不证明适用于某张命盘。前提判别不计算旺衰、喜忌、格局或现实事件；部分判据只检查前提的一部分，限度见知识目录。

三类 JSON 的恢复保证不同：命盘重算并核对，知识库恢复内容，前提判别记录只校验记录结构而不重判。
详细条件见[接口与记录契约](https://github.com/0xf3cd/bazi/blob/main/API_CONTRACT.md)；升级变化见[发布说明](https://github.com/0xf3cd/bazi/blob/main/RELEASE_NOTES.md)。

## 源码脚本

以下脚本需先按[开发](#开发)安装依赖，在仓库根目录运行，不是安装包的命令行入口。

| 命令 | 输出 |
| --- | --- |
| `python run_demo.py` | 命盘、大运／小运／流年及命盘 JSON |
| `python run_relationship_analyzer.py` | 夫妻宫、配偶星、原局神煞及十年流年神煞 |
| `python run_interpreter.py` | 三个任务：`chart` 展示命盘，`knowledge` 查询知识，`match` 判别前提 |

前两个默认生成随机命盘。`run_interpreter.py` 先选任务，再按需要加选项；拿不准时只写任务名，
它会告诉你下一步：`chart` 出一张随机命盘，`knowledge` 给知识库概览，`match` 列出全部判据。

展示一张命盘；不给 `--birth-time` 就随机生成，随机命盘的种子打印在第一行，用 `--seed` 重放：

```sh
python run_interpreter.py chart \
  --birth-time "2000-01-01 12:00" \
  --gender male
```

不排盘，查询知识：

```sh
python run_interpreter.py knowledge --object tiangan.ding
python run_interpreter.py knowledge --list-values topic
```

检查前提：先看有哪些判据和各自需要什么，再对命盘求值并导出记录：

```sh
python run_interpreter.py match
python run_interpreter.py match editorial.guansha_coexistence.v1
python run_interpreter.py match editorial.guansha_coexistence.v1 \
  --birth-time "2000-01-01 12:00" \
  --gender female \
  --observation-scope natal_and_liunian \
  --ganzhi-year 2024 \
  --export-context-json output_data/context.json
```

其余选项都可以省略，用到再加：`--include-reference-only` 同时显示仅供参考的条目，`--show-sources` 显示来源，
`--export-chart-json`、`--export-knowledge-json` 导出可重新载入的 JSON。每个任务的全部选项见
`python run_interpreter.py <任务> --help`。

不带任务名的旧写法（如 `python run_interpreter.py --seed 236`）这一版仍然可用，并在标准错误里提示等价的新命令，
将来会移除。命盘展示中的十神百分比只统计三个非日主明干与四支主气位置，不代表旺衰或力量。
JSON 导出拒绝覆盖知识源；用 `--output-dir` 导出命盘 TXT 时，会覆盖
`interpretation_examples/{序号}.txt` 路径上已有的同名文件，其他文件保留。

## 开发

在独立 Python 环境中安装开发与文档依赖，运行完整检查：

```sh
python -m pip install -r Requirements.txt
python -m pip install -r docs/requirements.txt
python -m pip install celestial-calendar==0.6.1
python run_tests.py -a -v
```

完整检查包含所有测试及 100% 库覆盖率、ruff、mypy、示例、`python -O` 输入检查、安装工件验证和文档检查。
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
