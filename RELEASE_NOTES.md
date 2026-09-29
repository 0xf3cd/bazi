# bazi 1.0.0

- Installable `bazi` package with modular imports, Python 3.11+, inline typing and
  no runtime dependencies. Source imports now use `bazi.*`, not `src.*`.
- The wheel bundles the two encoded HKO tables and three celestial tables. The
  source archive also includes raw HKO inputs and source-verification tests.
- Existing calendar backends, rules, school defaults, JSON restoration, transits,
  relationship analysis and Interpreter remain available without data regeneration.
- Standard MIT permission covers author-owned material; third-party notices state
  the separate scope of embedded data and quotations.
- The manual release workflow defaults to rehearsal. Publication requires protected
  environment approval and publishes only the tested sdist and its rebuilt wheel.
- A finite description-corpus pass corrected three wording defects in reference-only
  claims and retained seven source-unverified semantic ambiguities; default description
  output is unchanged. The chart renderer in `run_interpreter.py` now omits headings
  whose selected description list is empty. No public description fields were added.

No `src` shim, root-class facade or installed command-line entrypoint is provided.
See `README.md` for principal module interfaces and `RELEASING.md` for release
prerequisites.
