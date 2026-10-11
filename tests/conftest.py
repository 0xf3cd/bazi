# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from random import Random

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
  parser.addoption('--random-seed', type=int, default=236, help='Seed for local random regression inputs.')


def pytest_report_header(config: pytest.Config) -> str:
  return f'random regression seed: {config.getoption("--random-seed")}'


@pytest.fixture
def rng(request: pytest.FixtureRequest) -> Random:
  seed: int = request.config.getoption('--random-seed')
  request.node.user_properties.append(('random_seed', seed))
  print(f'random regression seed: {seed}')
  return Random(seed)
