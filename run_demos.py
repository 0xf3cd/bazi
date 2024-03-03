#!/usr/bin/env python3

import sys
from pathlib import Path
from datetime import datetime

import colorama

sys.path.append(str(Path(__file__).parent.parent))
from bazi import (
  Tiangan, Dizhi, Wuxing, Ganzhi,
  Bazi, BaziChart, BaziGender, BaziPrecision, BaziUtils
)

def get_wuxing(s: Tiangan | Dizhi) -> Wuxing:
  assert isinstance(s, (Tiangan, Dizhi))
  if isinstance(s, Dizhi):
    return BaziUtils.get_dizhi_traits(s).wuxing
  else:
    return BaziUtils.get_tiangan_traits(s).wuxing

def colored_str(s: Tiangan | Dizhi) -> str:
  assert isinstance(s, (Tiangan, Dizhi))

  color_mapping_table: dict[Wuxing, str] = {
    Wuxing.火: colorama.Fore.RED,
    Wuxing.木: colorama.Fore.GREEN,
    Wuxing.金: colorama.Fore.YELLOW,
    Wuxing.水: colorama.Fore.BLUE,
    Wuxing.土: colorama.Fore.MAGENTA,
  }

  wx = get_wuxing(s)
  return color_mapping_table[wx] + str(s) + colorama.Style.RESET_ALL

def get_trait_str(s: Tiangan | Dizhi) -> str:
  assert isinstance(s, (Tiangan, Dizhi))

  if isinstance(s, Dizhi):
    traits = BaziUtils.get_dizhi_traits(s)
  else:
    traits = BaziUtils.get_tiangan_traits(s)

  return f'{traits.yinyang}{traits.wuxing}'

def print_basic_info(chart: BaziChart) -> None:
  bazi: Bazi = chart.bazi
  day_master_wx: Wuxing = get_wuxing(bazi.day_master)
  print(f'日元{colored_str(bazi.day_master)}{day_master_wx}，{bazi.gender}，生于 {bazi.solar_birth_date}\n')

  pillars: list[Ganzhi] = list(bazi.pillars)
  shishens: list[BaziChart.PillarShishens] = list(chart.shishens)
  hidden_tiangans: list[BaziChart.PillarHiddenTiangans] = list(chart.hidden_tiangans)

  print('     天干                  地支                  地支藏干')
  for idx, head in enumerate(['年', '月', '日', '时']):
    tg: Tiangan = pillars[idx].tiangan
    dz: Dizhi = pillars[idx].dizhi

    tg_str: str = colored_str(tg)
    dz_str: str = colored_str(dz)

    tg_traits: str = get_trait_str(tg)
    dz_traits: str = get_trait_str(dz)

    if idx == 2:
      tg_shishen: str = colorama.Back.LIGHTBLACK_EX + '日主' + colorama.Style.RESET_ALL
    else:
      assert shishens[idx].tiangan is not None
      tg_shishen: str = str(shishens[idx].tiangan)
    dz_shishen: str = str(shishens[idx].dizhi)

    hidden_dict = hidden_tiangans[idx].dizhi
    hidden_tgs: str = ' '.join([f'{colored_str(tg)} [{get_trait_str(tg)}]' for tg in hidden_dict.keys()])

    print(f'{head}：  {tg_str} [{tg_traits}] <{tg_shishen}>      {dz_str} [{dz_traits}] <{dz_shishen}>     {hidden_tgs}')

def demo() -> None:
  chart: BaziChart = BaziChart.create(
    birth_time=datetime(1984, 4, 3, 2, 1),
    gender=BaziGender.男,
    precision=BaziPrecision.DAY,
  )

  print_basic_info(chart)

if __name__ == '__main__':
  demo()
