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

## 演练

1. 核对 pyproject.toml 静态版本与 RELEASE_NOTES.md，将拟发布内容合入 main 后再触发，不提前建 tag。
2. 在 main 触发 `Prepare or Publish Release`，取默认 `mode=rehearsal`。
   对触发 SHA 执行完整源码与工件验证，不绑定环境，也不取得写权限或 OIDC 权限。
3. 检查该运行的 `tested-release` 工件：dist/ 下恰有一份 wheel 与 sdist，另含发布说明、
   release.json 与 SHA256SUMS。核对源码 SHA、run ID、版本、许可证、文件内容及校验和。
   工件三十日后过期；若可能需要恢复，须在过期前保存已批准的原字节。

授权正式发布前须实跑演练。本地工件与离线策略测试不能替代演练，也不能证明 GitHub/PyPI 配置就绪。

## 正式发布

1. 单独取得授权，在 main 以 `mode=release` 触发；确认触发 SHA 为拟发布提交。
   本次运行重新执行完整验证，不接受以往运行的 artifact ID。
2. 核对本次已验证 bundle 后，批准 PyPI 受保护环境。仅有 OIDC 权限的任务下载本次运行产生的
   确切不可变 artifact ID，核对校验和及身份，拒绝已存在的版本、tag 或 Release。
3. PyPI 成功后，批准 GitHub Release 任务。此任务只取得 contents 写权限，先核 PyPI 哈希，
   在已测试 SHA 建 `v<version>`，创建草稿，上传同一字节及声明文件，核 asset 摘要后发布草稿。
   两个特权任务均不检出、构建、安装或导入仓库代码。
4. 从 PyPI 与 GitHub 独立下载两份已发布工件，与保存的校验和比较，确认 tag SHA 与 Release 元数据。
   在新环境安装已发布 wheel，重跑消费者冒烟，并核对实际 PyPI Trusted Publisher 身份与 attestations。

## 部分失败

发布不是事务。已有版本、tag 或 Release 均报错；不覆盖、不移动 tag，也不以 skip-existing 恢复。
不得重跑整个 workflow 绕过部分失败，也不得重建已经接受的字节。

若 PyPI 已有工件对而 GitHub 失败，先停下核对保存的同次运行 bundle、PyPI 摘要、tag SHA
以及草稿 Release/资产。作者须批准只补缺失步骤的定向恢复，且使用确切原字节。
已有 tag 或草稿须核验，不能移动或替换。摘要不一致须查明原因，不能自动删除、加版本或重新上传。
