# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_chart_text.py

import itertools
import random
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.calendar import calendar_utils_of
from bazi.chart_text import TextStyle, basic_text, chart_text, transit_text
from bazi.defines import Tiangan, Dizhi
from bazi.school import BaziConfig
from bazi.utils.bazi_utils import hidden_tiangans, nayin_str, shishen, shier_zhangsheng, traits


DATA = Path(__file__).parent / 'data'

DEFAULT_CHART = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
LOCATION_CHART = BaziChart(Bazi.create(
  datetime(2000, 1, 1, 12, tzinfo=timezone(timedelta(hours=-5))), 'female',
  BaziConfig.from_values(precision='minute'), longitude=-75,
))

# 一个干支字形加其“[阴阳五行] <十神>”标注。
_ANNOTATED = re.compile(r'(\S) \[(\S\S)\] <([^>]+)>')


@pytest.mark.parametrize('name, chart', [
  ('chart_text_default.txt', DEFAULT_CHART),
  ('chart_text_location.txt', LOCATION_CHART),
])
def test_fixed_chart_text_is_stable(name: str, chart: BaziChart) -> None:
  assert chart_text(chart) == (DATA / name).read_text(encoding='utf-8')


def test_plain_text_has_no_terminal_escapes(rng: random.Random) -> None:
  chart = BaziChart.random(rng=rng)
  text = chart_text(chart)
  assert '\x1b' not in text
  assert text.startswith('\n') and text.endswith('\n')
  assert text == basic_text(chart) + transit_text(chart)


def test_text_is_replayable_from_same_input() -> None:
  again = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male'))
  assert chart_text(again) == chart_text(DEFAULT_CHART)


def test_pillar_lines_match_chart_fields(rng: random.Random) -> None:
  chart = BaziChart.random(rng=rng)
  bazi = chart.bazi
  shishens, hidden = list(chart.shishen), list(chart.hidden_tiangan)
  nayins, zhangshengs = list(chart.nayin), list(chart.shier_zhangsheng)
  lines = basic_text(chart).splitlines()
  pillar_lines = [line for line in lines if re.match(r'[年月日时]：', line)]
  assert len(pillar_lines) == 4
  for idx, line in enumerate(pillar_lines):
    tiangan, dizhi = bazi.pillars[idx]
    (tg, tg_traits, tg_label), (dz, dz_traits, dz_label), *stems = _ANNOTATED.findall(line)
    assert (tg, tg_traits) == (str(tiangan), f'{traits(tiangan).yinyang}{traits(tiangan).wuxing}')
    assert tg_label == ('日主' if idx == 2 else str(shishens[idx].tiangan))
    assert (dz, dz_traits) == (str(dizhi), f'{traits(dizhi).yinyang}{traits(dizhi).wuxing}')
    assert dz_label == str(shishens[idx].dizhi)
    assert [(g, label) for g, _, label in stems] == [
      (str(stem), shishen(bazi.day_master, stem).abbr) for stem in hidden[idx]
    ]
    assert lines[lines.index(line) + 1] == f'  -- 纳音：{nayins[idx]}  -- 十二长生：{zhangshengs[idx]}'


def test_header_follows_birth_input_kind() -> None:
  default_lines = basic_text(DEFAULT_CHART).splitlines()
  assert default_lines[1] == '日元戊土，male，生于 2000-01-01'
  assert '出生时刻：2000-01-01T12:00:00' in default_lines
  location_lines = basic_text(LOCATION_CHART).splitlines()
  assert '日元戊土，female，真太阳时日期：2000-01-01' in location_lines
  assert '民用出生时刻（固定出生地偏移）：2000-01-01T12:00:00-05:00；经度=-75.0' in location_lines
  assert not any(line.startswith('出生时刻：') for line in location_lines)


@pytest.mark.parametrize('dayun_count, liunian_count', [(0, 0), (1, 1), (3, 25), (10, 100), (12, 7)])
def test_transit_rows_follow_requested_counts(dayun_count: int, liunian_count: int) -> None:
  chart = DEFAULT_CHART
  text = transit_text(chart, dayun_count=dayun_count, liunian_count=liunian_count)
  lines = text.splitlines()

  dayun_rows = [line for line in lines if '年标签：' in line]
  expected_dayun = list(itertools.islice(chart.dayun, dayun_count))
  assert len(dayun_rows) == len(expected_dayun) == dayun_count
  for row, dayun in zip(dayun_rows, expected_dayun, strict=True):
    assert row.startswith(f'{dayun.ganzhi_year}年标签：')
    glyphs = [g for g, _, _ in _ANNOTATED.findall(row)[:2]]
    assert glyphs == [str(dayun.ganzhi.tiangan), str(dayun.ganzhi.dizhi)]
  ranges = [line for line in lines if '公历区间：' in line]
  assert ranges == [
    f'               -- 公历区间：{d.start_moment:%Y-%m-%d %H:%M} ～ {d.end_moment:%Y-%m-%d %H:%M}'
    for d in expected_dayun
  ]

  xiaoyun_at = lines.index('小运：')
  liunian_at = lines.index('流年：')
  xiaoyun_entries = '  '.join(lines[xiaoyun_at + 1:liunian_at - 1]).split('  ')
  assert xiaoyun_entries == [f'{xy.xusui}岁-{xy.ganzhi}' for xy in chart.xiaoyun]
  liunian_entries = '  '.join(lines[liunian_at + 1:]).split('  ')
  assert [e for e in liunian_entries if e.strip()] == [
    f'{ln.ganzhi_year}-{ln.ganzhi}' for ln in itertools.islice(chart.liunian, liunian_count)
  ]


