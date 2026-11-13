# 构建与归档文档

本地构建不会部署站点，也不会启用 GitHub Pages。站点根页经 `latest/` 跳到最新已就绪的发布版；尚无已就绪发布版时，根页打开 `versions/`，不生成 `latest/`。全部版本入口为 `versions/`，开发版位于 `dev/`，发布版位于固定 tag 的同名目录。

## 本地检查

使用 Python 3.13+，在源码根目录安装文档依赖和历法测试工具 `celestial-calendar==0.6.1`。这个要求只适用于构建和检查文档；bazi 库仍支持 Python 3.11+，已生成的 HTML 用浏览器即可阅读，不需要 Python：

```sh
python -m pip install -r docs/requirements.txt
python -m pip install celestial-calendar==0.6.1
python run_docs.py --output-dir output_data/docs-preview
```

输出目录必须为空。命令严格构建 HTML、执行教程与 README 示例，再核对 API 地址、知识目录和内部链接。
API 代码围栏逐项登记，先与实际页面核对，再各自在独立进程运行并校验断言或紧随的输出，每例限时 30 秒。
出生精度的文字对照另列，不计作可执行示例。全部成功后才交付成品。打开 `output_data/docs-preview/html/index.html` 查看。

仓库的完整检查另需开发依赖，见 {doc}`contributing`。在 Python 3.13+ 文档开发环境中，`python run_tests.py -a -v` 包含文档任务；只运行文档可用 `python run_tests.py -nt -docs`。Python 3.11／3.12 可用 `python run_tests.py -a -v --runtime-only` 检查运行时，但它不检查文档工具或构建文档，不能替代完整门禁。临时目录遵循 Python 的标准 `TMPDIR` 等环境设置。

`run_docs.py --version vX.Y.Z` 只接受干净检出且当前提交恰为该 tag 的源码；不接受把开发源码标成任意版本。开发版也记录实际提交和工作树状态，含未提交修改的构建不能进入归档。

新构建在 `build.json` 的 `built` 字段记录实际 UTC 构建时间（`YYYY-MM-DDTHH:MM:SSZ`），版本信息页显示同一时间。版本列表先列最新已就绪发布版，开发版排最后，显示构建时间与源码提交；旧构建未记录时间时明确标为“构建日期未记录”，不以提交日期代替。

## 维护者手动归档

`Publish Documentation` 工作流只有手动入口，默认模式 `rehearsal` 只构建，不写归档或部署。写入与部署只允许主仓的 `main` 分支执行；PR 和普通 push 不会触发它，fork 也不满足写入和部署条件。

| 模式 | 做什么 |
| --- | --- |
| `rehearsal` | 检出并检查选定源码；选发布 tag 时也构建本次触发提交的 dev，上传短期工件，不修改站点 |
| `pending` | 将发布版列为“文档待就绪”，不伪装该目录已经可用 |
| `publish` | 归档本次构建并部署完整站点，随后回读；不直接改成 `ready` |
| `promote` | 全站回读通过后将选定版本标为 `ready`；选发布版时也提升同一归档提交的 dev（如有），更新入口 |
| `resume` | 从持久归档重新部署，可升级三份入口 HTML，不改版本清单或版本目录 |

`initialize` 仅在归档分支 `docs-site` 尚不存在时设为 `true`。初始化从已检出的固定控制提交起步，先核有效签名，再在运行专用临时分支创建归档提交；核父提交、完整树与新提交签名后才建立 `docs-site`。不改写原有源码历史，也不要求关闭签名保护。

归档分支持久保存静态文件，不以短期 Actions 工件代替多版本保留。发布版目录已有内容时拒绝异字节覆盖；`dev/` 可整目录更新。后续发布只追加本版并保留旧版原字节，不重建旧 tag。

选择发布 tag 执行 `publish` 时，同次运行先构建该 tag，再构建触发运行的固定源码提交（`github.sha`）作为 dev；两份候选由同一个工件 ID 传递，一次归档提交同时保存两版。即使补发符合下段前提的旧 tag，dev 也不取旧 tag 的源码。选 `dev` 时只更新开发版；`pending`、`promote` 和 `resume` 不重建源码。

发布版构建还要求该 tag 已有正式 GitHub Release，并携带身份一致的 `release.json`；仅能归档自身带有文档构建器的版本，不修改旧 tag 来补文档。文档发布失败不表示软件尚未发布，`pending` 与 `archived` 都显示为待就绪。

`pending` 仅登记版本，尚无归档目录；`archived` 已归档，尚未通过线上回读；`ready` 已通过线上回读，选择页才提供链接。

维护者确认平台前提后，通常先 `publish`，等自动回读完成，再运行 `promote`。全站回读逐文件核对同一归档提交，并分别计算各版摘要；提升发布版与 dev 使用各自摘要，归档分支在回读后指向了其他提交就须重新核对。新内容归档后先为 `archived`，通过回读和提升后才为 `ready`。

`latest` 只指向已回读的 `ready` 发布版；开发版不参与。`resume` 用于归档已成功、部署或回读失败的重试；需要补归档时才重跑 `publish`。工具可读取完整旧入口布局，并将其升级为新布局；`resume` 仅可更新 `index.html`、`versions/index.html`、`latest/index.html`，旧版本目录与 `versions.json` 字节不变，不接受新旧入口混搭的归档。

## 平台前提与失败边界

首次实际使用前，维护者须另行将 Pages Source 设为 GitHub Actions，并检查 `github-pages` 环境、归档分支规则及默认令牌的权限。构建、归档和 Pages 部署分 job 授权，不新增个人令牌或签名密钥。签名、父提交、树、身份或回读字节不符时停止，不通过关闭保护来绕过。

归档提交已生效但响应丢失时，可从归档继续重试；初始化是否已建成以分支实际存在性为准，不能一直保留 `initialize=true`。临时分支清理失败或运行取消可能留下 `docs-site-staging-*`，确认对应运行已经结束后由维护者检查清理。

本地测试和模拟响应不能替代 GitHub 实际运行。默认令牌、规则集、工件重跑、特殊文件模式及 CDN 可见性仍需首次部署后的回读验证；在这之前不宣称站点已经上线。
