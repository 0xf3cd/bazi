# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_celestial_loader.py

import tempfile
import unittest

from datetime import date, datetime
from pathlib import Path

from src.Calendar.CelestialData.Loader import (
  JIEQI_BY_INDEX, JIEQI_COLUMNS, LUNAR_COLUMNS, SCHEMA_VERSION,
  JieqiMomentTable, LunarYearTable,
)
from src.Defines import Ganzhi, Jieqi


FIXTURES: Path = Path(__file__).parent / 'celestial_fixtures'


class TestFixtureTables(unittest.TestCase):
  '''
  The fixtures are a 5-year slice in the shipped format, frozen at S0.  Being a sparse
  slice, they are loaded with `contiguous_years=False`; the shipped tables use the strict
  default.
  '''

  def test_jieqi_fixture(self) -> None:
    table = JieqiMomentTable(FIXTURES / 'jieqi_moments.txt', contiguous_years=False)
    self.assertEqual(table.supported_year_range(), range(1901, 2025)) # min..max of the slice

    # Spot values, deliberately the ones that carry signal.
    self.assertEqual(table.get(2024, Jieqi.立春), datetime(2024, 2, 4, 16, 27, 6))
    self.assertEqual(table.get(1917, Jieqi.大雪), datetime(1917, 12, 8, 0, 1, 5))
    self.assertEqual(table.get(1979, Jieqi.大寒), datetime(1979, 1, 20, 23, 59, 56))

    # 小寒/大寒 of year Y land in January of Y, so rows are not date-sorted within a year.
    self.assertEqual(table.get(2024, Jieqi.小寒).month, 1)
    self.assertLess(table.get(2024, Jieqi.大寒), table.get(2024, Jieqi.立春))

  def test_jieqi_provenance(self) -> None:
    table = JieqiMomentTable(FIXTURES / 'jieqi_moments.txt', contiguous_years=False)
    provenance = table.provenance
    self.assertEqual(provenance['schema_version'], SCHEMA_VERSION)
    self.assertEqual(provenance['celestial_version'], '0.4.0')
    self.assertEqual(provenance['columns'], JIEQI_COLUMNS)
    self.assertEqual(len(provenance['dylib_sha256']), 64)
    # A copy, so a caller cannot mutate the table's own record.
    provenance['celestial_version'] = 'tampered'
    self.assertEqual(table.provenance['celestial_version'], '0.4.0')

  def test_lunar_fixture(self) -> None:
    for algo in (1, 2):
      table = LunarYearTable(FIXTURES / f'lunar_years_algo{algo}.txt', contiguous_years=False)
      self.assertEqual(table.provenance['columns'], LUNAR_COLUMNS)
      self.assertEqual(table.provenance['algo'], str(algo))

      info = table.get(1901)
      self.assertEqual(info['first_solar_day'], date(1901, 2, 19))
      self.assertFalse(info['leap'])
      self.assertIsNone(info['leap_month']) # The table spells this as 0; HkoData as None.
      self.assertEqual(len(info['days_counts']), 12)
      self.assertEqual(info['ganzhi'], Ganzhi.from_str('辛丑'))

      leap = table.get(1917)
      self.assertTrue(leap['leap'])
      self.assertEqual(leap['leap_month'], 2)
      self.assertEqual(len(leap['days_counts']), 13)

  def test_the_two_algos_differ_on_1914(self) -> None:
    # 1914 is one of the six years celestial's own diff_test.cpp records as divergent.
    algo1 = LunarYearTable(FIXTURES / 'lunar_years_algo1.txt', contiguous_years=False).get(1914)
    algo2 = LunarYearTable(FIXTURES / 'lunar_years_algo2.txt', contiguous_years=False).get(1914)
    self.assertEqual(algo1['first_solar_day'], algo2['first_solar_day'])
    self.assertNotEqual(algo1['days_counts'], algo2['days_counts'])

  def test_index_matches_the_jieqi_enum(self) -> None:
    # The table stores celestial's `jq_idx`; the loader trusts it to be this enum's index.
    self.assertEqual(len(JIEQI_BY_INDEX), 24)
    self.assertIs(JIEQI_BY_INDEX[0], Jieqi.立春)
    self.assertIs(JIEQI_BY_INDEX[23], Jieqi.大寒)
    # Even indices are 节 (they start ganzhi months), odd ones are 气.
    self.assertEqual(JIEQI_BY_INDEX[::2], Jieqi.as_list()[::2])


