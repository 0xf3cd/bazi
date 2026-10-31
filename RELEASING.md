# 发布 bazi

手动 `release.yml` workflow 准备一份已验证 sdist 及其重建 wheel；直接构建的 wheel 只作验证对照。
没有 push/tag 发布触发器，也不接受任意 ref、包仓库或工件输入。

## 前提

作者须另行确认 PyPI 账号及 bazi 项目资格，并配置 Trusted Publisher（或 pending publisher）：
owner `0xf3cd`、repository `bazi`、workflow `release.yml`、environment `release`。
公开查询包名不保留名称，也不能证明账号就绪；仓内不存 API token。

显式创建 GitHub 环境 `release`，至少指定一名必需审阅者；自定义部署策略只能包含确切分支
`main`，不能用 tag 或通配符。作者个人批准有效，若采用此路径须允许 self-review，流程不要求两人。
只有发布任务绑定环境；前置只读 REST 检查在环境、审阅规则或确切分支策略缺失时拒绝继续。

workflow 须先存在于默认分支，才能手动触发。

## 本地保留已验证工件

按[贡献指南](CONTRIBUTING.md#准备环境)准备独立开发环境，再从源码根目录运行：

```sh
python run_package_checks.py --output-dir ../bazi-tested
python -m pip install ../bazi-tested/bazi-*-py3-none-any.whl
```

输出目录必须为空且在仓外。检查通过后，命令保留受测 sdist 及其重建 wheel；直接构建的 wheel 只作验证对照。
安装示例使用保留的 wheel，不重新构建另一份安装包。检查可能联网取得构建与类型工具，
真实安装命令的导出检查在仓外临时目录执行。

本地通过不替代正式发布运行的验证，也不证明 PyPI／GitHub 配置或发布权限已就绪。
正式发布仍使用同次发布运行产生并验证的工件，不接受任意本地路径作为发布输入。

## 演练

先判断独立演练能补上哪项验证缺口，不将它固定为每版前置。首次启用或改动发布流程、
工件封装或权限配置时，重新判断是否需要单独的只读验证。若正式流程会在写入前完成相同验证，
并在受保护环境等待人工审批，就可以直接选择正式流程。需要单独验证构建或封装时，按以下步骤演练：

1. 核对 pyproject.toml 静态版本与 RELEASE_NOTES.md；发布说明顶部一节须为 `## bazi <version>`，
   否则构建即失败。将拟发布内容合入 main 后再触发，不提前建 tag。
2. 在 main 触发 `Prepare or Publish Release`，取默认 `mode=rehearsal`。
   对触发 SHA 执行完整源码与工件验证，不绑定环境，也不取得写权限或 OIDC 权限。
3. 检查该运行的 `tested-release` 工件：dist/ 下恰有一份 wheel 与 sdist，另含发布说明、
   release.json、environments.json 与 SHA256SUMS。核对源码 SHA、run ID、版本、许可证、文件内容及校验和。
   工件三十日后过期；若可能需要恢复，须在过期前保存已批准的原字节。

演练不执行真实的 PyPI 上传或 GitHub Release 写入，不能证明这些步骤会成功。
演练工件不用于正式发布；正式运行仍须重新验证并发布自身保留的原工件，不因演练通过而省略审批或公开验收。

## 实际环境清单

`environments.json` 记录外层门禁、三次隔离构建、两个最小 wheel 消费者及 typing 消费者。
每条记录包含 Python 实现与版本、系统与架构、完整已安装发行版名称／版本及实际安装器版本。
构建成功后、隔离环境销毁前取样；typing 环境在安装 mypy 及传递依赖后取样。
安装器观察覆盖依赖安装及消费者的 pip 调用，不包含 venv／ensurepip 初始化。
安装器按调用前的实际 pip 命令记录，`runner` 表示由外层 pip 向目标安装，`target` 表示目标自己的 pip。
同一角色使用过多个版本时保留多个观察；目标里有 pip 不等于安装由它执行。

清单不含路径、环境变量、pip 配置或 `direct_url.json`。外层三次安装前的原始版本输出只作临时输入，
解析后只保留版本，不上传原文。清单在 `dist/` 外，与门禁已测试 pair 的文件名／哈希、源码 SHA 及同次运行身份绑定；
封装和两个发布任务均核对这条对应关系，缺失、截断、角色不全或身份／字节错配即失败。PyPI 仍只上传原 pair，GitHub Release 另带清单。

这是一份实际环境记录，不是依赖锁：不保证以后解析到相同环境、离线恢复或逐字节重建，也不表示依赖没有漏洞。
它能检出构建／封装之间的意外漂移；若构建任务已被控制、工件和报告一起被伪造，清单不提供独立证明。
普通无报告的包检查仍可从 sdist 或无 Git 的目录运行；导出报告须在干净 Git 检出中执行，且实际源码输入均受跟踪。
构建观察器依赖钉版 build 的 pip 调用形态，升级 build 时须重跑两种安装器分支、未知形态拒绝与消费者对照测试。

## 正式发布

1. 单独取得授权，在 main 以 `mode=release` 触发；确认触发 SHA 为拟发布提交。
   本次运行重新执行完整验证，不接受以往运行的 artifact ID。
2. 核对本次已验证 bundle 后，批准 PyPI 受保护环境。仅有 OIDC 权限的任务下载本次运行产生的
   确切不可变 artifact ID，核对校验和及身份，拒绝已存在的版本、tag 或 Release。
3. PyPI 成功后，批准 GitHub Release 任务。此任务只取得 contents 写权限，先核 PyPI 哈希，
   在已测试 SHA 建 `v<version>`，以 RELEASE_NOTES.md 顶部一节为正文创建草稿，
   上传同一字节及声明文件，核 asset 摘要后发布草稿。
   两个特权任务均不检出、构建或安装源码，也不执行工件中的代码。
   前置检查和两个特权任务均从本仓本次触发 SHA 的 HTTPS 地址取得 `run_release.py`，取用前要求该 SHA 与 workflow SHA 相同；
   只接受 HTTP 200，再按临时目录中的绝对路径以 `python -I` 执行，避免工件目录影响脚本选择或模块导入。
4. 从 PyPI 与 GitHub 独立下载两份已发布工件，与保存的校验和比较，确认 tag SHA 与 Release 元数据。
   在新环境安装已发布 wheel，重跑消费者冒烟，并核对实际 PyPI Trusted Publisher 身份与 attestations。

## 部分失败

发布不是事务。已有版本、tag 或 Release 均报错；不覆盖、不移动 tag，也不以 skip-existing 恢复。
不得重跑整个 workflow 绕过部分失败，也不得重建已经接受的字节。

若 PyPI 已有工件对而 GitHub 失败，先停下核对保存的同次运行 bundle、PyPI 摘要、tag SHA
以及草稿 Release/资产。作者须批准只补缺失步骤的定向恢复，且使用确切原字节。
已有 tag 或草稿须核验，不能移动或替换。摘要不一致须查明原因，不能自动删除、加版本或重新上传。

## 升级 action

`.github/workflows/` 下每条 `uses:` 钉 40 位 commit SHA，同行注释写版本号；策略测试只核这个形状。
Dependabot 提出升级时，审阅者按其正文的 compare 链接核对 tag 与 SHA 一致，再合并。
