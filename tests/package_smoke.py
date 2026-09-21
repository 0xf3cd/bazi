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
from typing import Any


WRITE_ATTEMPTS: list[str] = []


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

  import bazi
  check('bazi.bazi_chart' not in sys.modules and 'bazi.calendar.hko_data_utils' not in sys.modules, 'Root import eagerly loaded chart/data')
  from bazi.bazi import Bazi
  from bazi.bazi_chart import BaziChart
  from bazi.school import BaziConfig
  from bazi.calendar import CalendarBackend, CalendarDate, CalendarType, calendar_utils_of
  from bazi.defines import Ganzhi, Jieqi, Tiangan, Shishen
  from bazi.transit_chart import TransitChart
  from bazi.transits import TransitKind
  from bazi.analyzer.relationship import RelationshipAnalyzer
  from bazi.interpreter import Interpreter

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
  for shishen in Shishen:
    check(bool(Interpreter.interpret_shishen(shishen)['general']), 'Missing Shishen description')
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
