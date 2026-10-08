# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_celestial_loader.py

import hashlib
import struct

from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from bazi.calendar.celestial_data.loader import (
  DATA_DIR, JIEQI_BY_INDEX, JIEQI_COLUMNS, LUNAR_COLUMNS, SCHEMA_VERSION,
  EOT_CADENCE_SECONDS, EOT_HEADER, EOT_MAGIC, EOT_SAMPLE_COUNT, EOT_SCALE,
  EOT_SENTINEL_DATE, EOT_START_DATE, EquationOfTimeTable, JieqiMomentTable, LunarYearTable,
)
from bazi.defines import Ganzhi, Jieqi


FIXTURES: Path = Path(__file__).parent / 'celestial_fixtures'
TABLE_NAMES: list[str] = ['jieqi_moments.txt', 'lunar_years_algo1.txt', 'lunar_years_algo2.txt']


def data_lines(path: Path) -> list[str]:
  return [line for line in path.read_text(encoding='utf-8').splitlines() if not line.startswith('#')]


# The shipped tables: the tables that actually ship, loaded with the strict contiguity check.


def test_they_cover_the_whole_window() -> None:
  assert JieqiMomentTable().supported_year_range() == range(1901, 2201)
  for algo in (1, 2):
    table = LunarYearTable(DATA_DIR / f'lunar_years_algo{algo}.txt')
    assert table.supported_year_range() == range(1901, 2100)


def test_data_sections_are_frozen() -> None:
  '''
  The real moments are the reason this backend exists, yet only a handful of the 7,200 are
  pinned by value anywhere else in the suite -- the parity whitelist plus a few directed
  cases.  So the data sections are hashed: a re-bake stays possible, but it has to come
  with a deliberate update to this expectation instead of slipping through.  `#` lines are
  excluded, so re-generating on another day does not trip it.
  '''
  digests: dict[str, str] = {
    'jieqi_moments.txt':     'da0ab657f3c89cbdcc1354cacdf1949f5964cd630256cff288db603b7ba90e50',
    'lunar_years_algo1.txt': '3e238a2e0494b5af8a53f24e2cae150406972e7ecaa3ce673ceba785bbf3b51d',
    'lunar_years_algo2.txt': '787229f4d253280f5fc0fc5b47adeb9292228ca503aab7032307d6dbde83bb53',
  }
  assert sorted(digests) == sorted(TABLE_NAMES) # Every shipped table is covered.
  for name, digest in digests.items():
    payload: str = '\n'.join(data_lines(DATA_DIR / name))
    assert hashlib.sha256(payload.encode('utf-8')).hexdigest() == digest, name


def test_package_provenance_value_is_pinned() -> None:
  '''
  The closed header namespace (test_celestial_tables.py) pins key *names* only, and the data
  digests above exclude `#` lines -- so without this test the recorded package identity could
  drift unnoticed. Re-baking with a new package is legitimate, but it has to update this
  expectation deliberately in the same commit.
  '''
  expected: dict[str, str] = {
    'celestial_version': '0.6.1',
    'release_asset': 'celestial-calendar==0.6.1 / PyPI wheel',
  }
  assert {key: JieqiMomentTable().provenance[key] for key in expected} == expected
  for algo in (1, 2):
    table = LunarYearTable(DATA_DIR / f'lunar_years_algo{algo}.txt')
    assert {key: table.provenance[key] for key in expected} == expected


def test_fixture_rows_appear_verbatim_in_the_shipped_tables() -> None:
  '''
  The fixtures and the shipped tables were written by two generators that never shared
  code (the fixtures came from a throwaway script, the tables from
  `celestial_data/generator.py`).  Byte-identical data lines on
  the overlapping years is therefore a check on `SCHEMA.md` itself, not just on the data.
  '''
  for name in TABLE_NAMES:
    fixture_rows: list[str] = data_lines(FIXTURES / name)
    shipped_rows: set[str] = set(data_lines(DATA_DIR / name))
    assert len(fixture_rows) == (120 if name.startswith('jieqi') else 5), name
    for row in fixture_rows:
      assert row in shipped_rows, f'{name}: fixture row absent from the shipped table'


# The fixture tables: a 5-year slice in the shipped format, frozen when the schema was.  Being a
# sparse slice, they are loaded with `contiguous_years=False`; the shipped tables use the strict
# default.


