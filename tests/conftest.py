# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from hashlib import sha256
from random import Random

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
  parser.addoption('--random-seed', type=int, default=236, help='Base seed for local random regression inputs and collection cases.')


def pytest_report_header(config: pytest.Config) -> str:
  return f'random regression base seed: {config.getoption("--random-seed")}'


@pytest.fixture
def rng(request: pytest.FixtureRequest) -> Random:
  base: int = request.config.getoption('--random-seed')
  seed = int.from_bytes(sha256(f'{base}:{request.node.nodeid}'.encode()).digest()[:8], 'big')
  print(f'random regression base={base} effective={seed} nodeid={request.node.nodeid}')
  return Random(seed)
