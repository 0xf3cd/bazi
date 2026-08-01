# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_relation_discovery.py

'''
Contract negatives for `RelationDiscovery`. Positive behaviors are covered by the
`discover`-family tests in `test_tiangan_utils.py` / `test_dizhi_utils.py`.
'''

import pytest

from src.defines import Tiangan, Dizhi
from src.utils import tiangan_utils, dizhi_utils
from src.utils.tiangan_utils import TianganRelationDiscovery


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
