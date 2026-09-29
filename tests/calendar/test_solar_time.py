# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import hashlib
import struct

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from bazi.calendar.celestial_data.loader import (
  DATA_DIR, EOT_CADENCE_SECONDS, EOT_HEADER, EOT_MAGIC, EOT_SAMPLE_COUNT,
  EOT_SCALE, EOT_SENTINEL_DATE, EOT_START_DATE, EquationOfTimeTable,
)


EOT_PATH = DATA_DIR / 'equation_of_time.bin'


def _independent_read(path: Path) -> tuple[tuple[object, ...], tuple[int, ...]]:
  encoded = path.read_bytes()
  header = struct.unpack('>8sIIII32s', encoded[:56])
  samples = struct.unpack(f'>{header[2]}h', encoded[56:])
  return header, samples


def _rewrite(tmp_path: Path, samples: tuple[int, ...]) -> Path:
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
  header, samples = _independent_read(EOT_PATH)
  magic, start_ordinal, count, cadence, scale, digest = header
  payload = EOT_PATH.read_bytes()[56:]

  assert EOT_HEADER.size == 56
  assert magic == b'BAZIEOT1'
  assert date.fromordinal(start_ordinal) == date(1901, 2, 18) # type: ignore[arg-type]
  assert count == EOT_SAMPLE_COUNT == 72_638
  assert cadence == 86_400
  assert scale == 10
  assert len(samples) == count
  assert hashlib.sha256(payload).digest() == digest
  assert hashlib.sha256(EOT_PATH.read_bytes()).hexdigest() == \
         '1300533084463522075b56962a8145686d1c34cd898a62551e84960f3c136809'


def test_runtime_reads_every_encoded_sample() -> None:
  _, independently_read = _independent_read(EOT_PATH)
  table = EquationOfTimeTable()
  assert table.samples == independently_read

  start = datetime.combine(EOT_START_DATE, datetime.min.time(), UTC)
  for index, sample in enumerate(independently_read[:-1]):
    assert table.seconds_at(start + timedelta(days=index)) == sample / EOT_SCALE


@pytest.mark.parametrize('moment, expected, tolerance', [
  # Jean Meeus, Astronomical Algorithms, 2nd ed., Example 28.a: 1992-10-13
  # at 0h TD has EOT +13m42.6s, using apparent-minus-mean sign.
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


def test_interpolation_range_is_half_open() -> None:
  table = EquationOfTimeTable()
  first = datetime.combine(EOT_START_DATE, datetime.min.time(), UTC)
  sentinel = datetime.combine(EOT_SENTINEL_DATE, datetime.min.time(), UTC)

  assert isinstance(table.seconds_at(first), float)
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
  _, samples = _independent_read(EOT_PATH)
  meeus = datetime(1992, 10, 13, tzinfo=UTC)

  inverted = EquationOfTimeTable(_rewrite(tmp_path, tuple(-sample for sample in samples)))
  assert inverted.seconds_at(meeus) < 0
  assert inverted.seconds_at(meeus) != pytest.approx(822.6, abs=0.2)

  shifted = EquationOfTimeTable(_rewrite(tmp_path, samples[1:] + samples[:1]))
  assert shifted.seconds_at(meeus) != pytest.approx(822.6, abs=0.2)
