# 构建与归档文档

本地构建不会部署站点，也不会启用 GitHub Pages。站点由维护者另行启用后，开发版位于 `dev/`，发布版位于固定 tag 的同名目录，全部版本入口为 `versions/`。

## 本地检查

使用 Python 3.13+，在源码根目录安装文档依赖和历法测试工具 `celestial-calendar==0.6.1`。这个要求只适用于构建和检查文档；bazi 库仍支持 Python 3.11+，已生成的 HTML 用浏览器即可阅读，不需要 Python：

```sh
python -m pip install -r docs/requirements.txt
python -m pip install celestial-calendar==0.6.1
python run_docs.py --output-dir output_data/docs-preview
```

输出目录必须为空。命令严格构建 HTML、执行教程与 README 示例，再核对 API 地址、知识目录和内部链接；全部成功后才交付成品。打开 `output_data/docs-preview/html/index.html` 查看。

源码脚本的完整检查另需开发依赖，见 {doc}`contributing`。在 Python 3.13+ 文档开发环境中，`python run_tests.py -a -v` 包含文档任务；只运行文档可用 `python run_tests.py -nt -docs`。Python 3.11／3.12 可用 `python run_tests.py -a -v --runtime-only` 检查运行时，但它不检查文档工具或构建文档，不能替代完整门禁。临时目录遵循 Python 的标准 `TMPDIR` 等环境设置。

`run_docs.py --version vX.Y.Z` 只接受干净检出且当前提交恰为该 tag 的源码；不接受把开发源码标成任意版本。开发版也记录实际提交和工作树状态，含未提交修改的构建不能进入归档。

## 维护者手动归档

`Publish Documentation` 工作流只有手动入口，默认模式 `rehearsal` 只构建，不写归档或部署。写入与部署只允许主仓的 `main` 分支执行；PR 和普通 push 不会触发它，fork 也不满足写入和部署条件。

| 模式 | 做什么 |
| --- | --- |
| `rehearsal` | 检出并检查选定源码，上传短期构建工件，不修改站点 |
| `pending` | 将发布版列为“文档待就绪”，不伪装该目录已经可用 |
| `publish` | 归档本次构建并部署完整站点，随后回读；不直接改成 `ready` |
| `promote` | 重新核对线上字节，通过后将版本标为 `ready`，更新选择页及 `latest` |
| `resume` | 从持久归档重新部署，不重建版本 HTML |

`initialize` 仅在归档分支 `docs-site` 尚不存在时设为 `true`。初始化从已检出的固定控制提交起步，先核有效签名，再在运行专用临时分支创建归档提交；核父提交、完整树与新提交签名后才建立 `docs-site`。不改写原有源码历史，也不要求关闭签名保护。

归档分支持久保存静态文件，不以短期 Actions 工件代替多版本保留。发布版目录已有内容时拒绝异字节覆盖；`dev/` 可整目录更新。后续发布只追加本版并保留旧版原字节，不重建旧 tag。

发布版构建还要求该 tag 已有正式 GitHub Release，并携带身份一致的 `release.json`；仅能归档自身带有文档构建器的版本，不修改旧 tag 来补文档。文档发布失败不表示软件尚未发布，`pending` 与 `archived` 都显示为待就绪。

`pending` 仅登记版本，尚无归档目录；`archived` 已归档，尚未通过线上回读；`ready` 已通过线上回读，选择页才提供链接。

维护者确认平台前提后，通常先 `publish`，等自动回读完成，再运行 `promote`。`latest` 只指向已回读的 `ready` 发布版；开发版不参与。`resume` 用于归档已成功、部署或回读失败的重试；需要补归档时才重跑 `publish`。

## 平台前提与失败边界

首次实际使用前，维护者须另行将 Pages Source 设为 GitHub Actions，并检查 `github-pages` 环境、归档分支规则及默认令牌的权限。构建、归档和 Pages 部署分 job 授权，不新增个人令牌或签名密钥。签名、父提交、树、身份或回读字节不符时停止，不通过关闭保护来绕过。

归档提交已生效但响应丢失时，可从归档继续重试；初始化是否已建成以分支实际存在性为准，不能一直保留 `initialize=true`。临时分支清理失败或运行取消可能留下 `docs-site-staging-*`，确认对应运行已经结束后由维护者检查清理。

本地测试和模拟响应不能替代 GitHub 实际运行。默认令牌、规则集、工件重跑、特殊文件模式及 CDN 可见性仍需首次部署后的回读验证；在这之前不宣称站点已经上线。
