#!/usr/bin/env python3

from run_demo import get_basic_info, colored_str

from src.bazi_chart import BaziChart
from src.transits import TransitOptions
from src.analyzer.relationship import RelationshipAnalyzer, ShenshaAnalysis


def shensha_strs(shensha: ShenshaAnalysis) -> list[str]:
  str_list: list[str] = []
  if len(dz_fs := shensha['taohua']) > 0:
    str_list.append(f'桃花：{", ".join(map(colored_str, dz_fs))}')
  if len(dz_fs := shensha['hongluan']) > 0:
    str_list.append(f'红鸾：{", ".join(map(colored_str, dz_fs))}')
  if len(dz_fs := shensha['hongyan']) > 0:
    str_list.append(f'红艳：{", ".join(map(colored_str, dz_fs))}')
  if len(dz_fs := shensha['tianxi']) > 0:
    str_list.append(f'天喜：{", ".join(map(colored_str, dz_fs))}')
  if len(dz_fs := shensha['yima']) > 0:
    str_list.append(f'驿马：{", ".join(map(colored_str, dz_fs))}')
  return str_list


if __name__ == '__main__':
  chart = BaziChart.random()
  analyzer = RelationshipAnalyzer(chart)

  print(get_basic_info(chart))
  print('\n' + '-' * 60 + '\n')

  house = chart.house_of_relationship
  stars = chart.relationship_stars
  star_strs = [colored_str(stars.tiangan), *map(colored_str, stars.dizhi)]
  print(f'夫妻宫：{colored_str(house)}')
  print(f'配偶星：{", ".join(star_strs)}')

  print('\n' + '-' * 60 + '\n')

  shensha_str_list = shensha_strs(analyzer.at_birth.shensha)
  if len(shensha_str_list) == 0:
    print('原局无桃花、红艳、红鸾、天喜、驿马星')
  else:
    print('原局神煞：')
    print('\n'.join(shensha_str_list))

  print('\n' + '-' * 60 + '\n')

  # The birth-side anchor is `ganzhi_year` (precision-attributed), the same source
  # `TransitDatabase.support` bounds liunian by -- a relative range can never fall
  # below it, which an absolute range would for charts born after its first year.
  start_gz_year = chart.bazi.ganzhi_year + 20
  print(f'流年神煞（{start_gz_year} 起十年）：')
  for gz_year in range(start_gz_year, start_gz_year + 10):
    year_strs = shensha_strs(analyzer.transits.shensha(gz_year, TransitOptions.LIUNIAN))
    if len(year_strs) == 0:
      print(f'{gz_year}：无')
    else:
      print(f'{gz_year}：')
      print('\n'.join(f'  {s}' for s in year_strs))
