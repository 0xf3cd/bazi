# 命令行

安装包提供唯一的 `bazi` 命令，可以排盘、保存文本、查询知识和检查前提，无需编写 Python。

```{include} ../installation.inc
```

安装后可在自己的工作目录运行。未激活虚拟环境时，直接使用环境中的 `bin/bazi`（macOS／Linux）
或 `Scripts\bazi.exe`（Windows）路径。裸调用 `bazi` 只打印帮助，不写文件。

## 按出生信息排盘并保存

下面仍用虚构的出生信息。默认按东八区（UTC+8）公历钟填写，不自动换算时区：

```sh
bazi chart --birth-time "1990-05-17 10:30" --gender 女 --output chart.txt
```

终端展示盘面事实，不读取知识文件。不带终端颜色码的完整输出保存为调用目录下的
`chart.txt`。省略 `--output` 就只展示，不保存；终端输出恒带颜色码，直接重定向也会保留颜色码。
同名 TXT 会被覆盖，其他文件保留，需保留的旧结果请先另存。
`--output` 拒绝覆盖随包或本次指定的知识源；路径经 `Path.resolve()` 比较，
可识别符号链接，不检查硬链接等文件身份别名。

`--birth-time` 与 `--gender` 必须同时给或同时不给；都不给则随机排盘并打印种子，
可用 `bazi chart --seed 236` 重放，保存时也包含种子。固定出生输入不与 `--seed` 组合。

`--gender` 接受 `男`／`女`／`male`／`female`。
`--precision` 复用库的中文／英文精度写法，如 `日`／`时`／`分` 或 `day`（默认）／`hour`／`minute`。
需要真太阳时，传带时区出生时刻，
用 `--longitude` 给出经度，并选 `hour` 或 `minute` 精度；
IANA 时区需要系统时区数据库，缺少时可安装 `tzdata`。合法输入与时间含义见 {doc}`configuration`。
CLI 可选精度、经度和民用时区，其他历法后端、换日与流派字段使用 Python API 配置，不能作为 CLI 选项传入。

命盘中的十神百分比只统计三个非日主明干与四支主气位置，不代表旺衰或力量。

`--transits` 追加流运文本，`--relationship` 追加夫妻宫、配偶星、神煞、旬空和十年流年报告；
两项都可用于固定出生输入或随机盘。`--knowledge` 按日主与十神分组阅读相关条目；
十神取三处非日主明干及全部藏干，包含中气、余气。同次输出按条目 ID 去重，前提和限度仍显示。
自定义库未收录某对象或对象名有歧义时，该组显示查询错误，其他组继续展示。
查到了材料不表示它适用于此盘。

```sh
bazi chart --birth-time "1990-05-17 10:30" --gender 女 --transits --relationship --knowledge --output chart-full.txt
```

## 查询知识与出处

`bazi knowledge` 显示知识库概览。不排盘，直接查丁的知识，或列出可用主题：

```sh
bazi knowledge 丁
bazi knowledge --list-values topic
```

对象 ID 可在 {doc}`../catalog/objects` 查到。中文名须精确匹配，重名时会列出候选 ID。
查询返回全部相关条目，也可以按文字搜索：

```sh
bazi knowledge 文昌 --viewpoint XIN_XU
bazi knowledge --search "枭印"
```

多个过滤条件取交集；`--object` 也接受名称或 ID，与位置参数二选一。
`--all` 阅读全部条目，不与查询条件组合；`--list-values` 可列对象、来源、主题或读法。

展开来源定位与引文：

```sh
bazi knowledge 丁 --show-sources
```

知识查询不写文件。

校验随包知识源：

```sh
bazi knowledge --validate-knowledge
```

自己的文件可用 `bazi knowledge --knowledge-source edited.json --validate-knowledge` 校验，
再用 `bazi knowledge --knowledge-source edited.json --object tiangan.ding` 查询。
先保存可继续编辑的副本，见 {ref}`编辑知识文件 <knowledge-edit>`。
`chart` 与 `match` 下的 `--knowledge-source`、`--show-sources` 都须配合 `--knowledge` 使用。

## 查看判据、检查命盘前提

先列目录，只给 ID 时查看定义、支持范围和所需输入，补齐参数后才求值：

```sh
bazi match
bazi match editorial.guansha_coexistence.v1
bazi match editorial.guansha_coexistence.v1 --birth-time "2000-01-01 12:00" --gender female --observation-scope natal
```

`--observation-scope` 须显式选择；输出中的 `natal` 表示只观察原局。
增加单流年时使用 `natal_and_liunian` 与干支年标签：

```sh
bazi match editorial.guansha_coexistence.v1 --birth-time "2000-01-01 12:00" --gender female --observation-scope natal_and_liunian --ganzhi-year 2024
```

婚恋结构判据用 `natal_and_transits`，并按该判据的说明给出 `--transit-entry`、坐标和 `--transit-kinds`。
例如检查原局加指定时刻的大运、流年，时刻坐标按东八区填写：

```sh
bazi match editorial.spouse_palace_xingchong.v1 --birth-time "2000-01-01 12:00" --gender female --precision hour --observation-scope natal_and_transits --transit-entry at_moment --solar-moment "2024-04-10T12:00:00" --transit-kinds dayun,liunian
```

`at_moment` 需要 `hour` 或 `minute` 命盘精度，默认 `day` 盘会得到 `UNKNOWN`。
这里的 `--precision hour` 设置整张命盘的精度，含义见 {doc}`configuration`。
若要改查干支年 2024 的午月，将上例的 `--transit-entry at_moment` 改为 `--transit-entry at_month`，
把 `--solar-moment "2024-04-10T12:00:00"` 替换为 `--ganzhi-year 2024 --ganzhi-month 午`，其余参数保留。
Python 请求与结果读取见 {doc}`integration`。

`SATISFIED` 表示所选判据的结构事实满足；`NOT_SATISFIED` 表示不满足；`UNKNOWN` 表示所需观察不完整。
部分证据存在时仍可能为 `UNKNOWN`。完整前提与局部条件由判据的 `entry_role` 区分，
输出中的原因码 `premise_satisfied` 只表示当前判据的事实成立，局部条件判据也使用它。
状态不认证条文本身为真，也不预测现实事件。默认只显示判别、证据与参考 ID；
`--knowledge` 才读取并追加参考正文，不改变判据状态。自定义库缺项时显示该 ID 及“知识库未收录”。

## 随机演示与帮助

用 `chart` 的选项查看随机盘的流运与婚恋报告：

```sh
bazi chart --seed 236 --transits
bazi chart --seed 236 --relationship
```

每个任务有独立选项，完整列表见各自帮助，例如：

```sh
bazi chart --help
bazi knowledge --help
bazi match --help
```

接口的精确行为见 {doc}`../api-contract`；已有命令或旧脚本的升级条件见 {doc}`../release-notes`。
