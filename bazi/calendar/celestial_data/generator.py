# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# bazi/calendar/celestial_data/generator.py
#
# 按 SCHEMA.md 的冻结契约，用 celestial-calendar Python 包重建 celestial_data/data/ 中的表。
#
# 本模块仅供离线重建；运行时 loader.py 只用纯 Python 读取已提交表，不得导入 celestial_calendar。
# 与 HKO 的离线 encoder.py 和运行时 decoder.py 采用相同分工。
#
# 只从源码检出运行，不从安装包运行：
#   python -m bazi.calendar.celestial_data.generator

import argparse
import hashlib
import struct

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Final

import celestial_calendar as celestial

from ...defines import Ganzhi, Jieqi


# ---------------------------------------------------------------------------
# 固定包版本

CELESTIAL_VERSION: Final[str] = '0.6.1'
RELEASE_ASSET: Final[str] = 'celestial-calendar==0.6.1 / PyPI wheel'

# 表窗口见 SCHEMA.md；节气行按公历年索引，农历行按农历年索引。
JIEQI_START_YEAR: Final[int] = 1901
JIEQI_END_YEAR:   Final[int] = 2200
LUNAR_START_YEAR: Final[int] = 1901
LUNAR_END_YEAR:   Final[int] = 2099 # 两算法均限制在此窗口；algo2 原生支持 [410, 2500]。

EXPECTED_JIEQI_ROWS: Final[int] = (JIEQI_END_YEAR - JIEQI_START_YEAR + 1) * 24
EXPECTED_LUNAR_ROWS: Final[int] = LUNAR_END_YEAR - LUNAR_START_YEAR + 1

EOT_MAGIC:           Final[bytes] = b'BAZIEOT1'
EOT_START_DATE:      Final[date] = date(1901, 2, 17)
EOT_SENTINEL_DATE:   Final[date] = date(2100, 1, 6)
EOT_CADENCE_SECONDS: Final[int] = 86_400
EOT_SCALE:           Final[int] = 10
EOT_HEADER:          Final[struct.Struct] = struct.Struct('>8sIIII32s')


# ---------------------------------------------------------------------------
# 固定版本检查：ΔT 或 celestial 更新可改变全部生成时刻。
if celestial.__version__ != CELESTIAL_VERSION:
  raise RuntimeError(
    f'Version gate failed: imported celestial-calendar {celestial.__version__}, '
    f'expected {CELESTIAL_VERSION}.'
  )


# ---------------------------------------------------------------------------
# 表记录

@dataclass(frozen=True)
class JieqiRow:
  year:   int
  jq_idx: int      # 与 list(Jieqi) 序号相同，0 为立春、23 为大寒。
  name:   str      # 与 jq_idx 冗余，加载器会交叉校验。
  moment: datetime # UTC+08:00，截断到整秒。

@dataclass(frozen=True)
class LunarRow:
  lunar_year:      int
  first_solar_date: date
  leap_month:      int             # 1..12，无闰月为 0。
  month_len_bits:  int             # 公共 month_lengths 按低位优先编码。
  days_counts:     tuple[int, ...] # 从 month_len_bits 解码，保留冗余校验。
  ganzhi:          Ganzhi


def _ut1_moment_to_utc8(moment: celestial.CivilDateTime) -> datetime:
  '''
  UT1 转 UTC+08:00：对完整时刻加八小时，重新计算日期，不能只改日内时刻。
  随后截断到整秒，避免把 23:59:59.6 四舍五入到次日而改变日期归属；截断不改变日期。
  '''
  utc8: datetime = (
    datetime(moment.year, moment.month, moment.day)
    + timedelta(days=moment.fraction)
    + timedelta(hours=8)
  )
  return utc8.replace(microsecond=0)


