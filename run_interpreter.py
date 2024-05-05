#!/usr/bin/env python3

import re
from pathlib import Path

from run_demos import get_basic_info
from src.Bazi import Bazi, BaziChart
from src.Common import ShishenDescription, TianganDescription
from src.Defines import Tiangan, Shishen
from src.Interpreter import Interpreter


def interpret(chart: BaziChart) -> str:
  s: str = '' # The string to return.
  j: BaziChart.JsonDict = chart.json

  bazi: Bazi = chart.bazi
  s += f'出生时间：{bazi.solar_birth_date}, {bazi.hour}:{bazi.minute}\n'
  s += f'性别：{bazi.gender}\n'

  def __gen_pillar_str(key: str) -> str:
    assert key in ['year', 'month', 'day', 'hour']
    __s: str = ''
    __s += f"天干{j['pillars'][key][0]}（{j['tiangan_traits'][key]}，" # type: ignore # mypy complains.
    __s += '日元' if key == 'day' else j['tiangan_shishens'][key] # type: ignore # mypy complains.
    __s += f"）。地支{j['pillars'][key][1]}（{j['dizhi_traits'][key]}，{j['dizhi_shishens'][key]}）。" # type: ignore # mypy complains.
    return __s
  
  s += '\n' + '-' * 60 + '\n'
  s += '年柱：' + __gen_pillar_str('year') + '\n'
  s += '月柱：' + __gen_pillar_str('month') + '\n'
  s += '日柱：' + __gen_pillar_str('day') + '\n'
  s += '时柱：' + __gen_pillar_str('hour') + '\n'

  day_master: Tiangan = chart.bazi.day_master
  day_master_desc: TianganDescription = Interpreter.interpret_tiangan(day_master)

  s += '\n' + '-' * 60 + '\n'
  s += f"日主：{j['pillars']['day'][0]}，为{j['tiangan_traits']['day']}。\n\n"
  s += '解读：' + ''.join(day_master_desc['general']) + '\n\n'
  s += '日主的个性：' + ''.join(day_master_desc['personality']) + '\n\n'

  shishens: dict[Shishen, int] = { ss : 0 for ss in Shishen }
  for pillar_shishens in chart.shishens:
    if pillar_shishens.tiangan is not None:
      shishens[pillar_shishens.tiangan] += 1
    shishens[pillar_shishens.dizhi] += 1
  
  for ss in shishens:
    count: int = shishens[ss]
    if count == 0:
      continue
    
    ratio: float = count / sum(shishens.values())
    desc: ShishenDescription = Interpreter.interpret_shishen(ss)

    s += '\n' + '-' * 60 + '\n'
    s += f'原局中，{ss}有{count}个，占比{ratio:.2%}。\n\n'
    s += '解读：' + ''.join(desc['general']) + '\n\n'
    s += f'{ss}代表的特点：' + ''.join(desc['in_good_status']) + '\n\n'
    s += f'当{ss}状态不好时，可能会有以下特点：' + ''.join(desc['in_bad_status']) + '\n\n'
    s += f'{ss}的恋爱/交友观：' + ''.join(desc['relationship']) + '\n\n'

  return s


def save_knowledge_base() -> None:
  tg_dir_path: Path = Path(__file__).parent / 'output_data'  / 'knowledge_base' / 'tiangan'
  if not tg_dir_path.exists():
    tg_dir_path.mkdir(parents=True)

  for tg in Tiangan:
    tg_desc: TianganDescription = Interpreter.interpret_tiangan(tg)
    with open(tg_dir_path / f'{tg}.txt', 'w', encoding='utf-8') as f:
      f.write('天干基本解读：\n')
      f.write('\n'.join(tg_desc['general']))
      f.write('\n\n')

      f.write('天干代表的个性：\n')
      f.write('\n'.join(tg_desc['personality']))
      f.write('\n\n')

  ss_dir_path: Path = Path(__file__).parent / 'output_data' / 'knowledge_base' / 'shishen'
  if not ss_dir_path.exists():
    ss_dir_path.mkdir(parents=True)

  for ss in Shishen:
    ss_desc: ShishenDescription = Interpreter.interpret_shishen(ss)
    with open(ss_dir_path / f'{ss}.txt', 'w', encoding='utf-8') as f:
      f.write(f'{ss}基本解读：\n')
      f.write('\n'.join(ss_desc['general']))
      f.write('\n\n')

      f.write(f'{ss}能量状态佳时所代表的特点：\n')
      f.write('\n'.join(ss_desc['in_good_status']))
      f.write('\n\n')

      f.write(f'{ss}能量状态不佳时所代表的特点：\n')
      f.write('\n'.join(ss_desc['in_bad_status']))
      f.write('\n\n')

      f.write(f'{ss}的恋爱/交友观：\n')
      f.write('\n'.join(ss_desc['relationship']))
      f.write('\n\n')


def save_chart_examples(count: int = 50) -> None:
  dir_path: Path = Path(__file__).parent / 'output_data' / 'interpretation_examples'
  if not dir_path.exists():
    dir_path.mkdir(parents=True)

  for i in range(count):
    chart: BaziChart = BaziChart.random()
    info: str = get_basic_info(chart)
    interpretation: str = interpret(chart)

    # `info` is a colored text. Remove its color control ascii codes.
    info = re.sub(r'\x1b\[[0-9;]*m', '', info)

    with open(dir_path / f'{i}.txt', 'w', encoding='utf-8') as f:
      f.write(info)
      f.write('\n\n')
      f.write('=' * 60 + '\n\n')
      f.write(interpretation)


if __name__ == '__main__':
  chart: BaziChart = BaziChart.random()
  info: str = get_basic_info(chart)
  interpretation: str = interpret(chart)

  print(info)
  print('\n' + '=' * 60 + '\n' + interpretation)

  save_knowledge_base()
  save_chart_examples()
