# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import pytest

from run_interpreter import interpret
from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Shishen, Tiangan
from bazi.descriptions import ShishenDescription, TianganDescription
from bazi.interpreter import Interpreter


@pytest.mark.parametrize(('tiangan_fields', 'shishen_fields'), [
  (
    {'general': ['日主解读。'], 'personality': []},
    {
      'general': [],
      'in_good_status': ['状态良好。'],
      'in_bad_status': [],
      'relationship': ['关系描述。'],
    },
  ),
  (
    {'general': [], 'personality': ['日主个性。']},
    {
      'general': ['十神解读。'],
      'in_good_status': [],
      'in_bad_status': ['状态不好。'],
      'relationship': [],
    },
  ),
  (
    {'general': ['日主解读。'], 'personality': ['日主个性。']},
    {
      'general': ['十神解读。'],
      'in_good_status': ['状态良好。'],
      'in_bad_status': ['状态不好。'],
      'relationship': ['关系描述。'],
    },
  ),
  (
    {'general': [], 'personality': []},
    {
      'general': ['十神解读。'],
      'in_good_status': ['状态良好。'],
      'in_bad_status': [],
      'relationship': [],
    },
  ),
], ids=['alternating-a', 'alternating-b', 'all-content', 'leading-content'])
def test_interpret_description_headings_follow_content(
  tiangan_fields: TianganDescription,
  shishen_fields: ShishenDescription,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  chart = BaziChart(Bazi.create('2000-01-01 12:00', 'male'))

  def tiangan_description(_: Tiangan) -> TianganDescription:
    return tiangan_fields

  def shishen_description(_: Shishen) -> ShishenDescription:
    return shishen_fields

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
  _, _, day_master_section, *shishen_sections = sections

  def assert_headings(
    section: str,
    headings: tuple[tuple[str, list[str]], ...],
  ) -> None:
    for heading, descriptions in headings:
      assert (heading + ''.join(descriptions) in section) is bool(descriptions)
    present_headings = tuple(heading for heading, descriptions in headings if descriptions)
    positions = tuple(section.index(heading) for heading in present_headings)
    assert positions == tuple(sorted(positions))

  day_master_headings = (
    ('解读：', tiangan_fields['general']),
    ('日主的个性：', tiangan_fields['personality']),
  )
  assert_headings(day_master_section, day_master_headings)

  shishen_headings = (
    ('解读：', shishen_fields['general']),
    ('代表的特点：', shishen_fields['in_good_status']),
    ('状态不好时，可能会有以下特点：', shishen_fields['in_bad_status']),
    ('的恋爱/交友观：', shishen_fields['relationship']),
  )
  for section in shishen_sections:
    assert_headings(section, shishen_headings)
