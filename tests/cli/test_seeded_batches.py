# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import random
from datetime import datetime

import pytest

from bazi import cli
from bazi.bazi import Bazi, BaziGender
from bazi.bazi_chart import BaziChart


def test_batch_generation_interleaves_rendering(
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  events: list[str] = []
  bazi = Bazi.create('2000-01-01 12:00', 'male')

  def generate(*, rng: object) -> Bazi:
    events.append('generate')
    return bazi

  def render(chart: BaziChart, **kwargs: object) -> str:
    events.append('render')
    return 'chart'

  monkeypatch.setattr(Bazi, 'random', staticmethod(generate))
  monkeypatch.setattr(cli, '_chart_text', render)
  assert cli.main(['chart', '--seed', '42', '--count', '3']) == 0
  assert events == ['generate', 'render', 'generate', 'render', 'generate', 'render']
  assert capsys.readouterr().out == 'random seed: 42\nchart\nchart\nchart\n'


@pytest.mark.parametrize('seed', [0, 42, -17])
def test_seed_keeps_birth_draw_order(monkeypatch: pytest.MonkeyPatch, seed: int) -> None:
  state = random.getstate()
  source = random.Random(seed)
  expected = [
    Bazi.create(
      datetime(
        source.randint(1902, 2080),
        source.randint(1, 12),
        source.randint(1, 28),
        source.randint(0, 23),
        source.randint(0, 59),
      ),
      source.choice(list(BaziGender)),
    )
    for _ in range(2)
  ]
  actual: list[Bazi] = []
  def render(chart: BaziChart, **kwargs: object) -> str:
    actual.append(chart.bazi)
    return f'birth={chart.bazi.solar_datetime.isoformat()} gender={chart.bazi.gender}'
  monkeypatch.setattr(cli, '_chart_text', render)
  assert cli.main(['chart', '--seed', str(seed), '--count', '2']) == 0
  assert actual == expected
  assert random.getstate() == state
