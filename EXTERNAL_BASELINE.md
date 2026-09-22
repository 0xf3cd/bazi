# External chart baseline

[The fixture](tests/integration/external_baseline.json) preserves sixteen synthetic
inputs, their results under twelve named bazi configurations, and observations from
three external calculators. It is a regression baseline for comparing configurations.
An external result can match several configurations or none of them.

Run the comparison offline from the source checkout:

```sh
python -m pytest tests/integration/test_external_baseline.py -v
```

The test needs neither the external packages nor access to the web calculators.
It recomputes the bazi results and checks the recorded sets of matching profiles.
Updating an expected result requires reviewing its configuration and source evidence;
agreement between calculators does not by itself determine a 命理 rule.

## Inputs and sources

The published cases were selected from forty synthetic boundary and control inputs.
They cover entry into 闰二月, 清明, minute ties at 立春, late 子时, a 子时 spanning
midnight, both orders of 春节 and 立春, gender pairing, and 起运 near 立春.
Case IDs identify inputs, not people.

All inputs use the same naive Gregorian civil components at minute resolution.
The reference clock is UTC+08:00, with no geographic, daylight-saving or solar-time
conversion applied. A reference longitude of 120°E is recorded where the source
accepts it; a common location interface is not assumed.

| Source | Recorded configuration | Identity and limits |
| --- | --- | --- |
| bazi | CELESTIAL × DAY/HOUR/MINUTE × WAN_ZISHI/ZIZHENG × JIE_PROJECTED/FIXED_DECADE | Commit and table fingerprint are in the fixture; other school fields are explicit |
| [lunar-python](https://github.com/6tail/lunar-python) | EightChar sect 1/2 × Yun sect 1/2, as separate options | Version 1.4.8; 寿星 lineage |
| [China95](https://p.china95.net/paipan/bazi/) | Ordinary civil-time calculation, solar correction disabled | Service version and lineage unknown; 交运 displayed to hours |
| [Iwzwh](https://pcbz.iwzwh.com/) | Captured default with a fixed as-of context | Service version and lineage unknown; absolute 起运 timestamp unavailable |

Each observation has a capture date and evidence fingerprint. The web results are
dated observations of those configurations, not version-pinned services. The
acquisition tools, complete forty-input matrix and raw responses are maintained
separately; this repository contains the admitted subset and its offline tests.
This report is repository documentation, not an installed package interface.

## Reading differences

Profile IDs name precision, day rollover and Dayun year-label rule. Four-pillar
matches compare year/month/day/hour together. `dayun_sequence_matching_profiles`
compares the first three actual 大运 Ganzhi, separately from their dates and labels.
A match of these fields is not a claim that the calculators are interchangeable.

| Case | Contrast preserved in the fixture |
| --- | --- |
| C09/C10/C11 | At 2000-02-04 20:40, bazi ties the entire minute to the new year/month. lunar-python still has 己卯/丁丑 at the supplied 20:40:00, before its 20:40:24 boundary |
| C16 | At 2017-02-03 23:10, bazi HOUR assigns the 立春-containing 子时 to the new year; MINUTE still assigns the old year. Iwzwh returns the new-year pillars in this observation |
| C23 | At 2009-02-03 23:30, bazi HOUR reaches the next day's 00:xx 立春 through the spanning 子时; DAY and MINUTE retain the old year |
| C29 | lunar-python sect 2 keeps 庚子 as the civil-day pillar but gives 戊子 for the hour. The recorded bazi profiles give either 辛丑/戊子 or 庚子/丙子 |
| C12/C34 | China95 returns 己卯/丙寅 at 2000-02-04 22:01 for both genders, while every recorded bazi profile returns 庚辰/戊寅. The resulting 大运 sequences differ too |
| C32/C33 | China95 retains 壬寅 across the sampled 2023 春节 dates. Together with C12, this prevents describing the service with a blanket 春节-based year rule |
| C36/C37 | Adjacent birth minutes produce bazi 起运 on opposite sides of 2005 立春. The external starts and year labels retain their own meanings |

Even per-case agreement does not imply a single matching configuration for a whole
source. Across the forty-input collection, each Iwzwh pillar observation matches
some bazi profile, but no one profile matches all forty. Its general boundary rule
remains unidentified here.

The 闰月 controls retain 月柱乙卯 when the lunar label enters 闰二月, then change to
丙辰 after 清明 within that lunar month. Month-stem comparisons condition on each
source's own year stem and month branch. These samples do not establish a universal
absence of alternative conventions.

## 起运, intervals and year labels

The fixture keeps the following fields separate:

- `duration`: a source's years/months/days/hours offset. These components are not
  added to the birthday to invent an unreported timestamp.
- `start`: a provided civil timestamp with display resolution, or an explicit
  missing value. China95's hour display has unknown rounding; extra zeros would
  not add precision. lunar-python's seconds display does not imply second-level
  accuracy of its conversion.
- bazi `dayun`: half-open start/end intervals and separately projected Ganzhi-year
  labels. `FIXED_DECADE` changes labels, not the physical timeline.
- external `year_labels` and `age_labels`: source-specific values. lunar-python
  returns Gregorian inclusive year ranges; Iwzwh labels come from its captured
  renderer. They are not converted to bazi's Ganzhi-year labels.
- `reported_forward`: an explicit library result, or null when the web observation
  lacks one. `sequence_direction` is derived from the ordered Ganzhi sequence.

For example, C03 starts bazi's first 大运 in January 2033 with Ganzhi-year label
2032. lunar-python and Iwzwh's displayed year labels start at 2033. Comparing those
integers as if they named the same kind of year would create a false discrepancy.

The astronomical table is the comparison reference; this collection is not a new
physical calibration. Differences in displayed 节气 times, pillar attribution and
起运 conversion are separate questions. Unknown source behavior remains an
observation to investigate, rather than a new school definition or an automatic
bug verdict. Historical time standards, DST and geographic preprocessing are
tracked separately in #118 and #2.
