# Copilot 指令 — bazi

八字排盘 Python 库。先读 AGENTS.md 与 README.md §开发。

## 审阅重点

- 本仓也是知识库：刑冲破害、合会、神煞、十神规则承载命理知识。流派有分歧时保留各读法，
  不静默合成一个“正确”答案。规则变更缺少命理依据或注释／docstring 出处，按高严重度处理。
- 新增或修改规则须注明流派／来源；缺出处与缺测试同样需要修复。
- 源文件须有原样版权头 `# Copyright (C) <year> Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>`，
  新文件用当年，既有年份不改；豁免按 AGENTS.md。
- Python ≥ 3.11，bazi 安装包从定义模块导入，没有根类入口或安装 CLI。
  pyproject.toml 只管打包，保留延迟导入及显式运行时数据清单。
- 模仿相邻模块，缩进两空格。API 说明与源码叙述中文优先；tests 仍英文叙述夹中文实体。
  引文、数据、错误消息、JSON keys、CLI flags 与结构标签保留原文或原拼写。
