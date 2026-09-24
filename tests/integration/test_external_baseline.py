# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>
# test_external_baseline.py

import json
import hashlib
from datetime import date, datetime
from itertools import islice, pairwise, product
from pathlib import Path
from typing import Any, Final

import pytest

from bazi.bazi import Bazi
from bazi.bazi_chart import BaziChart
from bazi.defines import Ganzhi
from bazi.school import BaziConfig, BaziSchool, DayRollover


pytestmark = pytest.mark.integration

BASELINE: Final[dict[str, Any]] = json.loads(
  Path(__file__).with_name('external_baseline.json').read_text(encoding='utf-8'),
)
CASE_IDS: Final[tuple[str, ...]] = tuple(case['id'] for case in BASELINE['cases'])


def _external_fingerprint() -> str:
  # Pin admitted source values independently of reference-dependent matching lists.
  payload = {
    'admission_sha256': BASELINE['admission_sha256'],
    'input_protocol': BASELINE['input_protocol'], 'sources': BASELINE['sources'],
    'cases': [{
      **{key: case[key] for key in ('id', 'birth_time', 'gender', 'synthetic')},
      'observations': sorted(
        [{key: value for key, value in row.items()
          if key not in ('matching_profiles', 'dayun_sequence_matching_profiles')}
         for row in case['observations']],
        key=lambda row: (row['source'], row['profile']),
      ),
    } for case in sorted(BASELINE['cases'], key=lambda case: case['id'])],
  }
  encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
  return hashlib.sha256(encoded).hexdigest()


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
  assert _external_fingerprint() == '65ece0cdf6e1f580d11efe5dff99e8a8a6eeb3782c2267cc5afaae13506c3f7e'
  cases = BASELINE['cases']
  expected_ids = {
    'C01', 'C02', 'C03', 'C04', 'C09', 'C10', 'C12', 'C16',
    'C18', 'C23', 'C29', 'C32', 'C33', 'C34', 'C36', 'C37',
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
  for profile, values in BASELINE['profiles'].items():
    precision, rollover, year_rule = profile.split('/')
    assert values['backend'] == 'celestial'
    assert values['precision'] == precision
    assert BaziSchool.from_json(values['school']) == BaziSchool(day_rollover=DayRollover[rollover])
    assert values['dayun_year_rule'] == year_rule
  for case in cases:
    assert set(case['reference']) == set(BASELINE['profiles'])
    assert len(case['observations']) == len(expected_sources)
    assert {(row['source'], row['profile']) for row in case['observations']} == expected_sources


@pytest.mark.parametrize('case', BASELINE['cases'], ids=CASE_IDS)
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


@pytest.mark.parametrize('case', BASELINE['cases'], ids=CASE_IDS)
def test_observation_meanings(case: dict[str, Any]) -> None:
  for observation in case['observations']:
    assert date.fromisoformat(observation['captured_on_utc']).isoformat() == observation['captured_on_utc']
    assert len(observation['evidence_sha256']) == 64
    assert all(character in '0123456789abcdef' for character in observation['evidence_sha256'])
    assert len(observation['pillars']) == 4
    for pillar in observation['pillars']:
      assert str(Ganzhi.from_str(pillar)) == pillar
    sequence = [Ganzhi.from_str(item) for item in observation['dayun_sequence']]
    assert len(sequence) == 3
    forward = all(left.next(1) == right for left, right in pairwise(sequence))
    reverse = all(left.next(-1) == right for left, right in pairwise(sequence))
    assert observation['sequence_direction'] == ('forward' if forward else 'reverse' if reverse else 'unidentified')
    assert set(observation['duration']) == {'years', 'months', 'days', 'hours'}

    if observation['source'] == 'lunar-python':
      assert type(observation['reported_forward']) is bool
      assert observation['reported_forward'] == forward
      assert observation['evidence_kind'] == 'serialized_method_record'
      assert observation['field_status'] == {'start': 'observed', 'year_labels': 'observed', 'age_labels': 'observed'}
      assert observation['year_labels']['kind'] == 'gregorian_year_inclusive'
      assert observation['start']['resolution'] == 'second_display'
      config = BASELINE['sources']['lunar-python']['profiles'][observation['profile']]
      assert observation['start']['calculation'] == f'yun_sect_{config["yun_sect"]}'
      assert observation['year_labels']['start'][0] == datetime.fromisoformat(observation['start']['value']).year
      assert all(end == start + 9 for start, end in zip(observation['year_labels']['start'], observation['year_labels']['end']))
    elif observation['source'] == 'china95':
      assert observation['reported_forward'] is None
      assert observation['evidence_kind'] == 'response_body'
      assert observation['field_status'] == {'start': 'observed', 'year_labels': 'not_provided', 'age_labels': 'observed'}
      assert observation['year_labels'] == {'kind': 'unclassified_source_display', 'raw': []}
      assert observation['start']['resolution'] == 'hour_display'
      assert observation['start']['rounding'] == 'unknown'
      assert datetime.fromisoformat(observation['start']['value']).isoformat(timespec='hours') == observation['start']['value']
    else:
      assert observation['source'] == 'iwzwh'
      assert observation['reported_forward'] is None
      assert observation['evidence_kind'] == 'response_body'
      assert observation['field_status'] == {'start': 'not_provided', 'year_labels': 'reconstructed', 'age_labels': 'reconstructed'}
      assert observation['start'] == {'status': 'missing', 'reason': 'no_absolute_start_in_observation'}
      assert observation['year_labels']['kind'] == 'renderer_year_label'
      assert observation['age_labels']['kind'] == 'renderer_xusui'
      assert observation['year_labels']['start'] == [
        datetime.fromisoformat(case['birth_time']).year + age - 1 for age in observation['age_labels']['start']
      ]
