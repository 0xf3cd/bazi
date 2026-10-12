# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relation_discovery.py

import os
import subprocess
import sys
from pathlib import Path

import pytest

from bazi.defines import Dizhi, Tiangan, DizhiRelation, TianganRelation
from bazi.utils import tiangan_utils, dizhi_utils
from bazi.utils.dizhi_utils import DizhiRelationDiscovery
from bazi.utils.tiangan_utils import TianganRelationDiscovery


def test_filter_negative() -> None:
  discovery: TianganRelationDiscovery = tiangan_utils.discover([Tiangan.甲, Tiangan.己])
  with pytest.raises(TypeError):
    discovery.filter('not a callable') # type: ignore


def test_merge_negative() -> None:
  discovery: TianganRelationDiscovery = tiangan_utils.discover([Tiangan.甲, Tiangan.己])
  with pytest.raises(TypeError):
    discovery.merge(dizhi_utils.discover([Dizhi.子, Dizhi.丑])) # type: ignore


def test_mutual_only_negative() -> None:
  discovery: TianganRelationDiscovery = tiangan_utils.discover([Tiangan.甲, Tiangan.己])
  with pytest.raises(TypeError):
    discovery.mutual_only([Tiangan.甲], {Tiangan.己}) # type: ignore
  with pytest.raises(TypeError):
    discovery.mutual_only({Tiangan.甲}, [Tiangan.己]) # type: ignore


@pytest.mark.parametrize('tiangan', [False, True])
def test_merge_first_occurrence_order(tiangan: bool) -> None:
  if tiangan:
    a, b, c = (frozenset(pair) for pair in ((Tiangan.甲, Tiangan.庚), (Tiangan.乙, Tiangan.辛), (Tiangan.丙, Tiangan.壬)))
    left = TianganRelationDiscovery({TianganRelation.冲: (b, a, b), TianganRelation.合: ()})
    right = TianganRelationDiscovery({TianganRelation.冲: (a, c, c), TianganRelation.克: (c,)})
    merged = left.merge(right)
    assert tuple(merged) == (TianganRelation.冲, TianganRelation.合, TianganRelation.克)
    assert merged[TianganRelation.冲] == (b, a, c)
    assert merged[TianganRelation.合] == ()
    assert right.merge(left)[TianganRelation.冲] == (a, c, b)
  else:
    x, y, z = (frozenset(pair) for pair in ((Dizhi.子, Dizhi.午), (Dizhi.丑, Dizhi.未), (Dizhi.寅, Dizhi.申)))
    dz_left = DizhiRelationDiscovery({DizhiRelation.冲: (y, x, y), DizhiRelation.六合: ()})
    dz_right = DizhiRelationDiscovery({DizhiRelation.冲: (x, z, z), DizhiRelation.克: (z,)})
    dz_merged = dz_left.merge(dz_right)
    assert tuple(dz_merged) == (DizhiRelation.冲, DizhiRelation.六合, DizhiRelation.克)
    assert dz_merged[DizhiRelation.冲] == (y, x, z)
    assert dz_merged[DizhiRelation.六合] == ()
    assert dz_right.merge(dz_left)[DizhiRelation.冲] == (x, z, y)


_DISCOVERY_SCRIPT = '''
import json
from bazi.defines import Tiangan, Dizhi, Ganzhi
from bazi.rules import DizhiRules, DizhiRelationDefinitions
from bazi.utils import tiangan_utils, dizhi_utils
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.analyzer.relationship import RelationshipAnalyzer, TransitAnalysis
from bazi.transits import TransitSet

def encode(discovery):
  return [(rel.name, [sorted(item.index for item in combo) for combo in combos])
          for rel, combos in discovery.items()]

results = {}
for module, members in ((tiangan_utils, list(Tiangan)), (dizhi_utils, list(Dizhi) * 2)):
  left = module.discover(members)
  right = module.discover_mutual(members[:5], members[3:])
  results[module.__name__] = [encode(left), encode(right), encode(left.merge(right))]
for anhe in DizhiRules.AnheDef:
  for xing in DizhiRules.XingDef:
    definitions = DizhiRelationDefinitions(anhe_def=anhe, xing_def=xing)
    results[f'{anhe.name}/{xing.name}'] = encode(dizhi_utils.discover(list(Dizhi) * 2, definitions=definitions))
analyzer = RelationshipAnalyzer(BaziChart(Bazi.create('1980-01-12 20:00', 'male')))
transits = TransitSet(dayun=Ganzhi.from_str('甲寅'), liunian=Ganzhi.from_str('甲午'), liuyue=Ganzhi.from_str('甲辰'))
results['birth_house'] = encode(analyzer.at_birth.house_relations)
results['birth_star'] = [encode(analyzer.at_birth.star_relations.tiangan), encode(analyzer.at_birth.star_relations.dizhi)]
results['transit_house'] = encode(analyzer.transits.house_relations(transits))
for level in (TransitAnalysis.Level.TRANSITS_ONLY, TransitAnalysis.Level.MUTUAL, TransitAnalysis.Level.ALL):
  result = analyzer.transits.star_relations(transits, level=level)
  results[level.name] = [encode(result.tiangan), encode(result.dizhi)]
print(json.dumps(results, ensure_ascii=False))
'''


def test_real_discovery_order_across_hash_seeds() -> None:
  outputs = []
  for seed in (1, 2, 3):
    result = subprocess.run(
      [sys.executable, '-B', '-c', _DISCOVERY_SCRIPT],
      cwd=Path(__file__).resolve().parents[2],
      env={**os.environ, 'PYTHONHASHSEED': str(seed)},
      capture_output=True,
      text=True,
      check=True,
      timeout=30,
    )
    outputs.append(result.stdout)
  assert outputs[0] == outputs[1] == outputs[2]
