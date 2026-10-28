# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import copy
from datetime import datetime, time, timedelta, timezone
from itertools import islice

import pytest

from bazi.analyzer.relationship import RelationshipAnalyzer
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.calendar import calendar_utils_of
from bazi.calendar.solar_time import apparent_solar_datetime
from bazi.chart_text import chart_text
from bazi.defines import Dizhi, Ganzhi, Jieqi, Tiangan
from bazi.school import BaziConfig, BaziSchool, DayRollover
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind


ZHONGQI_MONTHS = (
  (Jieqi.雨水, 1), (Jieqi.春分, 2), (Jieqi.谷雨, 3), (Jieqi.小满, 4),
  (Jieqi.夏至, 5), (Jieqi.大暑, 6), (Jieqi.处暑, 7), (Jieqi.秋分, 8),
  (Jieqi.霜降, 9), (Jieqi.小雪, 10), (Jieqi.冬至, 11), (Jieqi.大寒, 12),
)
BACKEND_PRECISIONS = (
  ('hko', 'day'),
  ('celestial', 'day'), ('celestial', 'hour'), ('celestial', 'minute'),
  ('celestial-algo2', 'day'), ('celestial-algo2', 'hour'), ('celestial-algo2', 'minute'),
)
MONTH_BRANCHES = '寅卯辰巳午未申酉戌亥子丑'
HOUR_BRANCHES = '子丑寅卯辰巳午未申酉戌亥'
YEAR_MONTH_STEMS = {
  Tiangan.甲: '丙丁戊己庚辛壬癸甲乙丙丁', Tiangan.癸: '甲乙丙丁戊己庚辛壬癸甲乙',
  Tiangan.辛: '庚辛壬癸甲乙丙丁戊己庚辛', Tiangan.己: '丙丁戊己庚辛壬癸甲乙丙丁',
  Tiangan.丙: '庚辛壬癸甲乙丙丁戊己庚辛',
  Tiangan.壬: '壬癸甲乙丙丁戊己庚辛壬癸',
}


def _expected(year: Tiangan, month: int, hour: Dizhi) -> Ganzhi:
  # Walk a literal palm; do not call the production auxiliary/month helpers.
  position = 0
  for _ in range(month - 1):
    position = (position - 1) % 12
  moving = HOUR_BRANCHES.index(str(hour))
  while HOUR_BRANCHES[moving] != '卯':
    moving = (moving + 1) % 12
    position = (position + 1) % 12
  branch = HOUR_BRANCHES[position]
  return Ganzhi.from_str(YEAR_MONTH_STEMS[year][MONTH_BRANCHES.index(branch)] + branch)


def _grain_start(moment: datetime, precision: str) -> datetime:
  if precision == 'day':
    return datetime.combine(moment.date(), time.min)
  if precision == 'minute':
    return moment.replace(second=0, microsecond=0)
  midnight = datetime.combine(moment.date(), time.min)
  candidates = [midnight + timedelta(hours=hour) for hour in (-1, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23)]
  return max(candidate for candidate in candidates if candidate <= moment)