def _gen_jieqi_rows() -> list[JieqiRow]:
  jieqi_list: Final[list[Jieqi]] = list(Jieqi)
  assert len(jieqi_list) == 24

  # 生成前交叉校验：celestial 节气序须与 list(Jieqi) 完全一致。
  for idx, jq in enumerate(jieqi_list):
    name: str = celestial.jieqi_name(celestial.Jieqi(idx))
    if name != jq.value:
      raise RuntimeError(f'Cross-check gate failed: jieqi_name({idx}) is {name}, expected {jq.value}.')

  rows: list[JieqiRow] = []
  for year in range(JIEQI_START_YEAR, JIEQI_END_YEAR + 1):
    for idx, jq in enumerate(jieqi_list):
      source_jieqi: celestial.Jieqi = celestial.Jieqi(idx)
      query: celestial.JieqiMoment = celestial.jieqi_moment(year, source_jieqi)
      if query.jieqi is not source_jieqi or query.moment_ut1.year != year:
        raise RuntimeError(
          f'Query echo mismatch: asked for ({year}, {idx}), '
          f'got ({query.moment_ut1.year}, {query.jieqi.value}).'
        )
      rows.append(JieqiRow(
        year=year,
        jq_idx=idx,
        name=jq.value,
        moment=_ut1_moment_to_utc8(query.moment_ut1),
      ))

  # 生成记录后核对行数。
  if len(rows) != EXPECTED_JIEQI_ROWS:
    raise RuntimeError(f'Row-count gate failed: {len(rows)} jieqi rows, expected {EXPECTED_JIEQI_ROWS}.')
  return rows


def _decode_month_len_bits(month_len_bits: int, month_count: int) -> tuple[int, ...]:
  '''低位优先：位 i 为序列第 i+1 个农历月，1 为三十日，0 为二十九日。'''
  return tuple(30 if (month_len_bits >> i) & 1 else 29 for i in range(month_count))

def _encode_days_counts(days_counts: tuple[int, ...]) -> int:
  bits: int = 0
  for i, count in enumerate(days_counts):
    if count == 30:
      bits |= 1 << i
    elif count != 29:
      raise RuntimeError(f'A lunar month has 29 or 30 days, got {count}.')
  return bits


def _gen_lunar_rows(algo: int) -> list[LunarRow]:
  assert algo in (1, 2)

  algorithm: celestial.LunarAlgorithm = (
    celestial.LunarAlgorithm.ALGO1 if algo == 1 else celestial.LunarAlgorithm.ALGO2
  )
  year_range: celestial.LunarYearRange = celestial.supported_lunar_year_range(algorithm)
  if year_range.start > LUNAR_START_YEAR or year_range.end < LUNAR_END_YEAR:
    raise RuntimeError(
      f'algo{algo} natively covers [{year_range.start}, {year_range.end}], '
      f'which does not contain the required window [{LUNAR_START_YEAR}, {LUNAR_END_YEAR}].'
    )

  sexagenary_cycle: Final[list[Ganzhi]] = Ganzhi.list_sexagenary_cycle()

  rows: list[LunarRow] = []
  for lunar_year in range(LUNAR_START_YEAR, LUNAR_END_YEAR + 1): # 限制为公共窗口，见 LUNAR_END_YEAR。
    info: celestial.LunarYearInfo = celestial.lunar_year_info(algorithm, lunar_year)
    leap_month: int = 0 if info.leap_month is None else info.leap_month
    days_counts: tuple[int, ...] = info.month_lengths
    month_count: int = 12 if leap_month == 0 else 13
    month_len_bits: int = _encode_days_counts(days_counts)

    # 位图须可往返解码，且不能有多余高位。
    if len(days_counts) != month_count or _decode_month_len_bits(month_len_bits, month_count) != days_counts:
      raise RuntimeError(
        f'Cross-check gate failed: algo{algo} {lunar_year} bitmask 0x{month_len_bits:04x} '
        f'does not round-trip through {days_counts}.'
      )

    rows.append(LunarRow(
      lunar_year=lunar_year,
      first_solar_date=date(info.first_day.year, info.first_day.month, info.first_day.day),
      leap_month=leap_month,
      month_len_bits=month_len_bits,
      days_counts=days_counts,
      ganzhi=sexagenary_cycle[(lunar_year - 4) % 60],
    ))

  # 生成记录后核对行数。
  if len(rows) != EXPECTED_LUNAR_ROWS:
    raise RuntimeError(f'Row-count gate failed: {len(rows)} lunar rows for algo{algo}, expected {EXPECTED_LUNAR_ROWS}.')
  return rows


def _equation_of_time_seconds(utc_day: date) -> float:
  '''返回 UTC 午夜、零经度处真太阳时减平太阳时的秒数。'''
  apparent: celestial.CivilDateTime = celestial.apparent_solar_time(
    celestial.CivilDateTime(utc_day.year, utc_day.month, utc_day.day, 0.0),
    0.0,
  )
  day_offset: int = (date(apparent.year, apparent.month, apparent.day) - utc_day).days
  return (day_offset + apparent.fraction) * EOT_CADENCE_SECONDS


