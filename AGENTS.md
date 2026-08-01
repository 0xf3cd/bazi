# AGENTS.md — bazi

八字排盘引擎: 排盘、五行、十神、纳音、刑冲破害、合会.
A Python library computing Bazi (Four Pillars) charts and their relations.

This file tells any AI assistant how to write code **in the author's style**, so
contributions stay indistinguishable from hand-written code. For *style* questions,
read a neighbouring module and imitate it rather than inventing a convention.

## Human-in-the-loop (read first)
Stop and confirm with the author before proceeding whenever anything is unclear or
non-obvious — an ambiguous requirement, a design fork with no precedent in the code,
a 命理 rule you're not sure of, an unexpected test failure, or any change whose intent
you can't verify from existing code. Prefer asking over guessing: a wrong 命理 rule
silently corrupts every downstream reading. (Imitate neighbours for *style*; ask the
human for *substance*.)

## This library is (partly) a knowledge base
Bazi is not one fixed system — different 流派 (schools) hold different rules and readings.
Treat this codebase as a **codified mirror of the author's Bazi knowledge base**, not just
an engine:
- Rules (刑冲破害 / 合会 / 神煞 / 十神 …) encode domain knowledge. When schools disagree,
  **preserve the competing viewpoints** — model them as alternatives/variants; do NOT
  silently collapse them into a single "correct" rule. School selection should be
  runtime-configurable, with a configurable default (tracking: issue #69).
- Attribute a rule to its 流派 / source where known (docstring or comment), so the
  provenance survives in the code.
- A change to a rule is a change to *knowledge*, not just code — apply the Human-in-the-loop
  rule; confirm the 命理 basis with the author before encoding it.

## Toolchain
Build / lint / type-check / test commands live in **README.md §Instructions** — follow
those, don't restate them here. Two rules the README doesn't spell out:
- `ruff` runs on its default rule face minus the few family-level carve-outs in
  `ruff.toml`. That file declares the **rule face only** (ignores with a written
  rationale each); formatting/style parameters must NEVER appear in it. `mypy`
  runs config-less (flags live in `run_tests.py`) — do NOT add mypy.ini/pyproject.
- NEVER run `ruff format` (or any auto-formatter) — it destroys the deliberate
  vertical alignment (see Idioms). `ruff check` is the only ruff gate.
- `ruff` is version-pinned in Requirements.txt; bumping it is a deliberate,
  reviewed change (new default rules get triaged one by one). Resolve new-rule
  hits by fixing the code, or an inline `# noqa: <RULE>` with a reason where a
  single site is deliberate; a `ruff.toml` ignore (with rationale) is reserved
  for whole families that fight the domain or the house style; scoped carve-outs
  (`per-file-ignores`, rationale included) where a family only fights one tree.
- Not a pip package — code runs with `src.` on path via the `run_*.py` scripts.
- Before opening a PR, verify locally with the **same gates CI runs** — the PR
  workflow invokes `run_tests.py -v -s -hko -c -cr 100 -ruff -mypy -d -i -osmoke`.
  Quick local equivalent (run all four, they are all hard gates):
  - `ruff check .`
  - `python -m mypy . --check-untyped-defs --warn-redundant-casts --warn-unused-ignores --warn-return-any --warn-unreachable`
    (flags come from `run_tests.py`; a bare `mypy .` misses `--warn-unreachable`)
  - `python -m coverage run --omit='*/__init__.py,*/run_tests.py,*/tests/*,src/calendar/hko_data/encoder.py,src/calendar/celestial_data/generator.py' -m pytest tests/`
    then `python -m coverage report --show-missing` — must stay at **100%**
    (intentionally unreachable lines carry `# pragma: no cover` + a reason).
  - `python -O tests/o_smoke.py` — the public fail-fast contract must survive `-O`
    (see Idioms below; the script refuses to run without `-O`).

## PR workflow
- Branch from `main`; PR body in Chinese, four sections (内容 / 测试 / 验证 / 范围说明);
  squash-merge is the author's call.
- Before the PR: run a double review round (same process as celestial-calendar) —
  a correctness adversarial round × a style/design round; R1 findings → batched
  fixes → R2 re-verify; don't touch the worktree while reviewers read. Reviewers
  are independent AI models invoked as plain CLI (`claude -p …` / `kimi -p` /
  `grok -p`), with task briefs written to disk for the callee to read. The detailed
  playbook is the author's `review-rounds` skill
  (`~/ai_memory/skills/review-rounds/SKILL.md` — author-machine tooling, not
  tracked in this repo); contributors without it follow the summary in this bullet.
- Commits must be signed; the author signs with a hardware security key, which
  agents can't operate. Agents commit via GraphQL `createCommitOnBranch` (GitHub
  signs the commit), or write a commit script for the author to run.

