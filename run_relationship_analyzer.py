#!/usr/bin/env python3

from run_demo import get_basic_info, colored_str

from src.bazi_chart import BaziChart
from src.defines import Dizhi
from src.transit_chart import TransitChart
from src.transits import TransitKind
from src.analyzer.relationship import RelationshipAnalyzer, ShenshaAnalysis, AtBirthShenshaAnalysis


def _named_shensha(shensha: ShenshaAnalysis) -> tuple[tuple[str, frozenset[Dizhi]], ...]:
  # TypedDict access needs literal keys under mypy, so the table pairs labels
  # with already-fetched fields instead of looping over key strings.
  return (
    ('桃花', shensha['taohua']),
    ('红鸾', shensha['hongluan']),
    ('红艳', shensha['hongyan']),
    ('天喜', shensha['tianxi']),
    ('驿马', shensha['yima']),
    ('华盖', shensha['huagai']),
    ('羊刃', shensha['yangren']),
    ('飞刃', shensha['feiren']),
    ('天乙贵人', shensha['tianyi']),
    ('将星', shensha['jiangxing']),
    ('灾煞', shensha['zaisha']),
    ('劫煞', shensha['jiesha']),
    ('亡神', shensha['wangshen']),
    ('孤辰', shensha['guchen']),
    ('寡宿', shensha['guasu']),
    ('禄神', shensha['lushen']),
    ('金舆', shensha['jinyu']),
  )


def shensha_strs(shensha: ShenshaAnalysis) -> list[str]:
  return [
    f'{label}：{", ".join(map(colored_str, dz_fs))}'
    for label, dz_fs in _named_shensha(shensha)
    if dz_fs
  ]


def at_birth_shensha_strs(shensha: AtBirthShenshaAnalysis) -> list[str]:
  result = shensha_strs(shensha)
  if (kuigang := shensha['kuigang']) is not None:
    result.append(f'魁罡：{colored_str(kuigang)}')
  if (tianshe := shensha['tianshe']) is not None:
    result.append(f'天赦：{colored_str(tianshe)}')
  return result


def _no_shensha_str(shensha: AtBirthShenshaAnalysis) -> str:
  labels = '、'.join(label for label, _ in _named_shensha(shensha))
  return f'原局无{labels}、魁罡、天赦'


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

  at_birth_shensha = analyzer.at_birth.shensha
  shensha_str_list = at_birth_shensha_strs(at_birth_shensha)
  if len(shensha_str_list) == 0:
    print(_no_shensha_str(at_birth_shensha))
  else:
    print('原局神煞：')
    print('\n'.join(shensha_str_list))

  print('\n' + '-' * 60 + '\n')

  transits_analysis = analyzer.transits
  transit_chart = TransitChart(chart)
  # Anchor the demo window on the chart's Ganzhi year; a fixed range could precede birth.
  start_gz_year = chart.bazi.ganzhi_year + 20
  print(f'流年神煞（{start_gz_year} 起十年）：')
  for gz_year in range(start_gz_year, start_gz_year + 10):
    year_transits = transit_chart.at_year(gz_year)
    assert year_transits is not None
    year_strs = shensha_strs(transits_analysis.shensha(
      year_transits.select(TransitKind.LIUNIAN)
    ))
    if len(year_strs) == 0:
      print(f'{gz_year}：无')
    else:
      print(f'{gz_year}：')
      print('\n'.join(f'  {s}' for s in year_strs))
