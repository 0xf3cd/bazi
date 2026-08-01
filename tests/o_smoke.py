# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# o_smoke.py

'''
Smoke-checks the public fail-fast contract under `python -O`: every face below must
raise its documented TypeError/ValueError even with asserts stripped (issue #102).
Before #102 these faces degraded under `-O` into silent wrong answers (e.g. a tz-aware
birth time quietly accepted) or deep internal KeyErrors.

Standalone by design -- no `test_` prefix, so pytest does not collect it; the gates
run it via `run_tests.py -osmoke` as `python -O tests/o_smoke.py`. Runnable from any
cwd: the script puts the repo root on sys.path itself (`-m tests.o_smoke` is not an
option -- a stray `tests` package in site-packages shadows the repo's `tests/`, see
the import note in `tests/calendar/test_celestial_tables.py`).
'''

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
  if __debug__:
    print('o_smoke.py must run under `python -O`: it checks the contract that outlives stripped asserts.')
    return 2

  from datetime import date, datetime
  from collections.abc import Callable
  from zoneinfo import ZoneInfo

  from src.defines import Dizhi, Jieqi
  from src.bazi import Bazi
  from src.bazi_chart import BaziChart
  from src.transits import TransitMoment
  from src.utils import tiangan_utils
  from src.calendar import hko_data, hko_data_utils
  from src.calendar.backend import CalendarBackend, calendar_utils_of

  checks: list[tuple[str, type[Exception], Callable[[], object]]] = [
    ('Bazi.create below window (1901-01-01)', ValueError,
     lambda: Bazi.create(datetime(1901, 1, 1, 12), 'male', 'day')),
    ('Bazi.create above window (2100-06-01)', ValueError,
     lambda: Bazi.create(datetime(2100, 6, 1, 12), 'male', 'day')),
    ('Bazi.create tz-aware birth time', ValueError,
     lambda: Bazi.create(datetime(2000, 1, 1, 7, tzinfo=ZoneInfo('Asia/Shanghai')), 'male', 'day')),
    ('tiangan_utils.he on raw strings', TypeError,
     lambda: tiangan_utils.he('甲', '己')), # type: ignore
    ('DecodedLunarYears.get out of range', ValueError,
     lambda: hko_data.DecodedLunarYears().get(1800)),
    ('jieqi_moment out of range', ValueError,
     lambda: hko_data_utils.jieqi_moment(1900, Jieqi.冬至)),
    ('TransitMoment mutually exclusive fields', ValueError,
     lambda: TransitMoment(2024, Dizhi.子, date(2024, 6, 1))),
    ('dayun past supported window (#63.1)', ValueError,
     lambda: next(BaziChart(Bazi.create(datetime(2091, 6, 1, 12), 'male', 'day')).dayun)),
    ('hko get_min_supported_date garbage date_type', ValueError,
     lambda: hko_data_utils.get_min_supported_date(42)),
    ('celestial get_max_supported_date garbage date_type', ValueError,
     lambda: calendar_utils_of(CalendarBackend.CELESTIAL).get_max_supported_date(42)), # type: ignore
    ('calendar_utils_of garbage backend', TypeError,
     lambda: calendar_utils_of(42)), # type: ignore
  ]

  failures: list[str] = []
  for label, expected, thunk in checks:
    try:
      thunk()
      failures.append(f'{label}: no exception, expected {expected.__name__}')
    except expected:
      pass
    except Exception as e: # noqa: BLE001 -- a smoke harness reports whatever actually leaked
      failures.append(f'{label}: {type(e).__name__} ({e}), expected {expected.__name__}')

  for line in failures:
    print(f'FAIL {line}')
  print(f'o_smoke: {len(checks) - len(failures)}/{len(checks)} public faces hold under -O.')
  return 1 if failures else 0


if __name__ == '__main__':
  sys.exit(main())
