#!/usr/bin/env python3

from run_demo import get_basic_info

from src.BaziChart import BaziChart
from src.Transits import TransitOptions, TransitDatabase
from src.Analyzer.Relationship import RelationshipAnalyzer, ShenshaAnalysis


def shensha_strs(shensha: ShenshaAnalysis) -> list[str]:
  str_list: list[str] = []
  if len(dz_fs := shensha['taohua']) > 0:
    str_list.append(f'桃花：{", ".join(str(x) for x in dz_fs)}')
  if len(dz_fs := shensha['hongluan']) > 0:
    str_list.append(f'红鸾：{", ".join(str(x) for x in dz_fs)}')
  if len(dz_fs := shensha['hongyan']) > 0:
    str_list.append(f'红艳：{", ".join(str(x) for x in dz_fs)}')
  if len(dz_fs := shensha['tianxi']) > 0:
    str_list.append(f'天喜：{", ".join(str(x) for x in dz_fs)}')
  return str_list


if __name__ == '__main__':
  chart = BaziChart.random()
  bazi = chart.bazi
  analyzer = RelationshipAnalyzer(chart)

  print(get_basic_info(chart))
  print('\n' + '-' * 60 + '\n')

  shensha_str_list = shensha_strs(analyzer.at_birth.shensha)
  if len(shensha_str_list) == 0:
    print('原局无桃花、红艳、红鸾、天喜星')
  else:
    print('原局神煞：')
    print('\n'.join(shensha_str_list))

  print('\n' + '-' * 60 + '\n')

  gz_year = chart.bazi.ganzhi_date.year + 20
  liunian_shensha_str_list = shensha_strs(analyzer.transits.shensha(gz_year, TransitOptions.LIUNIAN))
  if len(liunian_shensha_str_list) == 0:
    print(f'{gz_year} 流年无桃花、红艳、红鸾、天喜星')
  else:
    print(f'{gz_year} 流年神煞：')
    print('\n'.join(liunian_shensha_str_list))
