# bazi 1.0.0

- Installable `bazi` package with modular imports, Python 3.11+, inline typing and
  no runtime dependencies. Source imports now use `bazi.*`, not `src.*`.
- The wheel bundles the two encoded HKO tables and four celestial tables. The
  source archive also includes raw HKO inputs and source-verification tests.
- Existing calendar backends, rules, school defaults, JSON restoration, transits,
  relationship analysis and Interpreter remain available without data regeneration.
- `Bazi` and `Bazi.create` accept an opt-in, keyword-only east-positive longitude
  with an aware datetime for apparent-solar charts. Location-aware charts preserve
  the exact instant and frozen birth-region civil offset. Optional `civil_timezone`
  selects that basis explicitly; circular longitude correction preserves its date
  branch with natural midnight carry. Jie attribution projects both clocks in the
  same basis, while Dayun and transit ordering stay absolute. Location chart and
  context JSON retain civil, UTC and apparent coordinates. The Interpreter runner
  accepts fixed location inputs and reloadable chart exports. Legacy construction,
  JSON and knowledge content remain unchanged.
- Standard MIT permission covers author-owned material; third-party notices state
  the separate scope of embedded data and quotations.
- The manual release workflow defaults to rehearsal. Publication requires protected
  environment approval and publishes only the tested sdist and its rebuilt wheel.
- Among reference-only claims, a finite description-corpus pass corrected three wording
  defects and retained seven source-unverified semantic ambiguities; default description
  output is unchanged. The chart renderer in `run_interpreter.py` now omits headings
  whose selected description list is empty. No public description fields were added.
- Structured description queries expose immutable claims and source witnesses alongside
  the existing text lookups. The source-checkout Interpreter runner supports fixed
  births, seeded random charts, reference text, source display and explicit exports;
  its default invocation now displays one chart without exporting files.

No `src` shim, root-class facade or installed command-line entrypoint is provided.
See `README.md` for principal module interfaces and `RELEASING.md` for release
prerequisites.
