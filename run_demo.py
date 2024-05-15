#!/usr/bin/env python3

import colorama
import itertools

from pprint import pprint
from typing import Union, Iterable, Generator, TypeVar

from src.Bazi import Bazi
from src.BaziChart import BaziChart
from src.Defines import Tiangan, Dizhi, Wuxing, Ganzhi, ShierZhangsheng
from src.Common import HiddenTianganDict
from src.Utils.BaziUtils import traits, shishen, hidden_tiangans, nayin_str, shier_zhangsheng
from src.Calendar.HkoDataCalendarUtils import prev_jie, next_jie


T = TypeVar('T')
def batched(it: Iterable[T], n: int) -> Generator[tuple[T, ...], None, None]:
  '''My simple alternative to `itertools.batched` since it is not available before Python 3.12.'''
  assert n > 0
  it_list: list[T] = list(it)
  for i in range(0, len(it_list), n):
    yield tuple(it_list[i:i + n])


def colored_str(s: Union[Tiangan, Dizhi, Ganzhi]) -> str:
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


def traits_str(s: Union[Tiangan, Dizhi]) -> str:
  t = traits(s)
  return f'{t.yinyang}{t.wuxing}'


def hidden_tg_str(d: HiddenTianganDict, day_master: Tiangan) -> str:
  def f(tg: Tiangan) -> str:
    return f'{colored_str(tg)} [{traits_str(tg)}] <{shishen(day_master, tg).abbr}>'
  return ' '.join(f(tg) for tg in d.keys())


def get_basic_info(chart: BaziChart) -> str:
  s: str = '\n' # The output string.
  bazi: Bazi = chart.bazi
  day_master_wx: Wuxing = traits(bazi.day_master).wuxing
  s += f'日元{colored_str(bazi.day_master)}{day_master_wx}，{bazi.gender}，生于 {bazi.solar_date}\n\n'

  pillars: list[Ganzhi] = list(bazi.pillars)
  shishens: list[BaziChart.PillarShishens] = list(chart.shishen)
  hidden_tiangan: list[HiddenTianganDict] = list(chart.hidden_tiangan)
  nayin: list[str] = list(chart.nayin)
  zhangsheng: list[ShierZhangsheng] = list(chart.shier_zhangsheng)

  s += '     天干                  地支                  地支藏干\n'
  for idx, head in enumerate(['年', '月', '日', '时']):
    tg: Tiangan = pillars[idx].tiangan
    dz: Dizhi = pillars[idx].dizhi

    tg_shishen: str = str(shishens[idx].tiangan)
    if idx == 2:
      tg_shishen = colorama.Back.LIGHTBLUE_EX + colorama.Fore.BLACK + '日主' + colorama.Style.RESET_ALL

    tg_str: str = f'{colored_str(tg)} [{traits_str(tg)}] <{tg_shishen}>'
    dz_str: str = f'{colored_str(dz)} [{traits_str(dz)}] <{str(shishens[idx].dizhi)}>'
    hd_str: str = hidden_tg_str(hidden_tiangan[idx], bazi.day_master)

    s += f'{head}：  {tg_str}      {dz_str}     {hd_str}\n'
    s += f'  -- 纳音：{nayin[idx]}  -- 十二长生：{zhangsheng[idx]}\n'

  return s


def get_transit_info(chart: BaziChart) -> str:
  day_master: Tiangan = chart.bazi.day_master
  s: str = '\n' # The output string.

  jie_before = prev_jie(chart.bazi.solar_datetime)
  jie_after = next_jie(chart.bazi.solar_datetime)

  s += f'出生时刻前一节：{jie_before.jieqi} - {jie_before.moment.isoformat()}\n'
  s += f'出生时刻后一节：{jie_after.jieqi} - {jie_after.moment.isoformat()}\n'
  s += f'交运时间： {chart.dayun_start_moment.isoformat()}\n\n'

  s += '大运：            天干                 地支                 地支藏干\n'
  for start_gz_year, dayun in itertools.islice(chart.dayun, 10):
    tg, dz = dayun

    tg_str: str = f'{colored_str(tg)} [{traits_str(tg)}] <{shishen(day_master, tg)}>'
    dz_str: str = f'{colored_str(dz)} [{traits_str(dz)}] <{shishen(day_master, dz)}>'
    hd_str: str = hidden_tg_str(hidden_tiangans(dz), day_master)

    s += f'{start_gz_year}年 ～ {start_gz_year + 9}年： {tg_str}     {dz_str}    {hd_str}\n'
    s += f'               -- 纳音：{nayin_str(dayun)}  -- 十二长生：{shier_zhangsheng(day_master, dz)}\n\n'

  s += '小运：\n'
  for xy_batch in batched(chart.xiaoyun, 10):
    xy_batch_str: str = '  '.join(f'{xy.xusui}岁-{colored_str(xy.ganzhi)}' for xy in xy_batch)
    s += f'{xy_batch_str}\n'

  s += '\n流年：\n'
  for ln_batch in batched(itertools.islice(chart.liunian, 100), 10):
    ln_batch_str: str = '  '.join(f'{ln.ganzhi_year}-{colored_str(ln.ganzhi)}' for ln in ln_batch)
    s += f'{ln_batch_str}\n'

  return s


def demo() -> None:
  chart: BaziChart = BaziChart(Bazi.random())

  basic_info: str = get_basic_info(chart)
  print(basic_info)

  transit_info: str = get_transit_info(chart)
  print(transit_info)

  print('\n' + 'chart json:')
  pprint(chart.json)


if __name__ == '__main__':
  demo()
