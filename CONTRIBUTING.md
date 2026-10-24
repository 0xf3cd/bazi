# 贡献指南

本库既是八字排盘库，也记录作者整理的八字知识。欢迎以 issue 提交勘误和出处补充；PR 先开 issue 讨论，讨论通过后才接受。

## 先开 issue

| 想做的事 | 怎么提 |
| --- | --- |
| 更正某条知识，或为它补出处 | 用“知识勘误与出处补充”模板 |
| 提出另一流派的读法 | 用“流派读法提案”模板 |
| 报告程序的可复现问题 | 开普通 issue，写明 Python 版本、最小代码和实际与预期结果 |
| 改代码、文档或工具 | 开普通 issue 说明问题与方案，维护者回复同意后再写 PR |

没有 issue 讨论的 PR 不会合并。讨论通过只表示接受这个方向，PR 仍须通过下文的门禁与审阅。

## 出处要求

本库不收没有出处的规则。提交规则勘误或流派读法时，请提供可核对的原文：

- **作品、署名、版本**：古籍写书名、作者或注者、所用版本（刻本、影印本、点校本或电子书的出版信息）。
- **位置**：页码、卷次或章节；有在线原文时给出所用版本的链接，不用搜索结果或转载摘要代替原文。
- **摘录**：原文逐字摘出，保留原有字词、标点与异体字，不改写、不规范化。
- **能支持什么、不能支持什么**：一句话写清这段原文支持哪条结论，以及它没有说什么。

流派之间说法不同时，各读法分别记录并分别写出处，本库不合成一个“正确”规则。

模板收集的是线索，不是可直接导入的 JSON。没有在线链接时，也可先提交纸本作品、版本、位置和摘录，在表单指定的位置列出缺项。正式来源记录的 `url` 等必填信息须由维护者核对补齐；信息未齐不承诺入库，不编造链接或占位值。`text_layer` 的描述也由维护者核对，再映射为记录接受的 `baiwen`、`zhushi` 或 `editorial`。表单中的 `attribution` 是来源署名，条目署名由维护者另行填写。

## 来源状态的含义

来源记录用 `state`，条目用 `source_state` 表示出处整理状态。与出处核对直接相关的两种状态是：

- `witnessed`：原文出处已经核定，有可核对的作品、版本、位置和摘录。
- `unverified`：出处尚未核定，条目不绑定来源见证。

来源核定不等于命盘前提满足，也不证明现实事件。`source_state`、输出资格 `output` 和前提整理状态 `applicability` 分开记录。默认输出要求出处已核定（`witnessed`）、无命盘前提（`unconditional`），且引用来源至少有两个不同的 `lineage`。两个来源不自动构成独立见证，作品与版本是否同源仍由维护者核对。字段定义与校验见 [knowledge.py](bazi/knowledge.py)。

## 提 PR 之前

从 `main` 分支开始，一个 PR 只做 issue 中讨论过的事。知识编辑来源是 [bazi/knowledge_data.json](bazi/knowledge_data.json)，不是生成的目录页面；条目 ID 也可在该文件中查找。

### 准备环境

本库及其运行时检查支持 Python 3.11+；构建文档、检查文档工具及运行完整门禁需要 Python 3.12+。PR CI 在 3.11 上检查运行时，在 3.12 和 3.14 上运行包含文档的完整门禁，另有跨平台和 PyPy 兼容检查。本机一次运行不等于全部 CI 通过。

使用 Python 3.12+，在仓库根目录创建独立开发环境：

```sh
python -m venv .venv
```

macOS／Linux 用 `source .venv/bin/activate` 激活；Windows PowerShell 用 `.\.venv\Scripts\Activate.ps1`。激活后安装：

```sh
python -m pip install -r Requirements.txt
python -m pip install -r docs/requirements.txt
python -m pip install celestial-calendar==0.6.1
```

`Requirements.txt` 是开发依赖，`docs/requirements.txt` 是文档工具依赖，两者都不是运行时依赖；`celestial-calendar==0.6.1` 是历法测试用的工具依赖。

如果只在 Python 3.11 上检查运行时，另建 3.11 环境，只安装 `Requirements.txt` 与 `celestial-calendar==0.6.1`，使用 `python run_tests.py -a -v --runtime-only`。它保留库测试、覆盖率、lint、运行时类型检查、示例和安装工件检查，不收集 `tests/docs/` 或检查、构建文档工具；文档完整检查仍在 3.12+ 环境中执行。不要尝试在 3.11 环境安装新版 Sphinx。

生成后的 HTML 是静态文件，读者只需浏览器；阅读文档或在 Python 3.11 中运行其中的库调用示例，不需要安装文档工具。

### 完整门禁

PR 前须在上述 Python 3.12+ 开发环境、仓库根目录实跑完整 CPython 门禁：

```sh
python run_tests.py -a -v
```

完整检查包含全部测试与 100% 覆盖率检查、`ruff check`、`mypy`、两个 demo、`run_interpreter.py` 示例、`python -O` 输入契约检查、安装工件验证以及文档构建与检查。

- 裸 `python run_tests.py` 不含 `slow`、`hkodata` 测试和可选任务，不能代替完整门禁。
- 工件验证可能联网下载构建与类型工具；示例可能写入 `output_data/`。
- 只改知识 JSON 或文档也要跑完整门禁。
- 不要运行 `ruff format` 或其他自动格式化器，代码保留两空格缩进和纵向对齐。

### 提交与 PR 正文

- **提交须签名**，由维护者核验。提交信息不要带 `Co-Authored-By:`。
- **PR 正文用中文**，分四节：
  1. **内容**：改了什么、为什么；
  2. **测试**：新增或调整了哪些测试；
  3. **验证**：运行的命令与结果，如 `python run_tests.py -a -v` 的退出码；
  4. **范围说明**：没做什么，以及相关 issue 编号。
- **正文末尾写归属**，用实际贡献者的 GitHub 账号和实际使用的工具与型号，不要写会话链接。使用 AI 工具时：

  ```text
  Built by @<你的 GitHub 账号> with <工具名> (<型号>).
  ```

  用了多个工具，用 and 连接；没有使用 AI 工具，写 `Built by @<你的 GitHub 账号>.`。
- 不写本机路径、主机名等个人信息；示例命盘须匿名，用化名，出生地降到省级。

### 代码与知识的约定

- 领域术语用拼音，如 `Tiangan`、`Shensha`；JSON 中的干支、十神等领域值用中文，性别保存为 `male`／`female`，配置和键沿用既有拼写。
- 自有 API 与源码说明以中文为主，引文保留来源原有的字词和标点。
- 改知识即改规则：新增或修改条目前，须先在 issue 中让维护者核定出处与口径。

## 审阅与合并

维护者负责安排独立的正确性与设计审阅，以及修复后的复验。代理按本次任务约定完成审阅与验证；外部贡献者无需自行安排独立审阅或购买工具订阅。仓级编码与代理执行约定见 [AGENTS.md](https://github.com/0xf3cd/bazi/blob/main/AGENTS.md)。合并及是否 squash 均由维护者决定。
