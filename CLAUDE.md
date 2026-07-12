# CLAUDE.md — bazi

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
  silently collapse them into a single "correct" rule.
- Attribute a rule to its 流派 / source where known (docstring or comment), so the
  provenance survives in the code.
- A change to a rule is a change to *knowledge*, not just code — apply the Human-in-the-loop
  rule; confirm the 命理 basis with the author before encoding it.

## Toolchain
Build / lint / type-check / test commands live in **README.md §Instructions** — follow
those, don't restate them here. Two rules the README doesn't spell out:
- `ruff` / `mypy` run on **default** config. There is intentionally NO
  pyproject.toml / ruff.toml / mypy.ini — do NOT add one.
- Not a pip package — code runs with `src.` on path via the `run_*.py` scripts.

## File conventions
- Every source file opens with the copyright header, verbatim except the year:
  `# Copyright (C) <year> Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>`
  New files use the **current year**; never change the year on an existing file.
- Module filenames are **PascalCase** (`BaziChart.py`). NOT snake_case.
- Imports: stdlib → third-party → local (relative `from ..Defines import ...`),
  blank line between groups; long typing imports use the grouped `from typing import (…)` form.

## Ubiquitous language = Pinyin
Domain terms keep Pinyin names, never translated (`Tiangan`, `Shensha`, `he`, `chong`).
Enums carry Latin + Chinese members as aliases (`甲 = JIA`; `天干 = Tiangan`).
Prefer Chinese aliases in tests/examples (`Tiangan.甲`, `TianganRelation.合`).

## Docstrings are bilingual + structured
English first, then 中文, then `Note` / `Args` / `Return` / `Examples`; types in parens.

## Typing & immutability (non-negotiable)
- Fully typed; `mypy .` must pass. Lean on `Final/Optional/Callable/TypedDict/NamedTuple`.
- Returns immutable: `frozenset`, `frozendict` (from `..Common`), `tuple`.
  Private state snapshotted via `copy.deepcopy(...)`, stored `Final`.
- Document type aliases with a string literal above them.

## Idioms to keep
- Defensive `assert isinstance(...)` / `assert callable(...)` at function entry.
- FP where it reads well (map/filter/starmap/product/compress, walrus, functools).
- Expose computed results as `@property`.
- Deliberate vertical alignment of `=` / dict `:` — preserve when editing nearby.
- Reuse `Const`/metaclass + `#region` patterns from `Common.py`; don't reinvent.

## Tests
- Mirror src layout (`src/Utils/TianganUtils.py` → `tests/utils/test_tiangan_utils.py`).
- `unittest.TestCase` subclasses, `self.assertEqual/assertTrue`; pytest runs them.
- Data-driven: inline expected combos as literal sets. Integration → `tests/integration/`.

## AI do / don't
- DON'T add black/isort/a config file, snake_case modules, English-only docstrings,
  or English domain names — each breaks the house style.
- DON'T add deps casually; keep Requirements.txt lean.
- Anonymise any real chart in examples (化名, birthplace → province).
- Match the neighbouring file's texture; internal consistency > external "best practice".
