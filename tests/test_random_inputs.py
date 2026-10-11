# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import inspect
import random
from hashlib import sha256
from typing import get_type_hints

import pytest

from bazi.bazi import Bazi, 八字
from bazi.bazi_chart import BaziChart, 命盘


@pytest.mark.parametrize('factory', [Bazi, 八字, BaziChart, 命盘])
def test_random_factory_runtime_annotations(factory: type[Bazi] | type[BaziChart]) -> None:
  hints = get_type_hints(factory.random)
  assert hints['rng'] == random.Random | None
  assert hints['return'] is factory
  parameter = inspect.signature(factory.random).parameters['rng']
  assert parameter.annotation == random.Random | None
  assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
  assert factory.random.__annotations__['rng'] == random.Random | None


def test_rng_binds_printed_seed_to_real_state_without_touching_global_state(
  request: pytest.FixtureRequest, capsys: pytest.CaptureFixture[str],
) -> None:
  state = random.getstate()
  source = request.getfixturevalue('rng')
  base: int = request.config.getoption('--random-seed')
  effective = int.from_bytes(sha256(f'{base}:{request.node.nodeid}'.encode()).digest()[:8], 'big')
  assert type(source) is random.Random
  assert source.getstate() == random.Random(effective).getstate()
  assert random.getstate() == state
  assert capsys.readouterr().out == f'random regression base={base} effective={effective} nodeid={request.node.nodeid}\n'
  print(f'verified base={base} effective={effective} nodeid={request.node.nodeid}')