def test_transit_header_names_the_counted_jie() -> None:
  chart = DEFAULT_CHART
  utils = calendar_utils_of(chart.bazi.config.backend)
  before = utils.prev_jie(chart.bazi.reference_datetime)
  after = utils.next_jie(chart.bazi.reference_datetime)
  lines = transit_text(chart).splitlines()
  assert f'出生时刻前一节：{before.jieqi} - {before.moment.isoformat()}' in lines
  assert f'出生时刻后一节：{after.jieqi} - {after.moment.isoformat()}' in lines
  assert f'交运时间： {chart.dayun_start_moment.isoformat()}' in lines
  assert sum(line.startswith('大运数节依据（') for line in lines) == 1
  assert '节与大运区间采用节气表时刻（UTC+08:00），不采用真太阳时。' not in lines
  assert '节与大运区间采用节气表时刻（UTC+08:00），不采用真太阳时。' in transit_text(LOCATION_CHART).splitlines()


def test_dayun_rows_hold_hidden_stems_and_labels() -> None:
  chart = DEFAULT_CHART
  day_master = chart.bazi.day_master
  rows = [line for line in transit_text(chart, dayun_count=3).splitlines() if '年标签：' in line]
  for row, dayun in zip(rows, itertools.islice(chart.dayun, 3), strict=True):
    found = _ANNOTATED.findall(row)
    assert [label for _, _, label in found[:2]] == [str(shishen(day_master, dayun.ganzhi.tiangan)), str(shishen(day_master, dayun.ganzhi.dizhi))]
    assert [(g, label) for g, _, label in found[2:]] == [
      (str(tg), shishen(day_master, tg).abbr) for tg in hidden_tiangans(dayun.ganzhi.dizhi)
    ]
  nayin_rows = [line for line in transit_text(chart, dayun_count=3).splitlines() if '-- 纳音：' in line]
  assert nayin_rows == [
    f'               -- 纳音：{nayin_str(d.ganzhi)}  -- 十二长生：{shier_zhangsheng(day_master, d.ganzhi.dizhi)}'
    for d in itertools.islice(chart.dayun, 3)
  ]


def test_style_wraps_glyphs_and_day_master_mark() -> None:
  seen: list[Tiangan | Dizhi] = []

  def glyph(s: Tiangan | Dizhi) -> str:
    seen.append(s)
    return f'«{s}»'

  style = TextStyle(glyph=glyph, day_master_mark=lambda label: f'**{label}**')
  text = basic_text(DEFAULT_CHART, style=style)
  assert text.count('**日主**') == 1
  assert text.count('«') == text.count('»') == len(seen)
  assert all(isinstance(s, (Tiangan, Dizhi)) for s in seen)
  assert text.replace('«', '').replace('»', '').replace('**日主**', '日主') == basic_text(DEFAULT_CHART)


def test_style_covers_ganzhi_rows_per_glyph() -> None:
  chart = DEFAULT_CHART
  calls: list[str] = []

  def glyph(s: Tiangan | Dizhi) -> str:
    calls.append(str(s))
    return ''

  style = TextStyle(glyph=glyph)
  text = transit_text(chart, dayun_count=0, liunian_count=0, style=style)
  assert [e for e in text.splitlines() if '岁-' in e]
  assert len(calls) == 2 * len(chart.xiaoyun)


def test_default_style_is_plain() -> None:
  assert TextStyle().glyph is None and TextStyle().day_master_mark is None
  assert basic_text(DEFAULT_CHART, style=TextStyle()) == basic_text(DEFAULT_CHART)
  assert transit_text(DEFAULT_CHART, style=TextStyle()) == transit_text(DEFAULT_CHART)


def test_each_hook_can_be_set_alone() -> None:
  marked = basic_text(DEFAULT_CHART, style=TextStyle(day_master_mark=lambda label: f'*{label}*'))
  assert marked.count('*日主*') == 1 and marked.replace('*日主*', '日主') == basic_text(DEFAULT_CHART)
  glyphs = basic_text(DEFAULT_CHART, style=TextStyle(glyph=lambda s: f'«{s}»'))
  assert '«' in glyphs and '日主' in glyphs and '«日主»' not in glyphs


