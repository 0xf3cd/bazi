#!/usr/bin/env python3

from run_demo import get_basic_info, colored_str

from src.bazi_chart import BaziChart
from src.transits import TransitOptions
from src.analyzer.relationship import RelationshipAnalyzer, ShenshaAnalysis


def shensha_strs(shensha: ShenshaAnalysis) -> list[str]:
  # TypedDict access needs literal keys under mypy, so the table pairs labels
  # with already-fetched fields instead of looping over key strings.
  named = [
    ('桃花', shensha['taohua']),
    ('红鸾', shensha['hongluan']),
    ('红艳', shensha['hongyan']),
    ('天喜', shensha['tianxi']),
    ('驿马', shensha['yima']),
  ]
  return [f'{label}：{", ".join(map(colored_str, dz_fs))}' for label, dz_fs in named if dz_fs]


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
  transits_analysis = analyzer.transits
  start_gz_year = chart.bazi.ganzhi_year + 20
  print(f'流年神煞（{start_gz_year} 起十年）：')
  for gz_year in range(start_gz_year, start_gz_year + 10):
    year_strs = shensha_strs(transits_analysis.shensha(gz_year, TransitOptions.LIUNIAN))
    if len(year_strs) == 0:
      print(f'{gz_year}：无')
    else:
      print(f'{gz_year}：')
      print('\n'.join(f'  {s}' for s in year_strs))
