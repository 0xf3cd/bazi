# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''
读取 `SCHEMA.md` 所述的预生成 celestial-calendar 表。

加载层只解析、校验表并按键查询，不解释八字历法语义；上层 `CelestialCalendarUtils`
负责历法查询，使数据格式或来源变更与历法语义分开。
运行时只用纯 Python 读取已提交表，不导入离线生成器所用的 celestial-calendar 包。
LunarYearInfo 从共同日期层规范重导出，保留既有导入路径。
'''

import hashlib
import re
import struct

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Final

from ...defines import Ganzhi, Jieqi
from ..dates import LunarYearInfo as LunarYearInfo # noqa: PLC0414 # 显式规范重导出，供严格类型检查的包外调用方使用。


SCHEMA_VERSION: Final[str] = '2'

DATA_DIR: Final[Path] = Path(__file__).parent / 'data'

JIEQI_COLUMNS: Final[str] = 'year jq_idx name date time'
LUNAR_COLUMNS: Final[str] = 'lunar_year first_solar_date leap_month month_len_bits days_counts ganzhi'

EOT_MAGIC:           Final[bytes] = b'BAZIEOT1'
EOT_START_DATE:      Final[date] = date(1901, 2, 17)
EOT_SENTINEL_DATE:   Final[date] = date(2100, 1, 6)
EOT_SAMPLE_COUNT:    Final[int] = (EOT_SENTINEL_DATE - EOT_START_DATE).days + 1
EOT_CADENCE_SECONDS: Final[int] = 86_400
EOT_SCALE:           Final[int] = 10
EOT_HEADER:          Final[struct.Struct] = struct.Struct('>8sIIII32s')

# jq_idx 使用此枚举序号；生成时与库的 jieqi_name 交叉校验，JieqiMomentTable 再逐行核对。
JIEQI_BY_INDEX: Final[list[Jieqi]] = Jieqi.as_list(ganzhi_year=True)
assert len(JIEQI_BY_INDEX) == 24
assert JIEQI_BY_INDEX[0] is Jieqi.立春

# 头部键行采用 `# key: value`，井号后恰有一个空格；续行进一步缩进，不会误作键。
_HEADER_KEY: Final[re.Pattern[str]] = re.compile(r'^# (\w+): ?(.*)$')


class _EquationOfTimeRangeError(ValueError):
  '''UTC 瞬间超出均时差插值范围。'''


def _utc_instant(moment: datetime) -> datetime:
  try:
    return moment.astimezone(UTC)
  except OverflowError as error:
    raise _EquationOfTimeRangeError('Unsupported UTC instant: timezone conversion exceeds datetime range.') from error


def _require_table(path: Path) -> None:
  if not path.is_file():
    raise RuntimeError(
      f'Celestial data table is missing: {path}. '
      'Reinstall bazi; in a source checkout, run `python -m bazi.calendar.celestial_data.generator` '
      'with the optional generation tools.'
    )


class EquationOfTimeTable:
  '''
  UTC 每日午夜的均时差样本，以大端有符号十分之一秒存储；值为真太阳时减平太阳时。
  '''

  def __init__(self, path: Path = DATA_DIR / 'equation_of_time.bin') -> None:
    _require_table(path)

    encoded = path.read_bytes()
    if len(encoded) < EOT_HEADER.size:
      raise ValueError(f'{path}: equation-of-time header is truncated')
    magic, start_ordinal, count, cadence, scale, expected_digest = EOT_HEADER.unpack_from(encoded)
    payload = encoded[EOT_HEADER.size:]

    expected = (
      EOT_MAGIC,
      EOT_START_DATE.toordinal(),
      EOT_SAMPLE_COUNT,
      EOT_CADENCE_SECONDS,
      EOT_SCALE,
    )
    if (magic, start_ordinal, count, cadence, scale) != expected:
      raise ValueError(f'{path}: equation-of-time schema metadata mismatch')
    if len(payload) != count * 2:
      raise ValueError(f'{path}: expected {count * 2} payload bytes, got {len(payload)}')
    if hashlib.sha256(payload).digest() != expected_digest:
      raise ValueError(f'{path}: equation-of-time payload checksum mismatch')

    self._samples: Final[tuple[int, ...]] = struct.unpack(f'>{count}h', payload)

  @property
  def samples(self) -> tuple[int, ...]:
    '''返回全部不可变定点样本，单位为十分之一秒。'''
    return self._samples

  def seconds_at(self, utc_moment: datetime) -> float:
    '''按 UTC 日内比例线性插值，返回真太阳时减平太阳时的秒数。'''
    if not isinstance(utc_moment, datetime):
      raise TypeError(f'Expected datetime, got {type(utc_moment)}')
    if utc_moment.tzinfo is None or utc_moment.utcoffset() is None:
      raise ValueError('Expected a timezone-aware datetime.')

    utc = _utc_instant(utc_moment)
    start = datetime.combine(EOT_START_DATE, datetime.min.time(), UTC)
    offset = utc - start
    supported = timedelta(seconds=EOT_CADENCE_SECONDS * (len(self._samples) - 1))
    if offset < timedelta(0) or offset >= supported:
      raise _EquationOfTimeRangeError(
        f'"{utc_moment}" is out of the equation-of-time range '
        f'[{start}, {start + supported})'
      )

    index, remainder = divmod(offset.total_seconds(), EOT_CADENCE_SECONDS)
    lower = self._samples[int(index)] / EOT_SCALE
    upper = self._samples[int(index) + 1] / EOT_SCALE
    fraction = remainder / EOT_CADENCE_SECONDS
    return lower + (upper - lower) * fraction


def _parse(path: Path, expected_columns: str) -> tuple[dict[str, str], list[list[str]]]:
  '''
  拆出来源头部与数据行，检查各表共用的数据契约。
  损坏或过期的数据须显式抛异常，保证 `python -O` 下仍会立即失败。
  '''
  _require_table(path)

  header: dict[str, str] = {}
  rows: list[list[str]] = []
  for line in path.read_text(encoding='utf-8').splitlines():
    if line.startswith('#'):
      matched = _HEADER_KEY.match(line)
      if matched is not None:
        header[matched.group(1)] = matched.group(2).strip()
    else:
      rows.append(line.split())

  if header.get('schema_version') != SCHEMA_VERSION:
    raise ValueError(f'{path}: expected schema_version {SCHEMA_VERSION}, got {header.get("schema_version")!r}')
  if header.get('columns') != expected_columns:
    raise ValueError(f'{path}: expected columns {expected_columns!r}, got {header.get("columns")!r}')
  if header.get('rows') != str(len(rows)):
    raise ValueError(f'{path}: header claims {header.get("rows")!r} rows, parsed {len(rows)}')

  return header, rows


class JieqiMomentTable:
  '''
  各支持年份的二十四节气时刻，采用 UTC+08:00，精度到秒。
  年键 Y 指时刻日期落在公历年 Y，因此小寒、大寒在 Y 年一月；年内行不按日期排序。
  '''

  def __init__(self, path: Path = DATA_DIR / 'jieqi_moments.txt', contiguous_years: bool = True) -> None:
    '''
    Args:
    - contiguous_years: (bool) 是否要求 `[min, max]` 内每年均有全部二十四时刻。
      随库表为 True，避免支持范围内缺行而抛 KeyError；稀疏测试切片用 False。
      此项是构造参数，不是文件头部键，编辑数据文件不能放宽检查。
    '''
    self._provenance, rows = _parse(path, JIEQI_COLUMNS)
    self._moments: dict[tuple[int, Jieqi], datetime] = {}

    for year_str, idx_str, name, date_str, time_str in rows:
      # 先查范围再取下标，保证错误为 ValueError；直接取下标会抛 IndexError，负数还会从末尾取值。
      idx: int = int(idx_str)
      if not 0 <= idx < len(JIEQI_BY_INDEX):
        raise ValueError(f'{path}: jq_idx {idx_str} is outside 0..{len(JIEQI_BY_INDEX) - 1}')
      jieqi: Jieqi = JIEQI_BY_INDEX[idx]
      if name != jieqi.value:
        raise ValueError(f'{path}: jq_idx {idx_str} is {jieqi.value}, but the row says {name!r}')
      key = (int(year_str), jieqi)
      if key in self._moments:
        raise ValueError(f'{path}: duplicate row for {key[0]} {name}')
      self._moments[key] = datetime.fromisoformat(f'{date_str} {time_str}')

    years = {year for year, _ in self._moments}
    self._year_range: Final[range] = range(min(years), max(years) + 1)
    if contiguous_years and len(self._moments) != len(self._year_range) * 24:
      raise ValueError(f'{path}: {len(self._moments)} moments do not cover {self._year_range} x 24')

  @property
  def provenance(self) -> dict[str, str]:
    return dict(self._provenance)

  def supported_year_range(self) -> range:
    '''支持的公历年份范围。'''
    return self._year_range

  def get(self, solar_year: int, jieqi: Jieqi) -> datetime:
    return self._moments[(solar_year, jieqi)]


class LunarYearTable:
  '''各支持农历年的首日公历日期、闰月及月长。'''

  def __init__(self, path: Path, contiguous_years: bool = True) -> None:
    '''
    Args:
    - contiguous_years: (bool) 连续年份检查，见 `JieqiMomentTable.__init__`。
    '''
    self._provenance, rows = _parse(path, LUNAR_COLUMNS)
    self._years: dict[int, LunarYearInfo] = {}

    for year_str, first_str, leap_str, bits_str, counts_str, ganzhi_str in rows:
      leap_month: int = int(leap_str)
      days_counts: list[int] = [int(c) for c in counts_str.split(',')]
      bits: int = int(bits_str, 16)
      decoded: list[int] = [30 if (bits >> i) & 1 else 29 for i in range(len(days_counts))]
      if decoded != days_counts:
        raise ValueError(f'{path}: year {year_str} has month_len_bits {bits_str} '
                         f'(= {decoded}) but days_counts {days_counts}')
      if len(days_counts) != (13 if leap_month else 12):
        raise ValueError(f'{path}: year {year_str} has leap_month {leap_month} '
                         f'but {len(days_counts)} months')

      year: int = int(year_str)
      if year in self._years:
        raise ValueError(f'{path}: duplicate row for year {year}')
      self._years[year] = LunarYearInfo(
        first_solar_day=date.fromisoformat(first_str),
        leap=leap_month != 0,
        # 无闰月在表中为 0，在 HKO 记录中为 None；转为 None，供两后端直接比较字典。
        leap_month=leap_month if leap_month else None,
        days_counts=days_counts,
        ganzhi=Ganzhi.from_str(ganzhi_str),
      )

    self._year_range: Final[range] = range(min(self._years), max(self._years) + 1)
    if contiguous_years and len(self._years) != len(self._year_range):
      raise ValueError(f'{path}: {len(self._years)} years do not cover {self._year_range}')

  @property
  def provenance(self) -> dict[str, str]:
    return dict(self._provenance)

  def supported_year_range(self) -> range:
    '''支持的农历年份范围。'''
    return self._year_range

  def get(self, lunar_year: int) -> LunarYearInfo:
    info: LunarYearInfo = self._years[lunar_year]
    # 每次返回新记录及独立 days_counts 列表，避免调用方修改内部表；其他值不可变，可共享。
    return LunarYearInfo(
      first_solar_day=info['first_solar_day'],
      leap=info['leap'],
      leap_month=info['leap_month'],
      days_counts=list(info['days_counts']),
      ganzhi=info['ganzhi'],
    )