@pytest.mark.parametrize('field', ['glyph', 'day_master_mark'])
def test_style_rejects_non_callables(field: str) -> None:
  with pytest.raises(TypeError, match=r'Expected callable \| None'):
    TextStyle(**{field: 'x'}) # type: ignore


@pytest.mark.parametrize('func', [basic_text, transit_text, chart_text])
def test_functions_reject_wrong_chart_with_hint(func: object) -> None:
  with pytest.raises(TypeError, match=r'Expected BaziChart, got .*; wrap it with BaziChart\(bazi\)'):
    func(DEFAULT_CHART.bazi) # type: ignore
  with pytest.raises(TypeError, match='Expected BaziChart'):
    func(None) # type: ignore


@pytest.mark.parametrize('func', [basic_text, transit_text, chart_text])
def test_functions_reject_wrong_style_type(func: object) -> None:
  with pytest.raises(TypeError, match=r'Expected TextStyle \| None'):
    func(DEFAULT_CHART, style=str) # type: ignore


@pytest.mark.parametrize('func', [transit_text, chart_text])
@pytest.mark.parametrize('name', ['dayun_count', 'liunian_count'])
def test_counts_reject_wrong_values(func: object, name: str) -> None:
  with pytest.raises(TypeError, match='Expected int'):
    func(DEFAULT_CHART, **{name: '3'}) # type: ignore
  with pytest.raises(ValueError, match=f'Unsupported {name}: -1'):
    func(DEFAULT_CHART, **{name: -1}) # type: ignore


def test_style_wraps_dayun_and_liunian_glyphs() -> None:
  chart = DEFAULT_CHART
  calls: list[str] = []

  def glyph(s: Tiangan | Dizhi) -> str:
    calls.append(str(s))
    return f'«{s}»'

  text = transit_text(chart, dayun_count=3, liunian_count=20, style=TextStyle(glyph=glyph))
  assert text.replace('«', '').replace('»', '') == transit_text(chart, dayun_count=3, liunian_count=20)
  expected = list(itertools.islice(chart.dayun, 3))
  hidden_count = sum(len(hidden_tiangans(d.ganzhi.dizhi)) for d in expected)
  assert len(calls) == 2 * 3 + hidden_count + 2 * len(chart.xiaoyun) + 2 * 20
  dayun_rows = [line for line in text.splitlines() if '年标签：' in line]
  assert [(f'«{d.ganzhi.tiangan}»' in row, f'«{d.ganzhi.dizhi}»' in row) for d, row in zip(expected, dayun_rows, strict=True)] == [(True, True)] * 3
  liunian_rows = text.split('流年：\n', 1)[1]
  assert liunian_rows.count('«') == 2 * 20 and all(f'«{ln.ganzhi.tiangan}»«{ln.ganzhi.dizhi}»' in liunian_rows for ln in itertools.islice(chart.liunian, 20))


def test_chart_text_forwards_transit_counts() -> None:
  chart = DEFAULT_CHART
  text = chart_text(chart, dayun_count=0, liunian_count=0)
  assert '年标签：' not in text
  assert text == basic_text(chart) + transit_text(chart, dayun_count=0, liunian_count=0)
  assert chart_text(chart, dayun_count=2, liunian_count=11).count('年标签：') == 2


def test_text_follows_the_hko_backend() -> None:
  chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male', BaziConfig.from_values(backend='hko')))
  utils = calendar_utils_of(chart.bazi.config.backend)
  before, after = utils.prev_jie(chart.bazi.reference_datetime), utils.next_jie(chart.bazi.reference_datetime)
  lines = chart_text(chart).splitlines()
  assert f'出生时刻前一节：{before.jieqi} - {before.moment.isoformat()}' in lines
  assert f'出生时刻后一节：{after.jieqi} - {after.moment.isoformat()}' in lines
  assert [line for line in lines if line.startswith(('年：', '月：', '日：', '时：'))][2].startswith('日：  ')


@pytest.mark.parametrize('precision', ['hour', 'minute'])
def test_basic_text_keeps_the_precision_pillars(precision: str) -> None:
  chart = BaziChart(Bazi.create(datetime(2009, 2, 3, 23, 30), 'female', BaziConfig.from_values(precision=precision)))
  lines = [line for line in basic_text(chart).splitlines() if line.startswith(('年：', '月：', '日：', '时：'))]
  for line, pillar in zip(lines, chart.bazi.pillars, strict=True):
    assert line.split('  ')[1].startswith(str(pillar.tiangan)) and f' {pillar.dizhi} [' in line