def test_jieqi_fixture() -> None:
  table = JieqiMomentTable(FIXTURES / 'jieqi_moments.txt', contiguous_years=False)
  assert table.supported_year_range() == range(1901, 2025) # min..max of the slice

  # Spot values, deliberately the ones that carry signal.
  assert table.get(2024, Jieqi.立春) == datetime(2024, 2, 4, 16, 27, 6)
  assert table.get(1917, Jieqi.大雪) == datetime(1917, 12, 8, 0, 1, 5)
  assert table.get(1979, Jieqi.大寒) == datetime(1979, 1, 20, 23, 59, 56)

  # 小寒/大寒 of year Y land in January of Y, so rows are not date-sorted within a year.
  assert table.get(2024, Jieqi.小寒).month == 1
  assert table.get(2024, Jieqi.大寒) < table.get(2024, Jieqi.立春)


def test_jieqi_provenance() -> None:
  table = JieqiMomentTable(FIXTURES / 'jieqi_moments.txt', contiguous_years=False)
  provenance = table.provenance
  assert provenance['schema_version'] == SCHEMA_VERSION
  assert provenance['celestial_version'] == '0.6.1'
  assert provenance['columns'] == JIEQI_COLUMNS
  # A copy, so a caller cannot mutate the table's own record.
  provenance['celestial_version'] = 'tampered'
  assert table.provenance['celestial_version'] == '0.6.1'


def test_lunar_fixture() -> None:
  for algo in (1, 2):
    table = LunarYearTable(FIXTURES / f'lunar_years_algo{algo}.txt', contiguous_years=False)
    assert table.provenance['columns'] == LUNAR_COLUMNS
    assert table.provenance['algo'] == str(algo)

    info = table.get(1901)
    assert info['first_solar_day'] == date(1901, 2, 19)
    assert not info['leap']
    assert info['leap_month'] is None # The table spells this as 0; hko_data as None.
    assert len(info['days_counts']) == 12
    assert info['ganzhi'] == Ganzhi.from_str('辛丑')

    leap = table.get(1917)
    assert leap['leap']
    assert leap['leap_month'] == 2
    assert len(leap['days_counts']) == 13


def test_lunar_get_returns_a_copy() -> None:
  # A copy, so a caller's in-place edit cannot corrupt the table's own record (issue #92).
  table = LunarYearTable(FIXTURES / 'lunar_years_algo1.txt', contiguous_years=False)
  info = table.get(1901)
  assert info is not table.get(1901)
  assert info['days_counts'] is not table.get(1901)['days_counts']

  original = list(info['days_counts'])
  info['days_counts'][0] = 999
  assert table.get(1901)['days_counts'] == original


def test_the_two_algos_differ_on_1914() -> None:
  # 1914 is one of the six years celestial's own diff_test.cpp records as divergent.
  algo1 = LunarYearTable(FIXTURES / 'lunar_years_algo1.txt', contiguous_years=False).get(1914)
  algo2 = LunarYearTable(FIXTURES / 'lunar_years_algo2.txt', contiguous_years=False).get(1914)
  assert algo1['first_solar_day'] == algo2['first_solar_day']
  assert algo1['days_counts'] != algo2['days_counts']


def test_index_matches_the_jieqi_enum() -> None:
  # The table stores celestial's `jq_idx`; the loader trusts it to be this enum's index.
  assert len(JIEQI_BY_INDEX) == 24
  assert JIEQI_BY_INDEX[0] is Jieqi.立春
  assert JIEQI_BY_INDEX[23] is Jieqi.大寒
  # Even indices are 节 (they start ganzhi months), odd ones are 气.
  assert JIEQI_BY_INDEX[::2] == Jieqi.as_list()[::2]


# Corrupt tables: every rejection path, exercised by mutating a fixture.  A stale or hand-edited
# table is the one failure mode that would otherwise silently produce wrong charts everywhere.


@pytest.fixture
def jieqi_lines() -> list[str]:
  return (FIXTURES / 'jieqi_moments.txt').read_text(encoding='utf-8').splitlines()


@pytest.fixture
def lunar_lines() -> list[str]:
  return (FIXTURES / 'lunar_years_algo1.txt').read_text(encoding='utf-8').splitlines()


def _write(tmp_path: Path, lines: list[str], name: str = 'table.txt') -> Path:
  path: Path = tmp_path / name
  path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
  return path


