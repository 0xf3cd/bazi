# Bazi

面向中文用户的 Python 3.11+ 八字排盘库，提供四柱、五行、十神、纳音、关系与流运查询。
也可不创建命盘，直接查阅带出处与适用限度的知识条目。运行时只用标准库及随包数据，不联网。

## 安装

在已有的 Python、conda 或虚拟环境中安装：

```sh
python -m pip install bazi
```

需要新建环境时，见[快速开始](https://0xf3cd.github.io/bazi/latest/guides/quickstart.html)。普通使用不需要测试或文档构建工具。

## 排第一张盘

下面使用虚构的出生信息，按东八区（UTC+8）公历钟填写；默认入口不自动换算时区。
可在 Python 交互环境中直接运行，也可保存为 UTF-8 脚本后运行；不要命名为 `bazi.py`，以免遮蔽安装包。

```python
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart

chart = BaziChart(Bazi.create('1990-05-17 10:30', 'female'))
print('四柱', ' '.join(map(str, chart.bazi.pillars)))
print('日主', chart.bazi.day_master)
print('年干十神', chart.shishen.year.tiangan)
```

```text
四柱 庚午 辛巳 壬午 乙巳
日主 壬
年干十神 偏印
```

四柱依次为年、月、日、时。性别用 `female`（女）或 `male`（男）；类型从定义模块导入。
默认采用 `DAY` 精度、`celestial` 后端和 23:00 换日柱。`DAY` 只按日期比较节气，出生小时仍用于时柱。
海外当地钟与真太阳时的输入方法见[配置指南](https://0xf3cd.github.io/bazi/latest/guides/configuration.html)。

## 继续使用

以下入口是最近发布版文档；当前源码的说明另见[开发版文档](https://0xf3cd.github.io/bazi/dev/)。

- [快速开始](https://0xf3cd.github.io/bazi/latest/guides/quickstart.html)：查看命盘文本、保存结果、按需准备环境。
- [完整文档](https://0xf3cd.github.io/bazi/)：配置、关系与流运、集成开发、知识目录及 API 参考。

不写 Python 时可使用安装后的 `bazi` 命令，先运行 `bazi chart --help` 查看排盘选项。

知识的来源状态、默认展示和命盘前提分别记录；已核出处不证明条文本身为真或适用于某张命盘。
关系与前提匹配返回结构事实，不预测现实事件。

## 开发

开发环境和完整检查见[贡献指南](CONTRIBUTING.md)，升级旧调用见[发布与迁移](RELEASE_NOTES.md)。
## 贡献与许可

欢迎通过 issue 提交勘误和出处；PR 先开 issue 讨论。

作者自有材料采用 [MIT License](LICENSE)；[第三方材料说明](THIRD_PARTY_NOTICES.md) 另列历法数据、引文等权利范围，
不由作者的 MIT 授权重新许可。
