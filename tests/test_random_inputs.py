# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import inspect
import os
import random
import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from typing import cast, get_type_hints
from unittest.mock import Mock

import pytest

from bazi.bazi import Bazi, 八字
from bazi.bazi_chart import BaziChart, 命盘
from bazi.analyzer.relationship import RelationshipAnalyzer
from bazi.transit_chart import TransitChart
from bazi import cli


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
def test_rng_binds_seed_without_global_state(
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


@pytest.mark.parametrize('task', ['demo', 'relationship'])
@pytest.mark.parametrize('seed', [0, 42, 236])
@pytest.mark.parametrize('optimized', [False, True])
def test_runner_seed_binds_birth_gender(task: str, seed: int, optimized: bool) -> None:
  root = Path(__file__).resolve().parents[1]
  expected = Bazi.random(rng=random.Random(seed))
  outputs = []
  for hash_seed in ('0', '1'):
    result = subprocess.run(
      [sys.executable, *(['-O'] if optimized else []), '-c',
       'from bazi.cli import main; raise SystemExit(main())', task, '--seed', str(seed)],
      cwd=root,
      env={**os.environ, 'PYTHONHASHSEED': hash_seed},
      capture_output=True,
      text=True,
      encoding='utf-8',
      timeout=45,
      check=True,
    )
    assert result.stdout.startswith(f'random seed: {seed}\n')
    assert f'出生时刻：{expected.solar_datetime.isoformat()}\n' in result.stdout
    assert f'，{expected.gender}，' in result.stdout
    outputs.append(result.stdout)
  assert outputs[0] == outputs[1]


@pytest.mark.parametrize('runner', ['demo', 'relationship'])
@pytest.mark.parametrize('sign', [-1, 1])
def test_runner_binds_consumers_to_seeded_chart(
  monkeypatch: pytest.MonkeyPatch, rng: random.Random, runner: str, sign: int,
) -> None:
  seed = sign * rng.getrandbits(64)
  expected = Bazi.random(rng=random.Random(seed))
  print(f'runner={runner} seed={seed}')
  state = random.getstate()
  basic = Mock(wraps=cli._get_basic_info)
  monkeypatch.setattr(cli, '_get_basic_info', basic)
  observed: list[BaziChart] = []
  if runner == 'demo':
    transit = Mock(wraps=cli._get_transit_info)
    monkeypatch.setattr(cli, '_get_transit_info', transit)
    assert cli.main(['demo', '--seed', str(seed)]) == 0
    for call in transit.call_args_list:
      chart = call.args[0]
      assert isinstance(chart, BaziChart)
      observed.append(chart)
  else:
    analyzer_init = RelationshipAnalyzer.__init__
    transit_init = TransitChart.__init__

    def observe_analyzer(self: RelationshipAnalyzer, chart: BaziChart) -> None:
      observed.append(chart)
      analyzer_init(self, chart)

    def observe_transit(self: TransitChart, chart: BaziChart) -> None:
      observed.append(chart)
      transit_init(self, chart)

    def observed_property(name: str) -> property:
      descriptor = inspect.getattr_static(BaziChart, name)

      def read(chart: BaziChart) -> object:
        observed.append(chart)
        return cast(object, descriptor.__get__(chart, BaziChart))

      return property(read)

    monkeypatch.setattr(RelationshipAnalyzer, '__init__', observe_analyzer)
    monkeypatch.setattr(TransitChart, '__init__', observe_transit)
    monkeypatch.setattr(BaziChart, 'house_of_relationship', observed_property('house_of_relationship'))
    monkeypatch.setattr(BaziChart, 'relationship_stars', observed_property('relationship_stars'))
    monkeypatch.setattr(BaziChart, 'bazi', observed_property('bazi'))
    assert cli.main(['relationship', '--seed', str(seed)]) == 0
  assert observed and basic.call_args_list
  for call in basic.call_args_list:
    chart = call.args[0]
    assert isinstance(chart, BaziChart)
    observed.append(chart)
  receivers = {id(chart): chart for chart in observed}
  assert all(chart.bazi == expected for chart in receivers.values())
  assert len(receivers) == 1
  assert random.getstate() == state


@pytest.mark.parametrize('task', ['demo', 'relationship', 'chart'])
@pytest.mark.parametrize('optimized', [False, True])
def test_runner_auto_seed_is_replayable(tmp_path: Path, task: str, optimized: bool) -> None:
  root = Path(__file__).resolve().parents[1]
  command = [sys.executable, *(['-O'] if optimized else []), '-c',
             'import sys; sys.path.insert(0, sys.argv.pop(1)); from bazi.cli import main; raise SystemExit(main())',
             str(root), task]
  first = subprocess.run(
    command,
    cwd=tmp_path,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=True,
  )
  seed_line = first.stdout.splitlines()[0]
  assert seed_line.startswith('random seed: ')
  seed = int(seed_line.removeprefix('random seed: '))
  replay = subprocess.run(
    [*command, '--seed', str(seed)],
    cwd=tmp_path,
    capture_output=True,
    text=True,
    encoding='utf-8',
    timeout=45,
    check=True,
  )
  assert replay.stdout == first.stdout
  assert list(tmp_path.iterdir()) == []