def _replace(lines: list[str], old_prefix: str, new: str) -> list[str]:
  out = list(lines)
  for i, line in enumerate(out):
    if line.startswith(old_prefix):
      out[i] = new
      return out
  raise AssertionError(f'No line starts with {old_prefix!r}') # pragma: no cover # Test-helper guard.


def test_missing_file() -> None:
  with pytest.raises(RuntimeError) as ctx:
    JieqiMomentTable(FIXTURES / 'does_not_exist.txt')
  assert 'generator' in str(ctx.value) # Tell the reader how to regenerate it.


def test_schema_version_mismatch(jieqi_lines: list[str], tmp_path: Path) -> None:
  path = _write(tmp_path, _replace(jieqi_lines, '# schema_version:', '# schema_version: 999'))
  with pytest.raises(ValueError):
    JieqiMomentTable(path)


def test_columns_mismatch(jieqi_lines: list[str], tmp_path: Path) -> None:
  path = _write(tmp_path, _replace(jieqi_lines, '# columns:', '# columns: year name'))
  with pytest.raises(ValueError):
    JieqiMomentTable(path)


def test_row_count_mismatch(jieqi_lines: list[str], tmp_path: Path) -> None:
  path = _write(tmp_path, _replace(jieqi_lines, '# rows:', '# rows: 119'))
  with pytest.raises(ValueError):
    JieqiMomentTable(path)


def test_jieqi_name_does_not_match_index(jieqi_lines: list[str], tmp_path: Path) -> None:
  path = _write(tmp_path, _replace(jieqi_lines, '1901 00 ', '1901 00 大寒 1901-02-04 19:39:57'))
  with pytest.raises(ValueError):
    JieqiMomentTable(path)


def test_jieqi_index_out_of_range(jieqi_lines: list[str], tmp_path: Path) -> None:
  # 24 is past the end; -1 would otherwise alias from the *end* of the list and read as
  # 大寒, letting a corrupt row through as long as its name matched that alias.
  for bad in ('1901 24 立春 1901-02-04 19:39:57', '1901 -1 大寒 1901-02-04 19:39:57'):
    with pytest.raises(ValueError):
      JieqiMomentTable(_write(tmp_path, _replace(jieqi_lines, '1901 00 ', bad)))


def test_duplicate_jieqi_row(jieqi_lines: list[str], tmp_path: Path) -> None:
  lines = _replace(jieqi_lines, '1901 01 ', '1901 00 立春 1901-02-19 15:45:00')
  with pytest.raises(ValueError):
    JieqiMomentTable(_write(tmp_path, lines))


def _synthetic(tmp_path: Path, lines: list[str], sample_prefix: str, years: list[int]) -> Path:
  '''
  Build a table covering exactly `years`, by restamping one sample year's rows.  Only
  the structure matters here, so the other columns keep the sample year's values.
  '''
  sample: list[str] = [line for line in lines if line.startswith(sample_prefix)]
  data: list[str] = [f'{year}{row[len(str(year)):]}' for year in years for row in sample]
  header: list[str] = [line for line in lines if line.startswith('#')]
  return _write(tmp_path, _replace(header, '# rows:', f'# rows: {len(data)}') + data)


def test_jieqi_years_not_fully_covered(jieqi_lines: list[str], tmp_path: Path) -> None:
  # A hole at 1903: the row count header matches, but the year range is not covered.
  with pytest.raises(ValueError):
    JieqiMomentTable(_synthetic(tmp_path, jieqi_lines, '1901 ', [1901, 1902, 1904]))
  # Positive control: the same builder with no hole passes the strict check.
  table = JieqiMomentTable(_synthetic(tmp_path, jieqi_lines, '1901 ', [1901, 1902, 1903]))
  assert table.supported_year_range() == range(1901, 1904)


def test_lunar_bits_disagree_with_days_counts(lunar_lines: list[str], tmp_path: Path) -> None:
  path = _write(tmp_path, _replace(
    lunar_lines, '1901 ',
    '1901 1901-02-19 0 0x0752 30,30,29,29,30,29,30,29,30,30,30,29 辛丑'))
  with pytest.raises(ValueError):
    LunarYearTable(path)


