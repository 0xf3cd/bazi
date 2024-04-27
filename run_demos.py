#!/usr/bin/env python3

import random
from pprint import pprint
from datetime import datetime
from typing import Union

import colorama

from src import (
  Tiangan, Dizhi, Wuxing, Ganzhi, ShierZhangsheng,
  Bazi, BaziChart, BaziGender, BaziPrecision, BaziUtils,
  HiddenTianganDict
)

def get_wuxing(s: Union[Tiangan, Dizhi]) -> Wuxing:
  assert isinstance(s, (Tiangan, Dizhi))
  if isinstance(s, Dizhi):
    return BaziUtils.get_dizhi_traits(s).wuxing
  else:
    return BaziUtils.get_tiangan_traits(s).wuxing

def colored_str(s: Union[Tiangan, Dizhi]) -> str:
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

def get_trait_str(s: Union[Tiangan, Dizhi]) -> str:
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
  hidden_tiangans: list[HiddenTianganDict] = list(chart.hidden_tiangans)
  nayins: list[str] = list(chart.nayins)
  zhangshengs: list[ShierZhangsheng] = list(chart.shier_zhangshengs)

  print('     天干                  地支                  地支藏干')
  for idx, head in enumerate(['年', '月', '日', '时']):
    tg: Tiangan = pillars[idx].tiangan
    dz: Dizhi = pillars[idx].dizhi

    tg_str: str = colored_str(tg)
    dz_str: str = colored_str(dz)

    tg_traits: str = get_trait_str(tg)
    dz_traits: str = get_trait_str(dz)

    if idx == 2:
      tg_shishen: str = colorama.Back.LIGHTBLUE_EX + colorama.Fore.BLACK + '日主' + colorama.Style.RESET_ALL
    else:
      assert shishens[idx].tiangan is not None
      tg_shishen: str = str(shishens[idx].tiangan)
    dz_shishen: str = str(shishens[idx].dizhi)

    hidden_dict: HiddenTianganDict = hidden_tiangans[idx]
    hidden_tgs: str = ' '.join([f'{colored_str(tg)} [{get_trait_str(tg)}]' for tg in hidden_dict.keys()])

    print(f'{head}：  {tg_str} [{tg_traits}] <{tg_shishen}>      {dz_str} [{dz_traits}] <{dz_shishen}>     {hidden_tgs}')
    print(f'  -- 纳音：{nayins[idx]}  -- 十二长生：{zhangshengs[idx]}')

def demo() -> None:
  chart: BaziChart = BaziChart.create(
    birth_time=datetime(
      year=random.randint(1902, 2098),
      month=random.randint(1, 12),
      day=random.randint(1, 28),
      hour=random.randint(0, 23),
      minute=random.randint(0, 59),
    ),
    gender=random.choice(list(BaziGender)),
    precision=BaziPrecision.DAY,
  )

  print_basic_info(chart)

  print('\n' + 'chart json:')
  pprint(chart.json)

if __name__ == '__main__':
  demo()
