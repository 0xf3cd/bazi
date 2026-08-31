# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# o_smoke.py

'''
Smoke-checks the public fail-fast contract under `python -O`: every face below must
raise its documented TypeError/ValueError even with asserts stripped (issue #102).
Without these gates, `-O` turns each face into a silent wrong answer (e.g. a tz-aware
birth time quietly accepted) or a deep internal KeyError.

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

  # Imports live here: at module level they would sit below the sys.path bootstrap and trip E402.
  from datetime import datetime
  from collections.abc import Callable
  from zoneinfo import ZoneInfo

  from src.defines import Tiangan, Dizhi, Ganzhi, Jieqi, DizhiRelation
  from src.bazi import Bazi
  from src.bazi_chart import BaziChart
  from src.rules import DizhiRules
  from src.school import BaziConfig, BaziSchool
  from src.transit_chart import TransitChart
  from src.transits import TransitDatabase, TransitKind, TransitSet
  from src.analyzer.relationship import RelationshipAnalyzer
  from src.utils import tiangan_utils, dizhi_utils, shensha_utils
  from src.calendar import hko_data, hko_data_utils
  from src.calendar.backend import CalendarBackend, calendar_utils_of

  chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
  transit_chart = TransitChart(chart)
  transit_db = TransitDatabase(chart)
  year_transits = transit_chart.at_year(2024)
  if year_transits is None:
    raise RuntimeError('Expected year 2024 to be supported')
  liunian = year_transits.select(TransitKind.LIUNIAN)
  transit_analysis = RelationshipAnalyzer(chart).transits

  checks: list[tuple[str, type[Exception], Callable[[], object]]] = [
    ('Bazi.create below window (1901-01-01)', ValueError,
     lambda: Bazi.create(datetime(1901, 1, 1, 12), 'male')),
    ('Bazi.create above window (2100-06-01)', ValueError,
     lambda: Bazi.create(datetime(2100, 6, 1, 12), 'male')),
    ('Bazi.create tz-aware birth time', ValueError,
     lambda: Bazi.create(datetime(2000, 1, 1, 7, tzinfo=ZoneInfo('Asia/Shanghai')), 'male')),
    ('tiangan_utils.he on raw strings', TypeError,
     lambda: tiangan_utils.he('甲', '己')), # type: ignore
    ('GanzhiOccurrence negative index', ValueError,
     lambda: dizhi_utils.GanzhiOccurrence(-1, Ganzhi.from_str('甲子'))),
    ('dizhi_utils.search_ganzhis on raw Dizhis', TypeError,
     lambda: dizhi_utils.search_ganzhis([Dizhi.子, Dizhi.丑], DizhiRelation.六合)), # type: ignore
    ('dizhi_utils.discover_ganzhis on raw Dizhis', TypeError,
     lambda: dizhi_utils.discover_ganzhis([Dizhi.子, Dizhi.丑])), # type: ignore
    ('dizhi_utils.gonghe on raw strings', TypeError,
     lambda: dizhi_utils.gonghe('申', '辰')), # type: ignore
    ('dizhi_utils.search Gong without Ganzhi context', ValueError,
     lambda: dizhi_utils.search([Dizhi.申, Dizhi.辰], DizhiRelation.拱合)),
    ('dizhi_utils.search_ganzhis wrong Gong profile', TypeError,
     lambda: dizhi_utils.search_ganzhis(
       [Ganzhi.from_str('庚申'), Ganzhi.from_str('庚辰')],
       DizhiRelation.拱合,
       gong_def=DizhiRules.GongheDef.NARROW, # type: ignore
     )),
    ('dizhi_utils.discover_mutual_ganzhis on raw Dizhis', TypeError,
     lambda: dizhi_utils.discover_mutual_ganzhis([Dizhi.申], [Dizhi.辰])), # type: ignore
    ('shensha_utils.taohua on raw string', TypeError,
     lambda: shensha_utils.taohua('申', Dizhi.酉)), # type: ignore
    ('shensha_utils.hongyan on raw string', TypeError,
     lambda: shensha_utils.hongyan(Tiangan.癸, '申')), # type: ignore
    ('shensha_utils.hongluan on raw string', TypeError,
     lambda: shensha_utils.hongluan('申', Dizhi.未)), # type: ignore
    ('shensha_utils.tianxi on raw string', TypeError,
     lambda: shensha_utils.tianxi(Dizhi.寅, '未')), # type: ignore
    ('shensha_utils.yima on raw string', TypeError,
     lambda: shensha_utils.yima('申', Dizhi.寅)), # type: ignore
    ('shensha_utils.huagai on raw strings', TypeError,
     lambda: shensha_utils.huagai('申', '辰')), # type: ignore
    ('shensha_utils.jiangxing on raw string', TypeError,
     lambda: shensha_utils.jiangxing('申', Dizhi.子)), # type: ignore
    ('shensha_utils.jiesha on raw string', TypeError,
     lambda: shensha_utils.jiesha('申', Dizhi.巳)), # type: ignore
    ('shensha_utils.wangshen on raw string', TypeError,
     lambda: shensha_utils.wangshen('申', Dizhi.亥)), # type: ignore
    ('shensha_utils.guchen on raw string', TypeError,
     lambda: shensha_utils.guchen('子', Dizhi.寅)), # type: ignore
    ('shensha_utils.guasu on raw string', TypeError,
     lambda: shensha_utils.guasu(Dizhi.子, '戌')), # type: ignore
    ('shensha_utils.lushen on raw string', TypeError,
     lambda: shensha_utils.lushen('甲', Dizhi.寅)), # type: ignore
    ('shensha_utils.jinyu on raw string', TypeError,
     lambda: shensha_utils.jinyu(Tiangan.甲, '辰')), # type: ignore
    ('shensha_utils.yangren wrong definition', TypeError,
     lambda: shensha_utils.yangren(Tiangan.甲, Dizhi.卯, definition=object())), # type: ignore
    ('shensha_utils.tianyi wrong definition', TypeError,
     lambda: shensha_utils.tianyi(Tiangan.甲, Dizhi.丑, definition=object())), # type: ignore
    ('BaziSchool wrong Shensha anchor profile', TypeError,
     lambda: BaziSchool(shensha_anchor_profile=object())), # type: ignore
    ('BaziSchool wrong Jinyu anchor', TypeError,
     lambda: BaziSchool(jinyu_anchor=object())), # type: ignore
    ('DecodedLunarYears.get out of range', ValueError,
     lambda: hko_data.DecodedLunarYears().get(1800)),
    ('jieqi_moment out of range', ValueError,
     lambda: hko_data_utils.jieqi_moment(1900, Jieqi.冬至)),
    ('TransitChart.at_year wrong year type', TypeError,
     lambda: transit_chart.at_year('2024')), # type: ignore
    ('TransitChart.at_month wrong year type', TypeError,
     lambda: transit_chart.at_month('2024', Dizhi.寅)), # type: ignore
    ('TransitChart.at_month wrong month type', TypeError,
     lambda: transit_chart.at_month(2024, 1)), # type: ignore
    ('TransitChart.at_date rejects datetime', TypeError,
     lambda: transit_chart.at_date(datetime(2024, 6, 1))),
    ('TransitChart.at_moment wrong type', TypeError,
     lambda: transit_chart.at_moment(object())), # type: ignore
    ('TransitChart.at_moment rejects timezone', ValueError,
     lambda: transit_chart.at_moment(datetime(2024, 6, 1, tzinfo=ZoneInfo('Asia/Shanghai')))),
    ('TransitSet empty', ValueError,
     lambda: TransitSet()),
    ('TransitSet wrong Ganzhi type', TypeError,
     lambda: TransitSet(liunian='甲辰')), # type: ignore
    ('TransitSet.select empty', ValueError,
     lambda: liunian.select()),
    ('TransitSet.select wrong kind type', TypeError,
     lambda: liunian.select('liunian')), # type: ignore
    ('TransitSet.select duplicate kind', ValueError,
     lambda: liunian.select(TransitKind.LIUNIAN, TransitKind.LIUNIAN)),
    ('TransitSet.select absent kind', ValueError,
     lambda: liunian.select(TransitKind.LIUNIAN, TransitKind.DAYUN)),
    ('TransitDatabase.xiaoyun wrong year type', TypeError,
     lambda: transit_db.xiaoyun('2024')), # type: ignore
    ('TransitDatabase.dayun wrong year type', TypeError,
     lambda: transit_db.dayun('2024')), # type: ignore
    ('TransitAnalysis.shensha wrong transits type', TypeError,
     lambda: transit_analysis.shensha(object())), # type: ignore
    ('TransitAnalysis.day_master_relations wrong transits type', TypeError,
     lambda: transit_analysis.day_master_relations(object())), # type: ignore
    ('TransitAnalysis.house_relations wrong transits type', TypeError,
     lambda: transit_analysis.house_relations(object())), # type: ignore
    ('TransitAnalysis.star_relations wrong transits type', TypeError,
     lambda: transit_analysis.star_relations(object())), # type: ignore
    ('TransitAnalysis.zhengyin wrong transits type', TypeError,
     lambda: transit_analysis.zhengyin(object())), # type: ignore
    ('TransitAnalysis.star wrong transits type', TypeError,
     lambda: transit_analysis.star(object())), # type: ignore
    ('hko get_min_supported_date garbage date_type', ValueError,
     lambda: hko_data_utils.get_min_supported_date(42)),
    ('celestial get_max_supported_date garbage date_type', ValueError,
     lambda: calendar_utils_of(CalendarBackend.CELESTIAL).get_max_supported_date(42)), # type: ignore
    ('calendar_utils_of garbage backend', TypeError,
     lambda: calendar_utils_of(42)), # type: ignore
    ('BaziConfig wrong Dayun year rule type', TypeError,
     lambda: BaziConfig(dayun_year_rule='fixed_decade')), # type: ignore
  ]

  failures: list[str] = []
  for label, expected, thunk in checks:
    try:
      thunk()
      failures.append(f'{label}: no exception, expected {expected.__name__}')
    except expected:
      pass
    except Exception as e: # noqa: BLE001 # a smoke harness reports whatever actually leaked
      failures.append(f'{label}: {type(e).__name__} ({e}), expected {expected.__name__}')

  for line in failures:
    print(f'FAIL {line}')
  print(f'o_smoke: {len(checks) - len(failures)}/{len(checks)} public faces hold under -O.')
  return 1 if failures else 0


if __name__ == '__main__':
  sys.exit(main())