## File conventions
- Every source file opens with the copyright header, verbatim except the year:
  `# Copyright (C) <year> Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>`
  New files use the **current year**; never change the year on an existing file.
  Exempt: `__init__.py` files and the root `run_*.py` entry scripts carry no header.
- Module filenames and package directories are **snake_case** (`bazi_chart.py`,
  `calendar/`). NOT PascalCase — the old PascalCase convention was a C++
  carry-over, flipped repo-wide on 2026-07-31. Class names stay PascalCase.
- Indentation is **2 spaces** (a fleet-wide convention that deliberately
  overrides PEP 8's 4) — never re-indent.
- Imports: stdlib → third-party → local (relative `from ..defines import ...`),
  blank line between groups; long typing imports use the grouped `from typing import (…)` form.
- Multi-line call layout: when an argument is itself a call, or the call grows long,
  put each argument on its own line and the closing `)` on its own line at the call's
  indentation (same rule as celestial-calendar). Trivial short calls stay on one line.
  ```python
  bazi = Bazi.create(
    birth_time,
    gender,
    precision,
  )
  ```

## Ubiquitous language = Pinyin
Domain terms keep Pinyin names, never translated (`Tiangan`, `Shensha`, `he`, `chong`).
Domain enums carry Latin + Chinese members as aliases (`甲 = JIA`; `天干 = Tiangan`).
Option-style enums (`BaziPrecision`, `TransitOptions`, …) are exempt from Chinese aliases.
Prefer Chinese aliases in tests/examples (`Tiangan.甲`, `TianganRelation.合`).
JSON output keeps domain values in Chinese (pillars, gender, …) — its consumers are
the author and AI assistants downstream.

## Docstrings are bilingual + structured
English first, then 中文, then `Note` / `Args` / `Return` / `Examples`; types in parens.
Bilingual is mandatory in knowledge-dense layers (`rules` / `defines` / `utils` /
`descriptions` — rules, tables, 命理 semantics). Infrastructure layers (`common`,
`calendar`, `transits` — mechanism code) may be English-only.

## Typing & immutability (non-negotiable)
- Fully typed; `mypy .` must pass. Lean on `Final`, `X | None` unions (PEP 604, not `Optional`), `Callable`, `TypedDict`, `NamedTuple`.
- Returns immutable: `frozenset`, `frozendict` (from `..common`), `tuple`,
  or `@dataclass(frozen=True)` for small immutable value types (the preferred shape —
  no hand-written `__init__`/`__eq__` boilerplate).
- Rule tables are plain `Final` class attributes — no `@classproperty` / `functools.cache`
  layering (the tables are constants; lazy loading buys nothing).
- Document type aliases with a string literal above them.

## Idioms to keep
- Defensive `assert isinstance(...)` / `assert callable(...)` at function entry —
  for **internal helpers only** (callers inside `src/` already validated the values).
  Public-boundary input checks are explicit `raise TypeError/ValueError` —
  `isinstance`/`callable` failures are `TypeError`; bad values, ranges and members
  are `ValueError`; messages follow `Expected X, got {type(x)}` /
  `Unsupported ...: {value}`. The fail-fast contract must survive `python -O`
  (canonical note: `hko_data/decoder.py`; gate: `tests/o_smoke.py`).
- FP where it reads well (map/filter/starmap/product/compress, walrus, functools).
- Expose computed results as `@property` (use `functools.cached_property` for
  expensive immutable results).
- Deliberate vertical alignment of `=` / dict `:` — preserve when editing nearby.
- Constants are plain `Final` class attributes or module-level names (mypy is the
  guard); reuse `frozendict` + `#region` from `common.py`; don't reinvent machinery.

## Tests
- Mirror src layout (`src/utils/tiangan_utils.py` → `tests/utils/test_tiangan_utils.py`).
- Plain pytest style: module-level `test_*` functions, bare `assert`, `pytest.raises`;
  `pytest.mark.parametrize` for literal case tables, plain loops for derived ones.
- Data-driven: inline expected combos as literal sets. Integration → `tests/integration/`.

## AI do / don't
- DON'T add black/isort/a config file, PascalCase module filenames, English-only
  docstrings in knowledge-dense layers, or English domain names — each breaks the
  house style. DON'T run `ruff format` or re-indent (2-space indent is charter).
- DON'T add deps casually; keep Requirements.txt lean.
- Anonymise any real chart in examples (化名, birthplace → province).
- Match the neighbouring file's texture; internal consistency > external "best practice".
