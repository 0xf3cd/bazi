#!/usr/bin/env python3

import argparse
from random import Random, SystemRandom

from typing import Final

import colorama

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.chart_text import TextStyle, basic_text, transit_text
from bazi.defines import Tiangan, Dizhi, Wuxing, Ganzhi
from bazi.utils.bazi_utils import traits


def colored_str(s: Tiangan | Dizhi | Ganzhi) -> str:
  color_mapping_table: dict[Wuxing, str] = {
    Wuxing.火: colorama.Fore.RED,
    Wuxing.木: colorama.Fore.GREEN,
    Wuxing.金: colorama.Fore.YELLOW,
    Wuxing.水: colorama.Fore.BLUE,
    Wuxing.土: colorama.Fore.MAGENTA,
  }

  if isinstance(s, Ganzhi):
    return colored_str(s.tiangan) + colored_str(s.dizhi)
  else:
    wx = traits(s).wuxing
    return color_mapping_table[wx] + str(s) + colorama.Style.RESET_ALL


def highlighted_day_master(label: str) -> str:
  return colorama.Back.LIGHTBLUE_EX + colorama.Fore.BLACK + label + colorama.Style.RESET_ALL


# 命盘文本由安装包的 bazi.chart_text 生成，终端颜色在这里接入。
TERMINAL_STYLE: Final[TextStyle] = TextStyle(glyph=colored_str, day_master_mark=highlighted_day_master)


def get_basic_info(chart: BaziChart) -> str:
  return basic_text(chart, style=TERMINAL_STYLE)


def get_transit_info(chart: BaziChart) -> str:
  return transit_text(chart, style=TERMINAL_STYLE)


def demo(seed: int | None = None) -> None:
  seed = SystemRandom().getrandbits(64) if seed is None else seed
  print(f'random seed: {seed}')
  chart: BaziChart = BaziChart(Bazi.random(rng=Random(seed)))

  basic_info: str = get_basic_info(chart)
  print(basic_info)

  transit_info: str = get_transit_info(chart)
  print(transit_info)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='展示随机命盘及其流运。')
  parser.add_argument('--seed', type=int, help='重放随机示例的种子。')
  demo(parser.parse_args().seed)
