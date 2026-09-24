# Third-Party Material

`LICENSE` grants MIT permission for material authored by Ningqi Wang. It does not
relicense third-party data, quotations or reference material included in this project.

- The raw calendar inputs and encoded tables in `bazi/calendar/hko_data/data/`
  derive from the Hong Kong Observatory's Gregorian-Lunar calendar conversion
  tables: https://www.hko.gov.hk/en/gts/time/conversion.htm.
  Consult the Observatory's terms: https://www.hko.gov.hk/en/readme/readme.htm.
- The tables in `bazi/calendar/celestial_data/data/` were generated with
  [celestial-calendar](https://github.com/0xf3cd/celestial-calendar). Their original
  generation headers record the version, algorithms and provenance. The schema
  documentation, `bazi/calendar/celestial_data/SCHEMA.md`, is in the source archive,
  not the wheel.
- The MIT grant for original code does not grant rights in third-party quotations,
  reference material or interpretive corpus content. Citations are retained where
  present; they identify sources, not grants of permission.
- External calculator observations in `tests/integration/external_baseline.json`
  identify their source, configuration and capture date. They are reference
  observations, separate from the author-owned comparison tests and bazi snapshots.

Inclusion in a wheel or source archive does not settle rights in third-party
material. No blanket license expression is asserted for the combined distribution.
