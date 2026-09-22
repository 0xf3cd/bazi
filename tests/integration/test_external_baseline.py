# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import json
from datetime import datetime
from itertools import islice, pairwise, product
from pathlib import Path
from typing import Any, Final

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Ganzhi
from bazi.school import BaziConfig, BaziSchool


pytestmark = pytest.mark.integration

BASELINE: Final[dict[str, Any]] = json.loads(
  Path(__file__).with_name('external_baseline.json').read_text(encoding='utf-8'),
)


def _chart(case: dict[str, Any], profile: str) -> BaziChart:
  values = BASELINE['profiles'][profile]
  return BaziChart(Bazi.create(
    case['birth_time'],
    case['gender'],
    BaziConfig.from_values(
      precision=values['precision'],
      backend=values['backend'],
      school=BaziSchool.from_json(values['school']),
      dayun_year_rule=values['dayun_year_rule'],
    ),
  ))


def _snapshot(chart: BaziChart) -> dict[str, Any]:
  return {
    'pillars': [str(pillar) for pillar in chart.bazi.pillars],
    'reported_forward': chart.dayun_order,
    'start': chart.dayun_start_moment.isoformat(),
    'dayun': [{
      'ganzhi': str(item.ganzhi), 'ganzhi_year': item.ganzhi_year,
      'start': item.start_moment.isoformat(), 'end': item.end_moment.isoformat(),
    } for item in islice(chart.dayun, 3)],
  }


def test_baseline_inventory() -> None:
  assert BASELINE['schema_version'] == 1
  cases = BASELINE['cases']
  expected_ids = {
    'C01', 'C02', 'C03', 'C04', 'C09', 'C10', 'C11', 'C12',
    'C16', 'C23', 'C29', 'C32', 'C33', 'C34', 'C36', 'C37',
  }
  assert len(cases) == len(expected_ids)
  assert {case['id'] for case in cases} == expected_ids
  assert len({(case['birth_time'], case['gender']) for case in cases}) == len(cases)
  assert all(case['synthetic'] is True for case in cases)
  assert set(BASELINE['profiles']) == {
    f'{precision}/{rollover}/{year_rule}'
    for precision, rollover, year_rule in product(
      ('day', 'hour', 'minute'), ('WAN_ZISHI', 'ZIZHENG'), ('jie_projected', 'fixed_decade'),
    )
  }
  expected_sources = {
    ('lunar-python', f'eightchar-{eight}/yun-{yun}') for eight, yun in product((1, 2), repeat=2)
  } | {('china95', 'captured-default'), ('iwzwh', 'captured-default')}
  assert set(BASELINE['sources']) == {'lunar-python', 'china95', 'iwzwh'}
  for case in cases:
    assert set(case['reference']) == set(BASELINE['profiles'])
    assert len(case['observations']) == len(expected_sources)
    assert {(row['source'], row['profile']) for row in case['observations']} == expected_sources


@pytest.mark.parametrize('case', BASELINE['cases'], ids=[case['id'] for case in BASELINE['cases']])
def test_reference_profiles_and_external_matches(case: dict[str, Any]) -> None:
  current = {profile: _snapshot(_chart(case, profile)) for profile in BASELINE['profiles']}
  assert current == case['reference']

  # Matching means equality of the named fields, not equivalence of entire schools.
  for observation in case['observations']:
    expected_pillars = sorted(
      profile for profile, value in current.items() if value['pillars'] == observation['pillars']
    )
    expected_dayun = sorted(
      profile for profile, value in current.items()
      if [item['ganzhi'] for item in value['dayun']] == observation['dayun_sequence']
    )
    assert expected_pillars == observation['matching_profiles']
    assert expected_dayun == observation['dayun_sequence_matching_profiles']


@pytest.mark.parametrize('case', BASELINE['cases'], ids=[case['id'] for case in BASELINE['cases']])
def test_observation_meanings(case: dict[str, Any]) -> None:
  for observation in case['observations']:
    assert len(observation['pillars']) == 4
    for pillar in observation['pillars']:
      assert str(Ganzhi.from_str(pillar)) == pillar
    sequence = [Ganzhi.from_str(item) for item in observation['dayun_sequence']]
    assert len(sequence) == 3
    step = 1 if observation['sequence_direction'] == 'forward' else -1
    assert all(left.next(step) == right for left, right in pairwise(sequence))
    assert set(observation['duration']) == {'years', 'months', 'days', 'hours'}

    if observation['source'] == 'lunar-python':
      assert type(observation['reported_forward']) is bool
      assert observation['reported_forward'] == (step == 1)
      assert observation['year_labels']['kind'] == 'gregorian_year_inclusive'
      assert observation['start']['resolution'] == 'second_display'
    elif observation['source'] == 'china95':
      assert observation['reported_forward'] is None
      assert observation['start']['resolution'] == 'hour_display'
      assert observation['start']['rounding'] == 'unknown'
      assert datetime.fromisoformat(observation['start']['value']).isoformat(timespec='hours') == observation['start']['value']
    else:
      assert observation['source'] == 'iwzwh'
      assert observation['reported_forward'] is None
      assert observation['start'] == {'status': 'missing', 'reason': 'no_absolute_start_in_observation'}
      assert observation['year_labels']['kind'] == 'renderer_year_label'
