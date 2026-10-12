# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import inspect
import os
import random
import runpy
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
import run_demo


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


@pytest.mark.parametrize('runner', ['demo', 'relationship'])
@pytest.mark.parametrize('sign', [-1, 1])
def test_runner_binds_every_consumer_to_its_seeded_chart(
  monkeypatch: pytest.MonkeyPatch, rng: random.Random, runner: str, sign: int,
) -> None:
  seed = sign * rng.getrandbits(64)
  expected = BaziChart(Bazi.random(rng=random.Random(seed))).json
  print(f'runner={runner} seed={seed}')
  basic = Mock(wraps=run_demo.get_basic_info)
  monkeypatch.setattr(run_demo, 'get_basic_info', basic)
  observed: list[BaziChart] = []
  if runner == 'demo':
    transit = Mock(wraps=run_demo.get_transit_info)
    printer = Mock(wraps=run_demo.pprint)
    monkeypatch.setattr(run_demo, 'get_transit_info', transit)
    monkeypatch.setattr(run_demo, 'pprint', printer)
    run_demo.demo(seed)
    for call in transit.call_args_list:
      chart = call.args[0]
      assert isinstance(chart, BaziChart)
      observed.append(chart)
    printer.assert_called_once_with(expected)
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
    monkeypatch.setattr(sys, 'argv', ['run_relationship_analyzer.py', '--seed', str(seed)])
    runpy.run_path(
      str(Path(__file__).resolve().parents[1] / 'run_relationship_analyzer.py'),
      run_name='__main__',
    )
  assert observed and basic.call_args_list
  for call in basic.call_args_list:
    chart = call.args[0]
    assert isinstance(chart, BaziChart)
    observed.append(chart)
  receivers = {id(chart): chart for chart in observed}
  assert all(chart.json == expected for chart in receivers.values())


@pytest.mark.parametrize('script', ['run_demo.py', 'run_relationship_analyzer.py', 'run_interpreter.py'])
def test_runner_automatic_seed_is_printed_and_replayable(tmp_path: Path, script: str) -> None:
  path = Path(__file__).resolve().parents[1] / script
  command = [sys.executable, str(path)]
  first = subprocess.run(
    command,
    cwd=tmp_path,
    capture_output=True,
    text=True,
    encoding='utf-8',
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
    check=True,
  )
  assert replay.stdout == first.stdout
  assert list(tmp_path.iterdir()) == []