def _gen_eot_samples() -> tuple[int, ...]:
  samples: list[int] = []
  day: date = EOT_START_DATE
  while day <= EOT_SENTINEL_DATE:
    encoded: int = round(_equation_of_time_seconds(day) * EOT_SCALE)
    if not -(2 ** 15) <= encoded < 2 ** 15:
      raise RuntimeError(f'Equation of time on {day} does not fit signed int16: {encoded}')
    samples.append(encoded)
    day += timedelta(days=1)
  expected: int = (EOT_SENTINEL_DATE - EOT_START_DATE).days + 1
  if len(samples) != expected:
    raise RuntimeError(f'Row-count gate failed: {len(samples)} EOT samples, expected {expected}.')
  return tuple(samples)


def _render_eot_table(samples: tuple[int, ...]) -> bytes:
  payload: bytes = struct.pack(f'>{len(samples)}h', *samples)
  return EOT_HEADER.pack(
    EOT_MAGIC,
    EOT_START_DATE.toordinal(),
    len(samples),
    EOT_CADENCE_SECONDS,
    EOT_SCALE,
    hashlib.sha256(payload).digest(),
  ) + payload


# ---------------------------------------------------------------------------
# 渲染，头部键为 SCHEMA.md 要求的机器可读来源信息。

def _common_header(generated_on: date, source_api: str) -> list[str]:
  return [
    '# schema_version: 2',
    f'# celestial_version: {CELESTIAL_VERSION}',
    f'# release_asset: {RELEASE_ASSET}',
    '# generated_by: bazi/calendar/celestial_data/generator.py',
    f'# generated_on: {generated_on.isoformat()}',
    f'# source_api: {source_api}',
  ]


def _render_jieqi_table(rows: list[JieqiRow], generated_on: date) -> str:
  header: list[str] = [
    '# celestial-calendar jieqi moment table',
    *_common_header(generated_on, 'celestial_calendar.jieqi_moment(year, jieqi)'),
    '# timescale: UTC+08:00, derived from celestial UT1 moments by adding exactly 8h',
    '# timescale_caveat: UT1-UTC <= 0.9s (1972+); pre-1972 UT1 is a proxy (celestial Phase C).',
    '#   Normally only affects births within +/-0.9s of a jieqi moment -- but when the moment',
    '#   itself sits near midnight, 0.9s flips the whole *date* attribution.',
    '#   Measured worst case in window: 1979 大寒 is 4s from midnight.',
    '# rounding: truncate to whole seconds (sub-second discarded; never carries into the next date)',
    f'# year_range: {JIEQI_START_YEAR}..{JIEQI_END_YEAR} inclusive',
    '#   TT moments still come from solar-longitude roots; their conversion to UT1 in',
    '#   2101..2200 uses the Stephenson-Morrison-Hohenkerk integrated-lod Delta T extrapolation:',
    '#   it is continuous, but has no precision guarantee or independent HKO comparison.',
    '# columns: year jq_idx name date time',
    '#   jq_idx is 0..23, identical to the bazi `list(Jieqi)` index (0=立春 .. 23=大寒), and',
    '#   `name` is cross-checked against celestial_calendar.jieqi_name at generation.',
    '#   Rows ascend by (year, jq_idx), which is not date order: 小寒/大寒 (idx 22/23) of',
    '#   year Y fall in January of Y.',
    f'# rows: {len(rows)}',
  ]
  lines: list[str] = [
    f'{row.year} {row.jq_idx:02d} {row.name} {row.moment:%Y-%m-%d} {row.moment:%H:%M:%S}'
    for row in rows
  ]
  return '\n'.join(header + lines) + '\n'


