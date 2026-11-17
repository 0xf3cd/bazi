# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

from hashlib import sha256
from random import Random

import pytest

from api_contract import INPUT_CONTRACTS


pytest.register_assert_rewrite('cli_runner', 'matching_samples', 'relationship_samples')


def pytest_configure(config: pytest.Config) -> None:
  config.addinivalue_line('markers', 'input_contract(owner, names): rejection tests for the named public inputs')
  config.addinivalue_line('markers', 'optimized: helper controls and representative tasks required under -O')


def pytest_addoption(parser: pytest.Parser) -> None:
  parser.addoption('--random-seed', type=int, default=236, help='Base seed for local random regression inputs and collection cases.')
  parser.addoption('--input-contracts', action='store_true', help='Run the complete public-input selection under python -O.')


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
  expected = {f'{owner}.{name}' for owner, names in INPUT_CONTRACTS.items() for name in names.split()}
  found: set[str] = set()
  selected: list[pytest.Item] = []
  deselected: list[pytest.Item] = []
  for item in items:
    contracts: set[str] = set()
    for marker in item.iter_markers('input_contract'):
      owner, names = marker.args
      contracts.update(f'{owner}.{name}' for name in names.split())
    if unknown := contracts - expected:
      raise pytest.UsageError(f'{item.nodeid}: unknown input contracts: {sorted(unknown)}')
    found.update(contracts)
    (selected if contracts or item.get_closest_marker('optimized') else deselected).append(item)
  if config.getoption('--input-contracts'):
    if __debug__:
      raise pytest.UsageError('--input-contracts requires python -O')
    if missing := expected - found:
      raise pytest.UsageError(f'Input contracts without rejection tests: {sorted(missing)}')
    config.hook.pytest_deselected(items=deselected)
    items[:] = selected


def pytest_report_header(config: pytest.Config) -> str:
  return f'random regression base seed: {config.getoption("--random-seed")}'


@pytest.fixture
def rng(request: pytest.FixtureRequest) -> Random:
  base: int = request.config.getoption('--random-seed')
  seed = int.from_bytes(sha256(f'{base}:{request.node.nodeid}'.encode()).digest()[:8], 'big')
  print(f'random regression base={base} effective={seed} nodeid={request.node.nodeid}')
  return Random(seed)


@pytest.fixture
def short_jie_window(monkeypatch: pytest.MonkeyPatch) -> None:
  # A shorter table exercises finite/empty dayun timelines without changing birth-date support.
  from bazi.calendar import utils
  from bazi.defines import Jieqi

  first, _ = utils.supported_jie_boundaries()
  last = utils.jieqi_moment(2100, Jieqi.大雪)
  monkeypatch.setattr(utils, 'supported_jie_boundaries', lambda: (first, last))
