# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import pytest

from run_interpreter import interpret
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Shishen, Tiangan
from bazi.descriptions import ShishenDescription, TianganDescription
from bazi.interpreter import Interpreter


def test_interpret_suppresses_empty_description_headings(
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))

  def tiangan_description(_: Tiangan) -> TianganDescription:
    return {
      'general': ['日主解读。'],
      'personality': [],
    }

  def shishen_description(_: Shishen) -> ShishenDescription:
    return {
      'general': [],
      'in_good_status': ['状态良好。'],
      'in_bad_status': [],
      'relationship': ['关系描述。'],
    }

  monkeypatch.setattr(
    Interpreter,
    'interpret_tiangan',
    staticmethod(tiangan_description),
  )
  monkeypatch.setattr(
    Interpreter,
    'interpret_shishen',
    staticmethod(shishen_description),
  )

  sections = interpret(chart).split('\n' + '-' * 60 + '\n')
  assert len(sections) > 3
  assert '解读：日主解读。\n\n' in sections[2]
  assert '日主的个性：' not in sections[2]
  for section in sections[3:]:
    assert '解读：' not in section
    assert '代表的特点：状态良好。\n\n' in section
    assert '状态不好时，可能会有以下特点：' not in section
    assert '的恋爱/交友观：关系描述。\n\n' in section
    assert section.index('代表的特点：') < section.index('的恋爱/交友观：')
