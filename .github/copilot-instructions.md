# Copilot Instructions — bazi

八字排盘引擎 (Bazi/Four Pillars library). Conventions live in `CLAUDE.md` and `README.md` §Instructions — read them first.

## Review focus

- **This repo is partly a knowledge base**: rules (刑冲破害 / 合会 / 神煞 / 十神) encode domain knowledge, and 流派 (schools) legitimately disagree. **Never silently collapse competing rules into one "correct" answer** — variants must be preserved as alternatives. Any rule change without a stated 命理 basis or source attribution in a comment/docstring is high-severity.
- **Domain changes need provenance**: new or modified rules should cite their 流派/source; treat a missing citation like a missing test.
- **No config files**: `ruff` and `mypy` run on default config intentionally — there is no and must be no `pyproject.toml` / `ruff.toml` / `mypy.ini`. Flag any PR that adds one.
- **File header**: every source file opens with the verbatim copyright header (`# Copyright (C) <year> Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>`); new files use the current year, existing years never change.
- Python ≥ 3.11; not a pip package — code runs with `src.` on path via `run_*.py` scripts; do not suggest packaging changes.
- Style: imitate neighbouring modules; 2-space indent.
