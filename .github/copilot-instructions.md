# Copilot Instructions — bazi

八字排盘引擎 (Bazi/Four Pillars library). Conventions live in `AGENTS.md` and `README.md` §Instructions — read them first.

## Review focus

- **This repo is partly a knowledge base**: rules (刑冲破害 / 合会 / 神煞 / 十神) encode domain knowledge, and 流派 (schools) legitimately disagree. **Never silently collapse competing rules into one "correct" answer** — variants must be preserved as alternatives. Any rule change without a stated 命理 basis or source attribution in a comment/docstring is high-severity.
- **Domain changes need provenance**: new or modified rules should cite their 流派/source; treat a missing citation like a missing test.
- **File header**: every source file opens with the verbatim copyright header (`# Copyright (C) <year> Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>`); new files use the current year, existing years never change.
- Python ≥ 3.11; installable `bazi` package with modular imports, no root-class facade or installed CLI. `pyproject.toml` is packaging-only; preserve lazy imports and the explicit runtime-data roster.
- Style: imitate neighbouring modules; 2-space indent.