class TestCorruptTables(unittest.TestCase):
  '''
  Every rejection path, exercised by mutating a fixture.  A stale or hand-edited table is
  the one failure mode that would otherwise silently produce wrong charts everywhere.
  '''

  def setUp(self) -> None:
    self.jieqi_lines: list[str] = (FIXTURES / 'jieqi_moments.txt').read_text(encoding='utf-8').splitlines()
    self.lunar_lines: list[str] = (FIXTURES / 'lunar_years_algo1.txt').read_text(encoding='utf-8').splitlines()

  def __write(self, lines: list[str], name: str = 'table.txt') -> Path:
    path: Path = Path(self.enterContext(tempfile.TemporaryDirectory())) / name
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return path

  def __replace(self, lines: list[str], old_prefix: str, new: str) -> list[str]:
    out = list(lines)
    for i, line in enumerate(out):
      if line.startswith(old_prefix):
        out[i] = new
        return out
    raise AssertionError(f'No line starts with {old_prefix!r}') # pragma: no cover # Test-helper guard.

  def test_missing_file(self) -> None:
    with self.assertRaises(RuntimeError) as ctx:
      JieqiMomentTable(FIXTURES / 'does_not_exist.txt')
    self.assertIn('Generator', str(ctx.exception)) # Tell the reader how to regenerate it.

  def test_schema_version_mismatch(self) -> None:
    path = self.__write(self.__replace(self.jieqi_lines, '# schema_version:', '# schema_version: 999'))
    with self.assertRaises(ValueError):
      JieqiMomentTable(path)

  def test_columns_mismatch(self) -> None:
    path = self.__write(self.__replace(self.jieqi_lines, '# columns:', '# columns: year name'))
    with self.assertRaises(ValueError):
      JieqiMomentTable(path)

  def test_row_count_mismatch(self) -> None:
    path = self.__write(self.__replace(self.jieqi_lines, '# rows:', '# rows: 119'))
    with self.assertRaises(ValueError):
      JieqiMomentTable(path)

  def test_jieqi_name_does_not_match_index(self) -> None:
    path = self.__write(self.__replace(self.jieqi_lines, '1901 00 ', '1901 00 大寒 1901-02-04 19:39:57'))
    with self.assertRaises(ValueError):
      JieqiMomentTable(path)

  def test_duplicate_jieqi_row(self) -> None:
    lines = self.__replace(self.jieqi_lines, '1901 01 ', '1901 00 立春 1901-02-19 15:45:00')
    with self.assertRaises(ValueError):
      JieqiMomentTable(self.__write(lines))

  def __synthetic(self, lines: list[str], sample_prefix: str, years: list[int]) -> Path:
    '''
    Build a table covering exactly `years`, by restamping one sample year's rows.  Only
    the structure matters here, so the other columns keep the sample year's values.
    '''
    sample: list[str] = [line for line in lines if line.startswith(sample_prefix)]
    data: list[str] = [f'{year}{row[len(str(year)):]}' for year in years for row in sample]
    header: list[str] = [line for line in lines if line.startswith('#')]
    return self.__write(self.__replace(header, '# rows:', f'# rows: {len(data)}') + data)

  def test_jieqi_years_not_fully_covered(self) -> None:
    # A hole at 1903: the row count header matches, but the year range is not covered.
    with self.assertRaises(ValueError):
      JieqiMomentTable(self.__synthetic(self.jieqi_lines, '1901 ', [1901, 1902, 1904]))
    # Positive control: the same builder with no hole passes the strict check.
    table = JieqiMomentTable(self.__synthetic(self.jieqi_lines, '1901 ', [1901, 1902, 1903]))
    self.assertEqual(table.supported_year_range(), range(1901, 1904))

  def test_lunar_bits_disagree_with_days_counts(self) -> None:
    path = self.__write(self.__replace(
      self.lunar_lines, '1901 ',
      '1901 1901-02-19 0 0x0752 30,30,29,29,30,29,30,29,30,30,30,29 辛丑'))
    with self.assertRaises(ValueError):
      LunarYearTable(path)

  def test_lunar_leap_month_disagrees_with_month_count(self) -> None:
    # 12 months but a non-zero leap month.
    path = self.__write(self.__replace(
      self.lunar_lines, '1901 ',
      '1901 1901-02-19 5 0x0752 29,30,29,29,30,29,30,29,30,30,30,29 辛丑'))
    with self.assertRaises(ValueError):
      LunarYearTable(path)

  def test_duplicate_lunar_year(self) -> None:
    path = self.__write(self.__replace(
      self.lunar_lines, '1914 ',
      '1901 1901-02-19 0 0x0752 29,30,29,29,30,29,30,29,30,30,30,29 辛丑'))
    with self.assertRaises(ValueError):
      LunarYearTable(path)

  def test_lunar_years_not_contiguous(self) -> None:
    with self.assertRaises(ValueError):
      LunarYearTable(self.__synthetic(self.lunar_lines, '1901 ', [1901, 1902, 1904]))
    table = LunarYearTable(self.__synthetic(self.lunar_lines, '1901 ', [1901, 1902, 1903]))
    self.assertEqual(table.supported_year_range(), range(1901, 1904))

  def test_header_continuation_lines_are_not_keys(self) -> None:
    # Prose continuation lines are indented further; they must not become header keys.
    table = JieqiMomentTable(FIXTURES / 'jieqi_moments.txt', contiguous_years=False)
    self.assertNotIn('Measured', table.provenance)
    self.assertIn('timescale_caveat', table.provenance)