def _render_lunar_table(rows: list[LunarRow], algo: int, generated_on: date) -> str:
  # 机器可读键行只放值，叙述放在井号加两个空格的续行，避免加载器将说明解析为值。
  # 各列说明挂在 columns 续行；若另写 `# leap_month: 1..12, or 0 when ...`，
  # 加载器会把整句作为来源键值，见 SCHEMA.md。
  algo_note: Final[dict[int, str]] = {
    1: 'HKO official almanac lineage -- the default.',
    2: 'Leap-second aware UTC+8 via jde_to_utc8, celestial #84.',
  }
  timescale_note: Final[dict[int, str]] = {
    1: 'HKO official civil dates (no astronomical timescale involved)',
    2: 'leap-second aware UTC+08:00',
  }
  header: list[str] = [
    f'# celestial-calendar lunar year table (algo{algo})',
    *_common_header(generated_on, 'celestial_calendar.lunar_year_info(algorithm, lunar_year)'),
    f'# algo: {algo}',
    f'#   {algo_note[algo]}',
    f'# timescale: {timescale_note[algo]}',
    f'# year_range: {LUNAR_START_YEAR}..{LUNAR_END_YEAR} inclusive -- BOTH algos clamped to this window.',
    '#   algo2 natively reports [410, 2500].  Clamping keeps one',
    '#   range contract for both algos.  Widening is a follow-up issue.',
    '# columns: lunar_year first_solar_date leap_month month_len_bits days_counts ganzhi',
    '#   leap_month -- 1..12, or 0 when the year has no leap month.  hko_data spells the same',
    '#   thing as `None`; the loader normalizes.',
    '#   month_len_bits -- encoded from the public `month_lengths` tuple, LSB-first',
    '#   (bit i = the (i+1)-th lunar month in sequence; a leap month occupies its own',
    '#   slot; 1 = 30 days, 0 = 29 days).',
    '#   days_counts -- decoded from month_len_bits, 12 or 13 entries; redundant on purpose,',
    '#   so a hand-edit of either column is caught by the loader cross-check.',
    '#   ganzhi -- (lunar_year - 4) mod 60 over Ganzhi.list_sexagenary_cycle(); not consumed',
    '#   at runtime.  The 199/199 agreement with hko_data is checked by the test suite, not',
    '#   here: see tests/calendar/test_celestial_tables.py.',
    f'# rows: {len(rows)}',
  ]
  lines: list[str] = [
    f'{row.lunar_year} {row.first_solar_date} {row.leap_month} 0x{row.month_len_bits:04x} '
    f'{",".join(map(str, row.days_counts))} {row.ganzhi}'
    for row in rows
  ]
  return '\n'.join(header + lines) + '\n'


def _write_table(path: Path, text: str, expected_rows: int) -> None:
  path.write_text(text, encoding='utf-8', newline='\n') # LF 换行，末尾换行，无空行。

  # 写出后再核对行数，rows 头部须与实际数据行相等。
  written_rows: int = sum(1 for line in path.read_text(encoding='utf-8').splitlines() if not line.startswith('#'))
  if written_rows != expected_rows:
    raise RuntimeError(f'Row-count gate failed: {path} holds {written_rows} data rows, header says {expected_rows}.')
  print(f'> Wrote {path} ({expected_rows} rows)')


def _write_eot_table(path: Path, encoded: bytes, expected_samples: int) -> None:
  path.write_bytes(encoded)
  expected_bytes = EOT_HEADER.size + expected_samples * 2
  if path.stat().st_size != expected_bytes:
    raise RuntimeError(
      f'Byte-count gate failed: {path} holds {path.stat().st_size} bytes, expected {expected_bytes}.'
    )
  print(f'> Wrote {path} ({expected_samples} samples)')


# ---------------------------------------------------------------------------

def main() -> None:
  parser = argparse.ArgumentParser(description='生成随库 celestial-calendar 历法表')
  parser.add_argument('--eot-only', action='store_true', help='只生成 equation_of_time.bin')
  parser.add_argument('--output-dir', type=Path, help='将表写入此目录')
  args = parser.parse_args()

  data_dir: Path = args.output_dir or Path(__file__).parent / 'data'
  data_dir.mkdir(parents=True, exist_ok=True)

  eot_samples: tuple[int, ...] = _gen_eot_samples()
  _write_eot_table(
    data_dir / 'equation_of_time.bin',
    _render_eot_table(eot_samples),
    len(eot_samples),
  )
  if args.eot_only:
    return

  jieqi_rows: list[JieqiRow] = _gen_jieqi_rows()
  algo1_rows: list[LunarRow] = _gen_lunar_rows(algo=1)
  algo2_rows: list[LunarRow] = _gen_lunar_rows(algo=2)

  generated_on: date = date.today()
  _write_table(
    data_dir / 'jieqi_moments.txt',
    _render_jieqi_table(jieqi_rows, generated_on),
    EXPECTED_JIEQI_ROWS,
  )
  _write_table(
    data_dir / 'lunar_years_algo1.txt',
    _render_lunar_table(algo1_rows, 1, generated_on),
    EXPECTED_LUNAR_ROWS,
  )
  _write_table(
    data_dir / 'lunar_years_algo2.txt',
    _render_lunar_table(algo2_rows, 2, generated_on),
    EXPECTED_LUNAR_ROWS,
  )


if __name__ == '__main__':
  main()
