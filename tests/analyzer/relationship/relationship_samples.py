# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# relationship_samples.py

# Helpers shared by the relationship-analyzer tests in this directory: gong projection, discovery
# equality and the year-transit builders.
# Imported as a bare sibling module: the suite has no `__init__.py`, so pytest puts this directory on
# `sys.path`, and `from tests.<package>...` would be shadowed by a stray installed `tests` package
# (see the NOTE in `tests/calendar/test_celestial_tables.py`).

import random
from collections.abc import Callable

from bazi.defines import DizhiRelation
from bazi.utils import tiangan_utils, dizhi_utils
from bazi.transit_chart import TransitChart
from bazi.transits import TransitSet


GONG_RELATIONS = (DizhiRelation.拱合, DizhiRelation.拱会)


def project_gong(
  discovery: dizhi_utils.GanzhiRelationDiscovery,
  predicate: Callable[[dizhi_utils.GanzhiRelationCombo], bool],
) -> dizhi_utils.DizhiRelationDiscovery:
  return dizhi_utils.GanzhiRelationDiscovery({
    relation : tuple(combo for combo in discovery.get(relation, ()) if predicate(combo))
    for relation in GONG_RELATIONS
  }).to_dizhi_discovery()


'''Operand type of `discoveries_equal`: either relation-discovery flavor.'''
DiscoveryType = tiangan_utils.TianganRelationDiscovery | dizhi_utils.DizhiRelationDiscovery


def discoveries_equal(discovery1: DiscoveryType, discovery2: DiscoveryType) -> bool:
  if type(discovery1) is not type(discovery2):
    print(f'Different discovery types: {type(discovery1).__name__}, {type(discovery2).__name__}')
    return False
  if set(discovery1.keys()) != set(discovery2.keys()):
    print(f'Left-only relations: {discovery1.keys() - discovery2.keys()}')
    print(f'Right-only relations: {discovery2.keys() - discovery1.keys()}')
    return False
  for key, combos in discovery1.items():
    left = set(combos)
    right = set(discovery2[key])  # type: ignore
    if left != right:
      print(f'{key}: left-only combos={left - right}, right-only combos={right - left}')
      return False
  return True


def at_year(transit_chart: TransitChart, gz_year: int) -> TransitSet:
  transits = transit_chart.at_year(gz_year)
  assert transits is not None
  return transits


def random_year_transits(transit_chart: TransitChart, gz_year: int, rng: random.Random) -> TransitSet:
  full_transits = at_year(transit_chart, gz_year)
  available = tuple(full_transits)
  selected = rng.sample(available, rng.randint(1, len(available)))
  return full_transits.select(*selected)
