# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import random
import re

import pytest

from bazi import cli
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.chart_text import basic_text, chart_text, transit_text


ANSI = re.compile(r'\x1b\[[0-9;]*m')


def _charts(rng: random.Random) -> list[BaziChart]:
  return [BaziChart(Bazi.random(rng=rng)) for _ in range(5)]


def test_demo_reuses_the_package_renderer(rng: random.Random) -> None:
  for chart in _charts(rng):
    assert cli._get_basic_info(chart) == basic_text(chart, style=cli._TERMINAL_STYLE)
    assert cli._get_transit_info(chart) == transit_text(chart, style=cli._TERMINAL_STYLE)


def test_demo_output_keeps_terminal_color(rng: random.Random) -> None:
  for chart in _charts(rng):
    colored = cli._get_basic_info(chart) + cli._get_transit_info(chart)
    assert '\x1b[' in colored and ANSI.sub('', colored) == chart_text(chart)


def test_demo_colors_glyphs_and_day_master(rng: random.Random) -> None:
  chart = _charts(rng)[0]
  text = cli._get_basic_info(chart)
  assert text.count(cli._highlighted_day_master('日主')) == 1
  assert cli._colored_str(chart.bazi.day_master) in text


def test_main_demo_keeps_the_complete_report(capsys: pytest.CaptureFixture[str]) -> None:
  state = random.getstate()
  chart = BaziChart(Bazi.random(rng=random.Random(236)))
  assert cli.main(['demo', '--seed', '236']) == 0
  output = capsys.readouterr()
  assert output.err == ''
  assert output.out == f'random seed: 236\n{cli._get_basic_info(chart)}\n{cli._get_transit_info(chart)}\n'
  assert random.getstate() == state
