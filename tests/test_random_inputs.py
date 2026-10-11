# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import inspect
import os
import random
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import get_type_hints

import pytest

from bazi.bazi import Bazi, 八字
from bazi.bazi_chart import BaziChart, 命盘


@pytest.mark.parametrize('factory', [Bazi, BaziChart])
def test_random_factory_runtime_annotations(factory: type[Bazi] | type[BaziChart]) -> None:
  assert 八字 is Bazi and 命盘 is BaziChart
  hints = get_type_hints(factory.random)
  assert hints['rng'] == random.Random | None
  assert hints['return'] is factory
  parameter = inspect.signature(factory.random).parameters['rng']
  assert parameter.annotation == random.Random | None
  assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
  assert factory.random.__annotations__['rng'] == random.Random | None


@pytest.mark.parametrize('_case', [0, 1])
def test_rng_binds_printed_seed_to_real_state_without_touching_global_state(
  request: pytest.FixtureRequest, capsys: pytest.CaptureFixture[str], _case: int,
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


@pytest.mark.parametrize('script', ['run_demo.py', 'run_relationship_analyzer.py'])
@pytest.mark.parametrize('seed', [0, 42, 236])
def test_runner_seed_binds_birth_and_gender_across_processes(script: str, seed: int) -> None:
  root = Path(__file__).resolve().parents[1]
  expected = Bazi.random(rng=random.Random(seed))
  outputs = []
  for hash_seed in ('0', '1'):
    result = subprocess.run(
      [sys.executable, str(root / script), '--seed', str(seed)],
      cwd=root,
      env={**os.environ, 'PYTHONHASHSEED': hash_seed},
      capture_output=True,
      text=True,
      encoding='utf-8',
      check=True,
    )
    assert result.stdout.startswith(f'random seed: {seed}\n')
    assert f'出生时刻：{expected.solar_datetime.isoformat()}\n' in result.stdout
    assert f'，{expected.gender}，' in result.stdout
    outputs.append(result.stdout)
  assert outputs[0] == outputs[1]
