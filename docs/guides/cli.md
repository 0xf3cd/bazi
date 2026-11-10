# 命令行

安装包提供唯一的 `bazi` 命令，可以排盘、保存文本、查询知识和检查前提，无需编写 Python。

```{include} ../installation.inc
```

安装后可在自己的工作目录运行。未激活虚拟环境时，直接使用环境中的 `bin/bazi`（macOS／Linux）
或 `Scripts\bazi.exe`（Windows）路径。裸调用 `bazi` 只打印帮助，不写文件。

## 按出生信息排盘并保存

下面仍用虚构的出生信息。默认按东八区（UTC+8）公历钟填写，不自动换算时区：

```sh
bazi chart --birth-time "1990-05-17 10:30" --gender female --output-dir output_data
```

终端展示命盘与默认知识条目；不带终端颜色码的 TXT 保存为调用目录下的
`output_data/interpretation_examples/0.txt`。省略 `--output-dir` 就只展示，不保存。
同名 TXT 会被覆盖，其他文件保留，需保留的旧结果请先另存。

`--birth-time` 与 `--gender` 必须同时给或同时不给；都不给则随机排盘并打印种子，
可用 `bazi chart --seed 236` 重放。固定出生输入不与 `--seed` 或大于 1 的 `--count` 组合。

默认精度是 `day`。需要真太阳时，传带时区出生时刻、经度和 `hour`／`minute` 精度；
IANA 时区需要系统时区数据库，缺少时可安装 `tzdata`。合法输入与时间含义见 {doc}`configuration`。
CLI 可选精度、经度和民用时区，其他历法后端、换日与流派字段使用 Python API 配置，不能作为 CLI 选项传入。

命盘中的十神百分比只统计三个非日主明干与四支主气位置，不代表旺衰或力量。

## 查询知识与出处

不排盘，直接查丁的知识，或列出可用主题：

```sh
bazi knowledge --object tiangan.ding
bazi knowledge --list-values topic
```

对象 ID 可在 {doc}`../catalog/objects` 查到。默认只返回默认展示条目；例如文昌的条目均仅供参考，须显式包含：

```sh
bazi knowledge --object shensha.wenchang --include-reference-only
```

默认查询为空而相同条件有参考条目时，命令会提示 `--include-reference-only`，不会自动放开展示。
多个过滤条件取交集；CLI 不提供中文名称或关键词搜索参数，名称和字面搜索用 {doc}`knowledge` 的 Python API。

导出天干与十神知识 TXT，并附来源详情：

```sh
bazi knowledge --export-knowledge-base --show-sources
```

文件默认写在调用目录的 `output_data/knowledge_base/{tiangan,shishen}/`；
加 `--output-dir out` 则写到 `out/knowledge_base/`。此导出命令不向终端打印结果。
命盘展示与知识导出是独立命令，各自拒绝覆盖包内或自定义知识源，不提供跨命令整体回滚。

校验随包知识源：

```sh
bazi knowledge --validate-knowledge
```

自己的文件可用 `bazi knowledge --knowledge-source edited.json --validate-knowledge` 校验，
再用 `bazi knowledge --knowledge-source edited.json --object tiangan.ding` 查询。
先保存可继续编辑的副本，见 {ref}`编辑知识文件 <knowledge-edit>`；`--knowledge-source` 也可用于 `bazi match`，不用于 `bazi chart`。

## 查看判据、检查命盘前提

先列目录，只给 ID 时查看定义、支持范围和所需输入，补齐参数后才求值：

```sh
bazi match
bazi match editorial.guansha_coexistence.v1
bazi match editorial.guansha_coexistence.v1 --birth-time "2000-01-01 12:00" --gender female --observation-scope natal
```

`--observation-scope` 须显式选择。增加单流年时使用 `natal_and_liunian` 与干支年标签：

```sh
bazi match editorial.guansha_coexistence.v1 --birth-time "2000-01-01 12:00" --gender female --observation-scope natal_and_liunian --ganzhi-year 2024
```

婚恋结构判据用 `natal_and_transits`，并按该判据的说明给出 `--transit-entry`、坐标和 `--transit-kinds`。
时刻坐标按东八区填写，`at_moment` 还需要支持的命盘精度；默认 `day` 盘会得到 `UNKNOWN`。
Python 请求与结果读取见 {doc}`integration`。

`SATISFIED` 表示所选判据的结构事实满足；`NOT_SATISFIED` 表示不满足；`UNKNOWN` 表示所需观察不完整。
部分证据存在时仍可能为 `UNKNOWN`。完整前提与局部条件由判据的 `entry_role` 区分，
状态不认证条文本身为真，也不预测现实事件。`--include-reference-only` 只改变参考文字的展示，不改变判据状态。

## 随机演示与帮助

两个演示任务不写文件，均支持种子重放：

```sh
bazi demo --seed 236
bazi relationship --seed 236
```

前者给完整命盘与流运文本；后者给夫妻宫、配偶星、原局神煞、旬空和连续十年流年报告。
每个任务有独立选项，完整列表见各自帮助，例如：

```sh
bazi chart --help
bazi knowledge --help
bazi match --help
```

接口的精确行为见 {doc}`../api-contract`；已有命令或旧脚本的升级条件见 {doc}`../release-notes`。
