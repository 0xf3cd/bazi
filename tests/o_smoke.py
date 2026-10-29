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
  import inspect
  import json
  import os
  from tempfile import TemporaryDirectory
  from dataclasses import fields, replace
  from datetime import UTC, date, datetime, timedelta, timezone, tzinfo
  from collections.abc import Callable
  from functools import partial
  from fractions import Fraction
  from zoneinfo import ZoneInfo
  from unittest.mock import patch
  from typing import Any, get_args

  from bazi.defines import Zhu, Tiangan, TianganLayer, Dizhi, Ganzhi, Jieqi, TianganRelation, DizhiRelation
  from bazi.bazi import Bazi, BaziGender
  from bazi.bazi_chart import BaziChart
  from bazi.knowledge import DEFAULT_SOURCE_PATH, KnowledgeBase, KnowledgeEntry, KnowledgeRole, LegacyDescription, object_id
  from bazi.context_matching import (
    NatalObservation, LiunianObservation, TransitObservation, LiunianPosition, ChartOccurrence,
    YearCoordinate, MonthCoordinate, DateCoordinate, MomentCoordinate, ScopeName, CriterionReason,
    CriterionResult,
    criterion as lookup_criterion, evaluate_context,
  )
  from bazi.common import frozendict
  from bazi.rules import DizhiRules, DizhiRelationDefinitions
  from bazi.school import Anchor, BaziConfig, BaziSchool
  from bazi.transit_chart import TransitChart
  from bazi.transits import TransitDatabase, TransitKind, TransitSet
  from bazi.analyzer.relationship import (
    RelationshipAnalyzer, KongwangHit, KongwangResult, _REGISTRY, _AnchorKind, spouse_evidence,
  )
  from bazi.utils import tiangan_utils, dizhi_utils, shensha_utils, bazi_utils
  from bazi.calendar import CalendarDate, CalendarType, hko_data, hko_data_utils
  from bazi.calendar.dates import GanzhiYearMonth, JieqiTime
  from bazi.calendar.celestial_utils import ALGO1, ALGO2
  from bazi.calendar.backend import CalendarBackend, calendar_utils_of
  from bazi.calendar.solar_time import apparent_solar_datetime

  chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
  transit_chart = TransitChart(chart)
  transit_db = TransitDatabase(chart)
  year_transits = transit_chart.at_year(2024)
  if year_transits is None:
    raise RuntimeError('Expected year 2024 to be supported')
  liunian = year_transits.select(TransitKind.LIUNIAN)
  transit_analysis = RelationshipAnalyzer(chart).transits
  chart_input = chart.bazi
  decoded_jieqi = hko_data.DecodedJieqiDates()
  knowledge = KnowledgeBase.load()
  solar_date = CalendarDate(2024, 1, 1, CalendarType.公历)
  aware_birth = datetime(2000, 1, 1, 12, tzinfo=UTC)
  location_config = BaziConfig.from_values(precision='minute')
  civil_zone = timezone(timedelta(hours=14))
  local_chart = BaziChart(Bazi.create('2024-01-01T12:00:00+14:00', 'female', location_config, longitude=-157.4))
  local_result = evaluate_context(local_chart, criterion_id='editorial.guansha_coexistence.v1', observation=NatalObservation())
  from bazi.analyzer.relationship import StarAppearance
  relationship_result = evaluate_context(chart, criterion_id='editorial.spouse_star_tougan.v1', observation=NatalObservation())
  def load_source(text: str) -> KnowledgeBase:
    with TemporaryDirectory(prefix='bazi-source-', dir=os.environ.get('SCRATCH')) as directory:
      source = Path(directory) / 'knowledge.json'
      source.write_text(text, encoding='utf-8')
      return KnowledgeBase.load(source)

  class Year(int):
    pass

  class MissingOffset(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
      return None
    def dst(self, dt: datetime | None) -> None:
      return None
    def tzname(self, dt: datetime | None) -> None:
      return None
    def fromutc(self, dt: datetime) -> datetime:
      return dt

  class EqualKey:
    def __init__(self, value: object) -> None:
      self.value = value

    def __eq__(self, other: object) -> bool:
      return self.value == other

    def __hash__(self) -> int:
      return hash(self.value)

  checks: list[tuple[str, type[Exception], Callable[[], object]]] = [
    ('Ganzhi.next rejects 甲丑', ValueError, lambda: Ganzhi.from_str('甲丑').next()),
    ('Ganzhi.prev rejects 甲丑 even at zero', ValueError, lambda: Ganzhi.from_str('甲丑').prev(0)),
    ('Jieqi.jies rejects int', TypeError, lambda: Jieqi.jies(1)), # type: ignore[arg-type]
    ('nayin_str rejects 甲丑', ValueError,
     lambda: bazi_utils.nayin_str(Ganzhi.from_str('甲丑'))),
    ('xing rejects four Dizhis', ValueError,
     lambda: dizhi_utils.xing(Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.午)),
    ('xing rejects five Dizhis', ValueError,
     lambda: dizhi_utils.xing(Dizhi.寅, Dizhi.巳, Dizhi.申, Dizhi.午, Dizhi.午)),
    ('Bazi.random wrong rng', TypeError,
     lambda: Bazi.random(rng=42)), # type: ignore[arg-type]
    ('BaziChart.random wrong rng', TypeError,
     lambda: BaziChart.random(rng=42)), # type: ignore[arg-type]
    ('Bazi.create civil timezone without longitude', ValueError,
     lambda: Bazi.create(datetime(2000, 1, 1), 'male', civil_timezone=civil_zone)),
    ('Bazi constructor civil timezone without longitude', ValueError,
     lambda: Bazi(datetime(2000, 1, 1), BaziGender.男, civil_timezone=civil_zone)),
    ('Bazi.create civil timezone wrong type', TypeError,
     lambda: Bazi.create(aware_birth, 'male', location_config, longitude=0.0, civil_timezone='+14:00')), # type: ignore[arg-type]
    ('Bazi constructor civil timezone wrong type', TypeError,
     lambda: Bazi(aware_birth, BaziGender.男, location_config, longitude=0.0, civil_timezone=14)), # type: ignore[arg-type]
    ('LiunianObservation rejects bool year', TypeError, lambda: LiunianObservation(True)),
    ('LiunianObservation rejects int subclass year', TypeError, lambda: LiunianObservation(Year(2024))),
    ('LiunianPosition rejects bool year', TypeError, lambda: LiunianPosition(True)),
    ('NatalObservation rejects a coordinate', TypeError, lambda: NatalObservation(2024)), # type: ignore[call-arg]
    ('YearCoordinate rejects bool year', TypeError, lambda: YearCoordinate(True)),
    ('YearCoordinate rejects int subclass', TypeError, lambda: YearCoordinate(Year(2024))),
    ('MonthCoordinate rejects bool year', TypeError, lambda: MonthCoordinate(True, Dizhi.辰)),
    ('MomentCoordinate rejects tz-aware moment', ValueError,
     lambda: MomentCoordinate(datetime(2024, 4, 10, 12, tzinfo=ZoneInfo('Asia/Shanghai')))),
    ('DateCoordinate rejects datetime', TypeError, lambda: DateCoordinate(datetime(2024, 4, 10, 12))),
    ('MonthCoordinate rejects missing field', TypeError, lambda: MonthCoordinate(2024)), # type: ignore[call-arg]
    ('YearCoordinate rejects foreign field', TypeError,
     lambda: YearCoordinate(2024, ganzhi_month=Dizhi.辰)), # type: ignore[call-arg]
    ('TransitObservation rejects empty kinds', ValueError, lambda: TransitObservation(())),
    ('TransitObservation rejects non-tuple kinds', TypeError,
     lambda: TransitObservation([TransitKind.LIUNIAN])), # type: ignore[arg-type]
    ('TransitObservation rejects duplicate kinds', ValueError,
     lambda: TransitObservation((TransitKind.LIUNIAN, TransitKind.LIUNIAN))),
    ('TransitObservation rejects kinds beyond entry', ValueError,
     lambda: TransitObservation((TransitKind.LIUYUE,), YearCoordinate(2024))),
    ('evaluate_context rejects observation mismatch', ValueError,
     lambda: evaluate_context(chart, criterion_id='editorial.spouse_star_tougan.v1', observation=LiunianObservation())),
    ('Relationship record rejects liunian observation', ValueError,
     lambda: replace(relationship_result, observation=LiunianObservation())),
    ('Context record rejects relationship evidence', ValueError,
     lambda: replace(positive, evidence=relationship_result.evidence)),
    ('StarAppearance rejects string position', TypeError,
     lambda: StarAppearance('liuyue', Ganzhi.from_str('辛亥'), TianganLayer.明干, Tiangan.辛)), # type: ignore[arg-type]
    ('StarAppearance rejects integer position', TypeError,
     lambda: StarAppearance(1, Ganzhi.from_str('辛亥'), TianganLayer.明干, Tiangan.辛)), # type: ignore[arg-type]
    ('StarAppearance rejects string layer', TypeError,
     lambda: StarAppearance(TransitKind.LIUNIAN, Ganzhi.from_str('辛亥'), '明干', Tiangan.辛)), # type: ignore[arg-type]
    ('spouse_evidence rejects non-chart', TypeError,
     lambda: spouse_evidence('chart', None)), # type: ignore[arg-type]
    ('spouse_evidence rejects non-TransitSet transits', TypeError,
     lambda: spouse_evidence(chart, 'transits')), # type: ignore[arg-type]
    ('MonthCoordinate rejects str month', TypeError, lambda: MonthCoordinate(2024, '辰')), # type: ignore[arg-type]
    ('MomentCoordinate rejects date', TypeError, lambda: MomentCoordinate(date(2024, 4, 10))), # type: ignore[arg-type]
    ('TransitObservation rejects non-coordinate', TypeError,
     lambda: TransitObservation((TransitKind.LIUNIAN,), 'at_year')), # type: ignore[arg-type]
    ('BaziSchool rejects non-enum peiou_xing_def', TypeError,
     lambda: BaziSchool(peiou_xing_def=1)), # type: ignore[arg-type]
    ('StarAppearance rejects visible stem mismatch', ValueError,
     lambda: StarAppearance(TransitKind.LIUNIAN, Ganzhi.from_str('辛亥'), TianganLayer.明干, Tiangan.庚)),
    ('StarAppearance rejects absent hidden stem', ValueError,
     lambda: StarAppearance(Zhu.时, Ganzhi.from_str('辛亥'), TianganLayer.藏干, Tiangan.辛)),
    ('evaluate_context rejects unknown criterion', ValueError,
     lambda: evaluate_context(chart, criterion_id='typo', observation=NatalObservation())),
    ('evaluate_context rejects wrong observation', TypeError,
     lambda: evaluate_context(chart, criterion_id='editorial.guansha_coexistence.v1', observation='natal')), # type: ignore[arg-type]
    ('evaluate_context rejects truthy reference flag', TypeError,
     lambda: evaluate_context(chart, criterion_id='editorial.guansha_coexistence.v1', observation=NatalObservation(), include_reference_only=1)), # type: ignore[arg-type]
    ('ContextResult rejects wrong Bazi input', TypeError,
     lambda: replace(local_result, _bazi=42)), # type: ignore[arg-type]
    ('Bazi.create below window (1901-01-01)', ValueError,
     lambda: Bazi.create(datetime(1901, 1, 1, 12), 'male')),
    ('Bazi.create above window (2100-06-01)', ValueError,
     lambda: Bazi.create(datetime(2100, 6, 1, 12), 'male')),
    ('Bazi.create tz-aware birth time', ValueError,
     lambda: Bazi.create(datetime(2000, 1, 1, 7, tzinfo=ZoneInfo('Asia/Shanghai')), 'male')),
    ('Bazi.create naive birth with longitude', ValueError,
     lambda: Bazi.create(datetime(2000, 1, 1, 12), 'male', location_config, longitude=120.0)),
    ('Bazi.create bool longitude', TypeError,
     lambda: Bazi.create(aware_birth, 'male', location_config, longitude=True)),
    ('Bazi.create non-real longitude', TypeError,
     lambda: Bazi.create(aware_birth, 'male', location_config, longitude='120')), # type: ignore[arg-type]
    ('Bazi.create non-finite longitude', ValueError,
     lambda: Bazi.create(aware_birth, 'male', location_config, longitude=float('nan'))),
    ('Bazi.create out-of-range longitude', ValueError,
     lambda: Bazi.create(aware_birth, 'male', location_config, longitude=180.1)),
    ('Bazi.create DAY with longitude', ValueError,
     lambda: Bazi.create(aware_birth, 'male', BaziConfig(), longitude=120.0)),
    ('Bazi.create HKO with longitude', ValueError,
     lambda: Bazi.create(
       aware_birth, 'male', BaziConfig.from_values(precision='minute', backend='hko'), longitude=120.0,
     )),
    ('Bazi.create CELESTIAL_ALGO2 with longitude', ValueError,
     lambda: Bazi.create(
       aware_birth, 'male',
       BaziConfig.from_values(precision='minute', backend='celestial-algo2'), longitude=120.0,
     )),
    ('Bazi constructor aware without longitude', ValueError,
     lambda: Bazi(aware_birth, BaziGender.男, location_config)),
    ('Bazi constructor naive birth with longitude', ValueError,
     lambda: Bazi(datetime(2000, 1, 1, 12), BaziGender.男, location_config, longitude=120.0)),
    ('Bazi constructor bool longitude', TypeError,
     lambda: Bazi(aware_birth, BaziGender.男, location_config, longitude=True)),
    ('Bazi constructor non-real longitude', TypeError,
     lambda: Bazi(aware_birth, BaziGender.男, location_config, longitude='120')), # type: ignore[arg-type]
    ('Bazi constructor non-finite longitude', ValueError,
     lambda: Bazi(aware_birth, BaziGender.男, location_config, longitude=float('inf'))),
    ('Bazi constructor out-of-range longitude', ValueError,
     lambda: Bazi(aware_birth, BaziGender.男, location_config, longitude=-180.1)),
    ('Bazi constructor DAY with longitude', ValueError,
     lambda: Bazi(aware_birth, BaziGender.男, BaziConfig(), longitude=120.0)),
    ('Bazi constructor HKO with longitude', ValueError,
     lambda: Bazi(
       aware_birth, BaziGender.男,
       BaziConfig.from_values(precision='minute', backend='hko'), longitude=120.0,
     )),
    ('Bazi constructor CELESTIAL_ALGO2 with longitude', ValueError,
     lambda: Bazi(
       aware_birth, BaziGender.男,
       BaziConfig.from_values(precision='minute', backend='celestial-algo2'), longitude=120.0,
     )),
    ('Bazi.random wrong config', TypeError,
     lambda: Bazi.random(None)), # type: ignore
    ('BaziChart.random wrong config', TypeError,
     lambda: BaziChart.random(False)), # type: ignore
    ('Bazi.random unsupported config', ValueError,
     lambda: Bazi.random(BaziConfig.from_values(backend='hko', precision='hour'))),
    ('BaziChart.random unsupported config', ValueError,
     lambda: BaziChart.random(BaziConfig.from_values(backend='hko', precision='minute'))),
    ('knowledge object_id raw subject', TypeError,
     lambda: object_id('食神')), # type: ignore[arg-type]
    ('knowledge object_id unrelated enum', TypeError,
     lambda: object_id(Dizhi.子)), # type: ignore[arg-type]
    ('KnowledgeBase.render_subject wrong identifier', TypeError,
     lambda: knowledge.render_subject(Tiangan.甲)), # type: ignore[arg-type]
    ('Criterion directory wrong ID type', TypeError,
     lambda: lookup_criterion(1)), # type: ignore[arg-type]
    ('Criterion directory unknown ID', ValueError,
     lambda: lookup_criterion('unknown')),
    ('KnowledgeBase.find_objects wrong name', TypeError,
     lambda: knowledge.find_objects(1)), # type: ignore[arg-type]
    ('KnowledgeBase.find_objects blank name', ValueError,
     lambda: knowledge.find_objects('   ')),
    ('KnowledgeBase.search wrong keyword', TypeError,
     lambda: knowledge.search(1)), # type: ignore[arg-type]
    ('KnowledgeBase.search blank keyword', ValueError,
     lambda: knowledge.search('   ')),
    ('KnowledgeBase.search invalid filter before empty result', ValueError,
     lambda: knowledge.search('no match', topic='unknown')),
    ('KnowledgeBase.filter_values wrong dimension type', TypeError,
     lambda: knowledge.filter_values(1)), # type: ignore[arg-type]
    ('KnowledgeBase.filter_values unknown dimension', ValueError,
     lambda: knowledge.filter_values('include_reference_only')),
    ('KnowledgeBase.render_subject unknown object', ValueError,
     lambda: knowledge.render_subject('missing')),
    ('KnowledgeBase.render_subject truthy reference flag', TypeError,
     lambda: knowledge.render_subject('tiangan.jia', include_reference_only=1)), # type: ignore[arg-type]
    ('KnowledgeBase.render_subject falsy reference flag', TypeError,
     lambda: knowledge.render_subject('tiangan.jia', include_reference_only=0)), # type: ignore[arg-type]
    ('KnowledgeBase.render_subject null reference flag', TypeError,
     lambda: knowledge.render_subject('tiangan.jia', include_reference_only=None)), # type: ignore[arg-type]
    ('KnowledgeBase.render_subject invalid display flag on empty selection', TypeError,
     lambda: knowledge.render_subject('shishen.jiecai', show_sources=1)), # type: ignore[arg-type]
    ('KnowledgeBase.render wrong verdict type', TypeError,
     lambda: knowledge.render(knowledge.entry('tiangan.jia.definition'), premise_verdict=1)), # type: ignore[arg-type]
    ('KnowledgeBase.render empty verdict', ValueError,
     lambda: knowledge.render(knowledge.entry('tiangan.jia.definition'), premise_verdict='')),
    ('KnowledgeBase.render whitespace verdict', ValueError,
     lambda: knowledge.render(knowledge.entry('tiangan.jia.definition'), premise_verdict=' \t\n\u3000')),
    ('KnowledgeEntry mutable sources', TypeError,
     lambda: replace(knowledge.entry('tiangan.jia.definition'), sources=[])), # type: ignore[arg-type]
    ('KnowledgeBase unknown filter', ValueError,
     lambda: knowledge.query(object_id='unknown')),
    ('KnowledgeBase wrong filter type', TypeError,
     lambda: knowledge.query(object_id=42)), # type: ignore[arg-type]
    ('KnowledgeBase truthy reference flag', TypeError,
     lambda: knowledge.query(include_reference_only=1)), # type: ignore[arg-type]
    ('KnowledgeBase wrong source type', TypeError,
     lambda: KnowledgeBase.load([])), # type: ignore[arg-type]
    ('KnowledgeBase duplicate JSON keys', ValueError,
     lambda: load_source('{"schema_version":1,"schema_version":1}')),
    ('KnowledgeRole wrong object type', TypeError,
     lambda: KnowledgeRole('role', 1)), # type: ignore[arg-type]
    ('KnowledgeEntry ineligible default', ValueError,
     lambda: replace(knowledge.entry('legacy.shishen.SH-199'), show_by_default=True)),
    ('KnowledgeEntry unconditional legacy condition', ValueError,
     lambda: replace(
       knowledge.entry('tiangan.ding.definition'),
       legacy=LegacyDescription('tiangan.ding', 'general', 0, ('chart_context_required',), ''),
     )),
    ('KnowledgeEntry unconditional legacy field premise', ValueError,
     lambda: replace(
       knowledge.entry('tiangan.ding.definition'),
       legacy=LegacyDescription('tiangan.ding', 'general', 0, (), 'Unexpected legacy field premise'),
     )),
    ('LegacyDescription wrong condition member', ValueError,
     lambda: LegacyDescription('tiangan.jia', 'general', 0, ('invalid',), '')),
    ('KnowledgeSource wrong text layer', ValueError,
      lambda: replace(
        knowledge.sources['editorial'],
        text_layer='invalid',
      )),
    ('KnowledgeSource wrong lineage type', TypeError,
      lambda: replace(
        knowledge.sources['editorial'],
        lineage=1, # type: ignore[arg-type]
      )),
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
       definitions=DizhiRules.GongheDef.NARROW, # type: ignore
     )),
    ('dizhi_utils.discover_mutual_ganzhis on raw Dizhis', TypeError,
     lambda: dizhi_utils.discover_mutual_ganzhis([Dizhi.申], [Dizhi.辰])), # type: ignore
    ('shensha_utils.kuigang on raw string', TypeError,
     lambda: shensha_utils.kuigang('庚辰')), # type: ignore
    ('shensha_utils.tianshe on raw month string', TypeError,
     lambda: shensha_utils.tianshe('寅', Ganzhi.from_str('戊寅'))), # type: ignore
    ('shensha_utils.tianshe on raw day string', TypeError,
     lambda: shensha_utils.tianshe(Dizhi.寅, '戊寅')), # type: ignore
    ('BaziSchool wrong Yima anchor', TypeError,
     lambda: BaziSchool(yima_anchor=object())), # type: ignore
    ('BaziSchool unsupported Hongyan anchor', ValueError,
     lambda: BaziSchool(hongyan_anchor=Anchor.YEAR_AND_DAY)),
    ('BaziSchool wrong Jinyu anchor', TypeError,
     lambda: BaziSchool(jinyu_anchor=object())), # type: ignore
    ('BaziSchool wrong Feiren definition', TypeError,
     lambda: BaziSchool(feiren_def=object())), # type: ignore
    ('BaziSchool wrong Zaisha anchor', TypeError,
     lambda: BaziSchool(zaisha_anchor=object())), # type: ignore
    ('DecodedLunarYears.get out of range', ValueError,
     lambda: hko_data.DecodedLunarYears().get(1800)),
    ('jieqi_moment out of range', ValueError,
     lambda: hko_data_utils.jieqi_moment(1900, Jieqi.冬至)),
    # Warm and reject in one thunk on the same receiver: cold misses cannot expose a cache bypass.
    ('DecodedJieqiDates.get warm cache wrong year', TypeError,
     lambda: (decoded_jieqi.get(2024, Jieqi.立春), decoded_jieqi.get(2024.0, Jieqi.立春))), # type: ignore
    ('DecodedJieqiDates.get wrong Jieqi', TypeError,
     lambda: decoded_jieqi.get(2024, '立春')), # type: ignore
    ('HKO jieqi_date warm cache wrong year', TypeError,
     lambda: (hko_data_utils.jieqi_date(2024, Jieqi.立春), hko_data_utils.jieqi_date(2024.0, Jieqi.立春))), # type: ignore
    ('HKO jieqi_moment warm cache wrong year', TypeError,
     lambda: (hko_data_utils.jieqi_moment(2024, Jieqi.立春), hko_data_utils.jieqi_moment(2024.0, Jieqi.立春))), # type: ignore
    ('ALGO1 jieqi_date warm cache wrong year', TypeError,
     lambda: (ALGO1.jieqi_date(2024, Jieqi.立春), ALGO1.jieqi_date(2024.0, Jieqi.立春))), # type: ignore
    ('ALGO1 jieqi_moment warm cache wrong year', TypeError,
     lambda: (ALGO1.jieqi_moment(2024, Jieqi.立春), ALGO1.jieqi_moment(2024.0, Jieqi.立春))), # type: ignore
    ('ALGO2 jieqi_date warm cache wrong year', TypeError,
     lambda: (ALGO2.jieqi_date(2024, Jieqi.立春), ALGO2.jieqi_date(2024.0, Jieqi.立春))), # type: ignore
    ('ALGO2 jieqi_moment warm cache wrong year', TypeError,
     lambda: (ALGO2.jieqi_moment(2024, Jieqi.立春), ALGO2.jieqi_moment(2024.0, Jieqi.立春))), # type: ignore
    ('HKO month lengths int-subclass warm cache wrong year', TypeError,
     lambda: (hko_data_utils.days_counts_in_ganzhi_year(Year(2024)), hko_data_utils.days_counts_in_ganzhi_year(2024.0))), # type: ignore
    ('ALGO1 month lengths int-subclass warm cache wrong year', TypeError,
     lambda: (ALGO1.days_counts_in_ganzhi_year(Year(2024)), ALGO1.days_counts_in_ganzhi_year(2024.0))), # type: ignore
    ('ALGO2 month lengths int-subclass warm cache wrong year', TypeError,
     lambda: (ALGO2.days_counts_in_ganzhi_year(Year(2024)), ALGO2.days_counts_in_ganzhi_year(2024.0))), # type: ignore
    ('HKO rejects lunar day zero inside the supported range', ValueError,
     lambda: hko_data_utils.to_solar(CalendarDate(2000, 6, 0, CalendarType.LUNAR))),
    ('HKO rejects Ganzhi day zero inside the supported range', ValueError,
     lambda: hko_data_utils.to_solar(CalendarDate(2000, 6, 0, CalendarType.GANZHI))),
    ('HKO rejects negative lunar day inside the supported range', ValueError,
     lambda: hko_data_utils.to_solar(CalendarDate(2000, 6, -1, CalendarType.LUNAR))),
    ('HKO rejects negative Ganzhi day inside the supported range', ValueError,
     lambda: hko_data_utils.to_solar(CalendarDate(2000, 6, -1, CalendarType.GANZHI))),
    ('CalendarDate ordering foreign rhs', TypeError,
     lambda: solar_date < date(2024, 1, 1)),
    ('CalendarDate ordering foreign lhs', TypeError,
     lambda: date(2024, 1, 1) < solar_date),
    ('CalendarDate ordering different calendars', TypeError,
     lambda: solar_date >= CalendarDate(2024, 1, 1, CalendarType.农历)),
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
    ('hko get_min_supported_date garbage date_type', TypeError,
     lambda: hko_data_utils.get_min_supported_date(42)), # type: ignore[arg-type] # Deliberately invalid input.
    ('celestial get_max_supported_date garbage date_type', TypeError,
     lambda: calendar_utils_of(CalendarBackend.CELESTIAL).get_max_supported_date(42)), # type: ignore
    ('calendar_utils_of garbage backend', TypeError,
     lambda: calendar_utils_of(42)), # type: ignore
    ('BaziConfig wrong Dayun year rule type', TypeError,
     lambda: BaziConfig(dayun_year_rule='fixed_decade')), # type: ignore
  ]

  sequence_iterators = []
  for module, member, relation in (
    (tiangan_utils, Tiangan.甲, TianganRelation.合),
    (dizhi_utils, Dizhi.辰, DizhiRelation.刑),
  ):
    calls = (
      partial(module.search, relation=relation),
      module.discover,
      partial(module.discover_mutual, []),
      lambda values, module=module: module.discover_mutual(values, []),
    )
    for index, call in enumerate(calls):
      label = f'{module.__name__} Sequence entry {index}'
      values = iter((member,))
      sequence_iterators.append((label, values, member))
      checks.append((label, TypeError, partial(call, values)))
      checks.append((label + ' empty iterator', TypeError, partial(call, iter(()))))

  for backend in CalendarBackend:
    utils = calendar_utils_of(backend)
    date_calls: list[tuple[str, object]] = [
      ('get_min_supported_date', CalendarType.SOLAR),
      ('get_max_supported_date', CalendarType.SOLAR),
      ('is_valid', solar_date),
      *[(f'is_valid_{kind}_date', CalendarDate(2024, 1, 1, CalendarType[kind.upper()]))
        for kind in ('solar', 'lunar', 'ganzhi')],
      *[(f'{source}_to_{target}', CalendarDate(2024, 1, 1, CalendarType[source.upper()]))
        for source in ('solar', 'lunar', 'ganzhi') for target in ('solar', 'lunar', 'ganzhi') if source != target],
      *[(name, datetime(2024, 3, 1)) for name in ('to_solar', 'to_lunar', 'to_ganzhi', 'to_date', 'prev_jie', 'next_jie')],
    ]
    for name, good in date_calls:
      method = getattr(utils, name)
      method(good)
      bad = EqualKey(good)
      if not (bad == good and good == bad and hash(bad) == hash(good)):
        raise RuntimeError('Cache collision control failed')
      checks.append((f'{backend}.{name} warm cache wrong type', TypeError, partial(method, bad)))

  for step in (Ganzhi.from_str('甲子').next, Ganzhi.from_str('甲子').prev):
    step(1)
    checks.append((f'Ganzhi.{step.__name__} warm cache wrong type', TypeError, partial(step, 1.0))) # type: ignore[arg-type]

  # The registry covers branch results; the whole-pillar predicates stay explicit above.
  for name, spec in _REGISTRY.items():
    key = {
      _AnchorKind.TIANGAN: Tiangan.甲,
      _AnchorKind.DIZHI: Dizhi.子,
      _AnchorKind.GANZHI: Ganzhi.from_str('甲子'),
    }[spec.kind]
    spec.predicate(key, Dizhi.子)
    checks.extend([
      (f'shensha_utils.{name} wrong key', TypeError, partial(spec.predicate, str(key), Dizhi.子)),
      (f'shensha_utils.{name} wrong dizhi', TypeError, partial(spec.predicate, key, '子')),
    ])
    if 'definition' in inspect.signature(spec.predicate).parameters:
      checks.extend([
        (f'shensha_utils.{name} wrong definition', TypeError,
         partial(spec.predicate, key, Dizhi.子, definition=object())),
        (f'shensha_utils.{name} wrong definition enum', TypeError,
         partial(spec.predicate, key, Dizhi.子, definition=DizhiRules.AnheDef.NORMAL)),
      ])

  shensha_utils.xunkong(Ganzhi.from_str('甲子'))
  for bad_anchor, expected_error in (
    ('甲子', TypeError),
    (Ganzhi.from_str('甲丑'), ValueError),
    (Ganzhi('甲', Dizhi.子), TypeError), # type: ignore[arg-type]
    (Ganzhi(Tiangan.甲, '子'), TypeError), # type: ignore[arg-type]
  ):
    checks.extend([
      ('xunkong rejects invalid anchor', expected_error, partial(shensha_utils.xunkong, bad_anchor)), # type: ignore[arg-type]
      ('kongwang rejects invalid anchor', expected_error, partial(shensha_utils.kongwang, bad_anchor, Dizhi.戌)), # type: ignore[arg-type]
    ])

  kongwang_anchor = Ganzhi.from_str('甲子')
  kongwang_target = Ganzhi.from_str('甲戌')
  kongwang_natal_hit = KongwangHit(Zhu.时, kongwang_target)
  kongwang_transit_hit = KongwangHit(TransitKind.DAYUN, kongwang_target)
  KongwangResult(Zhu.日, kongwang_anchor, (kongwang_natal_hit,))
  KongwangResult(Zhu.年, kongwang_anchor, (kongwang_transit_hit,))
  for rejected_anchor in (Zhu.月, Zhu.YUE, Zhu.时, Zhu.SHI):
    checks.append((
      'KongwangResult rejects month/hour aliases', ValueError,
      partial(KongwangResult, rejected_anchor, kongwang_anchor, ()), # type: ignore[arg-type] # 月／时不属于年日静态子集。
    ))
  checks.extend([
    ('KongwangHit wrong Ganzhi type', TypeError,
     lambda: KongwangHit(Zhu.时, '甲戌')), # type: ignore[arg-type]
    ('KongwangHit unknown position', TypeError,
     lambda: replace(kongwang_natal_hit, position='unknown')), # type: ignore[arg-type]
    ('KongwangResult wrong Ganzhi type', TypeError,
     lambda: KongwangResult(Zhu.日, '甲子', ())), # type: ignore[arg-type]
    ('KongwangResult unknown anchor', ValueError,
     lambda: KongwangResult(Zhu.月, kongwang_anchor, ())), # type: ignore[arg-type] # 月不在年日静态子集中。
    ('KongwangResult mutable hits', TypeError,
     lambda: KongwangResult(Zhu.日, kongwang_anchor, [kongwang_natal_hit])), # type: ignore[arg-type]
    ('KongwangResult hit outside xunkong', ValueError,
     lambda: KongwangResult(Zhu.日, kongwang_anchor, (replace(kongwang_natal_hit, ganzhi=kongwang_anchor),))),
    ('KongwangResult natal anchor inspects itself', ValueError,
     lambda: KongwangResult(Zhu.日, kongwang_anchor, (replace(kongwang_natal_hit, position=Zhu.日),))),
  ])

  for name, longitude_value in (('integer', 10 ** 10_000), ('fraction', Fraction(10 ** 10_000, 3))):
    for sign in (-1, 1):
      checks.extend([
        (f'Bazi.create overflowing {name} sign={sign}', ValueError,
         partial(Bazi.create, aware_birth, 'male', location_config, longitude=sign * longitude_value)), # type: ignore[arg-type]
        (f'Bazi constructor overflowing {name} sign={sign}', ValueError,
         partial(Bazi, aware_birth, BaziGender.男, location_config, longitude=sign * longitude_value)), # type: ignore[arg-type]
      ])

  criterion_metadata = lookup_criterion('editorial.guansha_coexistence.v1')
  for metadata_field in (
    'criterion_id', 'definition', 'analysis_kind', 'entry_role', 'observation_keys',
    'required_gender', 'claim_ids', 'claim_genders',
  ):
    checks.append((f'CriterionInfo rejects wrong {metadata_field}', TypeError,
                   partial(replace, criterion_metadata, **{metadata_field: object()})))
  checks.extend([
    ('CriterionInfo rejects blank ID', ValueError, partial(replace, criterion_metadata, criterion_id=' ')),
    ('CriterionInfo rejects empty definition', ValueError, partial(replace, criterion_metadata, definition='')),
    ('CriterionInfo rejects empty metadata', ValueError, partial(replace, criterion_metadata, claim_ids=())),
    ('CriterionInfo rejects unsupported analysis kind', ValueError, partial(replace, criterion_metadata, analysis_kind='unknown')),
    ('CriterionInfo remains frozen', AttributeError, partial(setattr, criterion_metadata, 'definition', 'changed')),
  ])

  no_offset_birth = datetime(2000, 1, 1, tzinfo=MissingOffset())
  checks.extend([
    ('Bazi.create birth with None UTC offset', ValueError,
     partial(Bazi.create, no_offset_birth, 'male', location_config, longitude=0.0)),
    ('Bazi constructor birth with None UTC offset', ValueError,
     partial(Bazi, no_offset_birth, BaziGender.男, location_config, longitude=0.0)),
    ('Solar time wrong datetime type', TypeError,
     partial(apparent_solar_datetime, 42, 0.0)), # type: ignore[arg-type]
    ('Solar time naive civil datetime', ValueError,
     partial(apparent_solar_datetime, datetime(2000, 1, 1), 0.0)),
    ('Solar time birth with None UTC offset', ValueError,
     partial(apparent_solar_datetime, no_offset_birth, 0.0)),
    ('Solar time bool longitude', TypeError,
     partial(apparent_solar_datetime, aware_birth, True)),
    ('Solar time string longitude', TypeError,
     partial(apparent_solar_datetime, aware_birth, '0')), # type: ignore[arg-type]
    ('Solar time non-finite longitude', ValueError,
     partial(apparent_solar_datetime, aware_birth, float('nan'))),
    ('Solar time out-of-range longitude', ValueError,
     partial(apparent_solar_datetime, aware_birth, 180.01)),
    ('Solar time overflowing longitude', ValueError,
     partial(apparent_solar_datetime, aware_birth, 10 ** 400)),
    ('Bazi.create birth outside EOT and birth windows', ValueError,
     partial(Bazi.create, datetime(1850, 1, 1, tzinfo=UTC), 'male', location_config, longitude=0.0)),
    ('Bazi constructor birth outside EOT and birth windows', ValueError,
     partial(Bazi, datetime(2200, 1, 1, tzinfo=UTC), BaziGender.男, location_config, longitude=0.0)),
  ])

  checks.extend([
    ('GanzhiYearMonth wrong year', TypeError, partial(GanzhiYearMonth, '2000', 1)), # type: ignore[arg-type]
    ('GanzhiYearMonth wrong month type', TypeError, partial(GanzhiYearMonth, 2000, '1')), # type: ignore[arg-type]
    ('GanzhiYearMonth zero-based month', ValueError, partial(GanzhiYearMonth, 2000, 0)),
    ('GanzhiYearMonth month above range', ValueError, partial(GanzhiYearMonth, 2000, 13)),
    ('GanzhiYearMonth wrong branch', TypeError, partial(GanzhiYearMonth.from_dizhi, 2000, '寅')), # type: ignore[arg-type]
    ('GanzhiYearMonth wrong Jie container', TypeError, partial(GanzhiYearMonth.from_jie, None)), # type: ignore[arg-type]
    ('GanzhiYearMonth wrong Jie member', TypeError,
     partial(GanzhiYearMonth.from_jie, JieqiTime('立春', datetime(2000, 2, 4)))), # type: ignore[arg-type]
    ('GanzhiYearMonth wrong Jie moment', TypeError,
     partial(GanzhiYearMonth.from_jie, JieqiTime(Jieqi.立春, '2000-02-04'))), # type: ignore[arg-type]
    ('GanzhiYearMonth 中气', ValueError, partial(GanzhiYearMonth.from_jie, JieqiTime(Jieqi.雨水, datetime(2000, 2, 19)))),
    ('GanzhiYearMonth readonly month', AttributeError, partial(setattr, GanzhiYearMonth(2000, 1), 'month', 12)),
    ('Bazi readonly reference', AttributeError, partial(setattr, local_chart.bazi, 'reference_datetime', datetime(2000, 1, 1))),
    ('LocationTime readonly facts', AttributeError, partial(setattr, local_chart.bazi.location_time, 'longitude', 0.0)),
  ])
  for field, invalid_definition in (
    ('anhe_def', 'NORMAL_EXTENDED'), ('anhe_def', 0), ('anhe_def', DizhiRules.XingDef.LOOSE),
    ('xing_def', 'LOOSE'), ('xing_def', 1), ('xing_def', DizhiRules.AnheDef.NORMAL),
    ('gong_def', 'NARROW'), ('gong_def', 0), ('gong_def', DizhiRules.GongheDef.NARROW),
  ):
    checks.append((f'Relation definitions wrong {field}: {invalid_definition}', TypeError,
                   partial(replace, DizhiRelationDefinitions(), **{field: invalid_definition})))
  for query, args in (
    (dizhi_utils.search, ([], DizhiRelation.六合)),
    (dizhi_utils.discover, ([],)),
    (dizhi_utils.discover_mutual, ([], [])),
    (dizhi_utils.search_ganzhis, ([], DizhiRelation.拱合)),
    (dizhi_utils.discover_ganzhis, ([],)),
    (dizhi_utils.discover_mutual_ganzhis, ([], [])),
  ):
    checks.append((f'{query.__name__} wrong definitions', TypeError, partial(query, *args, definitions=None))) # type: ignore[arg-type]
  for query, args in (
    (dizhi_utils.discover_ganzhis, ([],)),
    (dizhi_utils.discover_mutual_ganzhis, ([], [])),
  ):
    for relations in (iter(DizhiRelation), [TianganRelation.合]):
      checks.append((f'{query.__name__} wrong relations', TypeError, partial(query, *args, relations=relations))) # type: ignore[arg-type]
  failures: list[str] = []
  for anchor in (Zhu.年, Zhu.NIAN, Zhu.日, Zhu.RI):
    if KongwangResult(anchor, kongwang_anchor, ()).anchor is not anchor:
      failures.append('Optimized year/day anchor alias changed')
  for label, birth, basis in (
    ('UTC underflow', datetime.min.replace(tzinfo=timezone(timedelta(hours=14))), None),
    ('UTC overflow', datetime.max.replace(tzinfo=timezone(timedelta(hours=-12))), None),
    ('civil underflow', datetime.min.replace(tzinfo=UTC), timezone(timedelta(hours=-12))),
    ('civil overflow', datetime.max.replace(tzinfo=UTC), timezone(timedelta(hours=14))),
  ):
    checks.extend([
      (f'Bazi.create {label}', ValueError,
       partial(Bazi.create, birth, 'male', location_config, longitude=0.0, civil_timezone=basis)),
      (f'Bazi constructor {label}', ValueError,
       partial(Bazi, birth, BaziGender.男, location_config, longitude=0.0, civil_timezone=basis)),
    ])
  from bazi.calendar.celestial_data.loader import EquationOfTimeTable
  for birth in (
    datetime.min.replace(tzinfo=timezone(timedelta(hours=14))),
    datetime.max.replace(tzinfo=timezone(timedelta(hours=-12))),
  ):
    checks.extend([
      ('Solar primitive UTC conversion overflow', ValueError, partial(apparent_solar_datetime, birth, 0.0)),
      ('EOT reader UTC conversion overflow', ValueError, partial(EquationOfTimeTable().seconds_at, birth)),
    ])
  if local_chart.bazi.solar_date != date(2024, 1, 1) or local_chart.bazi.solar_datetime != datetime(2024, 1, 1, 11, 27):
    failures.append('Optimized Kiritimati civil date lost')
  if local_result.bazi != local_chart.bazi or local_result.bazi.location_time != local_chart.bazi.location_time:
    failures.append('Optimized context input lost location facts')
  location_bazi = local_chart.bazi
  for moment in (location_bazi.reference_datetime, location_bazi.solar_datetime):
    legacy_bazi = Bazi.create(moment, 'female', location_config)
    if not (legacy_bazi != location_bazi and location_bazi != legacy_bazi and len({legacy_bazi, location_bazi}) == 2):
      failures.append('Optimized legacy/location identity partition failed')
  missing = evaluate_context(chart, criterion_id='editorial.guansha_coexistence.v1', observation=LiunianObservation())
  if missing.criterion.status != 'UNKNOWN' or missing.criterion.reason != 'missing_transit_coordinate':
    failures.append('Missing year became a false verdict')
  positive = evaluate_context(chart, criterion_id='editorial.guansha_coexistence.v1', observation=LiunianObservation(2024), include_reference_only=True)
  if positive.criterion.status != 'SATISFIED' or positive.reference_ids != ('editorial.shishen.zhengguan.legal_trouble', 'editorial.shishen.qisha.legal_trouble') or positive.bazi != chart.bazi:
    failures.append('Optimized context evaluation/input failed')
  condition = evaluate_context(chart, criterion_id='shishen.pianyin_favorable_or_balanced', observation=NatalObservation(), include_reference_only=True)
  range_evidence = spouse_evidence(chart, None)
  obtained_evidence = replace(range_evidence, transits=liunian)
  missing_scope = evaluate_context(
    chart, criterion_id='editorial.spouse_star_tougan.v1',
    observation=TransitObservation((TransitKind.LIUNIAN,)),
  )
  partial_scope = evaluate_context(
    chart, criterion_id='editorial.spouse_star_tougan.v1',
    observation=TransitObservation((TransitKind.XIAOYUN, TransitKind.DAYUN), YearCoordinate(2024)),
  )
  outside_evidence = replace(range_evidence, house_relations=dizhi_utils.GanzhiRelationDiscovery({
    DizhiRelation.冲: (frozenset({dizhi_utils.GanzhiOccurrence(9, Ganzhi.from_str('甲子'))}),),
  }))
  checks.extend([
    ('ContextResult rejects natal obtained transits', ValueError,
     partial(replace, relationship_result, evidence=obtained_evidence)),
    ('ContextResult rejects obtained kinds outside request', ValueError,
     partial(replace, missing_scope, observation=TransitObservation((TransitKind.DAYUN,)), evidence=obtained_evidence)),
    ('ContextResult rejects complete scope without query', ValueError,
     partial(replace, missing_scope, criterion=replace(missing_scope.criterion, reason='premise_satisfied'))),
    ('ContextResult rejects complete scope with partial kinds', ValueError,
     partial(replace, partial_scope, criterion=replace(partial_scope.criterion, reason='premise_satisfied'))),
    ('ContextResult rejects evidence outside sequence', ValueError,
     partial(replace, relationship_result, evidence=outside_evidence)),
    ('Context knowledge object type', TypeError, partial(replace, positive, knowledge=None)),
    ('CriterionResult rejects entry-only reason', ValueError,
     partial(CriterionResult, 'editorial.guansha_coexistence.v1', 'binding_unrecognized', frozendict({}))), # type: ignore[arg-type]
    ('ChartOccurrence rejects foreign position', TypeError,
     partial(ChartOccurrence, TransitKind.LIUNIAN, Ganzhi.from_str('甲子'), TianganLayer.明干, Tiangan.甲, bazi_utils.shishen(Tiangan.甲, Tiangan.甲))), # type: ignore[arg-type]
    ('ChartOccurrence excludes day master visible', ValueError,
     partial(ChartOccurrence, Zhu.日, Ganzhi.from_str('甲子'), TianganLayer.明干, Tiangan.甲, bazi_utils.shishen(Tiangan.甲, Tiangan.甲))),
    ('ChartOccurrence rejects string layer', TypeError,
     partial(ChartOccurrence, Zhu.年, Ganzhi.from_str('甲子'), '明干', Tiangan.甲, bazi_utils.shishen(Tiangan.甲, Tiangan.甲))), # type: ignore[arg-type]
    ('ContextResult rejects mutable IDs', TypeError, partial(replace, positive, reference_ids=[])),
    ('ContextResult rejects non-string ID', TypeError, partial(replace, positive, reference_ids=(1,))),
    ('ContextResult rejects missing ID', ValueError, partial(replace, positive, reference_ids=('unknown',))),
    ('ContextResult rejects empty ID', ValueError, partial(replace, positive, reference_ids=('',))),
    ('ContextResult rejects old references field', TypeError, partial(replace, positive, references=())),
    ('ContextResult rejects foreign evidence', TypeError, partial(replace, positive, evidence=object())),
    ('CriterionResult rejects non-bool observation', TypeError,
     partial(CriterionResult, 'editorial.guansha_coexistence.v1', 'premise_satisfied', frozendict({'known': 1}))), # type: ignore[dict-item]
  ])
  if get_args(ScopeName) != ('natal', 'natal_and_liunian', 'natal_and_transits') or set(get_args(CriterionReason)) != {
    'premise_satisfied', 'required_classification_absent', 'day_master_differs', 'female_gate_false',
    'missing_transit_coordinate', 'transit_unavailable',
  }:
    failures.append('Optimized scope/reason public subsets changed')
  empty_condition = replace(condition, reference_ids=())
  if '事实判别不表示原文完整条件已满足' not in empty_condition.render():
    failures.append('Optimized empty condition references lost their role')
  ids = (positive.reference_ids[1], positive.reference_ids[0], positive.reference_ids[1])
  if replace(positive, reference_ids=ids).reference_ids != ids:
    failures.append('Optimized manual reference IDs lost order or repeats')
  if replace(positive, reference_ids=('tiangan.ding.definition',)).reference_ids != ('tiangan.ding.definition',):
    failures.append('Optimized manual IDs gained an unapproved claim-membership gate')
  def auxiliary_type_error(thunk: Callable[[], object], name: str, value: object) -> object:
    # Verify the canonical first failure even when Python strips every assert.
    try:
      return thunk()
    except TypeError as error:
      if str(error) != f'Expected {name}, got {type(value)}':
        raise RuntimeError(f'Unexpected auxiliary type message: {error}') from error
      raise

  auxiliary_bad: object
  for auxiliary_bad in ('子', 0, 13, None, [], True):
    for name, operation in (
      ('Ganzhi', partial(bazi_utils.taiyuan, auxiliary_bad)), # type: ignore[arg-type]
      ('Tiangan', partial(bazi_utils.taiyuan, Ganzhi(auxiliary_bad, Dizhi.子))), # type: ignore[arg-type]
      ('Dizhi', partial(bazi_utils.taiyuan, Ganzhi(Tiangan.甲, auxiliary_bad))), # type: ignore[arg-type]
      ('Tiangan', partial(bazi_utils.minggong, auxiliary_bad, Dizhi.寅, Dizhi.子)), # type: ignore[arg-type]
      ('Dizhi', partial(bazi_utils.minggong, Tiangan.甲, auxiliary_bad, Dizhi.子)), # type: ignore[arg-type]
      ('Dizhi', partial(bazi_utils.minggong, Tiangan.甲, Dizhi.寅, auxiliary_bad)), # type: ignore[arg-type]
    ):
      checks.append((f'Auxiliary {name} rejects {auxiliary_bad!r}: {operation}', TypeError,
                     partial(auxiliary_type_error, operation, name, auxiliary_bad)))
  for tg in Tiangan:
    for dz in Dizhi:
      if tg.index % 2 != dz.index % 2:
        checks.append((f'Taiyuan rejects {tg}{dz}', ValueError, partial(bazi_utils.taiyuan, Ganzhi(tg, dz))))
  if bazi_utils.taiyuan(Ganzhi.from_str('己巳')) != Ganzhi.from_str('庚申'):
    failures.append('Optimized 胎元 example failed')
  if bazi_utils.minggong(Tiangan.甲, Dizhi.辰, Dizhi.戌) != Ganzhi.from_str('丁卯'):
    failures.append('Optimized 命宫 example failed')
  _ = chart.taiyuan, chart.minggong
  if chart.bazi != chart_input or len(chart.bazi.pillars) != 4:
    failures.append('Optimized auxiliary query changed the natal chart')

  source_data = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  if source_data['schema_version'] != 3 or KnowledgeBase._from_data(source_data) != knowledge:
    failures.append('Optimized schema3 source did not load')
  display_entry = knowledge.entry('tiangan.ding.definition')
  display_bad: Any
  for display_bad in (1, 0, 'true', None):
    bad_source = json.loads(json.dumps(source_data))
    bad_source['entries'][0]['show_by_default'] = display_bad
    checks.extend([
      (f'KnowledgeEntry rejects non-bool display {display_bad!r}', TypeError, partial(replace, display_entry, show_by_default=display_bad)),
      (f'KnowledgeEntry constructor rejects non-bool display {display_bad!r}', TypeError,
       partial(KnowledgeEntry, **{**{f.name: getattr(display_entry, f.name) for f in fields(display_entry)}, 'show_by_default': display_bad})),
      (f'Editing source rejects non-bool display {display_bad!r}', TypeError, partial(load_source, json.dumps(bad_source))),
    ])
  for version in (1, 2, 3.0, True, '3'):
    checks.append((f'Knowledge rejects source version {version!r}', ValueError, partial(load_source, json.dumps({**source_data, 'schema_version': version}))))
  for mutation in ('old', 'extra', 'missing'):
    bad_source = json.loads(json.dumps(source_data))
    row = bad_source['entries'][0]
    if mutation == 'old':
      row['output'] = 'default' if row.pop('show_by_default') else 'reference_only'
    elif mutation == 'extra':
      row['output'] = 'default'
    else:
      del row['show_by_default']
    checks.append((f'Knowledge rejects {mutation} display fields', ValueError, partial(load_source, json.dumps(bad_source))))
  bad_knowledge = json.loads(DEFAULT_SOURCE_PATH.read_text(encoding='utf-8'))
  bad_knowledge['entries'][0]['text'] = '\ud800'
  def parser_limit(load: Callable[[str], object]) -> None:
    with patch('json.loads', side_effect=RecursionError('injected parser limit')):
      load('{}')

  checks.extend([
    ('Knowledge rejects surrogate', ValueError, partial(load_source, json.dumps(bad_knowledge))),
    ('Context render rejects surrogate key', ValueError, lambda: replace(positive, criterion=replace(positive.criterion, observations=frozendict({'\ud800': True}))).render()),
  ])
  checks.append(('Source parser limit remains a value error', ValueError, partial(parser_limit, load_source)))

  for relation_query in (tiangan_utils.he, tiangan_utils.chong, tiangan_utils.sheng, tiangan_utils.ke):
    for operands in ((True, Tiangan.甲), (Tiangan.甲, True)):
      checks.append((f'{relation_query.__name__} rejects bool at either position', TypeError, partial(relation_query, *operands)))
  for dz_query in (
    dizhi_utils.liuhe, dizhi_utils.anhe, dizhi_utils.tonghe, dizhi_utils.tongluhe,
    dizhi_utils.banhe, dizhi_utils.gonghe, dizhi_utils.gonghui,
    dizhi_utils.chong, dizhi_utils.po, dizhi_utils.hai, dizhi_utils.sheng, dizhi_utils.ke,
  ):
    for dz_operands in ((True, Dizhi.子), (Dizhi.子, True)):
      checks.append((f'{dz_query.__name__} rejects bool at either position', TypeError, partial(dz_query, *dz_operands)))
  for triple_query in (dizhi_utils.sanhui, dizhi_utils.sanhe):
    for dz_triple in ((True, Dizhi.子, Dizhi.丑), (Dizhi.子, True, Dizhi.丑), (Dizhi.子, Dizhi.丑, True)):
      checks.append((f'{triple_query.__name__} rejects bool at every position', TypeError, partial(triple_query, *dz_triple)))
  decoded_lunar = hko_data.DecodedLunarYears()
  for bool_year in (True, False):
    checks.extend([
      ('Jieqi get rejects bool year by range', ValueError, partial(decoded_jieqi.get, bool_year, Jieqi.立春)),
      ('Jieqi index rejects bool year by range', ValueError, partial(decoded_jieqi.__getitem__, bool_year)),
      ('Lunar get rejects bool year by range', ValueError, partial(decoded_lunar.get, bool_year)),
      ('Lunar index rejects bool year by range', ValueError, partial(decoded_lunar.__getitem__, bool_year)),
    ])

  for label, expected, thunk in checks:
    try:
      thunk()
      failures.append(f'{label}: no exception, expected {expected.__name__}')
    except expected:
      pass
    except Exception as e: # noqa: BLE001 # a smoke harness reports whatever actually leaked
      failures.append(f'{label}: {type(e).__name__} ({e}), expected {expected.__name__}')

  for label, values, member in sequence_iterators:
    if tuple(values) != (member,):
      failures.append(f'{label}: rejected iterator was consumed')
  for line in failures:
    print(f'FAIL {line}')
  print(f'o_smoke: {len(checks) - len(failures)}/{len(checks)} public faces hold under -O.')
  return 1 if failures else 0


if __name__ == '__main__':
  sys.exit(main())