@pytest.mark.parametrize('backend,precision', BACKEND_PRECISIONS)
@pytest.mark.parametrize('zhongqi,month', ZHONGQI_MONTHS)
def test_twelve_zhongqi_grain_boundaries(backend: str, precision: str, zhongqi: Jieqi, month: int) -> None:
  boundary = calendar_utils_of(backend).jieqi_moment(2024, zhongqi)
  start = _grain_start(boundary, precision)
  unit = timedelta(days=1) if precision == 'day' else timedelta(hours=2) if precision == 'hour' else timedelta(minutes=1)
  for birth, advanced in ((start - timedelta(minutes=1), False), (start, True),
                          (boundary, True), (start + unit, True)):
    chart = BaziChart(Bazi.create(birth, 'male', BaziConfig.from_values(backend=backend, precision=precision)))
    year = Tiangan.癸 if month == 12 else Tiangan.甲
    effective_month = month % 12 + 1 if advanced else month
    hour = Dizhi(HOUR_BRANCHES[(birth.hour + 1) // 2 % 12])
    assert chart.bazi.month_pillar.dizhi is Dizhi(MONTH_BRANCHES[month - 1])
    assert chart.bazi.year_pillar.tiangan is year
    assert chart.bazi._attribution_reached(boundary) is advanced
    assert chart.minggong == _expected(year, effective_month, hour)
    assert chart.minggong is chart.minggong


@pytest.mark.parametrize('backend,precision', BACKEND_PRECISIONS)
@pytest.mark.parametrize('jie,month', [(Jieqi.立春, 1), (Jieqi.清明, 3), (Jieqi.小寒, 12)])
def test_opening_jie_keeps_effective_month(backend: str, precision: str, jie: Jieqi, month: int) -> None:
  boundary = calendar_utils_of(backend).jieqi_moment(2024, jie)
  start = _grain_start(boundary, precision)
  for birth, reached in ((start - timedelta(minutes=1), False), (start, True), (boundary, True)):
    chart = BaziChart(Bazi.create(birth, 'female', BaziConfig.from_values(backend=backend, precision=precision)))
    year = Tiangan.癸 if month == 12 or (month == 1 and not reached) else Tiangan.甲
    hour = Dizhi(HOUR_BRANCHES[(birth.hour + 1) // 2 % 12])
    assert chart.bazi.year_pillar.tiangan is year
    assert chart.bazi.month_jies[0].jieqi is (jie if reached else {
      Jieqi.立春: Jieqi.小寒, Jieqi.清明: Jieqi.惊蛰, Jieqi.小寒: Jieqi.大雪,
    }[jie])
    assert chart.minggong == _expected(year, month, hour)


def test_dahan_real_chart_retains_natal_year() -> None:
  # Derived calendar counterpart, not a dated natal example supplied by the book.
  chart = BaziChart(Bazi.create('1907-01-25 16:00', 'male'))
  assert str(chart.bazi.year_pillar) == '丙午'
  assert chart.bazi.month_pillar.dizhi is Dizhi.丑
  assert chart.bazi.month_jies[0].moment.year == 1907
  assert chart.bazi.ganzhi_year == 1906
  assert str(chart.minggong) == '乙未'


def test_hour_zhongqi_crosses_midnight() -> None:
  midnight_boundary = calendar_utils_of('celestial').jieqi_moment(2022, Jieqi.雨水)
  assert midnight_boundary == datetime(2022, 2, 19, 0, 42, 59)
  for birth, reached in (
    (datetime.combine(midnight_boundary.date(), time.min) - timedelta(hours=1, minutes=1), False),
    (datetime.combine(midnight_boundary.date(), time.min) - timedelta(hours=1), True),
    (midnight_boundary, True),
  ):
    bazi = Bazi.create(birth, 'male', BaziConfig.from_values(precision='hour'))
    assert bazi._attribution_reached(midnight_boundary) is reached
    hour = Dizhi.子 if reached else Dizhi.亥
    assert BaziChart(bazi).minggong == _expected(Tiangan.壬, 2 if reached else 1, hour)
    following = Bazi.create(birth + timedelta(days=1), 'male', BaziConfig.from_values(precision='hour'))
    assert following._attribution_reached(midnight_boundary)


@pytest.mark.parametrize('precision', ['hour', 'minute'])
def test_location_zhongqi_uses_apparent_grain(precision: str) -> None:
  zone = timezone(timedelta(hours=8))
  boundary = calendar_utils_of('celestial').jieqi_moment(2024, Jieqi.谷雨)
  longitude = 0.1
  apparent_boundary = apparent_solar_datetime(boundary.replace(tzinfo=zone), longitude)
  start = _grain_start(apparent_boundary, precision)
  # Search nearby real instants for both sides of the apparent-clock grain.
  pairs = []
  offsets = sorted({minute * 60 for minute in range(-125, 2)} | set(range(-59, 1)))
  for offset in offsets:
    instant = boundary.replace(tzinfo=zone) + timedelta(seconds=offset)
    apparent = apparent_solar_datetime(instant, longitude)
    reached = _grain_start(apparent, precision) >= start
    physical_reached = _grain_start(instant.replace(tzinfo=None), precision) >= _grain_start(boundary, precision)
    pairs.append((instant, apparent, reached, physical_reached))
  assert any(reached != physical for _, _, reached, physical in pairs)
  selected = [next(pair for pair in pairs if not pair[2]),
              next(pair for pair in pairs if pair[2]), pairs[-1]]
  for instant, apparent, reached, _ in selected:
    chart = BaziChart(Bazi.create(instant, 'male', BaziConfig.from_values(precision=precision), longitude=longitude))
    hour = Dizhi(HOUR_BRANCHES[(apparent.hour + 1) // 2 % 12])
    assert chart.bazi.hour_pillar.dizhi is hour
    assert chart.bazi._attribution_reached(boundary) is reached
    assert chart.minggong == _expected(Tiangan.甲, 4 if reached else 3, hour)


@pytest.mark.parametrize('precision', ['day', 'hour', 'minute'])
@pytest.mark.parametrize('birth,hour', [('2024-04-10 12:00', Dizhi.午), ('2024-04-10 23:30', Dizhi.子)])
def test_hour_source_ignores_day_rollover(precision: str, birth: str, hour: Dizhi) -> None:
  charts = [BaziChart(Bazi.create(birth, 'male', BaziConfig.from_values(
    precision=precision, school=BaziSchool(day_rollover=rollover),
  ))) for rollover in DayRollover]
  assert all(chart.bazi.hour_pillar.dizhi is hour for chart in charts)
  assert all(chart.minggong == _expected(Tiangan.甲, 3, hour) for chart in charts)
  if hour is Dizhi.子:
    assert charts[0].bazi.day_pillar != charts[1].bazi.day_pillar


@pytest.mark.parametrize('backend,precision', BACKEND_PRECISIONS)
@pytest.mark.parametrize('birth,year,month', [
  ('1901-02-19 12:00', Tiangan.辛, 2), ('2099-12-31 12:00', Tiangan.己, 12),
])
def test_auxiliary_at_real_window_endpoints(backend: str, precision: str, birth: str, year: Tiangan, month: int) -> None:
  chart = BaziChart(Bazi.create(birth, 'male', BaziConfig.from_values(backend=backend, precision=precision)))
  # 1901 雨水 is 15:45; DAY owns it all day, HOUR/MINUTE do not at noon.
  effective_month = 1 if birth.startswith('1901') and precision != 'day' else month
  assert chart.minggong == _expected(year, effective_month, Dizhi.午)
  pillar = chart.bazi.month_pillar
  assert chart.taiyuan == Ganzhi(
    Tiangan.from_index((pillar.tiangan.index + 1) % 10), Dizhi.from_index((pillar.dizhi.index + 3) % 12),
  )


@pytest.mark.parametrize('precision', ['hour', 'minute'])
def test_location_hour_ignores_rollover(precision: str) -> None:
  charts = [BaziChart(Bazi.create(
    '2024-04-11T07:30:00+08:00', 'male',
    BaziConfig.from_values(precision=precision, school=BaziSchool(day_rollover=rollover)),
    longitude=0.0,
  )) for rollover in DayRollover]
  for chart in charts:
    assert chart.bazi.hour_pillar.dizhi is Dizhi.子
    assert chart.bazi.solar_datetime.date() == datetime(2024, 4, 10).date()
    assert chart.minggong == _expected(Tiangan.甲, 3, Dizhi.子)
  assert charts[0].bazi.day_pillar != charts[1].bazi.day_pillar


@pytest.mark.parametrize('precision', ['hour', 'minute'])
def test_hko_still_rejects_subday_precision(precision: str) -> None:
  with pytest.raises(ValueError, match='needs real jieqi moments'):
    Bazi.create('2024-04-10 12:00', 'male', BaziConfig.from_values(backend='hko', precision=precision))


@pytest.mark.parametrize('located', [False, True])
def test_auxiliary_reads_preserve_old_contracts(located: bool) -> None:
  original = Bazi.create('2024-04-10T23:30:12+08:00' if located else '2024-04-10 23:30',
                         'male', BaziConfig.from_values(precision='minute'), longitude=0.0 if located else None)
  chart = BaziChart(original)
  snapshot = copy.deepcopy(original)
  identity_hash = hash(original)
  text = chart_text(chart)
  properties = (chart.traits, chart.hidden_tiangan, chart.shishen, chart.nayin, chart.shier_zhangsheng,
                chart.relationship_stars, tuple(chart.dayun), chart.xiaoyun, tuple(islice(chart.liunian, 3)))
  analyzer = RelationshipAnalyzer(chart)
  relations = (analyzer.at_birth.shensha, analyzer.at_birth.day_master_relations,
               analyzer.at_birth.house_relations)
  transit_chart = TransitChart(chart)
  year = transit_chart.at_year(2025)
  assert year is not None
  selected = year.select(TransitKind.LIUNIAN)
  transit_relations = analyzer.transits.shensha(selected)
  # A fresh instance reads the new properties in the opposite order.
  other = BaziChart(original)
  palace, embryo = other.minggong, other.taiyuan
  assert chart.taiyuan == embryo and chart.minggong == palace
  assert chart.taiyuan is chart.taiyuan and chart.minggong is chart.minggong
  assert original == snapshot == chart.bazi == other.bazi
  assert hash(original) == identity_hash == hash(chart.bazi)
  assert len(chart.bazi.pillars) == 4 and chart.bazi.pillars == snapshot.pillars
  assert chart.bazi == other.bazi
  assert chart_text(chart) == text
  assert properties == (chart.traits, chart.hidden_tiangan, chart.shishen, chart.nayin, chart.shier_zhangsheng,
                         chart.relationship_stars, tuple(chart.dayun), chart.xiaoyun, tuple(islice(chart.liunian, 3)))
  assert properties == (other.traits, other.hidden_tiangan, other.shishen, other.nayin, other.shier_zhangsheng,
                        other.relationship_stars, tuple(other.dayun), other.xiaoyun, tuple(islice(other.liunian, 3)))
  assert relations == (analyzer.at_birth.shensha, analyzer.at_birth.day_master_relations,
                       analyzer.at_birth.house_relations)
  assert analyzer.transits.shensha(selected) == transit_relations
