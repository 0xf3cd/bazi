# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''Copied into a foreign cwd and run with an installed wheel, under -I -B and -O.'''

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import sys

from datetime import date, datetime, timedelta, timezone, UTC
from pathlib import Path
from typing import Any, cast


WRITE_ATTEMPTS: list[str] = []
EOT_READS: list[str] = []


def check(condition: bool, message: str) -> None:
  if not condition:
    raise RuntimeError(message)


class EqualKey:
  def __init__(self, value: object) -> None:
    self.value = value

  def __eq__(self, other: object) -> bool:
    return self.value == other

  def __hash__(self) -> int:
    return hash(self.value)


def record_eot_reads(event: str, args: tuple[Any, ...]) -> None:
  if event == 'open':
    path, _, _ = args
    if isinstance(path, str) and path.replace('\\', '/').endswith('/equation_of_time.bin'):
      EOT_READS.append(event)


def deny_writes(event: str, args: tuple[Any, ...]) -> None:
  if event == 'open':
    _, mode, flags = args
    if (mode and any(char in mode for char in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
      WRITE_ATTEMPTS.append(event)
      raise PermissionError('Runtime write blocked')
  if event in ('os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.chmod', 'os.link', 'os.symlink', 'os.truncate', 'os.utime'):
    WRITE_ATTEMPTS.append(event)
    raise PermissionError('Runtime write blocked')


def main() -> None:
  expected = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
  check(sys.flags.isolated == 1 and sys.dont_write_bytecode, 'Smoke requires -I -B')
  check(not os.environ.get('PYTHONPATH'), 'PYTHONPATH must be empty')
  check(sys.prefix != sys.base_prefix, 'Consumer must be a virtual environment')
  prefix = Path(sys.prefix).resolve()
  dist = importlib.metadata.distribution('bazi')
  check(dist.version == expected['version'], 'Installed version mismatch')
  check(dist.metadata['Name'] == 'bazi', 'Installed name mismatch')
  check(dist.metadata['Requires-Python'] == '>=3.11', 'Python requirement mismatch')
  check(not dist.requires, 'Unexpected runtime dependencies')
  check(not dist.entry_points, 'Unexpected installed entrypoints')
  check(not dist.metadata.get_all('License-Expression', []) and not dist.metadata.get_all('License', []), 'Blanket license claim')
  check(not any('License ::' in value for value in dist.metadata.get_all('Classifier', [])), 'Blanket license classifier')
  check(set(dist.metadata.get_all('License-File', [])) == {'LICENSE', 'THIRD_PARTY_NOTICES.md'}, 'License file metadata mismatch')
  check({d.metadata['Name'].lower() for d in importlib.metadata.distributions()} == {'bazi', 'pip'}, 'Functional consumer contains development dependencies')
  spec = importlib.util.find_spec('bazi')
  check(spec is not None and spec.origin is not None, 'Package not found')
  if spec is None or spec.origin is None:
    raise RuntimeError('Package not found')
  package_root = Path(spec.origin).resolve().parent
  check(package_root.is_relative_to(prefix), 'Package origin outside consumer')
  check(not Path.cwd().is_relative_to(package_root), 'Consumer cwd is inside package')
  check(importlib.util.find_spec('src') is None, 'Unexpected src compatibility package')
  roster = {path.relative_to(package_root.parent).as_posix() for path in package_root.rglob('*') if path.is_file()}
  check(roster == set(expected['package']), 'Installed package file roster mismatch')
  for name, digest in expected['package'].items():
    check(hashlib.sha256((package_root.parent / name).read_bytes()).hexdigest() == digest, f'Installed bytes differ: {name}')
  for name, digest in expected['licenses'].items():
    matches = [file for file in dist.files or () if str(file).endswith('/licenses/' + name)]
    check(len(matches) == 1, 'Installed license missing')
    check(hashlib.sha256(matches[0].read_binary()).hexdigest() == digest, 'Installed license bytes differ')

  # Audit hooks enforce read-only use even under root and on Windows.
  sys.addaudithook(deny_writes)
  try:
    (package_root / 'write-control').write_bytes(b'must not be written')
  except PermissionError as error:
    check(str(error) == 'Runtime write blocked', 'Write control failed for the wrong reason')
  else:
    raise RuntimeError('Write guard failed its positive control')
  print('PASS executable runtime write-attempt control')

  sys.addaudithook(record_eot_reads)

  import bazi
  check('bazi.bazi_chart' not in sys.modules and 'bazi.calendar.hko_data_utils' not in sys.modules, 'Root import eagerly loaded chart/data')
  check('bazi.descriptions' not in sys.modules and 'bazi.knowledge' not in sys.modules, 'Root import eagerly loaded interpretation data')
  check('bazi.context_matching' not in sys.modules, 'Root import eagerly loaded context matcher')
  matching_module = bazi.context_matching
  check('context_matching' in bazi.__all__ and matching_module is bazi.context_matching, 'Matching ordinary module attribute registration mismatch')
  knowledge_module = bazi.knowledge
  check('knowledge' in bazi.__all__ and knowledge_module is bazi.knowledge, 'Knowledge module registration mismatch')
  check('bazi.descriptions' not in sys.modules, 'Knowledge module loaded legacy descriptions')
  from bazi.bazi import Bazi
  from bazi.bazi_chart import BaziChart, BaziJson
  from bazi.school import BaziConfig
  from bazi.calendar import CalendarBackend, CalendarDate, CalendarType, calendar_utils_of
  from bazi.calendar.solar_time import apparent_solar_datetime
  from bazi.defines import Ganzhi, Jieqi, Tiangan, Shishen, Dizhi
  from bazi.transit_chart import TransitChart
  from bazi.transits import TransitKind
  from bazi.analyzer.relationship import RelationshipAnalyzer
  from bazi.interpreter import Interpreter
  from bazi.knowledge import KnowledgeBase
  from bazi.context_matching import ContextProfile, ContextResult, evaluate_context

  check(not EOT_READS, 'Imports eagerly read the EOT table')
  for longitude, error_type in ((True, TypeError), (float('nan'), ValueError), (180.01, ValueError)):
    try:
      Bazi.create(datetime(2000, 1, 1, tzinfo=UTC), 'male',
                  BaziConfig.from_values(precision='minute'), longitude=longitude)
    except error_type:
      pass
    else:
      raise RuntimeError('Longitude validation failed')
  check(not EOT_READS, 'Longitude validation read the EOT table')
  apparent = apparent_solar_datetime(datetime(2000, 11, 3, 0, 50, tzinfo=UTC), 0.0)
  check(len(EOT_READS) == 1, 'First apparent-solar conversion did not read exactly one EOT table')
  check(apparent == datetime(2000, 11, 3, 1, 6, 26, 82639), 'Installed apparent-solar primitive mismatch')
  location_chart = BaziChart(Bazi.create(
    datetime(2000, 11, 3, 0, 50, tzinfo=UTC),
    'male',
    BaziConfig.from_values(precision='hour'),
    longitude=0.0,
  ))
  check(location_chart.bazi.hour == 1, 'Installed apparent-solar chart mismatch')
  check(
    BaziChart.from_json(json.loads(json.dumps(location_chart.json))).json == location_chart.json,
    'Installed apparent-solar JSON restoration mismatch',
  )

  precise_chart = BaziChart(Bazi.create(
    datetime(2000, 11, 3, 0, 43, 59, 123456, tzinfo=UTC),
    'male',
    BaziConfig.from_values(precision='hour'),
    longitude=-0.0,
  ))
  precise_data = cast(BaziJson.LocationBaziChartJsonDict, precise_chart.json)
  check(precise_chart.bazi.hour_pillar.dizhi is Dizhi.丑, 'Installed conversion discarded seconds')
  check(precise_data['canonical_instant'] == '2000-11-03T00:43:59.123456+00:00', 'Installed exact instant mismatch')
  check(str(precise_data['longitude']) == '0.0', 'Installed negative-zero emission mismatch')
  check(
    BaziChart.from_json(json.loads(json.dumps(precise_chart.json))).json == precise_chart.json,
    'Installed precise-instant JSON restoration mismatch',
  )
  hour_tie = Bazi.create(
    datetime(2024, 3, 5, 1, 52, 45, tzinfo=UTC),
    'male',
    BaziConfig.from_values(precision='hour'),
    longitude=-74.0,
  )
  check(str(hour_tie.month_pillar) == '丙寅', 'Installed apparent-shichen Jie attribution mismatch')
  kiritimati = BaziChart(Bazi.create(
    '2024-01-01T12:00:00+14:00', 'female', BaziConfig.from_values(precision='minute'), longitude=-157.4,
  ))
  check(kiritimati.bazi.solar_datetime == datetime(2024, 1, 1, 11, 27), 'Installed civil date anchoring mismatch')
  alternate = BaziChart(Bazi.create(
    '2023-12-31T22:00:00+00:00', 'female', BaziConfig.from_values(precision='minute'), longitude=-157.4,
    civil_timezone=datetime.fromisoformat('2024-01-01T12:00:00+14:00').tzinfo,
  ))
  check(alternate.bazi == kiritimati.bazi and hash(alternate.bazi) == hash(kiritimati.bazi), 'Installed explicit civil identity mismatch')
  check(alternate.json == kiritimati.json and BaziChart.from_json(kiritimati.json).json == kiritimati.json, 'Installed civil JSON mismatch')
  location_match = evaluate_context(kiritimati, criterion_id='editorial.guansha_coexistence.v1', profile=ContextProfile('natal'))
  check(json.loads(location_match.input_json)['civil_time'] == '2024-01-01T12:00:00+14:00', 'Installed context dropped civil basis')
  check(ContextResult.from_json(location_match.export_json()) == location_match, 'Installed location context restore mismatch')
  for birth, basis in (
    (datetime.min.replace(tzinfo=timezone(timedelta(hours=14))), None),
    (datetime.max.replace(tzinfo=timezone(timedelta(hours=-12))), None),
    (datetime.min.replace(tzinfo=UTC), timezone(timedelta(hours=-12))),
    (datetime.max.replace(tzinfo=UTC), timezone(timedelta(hours=14))),
  ):
    try:
      Bazi.create(birth, 'male', BaziConfig.from_values(precision='minute'), longitude=0.0, civil_timezone=basis)
    except ValueError:
      pass
    else:
      raise RuntimeError('Installed extreme date did not raise ValueError')
  for birth in (datetime.min.replace(tzinfo=timezone(timedelta(hours=14))),
                datetime.max.replace(tzinfo=timezone(timedelta(hours=-12)))):
    try:
      apparent_solar_datetime(birth, 0.0)
    except ValueError:
      pass
    else:
      raise RuntimeError('Installed solar primitive leaked an extreme instant')
  for field, spelling in (('canonical_instant', '2030-01-01T00:00:00+00:00'),
                       ('civil_time', '2024-01-01T12:00:00+13:00')):
    inconsistent = json.loads(location_match.export_json())
    inconsistent['input'][field] = spelling
    try:
      ContextResult.from_json(json.dumps(inconsistent))
    except ValueError:
      pass
    else:
      raise RuntimeError('Installed record accepted contradictory civil/UTC inputs')
  historical = json.loads(location_match.export_json())
  historical['input'].update(civil_time='1850-01-01T12:00:00+14:00', canonical_instant='1849-12-31T22:00:00+00:00', apparent_time='2000-01-01T12:00:00')
  recovered = ContextResult.from_json(json.dumps(historical))
  check(recovered.criterion == location_match.criterion and recovered.occurrences == location_match.occurrences,
        'Installed observation recovery recalculated stored observations')
  for kwargs, expected_error in (({'civil_timezone': UTC}, ValueError), ({'longitude': 0.0, 'civil_timezone': 'UTC'}, TypeError)):
    try:
      Bazi.create(datetime(2000, 1, 1, tzinfo=UTC), 'male', BaziConfig.from_values(precision='minute'), **kwargs)
    except expected_error:
      pass
    else:
      raise RuntimeError('Installed civil timezone validation failed')

  check(Path(bazi.__file__).resolve().is_relative_to(prefix), 'Root import source leakage')
  for backend in CalendarBackend:
    utils = calendar_utils_of(backend)
    check(utils.to_date(utils.to_lunar(date(2024, 2, 10))) == date(2024, 2, 10), 'Calendar roundtrip mismatch')
    check(utils.jieqi_date(2024, Jieqi.LICHUN) == date(2024, 2, 4), 'Calendar absolute date mismatch')
    date_calls: list[tuple[str, object]] = [
      ('get_min_supported_date', CalendarType.SOLAR),
      ('get_max_supported_date', CalendarType.SOLAR),
      ('is_valid', CalendarDate(2024, 1, 1, CalendarType.SOLAR)),
      *[(f'is_valid_{kind}_date', CalendarDate(2024, 1, 1, CalendarType[kind.upper()]))
        for kind in ('solar', 'lunar', 'ganzhi')],
      *[(f'{source}_to_{target}', CalendarDate(2024, 1, 1, CalendarType[source.upper()]))
        for source in ('solar', 'lunar', 'ganzhi') for target in ('solar', 'lunar', 'ganzhi') if source != target],
      *[(name, datetime(2024, 3, 1)) for name in ('to_solar', 'to_lunar', 'to_ganzhi', 'to_date', 'prev_jie', 'next_jie')],
    ]
    for name, good in date_calls:
      method = getattr(utils, name)
      method(good)
      bad = EqualKey(good)
      check(bad == good and good == bad and hash(bad) == hash(good), 'Cache collision control failed')
      try:
        method(bad)
      except TypeError as error:
        check(str(error).startswith('Expected '), f'{name}: wrong rejection boundary')
      else:
        raise RuntimeError(f'{name}: warm cache bypassed input validation')
      for attribute in ('cache_clear', 'cache_info', 'cache_parameters', '__wrapped__'):
        check(not hasattr(method, attribute), f'{name}: public cache attribute {attribute}')
    a = datetime(2024, 3, 1, 0, 30, tzinfo=UTC)
    b = datetime(2024, 2, 29, 19, 30, tzinfo=timezone(timedelta(hours=-5)))
    check(a == b and hash(a) == hash(b), 'Datetime collision control failed')
    for name in ('to_solar', 'to_lunar', 'to_ganzhi', 'to_date'):
      project = getattr(utils, name)
      check(utils.to_date(project(a)) == date(2024, 3, 1), 'First civil projection mismatch')
      check(utils.to_date(project(b)) == date(2024, 2, 29), 'Warm civil projection mismatch')
    print(f'PASS backend={backend.value} cache boundaries/civil projection')
    chart = BaziChart(Bazi.create(datetime(2000, 1, 1, 12), 'male', BaziConfig.from_values(backend=backend, precision='day')))
    check(BaziChart.from_json(json.loads(json.dumps(chart.json))).json == chart.json, 'JSON restoration mismatch')
    transits = TransitChart(chart).at_year(2024)
    check(transits is not None, 'Missing transits')
    if transits is None:
      raise RuntimeError('Missing transits')
    analysis = RelationshipAnalyzer(chart)
    check('taohua' in analysis.at_birth.shensha, 'Missing natal analysis')
    check('taohua' in analysis.transits.shensha(transits.select(TransitKind.LIUNIAN)), 'Missing transit analysis')
    try:
      Bazi.create(datetime(2000, 1, 1, tzinfo=UTC), 'male')
    except ValueError:
      pass
    else:
      raise RuntimeError('Timezone rejection failed')
    try:
      BaziChart.from_json({**chart.json, 'extra': 'invalid'})
    except ValueError:
      pass
    else:
      raise RuntimeError('JSON input rejection failed')
    print(f'PASS backend={backend.value} JSON/transits/analysis/input rejection')
  for step in (Ganzhi.from_str('甲子').next, Ganzhi.from_str('甲子').prev):
    step(1)
    try:
      step(1.0) # type: ignore[arg-type] # Must reject even when 1 has warmed the cache.
    except TypeError as error:
      check(str(error).startswith('Expected int'), 'Wrong step rejection boundary')
    else:
      raise RuntimeError('Ganzhi warm cache bypassed step validation')
  for value in Tiangan:
    check(bool(Interpreter.interpret_tiangan(value)['general']), 'Missing Tiangan description')
    structured = Interpreter.query_tiangan(value)
    claim = structured['general'][0]
    check(claim.text == Interpreter.interpret_tiangan(value)['general'][0], 'Structured text differs')
    check(bool(claim.sources) and not claim.conditions, 'Default claim eligibility differs')
    for source_id in claim.sources:
      witness = Interpreter.query_source(source_id)
      check(bool(witness.work and witness.locator and witness.limitations), 'Incomplete witness')
    check(hash(structured) == hash(Interpreter.query_tiangan(value)), 'Unhashable structured results')
  check(
    len(Interpreter.interpret_tiangan(Tiangan.甲, include_reference_only=True)['general'])
    > len(Interpreter.interpret_tiangan(Tiangan.甲)['general']),
    'Reference-only Tiangan descriptions are not opt-in',
  )
  complete_shishen_counts = (25, 23, 23, 23, 20, 20, 22, 22, 19, 22)
  for shishen, complete_count in zip(Shishen, complete_shishen_counts, strict=True):
    default = Interpreter.interpret_shishen(shishen)
    complete = Interpreter.interpret_shishen(shishen, include_reference_only=True)
    expected_default_count = 0 if shishen is Shishen.劫财 else 1
    default_count = (
      len(default['general'])
      + len(default['in_good_status'])
      + len(default['in_bad_status'])
      + len(default['relationship'])
    )
    actual_complete_count = (
      len(complete['general'])
      + len(complete['in_good_status'])
      + len(complete['in_bad_status'])
      + len(complete['relationship'])
    )
    check(
      default_count == expected_default_count,
      f'Wrong default Shishen projection: {shishen}',
    )
    check(
      actual_complete_count == complete_count,
      f'Wrong complete Shishen projection: {shishen}',
    )
  knowledge = KnowledgeBase.load()
  check(len(knowledge.entries) == 295 and len(knowledge.query()) == 19, 'Knowledge corpus/eligibility mismatch')
  selected = knowledge.query(object_id='tiangan.ding', topic='历史象', include_reference_only=True)
  check(tuple(entry.claim_id for entry in selected) == ('tiangan.ding.lamp_symbol',), 'Installed knowledge lookup mismatch')
  restored_knowledge = KnowledgeBase.from_json(knowledge.export_json(selected))
  check(restored_knowledge.entries == {entry.claim_id: entry for entry in selected}, 'Knowledge export/reload lost entries')
  check(restored_knowledge.sources == knowledge.sources, 'Knowledge export/reload lost witnesses')
  check('p. 70' in restored_knowledge.render(selected[0]), 'Knowledge display lost source locator')
  try:
    knowledge.query(object_id='typo')
  except ValueError:
    pass
  else:
    raise RuntimeError('Optimized knowledge input rejection failed')
  print('PASS installed knowledge query/display/export/reload')
  criterion = 'editorial.guansha_coexistence.v1'
  positive_chart = BaziChart(Bazi.create(datetime(2000, 1, 3, 12), 'female'))
  matched = evaluate_context(positive_chart, criterion_id=criterion, profile=ContextProfile('natal'), include_reference_only=True)
  check(matched.criterion.status == 'SATISFIED' and len(matched.entries) == 2, 'Installed context positive mismatch')
  check(any(o.pillar == 'hour' and o.layer == 'hidden' and str(o.stem) == '丁' and str(o.shishen) == '正官' for o in matched.occurrences), 'Installed context lost hidden witness')
  check('也许' in matched.render() and 'Does not establish a classical rule or real-world prediction.' in matched.render(), 'Installed context lost modal/source limit')
  check(ContextResult.from_json(matched.export_json()) == matched, 'Installed context restoration lost evidence/knowledge')
  check(evaluate_context(positive_chart, criterion_id=criterion, profile=ContextProfile('natal')).entries == (), 'Installed context promoted reference output')
  missing = evaluate_context(positive_chart, criterion_id=criterion, profile=ContextProfile('natal_and_liunian'))
  check(missing.criterion.status == 'UNKNOWN', 'Installed context missing year became false')
  first, second = (evaluate_context(chart, criterion_id=criterion, profile=ContextProfile('natal_and_liunian', year)) for year in (2024, 2084))
  check(first != second and all(o.ganzhi_year == 2024 and o.kind is TransitKind.LIUNIAN for o in first.occurrences if o.origin == 'transit'), 'Installed context lost transit coordinate/kind')
  for invalid_year in (True, type('Year', (int,), {})(2024)):
    try:
      ContextProfile('natal_and_liunian', invalid_year)
    except TypeError:
      pass
    else:
      raise RuntimeError('Installed exact-int year rejection failed')
  print('PASS installed context matching/lazy/readonly/evidence/record restoration')
  try:
    calendar_utils_of(42)  # type: ignore[arg-type] # Deliberately invalid public input.
  except TypeError:
    pass
  else:
    raise RuntimeError('Type rejection failed')
  for name, module in tuple(sys.modules.items()):
    if name == 'bazi' or name.startswith('bazi.'):
      origin = getattr(module, '__file__', None)
      check(origin is not None and Path(origin).resolve().is_relative_to(package_root), f'Submodule source leakage: {name}')
  check(not {'celestial_calendar', 'requests', 'bazi.calendar.celestial_data.generator', 'bazi.calendar.hko_data.encoder'} & sys.modules.keys(), 'Optional offline module imported')
  check(WRITE_ATTEMPTS == ['open'], 'Runtime attempted a write after the positive control')
  print(f'PASS installed smoke: {len(roster)} files, optimized={not __debug__}, origin={package_root}')


if __name__ == '__main__':
  main()