def test_lunar_leap_month_disagrees_with_month_count(lunar_lines: list[str], tmp_path: Path) -> None:
  # 12 months but a non-zero leap month.
  path = _write(tmp_path, _replace(
    lunar_lines, '1901 ',
    '1901 1901-02-19 5 0x0752 29,30,29,29,30,29,30,29,30,30,30,29 辛丑'))
  with pytest.raises(ValueError):
    LunarYearTable(path)


def test_duplicate_lunar_year(lunar_lines: list[str], tmp_path: Path) -> None:
  path = _write(tmp_path, _replace(
    lunar_lines, '1914 ',
    '1901 1901-02-19 0 0x0752 29,30,29,29,30,29,30,29,30,30,30,29 辛丑'))
  with pytest.raises(ValueError):
    LunarYearTable(path)


def test_lunar_years_not_contiguous(lunar_lines: list[str], tmp_path: Path) -> None:
  with pytest.raises(ValueError):
    LunarYearTable(_synthetic(tmp_path, lunar_lines, '1901 ', [1901, 1902, 1904]))
  table = LunarYearTable(_synthetic(tmp_path, lunar_lines, '1901 ', [1901, 1902, 1903]))
  assert table.supported_year_range() == range(1901, 1904)


def test_header_continuation_lines_are_not_keys() -> None:
  # Prose continuation lines are indented further; they must not become header keys.
  table = JieqiMomentTable(FIXTURES / 'jieqi_moments.txt', contiguous_years=False)
  assert 'Measured' not in table.provenance
  assert 'timescale_caveat' in table.provenance


# Binary EOT: immutable daily samples, UTC interpolation and independent source anchors.

EOT_PATH = DATA_DIR / 'equation_of_time.bin'


def _independent_read_eot(path: Path) -> tuple[tuple[object, ...], tuple[int, ...]]:
  encoded = path.read_bytes()
  header = struct.unpack('>8sIIII32s', encoded[:56])
  samples = struct.unpack(f'>{header[2]}h', encoded[56:])
  return header, samples


def _rewrite_eot(tmp_path: Path, samples: tuple[int, ...]) -> Path:
  payload = struct.pack(f'>{len(samples)}h', *samples)
  path = tmp_path / 'equation_of_time.bin'
  path.write_bytes(EOT_HEADER.pack(
    EOT_MAGIC,
    EOT_START_DATE.toordinal(),
    len(samples),
    EOT_CADENCE_SECONDS,
    EOT_SCALE,
    hashlib.sha256(payload).digest(),
  ) + payload)
  return path


def test_binary_schema_and_frozen_bytes() -> None:
  header, samples = _independent_read_eot(EOT_PATH)
  magic, start_ordinal, count, cadence, scale, digest = header
  payload = EOT_PATH.read_bytes()[56:]

  assert EOT_HEADER.size == 56
  assert magic == b'BAZIEOT1'
  assert date.fromordinal(start_ordinal) == date(1901, 2, 17) # type: ignore[arg-type]
  assert count == EOT_SAMPLE_COUNT == 72_643
  assert cadence == 86_400
  assert scale == 10
  assert len(samples) == count
  assert hashlib.sha256(payload).digest() == digest
  assert hashlib.sha256(EOT_PATH.read_bytes()).hexdigest() == \
         'bfabfb3560969ec54679972f8a942f5ff081833df581746d77f317a5dccb4d89'


def test_runtime_reads_every_encoded_sample() -> None:
  _, independently_read = _independent_read_eot(EOT_PATH)
  table = EquationOfTimeTable()
  assert table.samples == independently_read

  start = datetime.combine(EOT_START_DATE, datetime.min.time(), UTC)
  for index, sample in enumerate(independently_read[:-1]):
    assert table.seconds_at(start + timedelta(days=index)) == sample / EOT_SCALE


@pytest.mark.parametrize('moment, expected, tolerance', [
  # Jean Meeus, Astronomical Algorithms, 2nd ed., Example 28.a: 1992-10-13
  # at 0h TD has EOT +13m42.6s, using apparent-minus-mean sign. The allowance
  # includes the rounded source value, decisecond encoding and the UTC/TD instant difference.
  (datetime(1992, 10, 13, tzinfo=UTC), 822.6, 0.2),
  # USNO "Computing Approximate Solar Coordinates" (EqT = q/15 - RA):
  # https://aa.usno.navy.mil/faq/sun_approx
  # independently evaluated at 0h UTC. Its stated solar-coordinate accuracy is about
  # one arcminute, equivalent to four seconds of time; 0.1s covers table quantization.
  (datetime(1901, 2, 18, tzinfo=UTC), -851.5156, 4.1),
  (datetime(2000, 2, 11, tzinfo=UTC), -854.4708, 4.1),
  (datetime(2000, 11, 3, tzinfo=UTC), 985.3753, 4.1),
  (datetime(2099, 12, 31, tzinfo=UTC), -162.1897, 4.1),
])
def test_published_equation_of_time_anchors(moment: datetime, expected: float, tolerance: float) -> None:
  assert EquationOfTimeTable().seconds_at(moment) == pytest.approx(expected, abs=tolerance)


