#!/usr/bin/env python3

from pprint import pprint
from typing import Union

import colorama

from src.Bazi import Bazi
from src.Charts.BaziChart import BaziChart
from src.Defines import Tiangan, Dizhi, Wuxing, Ganzhi, ShierZhangsheng
from src.Common import HiddenTianganDict
from src.Utils import BaziUtils


def colored_str(s: Union[Tiangan, Dizhi]) -> str:
  assert isinstance(s, (Tiangan, Dizhi))
  color_mapping_table: dict[Wuxing, str] = {
    Wuxing.火: colorama.Fore.RED,
    Wuxing.木: colorama.Fore.GREEN,
    Wuxing.金: colorama.Fore.YELLOW,
    Wuxing.水: colorama.Fore.BLUE,
    Wuxing.土: colorama.Fore.MAGENTA,
  }

  wx = BaziUtils.traits(s).wuxing
  return color_mapping_table[wx] + str(s) + colorama.Style.RESET_ALL

def get_trait_str(s: Union[Tiangan, Dizhi]) -> str:
  assert isinstance(s, (Tiangan, Dizhi))
  if isinstance(s, Dizhi):
    traits = BaziUtils.traits(s)
  else:
    traits = BaziUtils.traits(s)
  return f'{traits.yinyang}{traits.wuxing}'

def get_basic_info(chart: BaziChart) -> str:
  s: str = '\n' # The output string.
  bazi: Bazi = chart.bazi
  day_master_wx: Wuxing = BaziUtils.traits(bazi.day_master).wuxing
  s += f'日元{colored_str(bazi.day_master)}{day_master_wx}，{bazi.gender}，生于 {bazi.solar_date}\n\n'

  pillars: list[Ganzhi] = list(bazi.pillars)
  shishens: list[BaziChart.PillarShishens] = list(chart.shishens)
  hidden_tiangans: list[HiddenTianganDict] = list(chart.hidden_tiangans)
  nayins: list[str] = list(chart.nayins)
  zhangshengs: list[ShierZhangsheng] = list(chart.shier_zhangshengs)

  s += '     天干                  地支                  地支藏干\n'
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
      tg_shishen: str = str(shishens[idx].tiangan) # type: ignore # mypy complains.
    dz_shishen: str = str(shishens[idx].dizhi)

    hidden_dict: HiddenTianganDict = hidden_tiangans[idx]
    hidden_tgs: str = ' '.join([f'{colored_str(tg)} [{get_trait_str(tg)}]' for tg in hidden_dict.keys()])

    s += f'{head}：  {tg_str} [{tg_traits}] <{tg_shishen}>      {dz_str} [{dz_traits}] <{dz_shishen}>     {hidden_tgs}\n'
    s += f'  -- 纳音：{nayins[idx]}  -- 十二长生：{zhangshengs[idx]}\n'

  return s

def demo() -> None:
  chart: BaziChart = BaziChart(Bazi.random())
  info: str = get_basic_info(chart)
  print(info)
  print('\n' + 'chart json:')
  pprint(chart.json)

if __name__ == '__main__':
  demo()
