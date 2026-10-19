# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_run_demo.py

import random
import re

import run_demo
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.chart_text import basic_text, chart_text, transit_text


ANSI = re.compile(r'\x1b\[[0-9;]*m')


def _charts(rng: random.Random) -> list[BaziChart]:
  return [BaziChart(Bazi.random(rng=rng)) for _ in range(5)]


def test_demo_reuses_the_package_renderer(rng: random.Random) -> None:
  for chart in _charts(rng):
    assert run_demo.get_basic_info(chart) == basic_text(chart, style=run_demo.TERMINAL_STYLE)
    assert run_demo.get_transit_info(chart) == transit_text(chart, style=run_demo.TERMINAL_STYLE)


def test_demo_output_keeps_terminal_color(rng: random.Random) -> None:
  for chart in _charts(rng):
    colored = run_demo.get_basic_info(chart) + run_demo.get_transit_info(chart)
    assert '\x1b[' in colored and ANSI.sub('', colored) == chart_text(chart)


def test_demo_colors_glyphs_and_day_master(rng: random.Random) -> None:
  chart = _charts(rng)[0]
  text = run_demo.get_basic_info(chart)
  assert text.count(run_demo.highlighted_day_master('日主')) == 1
  assert run_demo.colored_str(chart.bazi.day_master) in text
