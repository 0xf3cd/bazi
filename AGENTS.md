# AGENTS.md — bazi

八字排盘 Python 库：排盘、五行、十神、纳音、刑冲破害、合会。
代码须沿用作者风格；风格问题先读相邻模块，不另造约定。

## 人工确认（先读）

需求有歧义、没有先例的设计分岔、无法确认的命理规则、意外测试失败，或无法从既有代码
验证意图的改动，须先向作者确认。风格模仿相邻代码，知识与行为依据由作者确认；
错误命理规则会静默影响下游解读。

## 本库也是知识库

不同流派可以有不同规则和读法，本库记录作者的八字知识：

- 刑冲破害、合会、神煞、十神等规则承载领域知识。流派有分歧时保留各读法，建模为可选变体，
  不静默合成一个“正确”规则。流派及默认值应可在运行时配置。
- 已知流派或来源写入 docstring、注释，保留出处。
- 改规则即改知识，编码前按人工确认要求核定命理依据。

## 工具链

构建、lint、类型检查与测试入口见 [README.md §开发](README.md#开发)。以下为补充约束：

- ruff 使用默认规则，少数整类例外在 `ruff.toml` 中逐项说明理由。此文件只声明规则，
  不得添加格式参数。mypy 不设配置，完整 flags 在 `run_tests.py`；`pyproject.toml` 只管打包。
- 不运行 `ruff format` 或其他自动格式化器，以免破坏刻意的纵向对齐；ruff 门禁只用 `ruff check`。
- `Requirements.txt` 固定 ruff 版本；升级须逐条审议新增规则。单处有意写法用带理由的
  `# noqa: <RULE>`；整类与领域或风格冲突时才在 `ruff.toml` 忽略。只与某一子树冲突的规则，
  可用带理由的 `per-file-ignores`。
- 安装包为 `bazi`，从定义模块导入，没有安装 CLI 或根类入口。
- 库运行时支持 Python 3.11+；文档构建、文档工具检查及完整开发门禁需要 Python 3.13+。
  已生成的 HTML 是静态文件，阅读不需要 Python。3.11／3.12 环境不安装 `docs/requirements.txt`，使用
  `run_tests.py -a -v --runtime-only`：保留全部库检查，排除 `docs/`、`tests/docs/`、
  `run_docs.py`、`run_doc_checks.py` 的文档工具类型检查和测试／构建。
  `tests/test_docs_site.py`、`tests/test_docs_workflows.py` 保留。
- PR 前须在 Python 3.13+ 文档开发环境实跑与 CI 相同的 **`run_tests.py -a -v`**；
  `--runtime-only` 不能代替该完整门禁。下列内层检查较快，但省略了两个 demo、
  `run_interpreter.py` 示例与安装工件检查，不能替代完整门禁：
  - `ruff check .`
  - `python -m mypy . --check-untyped-defs --warn-redundant-casts --warn-unused-ignores --warn-return-any --warn-unreachable`
    （裸 `mypy .` 缺少 `--warn-unreachable`。）
  - `python -m coverage run --source=bazi --omit='bazi/calendar/hko_data/encoder.py,bazi/calendar/celestial_data/generator.py' -m pytest tests/`
    然后 `python -m coverage report --show-missing --fail-under=100`，覆盖率须为 **100%**。
    没有 fail-under 时即使覆盖率下降也退出 0；CI 通过完整 runner 检查。
    有意不可达的行须有 `# pragma: no cover` 及理由。
  - `python -O tests/o_smoke.py`，公开输入的立即失败契约须在 `-O` 下保持；脚本拒绝无 `-O` 运行。
- 裸 `./run_tests.py` 默认用 `-m 'not slow and not hkodata'` 排除测试，神煞套件也在 `slow` 内。
  要验证这些测试须给 `-s -hko` 或完整调用；可用 `pytest tests/ --collect-only -q`
  对比带标记与不带标记的收集结果。

## PR 流程

- 从 main 分支开始；PR 正文用中文，分为内容、测试、验证、范围说明四节。squash 合并由作者决定。
- PR 前由维护者安排独立的正确性对抗与风格／设计审阅：R1 发现合批修复，再由 R2 复验；
  审阅者读取期间不改工作树。代理按本次任务约定完成审阅与验证；外部贡献者无需自行安排
  独立审阅或取得特定审阅工具，责任分工以[贡献指南](CONTRIBUTING.md#审阅与合并)为准。
- 提交须签名；代理使用作者批准的提交流程，不自行调用本地签名。
- PR 正文末尾以一行注明实际使用的工具，如 `Built by @0xf3cd with Claude Code (claude-opus-5).`；
  多个工具用 and 连接。不要写会话链接，其他读者无法访问。
  提交不带 `Co-Authored-By:`：squash 合并以 PR 正文为提交正文
  （`squash_merge_commit_message=PR_BODY`），归属写在进入 main 的 PR 正文中。

## 文件约定

- 源文件开头使用原样版权头，只有年份可按下述规则取值：
  `# Copyright (C) <year> Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>`。
  新文件用当年，既有文件不改年份；`__init__.py` 与根目录 `run_*.py` 不带版权头。
- 模块文件与包目录用 snake_case，如 `bazi_chart.py`、`calendar/`；类名用 PascalCase。
- 缩进为 **2 空格**，不得重缩进。
- 导入顺序为标准库、第三方、本地相对导入，组间空行；长 typing 导入用 `from typing import (…)`。
- 长调用或参数本身为调用时，逐参数换行，右括号与调用行同缩进；短调用保持单行。

  ```python
  from datetime import datetime

  from bazi.bazi import Bazi
  from bazi.school import BaziConfig

  birth_time = datetime(2000, 1, 1, 12)
  gender = 'male'
  config = BaziConfig()
  bazi = Bazi.create(
    birth_time,
    gender,
    config,
  )
  ```

## 领域命名

领域术语用拼音，不翻译为英文，如 `Tiangan`、`Shensha`、`he`、`chong`。
领域枚举提供拉丁与中文成员别名（`甲 = JIA`、`天干 = Tiangan`）；
`BaziPrecision`、`TransitKind` 等选项枚举不要求中文别名。测试和示例优先使用中文成员。
JSON 中的干支、十神等领域值用中文，供作者与下游 AI 助手读取；性别保存为 `male`／`female`。
配置选项、枚举成员名和 JSON keys 保留各自的既有拼写。

## 说明与注释语言

自有 API、模块、类、类型别名说明及源码叙述注释以中文为主，必要时保留英语辅助。
docstring 沿用 `Note` / `Args` / `Return` / `Examples`，类型放在括号中。
`rules`、`defines`、`utils`、`knowledge`、`context_matching` 等知识密集层须用中文说明规则、表与命理语义。
既有说明随相关改动更新；明确授权的全量文档整理按其任务范围执行。

tests 叙述仍用英文句子夹中文领域实体，不为统一说明语言而改写既有测试叙述；纯中文引用按原文保留。
中文叙述使用全角 `，：；（）`，英文句子用半角。**引文保留来源原有字词、标点与标记**，
不规范化口诀、古籍或第三方原文。代码、错误类型及规范消息、JSON keys、CLI flags、结构标签
不因语言整理改名。

## 类型与不可变性

- 完整类型标注，mypy 须通过；使用 `Final`、PEP 604 的 `X | None`、`Callable`、`TypedDict`、`NamedTuple`，
  不用 `Optional`。
- 返回结果不可变，使用 `frozenset`、`..common` 的 `frozendict`、`tuple`；小值类型优先 frozen dataclass，
  不手写重复的 `__init__` / `__eq__`。
- 规则表是普通 `Final` 类属性，不叠加 `classproperty` / `functools.cache`；常量无需懒加载。
- 类型别名上方用字符串说明。

## 保留的写法

- 内部辅助函数入口可用 `assert isinstance(...)` / `assert callable(...)`，调用方已在 bazi 内校验。
  公开入口显式抛 `TypeError` / `ValueError`：类型或 `callable` 检查失败为 `TypeError`，值、范围、成员
  不支持为 `ValueError`；公开枚举参数的穷尽 `else` 是成员检查，使用 `ValueError`。
  消息沿用 `Expected X, got {type(x)}` / `Unsupported ...: {value}`。
  立即失败契约须在 `python -O` 下成立，说明见 `hko_data/decoder.py`，门禁见 `tests/o_smoke.py`。
- 清晰时采用函数式写法，如 `map`/`filter`/`starmap`/`product`/`compress`、海象运算符、`functools`。
- 计算结果用 `property`；昂贵的不可变结果可用 `cached_property`。
- 保留等号、字典冒号的纵向对齐。
- 常量用普通 `Final` 类属性或模块名称，由 mypy 检查；复用 `common.py` 的 `frozendict` 与 `#region`。

## 测试

- 镜像包布局：`bazi/utils/tiangan_utils.py` 对应 `tests/utils/test_tiangan_utils.py`。
- 测试名用 `test_<行为>`，写被守住的行为或不变量，对象交给所在的文件和包；名字不超过 45 个字符。
  `tests/test_test_names.py` 对 `tests/` 内以 `test` 开头的标识符检查这一上限。
- 使用模块级 `test_*`、裸 `assert`、`pytest.raises`；字面案例表用 `parametrize`，派生案例用普通循环。
- 组合期望以内联字面集合给出；集成测试在 `tests/integration/`。

## 其他约束

不添加 black/isort/配置文件、PascalCase 模块、知识层纯英文说明或英文领域命名。
不运行格式化器，不改两空格缩进，不随意加依赖，保持 `Requirements.txt` 精简。
真实命盘示例须匿名，使用化名，出生地降到省级。
公开注释、审阅、提交、PR 不写仓外路径、主机名或工具细节；现有文件含某路径不代表可公开。
以相邻文件风格为准，内部一致性优先于外部“最佳实践”。
