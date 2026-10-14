#!/usr/bin/env python3

import argparse
from random import Random, SystemRandom
from typing import Final, cast
from collections.abc import Mapping

from run_demo import get_basic_info, colored_str

from bazi.bazi_chart import BaziChart
from bazi.common import frozendict
from bazi.defines import Dizhi, Ganzhi
from bazi.transit_chart import TransitChart
from bazi.transits import TransitKind
from bazi.analyzer.relationship import (
  RelationshipAnalyzer, ShenshaAnalysis, AtBirthShenshaAnalysis, SHENSHA_LABELS,
)


_WHOLE_PILLAR_SHENSHA_LABELS: Final[frozendict[str, str]] = frozendict({
  'kuigang': '魁罡',
  'tianshe': '天赦',
})


def _named_shensha(shensha: ShenshaAnalysis) -> tuple[tuple[str, frozenset[Dizhi]], ...]:
  # mypy 要求 TypedDict 用字面键，因此按普通映射读取，再依 SHENSHA_LABELS 注册序逐项展示。
  # 原局结果还有两个整柱神煞，不在此名册中，此处不读取。
  dizhis = cast(Mapping[str, frozenset[Dizhi]], shensha)
  return tuple((label, dizhis[name]) for name, label in SHENSHA_LABELS.items())


def shensha_strs(shensha: ShenshaAnalysis) -> list[str]:
  return [
    f'{label}：{", ".join(map(colored_str, sorted(dz_fs, key=lambda dz: dz.index)))}'
    for label, dz_fs in _named_shensha(shensha)
    if dz_fs
  ]


def at_birth_shensha_strs(shensha: AtBirthShenshaAnalysis) -> list[str]:
  result = shensha_strs(shensha)
  whole_pillars = cast(Mapping[str, Ganzhi | None], shensha)
  for name, label in _WHOLE_PILLAR_SHENSHA_LABELS.items():
    if (ganzhi := whole_pillars[name]) is not None:
      result.append(f'{label}：{colored_str(ganzhi)}')
  return result


def _no_shensha_str(shensha: AtBirthShenshaAnalysis) -> str:
  labels = tuple(label for label, _ in _named_shensha(shensha))
  return f'原局无{"、".join(labels + tuple(_WHOLE_PILLAR_SHENSHA_LABELS.values()))}'


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='展示随机命盘的亲密关系分析。')
  parser.add_argument('--seed', type=int, help='重放随机示例的种子。')
  seed = parser.parse_args().seed
  seed = SystemRandom().getrandbits(64) if seed is None else seed
  print(f'random seed: {seed}')
  chart = BaziChart.random(rng=Random(seed))
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
  # 固定年份范围可能早于出生。
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