def test_interpolation_uses_utc_day_fraction() -> None:
  table = EquationOfTimeTable()
  start = datetime(2000, 11, 3, tzinfo=UTC)
  lower = table.seconds_at(start)
  upper = table.seconds_at(start + timedelta(days=1))
  for fraction in (0.25, 0.5, 0.75):
    assert table.seconds_at(start + timedelta(days=fraction)) == pytest.approx(
      lower + (upper - lower) * fraction,
      abs=1e-12,
    )


def test_equation_of_time_normalizes_non_utc_offsets() -> None:
  table = EquationOfTimeTable()
  utc = datetime(2000, 1, 1, 12, 34, 56, 123456, tzinfo=UTC)
  for zone in (timezone(timedelta(hours=8)), timezone(timedelta(hours=-5))):
    assert table.seconds_at(utc.astimezone(zone)) == table.seconds_at(utc)


def test_interpolation_range_is_half_open() -> None:
  table = EquationOfTimeTable()
  first = datetime.combine(EOT_START_DATE, datetime.min.time(), UTC)
  sentinel = datetime.combine(EOT_SENTINEL_DATE, datetime.min.time(), UTC)

  assert EOT_SENTINEL_DATE == date(2100, 1, 6)
  assert isinstance(table.seconds_at(first), float)
  assert isinstance(table.seconds_at(datetime(2100, 1, 5, 7, 30, 49, tzinfo=UTC)), float)
  assert isinstance(table.seconds_at(sentinel - timedelta(microseconds=1)), float)
  for moment in (first - timedelta(microseconds=1), sentinel, sentinel + timedelta(microseconds=1)):
    with pytest.raises(ValueError, match='equation-of-time range'):
      table.seconds_at(moment)
  with pytest.raises(ValueError, match='timezone-aware'):
    table.seconds_at(first.replace(tzinfo=None))
  with pytest.raises(TypeError, match='datetime'):
    table.seconds_at(date(2000, 1, 1)) # type: ignore[arg-type]


def test_reader_rejects_schema_and_payload_corruption(tmp_path: Path) -> None:
  with pytest.raises(RuntimeError, match='table is missing'):
    EquationOfTimeTable(tmp_path / 'missing.bin')

  truncated = tmp_path / 'truncated.bin'
  truncated.write_bytes(EOT_MAGIC)
  with pytest.raises(ValueError, match='header is truncated'):
    EquationOfTimeTable(truncated)

  encoded = EOT_PATH.read_bytes()
  mutations: list[bytes] = []
  for index in (0, 8, 12, 16, 20, 24, 55, 56, len(encoded) - 1):
    mutated = bytearray(encoded)
    mutated[index] ^= 1
    mutations.append(bytes(mutated))
  mutations.extend((encoded[:-1], encoded + b'\0'))

  for index, corrupt in enumerate(mutations):
    path = tmp_path / f'corrupt-{index}.bin'
    path.write_bytes(corrupt)
    with pytest.raises(ValueError):
      EquationOfTimeTable(path)


def test_named_sign_and_index_mutants_fail_anchors(tmp_path: Path) -> None:
  _, samples = _independent_read_eot(EOT_PATH)
  meeus = datetime(1992, 10, 13, tzinfo=UTC)

  inverted = EquationOfTimeTable(_rewrite_eot(tmp_path, tuple(-sample for sample in samples)))
  assert inverted.seconds_at(meeus) < 0
  assert inverted.seconds_at(meeus) != pytest.approx(822.6, abs=0.2)

  shifted = EquationOfTimeTable(_rewrite_eot(tmp_path, samples[1:] + samples[:1]))
  assert shifted.seconds_at(meeus) != pytest.approx(822.6, abs=0.2)
